"""Property test for the pair join: whatever buckets brute force finds for a (pair, bucket)
under the documented necessary condition, pair_join must report - it may over-approximate,
never miss. Bucket-edge deltas (exact multiples of the 10 s bucket and off-by-one-second
deltas) are exercised explicitly."""

import numpy as np
import pytest

from dopplertrack import search
from dopplertrack.adsb import Trace
from dopplertrack.geo import enu_to_lla

C = 340.0
LAT0, LON0 = 48.35, 11.0
T0 = 1_700_000_000.0
W = 10.0


def _trace(icao, t, enu, gs):
    lat, lon, alt = enu_to_lla(enu[:, 0], enu[:, 1], enu[:, 2], LAT0, LON0)
    return Trace(
        icao, None, "C172", "synthetic", t, lat, lon, alt, np.full_like(t, gs), np.zeros(len(t), bool)
    )


def _cross(icao, t_cpa, p_cpa, vel, span=240.0):
    t = T0 + np.arange(t_cpa - span, t_cpa + span, 1.0)
    tau = (t - (T0 + t_cpa))[:, None]
    enu = np.asarray(p_cpa, float)[None, :] + np.asarray(vel, float)[None, :] * tau
    return _trace(icao, t, enu, np.linalg.norm(vel))


def _gates():
    return dict(v1=(80.0, 120.0), d1=(1000.0, 4000.0), v2=(80.0, 120.0), d2=(1000.0, 4000.0))


def _brute_pairs(idx, dt_heard, gates, tol_s=6.0, v_slack=0.1):
    """Every (seg1, seg2, flight-1-side bucket) the documented necessary condition allows."""
    v1g = (gates["v1"][0] * (1 - v_slack), gates["v1"][1] * (1 + v_slack))
    v2g = (gates["v2"][0] * (1 - v_slack), gates["v2"][1] * (1 + v_slack))
    lo, hi = search.lag_range(dt_heard, gates["d1"], gates["d2"], C, tol_s)
    R = gates["d1"][1] + gates["d2"][1] + (v1g[1] + v2g[1]) * W / 2
    A = (idx.sspd >= v1g[0]) & (idx.sspd <= v1g[1])
    B = (idx.sspd >= v2g[0]) & (idx.sspd <= v2g[1])
    found = set()
    for k in np.unique(idx.sb):
        tk = idx.bucket_time(int(k))
        kb_lo, kb_hi = int(np.floor((tk - W / 2 + lo) / W)), int(np.floor((tk + W / 2 + hi) / W))
        for kb in range(kb_lo, kb_hi + 1):
            sa = idx.ss[(idx.sb == k) & A]
            sb2 = idx.ss[(idx.sb == kb) & B]
            pa = idx.spos[(idx.sb == k) & A]
            pb = idx.spos[(idx.sb == kb) & B]
            if not len(sa) or not len(sb2):
                continue
            dist = np.linalg.norm(pa[:, None, :] - pb[None, :, :], axis=2)
            m = dist <= R
            for i, j in zip(*np.nonzero(m)):
                if sa[i] != sb2[j]:
                    found.add((int(sa[i]), int(sb2[j]), int(k)))
    return found


@pytest.mark.parametrize("dt_heard", [100.0, 110.0, 120.0, 105.0, 117.0])
def test_pair_join_is_complete_against_brute_force(dt_heard):
    fa = _cross("aaa001", 300.0, (0.0, 2500.0, 1200.0), (100.0, 0.0, 0.0))
    fb = _cross("aaa002", 300.0 + dt_heard, (2500.0, 0.0, 1100.0), (0.0, 100.0, 0.0))
    idx = search.DayIndex.build([fa, fb], LAT0, LON0)
    gates = _gates()
    pairs = search.pair_join(idx, dt_heard, c=C, **gates)
    got = {(int(r.seg1), int(r.seg2)): (int(r.b_min), int(r.b_max)) for r in pairs.itertuples()}
    for s1, s2, k in _brute_pairs(idx, dt_heard, gates):
        assert (s1, s2) in got, f"pair ({s1},{s2}) missed entirely at dt={dt_heard}"
        assert got[(s1, s2)][0] <= k <= got[(s1, s2)][1], f"bucket {k} outside reported range"
