from __future__ import annotations

import logging
import re
import unicodedata
from pathlib import Path
from typing import Final

import aiofiles

from app.modules.rag.exceptions import RAGIndexingError, UnsupportedFileTypeError

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS: Final[frozenset[str]] = frozenset(
    {".pdf", ".md", ".txt", ".docx", ".html", ".htm", ".csv"}
)

MAX_FILE_SIZE_BYTES: Final[int] = 50 * 1024 * 1024
MIN_CONTENT_LENGTH: Final[int] = 50


class LoaderService:

    async def load(self, file_path: Path) -> str:
        """Đọc file và trả về plain text đã normalize."""
        file_path = Path(file_path)
        self._validate_file(file_path)

        ext = file_path.suffix.lower()
        logger.info("[LoaderService] Bắt đầu load '%s' (type=%s)", file_path.name, ext)

        try:
            if ext == ".pdf":
                raw_text = await self._load_pdf(file_path)
            elif ext in {".md"}:
                raw_text = await self._load_text_file(file_path)
            elif ext == ".txt":
                raw_text = await self._load_text_file(file_path)
            elif ext == ".docx":
                raw_text = await self._load_docx(file_path)
            elif ext in {".html", ".htm"}:
                raw_text = await self._load_html(file_path)
            elif ext == ".csv":
                raw_text = await self._load_text_file(file_path)
            else:
                raise UnsupportedFileTypeError(
                    message=f"Extension '{ext}' không được hỗ trợ",
                    details={"file": str(file_path), "supported": list(SUPPORTED_EXTENSIONS)},
                )

            normalized = self._normalize(raw_text)

            if len(normalized) < MIN_CONTENT_LENGTH:
                logger.warning(
                    "[LoaderService] File '%s' có ít nội dung sau extract (%d chars). "
                    "Có thể là PDF dạng ảnh cần OCR.",
                    file_path.name,
                    len(normalized),
                )

            logger.info(
                "[LoaderService] Load xong '%s': %d chars sau normalize.",
                file_path.name,
                len(normalized),
            )
            return normalized

        except (UnsupportedFileTypeError, RAGIndexingError):
            raise
        except Exception as exc:
            raise RAGIndexingError(
                message=f"Không thể đọc file '{file_path.name}'",
                details={"error": str(exc), "file": str(file_path), "type": ext},
            ) from exc

    def get_file_type(self, file_path: Path) -> str:
        """Trả về extension chuẩn hóa ."""
        return Path(file_path).suffix.lower().lstrip(".")

    def is_supported(self, file_path: Path) -> bool:
        """Kiểm tra file có extension được hỗ trợ không."""
        return Path(file_path).suffix.lower() in SUPPORTED_EXTENSIONS

    async def _load_pdf(self, file_path: Path) -> str:
        """Extract text từ PDF."""
        try:
            import fitz  # type: ignore[import-untyped]

            text = await self._load_pdf_with_pymupdf(file_path, fitz)
            if len(text.strip()) >= MIN_CONTENT_LENGTH:
                return text

            # PDF scan — thử OCR
            logger.info(
                "[LoaderService] '%s' có ít text (%d chars), thử OCR...",
                file_path.name,
                len(text.strip()),
            )
            ocr_text = await self._load_pdf_with_ocr(file_path, fitz)
            if ocr_text.strip():
                return ocr_text
            return text  # trả về text gốc dù rỗng, để downstream xử lý lỗi

        except ImportError:
            logger.debug(
                "[LoaderService] PyMuPDF không có sẵn, dùng pypdf cho '%s'.",
                file_path.name,
            )

        return await self._load_pdf_with_pypdf(file_path)

    async def _load_pdf_with_pymupdf(self, file_path: Path, fitz: Any) -> str:
        """Extract text dùng PyMuPDF trong threadpool."""
        import asyncio

        def _extract() -> str:
            doc = fitz.open(str(file_path))
            pages_text: list[str] = []
            for page_num, page in enumerate(doc):
                page_text = page.get_text("text")
                if page_text.strip():
                    pages_text.append(f"[Page {page_num + 1}]\n{page_text}")
            doc.close()
            return "\n\n".join(pages_text)

        return await asyncio.get_event_loop().run_in_executor(None, _extract)

    async def _load_pdf_with_ocr(self, file_path: Path, fitz: Any) -> str:
        """OCR fallback cho PDF dạng scan/ảnh."""
        import asyncio

        def _ocr() -> str:
            try:
                import pytesseract  # type: ignore[import-untyped]
                from PIL import Image  # type: ignore[import-untyped]
                import io as _io
            except ImportError as exc:
                logger.warning(
                    "[LoaderService] OCR không khả dụng (thiếu pytesseract/Pillow): %s", exc
                )
                return ""

            # Tesseract path trên Windows
            pytesseract.pytesseract.tesseract_cmd = (
                r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            )

            doc = fitz.open(str(file_path))
            pages_text: list[str] = []
            dpi = 200
            mat = fitz.Matrix(dpi / 72, dpi / 72)

            for page_num, page in enumerate(doc):
                pix = page.get_pixmap(matrix=mat)
                img = Image.open(_io.BytesIO(pix.tobytes("png")))
                try:
                    page_text = pytesseract.image_to_string(img, lang="vie+eng")
                except Exception:
                    # Fallback: OCR không có ngôn ngữ vie, thử eng
                    try:
                        page_text = pytesseract.image_to_string(img, lang="eng")
                    except Exception as ocr_exc:
                        logger.warning(
                            "[LoaderService] OCR trang %d thất bại: %s",
                            page_num + 1,
                            ocr_exc,
                        )
                        page_text = ""

                if page_text.strip():
                    pages_text.append(f"[Page {page_num + 1}]\n{page_text.strip()}")

            doc.close()
            result = "\n\n".join(pages_text)
            logger.info(
                "[LoaderService] OCR '%s': %d trang, %d chars.",
                file_path.name,
                len(pages_text),
                len(result),
            )
            return result

        return await asyncio.get_event_loop().run_in_executor(None, _ocr)

    async def _load_pdf_with_pypdf(self, file_path: Path) -> str:
        """Extract text dùng pypdf trong threadpool."""
        import asyncio

        def _extract() -> str:
            from pypdf import PdfReader  # type: ignore[import-untyped]

            reader = PdfReader(str(file_path))
            pages_text: list[str] = []
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                if page_text.strip():
                    pages_text.append(f"[Page {page_num + 1}]\n{page_text}")
            return "\n\n".join(pages_text)

        return await asyncio.get_event_loop().run_in_executor(None, _extract)

    async def _load_docx(self, file_path: Path) -> str:
        """Extract text từ .docx qua python-docx. Giữ heading style và tables."""
        try:
            import docx  # type: ignore[import-untyped]
        except ImportError as exc:
            raise UnsupportedFileTypeError(
                message="python-docx chưa được cài đặt. Chạy: pip install python-docx",
                details={"file": str(file_path), "missing_package": "python-docx"},
            ) from exc

        import asyncio

        def _extract() -> str:
            document = docx.Document(str(file_path))
            parts: list[str] = []

            for para in document.paragraphs:
                text = para.text.strip()
                if not text:
                    continue
                if para.style and para.style.name.startswith("Heading"):
                    level = para.style.name.replace("Heading ", "")
                    parts.append(f"{'#' * int(level) if level.isdigit() else '#'} {text}")
                else:
                    parts.append(text)

            for table in document.tables:
                rows: list[str] = []
                for row in table.rows:
                    cells = " | ".join(cell.text.strip() for cell in row.cells)
                    rows.append(cells)
                if rows:
                    parts.append("\n".join(rows))

            return "\n\n".join(parts)

        return await asyncio.get_event_loop().run_in_executor(None, _extract)

    async def _load_html(self, file_path: Path) -> str:
        """Parse HTML và extract text dùng BeautifulSoup."""
        raw_html = await self._read_file_bytes(file_path)

        from bs4 import BeautifulSoup  # type: ignore[import-untyped]

        soup = BeautifulSoup(raw_html, "lxml" if self._lxml_available() else "html.parser")

        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        return soup.get_text(separator="\n")

    async def _load_text_file(self, file_path: Path) -> str:
        """Đọc file text (md, txt, csv)."""
        try:
            async with aiofiles.open(file_path, encoding="utf-8") as f:
                return await f.read()
        except UnicodeDecodeError:
            logger.warning(
                "[LoaderService] File '%s' không phải UTF-8, thử latin-1.",
                file_path.name,
            )
            async with aiofiles.open(file_path, encoding="latin-1") as f:
                return await f.read()

    def _normalize(self, text: str) -> str:
        """Normalize plain text: Unicode NFC, xóa control chars, chuẩn hóa newlines."""
        text = unicodedata.normalize("NFC", text)
        text = re.sub(r"[^\S\n\t ]+", " ", text)
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\ufeff]", "", text)
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"\n{3,}", "\n\n", text)
        lines = [line.rstrip() for line in text.split("\n")]
        text = "\n".join(lines)
        return text.strip()

    def _validate_file(self, file_path: Path) -> None:
        """Validate file: tồn tại, là file, kích thước <= 50MB, extension hỗ trợ."""
        if not file_path.exists():
            raise RAGIndexingError(
                message=f"File không tồn tại: '{file_path}'",
                details={"file": str(file_path)},
            )

        if not file_path.is_file():
            raise RAGIndexingError(
                message=f"Path không phải là file: '{file_path}'",
                details={"file": str(file_path)},
            )

        size = file_path.stat().st_size
        if size > MAX_FILE_SIZE_BYTES:
            raise RAGIndexingError(
                message=(
                    f"File '{file_path.name}' quá lớn ({size / 1024 / 1024:.1f} MB). "
                    f"Giới hạn: {MAX_FILE_SIZE_BYTES // 1024 // 1024} MB."
                ),
                details={"file": str(file_path), "size_mb": round(size / 1024 / 1024, 2)},
            )

        ext = file_path.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise UnsupportedFileTypeError(
                message=(
                    f"Extension '{ext}' không được hỗ trợ. "
                    f"Chấp nhận: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
                ),
                details={
                    "file": str(file_path),
                    "extension": ext,
                    "supported": sorted(SUPPORTED_EXTENSIONS),
                },
            )

    async def _read_file_bytes(self, file_path: Path) -> bytes:
        """Đọc toàn bộ file dưới dạng bytes."""
        async with aiofiles.open(file_path, mode="rb") as f:
            return await f.read()

    @staticmethod
    def _lxml_available() -> bool:
        """Kiểm tra lxml có khả dụng không."""
        try:
            import lxml  # noqa: F401  # type: ignore[import-untyped]
            return True
        except ImportError:
            return False


from typing import Any  # noqa: E402


loader_service = LoaderService()
