from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.models import PromptVersion, Prompt, ActivityLog, User
from schemas.schemas import VersionCreate, VersionResponse
from ml.analyzer import compute_quality_score, compute_sentiment, tokenize, diff_summary
from auth.auth import get_current_user

router = APIRouter()


@router.post("/{pid}", response_model=VersionResponse)
def create_version(pid: int, payload: VersionCreate, db: Session = Depends(get_db), cu: User = Depends(get_current_user)):
    p = db.query(Prompt).filter(Prompt.id == pid, Prompt.user_id == cu.id).first()
    if not p: raise HTTPException(404, "Prompt not found")

    db.query(PromptVersion).filter(PromptVersion.prompt_id == pid, PromptVersion.is_active == True).update({"is_active": False})
    count = db.query(PromptVersion).filter(PromptVersion.prompt_id == pid).count()
    overall, clarity, spec = compute_quality_score(payload.content)
    v = PromptVersion(
        prompt_id=pid, version_number=count + 1,
        content=payload.content, commit_message=payload.commit_message,
        quality_score=overall, clarity_score=clarity, specificity_score=spec,
        token_count=len(tokenize(payload.content)),
        sentiment=compute_sentiment(payload.content),
        model_used=payload.model_used or p.model, is_active=True,
    )
    db.add(v)
    db.add(ActivityLog(user_id=cu.id, action="create_version", entity="prompt", entity_id=pid,
                       metadata={"version": count + 1, "quality": overall}))
    db.commit(); db.refresh(v)
    return v


@router.get("/{pid}", response_model=List[VersionResponse])
def list_versions(pid: int, db: Session = Depends(get_db), cu: User = Depends(get_current_user)):
    p = db.query(Prompt).filter(Prompt.id == pid, Prompt.user_id == cu.id).first()
    if not p: raise HTTPException(404, "Prompt not found")
    return db.query(PromptVersion).filter(PromptVersion.prompt_id == pid).order_by(PromptVersion.version_number.desc()).all()


@router.post("/{pid}/rollback/{vnum}", response_model=VersionResponse)
def rollback(pid: int, vnum: int, db: Session = Depends(get_db), cu: User = Depends(get_current_user)):
    p = db.query(Prompt).filter(Prompt.id == pid, Prompt.user_id == cu.id).first()
    if not p: raise HTTPException(404, "Prompt not found")
    target = db.query(PromptVersion).filter(PromptVersion.prompt_id == pid, PromptVersion.version_number == vnum).first()
    if not target: raise HTTPException(404, "Version not found")

    db.query(PromptVersion).filter(PromptVersion.prompt_id == pid).update({"is_active": False})
    count = db.query(PromptVersion).filter(PromptVersion.prompt_id == pid).count()
    overall, clarity, spec = compute_quality_score(target.content)
    new_v = PromptVersion(
        prompt_id=pid, version_number=count + 1,
        content=target.content, commit_message=f"Rollback to v{vnum}",
        quality_score=overall, clarity_score=clarity, specificity_score=spec,
        token_count=len(tokenize(target.content)),
        sentiment=compute_sentiment(target.content), model_used=target.model_used, is_active=True,
    )
    db.add(new_v)
    db.add(ActivityLog(user_id=cu.id, action="rollback", entity="prompt", entity_id=pid,
                       metadata={"from_version": vnum, "new_version": count + 1}))
    db.commit(); db.refresh(new_v)
    return new_v


@router.get("/{pid}/diff/{v1}/{v2}")
def compare(pid: int, v1: int, v2: int, db: Session = Depends(get_db), cu: User = Depends(get_current_user)):
    p = db.query(Prompt).filter(Prompt.id == pid, Prompt.user_id == cu.id).first()
    if not p: raise HTTPException(404, "Prompt not found")
    ver1 = db.query(PromptVersion).filter(PromptVersion.prompt_id == pid, PromptVersion.version_number == v1).first()
    ver2 = db.query(PromptVersion).filter(PromptVersion.prompt_id == pid, PromptVersion.version_number == v2).first()
    if not ver1 or not ver2: raise HTTPException(404, "Version not found")
    return {
        "version_a": {"number": ver1.version_number, "content": ver1.content, "quality": ver1.quality_score},
        "version_b": {"number": ver2.version_number, "content": ver2.content, "quality": ver2.quality_score},
        "diff": diff_summary(ver1.content, ver2.content),
    }
