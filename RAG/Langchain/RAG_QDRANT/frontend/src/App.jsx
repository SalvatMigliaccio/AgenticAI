import { useState, useRef, useEffect } from "react";

const API = "http://localhost:8000";

/* ── Google Font (Inter) injected once ─────────────────────────────────── */
const fontLink = document.createElement("link");
fontLink.rel = "stylesheet";
fontLink.href = "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap";
document.head.appendChild(fontLink);

/* ── Global CSS (animations, scrollbar) ────────────────────────────────── */
const style = document.createElement("style");
style.textContent = `
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Inter', sans-serif; }

  ::-webkit-scrollbar { width: 5px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 10px; }

  @keyframes fadeSlideUp {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; } 50% { opacity: .4; }
  }
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
  .msg-enter { animation: fadeSlideUp .25s ease both; }
  .dot-pulse span {
    display: inline-block; width: 7px; height: 7px; border-radius: 50%;
    background: #7c3aed; margin: 0 2px;
    animation: pulse 1.2s ease-in-out infinite;
  }
  .dot-pulse span:nth-child(2) { animation-delay: .2s; }
  .dot-pulse span:nth-child(3) { animation-delay: .4s; }

  .upload-zone {
    border: 2px dashed rgba(255,255,255,0.2);
    border-radius: 14px;
    padding: 22px 16px;
    cursor: pointer;
    text-align: center;
    transition: all .25s;
    background: rgba(255,255,255,0.04);
  }
  .upload-zone:hover, .upload-zone.drag { 
    border-color: #a78bfa; 
    background: rgba(167,139,250,0.1);
  }

  .doc-chip {
    display: flex; align-items: center; gap: 8px;
    font-size: 12px; color: rgba(255,255,255,0.75);
    padding: 7px 10px; border-radius: 10px;
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.1);
    transition: background .2s;
    overflow: hidden;
  }
  .doc-chip:hover { background: rgba(255,255,255,0.13); }
  .doc-chip span { 
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap; 
    flex: 1; min-width: 0;
  }

  .send-btn {
    width: 40px; height: 40px; border-radius: 50%; border: none;
    background: linear-gradient(135deg, #7c3aed, #6366f1);
    color: white; cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    transition: all .2s; flex-shrink: 0;
    box-shadow: 0 4px 14px rgba(124,58,237,0.4);
  }
  .send-btn:hover:not(:disabled) { transform: scale(1.08); box-shadow: 0 6px 20px rgba(124,58,237,0.55); }
  .send-btn:disabled { background: #e5e7eb; box-shadow: none; cursor: not-allowed; }

  .source-badge {
    display: inline-flex; align-items: center; gap: 5px;
    font-size: 11px; padding: 3px 9px; border-radius: 20px;
    background: linear-gradient(135deg, #ede9fe, #ddd6fe);
    color: #5b21b6; border: 1px solid #c4b5fd;
    margin-right: 5px; margin-top: 5px;
    font-weight: 500; letter-spacing: 0.01em;
    transition: transform .15s;
  }
  .source-badge:hover { transform: translateY(-1px); }

  .chat-input {
    flex: 1; border: none; background: transparent;
    font-size: 14px; color: #1e1e2e; outline: none;
    font-family: 'Inter', sans-serif;
    resize: none; line-height: 1.5;
  }
  .chat-input::placeholder { color: #9ca3af; }
`;
document.head.appendChild(style);

/* ── SVG Icons ──────────────────────────────────────────────────────────── */
const SendIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.2}
    strokeLinecap="round" strokeLinejoin="round" width={17} height={17}>
    <line x1="22" y1="2" x2="11" y2="13"/>
    <polygon points="22 2 15 22 11 13 2 9 22 2"/>
  </svg>
);

const UploadIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}
    strokeLinecap="round" strokeLinejoin="round" width={28} height={28}>
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
    <polyline points="17 8 12 3 7 8"/>
    <line x1="12" y1="3" x2="12" y2="15"/>
  </svg>
);

const FileIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}
    strokeLinecap="round" strokeLinejoin="round" width={13} height={13} style={{flexShrink:0}}>
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
    <polyline points="14 2 14 8 20 8"/>
  </svg>
);

const BookIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}
    strokeLinecap="round" strokeLinejoin="round" width={11} height={11}>
    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
    <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
  </svg>
);

const SparkleIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" width={16} height={16}>
    <path d="M12 2l2.4 7.2H22l-6.2 4.5 2.4 7.2L12 16.4l-6.2 4.5 2.4-7.2L2 9.2h7.6z"/>
  </svg>
);

/* ── Source Badge ───────────────────────────────────────────────────────── */
function SourceBadge({ source }) {
  return (
    <span className="source-badge">
      <BookIcon />
      {source.file} p.{source.page}
    </span>
  );
}

/* ── Message ────────────────────────────────────────────────────────────── */
function Message({ msg }) {
  const isUser = msg.role === "user";
  return (
    <div className="msg-enter" style={{
      display: "flex",
      justifyContent: isUser ? "flex-end" : "flex-start",
      marginBottom: 20, gap: 12, alignItems: "flex-start",
    }}>
      {!isUser && (
        <div style={{
          width: 36, height: 36, borderRadius: "50%", flexShrink: 0,
          background: "linear-gradient(135deg, #7c3aed, #6366f1)",
          display: "flex", alignItems: "center", justifyContent: "center",
          color: "white", boxShadow: "0 4px 12px rgba(124,58,237,0.35)",
        }}>
          <SparkleIcon />
        </div>
      )}
      <div style={{ maxWidth: "72%" }}>
        <div style={{
          padding: "12px 16px",
          borderRadius: isUser ? "20px 20px 6px 20px" : "6px 20px 20px 20px",
          background: isUser
            ? "linear-gradient(135deg, #7c3aed, #6366f1)"
            : "white",
          color: isUser ? "white" : "#1e1e2e",
          fontSize: 14, lineHeight: 1.65,
          boxShadow: isUser
            ? "0 4px 16px rgba(124,58,237,0.3)"
            : "0 2px 12px rgba(0,0,0,0.07)",
          border: isUser ? "none" : "1px solid #f0f0f5",
          whiteSpace: "pre-wrap",
        }}>
          {msg.content}
        </div>
        {msg.sources?.length > 0 && (
          <div style={{ marginTop: 7, paddingLeft: 4 }}>
            {msg.sources.map((s, i) => <SourceBadge key={i} source={s} />)}
          </div>
        )}
      </div>
      {isUser && (
        <div style={{
          width: 36, height: 36, borderRadius: "50%", flexShrink: 0,
          background: "linear-gradient(135deg, #e0e7ff, #c7d2fe)",
          display: "flex", alignItems: "center", justifyContent: "center",
          color: "#6366f1", fontSize: 13, fontWeight: 700,
          boxShadow: "0 2px 8px rgba(99,102,241,0.2)",
        }}>U</div>
      )}
    </div>
  );
}

/* ── Typing indicator ───────────────────────────────────────────────────── */
function TypingIndicator() {
  return (
    <div className="msg-enter" style={{
      display: "flex", gap: 12, alignItems: "flex-start", marginBottom: 20,
    }}>
      <div style={{
        width: 36, height: 36, borderRadius: "50%", flexShrink: 0,
        background: "linear-gradient(135deg, #7c3aed, #6366f1)",
        display: "flex", alignItems: "center", justifyContent: "center",
        color: "white", boxShadow: "0 4px 12px rgba(124,58,237,0.35)",
      }}>
        <SparkleIcon />
      </div>
      <div style={{
        padding: "14px 18px",
        borderRadius: "6px 20px 20px 20px",
        background: "white",
        boxShadow: "0 2px 12px rgba(0,0,0,0.07)",
        border: "1px solid #f0f0f5",
      }}>
        <div className="dot-pulse">
          <span/><span/><span/>
        </div>
      </div>
    </div>
  );
}

/* ── Upload Zone ────────────────────────────────────────────────────────── */
function UploadZone({ onUpload }) {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const inputRef = useRef();

  const handleFiles = async (files) => {
    const pdfs = [...files].filter(f => f.name.endsWith(".pdf"));
    if (!pdfs.length) return;
    setUploading(true);
    setResult(null);
    const form = new FormData();
    pdfs.forEach(f => form.append("files", f));
    try {
      const res = await fetch(`${API}/upload`, { method: "POST", body: form });
      const data = await res.json();
      setResult({ ok: res.ok, data });
      if (res.ok) onUpload(data);
    } catch {
      setResult({ ok: false, data: { detail: "Errore di connessione." } });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div
      className={`upload-zone${dragging ? " drag" : ""}`}
      onDragOver={e => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={e => { e.preventDefault(); setDragging(false); handleFiles(e.dataTransfer.files); }}
      onClick={() => inputRef.current.click()}
    >
      <input ref={inputRef} type="file" accept=".pdf" multiple hidden
        onChange={e => handleFiles(e.target.files)} />
      <div style={{ color: uploading ? "#a78bfa" : "rgba(255,255,255,0.5)", marginBottom: 10 }}>
        {uploading
          ? <div style={{ width: 28, height: 28, border: "3px solid #a78bfa", borderTopColor: "transparent", borderRadius: "50%", animation: "spin 0.8s linear infinite", margin: "0 auto" }} />
          : <UploadIcon />
        }
      </div>
      <p style={{ fontSize: 13, color: "rgba(255,255,255,0.6)", lineHeight: 1.4 }}>
        {uploading ? "Indicizzazione in corso…" : "Trascina PDF qui"}
      </p>
      {!uploading && (
        <p style={{ fontSize: 11, color: "rgba(255,255,255,0.35)", marginTop: 4 }}>
          o clicca per scegliere
        </p>
      )}
      {result && (
        <p style={{
          marginTop: 10, fontSize: 12, fontWeight: 500,
          color: result.ok ? "#86efac" : "#fca5a5",
        }}>
          {result.ok
            ? `✓ ${result.data.files?.length ?? 1} file — ${result.data.chunks} chunk`
            : `✗ ${result.data.detail}`}
        </p>
      )}
    </div>
  );
}

/* ── App ────────────────────────────────────────────────────────────────── */
export default function App() {
  const [messages, setMessages] = useState([{
    role: "assistant",
    content: "Ciao! 👋 Carica uno o più PDF dal pannello a sinistra e fai le tue domande. Posso analizzare e confrontare più documenti contemporaneamente.",
    sources: [],
  }]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [docs, setDocs] = useState([]);
  const bottomRef = useRef();
  const inputRef = useRef();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    fetch(`${API}/tracked-documents`)
      .then(r => r.ok ? r.json() : null)
      .then(d => d && setDocs(d.tracked_documents || []))
      .catch(() => {});
  }, []);

  const handleUpload = (data) => {
    setDocs(data.tracked_documents || []);
  };

  const sendMessage = async () => {
    const q = input.trim();
    if (!q || loading) return;
    setMessages(prev => [...prev, { role: "user", content: q }]);
    setInput("");
    setLoading(true);
    try {
      const res = await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q }),
      });
      const data = await res.json();
      setMessages(prev => [...prev, {
        role: "assistant",
        content: res.ok ? data.answer : `Errore: ${data.detail}`,
        sources: res.ok ? data.sources : [],
      }]);
    } catch {
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "Errore di connessione con il backend.",
        sources: [],
      }]);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  };

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  };

  return (
    <div style={{
      display: "flex", height: "100vh",
      fontFamily: "'Inter', sans-serif",
      background: "#f5f5f8",
    }}>

      {/* ═══ SIDEBAR ════════════════════════════════════════════════════ */}
      <div style={{
        width: 290, flexShrink: 0,
        background: "linear-gradient(160deg, #1e1b4b 0%, #312e81 40%, #4c1d95 100%)",
        display: "flex", flexDirection: "column",
        padding: "28px 20px 24px",
        boxShadow: "4px 0 24px rgba(0,0,0,0.15)",
      }}>

        {/* Logo */}
        <div style={{ marginBottom: 28 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
            <div style={{
              width: 38, height: 38, borderRadius: 12,
              background: "linear-gradient(135deg, #a78bfa, #818cf8)",
              display: "flex", alignItems: "center", justifyContent: "center",
              boxShadow: "0 4px 12px rgba(167,139,250,0.4)",
            }}>
              <SparkleIcon />
            </div>
            <div>
              <div style={{ fontSize: 15, fontWeight: 700, color: "white", lineHeight: 1.2 }}>
                PDF RAG Agent
              </div>
              <div style={{ fontSize: 11, color: "rgba(255,255,255,0.45)", marginTop: 1 }}>
                LangChain · Qdrant · Mistral
              </div>
            </div>
          </div>
        </div>

        {/* Upload */}
        <div style={{ marginBottom: 20 }}>
          <div style={{
            fontSize: 10, fontWeight: 600, letterSpacing: "0.08em",
            textTransform: "uppercase", color: "rgba(255,255,255,0.4)",
            marginBottom: 10,
          }}>Carica documenti</div>
          <UploadZone onUpload={handleUpload} />
        </div>

        {/* Doc list */}
        <div style={{ flex: 1, overflowY: "auto", minHeight: 0 }}>
          {docs.length > 0 ? (
            <>
              <div style={{
                fontSize: 10, fontWeight: 600, letterSpacing: "0.08em",
                textTransform: "uppercase", color: "rgba(255,255,255,0.4)",
                marginBottom: 10,
                display: "flex", alignItems: "center", justifyContent: "space-between",
              }}>
                <span>Documenti</span>
                <span style={{
                  background: "rgba(167,139,250,0.25)", color: "#c4b5fd",
                  borderRadius: 20, padding: "1px 8px", fontSize: 10,
                }}>{docs.length}</span>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
                {docs.map((d, i) => (
                  <div key={i} className="doc-chip">
                    <FileIcon />
                    <span title={d}>{d}</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div style={{
              textAlign: "center", padding: "20px 10px",
              color: "rgba(255,255,255,0.25)", fontSize: 12,
            }}>
              Nessun documento caricato
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={{
          marginTop: 20, paddingTop: 16,
          borderTop: "1px solid rgba(255,255,255,0.08)",
          fontSize: 11, color: "rgba(255,255,255,0.25)", textAlign: "center",
        }}>
          {docs.length > 0
            ? `${docs.length} document${docs.length > 1 ? "i" : "o"} in memoria`
            : "Pronto · nessun documento"
          }
        </div>
      </div>

      {/* ═══ MAIN CHAT ══════════════════════════════════════════════════ */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>

        {/* Top bar */}
        <div style={{
          padding: "0 32px",
          height: 64, flexShrink: 0,
          display: "flex", alignItems: "center", justifyContent: "space-between",
          background: "white",
          borderBottom: "1px solid #ebebf0",
          boxShadow: "0 1px 6px rgba(0,0,0,0.04)",
        }}>
          <div>
            <div style={{ fontSize: 15, fontWeight: 600, color: "#1e1e2e" }}>
              Chat con i tuoi PDF
            </div>
            <div style={{ fontSize: 12, color: "#9ca3af", marginTop: 1 }}>
              {docs.length > 0
                ? `${docs.length} document${docs.length > 1 ? "i" : "o"} disponibil${docs.length > 1 ? "i" : "e"}`
                : "Nessun documento caricato"}
            </div>
          </div>
          <div style={{
            display: "flex", alignItems: "center", gap: 6,
            background: "#f0fdf4", border: "1px solid #bbf7d0",
            borderRadius: 20, padding: "4px 12px",
            fontSize: 12, color: "#166534", fontWeight: 500,
          }}>
            <div style={{
              width: 7, height: 7, borderRadius: "50%",
              background: "#22c55e",
              boxShadow: "0 0 6px #22c55e",
            }} />
            Online
          </div>
        </div>

        {/* Messages */}
        <div style={{
          flex: 1, overflowY: "auto", padding: "28px 40px",
          background: "#f5f5f8",
        }}>
          {messages.map((m, i) => <Message key={i} msg={m} />)}
          {loading && <TypingIndicator />}
          <div ref={bottomRef} />
        </div>

        {/* Input bar */}
        <div style={{
          padding: "16px 32px 20px",
          background: "white",
          borderTop: "1px solid #ebebf0",
        }}>
          <div style={{
            display: "flex", gap: 12, alignItems: "flex-end",
            background: "#f7f7fb",
            borderRadius: 20,
            border: "1.5px solid #ebebf0",
            padding: "10px 12px 10px 20px",
            transition: "border-color .2s, box-shadow .2s",
            boxShadow: "0 1px 4px rgba(0,0,0,0.04)",
          }}
            onFocus={() => {}}
          >
            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Scrivi una domanda sui tuoi documenti…"
              rows={1}
              className="chat-input"
              style={{ maxHeight: 120, overflowY: "auto" }}
            />
            <button
              className="send-btn"
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              style={loading || !input.trim() ? { background: "#e5e7eb", boxShadow: "none", cursor: "not-allowed" } : {}}
            >
              <SendIcon />
            </button>
          </div>
          <p style={{
            margin: "8px 0 0", fontSize: 11,
            color: "#c9c9d4", textAlign: "center", letterSpacing: "0.02em",
          }}>
            Invio con <kbd style={{
              background: "#f3f4f6", border: "1px solid #e5e7eb",
              borderRadius: 4, padding: "1px 5px", fontSize: 10, color: "#6b7280",
            }}>Enter</kbd>
            &nbsp;·&nbsp;A capo con <kbd style={{
              background: "#f3f4f6", border: "1px solid #e5e7eb",
              borderRadius: 4, padding: "1px 5px", fontSize: 10, color: "#6b7280",
            }}>Shift+Enter</kbd>
          </p>
        </div>
      </div>
    </div>
  );
}

