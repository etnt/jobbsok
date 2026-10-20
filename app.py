"""JobbSök – lokal app för att hitta tillfälliga och deltidsjobb.

Starta med starta.bat (Windows) eller: streamlit run app.py
"""

from __future__ import annotations

import os

import streamlit as st
from dotenv import load_dotenv

from jobbsok import settings
from jobbsok.storage import APP_DIR, connect

load_dotenv(APP_DIR / ".env")

st.set_page_config(page_title="JobbSök", page_icon="💼", layout="wide")


@st.cache_resource
def _db():
    return connect()


conn = _db()


def _lista_fran_text(text: str) -> list[str]:
    """Gör en rad per post till en lista, utan tomma rader."""
    return [rad.strip() for rad in text.splitlines() if rad.strip()]


def _text_fran_lista(lista: list[str]) -> str:
    return "\n".join(lista)


def sida_profil() -> None:
    st.header("Min profil")
    st.caption(
        "Fyll i uppgifterna en gång. Personnummer ska inte skrivas in här. "
        "Uppgifterna används för matchning och för att skriva CV och brev."
    )
    p = settings.load_profil(conn)

    with st.form("profil_form"):
        c1, c2 = st.columns(2)
        with c1:
            namn = st.text_input("Namn", p.namn)
            ort = st.text_input("Bor i (ort)", p.ort)
            epost = st.text_input("E-post", p.epost)
            telefon = st.text_input("Telefon", p.telefon)
            korkort = st.checkbox("Har körkort (B)", p.korkort)
        with c2:
            tillganglighet = st.text_input(
                "Tillgänglighet", p.tillganglighet,
                placeholder="t.ex. Kan börja direkt, tillgänglig från 1 september",
            )
            sprak = st.text_area(
                "Språk (en per rad)", _text_fran_lista(p.sprak),
                placeholder="Svenska (modersmål)\nEngelska (flytande)", height=110,
            )
            kompetenser = st.text_area(
                "Kompetenser (en per rad)", _text_fran_lista(p.kompetenser),
                placeholder="AutoCAD\nByggarbetsplatsrutiner\nTruckkort", height=110,
            )
        utbildning = st.text_area(
            "Utbildning", p.utbildning, height=90,
            placeholder="Byggingenjör, KTH, 2022–2025 (3-årigt program)",
        )
        erfarenhet = st.text_area(
            "Arbetslivserfarenhet", p.arbetslivserfarenhet, height=140,
            placeholder="Roll, företag, period, och kort om vad du gjorde",
        )
        cv_text = st.text_area(
            "Nuvarande CV (klistra in text)", p.cv_text, height=200,
            help="Klistra in texten från CV:t. Det används som utgångspunkt för dina dokument.",
        )
        if st.form_submit_button("Spara profil", type="primary"):
            settings.save_profil(conn, settings.Profil(
                namn=namn.strip(), ort=ort.strip(), epost=epost.strip(),
                telefon=telefon.strip(), utbildning=utbildning.strip(),
                arbetslivserfarenhet=erfarenhet.strip(),
                kompetenser=_lista_fran_text(kompetenser),
                sprak=_lista_fran_text(sprak), korkort=korkort,
                tillganglighet=tillganglighet.strip(), cv_text=cv_text.strip(),
            ))
            st.success("Profilen är sparad.")


def sida_sok() -> None:
    st.header("Sökinställningar")
    st.caption("Här väljer du var och hur du vill söka. Ändra gärna när som helst.")
    s = settings.load_sok(conn)

    with st.form("sok_form"):
        orter = st.text_area(
            "Orter eller kommuner (en per rad)", _text_fran_lista(s.orter), height=120,
            placeholder="Stockholm\nSolna\nSigtuna",
        )
        radie = st.slider("Max avstånd från din ort (km)", 0, 200, s.radie_km)
        c1, c2 = st.columns(2)
        with c1:
            timmar_min, timmar_max = st.slider(
                "Önskat antal timmar per vecka", 0, 40, (s.timmar_min, s.timmar_max),
            )
        with c2:
            deltid = st.checkbox(
                "Visa endast deltid, visstid och tillfälliga jobb",
                s.endast_deltid_och_tillfalligt,
            )
        yrken = st.text_area(
            "Yrken eller sökord (en per rad, tomt = alla yrken)",
            _text_fran_lista(s.yrken), height=120,
            placeholder="Bygg\nByggarbetsplats\nLager\nBIM-assistent",
        )
        if st.form_submit_button("Spara sökinställningar", type="primary"):
            settings.save_sok(conn, settings.Sokinstallningar(
                orter=_lista_fran_text(orter), radie_km=radie,
                timmar_min=timmar_min, timmar_max=timmar_max,
                yrken=_lista_fran_text(yrken),
                endast_deltid_och_tillfalligt=deltid,
            ))
            st.success("Sökinställningarna är sparade.")


def sida_installningar() -> None:
    st.header("Inställningar för AI")
    st.caption(
        "AI används för att matcha jobb och skriva dokument via OpenRouter. "
        "Nyckeln sparas i filen .env i appmappen."
    )
    nyckel_finns = bool(os.environ.get("OPENROUTER_API_KEY"))
    if nyckel_finns:
        st.success("OpenRouter-nyckel hittad.")
    else:
        st.warning(
            "Ingen OpenRouter-nyckel hittad. Kopiera filen .env.example till .env "
            "och skriv in nyckeln."
        )

    m = settings.load_modeller(conn)
    with st.form("modell_form"):
        poang = st.text_input(
            "Modell för matchning (billig)", m.poang_modell,
            help="OpenRouter-modellnamn, t.ex. openai/gpt-4o-mini",
        )
        skriv = st.text_input(
            "Modell för CV och brev (bättre skrivning)", m.skriv_modell,
            help="OpenRouter-modellnamn, t.ex. anthropic/claude-sonnet-4",
        )
        if st.form_submit_button("Spara modeller", type="primary"):
            settings.save_modeller(conn, settings.Modeller(
                poang_modell=poang.strip(), skriv_modell=skriv.strip(),
            ))
            st.success("Modellinställningarna är sparade.")


def sida_sok_jobb() -> None:
    st.header("Sök jobb")
    st.info("Sökning i Platsbanken kommer i nästa steg.")


def sida_tracker() -> None:
    st.header("Mina ansökningar")
    st.info("Uppföljningslistan kommer i ett senare steg.")


SIDOR = {
    "Min profil": sida_profil,
    "Sökinställningar": sida_sok,
    "Sök jobb": sida_sok_jobb,
    "Mina ansökningar": sida_tracker,
    "Inställningar för AI": sida_installningar,
}

with st.sidebar:
    st.title("💼 JobbSök")
    valt = st.radio("Meny", list(SIDOR.keys()), label_visibility="collapsed")

SIDOR[valt]()
