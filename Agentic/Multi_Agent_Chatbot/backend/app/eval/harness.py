import asyncio

# Dataset minimale: (domanda, dominio_atteso). Espandilo col tuo corpus.
EVAL_SET: list[tuple[str, str]] = [
    ("Qual è la differenza tra ML-KEM e ML-DSA?", "crypto_pqc"),
    ("Come pianifico la migrazione a crittografia post-quantum?", "crypto_pqc"),
    ("Che differenza c'è tra firma FEA e QES?", "eidas_compliance"),
    ("Quali sono i livelli di garanzia LoA in eIDAS?", "eidas_compliance"),
    ("Come scrivo un test asincrono con pytest?", "software_eng"),
]


async def run_eval(graph) -> dict:
    routing_ok, overalls, rows = 0, [], []
    for query, expected in EVAL_SET:
        cfg = {"configurable": {"thread_id": f"eval-{hash(query)}"}}
        out = await graph.ainvoke({"user_query": query}, config=cfg)
        route = out.get("route", "")
        overall = out.get("judge", {}).get("overall", 0.0)
        hit = route == expected
        routing_ok += int(hit)
        overalls.append(overall)
        rows.append({"query": query, "expected": expected, "got": route,
                     "routing_ok": hit, "judge_overall": overall})
    n = len(EVAL_SET)
    return {
        "routing_accuracy": round(routing_ok / n, 3),
        "avg_judge_overall": round(sum(overalls) / n, 3),
        "rows": rows,
    }


if __name__ == "__main__":
    from app.agents.graph import build_graph

    async def _m():
        print(await run_eval(build_graph()))
    asyncio.run(_m())