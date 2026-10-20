import json
from pathlib import Path

import pytest

from jobbsok import llm, matchning
from jobbsok.platsbanken import Annons
from jobbsok.settings import Modeller, Profil, Sokinstallningar
from jobbsok.storage import connect

FIXTURE = Path(__file__).parent / "fixtures" / "annons.json"


def _annons() -> Annons:
    return Annons.fran_api(json.loads(FIXTURE.read_text(encoding="utf-8")))


def _profil() -> Profil:
    return Profil(
        namn="Testperson", epost="hemlig@example.se", telefon="070-1234567",
        ort="Solna", kompetenser=["AutoCAD"], sprak=["Svenska"], korkort=True,
        cv_text="Byggingenjör, KTH",
    )


def _sok() -> Sokinstallningar:
    return Sokinstallningar(orter=["Solna"], radie_km=30, yrken=["bygg"])


def _fake_svar(poang=72, passar="bra"):
    def chatt(messages, modell, **kw):
        return json.dumps({
            "poang": poang, "passar": passar, "motivering": "Bra match.",
            "sprakkrav": "okant", "varningar": ["Kräver körkort"],
        })
    return chatt


def test_privacy_kontaktuppgifter_skickas_inte():
    text = matchning.bygg_profiltext(_profil(), _sok())
    assert "hemlig@example.se" not in text
    assert "070-1234567" not in text
    assert "Solna" in text and "AutoCAD" in text


def test_poangsatt_en_tolkar_svar_och_begransar_poang():
    p = matchning.poangsatt_en(_profil(), _sok(), _annons(), "m", chatt=_fake_svar(poang=150))
    assert p.poang == 100
    assert p.passar == "bra"
    assert p.varningar == ["Kräver körkort"]
    assert p.modell == "m"


def test_ogiltig_poang_ger_fel():
    def chatt(messages, modell, **kw):
        return '{"poang": "mycket bra"}'
    with pytest.raises(llm.LLMFel):
        matchning.poangsatt_en(_profil(), _sok(), _annons(), "m", chatt=chatt)


def test_poangsatt_nya_sparar_och_hoppar_over_befintliga(tmp_path):
    conn = connect(tmp_path / "t.sqlite3")
    a = _annons()
    klara, fel = matchning.poangsatt_nya(conn, [a], _profil(), _sok(), Modeller(), chatt=_fake_svar())
    assert klara == 1 and fel == []
    anrop = []

    def chatt(*args, **kw):
        anrop.append(1)
        return _fake_svar()(*args, **kw)
    klara, fel = matchning.poangsatt_nya(conn, [a], _profil(), _sok(), Modeller(), chatt=chatt)
    assert klara == 0 and anrop == []  # redan poängsatt, inget nytt anrop
    assert matchning.hamta_poang(conn)[a.id].poang == 72


def test_fatalt_fel_avbryter_direkt(tmp_path):
    conn = connect(tmp_path / "t.sqlite3")
    a = _annons()
    b = Annons(**{**a.__dict__, "id": "2"})
    anrop = []

    def chatt(*args, **kw):
        anrop.append(1)
        raise llm.LLMFatalFel("Nyckeln godkändes inte (401).")
    klara, fel = matchning.poangsatt_nya(conn, [a, b], _profil(), _sok(), Modeller(), chatt=chatt)
    assert klara == 0 and len(fel) == 1 and len(anrop) == 1


def test_parsa_json_med_kodblock():
    assert llm.parsa_json('```json\n{"poang": 5}\n```') == {"poang": 5}
    with pytest.raises(llm.LLMFel):
        llm.parsa_json("inget json här")


def test_http_fel_klassas():
    assert llm._forklara_http_fel(401, "", "m").startswith("OpenRouter-nyckeln")
    assert "finns inte" in llm._forklara_http_fel(404, "", "x/y")
