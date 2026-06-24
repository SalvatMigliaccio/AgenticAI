import os 
import re
import shutil
import tempfile
from datetime import datetime, timezone
from typing import List

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from ingest import ingest_files
from agent import build_agent

load_dotenv()

app = FastAPI(title="LangChain-Qdrant RAG API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_agent = None  # global variable to hold the agent instance
_uploaded_docs = set()  # tracks uploaded PDF filenames; persisted in Qdrant
_last_agent_sources: frozenset = frozenset()  # tracks which sources the cached agent was built with
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
TRACKING_COLLECTION = os.getenv("QDRANT_TRACKING_COLLECTION", "rag_tracking_state")
TRACKING_POINT_ID = 1


def _get_qdrant_client() -> QdrantClient:
    return QdrantClient(QDRANT_URL)


def _ensure_tracking_collection(client: QdrantClient):
    collections = [c.name for c in client.get_collections().collections]
    if TRACKING_COLLECTION not in collections:
        client.create_collection(
            collection_name=TRACKING_COLLECTION,
            vectors_config=VectorParams(size=1, distance=Distance.COSINE),
        )


def _load_uploaded_docs_from_qdrant() -> set:
    try:
        client = _get_qdrant_client()
        _ensure_tracking_collection(client)
        records = client.retrieve(
            collection_name=TRACKING_COLLECTION,
            ids=[TRACKING_POINT_ID],
            with_payload=True,
        )
        if not records:
            return set()
        payload = records[0].payload or {}
        docs = payload.get("uploaded_docs", [])
        return {str(d) for d in docs if str(d).strip()}
    except Exception:
        # Keep app usable even if Qdrant is temporarily unavailable.
        return set()


def _persist_uploaded_docs_to_qdrant(docs: set):
    try:
        client = _get_qdrant_client()
        _ensure_tracking_collection(client)
        client.upsert(
            collection_name=TRACKING_COLLECTION,
            points=[
                PointStruct(
                    id=TRACKING_POINT_ID,
                    vector=[1.0],
                    payload={
                        "uploaded_docs": sorted(docs),
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    },
                )
            ],
        )
    except Exception:
        # Don't block uploads if persistence temporarily fails.
        pass


def _hydrate_uploaded_docs_from_qdrant():
    global _uploaded_docs
    # Always reload from Qdrant to pick up changes persisted by other requests
    _uploaded_docs = _load_uploaded_docs_from_qdrant()

def get_agent():
    global _agent, _last_agent_sources
    _hydrate_uploaded_docs_from_qdrant()
    current_sources = frozenset(_uploaded_docs)
    # Rebuild agent if document list changed or no agent exists yet
    if _agent is None or current_sources != _last_agent_sources:
        _agent = build_agent(allowed_sources=_uploaded_docs)
        _last_agent_sources = current_sources
    return _agent

# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health_check():
    return {"status":"ok"}


@app.get("/tracked-documents")
async def get_tracked_documents():
    """Returns the list of currently tracked uploaded documents."""
    _hydrate_uploaded_docs_from_qdrant()
    return {"tracked_documents": sorted(_uploaded_docs)}


@app.on_event("startup")
async def startup_event():
    _hydrate_uploaded_docs_from_qdrant()

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """
    Accepts one or more PDF files as multipart/form-data.
    every file is a PDF, save them to a temporary directory, call ingest files to chunk
    and index them into Qdrant, then delete the temporary files.
    4. Invalidate the cached agent so the next /chat call rebuilds it
   with a retriever that sees the new documents.
   5. Clean up the temp directory in the finally block so we never
      leave uploaded files on disk after processing.
    """
    global _agent, _uploaded_docs

    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
    
    for f in files:
        if not f.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail=f"Invalid file type: {f.filename}. Only PDFs are allowed.")
    
    temp_dir = tempfile.mkdtemp()
    try:
        saved = []
        for f in files:
            dest = os.path.join(temp_dir, f.filename)
            with open(dest, "wb") as out:
                shutil.copyfileobj(f.file, out)
                saved.append(dest)
            
        count = ingest_files(saved)

        # Reset the agent cache — next request to /chat will call
        # build_agent() again, which opens a fresh connection to Qdrant
        # and therefore sees the chunks we just inserted.
        _uploaded_docs.update([f.filename for f in files])
        _persist_uploaded_docs_to_qdrant(_uploaded_docs)
        _agent = None
        
        return {
            "status": "success",
            "files": [f.filename for f in files],
            "tracked_documents": sorted(_uploaded_docs),
            "chunks": count,
            "chunks_indexed": count,
        }
    finally:
        shutil.rmtree(temp_dir)
        
#----------------------------------------------------------------------------
# Data Models
#----------------------------------------------------------------------------
        
class ChatRequest(BaseModel):
    question: str

class Source(BaseModel):
    file: str
    page: int

class ChatResponse(BaseModel):
    answer: str
    sources: List[Source]
    
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Passes the user question to the ReAct agent and returns the answer
    together with the source citations extracted from intermediate steps.

    How citations are extracted:
        The retriever tool returns chunks as plain text with metadata
        prepended in the format "Source: file.pdf\\nPage: 2\\n\\n<chunk>".
        We scan the intermediate_steps produced by AgentExecutor
        (each step is a tuple of (AgentAction, tool_output_string))
        and extract all Source/Page pairs with a regex.
        Duplicates are filtered with a set so the same page is not
        listed twice if multiple chunks came from it.
    """
    if not req.question.strip():
        raise HTTPException(400, "Question cannot be empty.")

    # Ensure document list is synced from Qdrant before querying
    _hydrate_uploaded_docs_from_qdrant()
    agent = get_agent()

    try:
        result = agent.invoke({"input": req.question})
    except Exception as e:
        raise HTTPException(500, f"Agent error: {e}")

    answer = result["output"]
    sources = []
    seen = set()

    for step in result.get("intermediate_steps", []):
        # step[0] is the AgentAction (tool name + input)
        # step[1] is the raw string output returned by the tool
        tool_output = step[1] if len(step) > 1 else ""
        for match in re.finditer(
            r"[Ss]ource:\s*(.+?)\n[Pp]age:\s*(\d+)", tool_output
        ):
            key = (match.group(1).strip(), int(match.group(2)))
            if key not in seen:
                seen.add(key)
                # Page numbers from PyPDFLoader are 0-based; add 1 for display.
                sources.append(Source(file=key[0], page=key[1] + 1))

    return ChatResponse(answer=answer, sources=sources)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)

    