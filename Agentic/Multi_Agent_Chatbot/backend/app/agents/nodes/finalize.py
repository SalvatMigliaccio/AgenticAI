from langchain_core.messages import AIMessage
from app.agents.state import GraphState

async def finalize_node(state: GraphState) -> dict:
    """Nodo finale: restituisce la risposta all'utente, eventualmente con un messaggio di errore."""
    answer = state.get("draft_answer", "")
    trace = state.get("trace", []) + [{"step": "finalize"}]
    return {
        "final_answer": answer,
        "messages": [AIMessage(content=answer)],   # entra nella memoria conversazionale
        "trace": trace,
    }