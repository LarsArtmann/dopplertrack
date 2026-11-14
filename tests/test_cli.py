import pytest

from dopplertrack.cli import main


def test_version_flag_prints_package_version(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert out.startswith("dopplertrack ")
    assert out.strip() == "dopplertrack 0.3.0"
