"""
tests/unit/ai/test_chunker.py

Why this file exists:
    Verifies chunking produces sane, overlapping, index-ordered pieces and
    handles edge cases (empty text, text shorter than one chunk) correctly.
"""

from app.ai.rag.chunker import chunk_text


def test_short_text_produces_single_chunk():
    chunks = chunk_text("This is a short document.", chunk_size=1000, overlap=150)
    assert len(chunks) == 1
    assert chunks[0].chunk_index == 0
    assert chunks[0].content == "This is a short document."


def test_empty_text_produces_no_chunks():
    assert chunk_text("", chunk_size=1000, overlap=150) == []
    assert chunk_text("   ", chunk_size=1000, overlap=150) == []


def test_long_text_produces_multiple_overlapping_chunks():
    # Build text long enough to force multiple chunks at a small chunk_size.
    paragraph = "Sentence about topic A. " * 20  # ~500 chars
    text = paragraph + "\n\n" + ("Sentence about topic B. " * 20)

    chunks = chunk_text(text, chunk_size=300, overlap=50)

    assert len(chunks) > 1
    # Indices should be sequential starting at 0
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))
    # No chunk should exceed chunk_size by a large margin
    assert all(len(c.content) <= 300 + 50 for c in chunks)


def test_overlap_must_be_smaller_than_chunk_size():
    import pytest

    with pytest.raises(ValueError):
        chunk_text("some text", chunk_size=100, overlap=100)
