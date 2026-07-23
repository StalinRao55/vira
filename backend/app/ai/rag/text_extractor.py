"""
ai/rag/text_extractor.py

Why this file exists:
    Normalizes every supported upload format (PDF, DOCX, TXT, Markdown)
    into plain text before chunking. This is the ONLY file that knows
    format-specific parsing libraries (pypdf, python-docx) — everything
    downstream (chunker, embeddings) works on plain strings.

How it communicates with other modules:
    - Called by application/use_cases/upload_document.py
"""

import io

import pypdf
from docx import Document as DocxDocument


class UnsupportedFileTypeError(Exception):
    def __init__(self, file_type: str):
        super().__init__(f"Unsupported file type for extraction: {file_type}")


def extract_text(content: bytes, file_type: str) -> str:
    """Dispatches to the correct extractor based on file_type (a simple
    extension-derived string like 'pdf', 'docx', 'txt', 'md')."""
    normalized = file_type.lower().lstrip(".")

    if normalized == "pdf":
        return _extract_pdf(content)
    if normalized == "docx":
        return _extract_docx(content)
    if normalized in ("txt", "md", "markdown"):
        return _extract_plain_text(content)

    raise UnsupportedFileTypeError(file_type)


def _extract_pdf(content: bytes) -> str:
    reader = pypdf.PdfReader(io.BytesIO(content))
    pages_text = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        # Page markers let the chunker attach a page number to each chunk's
        # metadata later, which is what makes citations useful ("page 4")
        # rather than just "somewhere in this PDF".
        pages_text.append(f"[page {page_number}]\n{text}")
    return "\n\n".join(pages_text)


def _extract_docx(content: bytes) -> str:
    doc = DocxDocument(io.BytesIO(content))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


def _extract_plain_text(content: bytes) -> str:
    # Try common encodings; fall back to replacing undecodable bytes rather
    # than failing the whole upload over one bad character.
    for encoding in ("utf-8", "latin-1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="replace")
