"""Poängsätter annonser mot profilen med en AI-modell.

Personuppgifter som e-post och telefon skickas aldrig till modellen.
Resultat sparas i databasen, så en annons poängsätts bara en gång
(om inte modellen ändras).
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from . import llm
from .platsbanken import Annons
from .settings import Modeller, Profil, Sokinstallningar

MAX_BESKRIVNING_TECKEN = 6000
Chattfunktion = Callable[..., str]

SYSTEM_PROMPT = """Du hjälper en person att hitta tillfälliga och deltidsjobb i Sverige.
Du får en profil på personen, hens sökinriktning och en jobbannons.
Bedöm hur väl annonsen passar personen.

Svara ENDAST med ett JSON-objekt med dessa fält:
- "poang": heltal 0–100 (100 = perfekt match)
- "passar": "bra", "delvis" eller "nej"
- "motivering": en eller två korta meningar på svenska som förklarar poängen
- "sprakkrav": "svenska_kravs", "engelska_racker" eller "okant"
- "varningar": lista med korta svenska strängar, t.ex. krav som personen troligen inte uppfyller (kan vara tom)

Var ärlig. Om annonsen kräver något personen inte har, sänk poängen och nämn det.
Om annonsen är för avlägsen från personens ort eller arbetstid inte passar, nämn det.
"""


@dataclass
class Poang:
    annons_id: str
    poang: int
    passar: str
    motivering: str
    sprakkrav: str
    varningar: list[str]
    modell: str


def bygg_profiltext(profil: Profil, sok: Sokinstallningar) -> str:
    """Profil utan kontaktuppgifter, med sökinriktning."""
    rader = [
        f"Bor i: {profil.ort or 'okänt'}",
        f"Utbildning: {profil.utbildning or 'ej angiven'}",
        f"Arbetslivserfarenhet: {profil.arbetslivserfarenhet or 'ej angiven'}",
        f"Kompetenser: {', '.join(profil.kompetenser) or 'ej angivna'}",
        f"Språk: {', '.join(profil.sprak) or 'ej angivna'}",
        f"Körkort B: {'ja' if profil.korkort else 'nej'}",
        f"Tillgänglighet: {profil.tillganglighet or 'ej angiven'}",
        f"Önskar arbeta {sok.timmar_min}–{sok.timmar_max} timmar per vecka",
        f"Söker inom {sok.radie_km} km från: {', '.join(sok.orter) or 'ej angivet'}",
        f"Söker efter: {', '.join(sok.yrken) or 'alla yrken'}",
    ]
    if profil.cv_text:
        rader.append(f"CV (utdrag):\n{profil.cv_text[:4000]}")
    return "\n".join(rader)


def bygg_annonstext(annons: Annons) -> str:
    beskr = (annons.beskrivning or "")[:MAX_BESKRIVNING_TECKEN]
    return (
        f"Rubrik: {annons.rubrik}\n"
        f"Arbetsgivare: {annons.arbetsgivare}\n"
        f"Ort: {annons.ort}, {annons.lan}\n"
        f"Anställning: {annons.anstallning or 'okänt'}\n"
        f"Arbetstid: {annons.arbetstid or 'okänt'}\n"
        f"Yrke: {annons.yrke or 'okänt'}\n"
        f"Körkort krävs: {'ja' if annons.korkort_kravs else 'nej/okänt'}\n\n"
        f"Annonstext:\n{beskr}"
    )


def poangsatt_en(
    profil: Profil,
    sok: Sokinstallningar,
    annons: Annons,
    modell: str,
    chatt: Chattfunktion = llm.chat,
) -> Poang:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"PROFIL:\n{bygg_profiltext(profil, sok)}\n\nANNONS:\n{bygg_annonstext(annons)}",
        },
    ]
    svar = chatt(messages, modell, json_format=True, temperature=0.1, max_tokens=500)
    data = llm.parsa_json(svar)
    try:
        poang = int(round(float(data.get("poang", 0))))
    except (TypeError, ValueError) as fel:
        raise llm.LLMFel("Modellen gav ingen giltig poäng.") from fel
    varningar = data.get("varningar") or []
    if not isinstance(varningar, list):
        varningar = [str(varningar)]
    return Poang(
        annons_id=annons.id,
        poang=max(0, min(100, poang)),
        passar=str(data.get("passar", "delvis")),
        motivering=str(data.get("motivering", "")).strip(),
        sprakkrav=str(data.get("sprakkrav", "okant")),
        varningar=[str(v) for v in varningar],
        modell=modell,
    )


# --- Lagring -------------------------------------------------------------

def init_tabell(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS poang ("
        " annons_id TEXT PRIMARY KEY,"
        " poang INTEGER NOT NULL,"
        " passar TEXT NOT NULL,"
        " motivering TEXT NOT NULL,"
        " sprakkrav TEXT NOT NULL,"
        " varningar TEXT NOT NULL,"
        " modell TEXT NOT NULL,"
        " skapad TEXT NOT NULL)"
    )
    conn.commit()


def spara_poang(conn: sqlite3.Connection, p: Poang) -> None:
    init_tabell(conn)
    conn.execute(
        "INSERT OR REPLACE INTO poang VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            p.annons_id, p.poang, p.passar, p.motivering, p.sprakkrav,
            json.dumps(p.varningar, ensure_ascii=False), p.modell,
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    conn.commit()


def hamta_poang(conn: sqlite3.Connection) -> dict[str, Poang]:
    init_tabell(conn)
    rader = conn.execute("SELECT * FROM poang").fetchall()
    return {
        r["annons_id"]: Poang(
            annons_id=r["annons_id"], poang=r["poang"], passar=r["passar"],
            motivering=r["motivering"], sprakkrav=r["sprakkrav"],
            varningar=json.loads(r["varningar"]), modell=r["modell"],
        )
        for r in rader
    }


def poangsatt_nya(
    conn: sqlite3.Connection,
    annonser: list[Annons],
    profil: Profil,
    sok: Sokinstallningar,
    modeller: Modeller,
    chatt: Chattfunktion = llm.chat,
    grans: int = 25,
) -> tuple[int, list[str]]:
    """Poängsätter annonser som saknar poäng. Returnerar (antal klara, felmeddelanden)."""
    befintliga = hamta_poang(conn)
    att_gora = [a for a in annonser if a.id not in befintliga][:grans]
    klara, fel = 0, []
    for annons in att_gora:
        try:
            spara_poang(conn, poangsatt_en(profil, sok, annons, modeller.poang_modell, chatt))
            klara += 1
        except llm.LLMFatalFel as e:
            fel.append(str(e))
            break  # samma fel skulle upprepas för varje annons
        except llm.LLMFel as e:
            fel.append(str(e))
    return klara, fel
