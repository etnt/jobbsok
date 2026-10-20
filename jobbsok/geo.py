"""Omvandlar ortnamn till koordinater med OpenStreetMap Nominatim.

Resultaten cachas i databasen, så varje ort slås upp bara en gång.
Nominatim kräver max 1 förfrågan per sekund och en identifierbar User-Agent.
"""

from __future__ import annotations

import json
import sqlite3
import time
import urllib.parse
import urllib.request

from .platsbanken import USER_AGENT, Plats
from .storage import get_setting, set_setting

CACHE_KEY = "geocache"


def geocode(conn: sqlite3.Connection, ort: str) -> Plats | None:
    ort = ort.strip()
    if not ort:
        return None
    cache: dict = get_setting(conn, CACHE_KEY, {}) or {}
    if ort in cache:
        punkt = cache[ort]
        return Plats(ort, punkt[0], punkt[1]) if punkt else None

    params = urllib.parse.urlencode(
        {"q": ort, "format": "json", "limit": 1, "countrycodes": "se", "accept-language": "sv"}
    )
    req = urllib.request.Request(
        f"https://nominatim.openstreetmap.org/search?{params}",
        headers={"User-Agent": USER_AGENT},
    )
    time.sleep(1.1)  # håll oss under gränsen på 1 förfrågan/sekund
    with urllib.request.urlopen(req, timeout=30) as resp:
        träffar = json.loads(resp.read().decode("utf-8"))

    if träffar:
        lat, lon = float(träffar[0]["lat"]), float(träffar[0]["lon"])
        cache[ort] = [lat, lon]
        set_setting(conn, CACHE_KEY, cache)
        return Plats(ort, lat, lon)

    # Spara inga träffar, så att ortnamnet kan kollas igen senare.
    return None
