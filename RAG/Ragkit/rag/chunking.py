""""
simple chunking strategies for RAG, it is build as an abstract interface to be extended by other chunking strategies. The default implementation is a paragraph-based chunker that merges paragraphs until a minimum character threshold is reached.
"""

import re
from abc import ABC, abstractmethod

from rag.documents import Chunk, Document


class Chunker(ABC):
    @abstractmethod
    def split(self, text: str) -> list[str]:
        """Spezza il testo grezzo. Le sottoclassi implementano QUI."""

    def chunk(self, doc: Document) -> list[Chunk]:
        """Wrap comune: assegna id stabili '{doc_id}#{i}' ai pezzi."""
        pieces = [p for p in self.split(doc.text) if p.strip()]
        return [
            Chunk(chunk_id=f"{doc.doc_id}#{i}", doc_id=doc.doc_id,
                  text=piece.strip(), position=i, metadata=dict(doc.metadata))
            for i, piece in enumerate(pieces)
        ]


class ParagraphChunker(Chunker):
    def __init__(self, min_chars: int = 200, drop_headings: bool = True):
        self.min_chars = min_chars
        self.drop_headings = drop_headings

    def split(self, text: str) -> list[str]:
        paras = re.split(r"\n\s*\n", text)
        if self.drop_headings:
            paras = [p for p in paras
                     if not re.fullmatch(r"#{1,6}\s+.*", p.strip())]
        merged, buf = [], ""
        for p in paras:
            p = p.strip()
            if not p:
                continue
            buf = f"{buf}\n\n{p}".strip() if buf else p
            if len(buf) >= self.min_chars:
                merged.append(buf)
                buf = ""
        if buf:
            merged.append(buf)
        return merged


if __name__ == "__main__":
    from rag.loaders import load_directory

    docs = {d.doc_id: d for d in load_directory("data")}
    chunker = ParagraphChunker(min_chars=200)

    for doc_id in ("shor-quantum-threat", "aes"):
        chunks = chunker.chunk(docs[doc_id])
        print(f"\n{doc_id}: {len(chunks)} chunk")
        for c in chunks:
            print(f"  [{c.chunk_id}] ({len(c.text)} char) {c.text[:60]}...")