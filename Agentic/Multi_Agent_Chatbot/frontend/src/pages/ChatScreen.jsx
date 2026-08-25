import { CHAT_STREAM_ENDPOINT, toPercent } from "../lib/api";
import { routeColorMap } from "../lib/content";
import JudgePanel from "../components/JudgePanel";

function onComposerKeyDown(evt) {
  if (evt.key === "Enter" && !evt.shiftKey) {
    evt.preventDefault();
    evt.currentTarget.form?.requestSubmit();
  }
}

export default function ChatScreen({
  query,
  setQuery,
  pending,
  agents,
  messages,
  sendMessage,
  resetThread,
  error,
  live,
  activeThreadLabel,
  onBackHome,
}) {
  return (
    <div className="chat-screen">
      <header className="chat-topbar">
        <button type="button" className="ghost home-back" onClick={onBackHome}>
          ← Home
        </button>
        <h1>Console</h1>
      </header>

      <div className="page-shell">
        <aside className="left-panel">
          <p className="subhead">Chat per testare routing, giudice e trace end-to-end.</p>

          <div className="thread-card">
            <div>
              <strong>Thread</strong>
              <div className="mono">{activeThreadLabel}</div>
            </div>
            <button type="button" onClick={resetThread}>
              Nuovo thread
            </button>
          </div>

          <h2>Domini</h2>
          <ul className="agent-list">
            {agents.map((agent) => (
              <li key={agent.key}>
                <span className="dot" style={{ background: routeColorMap[agent.key] || "#8a8a8a" }} />
                <div>
                  <strong>{agent.label}</strong>
                  <p>{agent.description}</p>
                </div>
              </li>
            ))}
            {agents.length === 0 && <li className="empty">Nessun dominio disponibile dal backend.</li>}
          </ul>
        </aside>

        <main className="chat-panel">
          <div className="messages">
            {messages.map((msg) => (
              <article key={msg.id} className={`msg ${msg.role}`}>
                <header>
                  <span>{msg.role === "user" ? "Tu" : "Assistente"}</span>
                  {msg.meta?.route && (
                    <span className="badge" style={{ borderColor: routeColorMap[msg.meta.route] || "#777" }}>
                      {msg.meta.route}
                    </span>
                  )}
                </header>
                {msg.role === "assistant" ? (
                  <div className="assistant-layout">
                    <div className="assistant-answer">
                      <p>{msg.text}</p>
                      {msg.meta && (
                        <footer>
                          <span>Confidence: {toPercent(msg.meta.confidence)}</span>
                          <span>Judge overall: {msg.meta.judge?.overall ?? "-"}</span>
                          <span>Trace steps: {msg.meta.trace?.length ?? 0}</span>
                        </footer>
                      )}
                    </div>
                    {msg.meta && <JudgePanel meta={msg.meta} />}
                  </div>
                ) : (
                  <p>{msg.text}</p>
                )}
              </article>
            ))}
            {pending && <div className="typing">Elaborazione in corso...</div>}
          </div>

          <form className="composer" onSubmit={sendMessage}>
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={onComposerKeyDown}
              placeholder="Scrivi una domanda..."
              rows={3}
            />
            <div className="composer-actions">
              <span className="hint">Endpoint: {CHAT_STREAM_ENDPOINT}</span>
              <button type="submit" disabled={pending}>
                Invia
              </button>
            </div>
          </form>

          {pending && (
            <section className="live-box">
              <strong>Live routing</strong>
              <div className="live-grid">
                <span>Route: {live.route}</span>
                <span>Metodo: {live.method}</span>
                <span>Confidence: {toPercent(live.confidence)}</span>
                <span>Judge overall: {live.judgeOverall ?? "-"}</span>
              </div>
            </section>
          )}

          {error && <div className="error-box">{error}</div>}
        </main>
      </div>
    </div>
  );
}
