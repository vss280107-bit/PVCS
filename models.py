# database schema (data model layer) using ORM mapping with SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"
    id            = Column(Integer, primary_key=True, index=True)
    username      = Column(String(100), unique=True, nullable=False, index=True)
    email         = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name     = Column(String(255), nullable=True)
    avatar_url    = Column(String(500), nullable=True)
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    last_login    = Column(DateTime(timezone=True), nullable=True)

    prompts       = relationship("Prompt", back_populates="owner", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="user", cascade="all, delete-orphan")


class Prompt(Base):
    __tablename__ = "prompts"
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    title       = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category    = Column(String(100), default="general")
    tags        = Column(JSON, default=[])
    model       = Column(String(100), default="gpt-4")
    is_archived = Column(Boolean, default=False)
    is_favorite = Column(Boolean, default=False)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())

    owner       = relationship("User", back_populates="prompts")
    versions    = relationship("PromptVersion", back_populates="prompt", cascade="all, delete-orphan")
    suggestions = relationship("PromptSuggestion", back_populates="prompt", cascade="all, delete-orphan")


class PromptVersion(Base):
    __tablename__ = "prompt_versions"
    id               = Column(Integer, primary_key=True, index=True)
    prompt_id        = Column(Integer, ForeignKey("prompts.id"), nullable=False)
    version_number   = Column(Integer, nullable=False)
    content          = Column(Text, nullable=False)
    commit_message   = Column(String(500), nullable=True)
    quality_score    = Column(Float, nullable=True)
    clarity_score    = Column(Float, nullable=True)
    specificity_score= Column(Float, nullable=True)
    token_count      = Column(Integer, nullable=True)
    sentiment        = Column(String(50), nullable=True)
    model_used       = Column(String(100), nullable=True)
    is_active        = Column(Boolean, default=False)
    created_at       = Column(DateTime(timezone=True), server_default=func.now())

    prompt      = relationship("Prompt", back_populates="versions")


class PromptSuggestion(Base):
    __tablename__ = "prompt_suggestions"
    id               = Column(Integer, primary_key=True, index=True)
    prompt_id        = Column(Integer, ForeignKey("prompts.id"), nullable=False)
    version_id       = Column(Integer, ForeignKey("prompt_versions.id"), nullable=True)
    suggestion_type  = Column(String(100), nullable=False)
    original_text    = Column(Text, nullable=False)
    suggested_text   = Column(Text, nullable=False)
    reasoning        = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    is_applied       = Column(Boolean, default=False)
    created_at       = Column(DateTime(timezone=True), server_default=func.now())

    prompt = relationship("Prompt", back_populates="suggestions")


class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=True)
    action     = Column(String(100), nullable=False)
    entity     = Column(String(100), nullable=True)
    entity_id  = Column(Integer, nullable=True)
    meta_data   = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="activity_logs")
