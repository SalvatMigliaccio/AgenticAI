import json
import re

from app.core.config import settings
from app.agents.state import GraphState, JudgeVerdict
from app.agents.prompts import build_judge_messages
from app.llm.provider import chat


def _clamp(v: object) -> int:
    """Porta un punteggio nel range 1..5 in modo robusto."""
    try:
        return max(1, min(5, int(round(float(v)))))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 3


def _parse_verdict(raw: str) -> JudgeVerdict:
    data = None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Il modello ha aggiunto testo attorno al JSON: estraggo il primo oggetto {...}.
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group(0))
            except json.JSONDecodeError:
                data = None

    if not isinstance(data, dict):
        # Giudice illeggibile: verdetto neutro e PASS, per non bloccare l'utente.
        return JudgeVerdict(
            faithfulness=3, relevance=3, completeness=3, safety=3,
            overall=float(settings.JUDGE_PASS_THRESHOLD), passed=True,
            feedback="(giudice non interpretabile: verdetto neutro)",
        )

    f = _clamp(data.get("faithfulness", 3))
    r = _clamp(data.get("relevance", 3))
    c = _clamp(data.get("completeness", 3))
    s = _clamp(data.get("safety", 3))
    # Media pesata: fedeltà e pertinenza contano più di completezza e safety.
    overall = round(0.35 * f + 0.35 * r + 0.20 * c + 0.10 * s, 2)
    return JudgeVerdict(
        faithfulness=f, relevance=r, completeness=c, safety=s,
        overall=overall, passed=overall >= settings.JUDGE_PASS_THRESHOLD,
        feedback=str(data.get("feedback", "")),
    )


async def judge_node(state: GraphState) -> dict:
    query = state["user_query"]
    answer = state.get("draft_answer", "")
    context = state.get("retrieved_context", [])

    try:
        raw = await chat(
            build_judge_messages(query, answer, context),
            model=settings.LLM_BASE_MODEL,      # il giudice è sempre il base model, imparziale
            temperature=settings.JUDGE_TEMPERATURE,
            json_mode=True,
            max_tokens=300,
        )
        verdict = _parse_verdict(raw)
    except Exception:
        verdict = JudgeVerdict(
            faithfulness=3, relevance=3, completeness=3, safety=3,
            overall=float(settings.JUDGE_PASS_THRESHOLD), passed=True,
            feedback="(giudice non disponibile: verdetto neutro)",
        )

    trace = state.get("trace", []) + [{
        "step": "judge",
        "overall": verdict["overall"],
        "passed": verdict["passed"],
        "scores": {
            "faithfulness": verdict["faithfulness"],
            "relevance": verdict["relevance"],
            "completeness": verdict["completeness"],
            "safety": verdict["safety"],
        },
    }]
    return {"judge": verdict, "trace": trace}