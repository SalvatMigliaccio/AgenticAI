import json
from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/stream")
async def chat_stream_endpoint(req: ChatRequest, request: Request):
    graph = request.app.state.graph
    config = {"configurable": {"thread_id": req.thread_id}}

    async def event_gen():
        final_state: dict = {}
        # stream_mode="updates": ogni item è {nome_nodo: delta_di_stato}.
        async for update in graph.astream(
            {"user_query": req.query}, config=config, stream_mode="updates"
        ):
            for node, delta in update.items():
                final_state.update(delta)
                if node == "router":
                    yield {"event": "route", "data": json.dumps({
                        "route": delta.get("route"),
                        "confidence": delta.get("route_confidence"),
                        "method": delta.get("route_method"),
                    })}
                elif node == "specialist":
                    specialist_reflection = next(
                        (s.get("reflection") for s in delta.get("trace", [])
                         if s.get("step") == "specialist"), False
                    )
                    yield {"event": "specialist", "data": json.dumps({
                        "reflection": specialist_reflection,
                        "preview": delta.get("draft_answer", ""),
                    })}
                    # Avvio esplicito dello stato judge nel frontend: il giudice parte
                    # subito dopo lo specialista e può valutare mentre mostriamo la preview.
                    yield {"event": "judge_status", "data": json.dumps({"status": "running"})}
                elif node == "judge":
                    yield {"event": "judge", "data": json.dumps(delta.get("judge", {}))}
                    yield {"event": "judge_status", "data": json.dumps({"status": "done"})}
                elif node == "finalize":
                    yield {"event": "answer", "data": json.dumps({
                        "answer": delta.get("final_answer", ""),
                    })}
        # Chiusura: mando il trace completo per il pannello di debug del frontend.
        yield {"event": "done", "data": json.dumps({"trace": final_state.get("trace", [])})}

    return EventSourceResponse(event_gen())


@router.post("", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest, request: Request) -> ChatResponse:
    """Versione sincrona (comoda per test e per l'eval harness)."""
    graph = request.app.state.graph
    config = {"configurable": {"thread_id": req.thread_id}}
    out = await graph.ainvoke({"user_query": req.query}, config=config)
    return ChatResponse(
        answer=out.get("final_answer", ""),
        route=out.get("route", ""),
        route_confidence=out.get("route_confidence", 0.0),
        judge=out.get("judge", {}),
        trace=out.get("trace", []),
    )