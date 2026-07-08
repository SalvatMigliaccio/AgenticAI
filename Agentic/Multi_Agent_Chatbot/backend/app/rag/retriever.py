import asyncio
from rank_bm25 import BM25Okapi

from app.core.config import settings
from app.llm.embeddings import embed_one
from app.rag.store import client, ensure_collection

#cache dell'indice BM25 per collection: viene ricostruito al primo accesso e riutilizzato finché il processo resta vivo
_bm25_cache: dict[str, tuple[BM25Okapi, list[str]]] = {}
_bm25_lock = asyncio.Lock()  #evita ricostruzione concorrente al primo accesso

def _tok(text: str) -> list[str]:
    """ 
    Tokenizzazione semplice per BM25: split su spazi e punteggiatura, minuscolo.
    """
    return text.lower().split()

async def _load_all_chunks(collection: str) -> list[str]:
    """Recupera tutti i passaggi della collection da Qdrant (solo testo)."""
    await ensure_collection(collection)
    # Recupero tutti i punti dalla collection
    points = await client.scroll(
        collection_name=collection,
        limit=settings.RAG_FETCH_K * 1000,  #prendo un numero alto di punti per avere più contesto
        with_payload=True,
        with_vector=False,
    )
    chunks = [p.payload.get("text", "") for p in points]
    return [c for c in chunks if c.strip()]  #filtra chunk vuoti


async def _get_bm25(collection: str) -> tuple[BM25Okapi, list[str]]:
    """Recupera o costruisce l'indice BM25 per una collection."""
    if collection in _bm25_cache:
        return _bm25_cache[collection]
    async with _bm25_lock:
        if collection in _bm25_cache:
            return _bm25_cache[collection]
        texts = await _load_all_chunks(collection)
        bm25 = BM25Okapi([_tok(t) for t in texts]) if texts else BM25Okapi([[""]])
        _bm25_cache[collection] = (bm25, texts)
        return _bm25_cache[collection]


def _rrf(rankings: list[list[str]], k: int = 60) -> dict[str, float]:
    """ 
    Reciprocal Rank Fusion: combina più ranking in un unico punteggio per ogni passaggio.
    """
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, text in enumerate(ranking):
            scores[text] = scores.get(text, 0.0) + 1.0 / (k + rank + 1)
    return scores

async def _rerank(query: str, candidates: list[str], top_k: int) -> list[str]:
    """ 
    Rerank cross-encoder in process (richiede sentence-trasformers + torch). Più preciso ma più costoso di BM25.
    """
    from sentence_transformers import CrossEncoder  # import pigro: non pesa se disattivato

    model = CrossEncoder(settings.RERANK_MODEL)
    pairs = [(query, c) for c in candidates]
    scores = model.predict(pairs)
    ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
    return [c for c, _ in ranked[:top_k]]

async def retrieve(collection: str | None, query: str, k: int = 4) -> list[str]:
    """Recupera i passaggi più rilveanti per la query dalla collection di Qdrant, se specificata. Altrimenti ritorna una lista vuota."""
    """Retrieval ibrida. Ritorna i top-k passaggi testuali per la query."""
    if not collection:
        return []
    top_k = k or settings.RAG_TOP_K
    fetch_k = settings.RAG_FETCH_K

    # --- Ramo denso: embedding query (Ollama) + ricerca vettoriale in Qdrant. ---
    qvec = await embed_one(query)
    dense_hits = await client.search(
        collection_name=collection, query_vector=qvec, limit=fetch_k, with_payload=True,
    )
    dense_ranking = [h.payload.get("text", "") for h in dense_hits]

    # --- Ramo sparso: BM25 sui chunk della collection. ---
    bm25, texts = await _get_bm25(collection)
    if texts:
        bm_scores = bm25.get_scores(_tok(query))
        top_idx = sorted(range(len(texts)), key=lambda i: bm_scores[i], reverse=True)[:fetch_k]
        sparse_ranking = [texts[i] for i in top_idx]
    else:
        sparse_ranking = []

    # --- Fusione RRF delle due classifiche. ---
    fused = _rrf([dense_ranking, sparse_ranking])
    candidates = [t for t, _ in sorted(fused.items(), key=lambda x: x[1], reverse=True)]

    # --- Rerank finale (opzionale) o taglio ai top_k. ---
    if settings.RERANK_ENABLED and candidates:
        return await _rerank(query, candidates[: fetch_k], top_k)
    return candidates[:top_k]