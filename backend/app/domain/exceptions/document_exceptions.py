"""
domain/exceptions/document_exceptions.py

Why this file exists:
    Framework-agnostic errors for document upload/retrieval, translated to
    HTTP only at the API boundary.
"""


class DocumentError(Exception):
    """Base class for document/RAG domain errors."""


class DocumentNotFoundError(DocumentError):
    def __init__(self, document_id):
        super().__init__(f"Document not found: {document_id}")


class DocumentProcessingError(DocumentError):
    def __init__(self, reason: str):
        super().__init__(f"Document processing failed: {reason}")
