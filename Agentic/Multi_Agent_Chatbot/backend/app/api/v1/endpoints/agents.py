from fastapi import APIRouter
from app.agents.registry import REGISTRY

router = APIRouter()


@router.get("")
async def list_agents() -> list[dict]:
    """Espone i domini al frontend (per badge, filtri, pannelli)."""
    return [
        {"key": a.key, "label": a.label, "description": a.description,
         "use_rag": a.use_rag}
        for a in REGISTRY.values()
    ]