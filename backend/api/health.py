"""
api/health.py — Health check endpoint
Tauri sidecar polls GET /health until it gets 200 before showing the UI.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from backend.config import settings

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str
    ollama_available: bool


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Lightweight check. Does NOT ping Ollama (too slow for startup probe).
    Ollama availability is checked lazily on first LLM fallback call.
    """
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        ollama_available=settings.ollama_enabled,
    )
