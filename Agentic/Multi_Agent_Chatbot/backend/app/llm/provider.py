from openai import AsyncOpenAI
from app.core.config import settings
from collections.abc import AsyncGenerator

# Un solo client async riusabile (gestisce connection pooling internamente).
# Punta al nostro endpoint OpenAI-compatible: con vLLM è http://vllm:8000/v1
_client = AsyncOpenAI(base_url=settings.LLM_BASE_URL, api_key=settings.LLM_API_KEY)

async def chat(
    messages: list[dict[str, str]], 
    *,
    model: str,
    temperature: float = 0.3,
    max_tokens: int = settings.MAX_TOKENS,
    json_mode: bool = False,
) -> str:
    """
    Chiamata di chat completition. Ritorna il solo testo della risposta (senza metadata).
    `messages` è nel formato OpenAI: [{"role": "system"|"user"|"assistant", "content": "..."}].
    `model` seleziona QUALE cervello risponde: con vLLM è il nome dell'adapter LoRA
    (es. "crypto-pqc-lora") o il base model. Questa è la leva del multi-agent.
    """
    extra: dict = {}
    if json_mode:
        # Forza JSON valido. vLLM supporta response_format; il nodo judge avrà
        # comunque un parsing difensivo come rete di sicurezza.
        extra["response_format"] = {"type": "json_schema"}
        
    resp = await _client.chat.completions.create(
        model=model,
        messages=messages,            # type: ignore[arg-type]
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=settings.LLM_REQUEST_TIMEOUT_SEC,
        **extra,
    )
    return resp.choices[0].message.content or ""

async def chat_stream(
    messages: list[dict[str, str]], *, model: str,
    temperature: float = 0.3, max_tokens: int = settings.MAX_TOKENS,
) -> AsyncGenerator[str, None]:
    """Come chat(), ma yielda i token man mano (per uno streaming futuro più fine)."""
    stream = await _client.chat.completions.create(
        model=model, messages=messages,   # type: ignore[arg-type]
        temperature=temperature, max_tokens=max_tokens, stream=True,
        timeout=settings.LLM_REQUEST_TIMEOUT_SEC,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
    