from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import prompts, versions, suggestions, analytics, auth

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="PromptFlow API",
    description="AI Prompt Version Control System",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:3000",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,        prefix="/api/auth",        tags=["Auth"])
app.include_router(prompts.router,     prefix="/api/prompts",     tags=["Prompts"])
app.include_router(versions.router,    prefix="/api/versions",    tags=["Versions"])
app.include_router(suggestions.router, prefix="/api/suggestions", tags=["Suggestions"])
app.include_router(analytics.router,   prefix="/api/analytics",   tags=["Analytics"])

@app.get("/")
def root():
    return {"message": "PromptFlow API v2.0", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "healthy"}
