from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any
from datetime import datetime


# ── Auth ──────────────────────────────────────────────────
class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    avatar_url: Optional[str]
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    class Config: from_attributes = True


# ── Prompt ────────────────────────────────────────────────
class PromptCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = "general"
    tags: Optional[List[str]] = []
    model: Optional[str] = "gpt-4"
    initial_content: str = Field(..., min_length=1)
    commit_message: Optional[str] = "Initial version"

class PromptUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    model: Optional[str] = None
    is_archived: Optional[bool] = None
    is_favorite: Optional[bool] = None

class PromptResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: Optional[str]
    category: Optional[str]
    tags: Optional[List[Any]]
    model: Optional[str]
    is_archived: bool
    is_favorite: bool
    created_at: datetime
    updated_at: Optional[datetime]
    version_count: Optional[int] = 0
    latest_version: Optional[int] = None
    latest_quality: Optional[float] = None
    class Config: from_attributes = True


# ── Version ───────────────────────────────────────────────
class VersionCreate(BaseModel):
    content: str = Field(..., min_length=1)
    commit_message: Optional[str] = "New version"
    model_used: Optional[str] = None

class VersionResponse(BaseModel):
    id: int
    prompt_id: int
    version_number: int
    content: str
    commit_message: Optional[str]
    quality_score: Optional[float]
    clarity_score: Optional[float]
    specificity_score: Optional[float]
    token_count: Optional[int]
    sentiment: Optional[str]
    model_used: Optional[str]
    is_active: bool
    created_at: datetime
    class Config: from_attributes = True


# ── Suggestion ────────────────────────────────────────────
class SuggestionRequest(BaseModel):
    prompt_id: int
    version_id: Optional[int] = None
    suggestion_types: Optional[List[str]] = ["clarity", "specificity", "structure", "tone"]

class SuggestionResponse(BaseModel):
    id: int
    prompt_id: int
    version_id: Optional[int]
    suggestion_type: str
    original_text: str
    suggested_text: str
    reasoning: Optional[str]
    confidence_score: Optional[float]
    is_applied: bool
    created_at: datetime
    class Config: from_attributes = True

class ApplySuggestion(BaseModel):
    suggestion_id: int
    commit_message: Optional[str] = "Applied AI suggestion"
