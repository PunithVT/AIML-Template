from dataclasses import dataclass, field

from src.features.contact_extractor import extract_contact
from src.features.education_extractor import extract_education
from src.features.experience_extractor import extract_experience
from src.features.skills_extractor import extract_skills


@dataclass
class CandidateProfile:
    raw_text: str
    contact: dict = field(default_factory=dict)
    skills: list[str] = field(default_factory=list)
    experience: list[dict] = field(default_factory=list)
    education: list[dict] = field(default_factory=list)
    total_experience_years: float = 0.0


def extract_features(text: str) -> CandidateProfile:
    """Run all feature extractors and return a structured profile."""
    experience = extract_experience(text)
    total_years = 0.0
    if experience:
        total_years = max(entry.get("years", 0.0) for entry in experience)

    return CandidateProfile(
        raw_text=text,
        contact=extract_contact(text),
        skills=extract_skills(text),
        experience=experience,
        education=extract_education(text),
        total_experience_years=total_years,
    )


__all__ = ["CandidateProfile", "extract_features"]
