"""Sparade annonser i databasen, med status (ny, sparad, dold)."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime

from .platsbanken import Annons

STATUS_NY = "ny"
STATUS_SPARAD = "sparad"
STATUS_DOLD = "dold"
STATUS_ANSOKT = "ansokt"  # ansökan finns i uppföljningen (ansokningar.py)


def init_tabell(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS annonser ("
        " id TEXT PRIMARY KEY,"
        " data TEXT NOT NULL,"
        " hamtad TEXT NOT NULL,"
        " status TEXT NOT NULL DEFAULT 'ny')"
    )
    conn.commit()


def spara_nya(conn: sqlite3.Connection, annonser: list[Annons]) -> int:
    """Lagrar annonser. Befintlig status behålls. Returnerar antal nya annonser."""
    init_tabell(conn)
    nu = datetime.now().isoformat(timespec="seconds")
    nya = 0
    for a in annonser:
        finns = conn.execute("SELECT 1 FROM annonser WHERE id = ?", (a.id,)).fetchone()
        if finns:
            conn.execute("UPDATE annonser SET data = ? WHERE id = ?", (_json(a), a.id))
        else:
            conn.execute(
                "INSERT INTO annonser (id, data, hamtad, status) VALUES (?, ?, ?, ?)",
                (a.id, _json(a), nu, STATUS_NY),
            )
            nya += 1
    conn.commit()
    return nya


def _json(a: Annons) -> str:
    data = {k: v for k, v in a.__dict__.items() if k != "raw"}
    data["raw"] = a.raw
    return json.dumps(data, ensure_ascii=False)


def lista(conn: sqlite3.Connection, status: str) -> list[tuple[Annons, str]]:
    init_tabell(conn)
    rader = conn.execute(
        "SELECT data, status FROM annonser WHERE status = ? ORDER BY json_extract(data, '$.publicerad') DESC",
        (status,),
    ).fetchall()
    return [(fran_json(r["data"]), r["status"]) for r in rader]


def antal_per_status(conn: sqlite3.Connection) -> dict[str, int]:
    init_tabell(conn)
    rader = conn.execute("SELECT status, COUNT(*) AS n FROM annonser GROUP BY status").fetchall()
    return {r["status"]: r["n"] for r in rader}


def satt_status(conn: sqlite3.Connection, annons_id: str, status: str) -> None:
    conn.execute("UPDATE annonser SET status = ? WHERE id = ?", (status, annons_id))
    conn.commit()


def fran_json(text: str) -> Annons:
    data = json.loads(text)
    raw = data.pop("raw", {})
    return Annons(**data, raw=raw)
