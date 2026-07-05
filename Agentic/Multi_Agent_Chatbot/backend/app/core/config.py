from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Legge da file .env, case-insensitive (LLM_BASE_URL == llm_base_url)
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    PROJECT_NAME: str = "Multi-Agent Chatbot"
    API_V1_STR: str = "/api/v1"
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # --- Endpoint LLM (OpenAI-compatible): in prod vLLM ---  ← vLLM
    # In vLLM il "model" che passiamo è il nome del base model OPPURE di un adapter LoRA.
    LLM_BASE_URL: str = "http://vllm:8000/v1"
    LLM_API_KEY: str = "not-needed"           # vLLM non controlla la key
    LLM_BASE_MODEL: str = "Qwen/Qwen2.5-7B-Instruct"  # usato dal generalista e dal giudice

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


# Singleton importato ovunque: `from app.core.config import settings`
settings = Settings()