"""CLI argument contracts and the Agg-backend plotting path, offline."""

import matplotlib

matplotlib.use("Agg")

import pytest

from dopplertrack.adsb import AircraftTypes
from dopplertrack.cli import main


def test_search_rejects_one_event_without_utc():
    with pytest.raises(SystemExit) as exc:
        main(["search", "s.npz", "--events", "a.json", "--day", "d.npz", "--out", "o.csv"])
    assert exc.value.code == 2


def test_search_rejects_two_events_with_utc():
    with pytest.raises(SystemExit) as exc:
        main(
            [
                "search", "s.npz",
                "--events", "a.json", "b.json",
                "--utc", "1700000000",
                "--day", "d.npz",
                "--out", "o.csv",
            ]
        )
    assert exc.value.code == 2


def test_bbox_requires_four_numbers(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["coverage", "2026-11-12", "48.0", "49.0", "10.0"])
    assert exc.value.code == 2
    assert "LATMIN" in capsys.readouterr().err


def test_aircraft_types_classify_offline(tmp_path):
    p = tmp_path / "doc8643.csv"
    p.write_text("Designator,EngineType\nC172,Piston\nB738,Turbofan\nDR40,Piston\n")
    types = AircraftTypes(path=p)
    assert types.is_prop("C172") and types.is_prop("DR40")
    assert not types.is_prop("B738")
    assert types.is_prop("ZZZ", unknown_ok=True) is True
    assert types.is_prop("ZZZ", unknown_ok=False) is False
    assert types.engine(None) is None


def test_plot_event_fit_renders_under_agg(tmp_path):
    import matplotlib.pyplot as plt
    import numpy as np

    from dopplertrack.audio import Spectrogram
    from dopplertrack.plots import plot_event_fit
    from dopplertrack.tracks import EventFit

    t = np.arange(0.0, 60.0, 0.25)
    f = np.arange(40.0, 450.0, 5.0)
    rng = np.random.default_rng(7)
    S = rng.normal(0.0, 1.0, (len(f), len(t)))
    sp = Spectrogram(t, f, S)
    fit = EventFit(
        t_cpa=30.0,
        t_cpa_emit=29.6,
        f0=120.0,
        v=80.0,
        d=400.0,
        t_start=10.0,
        t_end=50.0,
        score=3.0,
        f_pre=160.0,
        f_post=90.0,
    )
    ax = plot_event_fit(sp, fit, harmonics=1)
    assert "ideal fit" in ax.get_title()
    plt.close(ax.figure)
