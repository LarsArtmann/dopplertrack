"""Score candidate observers by modelling the exact Doppler curve they would hear."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .audio import Spectrogram
from .doppler import curve_from_trajectory, speed_of_sound
from .search import Segment
from .tracks import EventFit, local_whiten


@dataclass
class EventWindow:
    """Whitened spectrogram crop for one event plus its measured parameters."""
    fit: EventFit
    sp: Spectrogram
    harmonics: int = 1

    @classmethod
    def from_fit(cls, sp: Spectrogram, fit: EventFit, harmonics: int = 1, pad_s: float = 40.0):
        w = sp.crop(fit.t_start - pad_s, fit.t_end + pad_s, max(fit.f_post * 0.8, sp.f[0]),
                    min(fit.f_pre * 1.25 * harmonics, sp.f[-1]))
        return cls(fit, local_whiten(w), harmonics)

    def curve_score(self, t_audio, ratio, f0_scale=1.0) -> float:
        """Mean brightness under the curve, within the event's fit window."""
        m = (t_audio >= self.fit.t_start) & (t_audio <= self.fit.t_end) & np.isfinite(ratio)
        if m.sum() < 10:
            return 0.0
        s = 0.0
        for h in range(1, self.harmonics + 1):
            s += float(np.mean(self.sp.sample(t_audio[m], h * self.fit.f0 * f0_scale * ratio[m])))
        return s / self.harmonics


def modelled_curve(seg: Segment, obs_enu, c):
    """(t_obs unix, ratio f/f0) the observer at obs_enu hears from this segment."""
    t_obs, ratio, r = curve_from_trajectory(seg.t, seg.enu, obs_enu, f0=1.0, c=c)
    return t_obs, ratio


def locked_score(ev1: EventWindow, ev2: EventWindow, seg1: Segment, seg2: Segment, obs_enu,
                 t_heard1: float, c: float | None = None,
                 shifts=np.arange(-8, 8.01, 0.5), f0_scales=np.arange(0.95, 1.0501, 0.005)):
    """Two-event locked scoring.

    Event 1's placement is swept over small time shifts and f0 scales (both are
    measurements). Event 2 is placed with the *same* time shift, so its timing
    relative to event 1 is fixed purely by flight geometry.
    Returns (total, s1, s2, best_shift).
    """
    c = speed_of_sound() if c is None else c
    # map unix time -> audio time so that the modelled heard-CPA of event 1 lands on the measured one
    t0_map = ev1.fit.t_cpa - t_heard1
    to1, r1 = modelled_curve(seg1, obs_enu, c)
    to2, r2 = modelled_curve(seg2, obs_enu, c)
    best = (-np.inf, 0.0, 0.0)
    for sh in shifts:
        ta = to1 + t0_map + sh
        for fs in f0_scales:
            s = ev1.curve_score(ta, r1, fs)
            if s > best[0]:
                best = (s, sh, fs)
    s1, sh, _ = best
    ta2 = to2 + t0_map + sh
    s2 = max(ev2.curve_score(ta2, r2, fs) for fs in f0_scales)
    return s1 + s2, s1, s2, sh


def single_score(ev: EventWindow, seg: Segment, obs_enu, t_heard: float, c=None,
                 shifts=np.arange(-8, 8.01, 0.5), f0_scales=np.arange(0.95, 1.0501, 0.005)):
    c = speed_of_sound() if c is None else c
    to, r = modelled_curve(seg, obs_enu, c)
    t0_map = ev.fit.t_cpa - t_heard
    return max(ev.curve_score(to + t0_map + sh, r, fs) for sh in shifts for fs in f0_scales)
