"""Doppler curve physics.

All functions use *emission-time* kinematics: the frequency heard at
observation time t_obs was produced at emission time t_e where
t_obs = t_e + r(t_e)/c, and the shift is set by the range rate at t_e.
"""
from __future__ import annotations

import numpy as np


def speed_of_sound(temp_c: float = 15.0) -> float:
    return 331.3 * np.sqrt(1.0 + temp_c / 273.15)


def observed_frequency(f0, range_rate, c):
    """Frequency heard for a source of rest frequency f0 with range rate dr/dt
    (positive = receding)."""
    return f0 * c / (c + range_rate)


def ideal_curve(t_obs, f0, v, d_cpa, t_cpa, c=None, span=600.0, n=4001):
    """Frequency heard at times t_obs for a straight, constant-speed pass.

    v: speed (m/s); d_cpa: slant distance at closest approach (m);
    t_cpa: *emission* time of closest approach.
    """
    c = speed_of_sound() if c is None else c
    te = t_cpa + np.linspace(-span, span, n)
    r = np.sqrt(d_cpa**2 + (v * (te - t_cpa)) ** 2)
    rr = v * v * (te - t_cpa) / r
    f = observed_frequency(f0, rr, c)
    tobs = te + r / c
    return np.interp(np.asarray(t_obs, float), tobs, f, left=np.nan, right=np.nan)


def ideal_curve_params_from_endpoints(f_pre, f_post, c=None):
    """Recover (f0, v) from the approach and recede asymptote frequencies."""
    c = speed_of_sound() if c is None else c
    # f_pre = f0 c/(c-v), f_post = f0 c/(c+v)
    v = c * (f_pre - f_post) / (f_pre + f_post)
    f0 = f_pre * (c - v) / c
    return f0, v


def curve_from_trajectory(t_e, pos_enu, obs_enu, f0=1.0, c=None):
    """Doppler curve a stationary observer hears from a sampled trajectory.

    t_e: (N,) emission times (s); pos_enu: (N,3) source positions (m);
    obs_enu: (3,) observer position (m). Returns (t_obs, f, r) with f for
    rest frequency f0 (use f0=1 to get the ratio).
    """
    c = speed_of_sound() if c is None else c
    t_e = np.asarray(t_e, float)
    d = np.asarray(pos_enu, float) - np.asarray(obs_enu, float)
    r = np.linalg.norm(d, axis=-1)
    rr = np.gradient(r, t_e)
    f = observed_frequency(f0, rr, c)
    t_obs = t_e + r / c
    return t_obs, f, r


def cpa_from_trajectory(t_e, pos_enu, obs_enu, c=None):
    """Closest point of approach: (t_cpa_emission, t_cpa_heard, slant_m, speed_mps)."""
    c = speed_of_sound() if c is None else c
    t_e = np.asarray(t_e, float)
    d = np.asarray(pos_enu, float) - np.asarray(obs_enu, float)
    r = np.linalg.norm(d, axis=-1)
    i = int(np.argmin(r))
    vel = np.gradient(np.asarray(pos_enu, float), t_e, axis=0)
    speed = float(np.linalg.norm(vel[i]))
    return float(t_e[i]), float(t_e[i] + r[i] / c), float(r[i]), speed
