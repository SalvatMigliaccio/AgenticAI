from app.core.config import settings
from app.agents.state import GraphState
from app.agents.registry import get_agent, resolve_model, FALLBACK_KEY
from app.agents.prompts import build_specialist_messages, build_reflection_messages
from app.llm.provider import chat
from app.rag.retriever import retrieve


def _fallback_answer(agent, context: list[str]) -> str:
    if context:
        snippets = "\n".join(f"- {item}" for item in context[:3])
        return (
            "Il backend LLM non è disponibile al momento. "
            f"Per il dominio {agent.label}, i passaggi recuperati sono:\n{snippets}"
        )
    return (
        "Il backend LLM non è disponibile al momento e non posso generare "
        "una risposta completa in questa esecuzione."
    )


async def specialist_node(state: GraphState) -> dict:
    route = state.get("route", FALLBACK_KEY)
    agent = get_agent(route)
    query = state["user_query"]
    lang = state.get("detected_lang", "italiano")

    # RAG: recupero il contesto solo se il dominio lo prevede. Lo riuso se già presente
    # (nel giro di reflection non ha senso rifare la retrieval).
    context = state.get("retrieved_context")
    rag_status = "cached" if context is not None else "disabled"
    if context is None:
        if agent.use_rag:
            try:
                context = await retrieve(agent.collection, query)
                rag_status = "hit" if context else "miss"
            except Exception:
                # La RAG e opzionale: se fallisce, lo specialista risponde comunque.
                context = []
                rag_status = "error"
        else:
            context = []
            rag_status = "disabled"

    model = resolve_model(agent)   # dev → base model; prod → adapter LoRA del dominio
    prev = state.get("judge")
    is_reflection = bool(prev and not prev["passed"])

    if is_reflection:
        # Rigenero tenendo conto della critica del giudice.
        messages = build_reflection_messages(
            route, query, context, lang,
            state.get("draft_answer", ""), prev["feedback"],
        )
        retry = state.get("retry_count", 0) + 1
    else:
        messages = build_specialist_messages(route, query, context, lang)
        retry = state.get("retry_count", 0)

    try:
        answer = await chat(messages, model=model, temperature=settings.SPECIALIST_TEMPERATURE)
    except Exception:
        answer = _fallback_answer(agent, context)

    trace = state.get("trace", []) + [{
        "step": "specialist",
        "domain": route,
        "model": model,
        "reflection": is_reflection,
        "used_rag": bool(context),
        "rag_status": rag_status,
    }]
    return {
        "draft_answer": answer,
        "retrieved_context": context,   # persisto per il giudice e per l'eventuale reflection
        "retry_count": retry,
        "trace": trace,
    }