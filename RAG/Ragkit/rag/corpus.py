"""
the corpus decide what the retriver sees

"""

from collections.abc import Mapping

from rag.chunking import Chunker
from rag.documents import Chunk, Document


class Corpus:
    def __init__(self, chunks: list[Chunk]):
        self.chunks = {c.chunk_id: c for c in chunks}
        self._chunk_to_doc = {c.chunk_id: c.doc_id for c in chunks}

    @classmethod
    def build(cls, documents: list[Document], chunker: Chunker) -> "Corpus":
        chunks: list[Chunk] = []
        for doc in documents:
            chunks.extend(chunker.chunk(doc))
        return cls(chunks)

    def as_mapping(self) -> Mapping[str, str]:
        """{chunk_id: testo} — l'UNICO input dei retriever."""
        return {cid: c.text for cid, c in self.chunks.items()}

    def doc_of(self, chunk_id: str) -> str:
        return self._chunk_to_doc[chunk_id]

    @property
    def doc_ids(self) -> set[str]:
        return set(self._chunk_to_doc.values())

    @property
    def chunk_ids(self) -> list[str]:
        return list(self.chunks)

    def stats(self) -> dict[str, float]:
        n_docs, n_chunks = len(self.doc_ids), len(self.chunks)
        lengths = [len(c.text) for c in self.chunks.values()]
        return {
            "documents": n_docs,
            "chunks": n_chunks,
            "chunks_per_doc": n_chunks / n_docs if n_docs else 0.0,
            "avg_chunk_chars": sum(lengths) / n_chunks if n_chunks else 0.0,
        }


if __name__ == "__main__":
    from rag.loaders import load_directory
    from rag.chunking import ParagraphChunker

    docs = load_directory("data")
    corpus = Corpus.build(docs, ParagraphChunker(min_chars=200))

    s = corpus.stats()
    print(f"{int(s['documents'])} documenti -> {int(s['chunks'])} chunk "
          f"({s['chunks_per_doc']:.1f} chunk/doc, ~{s['avg_chunk_chars']:.0f} char/chunk)\n")

    print("Vista che vedra' il retriever (primi 3 chunk):")
    for cid, text in list(corpus.as_mapping().items())[:3]:
        print(f"  {cid:<26} -> {text[:45]}...")

    sample = "shor-quantum-threat#1"
    print(f"\nRisalita chunk -> documento: {sample} appartiene a "
          f"'{corpus.doc_of(sample)}'")