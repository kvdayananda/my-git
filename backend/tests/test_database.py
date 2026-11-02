import pytest
from app.db.session import normalize_database_url, create_db_engine
from app.core.config import Settings
from app.api.dashboard import get_system_status


def test_normalize_database_url() -> None:
    # Bare mysql -> mysql+pymysql
    assert normalize_database_url("mysql://root:pass@localhost:3306/gitauto") == "mysql+pymysql://root:pass@localhost:3306/gitauto"

    # Already specified mysql+pymysql -> preserved
    assert normalize_database_url("mysql+pymysql://root:pass@localhost:3306/gitauto") == "mysql+pymysql://root:pass@localhost:3306/gitauto"

    # Bare postgres -> postgresql
    assert normalize_database_url("postgres://user:pass@localhost:5432/gitauto") == "postgresql://user:pass@localhost:5432/gitauto"

    # SQLite -> preserved
    assert normalize_database_url("sqlite:///./gitauto.db") == "sqlite:///./gitauto.db"
    assert normalize_database_url("sqlite:///:memory:") == "sqlite:///:memory:"


def test_create_db_engine_sqlite() -> None:
    engine = create_db_engine("sqlite:///:memory:")
    assert engine.dialect.name == "sqlite"


@pytest.mark.asyncio
async def test_mysql_database_type_detected(monkeypatch) -> None:
    fake_settings = Settings(database_url="mysql+pymysql://gitauto:secret@localhost:3306/gitauto")
    monkeypatch.setattr("app.api.dashboard.get_settings", lambda: fake_settings)

    async def fake_docker_ready(s):
        return False

    monkeypatch.setattr("app.api.dashboard.docker_ready", fake_docker_ready)

    status = await get_system_status()
    assert status.database_type == "mysql"
