from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class JudgeVerdict(TypedDict):
    """Output strutturato del giudice (la rubrica)."""
    faithfulness: int      # 1-5: la risposta è fedele al contesto recuperato?
    relevance: int         # 1-5: risponde davvero alla domanda?
    completeness: int      # 1-5: è completa?
    safety: int            # 1-5: niente contenuti problematici/inventati pericolosi?
    overall: float         # media calcolata da noi
    passed: bool           # overall >= soglia ?
    feedback: str          # cosa migliorare (usato dal loop di reflection)


class GraphState(TypedDict, total=False):
    # `messages` accumula lo storico. `add_messages` è un "reducer": invece di
    # sovrascrivere, APPENDE i nuovi messaggi. È così che il grafo ha memoria.
    messages: Annotated[list[BaseMessage], add_messages]

    user_query: str            # la domanda corrente, normalizzata dal preprocess
    detected_lang: str         # lingua rilevata (per rispondere nella stessa lingua)

    route: str                 # chiave del dominio scelto (es. "crypto_pqc")
    route_confidence: float    # confidenza del router (0-1)
    route_method: str          # "embedding" | "llm_fallback" | "keyword_fallback" (per il trace)

    retrieved_context: list[str]  # passaggi recuperati dalla RAG (se il dominio la usa)

    draft_answer: str          # risposta prodotta dallo specialista
    judge: JudgeVerdict        # verdetto del giudice
    retry_count: int           # quante volte abbiamo già rigenerato

    final_answer: str          # risposta finale consegnata all'utente
    trace: list[dict]          # log dei passaggi, lo mostriamo nel frontend