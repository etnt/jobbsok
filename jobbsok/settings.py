"""Profil och sökinställningar, sparade som JSON i databasen."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import sqlite3

from .storage import get_setting, set_setting

PROFILE_KEY = "profil"
SEARCH_KEY = "sok"
MODEL_KEY = "modeller"


@dataclass
class Profil:
    namn: str = ""
    ort: str = ""
    epost: str = ""
    telefon: str = ""
    utbildning: str = ""
    arbetslivserfarenhet: str = ""
    kompetenser: list[str] = field(default_factory=list)
    sprak: list[str] = field(default_factory=list)  # t.ex. "Svenska (modersmål)"
    korkort: bool = False
    tillganglighet: str = ""  # t.ex. "Från 1 september, kan börja direkt"
    cv_text: str = ""  # klistrad text från nuvarande CV
    # Personnummer lagras aldrig i appen.


@dataclass
class Sokinstallningar:
    orter: list[str] = field(default_factory=list)  # kommuner eller regioner
    radie_km: int = 30
    timmar_min: int = 0  # 0 = inget krav
    timmar_max: int = 40
    yrken: list[str] = field(default_factory=list)  # fritt, tomt = alla
    endast_deltid_och_tillfalligt: bool = True


@dataclass
class Modeller:
    poang_modell: str = "openai/gpt-4.1-mini"
    skriv_modell: str = "anthropic/claude-sonnet-4.6"


def _from_dict(cls, data: dict):
    known = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
    return cls(**known)


def load_profil(conn: sqlite3.Connection) -> Profil:
    return _from_dict(Profil, get_setting(conn, PROFILE_KEY, {}) or {})


def save_profil(conn: sqlite3.Connection, profil: Profil) -> None:
    set_setting(conn, PROFILE_KEY, asdict(profil))


def load_sok(conn: sqlite3.Connection) -> Sokinstallningar:
    return _from_dict(Sokinstallningar, get_setting(conn, SEARCH_KEY, {}) or {})


def save_sok(conn: sqlite3.Connection, sok: Sokinstallningar) -> None:
    set_setting(conn, SEARCH_KEY, asdict(sok))


def load_modeller(conn: sqlite3.Connection) -> Modeller:
    return _from_dict(Modeller, get_setting(conn, MODEL_KEY, {}) or {})


def save_modeller(conn: sqlite3.Connection, modeller: Modeller) -> None:
    set_setting(conn, MODEL_KEY, asdict(modeller))
