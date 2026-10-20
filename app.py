"""JobbSök – lokal app för att hitta jobb i Sverige (heltid, deltid eller tillfälligt).

Starta med starta.bat (Windows) eller: streamlit run app.py
"""

from __future__ import annotations

import os
from datetime import date

import streamlit as st
from dotenv import load_dotenv

from jobbsok import annonser, ansokningar, dokument, geo, llm, matchning, platsbanken, settings
from jobbsok.version import __version__
from jobbsok.storage import connect, env_fil

load_dotenv(env_fil(), override=True)  # .env har företräde framför terminalens variabler

st.set_page_config(page_title="JobbSök", page_icon="💼", layout="wide")


# Ny anslutning för varje körning. SQLite-anslutningar får inte delas mellan trådar,
# och Streamlit kör varje körning i en egen tråd.
conn = connect()


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
                "Visa bara deltid och tillfälliga jobb",
                s.endast_deltid_och_tillfalligt,
                help="Av = visa alla jobb, även heltidsjobb. Timantalet ovan gäller oavsett.",
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
            help="OpenRouter-modellnamn, t.ex. openai/gpt-6-luna",
        )
        skriv = st.text_input(
            "Modell för CV och brev (bättre skrivning)", m.skriv_modell,
            help="OpenRouter-modellnamn, t.ex. anthropic/claude-haiku-5.5",
        )
        if st.form_submit_button("Spara modeller", type="primary"):
            settings.save_modeller(conn, settings.Modeller(
                poang_modell=poang.strip(), skriv_modell=skriv.strip(),
            ))
            st.success("Modellinställningarna är sparade.")

    st.subheader("Testa anslutningen")
    if st.button("Testa AI-anslutningen"):
        try:
            svar = llm.chat(
                [{"role": "user", "content": "Svara med ordet OK."}],
                settings.load_modeller(conn).poang_modell, max_tokens=10,
            )
            st.success(f"Anslutningen fungerar. Svar: {svar.strip()[:50]}")
        except llm.LLMFel as fel:
            st.error(str(fel))


def _poang_etikett(poang) -> str:
    if poang is None:
        return "⚪ ej poängsatt"
    if poang.poang >= 70:
        return f"🟢 {poang.poang}"
    if poang.poang >= 40:
        return f"🟡 {poang.poang}"
    return f"🔴 {poang.poang}"


def _visa_annons(annons, status: str, poang, har_korkort: bool) -> None:
    rubrik = f"{_poang_etikett(poang)}  ·  {annons.rubrik} – {annons.arbetsgivare} ({annons.ort})"
    with st.expander(rubrik):
        if poang is not None:
            st.markdown(f"**Bedömning:** {poang.motivering}")
            if poang.varningar:
                st.markdown("**Att tänka på:** " + "; ".join(poang.varningar))
            sprak_text = {"svenska_kravs": "Svenska krävs", "engelska_racker": "Engelska räcker",
                     "okant": "Språkkrav oklart"}.get(poang.sprakkrav, poang.sprakkrav)
            st.caption(f"{sprak_text} · Modell: {poang.modell}")
        st.markdown(
            f"**Anställning:** {annons.anstallning or '–'}  \n"
            f"**Arbetstid:** {annons.arbetstid or '–'}  \n"
            f"**Sista ansökningsdag:** {annons.sista_ansokningsdag or '–'}  \n"
            f"**Yrke:** {annons.yrke or '–'}  \n"
            f"**Publicerad:** {annons.publicerad or '–'}"
        )
        if not har_korkort and "körkort" in (annons.beskrivning or "").lower():
            st.warning("Annonsen nämner körkort. Kontrollera kravet innan du söker.")
        st.markdown(annons.beskrivning or "_Ingen beskrivning._")
        st.link_button("Öppna annonsen på Platsbanken", annons.lank)
        k1, k2 = st.columns(2)
        if status != annonser.STATUS_SPARAD and k1.button("Spara", key=f"spara_{annons.id}"):
            annonser.satt_status(conn, annons.id, annonser.STATUS_SPARAD)
            st.rerun()
        if status != annonser.STATUS_DOLD and k2.button("Dölj", key=f"dolj_{annons.id}"):
            annonser.satt_status(conn, annons.id, annonser.STATUS_DOLD)
            st.rerun()
        if status == annonser.STATUS_SPARAD and st.button("Markera som ansökt", key=f"ansokt_{annons.id}"):
            ansokningar.spara_status(conn, annons.id, ansokningar.ANSOKT)
            st.rerun()


def sida_sok_jobb() -> None:
    st.header("Sök jobb")
    sok = settings.load_sok(conn)
    profil = settings.load_profil(conn)
    modeller = settings.load_modeller(conn)
    if not sok.orter:
        st.warning("Lägg till minst en ort under Sökinställningar först.")
        return
    if not profil.namn and not profil.arbetslivserfarenhet and not profil.cv_text:
        st.info("Tips: fyll i Min profil först, så kan jobben bedömas mot din bakgrund.")

    if not profil.korkort:
        st.caption("Annonser som kräver körkort visas inte, eftersom din profil saknar körkort. "
                   "Bocka i \"Har körkort\" under Min profil om det ändras.")
    st.caption("Söker i Platsbanken (Arbetsförmedlingen) inom "
               f"{sok.radie_km} km från: {', '.join(sok.orter)}")
    k1, k2 = st.columns(2)
    if k1.button("Sök nya jobb", type="primary"):
        with st.spinner("Söker i Platsbanken..."):
            try:
                platser = []
                for ort in sok.orter:
                    plats = geo.geocode(conn, ort)
                    if plats is None:
                        st.warning(f"Hittade inte orten '{ort}'. Kontrollera stavningen.")
                    else:
                        platser.append(plats)
                if platser:
                    hittade = platsbanken.sok_annonser(platser, sok, har_korkort=profil.korkort)
                    nya = annonser.spara_nya(conn, hittade)
                    st.success(f"Hittade {len(hittade)} annonser, varav {nya} nya.")
            except Exception as fel:  # nätverksfel, API-fel
                st.error(f"Sökningen misslyckades: {fel}")

    if k2.button("Bedöm nya annonser med AI"):
        with st.spinner("Bedömer annonser (max 25 åt gången)..."):
            alla = [a for a, _ in annonser.lista(conn, annonser.STATUS_NY)]
            alla += [a for a, _ in annonser.lista(conn, annonser.STATUS_SPARAD)]
            klara, fel = matchning.poangsatt_nya(conn, alla, profil, sok, modeller)
        if klara:
            st.success(f"Bedömde {klara} annonser.")
        for meddelande in fel[:3]:
            st.error(meddelande)

    poang = matchning.hamta_poang(conn)
    # Samma filter för antalen i flikarna som för listorna
    per_status = {
        s: [(a, x) for a, x in annonser.lista(conn, s) if platsbanken.korkort_ok(a, profil.korkort)]
        for s in [annonser.STATUS_NY, annonser.STATUS_SPARAD, annonser.STATUS_DOLD]
    }
    flikar = st.tabs([
        f"Nya ({len(per_status[annonser.STATUS_NY])})",
        f"Sparade ({len(per_status[annonser.STATUS_SPARAD])})",
        f"Dolda ({len(per_status[annonser.STATUS_DOLD])})",
    ])
    for flik, status in zip(flikar, [annonser.STATUS_NY, annonser.STATUS_SPARAD, annonser.STATUS_DOLD]):
        with flik:
            lista = list(per_status[status])
            # Bästa poäng först, onbedömda sist
            lista.sort(key=lambda par: -(poang[par[0].id].poang if par[0].id in poang else -1))
            if not lista:
                st.info("Inga annonser här ännu.")
            for annons, _ in lista[:100]:
                _visa_annons(annons, status, poang.get(annons.id), profil.korkort)


def _ansokan_kort(a, status_val: str) -> None:
    ann = a.annons
    dagar = ansokningar.dagar_kvar(ann.sista_ansokningsdag)
    varning = ""
    if dagar is not None and dagar < 0:
        varning = " · ⛔ Ansökningstiden har gått ut"
    elif dagar is not None and dagar <= 3:
        varning = f" · ⏰ {dagar} dagar kvar"
    rubrik = f"{ansokningar.STATUSAR[a.status]}  ·  {ann.rubrik} – {ann.arbetsgivare} ({ann.ort}){varning}"
    if ansokningar.behover_uppfoljning(a):
        rubrik = "🔔 " + rubrik
    with st.expander(rubrik):
        st.markdown(
            f"**Ansökt:** {a.ansokt_datum or '–'}  \n"
            f"**Sista ansökningsdag:** {ann.sista_ansokningsdag or '–'}  \n"
            f"**Anställning:** {ann.anstallning or '–'} · **Arbetstid:** {ann.arbetstid or '–'}"
        )
        if ansokningar.behover_uppfoljning(a):
            st.info(f"Ansökan skickades för {ansokningar.UPPFOLJNING_EFTER_DAGAR}+ dagar sedan utan svar. "
                    "Överväg att höra av dig.")
        st.link_button("Öppna annonsen på Platsbanken", ann.lank, key=f"lank_{ann.id}_{status_val}")
        nya_status = st.selectbox(
            "Status", list(ansokningar.STATUSAR.keys()),
            index=list(ansokningar.STATUSAR.keys()).index(a.status),
            format_func=ansokningar.STATUSAR.get, key=f"status_{ann.id}_{status_val}",
        )
        datum_val = date.fromisoformat(a.ansokt_datum) if a.ansokt_datum else date.today()
        nytt_datum = st.date_input("Ansökt den", datum_val, key=f"datum_{ann.id}_{status_val}")
        anteckning = st.text_area("Anteckningar", a.anteckning, key=f"anteckning_{ann.id}_{status_val}",
                                  placeholder="T.ex. kontaktperson, intervjutid, nästa steg")
        k1, k2 = st.columns(2)
        if k1.button("Spara", key=f"spara_ans_{ann.id}_{status_val}", type="primary"):
            ansokningar.spara_status(conn, ann.id, nya_status,
                                     ansokt_datum=nytt_datum.isoformat(), anteckning=anteckning)
            st.rerun()
        if k2.button("Ta bort från uppföljningen", key=f"ta_bort_{ann.id}_{status_val}"):
            ansokningar.ta_bort(conn, ann.id)
            st.rerun()


def sida_tracker() -> None:
    st.header("Mina ansökningar")

    # --- Uppföljning ---
    antal = ansokningar.antal_per_status(conn)
    st.subheader("Uppföljning")
    flikar = st.tabs([f"{namn} ({antal.get(s, 0)})" for s, namn in ansokningar.STATUSAR.items()])
    for flik, status in zip(flikar, ansokningar.STATUSAR):
        with flik:
            poster = ansokningar.lista(conn, status)
            if not poster:
                st.info("Inga ansökningar med den här statusen.")
            for a in poster:
                _ansokan_kort(a, status)

    # --- CV och brev ---
    st.divider()
    st.subheader("CV och personligt brev")
    st.caption("Välj en annons för att skapa eller ändra CV och brev.")
    kandidater = [a for a, _ in annonser.lista(conn, annonser.STATUS_SPARAD)]
    kandidater += [a.annons for a in ansokningar.lista(conn)]
    if not kandidater:
        st.info("Spara en annons under Sök jobb först.")
        return

    valda = st.selectbox(
        "Annons", kandidater,
        format_func=lambda a: f"{a.rubrik} – {a.arbetsgivare} ({a.ort})",
    )
    st.link_button("Öppna annonsen på Platsbanken", valda.lank)
    profil = settings.load_profil(conn)
    sok = settings.load_sok(conn)
    modeller = settings.load_modeller(conn)

    sprak_val = st.radio(
        "Språk på dokumenten", ["sv", "en"], horizontal=True,
        format_func={"sv": "Svenska", "en": "Engelska"}.get,
        index=["sv", "en"].index(dokument.sprak_for_annons(valda)),
        key=f"sprak_{valda.id}",
        help="Standard: engelska om annonsen är på engelska, annars svenska.",
    )

    if st.button("Skapa CV och brev med AI", type="primary"):
        with st.spinner("Skriver CV och brev..."):
            try:
                dok = dokument.skapa_dokument(profil, sok, valda, modeller.skriv_modell, sprak=sprak_val)
                dokument.spara(conn, dok)
                st.success("Klart. Granska och ändra texten nedan.")
            except llm.LLMFel as fel:
                st.error(str(fel))

    dok = dokument.hamta(conn, valda.id)
    if dok is None:
        st.info("Inga dokument ännu. Klicka på knappen ovan.")
        return

    with st.form(f"dok_form_{valda.id}"):
        st.subheader("CV")
        profiltext = st.text_area("Profiltext", dok.profiltext, height=90)
        erf_text = st.text_area(
            "Arbetslivserfarenhet", dokument.erfarenhet_till_text(dok.erfarenhet), height=220,
            help="Ett block per jobb. Första raden: Titel | Arbetsgivare | Period. Punkter börjar med '- '.",
        )
        utb_text = st.text_area(
            "Utbildning", dokument.utbildning_till_text(dok.utbildning), height=90,
            help="En rad per examen: Examen | Lärosäte | Period",
        )
        komp = st.text_area("Kompetenser (en per rad)", _text_fran_lista(dok.kompetenser), height=110)
        sprakk = st.text_area("Språk (en per rad)", _text_fran_lista(dok.sprakkunskaper), height=70)
        st.subheader("Personligt brev")
        brev = st.text_area(
            "Brödtext (tre stycken, med tom rad mellan)", dok.brev, height=260,
            help="Hälsning och avslutning läggs till automatiskt i Word-filen.",
        )
        if st.form_submit_button("Spara ändringar", type="primary"):
            dok.profiltext = profiltext.strip()
            dok.erfarenhet = dokument.erfarenhet_fran_text(erf_text)
            dok.utbildning = dokument.utbildning_fran_text(utb_text)
            dok.kompetenser = _lista_fran_text(komp)
            dok.sprakkunskaper = _lista_fran_text(sprakk)
            dok.brev = brev.strip()
            dokument.spara(conn, dok)
            st.success("Ändringarna är sparade.")

    k1, k2 = st.columns(2)
    namn = (profil.namn or "ansokan").replace(" ", "_")
    k1.download_button(
        "Ladda ner CV (Word)", dokument.exportera_cv(profil, dok),
        file_name=f"CV_{namn}_{valda.id}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    k2.download_button(
        "Ladda ner personligt brev (Word)", dokument.exportera_brev(profil, dok),
        file_name=f"Brev_{namn}_{valda.id}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    if dok.modell:
        st.caption(f"Skapad med modellen {dok.modell}. Kontrollera alltid faktauppgifterna innan du skickar.")




SIDOR = {
    "Min profil": sida_profil,
    "Sökinställningar": sida_sok,
    "Sök jobb": sida_sok_jobb,
    "Mina ansökningar": sida_tracker,
    "Inställningar för AI": sida_installningar,
}

with st.sidebar:
    st.markdown(
        "## 💼 JobbSök "
        f"<span style='font-size:0.55em;color:#888;font-weight:400'>v{__version__}</span>",
        unsafe_allow_html=True,
    )
    valt = st.radio("Meny", list(SIDOR.keys()), label_visibility="collapsed")

SIDOR[valt]()
