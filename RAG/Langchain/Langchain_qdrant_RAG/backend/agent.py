import os
import requests
from dotenv import load_dotenv

from langchain.embeddings.base import Embeddings
from langchain.tools import Tool
from qdrant_client import QdrantClient

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

# Custom Ollama LLM using HTTP calls
class OllamaLLM:
    def __init__(self, model: str = "mistral", base_url: str = "http://ollama:11434"):
        self.model = model
        self.base_url = base_url
    
    def call(self, prompt: str, **kwargs) -> str:
        resp = requests.post(
            f"{self.base_url}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False}
        )
        resp.raise_for_status()
        return resp.json()["response"]
    
    def __call__(self, prompt: str, **kwargs) -> str:
        return self.call(prompt, **kwargs)

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
COLLECTION = os.getenv("QDRANT_COLLECTION", "pdf_docs")

def build_agent(allowed_sources=None):
    """
    Assembles and returns a LangChain ReAct agent wired to the Qdrant
    vector store. The agent exposes one tool — a semantic retriever over
    the indexed PDFs — and uses the ReAct loop to decide when to call it.
    """
    # -----------------------------------------------------------------------
    # LLM — Mistral running locally via Ollama (HTTP-based).
    # -----------------------------------------------------------------------
    llm = OllamaLLM(
        model="mistral",
        base_url=OLLAMA_URL,
    )
    
    # Embeddings — custom HTTP-based Ollama embeddings
    embeddings_model = OllamaEmbeddings(
        model="nomic-embed-text", 
        base_url=OLLAMA_URL
    )
    
    # Initialize Qdrant client for vector search
    qdrant_client = QdrantClient(QDRANT_URL)
    allowed_sources = {
        os.path.basename(str(s)) for s in (allowed_sources or []) if str(s).strip()
    }

    def _search_points(query_vector, limit=5):
        """Compatibility layer for qdrant-client versions."""
        if hasattr(qdrant_client, "query_points"):
            result = qdrant_client.query_points(
                collection_name=COLLECTION,
                query=query_vector,
                limit=limit,
            )
            return result.points if hasattr(result, "points") else result

        # Fallback for older qdrant-client APIs
        return qdrant_client.search(
            collection_name=COLLECTION,
            query_vector=query_vector,
            limit=limit,
        )
    
    # -----------------------------------------------------------------------
    # Retriever tool — create manually for direct Qdrant search.
    # -----------------------------------------------------------------------
    
    def _retrieve_hits(query: str, limit=8):
        try:
            query_embedding = embeddings_model.embed_query(query)
            # Search a large pool to maximise recall across all tracked documents
            search_limit = max(100, len(allowed_sources) * 20) if allowed_sources else 100
            search_results = _search_points(query_embedding, limit=search_limit)

            # Group hits by source document
            per_source: dict = {}
            for point in search_results:
                payload = point.payload if hasattr(point, 'payload') else {}
                source = os.path.basename(str(payload.get('source', 'Unknown')))
                if allowed_sources and source not in allowed_sources:
                    continue
                page = payload.get('page', 0)
                content = payload.get('content', '')
                per_source.setdefault(source, []).append(
                    {"source": source, "page": page, "content": content}
                )

            if not per_source:
                return []

            # Round-robin: take up to 2 best chunks per source to ensure diversity
            hits = []
            slots_per_source = max(1, limit // max(len(per_source), 1))
            for source_hits in per_source.values():
                hits.extend(source_hits[:slots_per_source])

            # Fill remaining slots with best leftover chunks
            extra = limit - len(hits)
            if extra > 0:
                for source_hits in per_source.values():
                    for h in source_hits[slots_per_source:]:
                        if extra <= 0:
                            break
                        hits.append(h)
                        extra -= 1

            return hits[:limit]
        except Exception as e:
            return [{"error": str(e)}]

    def _format_tool_output(hits):
        if not hits:
            return "No relevant documents found."
        if "error" in hits[0]:
            return f"Error searching documents: {hits[0]['error']}"

        rows = []
        for h in hits:
            rows.append(
                f"Source: {h['source']}\nPage: {h['page']}\n\n{h['content']}"
            )
        return "\n\n---\n\n".join(rows)

    def retrieve_pdf_info(query: str) -> str:
        """Searches the uploaded PDF documents for relevant information."""
        return _format_tool_output(_retrieve_hits(query))
    
    retriever_tool = Tool(
        name="cerca_nei_pdf",
        func=retrieve_pdf_info,
        description=(
            "Searches the uploaded PDF documents for relevant information. "
            "Use this tool to answer any question about the document contents. "
            "Returns the most relevant passages together with the source file "
            "name and page number for citation."
        ),
    )
    
    # -----------------------------------------------------------------------
    # For now, return a simple mock agent that just uses the retriever tool.
    # A full ReAct agent requires more complex integration with Ollama LLM.
    # -----------------------------------------------------------------------
    class SimpleAgent:
        def __call__(self, prompt):
            return self.invoke({"input": prompt})["output"]
        
        def invoke(self, data):
            question = data.get("input", "") if isinstance(data, dict) else str(data)
            hits = _retrieve_hits(question, limit=8)
            tool_output = _format_tool_output(hits)

            if not hits:
                return {
                    "output": "Non ho trovato contenuti rilevanti nei documenti caricati.",
                    "intermediate_steps": [("cerca_nei_pdf", tool_output)],
                }

            if "error" in hits[0]:
                return {
                    "output": f"Errore durante la ricerca nei documenti: {hits[0]['error']}",
                    "intermediate_steps": [("cerca_nei_pdf", tool_output)],
                }

            context_blocks = []
            for h in hits[:8]:
                context_blocks.append(
                    f"[Source: {h['source']} | Page: {h['page']}]\n{h['content'][:600]}"
                )
            context = "\n\n".join(context_blocks)

            docs_list = ", ".join(sorted(allowed_sources)) if allowed_sources else "nessun documento"
            prompt = (
                "Sei un assistente RAG. Rispondi in italiano in modo chiaro e sintetico, "
                "usando solo il contesto fornito. Se l'informazione non c'e, dillo esplicitamente.\n\n"
                f"Documenti disponibili: {docs_list}\n\n"
                f"Domanda: {question}\n\n"
                f"Contesto:\n{context}\n\n"
                "Risposta:"
            )

            answer = llm.call(prompt)
            return {
                "output": answer.strip(),
                "intermediate_steps": [("cerca_nei_pdf", tool_output)],
            }
    
    return SimpleAgent()
    