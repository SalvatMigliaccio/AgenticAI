from openai import AsyncOpenAI
from app.core.config import settings

# Client separato: l'endpoint degli embedding sta su un server diverso dalla chat
# (un modello di embedding è molto più piccolo e si serve a parte).
_embed_client = AsyncOpenAI(base_url=settings.EMBED_BASE_URL, api_key=settings.EMBED_API_KEY)


async def embed(texts: list[str]) -> list[list[float]]:
    """Trasforma una lista di testi in una lista di vettori (uno per testo)."""
    resp = await _embed_client.embeddings.create(
        model=settings.EMBED_MODEL,
        input=texts,
    )
    # L'API ritorna gli embedding nell'ordine dell'input.
    return [item.embedding for item in resp.data]


async def embed_one(text: str) -> list[float]:
    """Comodità per il caso singolo (es. la query dell'utente nel router)."""
    return (await embed([text]))[0]
