"""
PDF Processor API routes - PDF upload, parsing, AI summarization, RAG queries, and export.
"""

import json
import os
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import PlainTextResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user
from app.database import get_session
from app.models.user import User
from app.modules.pdf_processor.schemas import (
    PDFCompareRequest,
    PDFExportRequest,
    PDFQueryRequest,
    PDFQueryResponse,
    PDFRead,
    PDFSummarizeRequest,
    PDFUploadResponse,
)
from app.modules.pdf_processor.service import PDFProcessorService
from app.rate_limit import limiter

router = APIRouter()

MAX_PDF_SIZE = 50 * 1024 * 1024  # 50 MB


def _doc_to_upload_response(doc) -> dict:
    """Convert a PDFDocument to upload response dict."""
    return {
        "id": doc.id,
        "user_id": doc.user_id,
        "filename": doc.original_filename,
        "num_pages": doc.num_pages,
        "file_size_kb": doc.file_size_kb,
        "status": doc.status.value if hasattr(doc.status, "value") else doc.status,
        "created_at": doc.created_at,
    }


def _doc_to_read(doc) -> dict:
    """Convert a PDFDocument to full read dict."""
    pages = json.loads(doc.pages_json) if doc.pages_json else []
    metadata = json.loads(doc.metadata_json) if doc.metadata_json else {}
    keywords = json.loads(doc.keywords_json) if doc.keywords_json else []
    return {
        "id": doc.id,
        "user_id": doc.user_id,
        "filename": doc.original_filename,
        "num_pages": doc.num_pages,
        "file_size_kb": doc.file_size_kb,
        "text_content": doc.text_content,
        "pages": pages,
        "metadata": metadata,
        "summary": doc.summary,
        "keywords": keywords,
        "status": doc.status.value if hasattr(doc.status, "value") else doc.status,
        "created_at": doc.created_at,
        "updated_at": doc.updated_at,
    }


@router.post("/upload", response_model=PDFUploadResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def upload_pdf(
    request: Request,
    file: UploadFile = File(..., description="PDF file to upload"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Upload a PDF file for processing.

    Extracts text, metadata, and page information.
    Supports PyMuPDF (preferred) and pdfplumber engines.

    Rate limit: 5 requests/minute
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="File must have a filename")

    _, ext = os.path.splitext(file.filename)
    if ext.lower() != ".pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    content = await file.read()
    if len(content) > MAX_PDF_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large. Maximum size is {MAX_PDF_SIZE // (1024 * 1024)} MB")

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    doc = await PDFProcessorService.upload_pdf(
        user_id=current_user.id,
        file_content=content,
        filename=file.filename,
        session=session,
    )
    return _doc_to_upload_response(doc)


@router.get("/", response_model=list[PDFUploadResponse])
@limiter.limit("30/minute")
async def list_pdfs(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    List all PDFs for the current user.

    Rate limit: 30 requests/minute
    """
    docs = await PDFProcessorService.list_pdfs(current_user.id, session)
    return [_doc_to_upload_response(d) for d in docs]


@router.get("/{pdf_id}", response_model=PDFRead)
@limiter.limit("30/minute")
async def get_pdf(
    request: Request,
    pdf_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get full PDF details including text content.

    Rate limit: 30 requests/minute
    """
    doc = await PDFProcessorService.get_pdf(current_user.id, pdf_id, session)
    if not doc:
        raise HTTPException(status_code=404, detail="PDF not found")
    return _doc_to_read(doc)


@router.delete("/{pdf_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
async def delete_pdf(
    request: Request,
    pdf_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Delete a PDF and its associated files.

    Rate limit: 5 requests/minute
    """
    if not await PDFProcessorService.delete_pdf(current_user.id, pdf_id, session):
        raise HTTPException(status_code=404, detail="PDF not found")


@router.post("/{pdf_id}/summarize")
@limiter.limit("10/minute")
async def summarize_pdf(
    request: Request,
    pdf_id: UUID,
    body: PDFSummarizeRequest = PDFSummarizeRequest(),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Generate an AI summary of a PDF.

    Styles: executive, detailed, bullet_points.

    Rate limit: 10 requests/minute
    """
    result = await PDFProcessorService.summarize_pdf(
        current_user.id, pdf_id, session, style=body.style,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="PDF not found")
    if result.get("error"):
        raise HTTPException(status_code=422, detail=result["error"])
    return result


@router.post("/{pdf_id}/keywords")
@limiter.limit("10/minute")
async def extract_keywords(
    request: Request,
    pdf_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Extract keywords from a PDF using AI.

    Rate limit: 10 requests/minute
    """
    result = await PDFProcessorService.extract_keywords(current_user.id, pdf_id, session)
    if result is None:
        raise HTTPException(status_code=404, detail="PDF not found")
    return result


@router.post("/{pdf_id}/query", response_model=PDFQueryResponse)
@limiter.limit("10/minute")
async def query_pdf(
    request: Request,
    pdf_id: UUID,
    body: PDFQueryRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Ask a question about a PDF using RAG (chunk + search + AI answer).

    Rate limit: 10 requests/minute
    """
    result = await PDFProcessorService.query_pdf(
        current_user.id, pdf_id, body.question, session,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="PDF not found")
    return PDFQueryResponse(**result)


@router.get("/{pdf_id}/export/{export_format}")
@limiter.limit("30/minute")
async def export_pdf(
    request: Request,
    pdf_id: UUID,
    export_format: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Export PDF content as markdown, txt, or json.

    Rate limit: 30 requests/minute
    """
    if export_format not in ("markdown", "txt", "json"):
        raise HTTPException(status_code=400, detail="Supported formats: markdown, txt, json")

    result = await PDFProcessorService.export_pdf(current_user.id, pdf_id, export_format, session)
    if result is None:
        raise HTTPException(status_code=404, detail="PDF not found")
    if result.get("error"):
        raise HTTPException(status_code=422, detail=result["error"])

    if export_format == "txt":
        return PlainTextResponse(content=result["content"], media_type="text/plain")

    return result


@router.post("/compare")
@limiter.limit("5/minute")
async def compare_pdfs(
    request: Request,
    body: PDFCompareRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Compare 2-5 PDFs using AI.

    Comparison types: content, structure, summary.

    Rate limit: 5 requests/minute
    """
    result = await PDFProcessorService.compare_pdfs(
        current_user.id, body.pdf_ids, body.comparison_type, session,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="PDFs not found")
    if result.get("error"):
        raise HTTPException(status_code=422, detail=result["error"])
    return result


@router.post("/{pdf_id}/tables")
@limiter.limit("10/minute")
async def extract_tables(
    request: Request,
    pdf_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Extract tables from a PDF.

    Uses pdfplumber or PyMuPDF table detection.

    Rate limit: 10 requests/minute
    """
    result = await PDFProcessorService.extract_tables(current_user.id, pdf_id, session)
    if result is None:
        raise HTTPException(status_code=404, detail="PDF not found")
    return result


@router.post("/{pdf_id}/ocr")
@limiter.limit("5/minute")
async def ocr_pdf(
    request: Request,
    pdf_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    OCR a scanned PDF to extract text from images.

    Requires pytesseract and Tesseract-OCR to be installed.

    Rate limit: 5 requests/minute
    """
    result = await PDFProcessorService.ocr_pdf(current_user.id, pdf_id, session)
    if result is None:
        raise HTTPException(status_code=404, detail="PDF not found")
    if result.get("error"):
        raise HTTPException(status_code=422, detail=result["error"])
    return result


@router.get("/status/engines")
async def parser_status():
    """Check which PDF parsing engines are available."""
    return PDFProcessorService.get_parser_status()
