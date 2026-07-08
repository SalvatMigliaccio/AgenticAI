from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.checkpointer import get_checkpointer
from app.agents.graph import build_graph
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Un solo checkpointer e un solo grafo per tutta la vita del processo.
    # In dev senza Postgres: get_checkpointer(use_postgres=False).
    async with get_checkpointer(use_postgres=True) as cp:
        app.state.graph = build_graph(checkpointer=cp)
        yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)
app.include_router(api_router, prefix=settings.API_V1_STR)