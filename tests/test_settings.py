from jobbsok import settings
from jobbsok.storage import connect


def _conn(tmp_path):
    return connect(tmp_path / "test.sqlite3")


def test_profil_roundtrip(tmp_path):
    conn = _conn(tmp_path)
    p = settings.Profil(namn="Anna", kompetenser=["AutoCAD"], sprak=["Svenska (modersmål)"])
    settings.save_profil(conn, p)
    assert settings.load_profil(conn) == p


def test_standardvarden_nar_inget_sparats(tmp_path):
    conn = _conn(tmp_path)
    assert settings.load_profil(conn) == settings.Profil()
    assert settings.load_sok(conn).radie_km == 30


def test_sok_roundtrip_med_svenska_tecken(tmp_path):
    conn = _conn(tmp_path)
    s = settings.Sokinstallningar(orter=["Göteborg", "Malmö"], radie_km=50)
    settings.save_sok(conn, s)
    assert settings.load_sok(conn) == s


def test_okanda_falt_ignoreras(tmp_path):
    conn = _conn(tmp_path)
    from jobbsok.storage import set_setting
    set_setting(conn, settings.SEARCH_KEY, {"radie_km": 10, "gammalt_falt": 1})
    assert settings.load_sok(conn).radie_km == 10
