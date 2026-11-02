"""Helper script to verify MySQL connectivity, create database if missing, and run Alembic migrations."""
import os
import sys
from pathlib import Path
from urllib.parse import urlparse, unquote

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

import pymysql
from app.core.config import get_settings
from app.db.session import normalize_database_url
from alembic.config import Config
from alembic import command


def setup_mysql() -> None:
    settings = get_settings()
    raw_url = os.getenv("DATABASE_URL", settings.database_url)
    url = normalize_database_url(raw_url)

    if not url.startswith("mysql"):
        print(f"[!] Warning: DATABASE_URL is not configured for MySQL: {url}")
        print("    Example: DATABASE_URL=mysql+pymysql://root:password@localhost:3306/gitauto?charset=utf8mb4")
        sys.exit(1)

    # Parse connection components
    parsed = urlparse(url.replace("mysql+pymysql://", "http://").replace("mysql://", "http://"))
    host = parsed.hostname or "localhost"
    port = parsed.port or 3306
    user = unquote(parsed.username or "root")
    password = unquote(parsed.password or "")
    db_name = parsed.path.lstrip("/").split("?")[0] or "gitauto"

    print(f"[*] Connecting to MySQL host: {host}:{port} as user: '{user}'...")
    try:
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            connect_timeout=10,
        )
    except Exception as exc:
        print(f"[X] Could not connect to MySQL server at {host}:{port}: {exc}")
        print("    Please ensure MySQL server is running and credentials are valid.")
        sys.exit(1)

    try:
        with conn.cursor() as cursor:
            print(f"[*] Ensuring database `{db_name}` exists with utf8mb4 collation...")
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            )
        conn.commit()
        print(f"[V] Database `{db_name}` ready.")
    finally:
        conn.close()

    # Run Alembic migrations
    print("[*] Running Alembic migrations (upgrade head)...")
    alembic_cfg = Config(str(backend_dir / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(backend_dir / "migrations"))
    alembic_cfg.set_main_option("sqlalchemy.url", url)

    try:
        command.upgrade(alembic_cfg, "head")
        print("[V] All database migrations successfully applied to MySQL!")
    except Exception as exc:
        print(f"[X] Alembic migration failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    setup_mysql()

