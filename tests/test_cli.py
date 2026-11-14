import json

import pytest

from dopplertrack.cli import CliError, load_event, main


def test_version_flag_prints_package_version(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert out.startswith("dopplertrack ")
    assert out.strip() == "dopplertrack 0.3.0"


def test_missing_input_file_exits_1_with_friendly_error(capsys, tmp_path):
    ghost = tmp_path / "no-such-recording.mp4"
    with pytest.raises(SystemExit) as exc:
        main(["spectrogram", str(ghost), str(tmp_path / "out.npz")])
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert err.startswith("error:")
    assert "Nothing was written" in err
    assert "fix:" in err


def test_load_event_invalid_json_names_path_and_position(tmp_path):
    p = tmp_path / "ev.json"
    p.write_text('{"t_cpa": ')
    with pytest.raises(CliError) as exc:
        load_event(str(p))
    assert str(p) in str(exc.value)
    assert "not valid JSON" in str(exc.value)


def test_load_event_non_object_json_explains_expected_shape(tmp_path):
    p = tmp_path / "ev.json"
    p.write_text(json.dumps([]))
    with pytest.raises(CliError) as exc:
        load_event(str(p))
    assert "EventFit fields" in str(exc.value)
    p.write_text(json.dumps({"nonsense": 1}))
    with pytest.raises(CliError) as exc:
        load_event(str(p))
    assert "EventFit fields" in str(exc.value)
