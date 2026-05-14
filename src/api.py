"""FastAPI REST server.

Run:
    uvicorn src.api:app --reload --port 8000
"""

import os
import shutil
import tempfile
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.features import extract_features
from src.parser import parse_resume
from src.ranking import score_candidate
from src.ranking.resume_ranker import ResumeRanker
from src.features.resume_analyzer import ResumeAnalyzer
from src.parser.pdf_parser import parse_pdf
from src.parser.docx_parser import parse_docx

app = FastAPI(
    title="Resume Ranker API",
    description="Parse resumes, extract features, score against job descriptions.",
    version="0.1.0",
)


class ScoreResponse(BaseModel):
    profile: dict
    score: dict


class RankingResult(BaseModel):
    """Individual ranking result."""
    rank: int
    resume_name: str
    final_score: float
    skill_score: float
    language_score: float
    semantic_score: float
    keyword_score: float
    experience_score: float
    matched_skills: list[str]
    missing_skills: list[str]
    matched_languages: list[str]
    missing_languages: list[str]
    recommendation: str


class RankingResponse(BaseModel):
    """Resume ranking response."""
    total_resumes: int
    results: list[RankingResult]


class BulkRankingRequest(BaseModel):
    """Bulk resume ranking request."""
    resume_texts: list[str]
    job_description: str


# Initialize ranker
ranker = ResumeRanker()
analyzer = ResumeAnalyzer()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/parse", summary="Parse a single resume into structured features")
async def parse_endpoint(file: UploadFile = File(...)) -> dict:
    suffix = Path(file.filename or "").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
    text = parse_resume(tmp_path)
    profile = extract_features(text)
    return asdict(profile)


@app.post("/score", response_model=ScoreResponse, summary="Score a resume against a JD")
async def score_endpoint(
    file: UploadFile = File(...),
    jd_text: str = Form(...),
) -> ScoreResponse:
    suffix = Path(file.filename or "").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
    profile = extract_features(parse_resume(tmp_path))
    score = score_candidate(profile, jd_text)
    return ScoreResponse(profile=asdict(profile), score=asdict(score))


@app.post("/rank-bulk", response_model=RankingResponse, summary="Rank multiple resumes against a JD")
async def rank_bulk_endpoint(request: BulkRankingRequest) -> RankingResponse:
    """
    Rank multiple resumes against a job description.
    
    Args:
        resume_texts: List of resume text contents
        job_description: Target job description
    
    Returns:
        Ranking results with scores and analysis
    """
    try:
        if not request.resume_texts or not request.job_description.strip():
            raise HTTPException(status_code=400, detail="Resume texts and job description required")
        
        # Rank resumes
        ranked = ranker.rank_resumes(request.resume_texts, request.job_description)
        
        # Format results
        results = []
        for rank, (resume_text, score) in enumerate(ranked, 1):
            resume_analysis = analyzer.compare_with_jd(
                analyzer.analyze(resume_text),
                request.job_description
            )
            
            result = RankingResult(
                rank=rank,
                resume_name=f"Resume {rank}",
                final_score=round(score.final_score * 100, 2),
                skill_score=round(score.skill_score * 100, 2),
                language_score=round(score.language_score * 100, 2),
                semantic_score=round(score.semantic_score * 100, 2),
                keyword_score=round(score.keyword_score * 100, 2),
                experience_score=round(score.experience_score * 100, 2),
                matched_skills=resume_analysis.matched_skills,
                missing_skills=resume_analysis.missing_skills,
                matched_languages=resume_analysis.matched_languages,
                missing_languages=resume_analysis.missing_languages,
                recommendation=score.recommendation
            )
            results.append(result)
        
        return RankingResponse(
            total_resumes=len(ranked),
            results=results
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rank-files", response_model=RankingResponse, summary="Rank uploaded resume files against a JD")
async def rank_files_endpoint(
    job_description: str = Form(...),
    files: list[UploadFile] = File(...)
) -> RankingResponse:
    """
    Rank uploaded resume files against a job description.
    
    Args:
        job_description: Target job description
        files: Resume files (PDF, DOCX, or TXT)
    
    Returns:
        Ranking results with scores and analysis
    """
    try:
        if not job_description.strip():
            raise HTTPException(status_code=400, detail="Job description is required")
        
        if not files:
            raise HTTPException(status_code=400, detail="At least one resume file is required")
        
        resume_texts = []
        resume_names = []
        
        for file in files:
            try:
                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename or "").suffix) as tmp:
                    content = await file.read()
                    tmp.write(content)
                    tmp_path = tmp.name
                
                # Extract text based on file type
                ext = Path(file.filename or "").suffix.lower()
                
                if ext == ".pdf":
                    text = parse_pdf(tmp_path)
                elif ext == ".docx":
                    text = parse_docx(tmp_path)
                elif ext == ".txt":
                    with open(tmp_path, "r", encoding="utf-8", errors="ignore") as f:
                        text = f.read()
                else:
                    os.unlink(tmp_path)
                    continue
                
                if text.strip():
                    resume_texts.append(text)
                    resume_names.append(file.filename or f"Resume_{len(resume_names)}")
                
                # Clean up temp file
                os.unlink(tmp_path)
            
            except Exception as e:
                return JSONResponse(
                    status_code=400,
                    content={"detail": f"Error processing file {file.filename}: {str(e)}"}
                )
        
        if not resume_texts:
            raise HTTPException(status_code=400, detail="No valid resume files could be processed")
        
        # Rank resumes
        ranked = ranker.rank_resumes(resume_texts, job_description)
        
        # Format results
        results = []
        for rank, (resume_text, score) in enumerate(ranked, 1):
            resume_analysis = analyzer.compare_with_jd(
                analyzer.analyze(resume_text),
                job_description
            )
            
            result = RankingResult(
                rank=rank,
                resume_name=resume_names[resume_texts.index(resume_text)],
                final_score=round(score.final_score * 100, 2),
                skill_score=round(score.skill_score * 100, 2),
                language_score=round(score.language_score * 100, 2),
                semantic_score=round(score.semantic_score * 100, 2),
                keyword_score=round(score.keyword_score * 100, 2),
                experience_score=round(score.experience_score * 100, 2),
                matched_skills=resume_analysis.matched_skills,
                missing_skills=resume_analysis.missing_skills,
                matched_languages=resume_analysis.matched_languages,
                missing_languages=resume_analysis.missing_languages,
                recommendation=score.recommendation
            )
            results.append(result)
        
        return RankingResponse(
            total_resumes=len(ranked),
            results=results
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
