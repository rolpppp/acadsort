"""
database/engine.py — SQLite engine and table initialization
"""
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from backend.config import settings

# Async engine for FastAPI endpoint use
async_engine = create_async_engine(
    f"sqlite+aiosqlite:///{settings.db_path}",
    echo=settings.debug,
    connect_args={"check_same_thread": False},
)

# Sync engine for startup/migration use
sync_engine = create_engine(
    f"sqlite:///{settings.db_path}",
    echo=settings.debug,
    connect_args={"check_same_thread": False},
)

AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


def _apply_schema_migrations() -> None:
    """Add columns introduced after initial releases (SQLite has no ALTER from ORM)."""
    inspector = inspect(sync_engine)
    if "files" not in inspector.get_table_names():
        return

    columns = {col["name"] for col in inspector.get_columns("files")}
    if "semester_id" not in columns:
        with sync_engine.connect() as conn:
            conn.execute(
                text(
                    "ALTER TABLE files ADD COLUMN semester_id INTEGER "
                    "REFERENCES user_settings(id)"
                )
            )
            conn.commit()


async def init_db():
    """Create all tables on startup if they don't exist."""
    from backend.database.models import (
        UserSettings, Course, FileRecord,
        CorrectionHistory, EmbeddingExemplar,
    )
    SQLModel.metadata.create_all(sync_engine)
    _apply_schema_migrations()


async def get_session() -> AsyncSession:
    """FastAPI dependency for async DB sessions."""
    async with AsyncSessionLocal() as session:
        yield session
