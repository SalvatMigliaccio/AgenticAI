import os
import socket
import tempfile
from pathlib import Path

from httpx import ConnectError
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, CollectionStatus
from app.core.config import settings


def _is_connection_failure(error: Exception) -> bool:
    message = str(error).lower()
    return isinstance(error, ConnectError) or "all connection attempts failed" in message


class QdrantStore:
    def __init__(self) -> None:
        self._remote = AsyncQdrantClient(url=settings.QDRANT_URL)
        self._local: AsyncQdrantClient | None = None
        self._active = self._remote

    def _get_local(self) -> AsyncQdrantClient:
        if self._local is None:
            # Per-process fallback path: evita lock contention tra worker multipli.
            host = socket.gethostname().replace(" ", "_")
            pid = os.getpid()
            local_path = Path(tempfile.gettempdir()) / f"agenticai-qdrant-{host}-{pid}"
            local_path.mkdir(parents=True, exist_ok=True)
            self._local = AsyncQdrantClient(path=str(local_path))
        return self._local

    async def _call(self, method_name: str, *args, **kwargs):
        method = getattr(self._active, method_name)
        try:
            return await method(*args, **kwargs)
        except Exception as error:
            if self._active is self._remote and _is_connection_failure(error):
                self._active = self._get_local()
                return await getattr(self._active, method_name)(*args, **kwargs)
            raise

    async def get_collection(self, *args, **kwargs):
        return await self._call("get_collection", *args, **kwargs)

    async def create_collection(self, *args, **kwargs):
        return await self._call("create_collection", *args, **kwargs)

    async def upsert(self, *args, **kwargs):
        return await self._call("upsert", *args, **kwargs)

    async def scroll(self, *args, **kwargs):
        return await self._call("scroll", *args, **kwargs)

    async def search(self, *args, **kwargs):
        return await self._call("search", *args, **kwargs)


# client async singleton verso Qdrant (usa il server remoto quando disponibile,
# altrimenti ripiega su uno storage locale persistente per lo sviluppo)
client = QdrantStore()


async def ensure_collection(name: str) -> None:
    """Crea la collection Qdrant se non esiste già."""
    try:
        status = await client.get_collection(name)
        if status.status != CollectionStatus.GREEN:
            raise RuntimeError(f"Collection {name} exists but is not ready: {status.status}")
    except Exception:
        # La collection non esiste: la creo
        await client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=settings.EMBED_DIM, distance=Distance.COSINE),
        )