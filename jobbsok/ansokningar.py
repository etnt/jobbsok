"""Uppföljning av ansökningar: status, datum, anteckningar och påminnelser."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date, datetime

from . import annonser
from .platsbanken import Annons

ANSOKT = "ansokt"
INTERVJU = "intervju"
AVSLAG = "avslag"
INGET_SVAR = "inget_svar"

STATUSAR = {
    ANSOKT: "Ansökt",
    INTERVJU: "Intervju",
    INGET_SVAR: "Inget svar",
    AVSLAG: "Avslag",
}

UPPFOLJNING_EFTER_DAGAR = 14  # påminnelse om ansökan utan svar


@dataclass
class Ansokan:
    annons: Annons
    status: str
    ansokt_datum: str  # YYYY-MM-DD, tomt om ej satt
    anteckning: str
    uppdaterad: str


def init_tabell(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS ansokningar ("
        " annons_id TEXT PRIMARY KEY,"
        " status TEXT NOT NULL,"
        " ansokt_datum TEXT NOT NULL DEFAULT '',"
        " anteckning TEXT NOT NULL DEFAULT '',"
        " uppdaterad TEXT NOT NULL)"
    )
    conn.commit()


def spara_status(
    conn: sqlite3.Connection,
    annons_id: str,
    status: str,
    *,
    ansokt_datum: str | None = None,
    anteckning: str | None = None,
) -> None:
    """Sätter status för en ansökan. Skapar posten om den saknas."""
    if status not in STATUSAR:
        raise ValueError(f"Okänd status: {status}")
    init_tabell(conn)
    nu = datetime.now().isoformat(timespec="seconds")
    rad = conn.execute(
        "SELECT ansokt_datum, anteckning FROM ansokningar WHERE annons_id = ?", (annons_id,)
    ).fetchone()
    if rad is None:
        datum = ansokt_datum if ansokt_datum is not None else (date.today().isoformat() if status == ANSOKT else "")
        conn.execute(
            "INSERT INTO ansokningar (annons_id, status, ansokt_datum, anteckning, uppdaterad) "
            "VALUES (?, ?, ?, ?, ?)",
            (annons_id, status, datum, anteckning or "", nu),
        )
    else:
        datum = ansokt_datum if ansokt_datum is not None else rad["ansokt_datum"]
        if not datum and status == ANSOKT:
            datum = date.today().isoformat()
        text = anteckning if anteckning is not None else rad["anteckning"]
        conn.execute(
            "UPDATE ansokningar SET status = ?, ansokt_datum = ?, anteckning = ?, uppdaterad = ? "
            "WHERE annons_id = ?",
            (status, datum, text, nu, annons_id),
        )
    conn.commit()
    annonser.satt_status(conn, annons_id, annonser.STATUS_ANSOKT)


def ta_bort(conn: sqlite3.Connection, annons_id: str) -> None:
    """Tar bort ansökan och lägger tillbaka annonsen bland de sparade."""
    init_tabell(conn)
    conn.execute("DELETE FROM ansokningar WHERE annons_id = ?", (annons_id,))
    conn.commit()
    annonser.satt_status(conn, annons_id, annonser.STATUS_SPARAD)


def lista(conn: sqlite3.Connection, status: str | None = None) -> list[Ansokan]:
    init_tabell(conn)
    annonser.init_tabell(conn)
    sql = (
        "SELECT a.data AS data, ans.status, ans.ansokt_datum, ans.anteckning, ans.uppdaterad "
        "FROM ansokningar ans JOIN annonser a ON a.id = ans.annons_id"
    )
    params: tuple = ()
    if status:
        sql += " WHERE ans.status = ?"
        params = (status,)
    sql += " ORDER BY ans.ansokt_datum DESC, ans.uppdaterad DESC"
    rader = conn.execute(sql, params).fetchall()
    return [
        Ansokan(
            annons=annonser.fran_json(r["data"]),
            status=r["status"],
            ansokt_datum=r["ansokt_datum"],
            anteckning=r["anteckning"],
            uppdaterad=r["uppdaterad"],
        )
        for r in rader
    ]


def antal_per_status(conn: sqlite3.Connection) -> dict[str, int]:
    init_tabell(conn)
    rader = conn.execute("SELECT status, COUNT(*) AS n FROM ansokningar GROUP BY status").fetchall()
    return {r["status"]: r["n"] for r in rader}


# --- Hjälpfunktioner för visning -------------------------------------------

def dagar_kvar(sista_dag: str, idag: date | None = None) -> int | None:
    """Antal dagar till sista ansökningsdag. Negativt om den passerat. None om okänt."""
    try:
        slut = date.fromisoformat(sista_dag[:10])
    except (ValueError, TypeError):
        return None
    return (slut - (idag or date.today())).days


def behover_uppfoljning(a: Ansokan, idag: date | None = None) -> bool:
    """Ansökt för länge sedan utan svar, eller intervju/avslag som inte följts upp."""
    if a.status != ANSOKT or not a.ansokt_datum:
        return False
    try:
        sedan = date.fromisoformat(a.ansokt_datum)
    except ValueError:
        return False
    return ((idag or date.today()) - sedan).days >= UPPFOLJNING_EFTER_DAGAR
