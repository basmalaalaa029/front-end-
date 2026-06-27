"""
analysis.parsing.file_parsing — Resume file parsing (PDF, DOCX, TXT).
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import List, Union

try:
    import pdfplumber  # noqa: F401
    _PDFPLUMBER_AVAILABLE = True
except ImportError:
    _PDFPLUMBER_AVAILABLE = False


def _score_extraction(text: str) -> int:
    """Prefer extractions with more words and recognizable CV section keywords."""
    if not text or not text.strip():
        return 0

    score = min(len(text.split()), 800)
    lower = text.lower()
    for kw in ("experience", "education", "skills", "summary", "project"):
        if kw in lower:
            score += 40

    score -= text.count("\ufffd") * 15
    score -= sum(1 for ln in text.splitlines() if len(ln) > 220) * 25
    score -= sum(1 for ln in text.splitlines() if len(ln.split()) == 1 and len(ln) > 30) * 5
    return score


def _pick_best(candidates: List[str]) -> str:
    nonempty = [c for c in candidates if c and c.strip()]
    if not nonempty:
        return ""
    return max(nonempty, key=lambda t: (len(t.split()), _score_extraction(t)))


def _extract_pdf_pdfplumber(file_bytes: bytes) -> str:
    import pdfplumber

    pages: List[str] = []
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            words = page.extract_words(x_tolerance=3, y_tolerance=3, keep_blank_chars=False)
            if words:
                lines_map: dict[float, list] = {}
                for word in words:
                    y = round(word["top"], 1)
                    lines_map.setdefault(y, []).append(word)
                rebuilt: List[str] = []
                for y in sorted(lines_map):
                    row = sorted(lines_map[y], key=lambda w: w["x0"])
                    rebuilt.append(" ".join(w["text"] for w in row))
                pages.append("\n".join(rebuilt))
                continue

            text = page.extract_text(x_tolerance=2, y_tolerance=3) or ""
            if text.strip():
                pages.append(text)

    return "\n\n".join(pages)


def _extract_pdf_pypdf(file_bytes: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(file_bytes))
    return "\n\n".join(pg.extract_text() or "" for pg in reader.pages)


def _extract_pdf_pymupdf(file_bytes: bytes) -> str:
    import fitz  # type: ignore[import-untyped]

    doc = fitz.open(stream=file_bytes, filetype="pdf")
    try:
        return "\n\n".join(page.get_text("text") or "" for page in doc)
    finally:
        doc.close()


def _extract_pdf_bytes(file_bytes: bytes) -> str:
    candidates: List[str] = []

    if _PDFPLUMBER_AVAILABLE:
        try:
            candidates.append(_extract_pdf_pdfplumber(file_bytes))
        except Exception:
            pass

    try:
        candidates.append(_extract_pdf_pypdf(file_bytes))
    except Exception:
        pass

    try:
        candidates.append(_extract_pdf_pymupdf(file_bytes))
    except ImportError:
        pass
    except Exception:
        pass

    best = _pick_best(candidates)
    if not best:
        raise ValueError("Could not extract text from PDF — the file may be scanned/image-only.")
    return best


def parse_resume_bytes(file_bytes: bytes, filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        if not _PDFPLUMBER_AVAILABLE:
            try:
                return _extract_pdf_pypdf(file_bytes)
            except ImportError as e:
                raise ImportError("PDF parsing requires pdfplumber or pypdf") from e
        return _extract_pdf_bytes(file_bytes)
    if ext in (".docx", ".doc"):
        try:
            import docx

            paras = [p.text.strip() for p in docx.Document(BytesIO(file_bytes)).paragraphs if p.text.strip()]
            return "\n".join(paras)
        except ImportError as e:
            raise ImportError("DOCX parsing requires python-docx") from e
    if ext == ".txt":
        return file_bytes.decode("utf-8", errors="ignore")
    raise ValueError(f"Unsupported file type: '{ext}'. Supported: .pdf, .docx, .txt")


def parse_resume_file(path: Union[str, Path]) -> str:
    path = Path(path)
    return parse_resume_bytes(path.read_bytes(), path.name)
