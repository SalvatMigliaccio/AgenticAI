export const routeColorMap = {
  crypto_pqc: "#1a7f4f",
  eidas_compliance: "#b6720a",
  software_eng: "#2563a8",
  general: "#6b5fb0",
};

export const pipelineSteps = [
  {
    step: "01",
    title: "Preprocess",
    text: "Normalizza l'input, rileva la lingua, azzera il contatore dei retry.",
  },
  {
    step: "02",
    title: "Router",
    text: "Similarita coseno su embedding di dominio; fallback a classificazione LLM, poi a keyword matching.",
  },
  {
    step: "03",
    title: "Specialist",
    text: "Il modello del dominio risponde, con contesto RAG da Qdrant quando il dominio lo prevede.",
  },
  {
    step: "04",
    title: "Judge",
    text: "Un LLM valuta faithfulness, relevance, completeness e safety della risposta gia mostrata.",
  },
  {
    step: "05",
    title: "Finalize",
    text: "La risposta viene confermata e salvata nella memoria conversazionale su Postgres.",
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
