"""Sök i Platsbanken via Arbetsförmedlingens öppna JobSearch-API.

API-dokumentation: https://jobsearch.api.jobtechdev.se (swagger.json)
Inget API-nyckel krävs.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Iterable

from .settings import Sokinstallningar

BASE_URL = "https://jobsearch.api.jobtechdev.se"
USER_AGENT = "JobbSok/0.1 (lokal personlig jobbsökning)"
FULLTID_TIMMAR = 40  # 100 % omfattning i timmar per vecka

# Concept-id i JobSearch-taxonomin:
TILLFALLIG_ANSTALLNING = [
    "1paU_aCR_nGn",  # Behovsanställning
    "sTu5_NBQ_udq",  # Tidsbegränsad anställning
    "Jh8f_q9J_pbJ",  # Sommarjobb / feriejobb
]


@dataclass
class Plats:
    namn: str
    lat: float
    lon: float


@dataclass
class Annons:
    id: str
    rubrik: str
    arbetsgivare: str
    ort: str
    lan: str
    lank: str
    sista_ansokningsdag: str
    anstallning: str
    arbetstid: str
    omfattning_min: int | None
    omfattning_max: int | None
    beskrivning: str
    publicerad: str
    yrke: str
    korkort_kravs: bool = False
    raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def fran_api(cls, hit: dict[str, Any]) -> "Annons":
        def label(key: str) -> str:
            return ((hit.get(key) or {}).get("label")) or ""

        adress = hit.get("workplace_address") or {}
        employer = hit.get("employer") or {}
        scope = hit.get("scope_of_work") or {}
        desc = (hit.get("description") or {}).get("text") or ""
        ad_id = str(hit.get("id", ""))
        return cls(
            id=ad_id,
            rubrik=hit.get("headline") or "",
            arbetsgivare=employer.get("name") or "",
            ort=adress.get("city") or adress.get("municipality") or "",
            lan=adress.get("region") or "",
            lank=hit.get("webpage_url") or f"https://arbetsformedlingen.se/platsbanken/annonser/{ad_id}",
            sista_ansokningsdag=(hit.get("application_deadline") or "")[:10],
            anstallning=label("employment_type"),
            arbetstid=label("working_hours_type"),
            omfattning_min=scope.get("min"),
            omfattning_max=scope.get("max"),
            beskrivning=desc,
            publicerad=(hit.get("publication_date") or hit.get("original_publication_date") or "")[:10],
            yrke=label("occupation"),
            korkort_kravs=bool(hit.get("driving_license_required")),
            raw=hit,
        )


def _get_json(path: str, params: list[tuple[str, str]]) -> dict[str, Any]:
    url = f"{BASE_URL}{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def bygg_frageparametrar(
    platser: Iterable[Plats], sok: Sokinstallningar, har_korkort: bool | None = None
) -> list[list[tuple[str, str]]]:
    """Gör en lista med frågor (parameterlistor) för API:t.

    En fråga per plats och per filtertyp. Resultaten slås ihop efteråt.
    """
    q = " ".join(sok.yrken)  # API:t tolkar fritext med OR som standard
    radie = max(1, int(sok.radie_km))
    fragor: list[list[tuple[str, str]]] = []
    for plats in platser:
        bas: list[tuple[str, str]] = [
            ("q", q),
            ("position", f"{plats.lat},{plats.lon}"),
            ("position.radius", str(radie)),
            ("sort", "pubdate-desc"),
            ("limit", "100"),
        ]
        if har_korkort is False:
            # Hoppa över annonser som kräver körkort när personen saknar körkort
            bas.append(("driving-license-required", "false"))
        if sok.endast_deltid_och_tillfalligt:
            # Deltid: ads med omfattning under 100 %
            fragor.append(bas + [("parttime.max", "99")])
            # Tillfälliga anställningar av alla omfattningar
            fragor.append(bas + [("employment-type", c) for c in TILLFALLIG_ANSTALLNING])
        else:
            fragor.append(bas)
    return fragor


def passar_timmar(annons: Annons, sok: Sokinstallningar) -> bool:
    """Kontrollerar om annonsens omfattning överlappar önskade timmar.

    Annonser utan uppgift om omfattning släpps igenom.
    """
    if annons.omfattning_min is None or annons.omfattning_max is None:
        return True
    onskad_min = sok.timmar_min / FULLTID_TIMMAR * 100
    onskad_max = min(100, sok.timmar_max / FULLTID_TIMMAR * 100)
    return annons.omfattning_min <= onskad_max and annons.omfattning_max >= onskad_min


def korkort_ok(annons: Annons, har_korkort: bool | None) -> bool:
    """False om annonsen kräver körkort och personen saknar körkort."""
    return not (annons.korkort_kravs and har_korkort is False)


def sok_annonser(platser: list[Plats], sok: Sokinstallningar, har_korkort: bool | None = None) -> list[Annons]:
    """Kör alla frågor, slår ihop dubbletter och filtrerar på timmar och körkort."""
    funna: dict[str, Annons] = {}
    for params in bygg_frageparametrar(platser, sok, har_korkort):
        data = _get_json("/search", params + [("resdet", "full")])
        for hit in data.get("hits", []):
            annons = Annons.fran_api(hit)
            if annons.id and annons.id not in funna:
                funna[annons.id] = annons
    resultat = [a for a in funna.values() if passar_timmar(a, sok) and korkort_ok(a, har_korkort)]
    resultat.sort(key=lambda a: a.publicerad, reverse=True)
    return resultat
