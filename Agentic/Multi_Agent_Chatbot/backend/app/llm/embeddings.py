from openai import AsyncOpenAI
from hashlib import sha256
import re

import numpy as np

from app.core.config import settings

# Client separato: l'endpoint degli embedding sta su un server diverso dalla chat
# (un modello di embedding è molto più piccolo e si serve a parte).
_embed_client = AsyncOpenAI(base_url=settings.EMBED_BASE_URL, api_key=settings.EMBED_API_KEY)


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9_]+", text.lower())


def _fallback_embedding(text: str) -> list[float]:
    """Embedding locale deterministico, usato quando il server embeddings non risponde."""
    vector = np.zeros(settings.EMBED_DIM, dtype=float)
    tokens = _tokenize(text)
    if not tokens:
        return vector.tolist()

    for token in tokens:
        digest = sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "little") % settings.EMBED_DIM
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign

    norm = float(np.linalg.norm(vector))
    if norm > 0:
        vector /= norm
    return vector.tolist()


async def embed(texts: list[str]) -> list[list[float]]:
    """Trasforma una lista di testi in una lista di vettori (uno per testo)."""
    try:
        resp = await _embed_client.embeddings.create(
            model=settings.EMBED_MODEL,
            input=texts,
            timeout=settings.EMBED_REQUEST_TIMEOUT_SEC,
        )
        # L'API ritorna gli embedding nell'ordine dell'input.
        return [item.embedding for item in resp.data]
    except Exception:
        return [_fallback_embedding(text) for text in texts]


async def embed_one(text: str) -> list[float]:
    """Comodità per il caso singolo (es. la query dell'utente nel router)."""
    return (await embed([text]))[0]
