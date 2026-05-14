"""Resume feature extraction and analysis for ranking."""

import json
import re
from pathlib import Path
from dataclasses import dataclass

from src.parser.text_cleaner import clean_text


@dataclass
class ResumeAnalysis:
    """Extracted features from a resume."""
    text: str
    clean_text: str
    skills: list[str]
    programming_languages: list[str]
    experience_years: float
    matched_skills: list[str]
    matched_languages: list[str]
    missing_skills: list[str]
    missing_languages: list[str]


class ResumeAnalyzer:
    """Analyze resumes and extract relevant features."""
    
    def __init__(self, taxonomy_path: str = "config/skills_taxonomy.json"):
        """Initialize with skills taxonomy."""
        self.taxonomy_path = Path(taxonomy_path)
        self._load_skills_taxonomy()
    
    def _load_skills_taxonomy(self) -> None:
        """Load skills and languages from taxonomy."""
        if not self.taxonomy_path.exists():
            raise FileNotFoundError(f"Taxonomy not found: {self.taxonomy_path}")
        
        with open(self.taxonomy_path) as f:
            taxonomy = json.load(f)
        
        # Flatten all skills categories
        self.all_skills = []
        for category, items in taxonomy.items():
            if category != "programming_languages":
                self.all_skills.extend(items)
        
        self.programming_languages = taxonomy.get("programming_languages", [])
    
    def analyze(self, resume_text: str) -> ResumeAnalysis:
        """Analyze a single resume."""
        clean = clean_text(resume_text)
        
        # Extract features
        skills = self._extract_items(clean, self.all_skills)
        languages = self._extract_items(clean, self.programming_languages)
        experience_years = self._extract_experience_score(clean)
        
        return ResumeAnalysis(
            text=resume_text,
            clean_text=clean,
            skills=skills,
            programming_languages=languages,
            experience_years=experience_years,
            matched_skills=[],
            matched_languages=[],
            missing_skills=[],
            missing_languages=[]
        )
    
    def compare_with_jd(
        self, 
        resume_analysis: ResumeAnalysis,
        jd_text: str
    ) -> ResumeAnalysis:
        """Compare resume with job description."""
        clean_jd = clean_text(jd_text)
        
        jd_skills = self._extract_items(clean_jd, self.all_skills)
        jd_languages = self._extract_items(clean_jd, self.programming_languages)
        
        # Calculate matches and misses
        matched_skills = list(set(resume_analysis.skills) & set(jd_skills))
        missing_skills = list(set(jd_skills) - set(resume_analysis.skills))
        
        matched_languages = list(set(resume_analysis.programming_languages) & set(jd_languages))
        missing_languages = list(set(jd_languages) - set(resume_analysis.programming_languages))
        
        resume_analysis.matched_skills = matched_skills
        resume_analysis.missing_skills = missing_skills
        resume_analysis.matched_languages = matched_languages
        resume_analysis.missing_languages = missing_languages
        
        return resume_analysis
    
    @staticmethod
    def _extract_items(text: str, items: list[str]) -> list[str]:
        """Extract items found in text using word boundaries."""
        found = []
        for item in items:
            pattern = r"\b" + re.escape(item) + r"\b"
            if re.search(pattern, text, re.IGNORECASE):
                found.append(item.lower())
        return found
    
    @staticmethod
    def _extract_experience_score(text: str) -> float:
        """Extract years of experience from text."""
        patterns = [
            r"(\d+)\+?\s*years",
            r"(\d+)\+?\s*year",
            r"(\d+)\+?\s*yrs"
        ]
        
        years = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            years.extend([int(m) for m in matches])
        
        if not years:
            return 0.3
        
        max_years = max(years)
        
        if max_years >= 5:
            return 1.0
        elif max_years >= 3:
            return 0.8
        elif max_years >= 1:
            return 0.6
        else:
            return 0.3
    
    def calculate_skill_overlap(self, resume_skills: list[str], jd_skills: list[str]) -> float:
        """Calculate skill match percentage."""
        if not jd_skills:
            return 0.0
        return len(set(resume_skills) & set(jd_skills)) / len(set(jd_skills))
