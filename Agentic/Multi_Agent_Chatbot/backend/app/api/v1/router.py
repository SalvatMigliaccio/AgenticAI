from fastapi import APIRouter
from app.api.v1.endpoints import chat, agents, evaluation

api_router = APIRouter()
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(evaluation.router, prefix="/eval", tags=["eval"])