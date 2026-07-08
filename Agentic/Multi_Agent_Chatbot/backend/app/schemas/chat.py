from pydantic import BaseModel


class ChatRequest(BaseModel):
    query: str
    thread_id: str = "default"   # identifica la conversazione (memoria)


class ChatResponse(BaseModel):
    answer: str
    route: str
    route_confidence: float
    judge: dict
    trace: list[dict]