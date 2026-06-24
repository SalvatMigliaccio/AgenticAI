from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class Document:
    """
    A class representing a document with an ID, text content, source, and optional metadata.
    """
    doc_id: str
    text: str
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)
    
@dataclass(frozen=True)
class Chunk:
    """
    A class representing a chunk of a document with an ID, text content, source, and optional metadata.
    """
    chunk_id: str
    doc_id: str
    text: str
    position: int
    metadata: dict[str, Any] = field(default_factory=dict)
    
if __name__ == "__main__":
    # Example usage
    doc = Document(doc_id="1", text="This is a sample document.", source="source1")
    chunk = Chunk(chunk_id="1-1", doc_id="1", text="This is a sample chunk.", position=0)
    
    print(doc)
    print(chunk)