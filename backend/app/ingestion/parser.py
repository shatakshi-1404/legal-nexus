"""PDF / DOCX text extraction with OCR fallback for scanned pages."""
from dataclasses import dataclass


@dataclass
class PageText:
    page: int
    text: str
    ocr: bool = False


def parse_pdf(path: str, min_chars: int = 25) -> list[PageText]:
    import fitz  # PyMuPDF
    pages: list[PageText] = []
    with fitz.open(path) as pdf:
        for i, page in enumerate(pdf, start=1):
            text = page.get_text("text").strip()
            ocr = False
            if len(text) < min_chars:  # likely scanned -> OCR
                text, ocr = _ocr_page(page), True
            pages.append(PageText(i, text, ocr))
    return pages


def _ocr_page(page) -> str:
    import pytesseract
    from PIL import Image
    pix = page.get_pixmap(dpi=200)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    return pytesseract.image_to_string(img).strip()


def parse_docx(path: str) -> list[PageText]:
    """DOCX has no fixed pagination; the whole file is treated as page 1."""
    from docx import Document
    d = Document(path)
    parts = [p.text for p in d.paragraphs if p.text.strip()]
    for t in d.tables:
        for row in t.rows:
            parts.append(" | ".join(c.text.strip() for c in row.cells))
    return [PageText(1, "\n".join(parts))]


def parse_file(path: str, file_type: str) -> list[PageText]:
    return parse_pdf(path) if file_type == "pdf" else parse_docx(path)
