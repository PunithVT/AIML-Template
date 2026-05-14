"""PDF resume parser."""

import pdfplumber


def parse_pdf(file_path: str) -> str:
    """Extract raw text from a PDF resume."""
    text_blocks: list[str] = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_blocks.append(page_text)
    return "\n".join(text_blocks)
