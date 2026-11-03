"""Extract a Doppler event from a spectrogram window and fit the ideal model."""
from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np
from scipy.optimize import minimize

from .audio import Spectrogram
from .doppler import ideal_curve, speed_of_sound


@dataclass
class EventFit:
    t_cpa: float        # heard CPA time in the recording, s (observation time of the f0 crossing)
    t_cpa_emit: float   # emission-time CPA (t_cpa - d/c)
    f0: float           # rest fundamental, Hz
    v: float            # speed, m/s
    d: float            # CPA slant distance, m
    t_start: float
    t_end: float
    score: float        # mean whitened dB along the fitted curve
    f_pre: float
    f_post: float

    def to_dict(self):
        return asdict(self)


def local_whiten(sp: Spectrogram, floor: float = 0.0) -> Spectrogram:
    """Remove tones that are stationary over this window (per-bin median), clip at floor."""
    S = sp.S - np.median(sp.S, axis=1, keepdims=True)
    return Spectrogram(sp.t, sp.f, np.maximum(S, floor).astype(np.float32))


def ridge(sp: Spectrogram, max_step_bins: int = 3, smooth: float = 1.5) -> np.ndarray:
    """Viterbi ridge through S (F,T): maximise sum(S) - smooth*|Δbin|. Returns freq per frame."""
    S = sp.S
    F, T = S.shape
    cost = np.full((T, F), -np.inf)
    back = np.zeros((T, F), np.int16)
    cost[0] = S[:, 0]
    offs = np.arange(-max_step_bins, max_step_bins + 1)
    pen = smooth * np.abs(offs)
    for t in range(1, T):
        prev = cost[t - 1]
        cand = np.full((len(offs), F), -np.inf)
        for k, o in enumerate(offs):
            if o >= 0:
                cand[k, o:] = prev[: F - o] - pen[k]
            else:
                cand[k, :o] = prev[-o:] - pen[k]
        kbest = np.argmax(cand, axis=0)
        cost[t] = cand[kbest, np.arange(F)] + S[:, t]
        back[t] = offs[kbest]
    path = np.zeros(T, int)
    path[-1] = int(np.argmax(cost[-1]))
    for t in range(T - 1, 0, -1):
        path[t - 1] = path[t] - back[t, path[t]]
    return sp.f[path]


def _shape(v, d, c, span=400.0, n=161):
    """Observation-time offsets and frequency ratios for a straight pass, relative to
    emission-time CPA (tau=0)."""
    tau = np.linspace(-span, span, n)
    r = np.sqrt(d * d + (v * tau) ** 2)
    rr = v * v * tau / r
    return tau + r / c, c / (c + rr)


def grid_search(sp: Spectrogram, t_start, t_end, f_lo, f_hi, c, harmonics=1,
                v_grid=None, d_grid=None, f0_step=1.0, t0_step=1.0, n_curve=120):
    """Coarse maximisation of brightness under ideal curves. Returns (score, f0, v, d, t0_emit)."""
    v_grid = np.arange(30, 170, 10.0) if v_grid is None else v_grid
    d_grid = np.geomspace(300, 9000, 14) if d_grid is None else d_grid
    f0s = np.arange(f_lo * 1.15, f_hi * 0.85, f0_step)
    t0s = np.arange(t_start, t_end, t0_step)
    tq = np.linspace(t_start, t_end, n_curve)
    best = (-np.inf, None)
    for v in v_grid:
        for d in d_grid:
            dto, ratio = _shape(v, d, c)
            # for each t0: curve observation times = t0 + dto; frequencies = f0*ratio
            # sample at tq by interpolating ratio onto tq - t0
            rel = tq[None, :] - t0s[:, None]                         # (T0, N)
            rat = np.interp(rel, dto, ratio, left=np.nan, right=np.nan)  # (T0, N)
            total = np.zeros((len(t0s), len(f0s)))
            for h in range(1, harmonics + 1):
                F = h * f0s[None, None, :] * rat[:, :, None]           # (T0, N, F0)
                T = np.broadcast_to(tq[None, :, None], F.shape)
                vals = sp.sample(T.ravel(), F.ravel()).reshape(F.shape)
                total += np.nanmean(vals, axis=1)
            i, j = np.unravel_index(np.argmax(total), total.shape)
            if total[i, j] > best[0]:
                best = (float(total[i, j] / harmonics), (float(f0s[j]), float(v), float(d), float(t0s[i])))
    return best


def fit_event(sp: Spectrogram, t_start: float, t_end: float, f_lo: float, f_hi: float,
              c: float | None = None, harmonics: int = 1, whiten: bool = True) -> EventFit:
    """Fit (f0, v, d, t_cpa) to the brightest Doppler-shaped curve in a window."""
    c = speed_of_sound() if c is None else c
    pad = 0.3 * (f_hi - f_lo)
    win = sp.crop(t_start - 30, t_end + 30, max(f_lo - pad, sp.f[0]), min(f_hi * harmonics + pad, sp.f[-1]))
    if whiten:
        win = local_whiten(win)
    score0, (f0, v, d, t0) = grid_search(win, t_start, t_end, f_lo, f_hi, c, harmonics)
    tt = np.linspace(t_start, t_end, 400)

    def neg(p):
        f0_, v_, d_, t0_ = p
        if not (10 < v_ < 300 and 100 < d_ < 30000):
            return 1e3
        s = 0.0
        for h in range(1, harmonics + 1):
            s += float(np.nanmean(win.sample(tt, ideal_curve(tt, h * f0_, v_, d_, t0_, c=c))))
        return -s / harmonics

    best = minimize(neg, [f0, v, d, t0], method="Nelder-Mead",
                    options={"xatol": 1e-2, "fatol": 1e-4, "maxiter": 4000,
                             "initial_simplex": np.array([[f0, v, d, t0], [f0 + 2, v, d, t0], [f0, v + 10, d, t0],
                                                          [f0, v, d * 1.3, t0], [f0, v, d, t0 + 2]])})
    f0, v, d, t0 = best.x
    return EventFit(t_cpa=float(t0 + d / c), t_cpa_emit=float(t0), f0=float(f0), v=float(v), d=float(d),
                    t_start=t_start, t_end=t_end, score=float(-best.fun),
                    f_pre=float(f0 * c / (c - v)), f_post=float(f0 * c / (c + v)))
