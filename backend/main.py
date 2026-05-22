"""
main.py — AcadSort FastAPI backend entry point
Run with: cd backend && uvicorn main:app --host 127.0.0.1 --port 8765 --reload
"""
import sys
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import settings

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown logic.
    Tauri sidecar calls GET /health immediately after spawn — this
    must respond quickly so the frontend knows the backend is ready.
    """
    log.info("acadsort.backend.starting", version=settings.app_version)

    # ── Startup ──────────────────────────────────────────────
    from backend.database.engine import init_db
    from backend.database.seed import seed_database
    
    await init_db()
    log.info("database.initialized", path=str(settings.db_path))
    
    # Seed database with courses
    await seed_database()
    log.info("database.seeded", courses_count=63)

    from backend.classifier.embeddings import get_embedding_model
    get_embedding_model()               # Pre-loads model into memory on startup
    log.info("embedding_model.loaded", model=settings.embedding_model_name)

    log.info("acadsort.backend.ready", host=settings.host, port=settings.port)

    yield

    # ── Shutdown ──────────────────────────────────────────────
    log.info("acadsort.backend.shutting_down")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,   # Disable Swagger in production
    redoc_url=None,
)

# Allow Tauri frontend (localhost + tauri scheme) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:1420",        # Tauri dev server
        "http://localhost:5173",        # Vite dev server
        "tauri://localhost",            # Tauri production
        "https://tauri.localhost",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global Error Handlers ────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all error handler."""
    log.error("request_error", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content={"error": "Not found", "detail": f"Path {request.url.path} not found"},
    )


# ── Routers ────────────────────────────────────────────────────
from backend.api.health import router as health_router
from backend.api.files import router as files_router
from backend.api.courses import router as courses_router
from backend.api.settings import router as settings_router
from backend.api.queue import router as queue_router

app.include_router(health_router)
app.include_router(files_router)
app.include_router(courses_router)
app.include_router(settings_router)
app.include_router(queue_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
