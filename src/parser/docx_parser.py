"""DOCX resume parser."""

import docx


def parse_docx(file_path: str) -> str:
    """Extract raw text from a DOCX resume."""
    document = docx.Document(file_path)
    paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text]
    return "\n".join(paragraphs)
