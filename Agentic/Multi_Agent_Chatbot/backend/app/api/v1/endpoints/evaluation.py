from fastapi import APIRouter, Request
from app.eval.harness import run_eval

router = APIRouter()


@router.post("/run")
async def run_evaluation(request: Request) -> dict:
    return await run_eval(request.app.state.graph)