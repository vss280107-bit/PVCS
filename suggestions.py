from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.models import PromptSuggestion, PromptVersion, Prompt, ActivityLog, User
from schemas.schemas import SuggestionRequest, SuggestionResponse, ApplySuggestion
from ml.analyzer import generate_suggestions, compute_quality_score, compute_sentiment, tokenize
from auth.auth import get_current_user

router = APIRouter()


@router.post("/generate", response_model=List[SuggestionResponse])
def generate(payload: SuggestionRequest, db: Session = Depends(get_db), cu: User = Depends(get_current_user)):
    p = db.query(Prompt).filter(Prompt.id == payload.prompt_id, Prompt.user_id == cu.id).first()
    if not p: raise HTTPException(404, "Prompt not found")

    version = (
        db.query(PromptVersion).filter(PromptVersion.id == payload.version_id).first()
        if payload.version_id else
        db.query(PromptVersion).filter(PromptVersion.prompt_id == payload.prompt_id, PromptVersion.is_active == True).first()
    )
    if not version: raise HTTPException(404, "No active version found")

    suggestions_data = generate_suggestions(version.content, payload.suggestion_types)
    created = []
    for s in suggestions_data:
        obj = PromptSuggestion(
            prompt_id=payload.prompt_id, version_id=version.id,
            suggestion_type=s["suggestion_type"],
            original_text=s["original_text"], suggested_text=s["suggested_text"],
            reasoning=s["reasoning"], confidence_score=s["confidence_score"],
        )
        db.add(obj); created.append(obj)

    db.add(ActivityLog(user_id=cu.id, action="generate_suggestions", entity="prompt", entity_id=payload.prompt_id))
    db.commit()
    for s in created: db.refresh(s)
    return created


@router.get("/{pid}", response_model=List[SuggestionResponse])
def list_suggestions(pid: int, db: Session = Depends(get_db), cu: User = Depends(get_current_user)):
    p = db.query(Prompt).filter(Prompt.id == pid, Prompt.user_id == cu.id).first()
    if not p: raise HTTPException(404, "Prompt not found")
    return db.query(PromptSuggestion).filter(PromptSuggestion.prompt_id == pid).order_by(PromptSuggestion.created_at.desc()).all()


@router.post("/apply")
def apply(payload: ApplySuggestion, db: Session = Depends(get_db), cu: User = Depends(get_current_user)):
    s = db.query(PromptSuggestion).filter(PromptSuggestion.id == payload.suggestion_id).first()
    if not s: raise HTTPException(404, "Suggestion not found")

    p = db.query(Prompt).filter(Prompt.id == s.prompt_id, Prompt.user_id == cu.id).first()
    if not p: raise HTTPException(403, "Not authorized")

    s.is_applied = True
    db.query(PromptVersion).filter(PromptVersion.prompt_id == s.prompt_id, PromptVersion.is_active == True).update({"is_active": False})
    count = db.query(PromptVersion).filter(PromptVersion.prompt_id == s.prompt_id).count()
    overall, clarity, spec = compute_quality_score(s.suggested_text)
    new_v = PromptVersion(
        prompt_id=s.prompt_id, version_number=count + 1,
        content=s.suggested_text, commit_message=payload.commit_message or f"Applied {s.suggestion_type} suggestion",
        quality_score=overall, clarity_score=clarity, specificity_score=spec,
        token_count=len(tokenize(s.suggested_text)),
        sentiment=compute_sentiment(s.suggested_text), is_active=True,
    )
    db.add(new_v)
    db.add(ActivityLog(user_id=cu.id, action="apply_suggestion", entity="prompt", entity_id=s.prompt_id))
    db.commit(); db.refresh(new_v)
    return {"message": "Applied", "new_version_number": new_v.version_number, "quality_score": overall}


@router.delete("/{sid}")
def delete_suggestion(sid: int, db: Session = Depends(get_db), cu: User = Depends(get_current_user)):
    s = db.query(PromptSuggestion).filter(PromptSuggestion.id == sid).first()
    if not s: raise HTTPException(404)
    db.delete(s); db.commit()
    return {"message": "Deleted"}
