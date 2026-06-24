"""
reads the file from disk e transforms them into document. We use the registry pattern as a decorator to register the loader class. 
The loader class is then used to load the documents from disk.
"""
from pathlib import Path
from typing import Any, List, Optional, Callable

from rag.documents import Document

_EXTRACTORS: dict[str, Callable[[Path], str]] = {}

def register(*extensions: str):
    def deco(fn: Callable[[Path], str]):
        for ext in extensions:
            _EXTRACTORS[ext.lower()] = fn
        return fn
    return deco

@register(".txt", ".md")
def _extract_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")

register(".pdf")
def _extract_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise RuntimeError("Per i PDF serve pypdf: pip install pypdf") from e
    reader = PdfReader(str(path))
    return "\n\n".join(page.extract_text() or "" for page in reader.pages)

def load_document(path: Path) -> Document:
    """
    Load a document from disk and return a Document object.
    """
    extractor = _EXTRACTORS.get(path.suffix.lower())
    if extractor is None:
        raise ValueError(f"Unsupported file extension: {path.suffix}")
    text = extractor(path).strip()
    return Document(doc_id=path.stem, text=text, source = str(path), metadata={"extension": path.suffix.lower(), "chars": len(text)})

def load_directory(directory: str | Path, recursive: bool = False) -> List[Document]:
    """
    Load all documents from a directory and return a list of Document objects.
    """
    directory = Path(directory)
    pattern = "**/*" if recursive else "*"
    docs = []
    for path in sorted(directory.glob(pattern)):
        if path.is_file() and path.suffix.lower() in _EXTRACTORS:
            docs.append(load_document(path))
    if not docs:
        raise FileNotFoundError(f"Nessun documento supportato in {directory}")
    return docs

if __name__ == "__main__":
    docs = load_directory("data")
    print(f"Caricati {len(docs)} documenti:\n")
    for d in docs:
        print(f"  {d.doc_id:<32} {d.metadata['chars']:>4} char")
    print(f"\nPrimo documento ({docs[0].doc_id}), primi 80 char:")
    print(" ", repr(docs[0].text[:80]))