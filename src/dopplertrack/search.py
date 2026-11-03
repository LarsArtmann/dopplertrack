"""Candidate observer generation: who could have heard which flight, when, how far."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .adsb import Trace
from .doppler import speed_of_sound
from .geo import lla_to_enu, enu_to_lla


@dataclass
class Grid:
    lat: np.ndarray
    lon: np.ndarray
    elev: np.ndarray
    enu: np.ndarray        # (G,3) relative to (lat0, lon0, 0)
    lat0: float
    lon0: float

    @classmethod
    def make(cls, lat_min, lat_max, lon_min, lon_max, spacing_m, elevation_fn=None):
        lat0, lon0 = (lat_min + lat_max) / 2, (lon_min + lon_max) / 2
        dlat = spacing_m / 111320.0
        dlon = spacing_m / (111320.0 * np.cos(np.radians(lat0)))
        la, lo = np.meshgrid(np.arange(lat_min, lat_max, dlat), np.arange(lon_min, lon_max, dlon), indexing="ij")
        la, lo = la.ravel(), lo.ravel()
        el = elevation_fn(la, lo) if elevation_fn else np.zeros_like(la)
        el = np.maximum(el, 0.0)
        return cls(la, lo, el, lla_to_enu(la, lo, el, lat0, lon0), lat0, lon0)

    @classmethod
    def points(cls, lat, lon, elev, lat0=None, lon0=None):
        lat = np.atleast_1d(np.asarray(lat, float)); lon = np.atleast_1d(np.asarray(lon, float)); elev = np.atleast_1d(np.asarray(elev, float))
        lat0 = float(lat.mean()) if lat0 is None else lat0; lon0 = float(lon.mean()) if lon0 is None else lon0
        return cls(lat, lon, elev, lla_to_enu(lat, lon, elev, lat0, lon0), lat0, lon0)

    def __len__(self):
        return len(self.lat)


@dataclass
class Segment:
    trace_idx: int
    icao: str
    t: np.ndarray       # emission times (unix s), 1 Hz
    enu: np.ndarray     # (N,3)
    speed: np.ndarray   # (N,) m/s


def build_segments(traces: list[Trace], lat0: float, lon0: float, dt: float = 1.0, min_len: int = 20,
                   clip_enu: tuple[float, float, float, float] | None = None) -> list[Segment]:
    """1 Hz ENU segments. clip_enu=(e_min, e_max, n_min, n_max) keeps only the parts of a
    track inside that box (split where it leaves), which bounds memory in cpa_table."""
    segs = []
    for i, tr in enumerate(traces):
        for sl in tr.segments():
            t, enu = tr.enu(sl, lat0, lon0, dt)
            if len(t) < min_len or not np.all(np.isfinite(enu)):
                continue
            vel = np.gradient(enu, t, axis=0)
            spd = np.linalg.norm(vel, axis=1)
            if clip_enu is None:
                segs.append(Segment(i, tr.icao, t, enu, spd))
                continue
            inside = (enu[:, 0] >= clip_enu[0]) & (enu[:, 0] <= clip_enu[1]) & (enu[:, 1] >= clip_enu[2]) & (enu[:, 1] <= clip_enu[3])
            if not inside.any():
                continue
            edges = np.flatnonzero(np.diff(inside.astype(int))) + 1
            for a, b in zip(np.r_[0, edges], np.r_[edges, len(t)]):
                if inside[a] and b - a >= min_len:
                    segs.append(Segment(i, tr.icao, t[a:b], enu[a:b], spd[a:b]))
    return segs


def cpa_table(grid: Grid, segs: list[Segment], max_range_m: float = 10000.0, c: float | None = None,
              chunk: int = 20000) -> pd.DataFrame:
    """For every (grid point, segment) within max_range: CPA emission time, heard time,
    slant distance and ground-track speed at CPA."""
    c = speed_of_sound() if c is None else c
    rows = []
    for si, s in enumerate(segs):
        lo = s.enu.min(0)[:2] - max_range_m; hi = s.enu.max(0)[:2] + max_range_m
        m = np.where((grid.enu[:, 0] >= lo[0]) & (grid.enu[:, 0] <= hi[0]) & (grid.enu[:, 1] >= lo[1]) & (grid.enu[:, 1] <= hi[1]))[0]
        if len(m) == 0:
            continue
        for k in range(0, len(m), chunk):
            idx = m[k:k + chunk]
            g = grid.enu[idx]                                         # (G,3)
            nstep = max(1, int(2e7 // max(len(idx), 1)))
            best = np.full(len(idx), np.inf); j = np.zeros(len(idx), int)
            for n0 in range(0, len(s.t), nstep):
                d2 = ((g[:, None, :] - s.enu[None, n0:n0 + nstep, :]) ** 2).sum(-1)    # (G,n)
                jj = np.argmin(d2, axis=1)
                dd = d2[np.arange(len(idx)), jj]
                upd = dd < best
                best[upd] = dd[upd]; j[upd] = jj[upd] + n0
            r = np.sqrt(best)
            ok = (r <= max_range_m) & (j > 0) & (j < len(s.t) - 1)     # interior CPA only
            if not ok.any():
                continue
            rows.append(pd.DataFrame({
                "gidx": idx[ok], "seg": si, "trace": s.trace_idx, "icao": s.icao,
                "t_emit": s.t[j[ok]], "t_heard": s.t[j[ok]] + r[ok] / c,
                "d": r[ok], "v": s.speed[j[ok]],
            }))
    if not rows:
        return pd.DataFrame(columns=["gidx", "seg", "trace", "icao", "t_emit", "t_heard", "d", "v"])
    return pd.concat(rows, ignore_index=True)


def pair_candidates(cpa: pd.DataFrame, dt_offset: float, tol_s: float = 6.0,
                    v1=(0, 1e9), d1=(0, 1e9), v2=(0, 1e9), d2=(0, 1e9),
                    silence_d_m: float | None = 6000.0, silence_margin_s: float = 40.0) -> pd.DataFrame:
    """Grid points that hear an event-1-like CPA then, dt_offset later, an event-2-like CPA."""
    a = cpa[(cpa.v.between(*v1)) & (cpa.d.between(*d1))]
    b = cpa[(cpa.v.between(*v2)) & (cpa.d.between(*d2))]
    m = a.merge(b, on="gidx", suffixes=("1", "2"))
    m = m[(m.seg1 != m.seg2) & ((m.t_heard2 - m.t_heard1 - dt_offset).abs() <= tol_s)].copy()
    if silence_d_m is not None and len(m):
        near = cpa[cpa.d <= silence_d_m][["gidx", "seg", "t_heard"]]
        x = m[["gidx", "seg1", "seg2", "t_heard1", "t_heard2"]].reset_index().merge(near, on="gidx")
        bad = x[(x.seg != x.seg1) & (x.seg != x.seg2) & (x.t_heard > x.t_heard1 + silence_margin_s) & (x.t_heard < x.t_heard2 - silence_margin_s)]
        m = m.drop(index=bad["index"].unique())
    return m.reset_index(drop=True)


def grid_lla(grid: Grid, gidx):
    return grid.lat[gidx], grid.lon[gidx], grid.elev[gidx]
