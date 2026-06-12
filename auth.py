from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
from models.models import User, ActivityLog
from schemas.schemas import UserRegister, TokenResponse, UserResponse
from auth.auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter()


@router.post("/register", response_model=TokenResponse)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    print("calling register")
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        avatar_url=f"https://api.dicebear.com/7.x/initials/svg?seed={payload.username}",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log = ActivityLog(user_id=user.id, action="register", entity="user", entity_id=user.id)
    db.add(log); db.commit()

    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer",
            "user": {"id": user.id, "username": user.username, "email": user.email,
                     "full_name": user.full_name, "avatar_url": user.avatar_url}}


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    print("User login form")
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    user.last_login = datetime.utcnow()
    log = ActivityLog(user_id=user.id, action="login", entity="user", entity_id=user.id)
    db.add(log); db.commit()

    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer",
            "user": {"id": user.id, "username": user.username, "email": user.email,
                     "full_name": user.full_name, "avatar_url": user.avatar_url}}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/activity")
def get_activity(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logs = (
        db.query(ActivityLog)
        .filter(ActivityLog.user_id == current_user.id)
        .order_by(ActivityLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return [{"action": l.action, "entity": l.entity, "entity_id": l.entity_id,
             "created_at": l.created_at} for l in logs]
