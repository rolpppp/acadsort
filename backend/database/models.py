"""
database/models.py — AcadSort SQLModel table definitions
Matches the finalized schema from the MVP plan exactly.
"""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
import json


# ── Enums as string literals (SQLite-friendly) ───────────────

class FileStatus:
    AUTO_MOVED  = "auto_moved"
    PENDING     = "pending"
    CONFIRMED   = "confirmed"
    REJECTED    = "rejected"

class MaterialType:
    LECTURE     = "lecture"
    ASSIGNMENT  = "assignment"
    READING     = "reading"
    EXAM        = "exam"
    LAB         = "lab"
    OTHER       = "other"

class OrganizationStyle:
    WEEK        = "week"
    TYPE        = "type"

class ExemplarSource:
    SEED        = "seed"
    CORRECTION  = "correction"
    SYLLABUS    = "syllabus"


# ── Tables ───────────────────────────────────────────────────

class UserSettings(SQLModel, table=True):
    __tablename__ = "user_settings"

    id: Optional[int]           = Field(default=None, primary_key=True)
    semester_name: str          = Field(index=True)         # e.g. "1st Sem AY 2026-2027"
    organization_style: str     = Field(default=OrganizationStyle.WEEK)
    downloads_path: str         = Field(default="")
    confidence_auto: float      = Field(default=0.90)
    confidence_suggest: float   = Field(default=0.70)
    is_active: bool             = Field(default=True)       # One active semester at a time
    created_at: datetime        = Field(default_factory=datetime.utcnow)
    updated_at: datetime        = Field(default_factory=datetime.utcnow)


class Course(SQLModel, table=True):
    __tablename__ = "courses"

    id: Optional[int]           = Field(default=None, primary_key=True)
    course_code: str            = Field(index=True)         # e.g. "CMSC 127"
    course_name: str            = Field(default="")
    instructor: str             = Field(default="")
    syllabus_text: Optional[str]= Field(default=None)       # Pasted syllabus text
    keywords_json: str          = Field(default="[]")       # JSON-encoded list of strings
    semester_id: int            = Field(foreign_key="user_settings.id")
    created_at: datetime        = Field(default_factory=datetime.utcnow)

    @property
    def keywords(self) -> list[str]:
        return json.loads(self.keywords_json)

    @keywords.setter
    def keywords(self, value: list[str]):
        self.keywords_json = json.dumps(value)


class FileRecord(SQLModel, table=True):
    __tablename__ = "files"

    id: Optional[int]           = Field(default=None, primary_key=True)
    original_name: str          = Field(index=True)
    new_name: Optional[str]     = Field(default=None)
    semester_id: Optional[int]  = Field(default=None, foreign_key="user_settings.id")
    detected_course: Optional[str] = Field(default=None, index=True)
    material_type: str          = Field(default=MaterialType.OTHER)
    week_number: Optional[int]  = Field(default=None)
    confidence: float           = Field(default=0.0)
    status: str                 = Field(default=FileStatus.PENDING, index=True)
    original_path: str          = Field(default="")
    moved_path: Optional[str]   = Field(default=None)
    extraction_snippet: Optional[str] = Field(default=None)  # First 500 chars used for classification
    created_at: datetime        = Field(default_factory=datetime.utcnow)
    updated_at: datetime        = Field(default_factory=datetime.utcnow)


class CorrectionHistory(SQLModel, table=True):
    __tablename__ = "correction_history"

    id: Optional[int]           = Field(default=None, primary_key=True)
    file_id: int                = Field(foreign_key="files.id")
    predicted_course: Optional[str]  = Field(default=None)
    corrected_course: Optional[str]  = Field(default=None)
    predicted_type: Optional[str]    = Field(default=None)
    corrected_type: Optional[str]    = Field(default=None)
    created_at: datetime        = Field(default_factory=datetime.utcnow)


class EmbeddingExemplar(SQLModel, table=True):
    __tablename__ = "embedding_exemplars"

    id: Optional[int]           = Field(default=None, primary_key=True)
    course_code: str            = Field(index=True)         # e.g. "CMSC 127"
    text_sample: str                                         # Original text snippet
    embedding_data: bytes                                    # Serialized numpy array
    source: str                 = Field(default=ExemplarSource.SEED)  # seed, correction, syllabus
    created_at: datetime        = Field(default_factory=datetime.utcnow)


class WatchFolder(SQLModel, table=True):
    __tablename__ = "watch_folders"

    id: Optional[int]           = Field(default=None, primary_key=True)
    semester_id: int            = Field(foreign_key="user_settings.id", index=True)
    path: str                   = Field(index=True)         # e.g. "~/Downloads"
    enabled: bool               = Field(default=True)
    created_at: datetime        = Field(default_factory=datetime.utcnow)
    updated_at: datetime        = Field(default_factory=datetime.utcnow)


class Session(SQLModel, table=True):
    __tablename__ = "sessions"

    id: str                     = Field(default="", primary_key=True)  # UUID string
    created_at: datetime        = Field(default_factory=datetime.utcnow, index=True)
    last_activity: datetime     = Field(default_factory=datetime.utcnow)
    semester_id: Optional[int]  = Field(default=None, foreign_key="user_settings.id")
    metadata_json: str          = Field(default="{}")       # JSON-encoded session metadata
