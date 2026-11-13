import pytest

from app.core.config import Settings
from app.db.engine import normalize_async_database_url
from app.models.review import Base


def test_normalizes_neon_libpq_url_for_asyncpg() -> None:
    target = normalize_async_database_url(
        "postgresql://prism:example@ep-example-pooler.us-east-1.aws.neon.tech/"
        "prism?sslmode=require&channel_binding=require"
    )

    assert target.url.drivername == "postgresql+asyncpg"
    assert "sslmode" not in target.url.query
    assert "channel_binding" not in target.url.query
    assert target.connect_args == {"ssl": "require"}


def test_rejects_non_postgresql_database_urls() -> None:
    with pytest.raises(ValueError, match="PostgreSQL"):
        normalize_async_database_url("sqlite+aiosqlite:///prism.db")


def test_uses_direct_database_url_for_migrations() -> None:
    settings = Settings(
        DATABASE_URL="postgresql://prism:example@pooled.neon.tech/prism?sslmode=require",
        DIRECT_DATABASE_URL="postgresql://prism:example@direct.neon.tech/prism?sslmode=require",
    )

    assert settings.migration_database_url.startswith(
        "postgresql://prism:example@direct"
    )


def test_configures_groq_primary_and_gemini_fallback_without_exposing_keys() -> None:
    settings = Settings(GROQ_API_KEY="test-groq", GEMINI_API_KEY="test-gemini")

    assert settings.llm_primary_provider == "groq"
    assert settings.llm_fallback_provider == "gemini"
    assert str(settings.groq_api_key) == "**********"
    assert str(settings.gemini_api_key) == "**********"


def test_initial_metadata_includes_review_persistence_tables() -> None:
    assert set(Base.metadata.tables) == {
        "github_installations",
        "github_webhook_deliveries",
        "pull_requests",
        "repositories",
        "review_findings",
        "review_runs",
        "users",
    }
