import asyncio
import sys
import uuid
from pathlib import Path

from qdrant_client.models import PointStruct
from app.llm.embeddings import embed
from app.rag.store import client, ensure_collection

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - dependency check happens at install time
    PdfReader = None


def _chunk(text: str, size: int = 900, overlap: int = 150) -> list[str]:
    """Chunking a finestra scorrevole su parole (semplice e robusto)."""
    words = text.split()
    chunks, i = [], 0
    while i < len(words):
        chunks.append(" ".join(words[i:i + size]))
        i += size - overlap
    return [c for c in chunks if c.strip()]


def _read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _read_pdf_file(path: Path) -> list[tuple[str, str]]:
    if PdfReader is None:
        raise RuntimeError(
            "Per ingestire i PDF installa la dipendenza 'pypdf' nel backend."
        )

    reader = PdfReader(str(path))
    pages: list[tuple[str, str]] = []
    for index, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append((text, f"{path.name}#page{index}"))
    return pages


async def ingest_folder(collection: str, folder: str) -> None:
    await ensure_collection(collection)
    paths = [p for p in Path(folder).rglob("*") if p.suffix.lower() in {".txt", ".md", ".pdf"}]
    if not paths:
        print(f"Nessun .txt/.md/.pdf in {folder}")
        return

    # 1) Raccolgo tutti i chunk con la loro provenienza.
    records: list[tuple[str, str]] = []   # (testo_chunk, nome_file)
    for p in paths:
        if p.suffix.lower() == ".pdf":
            for page_text, source in _read_pdf_file(p):
                for ch in _chunk(page_text):
                    records.append((ch, source))
        else:
            for ch in _chunk(_read_text_file(p)):
                records.append((ch, p.name))

    # 2) Embedding a batch (Ollama regge bene batch moderati).
    texts = [t for t, _ in records]
    vectors: list[list[float]] = []
    for start in range(0, len(texts), 32):
        vectors.extend(await embed(texts[start:start + 32]))

    # 3) Upsert in Qdrant: il testo sta nel payload, lo rileggiamo in retrieval.
    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=vec,
            payload={"text": txt, "source": src},
        )
        for (txt, src), vec in zip(records, vectors)
    ]
    await client.upsert(collection_name=collection, points=points)
    print(f"Caricati {len(points)} chunk in '{collection}'.")


# Uso: python -m app.rag.ingest kb_crypto ./knowledge/crypto
if __name__ == "__main__":
    asyncio.run(ingest_folder(sys.argv[1], sys.argv[2]))