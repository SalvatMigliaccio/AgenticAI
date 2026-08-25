export const routeColorMap = {
  crypto_pqc: "#3fb950",
  eidas_compliance: "#d29922",
  software_eng: "#58a6ff",
  general: "#bc8cff",
};

export const factChips = [
  "grafo LangGraph a 5 nodi",
  "4 domini specializzati",
  "RAG ibrido dense+BM25",
  "streaming SSE",
];

export const pipelineSteps = [
  {
    step: "01",
    title: "Preprocess",
    text: "Normalizza l'input, rileva la lingua, azzera il contatore dei retry.",
    event: null,
  },
  {
    step: "02",
    title: "Router",
    text: "Similarita coseno su embedding di dominio; fallback a classificazione LLM, poi a keyword matching.",
    event: "route",
  },
  {
    step: "03",
    title: "Specialist",
    text: "Il modello del dominio risponde, con contesto RAG da Qdrant quando il dominio lo prevede.",
    event: "specialist",
  },
  {
    step: "04",
    title: "Judge",
    text: "Un LLM valuta faithfulness, relevance, completeness e safety della risposta gia mostrata.",
    event: "judge_status, judge",
  },
  {
    step: "05",
    title: "Finalize",
    text: "La risposta viene confermata e salvata nella memoria conversazionale su Postgres.",
    event: "answer, done",
  },
];

export const techCards = [
  { title: "LangGraph", text: "Grafo a stati: preprocess, router, specialist, judge, finalize." },
  { title: "Hybrid RAG", text: "Retrieval dense + BM25 su Qdrant con fusione RRF." },
  { title: "FastAPI + SSE", text: "Streaming eventi tipizzati (route, judge, answer) verso il client." },
  { title: "Nginx Gateway", text: "Reverse proxy con rate limiting e supporto streaming SSE." },
  {
    title: "Postgres Checkpointer",
    text: "Stato conversazionale persistito, non tenuto in memoria di processo.",
  },
  { title: "Ollama / vLLM", text: "Backend LLM OpenAI-compatible, in locale in sviluppo." },
];

export const apiEndpoints = [
  { method: "POST", path: "/api/v1/chat/stream", text: "Turno di chat in streaming (SSE)" },
  { method: "POST", path: "/api/v1/chat", text: "Turno di chat sincrono, senza streaming" },
  { method: "GET", path: "/api/v1/agents", text: "Elenco domini disponibili (usato da questa pagina)" },
  { method: "POST", path: "/api/v1/eval/run", text: "Esegue l'eval harness sul grafo live" },
];

export const statusColumns = {
  working: [
    "Routing per similarita embedding con fallback LLM e keyword",
    "RAG ibrido dense+BM25 sulla collection kb_crypto",
    "Streaming SSE di routing, risposta e giudizio",
    "Persistenza conversazioni su Postgres (layer API stateless)",
    "Giudice con fallback sicuro se la valutazione fallisce",
  ],
  inactive: [
    "Adapter LoRA per dominio (pipeline pronta, non ancora addestrata)",
    "Reflection loop (retry disattivato di default)",
    "Collection kb_eidas (mai ingerita, RAG vuoto per eIDAS)",
    "Redis (provisioned ma non richiamato dal codice)",
  ],
};
