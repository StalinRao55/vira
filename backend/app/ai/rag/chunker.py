"""
ai/rag/chunker.py

Why this file exists:
    Splits long extracted text into retrieval-sized pieces. Chunk size
    balances two failure modes: too large and embeddings become a vague
    blend that matches nothing precisely; too small and a chunk loses the
    surrounding context needed to make sense on its own. Overlap between
    consecutive chunks prevents a fact from being split exactly at a
    boundary and becoming unretrievable by either half.

How it communicates with other modules:
    - Called by application/use_cases/upload_document.py
    - Output consumed by ai/rag/rag_engine.py for embedding
"""

from dataclasses import dataclass


@dataclass
class Chunk:
    content: str
    chunk_index: int
    metadata: dict


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 150) -> list[Chunk]:
    """Character-based sliding-window chunking. Character-based (not
    word/token-based) keeps this dependency-free; swap for a tokenizer-aware
    splitter if precise token budgeting per chunk becomes necessary."""
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    text = text.strip()
    if not text:
        return []

    chunks: list[Chunk] = []
    start = 0
    index = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        # Prefer to break on a paragraph/sentence boundary near the target
        # end, rather than mid-word, when one exists within a reasonable
        # look-back window.
        if end < len(text):
            boundary = text.rfind("\n\n", start, end)
            if boundary == -1:
                boundary = text.rfind(". ", start, end)
            if boundary != -1 and boundary > start + chunk_size // 2:
                end = boundary + 1

        content = text[start:end].strip()
        if content:
            chunks.append(Chunk(content=content, chunk_index=index, metadata={}))
            index += 1

        if end >= len(text):
            break
        start = end - overlap

    return chunks
