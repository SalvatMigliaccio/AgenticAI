import { GITHUB_BACKEND_URL, GITHUB_FRONTEND_URL, GITHUB_MAIN_URL } from "../lib/api";
import { apiEndpoints, factChips, pipelineSteps, statusColumns, techCards } from "../lib/content";

export default function HomePage({ onStartChat, agents, architectureRef }) {
  return (
    <div className="home-page">
      <a className="skip-link" href="#main-content">
        Vai al contenuto
      </a>

      <header className="home-nav">
        <div className="brand">
          <span className="brand-mark">MA</span>
          <strong>Multi-Agent Chatbot</strong>
        </div>
        <nav>
          <a href="#how-it-works">Come funziona</a>
          <a href="#domains">Domini</a>
          <a href="#quickstart">Avvio rapido</a>
          <a href="#technology">Stack</a>
          <a href="#architecture">Architettura</a>
          <button type="button" className="nav-cta" onClick={onStartChat}>
            Apri la chat
          </button>
        </nav>
      </header>

      <main id="main-content">
        <section className="hero" id="top">
          <div className="hero-grid">
            <div>
              <p className="hero-kicker">Progetto sperimentale</p>
              <h1>Un chatbot che instrada ogni domanda allo specialista giusto</h1>
              <p className="hero-lead">
                Router basato su embedding, quattro domini specializzati (crittografia post-quantum, eIDAS2,
                ingegneria del software e un fallback generico), recupero di conoscenza da Qdrant dove serve,
                e un giudice LLM che valuta ogni risposta prima che venga confermata.
              </p>
              <ul className="fact-chips">
                {factChips.map((fact) => (
                  <li key={fact}>{fact}</li>
                ))}
              </ul>
              <div className="hero-actions">
                <button type="button" onClick={onStartChat}>
                  Apri la chat
                </button>
                <button
                  type="button"
                  className="ghost"
                  onClick={() =>
                    architectureRef.current?.scrollIntoView({ behavior: "smooth", block: "start" })
                  }
                >
                  Vedi l&apos;architettura
                </button>
              </div>
            </div>

            <div className="hero-trace" aria-hidden="true">
              <div className="trace-bar">
                <span className="trace-dot" />
                <span className="trace-dot" />
                <span className="trace-dot" />
                <span className="trace-title">chat/stream — eventi SSE</span>
              </div>
              <pre className="trace-log">
                {`event: route
data: {"route":"crypto_pqc","confidence":0.81,"method":"embedding"}

event: specialist
data: {"preview":"ML-KEM sostituisce RSA per lo scambio di chiavi..."}

event: judge
data: {"faithfulness":5,"relevance":4,"overall":4.3,"passed":true}

event: done
data: {"trace":[...]}`}
              </pre>
            </div>
          </div>
        </section>

        <section className="panel" id="how-it-works">
          <h2>Come funziona</h2>
          <p className="panel-lead">
            Ogni richiesta attraversa un grafo di stati LangGraph, non una singola chiamata a un modello.
          </p>
          <ol className="pipeline">
            {pipelineSteps.map((item) => (
              <li key={item.step}>
                <span className="pipeline-step">{item.step}</span>
                <div>
                  <h3>
                    {item.title}
                    {item.event && <code className="event-tag">{item.event}</code>}
                  </h3>
                  <p>{item.text}</p>
                </div>
              </li>
            ))}
          </ol>
        </section>

        <section className="panel" id="domains">
          <h2>Domini disponibili</h2>
          <p className="panel-lead">
            Caricati dinamicamente dal backend ({agents.length} attivi in questo momento).
          </p>
          <ul className="domain-list">
            {agents.map((agent) => (
              <li key={agent.key}>
                <strong>{agent.label}</strong>
                <p>{agent.description}</p>
                <span className={`tag ${agent.use_rag ? "tag-on" : "tag-off"}`}>
                  {agent.use_rag ? "RAG attivo" : "Nessun RAG"}
                </span>
              </li>
            ))}
            {agents.length === 0 && <li className="empty">In attesa di risposta dal backend...</li>}
          </ul>
        </section>

        <section className="panel" id="quickstart">
          <h2>Avvio rapido</h2>
          <p className="panel-lead">
            Serve Ollama attivo sull&apos;host con <code>qwen2.5:7b-instruct</code> e <code>bge-m3</code>{" "}
            scaricati.
          </p>
          <div className="hero-trace">
            <div className="trace-bar">
              <span className="trace-dot" />
              <span className="trace-dot" />
              <span className="trace-dot" />
              <span className="trace-title">terminale</span>
            </div>
            <pre className="trace-log">
              {`$ git clone ${GITHUB_MAIN_URL}
$ cd Multi_Agent_Chatbot
$ cp backend/.env.example backend/.env
$ docker compose up --build

# app disponibile su http://localhost (solo il gateway
# espone una porta host, backend/frontend restano interni)`}
            </pre>
          </div>
        </section>

        <section className="panel" id="api">
          <h2>API</h2>
          <p className="panel-lead">
            Endpoint principali esposti dal backend, sotto <code>/api/v1</code>.
          </p>
          <div className="api-table-wrap">
            <table className="api-table">
              <thead>
                <tr>
                  <th>Metodo</th>
                  <th>Path</th>
                  <th>Descrizione</th>
                </tr>
              </thead>
              <tbody>
                {apiEndpoints.map((endpoint) => (
                  <tr key={endpoint.path}>
                    <td>
                      <span className="http-method">{endpoint.method}</span>
                    </td>
                    <td>
                      <code>{endpoint.path}</code>
                    </td>
                    <td>{endpoint.text}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="panel" id="technology">
          <h2>Stack tecnico</h2>
          <p className="panel-lead">I componenti realmente usati nel progetto, non un elenco generico.</p>
          <div className="tech-grid">
            {techCards.map((card) => (
              <article key={card.title} className="tech-card">
                <h3>{card.title}</h3>
                <p>{card.text}</p>
              </article>
            ))}
          </div>

          <div className="repo-links">
            <a href={GITHUB_MAIN_URL} target="_blank" rel="noreferrer">
              Repository principale
            </a>
            <a href={GITHUB_BACKEND_URL} target="_blank" rel="noreferrer">
              Backend (FastAPI + LangGraph)
            </a>
            <a href={GITHUB_FRONTEND_URL} target="_blank" rel="noreferrer">
              Frontend (React + Vite)
            </a>
          </div>
        </section>

        <section className="panel" id="status">
          <h2>Stato del progetto</h2>
          <p className="panel-lead">
            Onestamente: cosa funziona davvero oggi, e cosa esiste gia nel codice senza essere ancora attivo.
          </p>
          <div className="status-grid">
            <div className="status-col">
              <h3 className="status-heading good">Funzionante</h3>
              <ul>
                {statusColumns.working.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <div className="status-col">
              <h3 className="status-heading mid">Non ancora attivo</h3>
              <ul>
                {statusColumns.inactive.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          </div>
        </section>

        <section className="panel" id="architecture" ref={architectureRef}>
          <h2>Architettura</h2>
          <p className="panel-lead">
            Gateway Nginx davanti a frontend e backend, Postgres per la memoria conversazionale, Qdrant per il
            retrieval, Redis previsto per il caching.
          </p>
          <div className="diagram-frame">
            <img
              className="architecture-image"
              src="/architecture-overview.svg"
              alt="Frontend to Nginx gateway to FastAPI backend running a LangGraph pipeline (preprocess, router, specialist, judge, finalize, with a retry loop from judge back to specialist), connected to an Ollama/vLLM server, Qdrant, Postgres and Redis"
            />
          </div>
          <div className="panel-foot">
            <button type="button" onClick={onStartChat}>
              Apri la chat
            </button>
          </div>
        </section>
      </main>

      <footer className="home-footer">
        <span>Multi-Agent Chatbot — progetto sperimentale</span>
        <a href={GITHUB_MAIN_URL} target="_blank" rel="noreferrer">
          GitHub
        </a>
      </footer>
    </div>
  );
}
