"""Resume parsing and section structuring engine.

Supports PDF (pypdf) and DOCX (python-docx) files, raw text cleaning,
and robust section/item identification across flexible resume formats.
"""

from __future__ import annotations

import io
import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("interviewmind.resume_processing.parser")

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/plain",
}


@dataclass
class ResumeItem:
    """An individual entry inside a section (e.g., one project, one work experience role)."""
    title: str
    organization: Optional[str] = None
    date_range: Optional[str] = None
    description: str = ""
    bullet_points: List[str] = field(default_factory=list)
    raw_text: str = ""


@dataclass
class ResumeSection:
    """A detected logical section of a resume."""
    name: str  # canonical section name: skills, projects, experience, certifications, education, summary, etc.
    header_raw: str
    items: List[ResumeItem] = field(default_factory=list)
    raw_text: str = ""
    lines: List[str] = field(default_factory=list)


@dataclass
class ParsedResume:
    """Structured representation of a parsed resume."""
    raw_text: str
    cleaned_text: str
    sections: Dict[str, ResumeSection] = field(default_factory=dict)
    all_sentences: List[str] = field(default_factory=list)
    filename: Optional[str] = None


SECTION_PATTERNS = {
    "skills": [
        r"technical\s+skills?",
        r"core\s+competencies",
        r"skills?\s*(?:&|and)?\s*(?:abilities|tools|technologies)?",
        r"tech\s*stack",
        r"proficiencies",
        r"technologies",
        r"tools?\s*&?\s*frameworks?",
        r"programming\s+languages?",
    ],
    "projects": [
        r"(?:key|academic|personal|selected|technical)?\s*projects?",
        r"project\s+experience",
        r"featured\s+projects?",
        r"portfolio",
    ],
    "experience": [
        r"(?:work|professional|industry|relevant)?\s*experience",
        r"employment\s+history",
        r"internships?",
        r"work\s+history",
        r"career\s+history",
    ],
    "certifications": [
        r"certifications?",
        r"licenses?\s*(?:&|and)?\s*certifications?",
        r"courses?\s*(?:&|and)?\s*certificates?",
        r"credentials?",
    ],
    "education": [
        r"education(?:al\s+background)?",
        r"academic\s+history",
        r"qualifications?",
        r"degrees?",
    ],
    "summary": [
        r"(?:professional\s+)?summary",
        r"objective",
        r"profile",
        r"about\s+me",
    ],
    "achievements": [
        r"achievements?",
        r"awards?\s*(?:&|and)?\s*honors?",
        r"publications?",
        r"hackathons?",
    ],
}


def extract_text_from_pdf_bytes(content: bytes) -> str:
    """Extract all text pages from PDF bytes."""
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(content))
    pages_text: List[str] = []
    for page in reader.pages:
        try:
            txt = page.extract_text() or ""
            if txt:
                pages_text.append(txt)
        except Exception as exc:
            logger.debug("Failed extracting PDF page text: %s", exc)

    return "\n\n".join(pages_text)


def extract_text_from_docx_bytes(content: bytes) -> str:
    """Extract text from DOCX bytes including paragraphs and tables."""
    try:
        import docx

        doc = docx.Document(io.BytesIO(content))
        elements: List[str] = []

        for p in doc.paragraphs:
            text = p.text.strip()
            if text:
                elements.append(text)

        for table in doc.tables:
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_cells:
                    elements.append(" | ".join(row_cells))

        return "\n".join(elements)
    except Exception as exc:
        logger.error("Failed extracting DOCX text: %s", exc)
        return ""


def clean_text(text: str) -> str:
    """Clean extracted resume text while preserving structural paragraphs."""
    if not text:
        return ""
    # Remove null and non-printable characters
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    # Normalize bullet points and dashes
    cleaned = re.sub(r"[\u2022\u2023\u25E6\u2043\u2219\u00B7\u25AA\u25AB\u25CF]", "\n• ", cleaned)
    # Replace horizontal tabs and multiple spaces with single space
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    # Remove excessive blank lines
    cleaned = re.sub(r"\n\s*\n\s*\n+", "\n\n", cleaned)
    return cleaned.strip()


def _split_into_sentences(text: str) -> List[str]:
    """Split text into sentence and bullet-point chunks for evidence mapping."""
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    chunks: List[str] = []
    for line in lines:
        # Strip leading bullet indicators
        cleaned_line = re.sub(r"^[\-\*\u2022\d\.\)]\s*", "", line).strip()
        if not cleaned_line:
            continue
        # Split by periods followed by space or capitalized letter
        parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", cleaned_line)
        for part in parts:
            p = part.strip()
            if len(p) >= 5:
                chunks.append(p)
    return chunks


def parse_resume_bytes(content: bytes, filename: Optional[str] = None) -> ParsedResume:
    """Parse resume from raw bytes (PDF, DOCX, or text) into a structured ParsedResume object."""
    lower_fn = (filename or "").lower()
    raw_text = ""

    if lower_fn.endswith(".docx") or lower_fn.endswith(".doc"):
        raw_text = extract_text_from_docx_bytes(content)
    elif lower_fn.endswith(".pdf") or content[:4] == b"%PDF":
        raw_text = extract_text_from_pdf_bytes(content)
    else:
        # Try PDF first, then docx, then utf-8 text
        if content[:4] == b"%PDF":
            raw_text = extract_text_from_pdf_bytes(content)
        elif b"word/document.xml" in content:
            raw_text = extract_text_from_docx_bytes(content)
        else:
            try:
                raw_text = content.decode("utf-8")
            except UnicodeDecodeError:
                raw_text = content.decode("latin-1", errors="ignore")

    return parse_resume_text(raw_text, filename=filename)


def parse_resume_text(raw_text: str, filename: Optional[str] = None) -> ParsedResume:
    """Parse plain or cleaned text into structured sections and candidate items."""
    cleaned = clean_text(raw_text)
    sections = _extract_sections(cleaned)
    sentences = _split_into_sentences(cleaned)

    return ParsedResume(
        raw_text=raw_text,
        cleaned_text=cleaned,
        sections=sections,
        all_sentences=sentences,
        filename=filename,
    )


def _match_section_header(line: str) -> Optional[str]:
    """Identify if a line is a section heading and return canonical section name."""
    clean_line = line.strip().strip(":#-_=*[]()").strip()
    if not clean_line or len(clean_line) > 50:
        return None

    for canonical_name, patterns in SECTION_PATTERNS.items():
        for pat in patterns:
            if re.fullmatch(rf"(?i){pat}", clean_line):
                return canonical_name

    return None


def _extract_sections(text: str) -> Dict[str, ResumeSection]:
    """Segment resume text into structured sections with child items."""
    lines = text.split("\n")
    sections: Dict[str, ResumeSection] = {}
    current_sec_name = "summary"
    current_header = "Summary / Header"
    current_lines: List[str] = []

    def flush_section():
        nonlocal current_sec_name, current_header, current_lines
        if current_lines:
            sec_text = "\n".join(current_lines).strip()
            items = _parse_section_items(current_sec_name, current_lines)
            if current_sec_name not in sections:
                sections[current_sec_name] = ResumeSection(
                    name=current_sec_name,
                    header_raw=current_header,
                    items=items,
                    raw_text=sec_text,
                    lines=list(current_lines),
                )
            else:
                # Merge into existing section
                existing = sections[current_sec_name]
                existing.raw_text += "\n" + sec_text
                existing.lines.extend(current_lines)
                existing.items.extend(items)
        current_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        detected_sec = _match_section_header(stripped)
        if detected_sec:
            flush_section()
            current_sec_name = detected_sec
            current_header = stripped
        else:
            current_lines.append(stripped)

    flush_section()
    return sections


def _parse_section_items(section_name: str, lines: List[str]) -> List[ResumeItem]:
    """Parse section lines into individual project, experience, or skill blocks."""
    items: List[ResumeItem] = []
    if not lines:
        return items

    if section_name in ("projects", "experience"):
        current_title = ""
        current_bullets: List[str] = []
        current_text_lines: List[str] = []

        def flush_item():
            nonlocal current_title, current_bullets, current_text_lines
            if current_title or current_bullets or current_text_lines:
                title = current_title or (current_text_lines[0] if current_text_lines else "Project Entry")
                items.append(
                    ResumeItem(
                        title=title[:100],
                        description=" ".join(current_bullets or current_text_lines),
                        bullet_points=list(current_bullets),
                        raw_text="\n".join(current_text_lines),
                    )
                )
            current_title = ""
            current_bullets = []
            current_text_lines = []

        for line in lines:
            stripped = line.strip()
            is_bullet = stripped.startswith("•") or stripped.startswith("-") or stripped.startswith("*")
            cleaned_bullet = re.sub(r"^[\-\*\u2022\d\.\)]\s*", "", stripped).strip()

            # Check if this line looks like a project/role title (short, capitalized, no bullet)
            if not is_bullet and len(stripped) < 75 and not stripped.endswith(".") and ":" not in stripped:
                flush_item()
                current_title = stripped
                current_text_lines.append(stripped)
            else:
                if is_bullet or len(cleaned_bullet) >= 20:
                    current_bullets.append(cleaned_bullet)
                current_text_lines.append(stripped)

        flush_item()
    else:
        # Generic single item containing all lines
        full_text = "\n".join(lines)
        items.append(
            ResumeItem(
                title=section_name.title(),
                description=full_text,
                bullet_points=[re.sub(r"^[\-\*\u2022]\s*", "", l).strip() for l in lines],
                raw_text=full_text,
            )
        )

    return items
