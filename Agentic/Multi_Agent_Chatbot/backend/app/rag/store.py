from qdrant_client import QradntClient
from qdrant_client.models import Distance, VectorParams, CollectionStatus, CreateCollection
from app.core.config import settings

#client async singleton verso Qdrant (usato dal retriever RAG)
client = AsyncQdrantClient(url=settings.QDRANT_URL)


async def ensure_collection(name: str) -> None:
    """Crea la collection Qdrant se non esiste già."""
    try:
        status = await client.get_collection(name)
        if status.status != CollectionStatus.GREEN:
            raise RuntimeError(f"Collection {name} exists but is not ready: {status.status}")
    except Exception:
        # La collection non esiste: la creo
        await client.create_collection(
            CreateCollection(
                name=name,
                vectors=VectorParams(size=settings.EMBED_DIM, distance=Distance.COSINE),
            )
        )