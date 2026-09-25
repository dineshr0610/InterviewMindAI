"""
Utility for extracting and cleaning text from PDF resumes.
"""

from __future__ import annotations

import io
import re
from typing import Optional


MAX_RESUME_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
}


def extract_text_from_file(file_content: bytes, filename: Optional[str] = None) -> Optional[str]:
    """
    Extract text from PDF, DOCX, or text file bytes.
    Returns cleaned text or None if extraction fails.
    """
    try:
        from app.resume_processing.parser import parse_resume_bytes

        parsed = parse_resume_bytes(file_content, filename=filename)
        return parsed.cleaned_text if parsed and parsed.cleaned_text.strip() else None
    except Exception:
        return extract_text_from_pdf(file_content)


def extract_text_from_pdf(file_content: bytes) -> Optional[str]:
    """
    Extract text from PDF bytes.
    Returns cleaned text or None if extraction fails.
    """
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(file_content))
        pages = []
        for page in reader.pages:
            try:
                text = page.extract_text() or ""
            except Exception:
                text = ""
            if text:
                pages.append(text)

        raw = "\n".join(pages)
        if not raw.strip():
            return None
        return clean_resume_text(raw)
    except Exception:
        return None


def clean_resume_text(text: str) -> str:
    """
    Clean extracted resume text while preserving useful content.
    """
    text = re.sub(r'\x00', '', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'^\s*\n', '', text, flags=re.MULTILINE)
    text = text.strip()
    return text


def sanitize_resume_for_prompt(text: str) -> str:
    """
    Sanitize resume text before inserting into an LLM prompt.
    Removes potential injection patterns.
    """
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
    text = text.strip()
    if len(text) > 8000:
        text = text[:8000]
    return text
