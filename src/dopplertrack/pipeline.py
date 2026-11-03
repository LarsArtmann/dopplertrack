"""High-level pipeline steps that the CLI and notebooks share."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd

from .adsb import AircraftTypes, Trace, load_region, load_traces, save_traces
from .audio import Spectrogram, compute_spectrogram, load_audio
from .doppler import speed_of_sound
from .score import EventWindow, locked_score
from .search import Grid, Segment, build_segments, cpa_table, pair_candidates, save_cpa_table, load_cpa_table
from .terrain import Terrain
from .tracks import EventFit, fit_event


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def make_spectrogram(audio_path, out_path, hop_s=0.25, fmin=40, fmax=450, nperseg=8192, whiten_window_s=600):
    x, sr = load_audio(audio_path)
    sp = compute_spectrogram(x, sr, nperseg=nperseg, hop_s=hop_s, fmin=fmin, fmax=fmax, whiten_window_s=whiten_window_s)
    sp.save(out_path)
    return sp


def extract_region(archive_dir, bbox, out_path, prop_only=True, workers=None) -> list[Trace]:
    log(f"scanning {archive_dir} for traces in {bbox}")
    traces = load_region(archive_dir, bbox, workers=workers)
    log(f"{len(traces)} traces touch the region")
    if prop_only:
        types = AircraftTypes()
        traces = [t for t in traces if types.is_prop(t.typ)]
        log(f"{len(traces)} after dropping known jets")
    save_traces(traces, out_path)
    return traces


def run_search(sp: Spectrogram, ev1: EventFit, ev2: EventFit, traces: list[Trace], grid: Grid,
               harmonics=(1, 1), tol_s=6.0, v_tol=0.35, d_tol=(0.4, 2.5), silence_d_m=6000.0,
               max_range_m=12000.0, c=None, top_pairs=None, progress=True,
               cpa_cache=None) -> tuple[pd.DataFrame, list[Segment]]:
    """Rank grid points for a two-event recording.

    cpa_cache: optional .npz path. The (grid point, flight) CPA table depends only on the grid,
    the traces and max_range, not on the events, and is the slow part; with a path given it is
    loaded if present and valid for this grid/traces, else computed and saved."""
    c = speed_of_sound() if c is None else c
    e0, e1 = grid.enu[:, 0].min() - max_range_m, grid.enu[:, 0].max() + max_range_m
    n0, n1 = grid.enu[:, 1].min() - max_range_m, grid.enu[:, 1].max() + max_range_m
    segs = build_segments(traces, grid.lat0, grid.lon0, clip_enu=(e0, e1, n0, n1))
    log(f"{len(segs)} airborne segments; grid of {len(grid)} points")
    cpa = None
    fp = {"grid": (len(grid), float(grid.lat0), float(grid.lon0), float(grid.lat.min()), float(grid.lon.max())),
          "segs": (len(segs), int(sum(len(s.t) for s in segs))), "max_range_m": float(max_range_m), "c": float(c)}
    if cpa_cache and os.path.exists(cpa_cache):
        cpa = load_cpa_table(cpa_cache, fp)
        log(f"loaded CPA table from {cpa_cache}" if cpa is not None else f"{cpa_cache} is for a different grid/traces; recomputing")
    if cpa is None:
        cpa = cpa_table(grid, segs, max_range_m=max_range_m, c=c)
        if cpa_cache:
            save_cpa_table(cpa_cache, cpa, fp)
    log(f"{len(cpa)} (point, flight) CPA records")
    dt = ev2.t_cpa - ev1.t_cpa
    pairs = pair_candidates(cpa, dt, tol_s=tol_s,
                            v1=(ev1.v * (1 - v_tol), ev1.v * (1 + v_tol)), d1=(ev1.d * d_tol[0], ev1.d * d_tol[1]),
                            v2=(ev2.v * (1 - v_tol), ev2.v * (1 + v_tol)), d2=(ev2.d * d_tol[0], ev2.d * d_tol[1]),
                            silence_d_m=silence_d_m)
    log(f"{len(pairs)} candidate (point, flight1, flight2) triples after offset + silence filters")
    w1 = EventWindow.from_fit(sp, ev1, harmonics[0]); w2 = EventWindow.from_fit(sp, ev2, harmonics[1])
    out = []
    t0 = time.time()
    for k, p in enumerate(pairs.itertuples()):
        tot, s1, s2, sh = locked_score(w1, w2, segs[p.seg1], segs[p.seg2], grid.enu[p.gidx], float(p.t_heard1), c=c)
        out.append((p.gidx, grid.lat[p.gidx], grid.lon[p.gidx], p.seg1, p.seg2, segs[p.seg1].icao, segs[p.seg2].icao, p.t_heard1, p.d1, p.v1, p.d2, p.v2, tot, s1, s2, sh))
        if progress and (k + 1) % 500 == 0:
            log(f"scored {k + 1}/{len(pairs)} ({(time.time() - t0) / (k + 1) * 1000:.0f} ms each)")
    cols = ["gidx", "lat", "lon", "seg1", "seg2", "icao1", "icao2", "t_heard1", "d1", "v1", "d2", "v2", "score", "s1", "s2", "shift"]
    res = pd.DataFrame(out, columns=cols).sort_values("score", ascending=False).reset_index(drop=True)
    return res, segs


def refine(sp, ev1, ev2, segs, res_row, spacing_m=50.0, half_m=400.0, harmonics=(1, 1), elevation=None, c=None):
    """Fine grid around one result row for one flight pair."""
    c = speed_of_sound() if c is None else c
    lat, lon = float(res_row.lat), float(res_row.lon)
    dlat = half_m / 111320.0; dlon = half_m / (111320.0 * np.cos(np.radians(lat)))
    g = Grid.make(lat - dlat, lat + dlat, lon - dlon, lon + dlon, spacing_m, elevation)
    # re-express grid in the segments' ENU frame (segments were built on the search grid origin)
    from .geo import lla_to_enu
    seg1, seg2 = segs[int(res_row.seg1)], segs[int(res_row.seg2)]
    w1 = EventWindow.from_fit(sp, ev1, harmonics[0]); w2 = EventWindow.from_fit(sp, ev2, harmonics[1])
    rows = []
    for i in range(len(g)):
        obs = lla_to_enu(g.lat[i], g.lon[i], g.elev[i], res_row.lat0, res_row.lon0)
        d = np.linalg.norm(seg1.enu - obs, axis=1); j = int(np.argmin(d)); t_heard1 = seg1.t[j] + d[j] / c
        tot, s1, s2, sh = locked_score(w1, w2, seg1, seg2, obs, float(t_heard1), c=c)
        rows.append((g.lat[i], g.lon[i], tot, s1, s2, sh))
    return pd.DataFrame(rows, columns=["lat", "lon", "score", "s1", "s2", "shift"]).sort_values("score", ascending=False).reset_index(drop=True)


def run_single_search(sp: Spectrogram, ev: EventFit, traces: list[Trace], grid: Grid, t_cpa_unix: float,
                      tol_s: float = 30.0, harmonics: int = 1, v_tol=0.35, d_tol=(0.4, 2.5),
                      max_range_m=12000.0, c=None) -> tuple[pd.DataFrame, list[Segment]]:
    """One event whose absolute time is known (±tol_s): rank grid points by how well the
    curve they would hear from each nearby flight matches the spectrogram."""
    from .score import single_score
    c = speed_of_sound() if c is None else c
    e0, e1 = grid.enu[:, 0].min() - max_range_m, grid.enu[:, 0].max() + max_range_m
    n0, n1 = grid.enu[:, 1].min() - max_range_m, grid.enu[:, 1].max() + max_range_m
    segs = build_segments(traces, grid.lat0, grid.lon0, clip_enu=(e0, e1, n0, n1))
    # only segments alive around the event time
    keep = [s for s in segs if s.t[0] - 300 <= t_cpa_unix <= s.t[-1] + 300]
    log(f"{len(keep)} of {len(segs)} segments overlap the event time")
    cpa = cpa_table(grid, keep, max_range_m=max_range_m, c=c)
    m = cpa[(cpa.t_heard - t_cpa_unix).abs() <= tol_s]
    m = m[m.v.between(ev.v * (1 - v_tol), ev.v * (1 + v_tol)) & m.d.between(ev.d * d_tol[0], ev.d * d_tol[1])]
    log(f"{len(m)} candidate (point, flight) pairs")
    w = EventWindow.from_fit(sp, ev, harmonics)
    out = []
    for p in m.itertuples():
        s = single_score(w, keep[p.seg], grid.enu[p.gidx], float(p.t_heard), c=c)
        out.append((p.gidx, grid.lat[p.gidx], grid.lon[p.gidx], p.seg, keep[p.seg].icao, p.t_heard, p.d, p.v, s))
    res = pd.DataFrame(out, columns=["gidx", "lat", "lon", "seg", "icao", "t_heard", "d", "v", "score"]).sort_values("score", ascending=False).reset_index(drop=True)
    return res, keep
