"""
PDF Processor service - PDF upload, parsing, AI summarization, RAG queries, and export.

PDF parsing engines (auto-detected):
- PyMuPDF (fitz) - fast, full-featured (preferred)
- pdfplumber - Python-native fallback
- OCR via pytesseract for scanned PDFs (optional)
"""

import json
import math
import os
import re
import shutil
from collections import Counter
from datetime import UTC, datetime
from typing import Optional
from uuid import UUID

import structlog
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.pdf_processor import PDFDocument, PDFStatus

logger = structlog.get_logger()

# Auto-detection: PyMuPDF (best) -> pdfplumber (fallback)
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    import pytesseract
    from PIL import Image
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

# Upload directory
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "..", "uploads"))
MAX_PDF_SIZE = 50 * 1024 * 1024  # 50 MB

# Chunking config for RAG
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


class PDFProcessorService:
    """Service for PDF processing, AI analysis, and RAG queries."""

    # ------------------------------------------------------------------
    # Text chunking (same pattern as knowledge module)
    # ------------------------------------------------------------------

    @staticmethod
    def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
        """Split text into overlapping chunks for RAG."""
        if not text.strip():
            return []

        paragraphs = re.split(r'\n\s*\n', text)
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_chunk) + len(para) <= chunk_size:
                current_chunk += ("\n\n" + para) if current_chunk else para
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                if overlap > 0 and current_chunk:
                    overlap_text = current_chunk[-overlap:]
                    current_chunk = overlap_text + "\n\n" + para
                else:
                    current_chunk = para

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks if chunks else [text.strip()[:chunk_size]]

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(r'[a-z0-9]+', text.lower())

    @staticmethod
    def _compute_tf(tokens: list[str]) -> dict[str, float]:
        counts = Counter(tokens)
        total = len(tokens)
        return {term: count / total for term, count in counts.items()} if total > 0 else {}

    @staticmethod
    def _cosine_similarity(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
        common = set(vec_a.keys()) & set(vec_b.keys())
        if not common:
            return 0.0
        dot_product = sum(vec_a[t] * vec_b[t] for t in common)
        norm_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
        norm_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)

    # ------------------------------------------------------------------
    # PDF parsing engines
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_with_pymupdf(file_path: str) -> dict:
        """Extract text, metadata, and page info using PyMuPDF (fitz)."""
        doc = fitz.open(file_path)
        pages = []
        full_text = ""
        images_count = 0

        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text("text")
            pages.append({
                "page_number": page_num + 1,
                "text": page_text,
                "width": page.rect.width,
                "height": page.rect.height,
            })
            full_text += page_text + "\n\n"
            images_count += len(page.get_images(full=True))

        meta = doc.metadata or {}
        metadata = {
            "author": meta.get("author", ""),
            "title": meta.get("title", ""),
            "subject": meta.get("subject", ""),
            "creator": meta.get("creator", ""),
            "producer": meta.get("producer", ""),
            "creation_date": meta.get("creationDate", ""),
            "modification_date": meta.get("modDate", ""),
            "images_count": images_count,
            "engine": "pymupdf",
        }

        doc.close()
        return {
            "text": full_text.strip(),
            "pages": pages,
            "num_pages": len(pages),
            "metadata": metadata,
        }

    @staticmethod
    def _extract_with_pdfplumber(file_path: str) -> dict:
        """Extract text and page info using pdfplumber (fallback)."""
        pages = []
        full_text = ""

        with pdfplumber.open(file_path) as pdf:
            metadata = {
                "author": pdf.metadata.get("Author", "") if pdf.metadata else "",
                "title": pdf.metadata.get("Title", "") if pdf.metadata else "",
                "creator": pdf.metadata.get("Creator", "") if pdf.metadata else "",
                "creation_date": pdf.metadata.get("CreationDate", "") if pdf.metadata else "",
                "engine": "pdfplumber",
            }
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text() or ""
                pages.append({
                    "page_number": i + 1,
                    "text": page_text,
                    "width": page.width,
                    "height": page.height,
                })
                full_text += page_text + "\n\n"

        return {
            "text": full_text.strip(),
            "pages": pages,
            "num_pages": len(pages),
            "metadata": metadata,
        }

    @staticmethod
    def _get_file_dir(user_id: UUID, pdf_id: UUID) -> str:
        """Get the storage directory for a PDF."""
        dir_path = os.path.join(UPLOAD_DIR, "pdf_processor", str(user_id), str(pdf_id))
        os.makedirs(dir_path, exist_ok=True)
        return dir_path

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    @staticmethod
    async def upload_pdf(
        user_id: UUID,
        file_content: bytes,
        filename: str,
        session: AsyncSession,
    ) -> PDFDocument:
        """Upload and parse a PDF file."""
        pdf_doc = PDFDocument(
            user_id=user_id,
            original_filename=filename,
            filename=filename,
            file_size_kb=len(file_content) // 1024,
            status=PDFStatus.PROCESSING,
        )
        session.add(pdf_doc)
        await session.flush()

        file_dir = PDFProcessorService._get_file_dir(user_id, pdf_doc.id)
        filename = os.path.basename(filename)
        if not filename:
            raise ValueError("Invalid filename after sanitization")
        file_path = os.path.join(file_dir, filename)

        try:
            # Save file to disk
            with open(file_path, "wb") as f:
                f.write(file_content)

            pdf_doc.file_path = file_path

            # Extract text using best available engine
            if HAS_PYMUPDF:
                extracted = PDFProcessorService._extract_with_pymupdf(file_path)
            elif HAS_PDFPLUMBER:
                extracted = PDFProcessorService._extract_with_pdfplumber(file_path)
            else:
                pdf_doc.status = PDFStatus.FAILED
                pdf_doc.metadata_json = json.dumps({"error": "No PDF parser available. Install PyMuPDF or pdfplumber."})
                session.add(pdf_doc)
                await session.commit()
                await session.refresh(pdf_doc)
                return pdf_doc

            pdf_doc.text_content = extracted["text"]
            pdf_doc.pages_json = json.dumps(extracted["pages"], ensure_ascii=False)
            pdf_doc.metadata_json = json.dumps(extracted["metadata"], ensure_ascii=False)
            pdf_doc.num_pages = extracted["num_pages"]
            pdf_doc.status = PDFStatus.READY
            pdf_doc.updated_at = datetime.now(UTC)

            logger.info(
                "pdf_uploaded",
                pdf_id=str(pdf_doc.id),
                filename=filename,
                pages=extracted["num_pages"],
                engine=extracted["metadata"].get("engine", "unknown"),
            )

        except Exception as e:
            pdf_doc.status = PDFStatus.FAILED
            pdf_doc.metadata_json = json.dumps({"error": str(e)[:1000]})
            pdf_doc.updated_at = datetime.now(UTC)
            logger.error("pdf_upload_failed", error=str(e))

        session.add(pdf_doc)
        await session.commit()
        await session.refresh(pdf_doc)
        return pdf_doc

    @staticmethod
    async def list_pdfs(
        user_id: UUID,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 20,
    ) -> list[PDFDocument]:
        """List PDFs for a user (paginated)."""
        result = await session.execute(
            select(PDFDocument)
            .where(PDFDocument.user_id == user_id, PDFDocument.is_deleted == False)
            .order_by(PDFDocument.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_pdf(
        user_id: UUID,
        pdf_id: UUID,
        session: AsyncSession,
    ) -> Optional[PDFDocument]:
        """Get a single PDF with text content."""
        doc = await session.get(PDFDocument, pdf_id)
        if not doc or doc.user_id != user_id or doc.is_deleted:
            return None
        return doc

    @staticmethod
    async def delete_pdf(
        user_id: UUID,
        pdf_id: UUID,
        session: AsyncSession,
    ) -> bool:
        """Soft-delete a PDF and remove files."""
        doc = await session.get(PDFDocument, pdf_id)
        if not doc or doc.user_id != user_id:
            return False

        doc.is_deleted = True
        doc.updated_at = datetime.now(UTC)
        session.add(doc)
        await session.commit()

        # Remove files from disk
        try:
            file_dir = PDFProcessorService._get_file_dir(user_id, pdf_id)
            if os.path.exists(file_dir):
                shutil.rmtree(file_dir)
        except Exception as e:
            logger.warning("pdf_file_cleanup_failed", pdf_id=str(pdf_id), error=str(e))

        logger.info("pdf_deleted", pdf_id=str(pdf_id))
        return True

    # ------------------------------------------------------------------
    # AI operations
    # ------------------------------------------------------------------

    @staticmethod
    async def summarize_pdf(
        user_id: UUID,
        pdf_id: UUID,
        session: AsyncSession,
        style: str = "executive",
    ) -> Optional[dict]:
        """Generate an AI summary of a PDF."""
        doc = await session.get(PDFDocument, pdf_id)
        if not doc or doc.user_id != user_id or doc.is_deleted:
            return None

        if not doc.text_content:
            return {"summary": "", "error": "No text content available for this PDF"}

        style_instructions = {
            "executive": "Write a concise executive summary (3-5 paragraphs) highlighting key points, conclusions, and actionable insights.",
            "detailed": "Write a comprehensive detailed summary covering all major sections, arguments, data points, and conclusions.",
            "bullet_points": "Write a summary as a structured list of bullet points organized by topic/section.",
        }

        prompt = (
            f"Summarize the following PDF document.\n\n"
            f"Style: {style_instructions.get(style, style_instructions['executive'])}\n\n"
            f"Document ({doc.num_pages} pages, filename: {doc.original_filename}):\n"
            f"{doc.text_content[:12000]}\n\n"
            f"Summary:"
        )

        try:
            from app.ai_assistant.service import AIAssistantService
            result = await AIAssistantService.process_text_with_provider(
                text=prompt,
                task="pdf_summarize",
                provider_name="gemini",
                user_id=user_id,
                module="pdf_processor",
            )
            summary = result.get("processed_text", "")

            doc.summary = summary
            doc.updated_at = datetime.now(UTC)
            session.add(doc)
            await session.commit()

            try:
                from app.modules.cost_tracker.tracker import track_ai_usage
                await track_ai_usage(
                    user_id=user_id, provider="gemini",
                    model=result.get("model", "gemini-2.5-flash"),
                    module="pdf_processor", action="summarize",
                    input_tokens=0, output_tokens=0, latency_ms=0,
                    success=True, session=session,
                )
            except Exception:
                pass

            return {"summary": summary, "style": style, "provider": result.get("provider", "gemini")}

        except Exception as e:
            logger.error("pdf_summarize_failed", error=str(e))
            return {"summary": "", "error": str(e)[:500]}

    @staticmethod
    async def extract_keywords(
        user_id: UUID,
        pdf_id: UUID,
        session: AsyncSession,
    ) -> Optional[dict]:
        """Extract keywords from a PDF using AI."""
        doc = await session.get(PDFDocument, pdf_id)
        if not doc or doc.user_id != user_id or doc.is_deleted:
            return None

        if not doc.text_content:
            return {"keywords": [], "error": "No text content available"}

        prompt = (
            f"Extract the 10-20 most important keywords and key phrases from this document. "
            f"Return them as a JSON array of strings.\n\n"
            f"Document:\n{doc.text_content[:10000]}\n\n"
            f"Keywords (JSON array):"
        )

        try:
            from app.ai_assistant.service import AIAssistantService
            result = await AIAssistantService.process_text_with_provider(
                text=prompt,
                task="pdf_keywords",
                provider_name="gemini",
                user_id=user_id,
                module="pdf_processor",
            )

            response = result.get("processed_text", "[]")
            start = response.find("[")
            end = response.rfind("]") + 1
            keywords = []
            if start >= 0 and end > start:
                keywords = json.loads(response[start:end])

            doc.keywords_json = json.dumps(keywords, ensure_ascii=False)
            doc.updated_at = datetime.now(UTC)
            session.add(doc)
            await session.commit()

            return {"keywords": keywords}

        except Exception as e:
            logger.error("pdf_keywords_failed", error=str(e))
            return {"keywords": [], "error": str(e)[:500]}

    @staticmethod
    async def query_pdf(
        user_id: UUID,
        pdf_id: UUID,
        question: str,
        session: AsyncSession,
    ) -> Optional[dict]:
        """RAG query: chunk PDF text, find relevant chunks, answer with AI + sources."""
        doc = await session.get(PDFDocument, pdf_id)
        if not doc or doc.user_id != user_id or doc.is_deleted:
            return None

        if not doc.text_content:
            return {"answer": "No text content available for this PDF.", "sources": [], "confidence": 0.0}

        # Chunk the text
        chunks = PDFProcessorService._chunk_text(doc.text_content)

        # Find relevant chunks using TF-IDF similarity
        query_tokens = PDFProcessorService._tokenize(question)
        query_tf = PDFProcessorService._compute_tf(query_tokens)

        scored_chunks = []
        for i, chunk_text in enumerate(chunks):
            chunk_tokens = PDFProcessorService._tokenize(chunk_text)
            chunk_tf = PDFProcessorService._compute_tf(chunk_tokens)
            score = PDFProcessorService._cosine_similarity(query_tf, chunk_tf)
            if score > 0:
                scored_chunks.append({"index": i, "text": chunk_text, "score": round(score, 4)})

        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        top_chunks = scored_chunks[:5]

        if top_chunks:
            context_parts = []
            for j, sc in enumerate(top_chunks):
                context_parts.append(f"[Chunk {j + 1}, score={sc['score']}]\n{sc['text']}")
            context = "\n\n".join(context_parts)
        else:
            context = doc.text_content[:3000]

        prompt = (
            f"Based on the following context from a PDF document ({doc.original_filename}), "
            f"answer the question. If the answer cannot be found in the context, say so clearly.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n\n"
            f"Answer:"
        )

        try:
            from app.ai_assistant.service import AIAssistantService
            result = await AIAssistantService.process_text_with_provider(
                text=prompt,
                task="pdf_rag_query",
                provider_name="gemini",
                user_id=user_id,
                module="pdf_processor",
            )
            answer = result.get("processed_text", "Unable to generate answer.")

            avg_score = sum(c["score"] for c in top_chunks) / len(top_chunks) if top_chunks else 0.0
            confidence = min(1.0, avg_score * 5)

            sources = [
                {"chunk_index": c["index"], "text": c["text"][:200], "relevance": c["score"]}
                for c in top_chunks
            ]

            try:
                from app.modules.cost_tracker.tracker import track_ai_usage
                await track_ai_usage(
                    user_id=user_id, provider="gemini",
                    model=result.get("model", "gemini-2.5-flash"),
                    module="pdf_processor", action="rag_query",
                    input_tokens=0, output_tokens=0, latency_ms=0,
                    success=True, session=session,
                )
            except Exception:
                pass

            return {"answer": answer, "sources": sources, "confidence": round(confidence, 3)}

        except Exception as e:
            logger.error("pdf_query_failed", error=str(e))
            return {"answer": f"Error: {str(e)[:500]}", "sources": [], "confidence": 0.0}

    @staticmethod
    async def export_pdf(
        user_id: UUID,
        pdf_id: UUID,
        export_format: str,
        session: AsyncSession,
    ) -> Optional[dict]:
        """Export PDF content to markdown, txt, or JSON."""
        doc = await session.get(PDFDocument, pdf_id)
        if not doc or doc.user_id != user_id or doc.is_deleted:
            return None

        pages = json.loads(doc.pages_json) if doc.pages_json else []
        metadata = json.loads(doc.metadata_json) if doc.metadata_json else {}
        keywords = json.loads(doc.keywords_json) if doc.keywords_json else []

        if export_format == "markdown":
            md = f"# {doc.original_filename}\n\n"
            if metadata.get("title"):
                md += f"**Title:** {metadata['title']}\n"
            if metadata.get("author"):
                md += f"**Author:** {metadata['author']}\n"
            md += f"**Pages:** {doc.num_pages}\n\n"
            if doc.summary:
                md += f"## Summary\n\n{doc.summary}\n\n"
            if keywords:
                md += f"**Keywords:** {', '.join(keywords)}\n\n"
            md += "---\n\n## Content\n\n"
            for page in pages:
                md += f"### Page {page['page_number']}\n\n{page.get('text', '')}\n\n"
            return {"content": md, "format": "markdown", "filename": f"{doc.original_filename}.md"}

        elif export_format == "txt":
            txt = f"{doc.original_filename}\n{'=' * len(doc.original_filename)}\n\n"
            txt += doc.text_content or ""
            return {"content": txt, "format": "txt", "filename": f"{doc.original_filename}.txt"}

        elif export_format == "json":
            data = {
                "filename": doc.original_filename,
                "num_pages": doc.num_pages,
                "metadata": metadata,
                "summary": doc.summary,
                "keywords": keywords,
                "pages": pages,
                "text_content": doc.text_content,
            }
            return {"content": json.dumps(data, ensure_ascii=False, indent=2), "format": "json", "filename": f"{doc.original_filename}.json"}

        return {"content": "", "format": export_format, "error": f"Unsupported format: {export_format}"}

    @staticmethod
    async def compare_pdfs(
        user_id: UUID,
        pdf_ids: list[UUID],
        comparison_type: str,
        session: AsyncSession,
    ) -> Optional[dict]:
        """Compare 2-5 PDFs using AI."""
        docs = []
        for pid in pdf_ids:
            doc = await session.get(PDFDocument, pid)
            if not doc or doc.user_id != user_id or doc.is_deleted:
                return {"error": f"PDF {pid} not found or not accessible"}
            docs.append(doc)

        if len(docs) < 2:
            return {"error": "At least 2 PDFs are required for comparison"}

        type_instructions = {
            "content": "Compare the content, topics, arguments, and conclusions of each document.",
            "structure": "Compare the structure, organization, page counts, and formatting of each document.",
            "summary": "Provide a brief summary of each document, then highlight key similarities and differences.",
        }

        doc_summaries = []
        for i, doc in enumerate(docs):
            text = doc.text_content or ""
            doc_summaries.append(
                f"Document {i + 1}: {doc.original_filename} ({doc.num_pages} pages)\n"
                f"{text[:3000]}\n"
            )

        prompt = (
            f"Compare the following {len(docs)} PDF documents.\n\n"
            f"Comparison type: {type_instructions.get(comparison_type, type_instructions['content'])}\n\n"
            f"{''.join(doc_summaries)}\n\n"
            f"Provide a structured comparison with similarities, differences, and key insights."
        )

        try:
            from app.ai_assistant.service import AIAssistantService
            result = await AIAssistantService.process_text_with_provider(
                text=prompt,
                task="pdf_compare",
                provider_name="gemini",
                user_id=user_id,
                module="pdf_processor",
            )
            comparison = result.get("processed_text", "")
            return {
                "comparison": comparison,
                "comparison_type": comparison_type,
                "documents": [
                    {"id": str(d.id), "filename": d.original_filename, "num_pages": d.num_pages}
                    for d in docs
                ],
                "provider": result.get("provider", "gemini"),
            }

        except Exception as e:
            logger.error("pdf_compare_failed", error=str(e))
            return {"comparison": "", "error": str(e)[:500]}

    @staticmethod
    async def extract_tables(
        user_id: UUID,
        pdf_id: UUID,
        session: AsyncSession,
    ) -> Optional[dict]:
        """Extract tables from a PDF."""
        doc = await session.get(PDFDocument, pdf_id)
        if not doc or doc.user_id != user_id or doc.is_deleted:
            return None

        if not doc.file_path or not os.path.exists(doc.file_path):
            return {"tables": [], "error": "PDF file not found on disk"}

        tables = []

        if HAS_PDFPLUMBER:
            try:
                with pdfplumber.open(doc.file_path) as pdf:
                    for i, page in enumerate(pdf.pages):
                        page_tables = page.extract_tables()
                        for j, table in enumerate(page_tables):
                            if table and len(table) > 0:
                                headers = table[0] if table[0] else [f"col_{k}" for k in range(len(table[0]))]
                                rows = table[1:] if len(table) > 1 else []
                                tables.append({
                                    "page": i + 1,
                                    "table_index": j,
                                    "headers": headers,
                                    "rows": rows,
                                    "row_count": len(rows),
                                })
                return {"tables": tables, "total": len(tables), "engine": "pdfplumber"}
            except Exception as e:
                logger.warning("pdf_table_extraction_failed_pdfplumber", error=str(e))

        if HAS_PYMUPDF:
            try:
                pdf_doc = fitz.open(doc.file_path)
                for i in range(len(pdf_doc)):
                    page = pdf_doc[i]
                    page_tables = page.find_tables()
                    for j, table in enumerate(page_tables.tables):
                        data = table.extract()
                        if data and len(data) > 0:
                            tables.append({
                                "page": i + 1,
                                "table_index": j,
                                "headers": data[0],
                                "rows": data[1:],
                                "row_count": len(data) - 1,
                            })
                pdf_doc.close()
                return {"tables": tables, "total": len(tables), "engine": "pymupdf"}
            except Exception as e:
                logger.warning("pdf_table_extraction_failed_pymupdf", error=str(e))

        return {"tables": [], "total": 0, "error": "No table extraction engine available"}

    @staticmethod
    async def ocr_pdf(
        user_id: UUID,
        pdf_id: UUID,
        session: AsyncSession,
    ) -> Optional[dict]:
        """OCR a scanned PDF to extract text from images."""
        doc = await session.get(PDFDocument, pdf_id)
        if not doc or doc.user_id != user_id or doc.is_deleted:
            return None

        if not HAS_TESSERACT:
            return {"text": "", "error": "OCR not available. Install pytesseract and Tesseract-OCR."}

        if not doc.file_path or not os.path.exists(doc.file_path):
            return {"text": "", "error": "PDF file not found on disk"}

        if not HAS_PYMUPDF:
            return {"text": "", "error": "PyMuPDF required for OCR (page rendering). Install PyMuPDF."}

        try:
            pdf_doc = fitz.open(doc.file_path)
            ocr_text = ""
            ocr_pages = []

            for i in range(len(pdf_doc)):
                page = pdf_doc[i]
                # Render page as image at 300 DPI
                mat = fitz.Matrix(300 / 72, 300 / 72)
                pix = page.get_pixmap(matrix=mat)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                page_text = pytesseract.image_to_string(img)
                ocr_pages.append({"page_number": i + 1, "text": page_text})
                ocr_text += page_text + "\n\n"

            pdf_doc.close()

            # Update document with OCR text if it was empty
            if not doc.text_content or len(doc.text_content.strip()) < 50:
                doc.text_content = ocr_text.strip()
                doc.pages_json = json.dumps(ocr_pages, ensure_ascii=False)
                doc.updated_at = datetime.now(UTC)
                session.add(doc)
                await session.commit()

            logger.info("pdf_ocr_completed", pdf_id=str(pdf_id), pages=len(ocr_pages))
            return {"text": ocr_text.strip(), "pages": ocr_pages, "total_pages": len(ocr_pages)}

        except Exception as e:
            logger.error("pdf_ocr_failed", error=str(e))
            return {"text": "", "error": str(e)[:500]}

    # ------------------------------------------------------------------
    # Status helpers
    # ------------------------------------------------------------------

    @staticmethod
    def get_parser_status() -> dict:
        """Return which PDF parsing engines are available."""
        return {
            "pymupdf": HAS_PYMUPDF,
            "pdfplumber": HAS_PDFPLUMBER,
            "tesseract_ocr": HAS_TESSERACT,
            "preferred_engine": "pymupdf" if HAS_PYMUPDF else ("pdfplumber" if HAS_PDFPLUMBER else "none"),
        }
