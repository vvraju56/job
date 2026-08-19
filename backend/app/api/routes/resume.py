"""Resume tools and AI endpoints."""
from typing import Annotated

from fastapi import APIRouter, HTTPException, UploadFile, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbDep
from app.models.models import ResumeAnalysis
from app.schemas.schemas import (
    CoverLetterOut,
    CoverLetterRequest,
    InterviewPrepOut,
    InterviewPrepRequest,
    ResumeAnalysisOut,
    ResumeAnalyzeRequest,
    SkillGapOut,
    SkillGapRequest,
)
from app.services.ai_service import ai_service

router = APIRouter(prefix="/resume", tags=["resume-tools"])

MAX_UPLOAD_BYTES = 2 * 1024 * 1024


@router.post("/analyze", response_model=ResumeAnalysisOut)
async def analyze_resume(db: DbDep, user: CurrentUser, payload: ResumeAnalyzeRequest) -> ResumeAnalysisOut:
    result = await ai_service.analyze_resume(
        payload.resume_text,
        payload.target_role,
        payload.job_description,
        api_key=payload.api_key,
        provider=payload.provider,
    )
    db.add(
        ResumeAnalysis(
            user_id=user.id,
            ats_score=result["ats_score"],
            missing_keywords=result["missing_keywords"],
            suggestions=result["suggestions"],
            raw=result,
        )
    )
    await db.commit()
    return ResumeAnalysisOut(**result)


@router.post("/analyze/upload", response_model=ResumeAnalysisOut)
async def analyze_uploaded_resume(db: DbDep, user: CurrentUser, file: UploadFile) -> ResumeAnalysisOut:
    if file.size and file.size > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large")
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large")
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only UTF-8 text files are supported")
    return await analyze_resume(db, user, ResumeAnalyzeRequest(resume_text=text))


@router.post("/cover-letter", response_model=CoverLetterOut)
async def cover_letter(payload: CoverLetterRequest) -> CoverLetterOut:
    text = await ai_service.cover_letter(
        payload.resume_text,
        payload.job_title,
        payload.company_name,
        payload.job_description,
        api_key=payload.api_key,
        provider=payload.provider,
    )
    return CoverLetterOut(cover_letter=text)


@router.post("/skill-gap", response_model=SkillGapOut)
async def skill_gap(payload: SkillGapRequest) -> SkillGapOut:
    result = await ai_service.skill_gap(
        payload.resume_text,
        payload.target_role,
        api_key=payload.api_key,
        provider=payload.provider,
    )
    return SkillGapOut(**result)


@router.post("/interview-prep", response_model=InterviewPrepOut)
async def interview_prep(payload: InterviewPrepRequest) -> InterviewPrepOut:
    questions = await ai_service.interview_questions(
        payload.job_title,
        payload.job_description,
        payload.resume_text,
        api_key=payload.api_key,
        provider=payload.provider,
    )
    return InterviewPrepOut(questions=questions)


@router.get("/history", response_model=list[ResumeAnalysisOut])
async def analysis_history(db: DbDep, user: CurrentUser) -> list[ResumeAnalysisOut]:
    result = await db.execute(
        select(ResumeAnalysis).where(ResumeAnalysis.user_id == user.id).order_by(ResumeAnalysis.created_at.desc())
    )
    return [
        ResumeAnalysisOut(
            ats_score=a.ats_score,
            missing_keywords=a.missing_keywords,
            suggestions=a.suggestions,
            summary=a.raw.get("summary", ""),
        )
        for a in result.scalars().all()
    ]