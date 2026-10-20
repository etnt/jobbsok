"""Lokal lagring i SQLite. Allt lagras i en fil på användarens dator."""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

APP_DIR = Path(__file__).resolve().parent.parent


def data_dir() -> Path:
    """Mappen för databasen. Kan ändras med miljövariabeln JOBBSOK_DATA."""
    custom = os.environ.get("JOBBSOK_DATA")
    path = Path(custom) if custom else APP_DIR / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def db_path() -> Path:
    return data_dir() / "jobbsok.sqlite3"


def connect(path: Path | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(path or db_path())
    conn.row_factory = sqlite3.Row
    conn.execute(
        "CREATE TABLE IF NOT EXISTS installningar ("
        " nyckel TEXT PRIMARY KEY,"
        " varde TEXT NOT NULL)"
    )
    conn.commit()
    return conn


def get_setting(conn: sqlite3.Connection, key: str, default: Any = None) -> Any:
    row = conn.execute(
        "SELECT varde FROM installningar WHERE nyckel = ?", (key,)
    ).fetchone()
    if row is None:
        return default
    return json.loads(row["varde"])


def set_setting(conn: sqlite3.Connection, key: str, value: Any) -> None:
    conn.execute(
        "INSERT INTO installningar (nyckel, varde) VALUES (?, ?) "
        "ON CONFLICT(nyckel) DO UPDATE SET varde = excluded.varde",
        (key, json.dumps(value, ensure_ascii=False)),
    )
    conn.commit()
