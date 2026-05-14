"""Sentence-transformer based semantic similarity."""

from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer


_MODEL: SentenceTransformer | None = None


def _load_model(model_name: str | None = None) -> SentenceTransformer:
    global _MODEL
    if _MODEL is None:
        _MODEL = SentenceTransformer(model_name or "all-MiniLM-L6-v2")
    return _MODEL


def embedding_similarity(resume_text: str, jd_text: str, model_name: str | None = None) -> float:
    """Return semantic similarity in [0, 1] using sentence embeddings."""
    if not resume_text or not jd_text:
        return 0.0

    model = _load_model(model_name)
    embeddings = model.encode([resume_text, jd_text], convert_to_numpy=True, show_progress_bar=False)
    score = cosine_similarity([embeddings[0]], [embeddings[1]])[0, 0]
    return float(score)
