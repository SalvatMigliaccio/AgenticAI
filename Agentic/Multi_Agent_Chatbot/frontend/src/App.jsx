import { useEffect, useMemo, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE || "/api/v1";
const CHAT_STREAM_ENDPOINT = `${API_BASE}/chat/stream`;

const routeColorMap = {
  crypto_pqc: "#2dbe74",
  eidas_compliance: "#f3a73f",
  software_eng: "#4aa6ff",
  general: "#9c8cf0",
};

function toPercent(value) {
  if (typeof value !== "number" || Number.isNaN(value)) return "-";
  return `${Math.max(0, Math.min(100, value * 100)).toFixed(1)}%`;
}

function newThreadId() {
  return `thread-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

function parseSSEBlock(block) {
  const lines = block.split("\n");
  let event = "message";
  const dataLines = [];

  for (const rawLine of lines) {
    const line = rawLine.trimEnd();
    if (!line || line.startsWith(":")) continue;
    if (line.startsWith("event:")) {
      event = line.slice(6).trim();
      continue;
    }
    if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trimStart());
    }
  }

  return { event, data: dataLines.join("\n") };
}

function scoreClass(score) {
  if (typeof score !== "number") return "neutral";
  if (score >= 4) return "good";
  if (score >= 3) return "mid";
  return "low";
}

function JudgePanel({ meta }) {
  if (!meta) return null;

  const judge = meta.judge || {};
  const judgePending = Boolean(meta.judgePending);
  const hasJudge = typeof judge.overall === "number";

  return (
    <section className="judge-panel">
      <header className="judge-head">
        <strong>LLM-as-a-Judge</strong>
        <span className={`judge-pill ${judgePending ? "loading" : hasJudge ? "ready" : "idle"}`}>
          {judgePending ? "Valutazione in corso" : hasJudge ? "Valutazione completata" : "Nessuna valutazione"}
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

export default function App() {
  const [query, setQuery] = useState("");
  const [pending, setPending] = useState(false);
  const [agents, setAgents] = useState([]);
  const [threadId, setThreadId] = useState(() => localStorage.getItem("thread_id") || newThreadId());
  const [messages, setMessages] = useState([
    {
      id: "welcome",
      role: "assistant",
      text: "Ciao. Sono pronto. In questo stage rispondo usando la knowledge locale indicizzata nel progetto.",
      meta: null,
    },
  ]);
  const [error, setError] = useState("");
  const [live, setLive] = useState({ route: "-", method: "-", confidence: null, judgeOverall: null });

  useEffect(() => {
    localStorage.setItem("thread_id", threadId);
  }, [threadId]);

  useEffect(() => {
    async function loadAgents() {
      try {
        const res = await fetch(`${API_BASE}/agents`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        setAgents(Array.isArray(data) ? data : []);
      } catch {
        setAgents([]);
      }
    }
    loadAgents();
  }, []);

  const activeThreadLabel = useMemo(() => threadId.slice(0, 18), [threadId]);

  function patchAssistantMessage(messageId, patch) {
    setMessages((prev) =>
      prev.map((msg) => {
        if (msg.id !== messageId) return msg;
        return {
          ...msg,
          ...(patch.text !== undefined ? { text: patch.text } : {}),
          meta: {
            ...(msg.meta || {}),
            ...(patch.meta || {}),
          },
        };
      })
    );
  }

  async function streamChat(queryText, currentThreadId, assistantId) {
    const response = await fetch(CHAT_STREAM_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: queryText, thread_id: currentThreadId }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    if (!response.body) {
      throw new Error("Streaming non disponibile dal backend.");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");

      while (true) {
        const sep = buffer.indexOf("\n\n");
        if (sep === -1) break;

        const block = buffer.slice(0, sep);
        buffer = buffer.slice(sep + 2);
        const { event, data } = parseSSEBlock(block);

        if (!data) continue;

        let parsed;
        try {
          parsed = JSON.parse(data);
        } catch {
          continue;
        }

        if (event === "route") {
          const routePatch = {
            route: parsed.route || "general",
            confidence: parsed.confidence,
            method: parsed.method || "-",
            routePending: false,
          };
          setLive((prev) => ({ ...prev, ...routePatch }));
          patchAssistantMessage(assistantId, { meta: routePatch });
          continue;
        }

        if (event === "judge") {
          setLive((prev) => ({ ...prev, judgeOverall: parsed.overall ?? null }));
          patchAssistantMessage(assistantId, {
            meta: {
              judge: parsed,
              judgePending: false,
            },
          });
          continue;
        }

        if (event === "answer") {
          patchAssistantMessage(assistantId, {
            text: parsed.answer || "Nessuna risposta disponibile.",
          });
          continue;
        }

        if (event === "done") {
          patchAssistantMessage(assistantId, {
            meta: {
              trace: Array.isArray(parsed.trace) ? parsed.trace : [],
              complete: true,
              routePending: false,
              judgePending: false,
            },
          });
        }
      }
    }
  }

  async function sendMessage(evt) {
    evt.preventDefault();
    const content = query.trim();
    if (!content || pending) return;

    const userMsg = {
      id: `u-${Date.now()}`,
      role: "user",
      text: content,
      meta: null,
    };
    setMessages((prev) => [...prev, userMsg]);
    setQuery("");
    setPending(true);
    setError("");
    setLive({ route: "-", method: "-", confidence: null, judgeOverall: null });

    const assistantId = `a-${Date.now()}`;
    const placeholderMsg = {
      id: assistantId,
      role: "assistant",
      text: "Sto elaborando la richiesta...",
      meta: {
        route: null,
        confidence: null,
        method: null,
        routePending: true,
        judgePending: true,
        complete: false,
        judge: {},
        trace: [],
      },
    };
    setMessages((prev) => [...prev, placeholderMsg]);

    try {
      await streamChat(content, threadId, assistantId);
    } catch {
      setError("Errore durante la chiamata API. Controlla backend e proxy Nginx.");
      patchAssistantMessage(assistantId, {
        text: "Non sono riuscito a completare lo stream. Riprova tra pochi secondi.",
      });
    } finally {
      setPending(false);
    }
  }

  function resetThread() {
    const fresh = newThreadId();
    setThreadId(fresh);
    setMessages([
      {
        id: "welcome-reset",
        role: "assistant",
        text: "Nuovo thread creato. Puoi iniziare una nuova conversazione.",
        meta: null,
      },
    ]);
    setError("");
  }

  return (
    <div className="page-shell">
      <aside className="left-panel">
        <h1>AgenticAI Console</h1>
        <p className="subhead">Knowledge-first chat per testare routing, giudice e trace.</p>

        <div className="thread-card">
          <div>
            <strong>Thread</strong>
            <div className="mono">{activeThreadLabel}</div>
          </div>
          <button type="button" onClick={resetThread}>Nuovo thread</button>
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
              <p>{msg.text}</p>
              {msg.meta && (
                <footer>
                  <span>Confidence: {toPercent(msg.meta.confidence)}</span>
                  <span>Judge overall: {msg.meta.judge?.overall ?? "-"}</span>
                  <span>Trace steps: {msg.meta.trace?.length ?? 0}</span>
                </footer>
              )}
              {msg.role === "assistant" && msg.meta && <JudgePanel meta={msg.meta} />}
            </article>
          ))}
          {pending && <div className="typing">Elaborazione in corso...</div>}
        </div>

        <form className="composer" onSubmit={sendMessage}>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Scrivi una domanda..."
            rows={3}
          />
          <div className="composer-actions">
            <span className="hint">Endpoint: {CHAT_STREAM_ENDPOINT}</span>
            <button type="submit" disabled={pending}>Invia</button>
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
  );
}
