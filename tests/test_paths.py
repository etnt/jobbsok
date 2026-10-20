import sys
from pathlib import Path

from jobbsok import storage


def test_standard_data_dir_i_projekt(monkeypatch, tmp_path):
    monkeypatch.delenv("JOBBSOK_DATA", raising=False)
    monkeypatch.setattr(storage, "APP_DIR", tmp_path)
    monkeypatch.setattr(sys, "frozen", False, raising=False)
    assert storage.data_dir() == tmp_path / "data"


def test_installerad_app_anvander_appdata(monkeypatch, tmp_path):
    monkeypatch.delenv("JOBBSOK_DATA", raising=False)
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    assert storage.data_dir() == tmp_path / "JobbSok" / "data"
    assert storage.data_dir().is_dir()


def test_env_fil_bredvid_programmet_nar_installerad(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "JobbSok.exe"))
    assert storage.env_fil() == tmp_path / ".env"


def test_jobbsok_data_har_fortur(monkeypatch, tmp_path):
    monkeypatch.setenv("JOBBSOK_DATA", str(tmp_path / "min"))
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    assert storage.data_dir() == tmp_path / "min"
