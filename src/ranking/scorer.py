"""Composite candidate-vs-JD scorer."""

from dataclasses import dataclass

from src.features import CandidateProfile
from src.similarity import hybrid_similarity


@dataclass
class ScoreBreakdown:
    skills: float
    experience: float
    education: float
    semantic: float
    total: float


DEFAULT_WEIGHTS = {
    "skills": 0.45,
    "experience": 0.30,
    "education": 0.15,
    "semantic": 0.10,
}


def _normalize_skill_name(text: str) -> str:
    return text.strip().lower()


def score_candidate(
    profile: CandidateProfile,
    jd_text: str,
    jd_required_skills: list[str] | None = None,
    weights: dict[str, float] | None = None,
) -> ScoreBreakdown:
    """Compute a composite score in [0, 1]."""
    if weights is None:
        weights = DEFAULT_WEIGHTS

    resume_skills = { _normalize_skill_name(skill) for skill in profile.skills }
    jd_skills = { _normalize_skill_name(skill) for skill in (jd_required_skills or []) if skill }
    jd_lower = jd_text.lower()

    if not jd_skills and resume_skills:
        matching_skills = {skill for skill in resume_skills if skill in jd_lower}
    else:
        matching_skills = resume_skills & jd_skills

    skills_score = float(len(matching_skills) / len(jd_skills)) if jd_skills else float(len(matching_skills) / max(len(resume_skills), 1))
    experience_score = min(profile.total_experience_years / 5.0, 1.0)
    education_score = 1.0 if profile.education else 0.0
    semantic_score = hybrid_similarity(profile.raw_text, jd_text)

    total = (
        weights.get("skills", 0.0) * skills_score
        + weights.get("experience", 0.0) * experience_score
        + weights.get("education", 0.0) * education_score
        + weights.get("semantic", 0.0) * semantic_score
    )
    total = min(max(total, 0.0), 1.0)

    return ScoreBreakdown(
        skills=skills_score,
        experience=experience_score,
        education=education_score,
        semantic=semantic_score,
        total=total,
    )
