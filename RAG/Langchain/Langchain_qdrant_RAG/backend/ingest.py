import os
import sys
import requests
import uuid
from dotenv import load_dotenv

from langchain.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.base import Embeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Custom Ollama embeddings using HTTP calls
class OllamaEmbeddings(Embeddings):
    def __init__(self, model: str = "nomic-embed-text", base_url: str = "http://ollama:11434"):
        self.model = model
        self.base_url = base_url
    
    def _embed_one(self, text: str):
        # Newer Ollama versions expose /api/embed; keep fallback to /api/embeddings.
        resp = requests.post(
            f"{self.base_url}/api/embed",
            json={"model": self.model, "input": text},
            timeout=30,
        )
        if resp.status_code == 404:
            resp = requests.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text},
                timeout=30,
            )
        resp.raise_for_status()
        data = resp.json()
        if "embedding" in data:
            return data["embedding"]
        if "embeddings" in data and data["embeddings"]:
            return data["embeddings"][0]
        raise ValueError("Unexpected Ollama embedding response format")

    def embed_documents(self, texts):
        return [self._embed_one(text) for text in texts]

    def embed_query(self, text):
        return self._embed_one(text)

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration — read from .env so we never hardcode URLs in the code.
# Inside Docker, these point to service names (e.g. "http://qdrant:6333")
# rather than localhost, because containers talk to each other by service name.
# ---------------------------------------------------------------------------
QDRANT_URL  = os.getenv("QDRANT_URL", "http://localhost:6333")
OLLAMA_URL  = os.getenv("OLLAMA_URL", "http://localhost:11434")
COLLECTION  = os.getenv("QDRANT_COLLECTION", "pdf_docs")
EMBED_MODEL = "nomic-embed-text"   # lightweight model dedicated to embeddings
EMBED_DIM   = 768                  # output vector size of nomic-embed-text
# ---------------------------------------------------------------------------
# This is a text splitter configuration that will be used to break up large documents into smaller chunks.
SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", " ", "."]
    )

def _get_embeddings() -> OllamaEmbeddings:
    """
    Return an embedding model instance backed by ollama running locally. The objective of this
    embedding model is to convert a text chunk into a vector number that can be stored in qdrant and later used for similarity search.
    """
    return OllamaEmbeddings(model=EMBED_MODEL, base_url=OLLAMA_URL)

def _ensure_collection(client: QdrantClient):
    """
    Creates the Qdrant collection if it doesn't exist yet. A collection is like a DB, 
    it holds all the vectors+ playload (chunk text + metadata).
    Distance.COSINE: measures similarity as the angle between two vectors.
    Standard choice for text embeddings — works better than euclidean
    distance because it ignores vector magnitude and focuses on direction.
    """
    exsists = [c.name for c in client.get_collections().collections]
    if COLLECTION not in exsists:
        client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE)
        )
    
def ingest_files(file_paths: list[str]) -> int:
    """
    Indexes a list of PDF file paths into Qdrant.
    called by the FastAPI /upload endpoint, which receives the files from the frontend.
     Each chunk is stored with metadata added automatically by PyPDFLoader:
        - source : original file path
        - page   : 0-based page number within the PDF
    These metadata fields are what power the source citations in /chat.

    Returns the total number of chunks indexed.
    """
    documents = []
    for path in file_paths:
        loader = PyPDFLoader(path) #extract text page by page, and add metadata (source, page number)
        documents.extend(loader.load())
    
    chunks = SPLITTER.split_documents(documents) #split text into smaller chunks, and add metadata (chunk number)
    
    client = QdrantClient(QDRANT_URL)
    _ensure_collection(client) #create collection if it doesn't exist
    
    embeddings = _get_embeddings()
    
    # Embed chunks and insert into Qdrant
    points = []
    for chunk in chunks:
        embedding = embeddings.embed_query(chunk.page_content)
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                "content": chunk.page_content,
                "source": os.path.basename(chunk.metadata.get("source", "unknown")),
                "page": chunk.metadata.get("page", 0),
            }
        )
        points.append(point)
    
    if points:
        client.upsert(collection_name=COLLECTION, points=points)
    
    return len(chunks)
    
def ingest_directory(dir_path: str) -> int:
    """
    Indexes all PDF files in a directory into Qdrant. This is a convenience function that calls ingest_files() on all PDFs in the directory.
     Useful for bulk indexing of many files at once.
     before starting the server, we can mount a local directory of PDFs into the container and call this function to index them all in one go.
     with the command python ingest.py ./my_documents
    """
    loader = DirectoryLoader(dir_path, glob="**/*.pdf", loader_cls=PyPDFLoader, recursive=True) #find all PDFs in the directory and subdirectories
    documents = loader.load() #extract text and metadata from all PDFs
    chunks = SPLITTER.split_documents(documents) #split text into smaller chunks, and add metadata (chunk number)
    
    client = QdrantClient(QDRANT_URL)
    _ensure_collection(client) #create collection if it doesn't exist
    
    embeddings = _get_embeddings()
    
    # Embed chunks and insert into Qdrant
    points = []
    for chunk in chunks:
        embedding = embeddings.embed_query(chunk.page_content)
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                "content": chunk.page_content,
                "source": os.path.basename(chunk.metadata.get("source", "unknown")),
                "page": chunk.metadata.get("page", 0),
            }
        )
        points.append(point)
    
    if points:
        client.upsert(collection_name=COLLECTION, points=points)
    
    return len(chunks)    

if __name__ == "__main__":
    docs_dir = sys.argv[1] if len(sys.argv) > 1 else "./docs"
    n = ingest_directory(docs_dir)
    print(f"Ingested {n} chunks from directory: {docs_dir}")
    

