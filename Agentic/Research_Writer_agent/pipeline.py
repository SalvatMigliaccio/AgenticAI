from agents import build_researcher, build_writer


# ---------------------------------------------------------------------------
# Pipeline — coordinates the two agents sequentially.
#
# In CrewAI this coordination is handled by the Crew class with
# Process.sequential. Here we do it explicitly in plain Python:
#   1. Run the researcher agent → get research report
#   2. Pass report to the writer function → get final article
#
# This explicit approach is more transparent — you can inspect,
# log, or modify the intermediate output between steps.
# ---------------------------------------------------------------------------

def run_pipeline(topic: str) -> dict:
    """
    Runs the full research → writing pipeline for a given topic.

    Returns a dict with:
        research : the raw research report produced by the researcher agent
        article  : the final polished article produced by the writer
    """

    # ------------------------------------------------------------------
    # Step 1 — Research
    # The researcher runs its ReAct loop, calling search and scrape tools
    # as many times as needed, then produces a structured markdown report.
    # ------------------------------------------------------------------
    print("\n" + "─"*60)
    print("  STEP 1 — Researcher agent running...")
    print("─"*60 + "\n")

    researcher = build_researcher()
    research_result = researcher.invoke({"input": topic})

    # AgentExecutor returns a dict — "output" is the Final Answer string
    research_report = research_result["output"]

    print("\n" + "─"*60)
    print("  RESEARCH REPORT COMPLETE")
    print("─"*60)
    print(research_report)

    # ------------------------------------------------------------------
    # Step 2 — Writing
    # The writer receives the research report as plain text context
    # and produces the final article in a single LLM call.
    # ------------------------------------------------------------------
    print("\n" + "─"*60)
    print("  STEP 2 — Writer agent running...")
    print("─"*60 + "\n")

    article = build_writer(research_report=research_report, topic=topic)

    return {
        "research": research_report,
        "article": article,
    }