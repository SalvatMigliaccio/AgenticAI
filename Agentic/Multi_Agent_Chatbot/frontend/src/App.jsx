import { useEffect, useMemo, useRef, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE || "/api/v1";
const CHAT_STREAM_ENDPOINT = `${API_BASE}/chat/stream`;
const STREAM_TIMEOUT_MS = Number(import.meta.env.VITE_STREAM_TIMEOUT_MS || 120000);
const GITHUB_MAIN_URL = import.meta.env.VITE_GITHUB_MAIN_URL || "https://github.com";
const GITHUB_BACKEND_URL = import.meta.env.VITE_GITHUB_BACKEND_URL || "https://github.com";
const GITHUB_FRONTEND_URL = import.meta.env.VITE_GITHUB_FRONTEND_URL || "https://github.com";

const routeColorMap = {
  crypto_pqc: "#2dbe74",
  eidas_compliance: "#f3a73f",
  software_eng: "#4aa6ff",
  general: "#9c8cf0",
};

const techCards = [
  { title: "LangGraph Agents", text: "Pipeline con router, specialist, LLM-as-a-Judge e reflection loop." },
  { title: "Hybrid RAG", text: "Retrieval su knowledge locale con indexing Qdrant e fallback robusti." },
  { title: "FastAPI + SSE", text: "Streaming eventi live (route, judge, answer) fino al finalize." },
  { title: "Nginx Gateway", text: "Reverse proxy + load balancer verso backend multipli per alta concorrenza." },
  { title: "Postgres Checkpointer", text: "Memoria conversazionale persistente per thread e valutazioni." },
  { title: "Redis + Cache", text: "Base pronta per caching semantico e ottimizzazione delle latenze." },
];

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

function MermaidArchitecture() {
  const ref = useRef(null);

  useEffect(() => {
    let mounted = true;

    async function renderDiagram() {
      try {
        const mermaidModule = await import("mermaid");
        const mermaid = mermaidModule.default;

        mermaid.initialize({
          startOnLoad: false,
          theme: "neutral",
          securityLevel: "loose",
          flowchart: {
            curve: "basis",
            htmlLabels: true,
          },
        });

        const definition = `
flowchart LR
  U[User Browser] --> G[Nginx Gateway]
  G --> B1[Backend 1 - FastAPI]
  G --> B2[Backend 2 - FastAPI]
  B1 --> L[LangGraph Pipeline]
  B2 --> L
  L --> R[Router]
  R --> S[Specialist]
  S --> J[LLM-as-a-Judge]
  J --> F[Finalize]
  S --> Q[(Qdrant)]
  B1 --> P[(Postgres Checkpointer)]
  B1 --> C[(Redis)]
  B2 --> P
  B2 --> C
  S --> O[(Ollama / LLM Server)]
  J --> O
`;

        const id = `arch-${Date.now().toString(36)}`;
        const { svg } = await mermaid.render(id, definition);

        if (mounted && ref.current) {
          ref.current.innerHTML = svg;
        }
      } catch {
        if (mounted && ref.current) {
          ref.current.innerHTML = "<p>Diagramma Mermaid non disponibile.</p>";
        }
      }
    }

    renderDiagram();
    return () => {
      mounted = false;
    };
  }, []);

  return <div className="mermaid-canvas" ref={ref} aria-label="Architecture diagram" />;
}

function HomePage({ onStartChat, agents, architectureRef }) {
  return (
    <div className="home-page">
      <header className="home-nav">
        <div className="brand">
          <span className="brand-dot" />
          <strong>AgenticAI</strong>
        </div>
        <nav>
          <a href="#features">Features</a>
          <a href="#technology">Technology</a>
          <a href="#architecture">Architecture</a>
          <button type="button" className="nav-cta" onClick={onStartChat}>Entra in chat</button>
        </nav>
      </header>

      <section className="hero" id="top">
        <p className="hero-kicker">Multi-agent assistant platform</p>
        <h1>
          The leading AI
          <br />
          Knowledge Console
        </h1>
        <p className="hero-lead">
          Chatta con specialisti orchestrati, osserva routing e judging in tempo reale,
          e lavora su una pipeline progettata per affidabilita, tracciabilita e scale-out.
        </p>
        <div className="hero-actions">
          <button type="button" onClick={onStartChat}>Start chat</button>
          <button
            type="button"
            className="ghost"
            onClick={() => architectureRef.current?.scrollIntoView({ behavior: "smooth", block: "start" })}
          >
            Vedi architettura
          </button>
          <a className="ghost github-link" href={GITHUB_MAIN_URL} target="_blank" rel="noreferrer">
            Go to GitHub
          </a>
        </div>
      </section>

      <section className="modes-card" id="features">
        <h2>Three AI Modes</h2>
        <div className="mode-grid">
          <article>
            <small>AI CHAT</small>
            <h3>Chat with knowledge</h3>
            <p>Una domanda, un thread, risposta con trace e controllo qualitativo.</p>
          </article>
          <article>
            <small>AI OBSERVABILITY</small>
            <h3>Compare reasoning steps</h3>
            <p>Route, confidence, judge e feedback mostrati live nello stesso flusso.</p>
          </article>
          <article className="dark">
            <small>AI TEAM</small>
            <h3>Collaboration pipeline</h3>
            <p>Router -&gt; Specialist -&gt; Judge -&gt; Finalize con supporto reflection.</p>
          </article>
        </div>
      </section>

      <section className="technology" id="technology">
        <h2>Technology Stack</h2>
        <p>
          L'app combina retrieval locale, orchestrazione ad agenti e valutazione automatica della qualita.
          Le componenti sotto sono quelle realmente in uso nel progetto.
        </p>
        <div className="tech-grid">
          {techCards.map((card) => (
            <article key={card.title} className="tech-card">
              <h3>{card.title}</h3>
              <p>{card.text}</p>
            </article>
          ))}
        </div>

        <div className="github-cards">
          <a href={GITHUB_MAIN_URL} target="_blank" rel="noreferrer" className="github-card">
            <strong>Project Repository</strong>
            <span>Spec, compose, training, deployment</span>
          </a>
          <a href={GITHUB_BACKEND_URL} target="_blank" rel="noreferrer" className="github-card">
            <strong>Backend Source</strong>
            <span>FastAPI, LangGraph, RAG, judge loop</span>
          </a>
          <a href={GITHUB_FRONTEND_URL} target="_blank" rel="noreferrer" className="github-card">
            <strong>Frontend Source</strong>
            <span>Hero landing, SSE chat, observability UI</span>
          </a>
        </div>
      </section>

      <section className="architecture" id="architecture" ref={architectureRef}>
        <h2>Architecture Overview</h2>
        <p>
          Di seguito trovi un diagramma visuale in pagina. Se vuoi, nel prossimo step lo trasformiamo
          in un SVG/diagramma definitivo con i tuoi blocchi personalizzati.
        </p>

        <div className="diagram mermaid-shell">
          <MermaidArchitecture />
        </div>

        <div className="arch-foot">
          <span>Domini caricati: {agents.length}</span>
          <button type="button" onClick={onStartChat}>Apri chat operativa</button>
        </div>
      </section>
    </div>
  );
}

function ChatScreen({
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
  function onComposerKeyDown(evt) {
    if (evt.key === "Enter" && !evt.shiftKey) {
      evt.preventDefault();
      evt.currentTarget.form?.requestSubmit();
    }
  }

  return (
    <div className="chat-screen">
      <header className="chat-topbar">
        <button type="button" className="ghost home-back" onClick={onBackHome}>← Home</button>
        <h1>AgenticAI Console</h1>
      </header>

      <div className="page-shell">
        <aside className="left-panel">
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
    </div>
  );
}

export default function App() {
  const architectureRef = useRef(null);
  const typingTimersRef = useRef(new Map());
  const [screen, setScreen] = useState("home");
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

  function stopPreviewAnimation(messageId) {
    const timer = typingTimersRef.current.get(messageId);
    if (timer) {
      clearInterval(timer);
      typingTimersRef.current.delete(messageId);
    }
  }

  function animatePreview(messageId, fullText) {
    if (!fullText) return;
    stopPreviewAnimation(messageId);

    let index = 0;
    const step = Math.max(8, Math.floor(fullText.length / 75));
    const timer = setInterval(() => {
      index = Math.min(fullText.length, index + step);
      patchAssistantMessage(messageId, { text: fullText.slice(0, index) });
      if (index >= fullText.length) {
        stopPreviewAnimation(messageId);
      }
    }, 20);

    typingTimersRef.current.set(messageId, timer);
  }

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
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), STREAM_TIMEOUT_MS);

    const response = await fetch(CHAT_STREAM_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: queryText, thread_id: currentThreadId }),
      signal: controller.signal,
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

    try {
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

          if (event === "specialist") {
            if (typeof parsed.preview === "string" && parsed.preview.trim()) {
              animatePreview(assistantId, parsed.preview);
            }
            patchAssistantMessage(assistantId, {
              meta: {
                specialistPending: false,
                judgePending: true,
              },
            });
            continue;
          }

          if (event === "judge_status") {
            patchAssistantMessage(assistantId, {
              meta: {
                judgePending: parsed.status === "running",
              },
            });
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
            stopPreviewAnimation(assistantId);
            patchAssistantMessage(assistantId, {
              text: parsed.answer || "Nessuna risposta disponibile.",
            });
            continue;
          }

          if (event === "done") {
            stopPreviewAnimation(assistantId);
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
    } finally {
      clearTimeout(timeoutId);
      stopPreviewAnimation(assistantId);
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
        specialistPending: true,
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
    } catch (err) {
      stopPreviewAnimation(assistantId);
      const timeoutMessage =
        err instanceof DOMException && err.name === "AbortError"
          ? "La richiesta ha superato il tempo massimo. Riprova con una domanda più specifica."
          : "Errore durante la chiamata API. Controlla backend e proxy Nginx.";
      setError(timeoutMessage);
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
    setLive({ route: "-", method: "-", confidence: null, judgeOverall: null });
  }

  if (screen === "home") {
    return <HomePage onStartChat={() => setScreen("chat")} agents={agents} architectureRef={architectureRef} />;
  }

  return (
    <ChatScreen
      query={query}
      setQuery={setQuery}
      pending={pending}
      agents={agents}
      messages={messages}
      sendMessage={sendMessage}
      resetThread={resetThread}
      error={error}
      live={live}
      activeThreadLabel={activeThreadLabel}
      onBackHome={() => setScreen("home")}
    />
  );
}
