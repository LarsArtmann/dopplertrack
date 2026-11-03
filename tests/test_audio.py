import numpy as np
from dopplertrack import audio, doppler


def test_spectrogram_sample_and_synthetic_doppler():
    sr = 4000
    t = np.arange(0, 400, 1 / sr)
    f0, v, d, t0 = 130.0, 110.0, 3000.0, 200.0
    finst = doppler.ideal_curve(t, f0, v, d, t0, c=340.0)
    finst = np.nan_to_num(finst, nan=f0)
    phase = 2 * np.pi * np.cumsum(finst) / sr
    x = (0.1 * np.sin(phase) + 0.5 * np.random.default_rng(0).standard_normal(len(t))).astype(np.float32)
    sp = audio.compute_spectrogram(x, sr, nperseg=8192, hop_s=0.5, fmin=60, fmax=250, whiten_window_s=None)
    tt = np.arange(20, 380, 2.0)
    on = sp.sample(tt, doppler.ideal_curve(tt, f0, v, d, t0, c=340.0))
    off = sp.sample(tt, doppler.ideal_curve(tt, f0, v, d, t0, c=340.0) + 15.0)
    assert on.mean() > off.mean() + 5.0
    assert sp.sample([-5.0], [100.0])[0] == 0.0
