"""
api/v1/routers/documents.py

Why this file exists:
    HTTP boundary for the RAG feature: multipart file upload, listing,
    deletion, and a standalone search endpoint (useful for a "search my
    docs" UI panel independent of chat).
"""

from typing import Annotated

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.api.v1.dependencies import (
    get_current_user,
    get_delete_document_use_case,
    get_list_documents_use_case,
    get_search_documents_use_case,
    get_upload_document_use_case,
)
from app.api.v1.schemas.document_schemas import (
    DocumentResponse,
    DocumentSearchRequest,
    RetrievedChunkResponse,
)
from app.application.use_cases.manage_documents import DeleteDocumentUseCase, ListDocumentsUseCase
from app.application.use_cases.search_documents import SearchDocumentsUseCase
from app.application.use_cases.upload_document import UploadDocumentUseCase
from app.domain.entities.user import User
from app.domain.exceptions.common_exceptions import AccessDeniedError
from app.domain.exceptions.document_exceptions import DocumentNotFoundError, DocumentProcessingError

router = APIRouter(prefix="/documents", tags=["documents"])

_MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20 MB


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[UploadDocumentUseCase, Depends(get_upload_document_use_case)],
) -> DocumentResponse:
    content = await file.read()
    if len(content) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File exceeds 20MB limit")

    try:
        document = await use_case.execute(user_id=current_user.id, filename=file.filename or "untitled", content=content)
    except DocumentProcessingError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return DocumentResponse.model_validate(document)


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[ListDocumentsUseCase, Depends(get_list_documents_use_case)],
) -> list[DocumentResponse]:
    documents = await use_case.execute(user_id=current_user.id)
    return [DocumentResponse.model_validate(d) for d in documents]


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[DeleteDocumentUseCase, Depends(get_delete_document_use_case)],
) -> None:
    try:
        await use_case.execute(user_id=current_user.id, document_id=document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except AccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.post("/search", response_model=list[RetrievedChunkResponse])
async def search_documents(
    body: DocumentSearchRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[SearchDocumentsUseCase, Depends(get_search_documents_use_case)],
) -> list[RetrievedChunkResponse]:
    results = await use_case.execute(
        user_id=current_user.id, query=body.query, document_ids=body.document_ids, top_k=body.top_k
    )
    return [RetrievedChunkResponse(**r.__dict__) for r in results]
