from pathlib import Path

import numpy as np

from dopplertrack import adsb

HERE = Path(__file__).parent


def test_parse_readsb_trace():
    tr = adsb.parse_trace_file(HERE / "data" / "trace_full_a2f38b.json")
    assert tr.icao == "a2f38b" and tr.typ == "SR20" and tr.reg == "N29EF"
    assert len(tr) > 500
    assert np.all(np.diff(tr.t) >= 0)
    assert tr.lat.min() > 39 and tr.lat.max() < 42 and tr.lon.min() > -76
    air = ~tr.on_ground
    assert np.nanmax(tr.alt[air]) > 300  # metres
    assert np.nanmax(tr.gs[air]) > 40  # m/s
    segs = tr.segments()
    assert segs and all(not tr.on_ground[s.start] for s in segs)
    t, enu = tr.enu(segs[0], 40.1, -74.1)
    assert enu.shape == (len(t), 3) and np.all(np.isfinite(enu))


def test_save_load_round_trip(tmp_path):
    tr = adsb.parse_trace_file(HERE / "data" / "trace_full_a2f38b.json")
    adsb.save_traces([tr], tmp_path / "t.npz")
    back = adsb.load_traces(tmp_path / "t.npz")[0]
    assert back.icao == tr.icao and back.typ == tr.typ
    assert np.allclose(back.t, tr.t) and np.array_equal(back.on_ground, tr.on_ground)
