from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models.models import Prompt, PromptVersion, ActivityLog, User
from schemas.schemas import PromptCreate, PromptUpdate, PromptResponse
from ml.analyzer import compute_quality_score, compute_sentiment, tokenize
from auth.auth import get_current_user

router = APIRouter()


def _enrich(p: Prompt, db: Session) -> dict:
    versions = db.query(PromptVersion).filter(PromptVersion.prompt_id == p.id).all()
    latest_v = max((v.version_number for v in versions), default=None)
    active_v = next((v for v in versions if v.is_active), None)
    d = {c.name: getattr(p, c.name) for c in p.__table__.columns}
    d["version_count"]  = len(versions)
    d["latest_version"] = latest_v
    d["latest_quality"] = active_v.quality_score if active_v else None
    return d


@router.post("/", response_model=PromptResponse)
def create_prompt(
    payload: PromptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prompt = Prompt(
        user_id=current_user.id,
        title=payload.title, description=payload.description,
        category=payload.category, tags=payload.tags, model=payload.model,
    )
    db.add(prompt); db.flush()

    overall, clarity, spec = compute_quality_score(payload.initial_content)
    v = PromptVersion(
        prompt_id=prompt.id, version_number=1,
        content=payload.initial_content, commit_message=payload.commit_message,
        quality_score=overall, clarity_score=clarity, specificity_score=spec,
        token_count=len(tokenize(payload.initial_content)),
        sentiment=compute_sentiment(payload.initial_content),
        model_used=payload.model, is_active=True,
    )
    db.add(v)
    db.add(ActivityLog(user_id=current_user.id, action="create_prompt",
                       entity="prompt", entity_id=prompt.id))
    db.commit(); db.refresh(prompt)
    return _enrich(prompt, db)


@router.get("/", response_model=List[PromptResponse])
def list_prompts(
    skip: int = Query(0, ge=0), limit: int = Query(50, le=200),
    category: Optional[str] = None, search: Optional[str] = None,
    archived: bool = False, favorite: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Prompt).filter(
        Prompt.user_id == current_user.id, Prompt.is_archived == archived)
    if category:  q = q.filter(Prompt.category == category)
    if search:    q = q.filter(Prompt.title.ilike(f"%{search}%"))
    if favorite is not None: q = q.filter(Prompt.is_favorite == favorite)
    return [_enrich(p, db) for p in q.order_by(Prompt.created_at.desc()).offset(skip).limit(limit)]


@router.get("/{pid}", response_model=PromptResponse)
def get_prompt(pid: int, db: Session = Depends(get_db), cu: User = Depends(get_current_user)):
    p = db.query(Prompt).filter(Prompt.id == pid, Prompt.user_id == cu.id).first()
    if not p: raise HTTPException(404, "Prompt not found")
    return _enrich(p, db)


@router.put("/{pid}", response_model=PromptResponse)
def update_prompt(pid: int, payload: PromptUpdate, db: Session = Depends(get_db), cu: User = Depends(get_current_user)):
    p = db.query(Prompt).filter(Prompt.id == pid, Prompt.user_id == cu.id).first()
    if not p: raise HTTPException(404, "Prompt not found")
    for k, v in payload.dict(exclude_unset=True).items(): setattr(p, k, v)
    db.add(ActivityLog(user_id=cu.id, action="update_prompt", entity="prompt", entity_id=pid))
    db.commit(); db.refresh(p)
    return _enrich(p, db)


@router.delete("/{pid}")
def delete_prompt(pid: int, db: Session = Depends(get_db), cu: User = Depends(get_current_user)):
    p = db.query(Prompt).filter(Prompt.id == pid, Prompt.user_id == cu.id).first()
    if not p: raise HTTPException(404, "Prompt not found")
    db.add(ActivityLog(user_id=cu.id, action="delete_prompt", entity="prompt", entity_id=pid))
    db.delete(p); db.commit()
    return {"message": "Deleted successfully"}
