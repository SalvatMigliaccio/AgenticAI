from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Legge da file .env, case-insensitive (LLM_BASE_URL == llm_base_url)
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    PROJECT_NAME: str = "Multi-Agent Chatbot"
    API_V1_STR: str = "/api/v1"
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # --- Endpoint LLM (OpenAI-compatible): in prod vLLM ---  ← vLLM
    # In vLLM il "model" che passiamo è il nome del base model OPPURE di un adapter LoRA.
    LLM_BASE_URL: str = "http://localhost:11434/v1"
    LLM_API_KEY: str = "ollama"
    LLM_BASE_MODEL: str = "qwen2.5:7b-instruct"      # usato dal generalista e dal giudice
    USE_ADAPTERS: bool = False                       # se True → usa adapter LoRA per specialisti

    # --- Embeddings (server OpenAI-compatible dedicato, es. vLLM/TEI con bge-m3) ---  ← vLLM
    EMBED_BASE_URL: str = "http://vllm-embed:8000/v1"
    EMBED_API_KEY: str = "not-needed"
    EMBED_MODEL: str = "BAAI/bge-m3"          # multilingue, ottimo per l'italiano
    EMBED_DIM: int = 1024                     # dimensione vettori bge-m3

    # --- Infra ---
    QDRANT_URL: str = "http://localhost:6333"
    REDIS_URL: str = "redis://localhost:6379/0"
    POSTGRES_DSN: str = "postgresql://chat:chat_pw@localhost:5432/chatdb"

    # --- Comportamento del grafo ---
    ROUTER_CONFIDENCE_THRESHOLD: float = 0.55  # sotto questa soglia → fallback LLM classifier
    JUDGE_PASS_THRESHOLD: float = 3.5          # overall medio per "pass" (rubrica 1-5)
    MAX_REFLECTION_RETRIES: int = 1            # quante volte lo specialista può rigenerare

    # --- Generazione ---
    SPECIALIST_TEMPERATURE: float = 0.3        # specialisti: precisi, poco creativi
    JUDGE_TEMPERATURE: float = 0.0             # giudice: deterministico
    MAX_TOKENS: int = 1024
    
    #--- RAG ---
    RAG_TOP_K: int = 4 # passaggi da recuperare per la RAG (se il dominio la usa)
    RAG_FETCH_K: int = 20 #candidati presi da ogni retriever prima della filtratura (per evitare di perdere passaggi rilevanti)
    RERANK_ENABLED: bool = False #se True, usa il modello LLM per riordinare i passaggi recuperati dalla RAG (più costoso ma più preciso)
    RERANK_MODEL: str = "BAAI/bge-reranker-v2-m3"


# Singleton importato ovunque: `from app.core.config import settings`
settings = Settings()