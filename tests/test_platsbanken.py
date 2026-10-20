import json
from pathlib import Path

from jobbsok import annonser, platsbanken
from jobbsok.platsbanken import Annons, Plats, bygg_frageparametrar, passar_timmar
from jobbsok.settings import Sokinstallningar
from jobbsok.storage import connect

FIXTURE = Path(__file__).parent / "fixtures" / "annons.json"


def _annons_fixture() -> Annons:
    return Annons.fran_api(json.loads(FIXTURE.read_text(encoding="utf-8")))


def test_fran_api_mappar_falt():
    a = _annons_fixture()
    assert a.id == "31621687"
    assert a.rubrik.startswith("PERSONLIGA ASSISTENTER")
    assert a.ort == "Örkelljunga"
    assert a.lan == "Skåne län"
    assert a.arbetstid == "Deltid"
    assert a.lank.startswith("https://arbetsformedlingen.se/platsbanken/annonser/")
    assert len(a.sista_ansokningsdag) == 10


def test_deltid_fragor_innehaller_parttime_filter():
    sok = Sokinstallningar(orter=["Solna"], radie_km=30, endast_deltid_och_tillfalligt=True)
    fragor = bygg_frageparametrar([Plats("Solna", 59.36, 18.0)], sok)
    assert len(fragor) == 2
    assert ("parttime.max", "99") in fragor[0]
    typer = [v for k, v in fragor[1] if k == "employment-type"]
    assert "1paU_aCR_nGn" in typer and "Jh8f_q9J_pbJ" in typer


def test_utan_deltidsfilter_en_fraga_per_plats():
    sok = Sokinstallningar(orter=["A", "B"], endast_deltid_och_tillfalligt=False)
    platser = [Plats("A", 1.0, 2.0), Plats("B", 3.0, 4.0)]
    fragor = bygg_frageparametrar(platser, sok)
    assert len(fragor) == 2
    assert ("position", "1.0,2.0") in fragor[0]
    assert ("position.radius", "30") in fragor[0]


def test_yrken_blir_or_fritext():
    sok = Sokinstallningar(yrken=["bygg", "lager"], endast_deltid_och_tillfalligt=False)
    fraga = bygg_frageparametrar([Plats("A", 1, 2)], sok)[0]
    assert ("q", "bygg lager") in fraga


def test_timfilter():
    a = _annons_fixture()
    a.omfattning_min, a.omfattning_max = 10, 50  # 10–50 % (4–20 h)
    assert passar_timmar(a, Sokinstallningar(timmar_min=0, timmar_max=10))
    assert not passar_timmar(a, Sokinstallningar(timmar_min=30, timmar_max=40))
    a.omfattning_min = None
    assert passar_timmar(a, Sokinstallningar(timmar_min=30, timmar_max=40))


def test_annonser_lagras_och_behaller_status(tmp_path):
    conn = connect(tmp_path / "t.sqlite3")
    a = _annons_fixture()
    assert annonser.spara_nya(conn, [a]) == 1
    annonser.satt_status(conn, a.id, annonser.STATUS_SPARAD)
    assert annonser.spara_nya(conn, [a]) == 0  # ingen dubblett
    sparade = annonser.lista(conn, annonser.STATUS_SPARAD)
    assert len(sparade) == 1 and sparade[0][0].rubrik == a.rubrik
    assert annonser.antal_per_status(conn) == {"sparad": 1}


def test_utan_korkort_skickas_filter_till_api():
    sok = Sokinstallningar(orter=["A"], endast_deltid_och_tillfalligt=False)
    fraga = bygg_frageparametrar([Plats("A", 1, 2)], sok, har_korkort=False)[0]
    assert ("driving-license-required", "false") in fraga


def test_med_korkort_inget_korkortsfilter():
    sok = Sokinstallningar(orter=["A"], endast_deltid_och_tillfalligt=False)
    fraga = bygg_frageparametrar([Plats("A", 1, 2)], sok, har_korkort=True)[0]
    assert not any(k == "driving-license-required" for k, _ in fraga)


def test_korkort_ok():
    a = _annons_fixture()
    a.korkort_kravs = True
    assert not platsbanken.korkort_ok(a, False)
    assert platsbanken.korkort_ok(a, True)
    assert platsbanken.korkort_ok(a, None)
    a.korkort_kravs = False
    assert platsbanken.korkort_ok(a, False)
