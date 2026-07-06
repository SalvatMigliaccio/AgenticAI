"""
Primo nodo: normalizza l'input, rileva la lingua, inizializza i contatori e mette il messaggio nello storico
"""

from langchain_core.messages import HumanMessage
from app.agents.state import GraphState


def _detect_lang(text: str) -> str:
    """Rilevamento lingua leggero e senza dipendenze (euristica su stopword).

    Sufficiente per decidere in che lingua far rispondere lo specialista.
    In futuro si può sostituire con langdetect/fasttext senza toccare il resto.
    """
    it_makers = {"il", "la", "che", "di", "e", "è", "come", "cosa", "quale", "perché"}
    tokens = {t.strip(".,!?;:()[]{}").lower() for t in text.split()}
    return "italiano" if tokens & it_makers else "inglese"

async def preprocess_node(state: GraphState) -> dict:
    # Guardrail input minimale: normalizza e gestisci il vuoto.
    raw = (state.get("user_query") or "").strip()
    if not raw:
        raw = "(messaggio vuoto)"

    lang = _detect_lang(raw)

    # Inizializziamo retry_count e apriamo il trace per questo turno.
    return {
        "user_query": raw,
        "detected_lang": lang,
        "retry_count": 0,
        "messages": [HumanMessage(content=raw)],  # add_messages APPENDE allo storico
        "trace": [{"step": "preprocess", "lang": lang}],
    }
