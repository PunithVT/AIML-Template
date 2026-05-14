"""Enhanced resume ranking with multiple scoring dimensions."""

from dataclasses import dataclass
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

from src.parser.text_cleaner import clean_text
from src.features.resume_analyzer import ResumeAnalyzer, ResumeAnalysis


@dataclass
class RankingScoreBreakdown:
    """Detailed scoring breakdown for resume ranking."""
    skill_score: float
    language_score: float
    semantic_score: float
    keyword_score: float
    experience_score: float
    final_score: float
    recommendation: str


# Weights for composite scoring (from notebook)
DEFAULT_WEIGHTS = {
    "skill": 0.25,
    "language": 0.35,
    "semantic": 0.20,
    "keyword": 0.10,
    "experience": 0.10,
}


class ResumeRanker:
    """Rank resumes against a job description using multiple scoring methods."""
    
    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2", taxonomy_path: str = "config/skills_taxonomy.json"):
        """Initialize ranker with embedding model and skills taxonomy."""
        self.analyzer = ResumeAnalyzer(taxonomy_path)
        self.model = SentenceTransformer(embedding_model)
        self.tfidf = None
    
    def rank_resumes(
        self,
        resume_texts: list[str],
        jd_text: str,
        weights: dict[str, float] | None = None
    ) -> list[tuple[str, RankingScoreBreakdown]]:
        """
        Rank multiple resumes against a job description.
        
        Args:
            resume_texts: List of resume text contents
            jd_text: Job description text
            weights: Custom weights for scoring dimensions
        
        Returns:
            List of (resume_text, score_breakdown) sorted by final_score descending
        """
        if weights is None:
            weights = DEFAULT_WEIGHTS
        
        if not resume_texts:
            return []
        
        # Analyze resumes and JD
        resume_analyses = [
            self.analyzer.compare_with_jd(
                self.analyzer.analyze(text),
                jd_text
            )
            for text in resume_texts
        ]
        
        jd_analysis = self.analyzer.analyze(jd_text)
        clean_jd = jd_analysis.clean_text
        
        # Prepare texts for semantic and keyword scoring
        clean_resumes = [r.clean_text for r in resume_analyses]
        
        # Compute scores
        keyword_scores = self._compute_keyword_scores(clean_resumes, clean_jd)
        semantic_scores = self._compute_semantic_scores(clean_resumes, clean_jd)
        
        # Compile results
        results = []
        for i, resume_analysis in enumerate(resume_analyses):
            skill_score = self._calculate_overlap_score(
                resume_analysis.skills,
                jd_analysis.skills
            )
            language_score = self._calculate_overlap_score(
                resume_analysis.programming_languages,
                jd_analysis.programming_languages
            )
            experience_score = resume_analysis.experience_years
            semantic_score = semantic_scores[i]
            keyword_score = keyword_scores[i]
            
            final_score = (
                weights.get("skill", 0.0) * skill_score +
                weights.get("language", 0.0) * language_score +
                weights.get("semantic", 0.0) * semantic_score +
                weights.get("keyword", 0.0) * keyword_score +
                weights.get("experience", 0.0) * experience_score
            )
            
            # Generate recommendation
            if final_score >= 0.85:
                recommendation = "Excellent Match"
            elif final_score >= 0.70:
                recommendation = "Good Match"
            elif final_score >= 0.50:
                recommendation = "Moderate Match"
            else:
                recommendation = "Low Match"
            
            score_breakdown = RankingScoreBreakdown(
                skill_score=skill_score,
                language_score=language_score,
                semantic_score=semantic_score,
                keyword_score=keyword_score,
                experience_score=experience_score,
                final_score=final_score,
                recommendation=recommendation
            )
            
            results.append((resume_texts[i], score_breakdown))
        
        # Sort by final score descending
        results.sort(key=lambda x: x[1].final_score, reverse=True)
        return results
    
    def _calculate_overlap_score(self, resume_items: list[str], jd_items: list[str]) -> float:
        """Calculate overlap score between resume and JD items."""
        if not jd_items:
            return 0.0
        return len(set(resume_items) & set(jd_items)) / len(set(jd_items))
    
    def _compute_keyword_scores(self, resume_texts: list[str], jd_text: str) -> list[float]:
        """Compute TF-IDF based keyword similarity scores."""
        try:
            tfidf = TfidfVectorizer(stop_words="english", max_features=500)
            tfidf_matrix = tfidf.fit_transform(resume_texts + [jd_text])
            
            resume_vectors = tfidf_matrix[:-1]
            jd_vector = tfidf_matrix[-1]
            
            scores = cosine_similarity(resume_vectors, jd_vector).flatten()
            return scores.tolist()
        except Exception:
            # Fallback if TF-IDF fails
            return [0.0] * len(resume_texts)
    
    def _compute_semantic_scores(self, resume_texts: list[str], jd_text: str) -> list[float]:
        """Compute semantic similarity scores using embeddings."""
        try:
            resume_embeddings = self.model.encode(resume_texts, show_progress_bar=False)
            jd_embedding = self.model.encode([jd_text])
            
            scores = cosine_similarity(resume_embeddings, jd_embedding).flatten()
            return scores.tolist()
        except Exception:
            # Fallback if embedding fails
            return [0.0] * len(resume_texts)
