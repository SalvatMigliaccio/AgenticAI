import asyncio
import re
import numpy as np

from app.core.config import settings
from app.agents.state import GraphState
from app.agents.registry import REGISTRY, FALLBACK_KEY, specialist_keys
from app.agents.prompts import build_router_messages
from app.llm.embeddings import embed, embed_one
from app.llm.provider import chat

# Cache dei centroidi: si calcolano una sola volta (embedding degli esemplari).
_centroids: dict[str, np.ndarray] | None = None
_lock = asyncio.Lock()


def _tokenize(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9_]+", text.lower())
        if token not in {"the", "and", "or", "of", "a", "to", "di", "e", "il", "la", "le", "i", "gli", "un", "una", "del", "della", "per", "con"}
    }


def _keyword_route(query: str) -> tuple[str, float]:
    """Fallback locale quando il backend embedding/LLM non è disponibile."""
    query_tokens = _tokenize(query)
    if not query_tokens:
        return FALLBACK_KEY, 0.0

    best_key = FALLBACK_KEY
    best_score = 0.0
    for key in specialist_keys():
        agent = REGISTRY[key]
        vocabulary = _tokenize(f"{agent.label} {agent.description} {' '.join(agent.exemplars)}")
        overlap = len(query_tokens & vocabulary)
        score = overlap / max(len(query_tokens), 1)
        if score > best_score:
            best_key = key
            best_score = score

    return best_key, round(best_score, 3)


async def _get_centroids() -> dict[str, np.ndarray]:
    """Centroide L2-normalizzato degli esemplari di ogni dominio specialistico."""
    global _centroids
    if _centroids is not None:
        return _centroids
    async with _lock:                      # evita ricalcolo concorrente al primo colpo
        if _centroids is not None:
            return _centroids
        cents: dict[str, np.ndarray] = {}
        for key in specialist_keys():
            vecs = await embed(REGISTRY[key].exemplars)
            arr = np.asarray(vecs, dtype=float)
            c = arr.mean(axis=0)                       # centroide = media degli esemplari
            c = c / (np.linalg.norm(c) + 1e-9)         # normalizzo per usare il dot come coseno
            cents[key] = c
        _centroids = cents
    return _centroids


async def router_node(state: GraphState) -> dict:
    query = state["user_query"]

    try:
        # 1) Embedding della query, normalizzato.
        qvec = np.asarray(await embed_one(query), dtype=float)
        qvec = qvec / (np.linalg.norm(qvec) + 1e-9)

        # 2) Coseno vs ogni centroide (dot di vettori normalizzati = coseno).
        cents = await _get_centroids()
        scores = {k: float(np.dot(qvec, c)) for k, c in cents.items()}
        best_key = max(scores, key=lambda k: scores[k])
        best_score = scores[best_key]

        # 3) Decisione: sopra soglia mi fido dell'embedding, altrimenti chiedo all'LLM.
        if best_score >= settings.ROUTER_CONFIDENCE_THRESHOLD:
            route, method = best_key, "embedding"
        else:
            options = [(k, REGISTRY[k].description) for k in specialist_keys()]
            try:
                raw = await chat(
                    build_router_messages(query, options),
                    model=settings.LLM_BASE_MODEL,
                    temperature=0.0,
                    max_tokens=20,                 # deve restituire solo una chiave
                )
                # Prendo il primo token e verifico che sia una chiave valida, altrimenti fallback.
                pick = raw.strip().split()[0].strip().lower() if raw.strip() else ""
                route = pick if pick in REGISTRY else FALLBACK_KEY
                method = "llm_fallback"
            except Exception:
                route, best_score = _keyword_route(query)
                method = "keyword_fallback"
    except Exception:
        route, best_score = _keyword_route(query)
        method = "keyword_fallback"
        scores = {}

    trace = state.get("trace", []) + [{
        "step": "router",
        "route": route,
        "confidence": round(best_score, 3),
        "method": method,
        "scores": {k: round(v, 3) for k, v in scores.items()} if "scores" in locals() else {},
    }]
    return {
        "route": route,
        "route_confidence": best_score,
        "route_method": method,
        "trace": trace,
    }