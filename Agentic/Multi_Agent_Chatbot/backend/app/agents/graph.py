from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.core.config import settings
from app.agents.state import GraphState
from app.agents.nodes.preprocess import preprocess_node
from app.agents.nodes.router import router_node
from app.agents.nodes.specialist import specialist_node
from app.agents.nodes.judge import judge_node
from app.agents.nodes.finalize import finalize_node


def _should_retry(state: GraphState) -> str:
    """Dopo il giudice: se ha bocciato e restano tentativi, torna allo specialista."""
    j = state.get("judge")
    retries = state.get("retry_count", 0)
    if j and not j["passed"] and retries < settings.MAX_REFLECTION_RETRIES:
        return "retry"
    return "finalize"


def build_graph(checkpointer=None):
    """Costruisce e compila il grafo.

    checkpointer=None → MemorySaver (dev). In prod passeremo il PostgresSaver
    (Tappa 4) per persistere le conversazioni tra i turni.
    """
    g = StateGraph(GraphState)

    g.add_node("preprocess", preprocess_node)
    g.add_node("router", router_node)
    g.add_node("specialist", specialist_node)
    g.add_node("judge", judge_node)
    g.add_node("finalize", finalize_node)

    g.add_edge(START, "preprocess")
    g.add_edge("preprocess", "router")
    g.add_edge("router", "specialist")     # il router ha già scelto: route è nello stato
    g.add_edge("specialist", "judge")
    g.add_conditional_edges(               # il cuore del loop di reflection
        "judge", _should_retry,
        {"retry": "specialist", "finalize": "finalize"},
    )
    g.add_edge("finalize", END)

    return g.compile(checkpointer=checkpointer or MemorySaver())


# --- Smoke test: `python -m app.agents.graph` (con Ollama avviato) ---
if __name__ == "__main__":
    import asyncio

    async def _t() -> None:
        graph = build_graph()
        # thread_id: identifica la conversazione per la memoria del checkpointer.
        cfg = {"configurable": {"thread_id": "test-1"}}
        out = await graph.ainvoke(
            {"user_query": "Qual è la differenza tra ML-KEM e ML-DSA?"}, config=cfg
        )
        print("ROUTE     :", out["route"], f'(conf={out["route_confidence"]:.3f}, {out["route_method"]})')
        print("JUDGE     :", out["judge"])
        print("ANSWER    :", out["final_answer"][:500])
        print("TRACE     :")
        for step in out["trace"]:
            print("  -", step)

    asyncio.run(_t())