from aperture_scholar.cli import main


def test_check(monkeypatch, capsys):
    assert main(["check"]) == 0
    assert "not implemented" in capsys.readouterr().out


def test_live_run_fails_honestly(capsys):
    assert main(["run"]) == 2
    assert "not wired" in capsys.readouterr().err


def test_offline_demo(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("APERTURE_DATABASE_PATH", str(tmp_path / "demo.sqlite3"))
    assert main(["demo"]) == 0
    assert '"persisted": true' in capsys.readouterr().out
