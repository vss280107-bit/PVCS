from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models.models import Prompt, PromptVersion, PromptSuggestion, ActivityLog, User
from auth.auth import get_current_user

router = APIRouter()


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), cu: User = Depends(get_current_user)):
    uid = cu.id

    total_prompts    = db.query(Prompt).filter(Prompt.user_id == uid, Prompt.is_archived == False).count()
    total_versions   = db.query(PromptVersion).join(Prompt).filter(Prompt.user_id == uid).count()
    total_suggestions= db.query(PromptSuggestion).join(Prompt).filter(Prompt.user_id == uid).count()
    applied          = db.query(PromptSuggestion).join(Prompt).filter(Prompt.user_id == uid, PromptSuggestion.is_applied == True).count()

    avg_q = db.query(func.avg(PromptVersion.quality_score)).join(Prompt).filter(Prompt.user_id == uid).scalar()

    cats = db.query(Prompt.category, func.count(Prompt.id)).filter(Prompt.user_id == uid).group_by(Prompt.category).all()
    cat_dist = {r[0] or "general": r[1] for r in cats}

    recent_v = (db.query(PromptVersion).join(Prompt).filter(Prompt.user_id == uid)
                .order_by(PromptVersion.created_at.desc()).limit(12).all())
    quality_timeline = [{"v": v.version_number, "q": v.quality_score,
                         "t": v.created_at.isoformat() if v.created_at else None} for v in reversed(recent_v)]

    top = (db.query(Prompt, func.count(PromptVersion.id).label("vc"))
           .join(PromptVersion, isouter=True).filter(Prompt.user_id == uid)
           .group_by(Prompt.id).order_by(func.count(PromptVersion.id).desc()).limit(5).all())

    activity = (db.query(ActivityLog).filter(ActivityLog.user_id == uid)
                .order_by(ActivityLog.created_at.desc()).limit(10).all())

    return {
        "total_prompts": total_prompts,
        "total_versions": total_versions,
        "total_suggestions": total_suggestions,
        "applied_suggestions": applied,
        "avg_quality_score": round(float(avg_q), 3) if avg_q else 0.0,
        "category_distribution": cat_dist,
        "quality_timeline": quality_timeline,
        "top_prompts": [{"id": p.id, "title": p.title, "versions": vc} for p, vc in top],
        "recent_activity": [{"action": a.action, "entity": a.entity,
                              "created_at": a.created_at.isoformat()} for a in activity],
    }
