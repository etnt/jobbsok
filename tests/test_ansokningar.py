import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from jobbsok import annonser, ansokningar
from jobbsok.platsbanken import Annons
from jobbsok.storage import connect

FIXTURE = Path(__file__).parent / "fixtures" / "annons.json"


@pytest.fixture
def conn(tmp_path):
    c = connect(tmp_path / "t.sqlite3")
    a = Annons.fran_api(json.loads(FIXTURE.read_text(encoding="utf-8")))
    annonser.spara_nya(c, [a])
    return c


def _id(conn):
    return annonser.lista(conn, annonser.STATUS_NY)[0][0].id


def test_ansokt_satter_datum_och_flyttar_annonsen(conn):
    aid = _id(conn)
    ansokningar.spara_status(conn, aid, ansokningar.ANSOKT)
    poster = ansokningar.lista(conn, ansokningar.ANSOKT)
    assert len(poster) == 1
    assert poster[0].ansokt_datum == date.today().isoformat()
    assert annonser.antal_per_status(conn).get(annonser.STATUS_ANSOKT) == 1
    assert annonser.lista(conn, annonser.STATUS_SPARAD) == []


def test_datum_och_anteckning_behalls_vid_statusbyte(conn):
    aid = _id(conn)
    ansokningar.spara_status(conn, aid, ansokningar.ANSOKT, ansokt_datum="2026-01-05", anteckning="Ring på måndag")
    ansokningar.spara_status(conn, aid, ansokningar.INTERVJU)
    p = ansokningar.lista(conn, ansokningar.INTERVJU)[0]
    assert p.ansokt_datum == "2026-01-05"
    assert p.anteckning == "Ring på måndag"


def test_ogiltig_status_ger_fel(conn):
    with pytest.raises(ValueError):
        ansokningar.spara_status(conn, _id(conn), "konstig")


def test_ta_bort_lagger_tillbaka_som_sparad(conn):
    aid = _id(conn)
    ansokningar.spara_status(conn, aid, ansokningar.ANSOKT)
    ansokningar.ta_bort(conn, aid)
    assert ansokningar.lista(conn) == []
    assert [a.id for a, _ in annonser.lista(conn, annonser.STATUS_SPARAD)] == [aid]


def test_antal_per_status(conn):
    aid = _id(conn)
    ansokningar.spara_status(conn, aid, ansokningar.AVSLAG)
    assert ansokningar.antal_per_status(conn) == {"avslag": 1}


def test_dagar_kvar():
    idag = date(2026, 3, 10)
    assert ansokningar.dagar_kvar("2026-03-13T23:59:59", idag) == 3
    assert ansokningar.dagar_kvar("2026-03-01", idag) == -9
    assert ansokningar.dagar_kvar("", idag) is None
    assert ansokningar.dagar_kvar("ogiltigt", idag) is None


def test_uppfoljning_efter_14_dagar(conn):
    aid = _id(conn)
    idag = date(2026, 3, 30)
    gammal = (idag - timedelta(days=20)).isoformat()
    ansokningar.spara_status(conn, aid, ansokningar.ANSOKT, ansokt_datum=gammal)
    a = ansokningar.lista(conn, ansokningar.ANSOKT)[0]
    assert ansokningar.behover_uppfoljning(a, idag)
    ny = (idag - timedelta(days=3)).isoformat()
    ansokningar.spara_status(conn, aid, ansokningar.ANSOKT, ansokt_datum=ny)
    a = ansokningar.lista(conn, ansokningar.ANSOKT)[0]
    assert not ansokningar.behover_uppfoljning(a, idag)


def test_ingen_uppfoljning_for_avslag(conn):
    aid = _id(conn)
    ansokningar.spara_status(conn, aid, ansokningar.AVSLAG, ansokt_datum="2020-01-01")
    a = ansokningar.lista(conn, ansokningar.AVSLAG)[0]
    assert not ansokningar.behover_uppfoljning(a)
