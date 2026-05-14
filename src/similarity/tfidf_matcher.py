"""TF-IDF cosine similarity between a resume and a job description."""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def tfidf_similarity(resume_text: str, jd_text: str) -> float:
    """Return a cosine-similarity score in [0, 1]."""
    if not resume_text or not jd_text:
        return 0.0

    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    matrix = vectorizer.fit_transform([resume_text, jd_text])
    score = cosine_similarity(matrix[0:1], matrix[1:2])[0, 0]
    return float(score)
