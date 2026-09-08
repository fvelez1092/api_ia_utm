"""Configuración de la aplicación obtenida desde variables de entorno."""

from datetime import timedelta
from os import environ
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _as_bool(name: str, default: bool = False) -> bool:
    value = environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _read_key(value_name: str, path_name: str):
    """Lee una clave desde el entorno o desde una ruta externa al repositorio."""
    value = environ.get(value_name)
    if value:
        return value.replace("\\n", "\n")

    key_path = environ.get(path_name)
    if not key_path:
        return None
    resolved = Path(key_path).expanduser()
    if not resolved.is_absolute():
        resolved = BASE_DIR / resolved
    return resolved.read_text(encoding="utf-8")


def _project_path(value: str) -> str:
    resolved = Path(value).expanduser()
    if not resolved.is_absolute():
        resolved = BASE_DIR / resolved
    return str(resolved.resolve())


class Config:
    SECRET_KEY = environ.get("SECRET_KEY")
    PROPAGATE_EXCEPTIONS = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_ALGORITHM = environ.get("JWT_ALGORITHM", "RS256")
    JWT_SECRET_KEY = environ.get("JWT_SECRET_KEY", SECRET_KEY)
    JWT_PRIVATE_KEY = _read_key("JWT_PRIVATE_KEY", "JWT_PRIVATE_KEY_PATH")
    JWT_PUBLIC_KEY = _read_key("JWT_PUBLIC_KEY", "JWT_PUBLIC_KEY_PATH")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=int(environ.get("JWT_ACCESS_TOKEN_MINUTES", "60"))
    )

    CHROMA_PATH = _project_path(environ.get("CHROMA_PATH", "./chroma_db"))
    COLLECTION_NAME = environ.get("COLLECTION_NAME", "utm_documents")

    OLLAMA_HOST = environ.get("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL = environ.get("OLLAMA_MODEL", "deepseek-r1:8b")
    EMBEDDING_MODEL = environ.get("EMBEDDING_MODEL", "nomic-embed-text")
    RAG_MAX_CHARS = int(environ.get("RAG_MAX_CHARS", "8000"))
    RAG_SCORE_THRESHOLD = float(environ.get("RAG_SCORE_THRESHOLD", "0.8"))
    RAG_MAX_QUESTION_LENGTH = int(environ.get("RAG_MAX_QUESTION_LENGTH", "1000"))

    UPLOAD_FOLDER = _project_path(environ.get("UPLOAD_FOLDER", "./uploads"))
    ALLOWED_EXTENSIONS = {"pdf"}
    MAX_CONTENT_LENGTH = int(environ.get("MAX_UPLOAD_MB", "20")) * 1024 * 1024

    CORS_ORIGINS = [
        origin.strip()
        for origin in environ.get(
            "CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"
        ).split(",")
        if origin.strip()
    ]
    AUTO_CREATE_TABLES = _as_bool("AUTO_CREATE_TABLES", True)
    RATELIMIT_STORAGE_URI = environ.get("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_ENABLED = _as_bool("RATELIMIT_ENABLED", True)


class DevelopmentConfig(Config):
    DEBUG = _as_bool("FLASK_DEBUG", False)
    SQLALCHEMY_DATABASE_URI = environ.get("DEV_DATABASE_URI")


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = environ.get("PROD_DATABASE_URI")
    AUTO_CREATE_TABLES = _as_bool("AUTO_CREATE_TABLES", False)


# Alias conservado para los servicios existentes.
config = Config
