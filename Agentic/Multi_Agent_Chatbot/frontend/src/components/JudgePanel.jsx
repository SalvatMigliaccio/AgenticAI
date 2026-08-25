import { scoreClass } from "../lib/api";

export default function JudgePanel({ meta }) {
  if (!meta) return null;

  const judge = meta.judge || {};
  const judgePending = Boolean(meta.judgePending);
  const hasJudge = typeof judge.overall === "number";
  const showJudge = Boolean(meta.answerVisible) && (judgePending || hasJudge);

  if (!showJudge) return null;

  return (
    <section className="judge-panel">
      <header className="judge-head">
        <strong>LLM-as-a-Judge</strong>
        <span className={`judge-pill ${judgePending ? "loading" : hasJudge ? "ready" : "idle"}`}>
          {judgePending
            ? "Valutazione in corso"
            : hasJudge
              ? "Valutazione completata"
              : "Nessuna valutazione"}
        </span>
      </header>

      {judgePending && (
        <div className="judge-loading">
          <span className="loader" aria-hidden="true" />
          <div>
            <p>Il giudice sta analizzando la risposta...</p>
            <small>Controllo di faithfulness, relevance, completeness e safety.</small>
          </div>
        </div>
      )}

      {hasJudge && (
        <>
          <div className="judge-grid">
            <div className={`score-card ${scoreClass(judge.faithfulness)}`}>
              <span>Faithfulness</span>
              <strong>{judge.faithfulness ?? "-"}/5</strong>
            </div>
            <div className={`score-card ${scoreClass(judge.relevance)}`}>
              <span>Relevance</span>
              <strong>{judge.relevance ?? "-"}/5</strong>
            </div>
            <div className={`score-card ${scoreClass(judge.completeness)}`}>
              <span>Completeness</span>
              <strong>{judge.completeness ?? "-"}/5</strong>
            </div>
            <div className={`score-card ${scoreClass(judge.safety)}`}>
              <span>Safety</span>
              <strong>{judge.safety ?? "-"}/5</strong>
            </div>
          </div>

          <div className="judge-summary">
            <span>
              Overall: <strong>{judge.overall ?? "-"}</strong>
            </span>
            <span className={`verdict ${judge.passed ? "pass" : "retry"}`}>
              {judge.passed ? "PASS" : "RETRY"}
            </span>
          </div>

          {judge.feedback && <p className="judge-feedback">{judge.feedback}</p>}
        </>
      )}
    </section>
  );
}
