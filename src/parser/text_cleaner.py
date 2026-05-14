"""Normalize extracted resume text."""

import re


def clean_text(text: str) -> str:
    """Normalize resume text for downstream extraction and matching."""
    text = text or ""
    text = re.sub(r"http\S+", " ", text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text)
    text = re.sub(r"[•·●◦▪]", "-", text)
    text = re.sub(r"[^a-zA-Z0-9\s+#.\-]", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip().lower()
