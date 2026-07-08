from contextlib import asynccontextmanager
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.core.config import settings


@asynccontextmanager
async def get_checkpointer(use_postgres: bool = True):
    """Fornisce un checkpointer. In dev puoi passare use_postgres=False."""
    if not use_postgres:
        yield MemorySaver()
        return
    async with AsyncPostgresSaver.from_conn_string(settings.POSTGRES_DSN) as cp:
        await cp.setup()          # crea le tabelle del checkpointer se mancano
        yield cp