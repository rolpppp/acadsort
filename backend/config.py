"""
config.py — AcadSort backend configuration
All settings are loaded from environment variables or .env file.
"""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── App ──────────────────────────────────────────────────
    app_name: str = "AcadSort"
    app_version: str = "0.1.0"
    debug: bool = False

    # ── Server ───────────────────────────────────────────────
    host: str = "127.0.0.1"
    port: int = 8765                        # Fixed port; Tauri sidecar connects here

    # ── Paths ─────────────────────────────────────────────────
    project_root: Path = Path(__file__).parent.parent
    data_dir: Path = project_root / "data"
    models_dir: Path = project_root / "models"
    db_path: Path = data_dir / "acadsort.db"

    # ── Embedding model ───────────────────────────────────────
    embedding_model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"
    embedding_cache_dir: Path = models_dir / "embeddings"
    embedding_batch_size: int = 32

    # ── LLM (Ollama) ─────────────────────────────────────────
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "smollm2:1.7b"
    ollama_timeout: int = 30                # Seconds; prevents blocking on slow hardware
    ollama_enabled: bool = True             # Set False to skip LLM fallback entirely

    # ── Classification thresholds ────────────────────────────
    confidence_auto_move: float = 0.90      # ≥ this → auto-move
    confidence_suggest: float = 0.70        # ≥ this → suggest + confirm
                                            # < suggest → review queue

    # ── File processing ───────────────────────────────────────
    extraction_max_chars: int = 2000        # Max chars extracted per file for classification
    max_file_size_mb: int = 100             # Max file size to process (prevent OOM)
    watcher_debounce_seconds: float = 2.0   # Wait after file event before processing
    undo_grace_period_seconds: int = 30     # Window to undo an auto-move

    # ── File organization ──────────────────────────────────────
    organization_style: str = "week"        # "week" or "type" for folder structure
    
    # ── Downloads folder ───────────────────────────────────────
    downloads_path: Path = Path.home() / "Downloads"

    # ── Logging ───────────────────────────────────────────────
    log_level: str = "INFO"


settings = Settings()

# Ensure required directories exist at import time
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.models_dir.mkdir(parents=True, exist_ok=True)
