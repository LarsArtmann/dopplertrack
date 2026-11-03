# dopplertrack

Acoustic geolocation from the Doppler curves of propeller aircraft.

Any outdoor (and many indoor) recordings contain faint, usually inaudible
tones from aircraft flying over: the propeller blade-pass fundamental and its
harmonics, between roughly 60 and 400 Hz. As the aircraft passes, the tone
sweeps down in frequency. The exact shape of that sweep depends on where the
listener was relative to the aircraft's real trajectory. With historical
ADS-B data for every flight that day, each candidate location on the ground
predicts a different curve, and the recording picks out the one that matches.

This is a reimplementation of the technique shown in colsto's video
["I discovered a sound that leaks your exact location"](https://www.youtube.com/watch?v=UytYrhYLOKI).
No code was released with that video; this project is an open, automatic
version of the method. See `docs/superpowers/specs/` for the design.

## Status

Proof of concept. Validated against the author's reference recording
(known answer: Oyster Bay, NY, 2026-09-08). See the results section below.

## Pipeline

1. `spectrogram` — decode any audio/video with ffmpeg, high-resolution STFT of
   the 40–450 Hz band, whitened per frequency bin so only *changing* tones stand out.
2. `fit` — fit an ideal straight-pass Doppler curve (f0, speed, CPA slant
   distance, CPA time) to a time/frequency window. The fit seeds a search
   with coarse parameter ranges.
3. `extract-region` — pull every flight that touched a bounding box out of an
   [adsb.lol](https://github.com/adsblol/globe_history_2026) daily archive and
   drop known jets using ICAO Doc 8643 engine classes.
4. `search` — for every grid point (200 m) and every flight, compute the
   closest point of approach (CPA), its slant distance (using a DEM for the
   observer's elevation) and the *heard* CPA time (propagation delay). Keep
   points that hear an event-1-like pass, then exactly Δt later an
   event-2-like pass, with no other prop flight in between. Model the exact
   Doppler curve each survivor would hear from the real trajectory
   (emission-time radial velocity) and score it against the spectrogram.
   Event 1's placement absorbs measurement error; event 2's placement is
   locked to the flight geometry.

## Usage

```bash
uv sync
uv run dopplertrack spectrogram recording.mp4 rec.npz
uv run dopplertrack fit rec.npz --window 2090 2200 --band 95 200 --harmonics 2 --out ev1.json
uv run dopplertrack fit rec.npz --window 3020 3130 --band 95 195 --out ev2.json
uv run dopplertrack extract-region /path/to/adsb-day --bbox 40.4 41.3 -74.4 -72.6 traces_ny.npz
uv run dopplertrack search rec.npz --events ev1.json ev2.json --traces traces_ny.npz \
    --bbox 40.4 41.3 -74.4 -72.6 --spacing 200 --out results.csv
```

`search --point LAT LON` scores a single known location instead of a grid,
which is the quickest way to validate the data and physics on a recording
whose location you already know.

## Changes from the method in the video

The physics and the search strategy are the author's. What differs:

- **Automatic curve measurement.** The video measures each Doppler curve by
  hand, sliding f0 / speed / distance / CPA-time until the overlay looks
  right, then choosing "generous ranges" by eye. `fit` does this without a
  person: the window is whitened per frequency bin so stationary tones
  (mains hum, machinery) vanish, a vectorised grid search over all four
  parameters maximises spectrogram brightness under the curve, and a
  Nelder-Mead pass refines it. The ideal-curve fit still only seeds coarse
  filters; final ranking uses real trajectories.
- **Harmonic-aware fitting and scoring.** When a flyover shows a second
  harmonic, fundamental and harmonic are scored together, which constrains
  the curve more tightly than one line.
- **Open, documented data path.** The video used a paid/scraped ADS-B feed
  and did not release code. Here every input is a public dataset with a
  loader: adsb.lol daily archives, ICAO Doc 8643 engine classes, AWS
  terrain tiles.
- **Search engineering.** A KD-tree corridor around each flight path limits
  CPA computation to grid points that could possibly hear it; distance math
  is chunked so multi-hour tracks do not exhaust memory; the time-shift and
  f0 sweeps of the locked scorer run as one array operation per candidate.
- **Single-event, known-time mode as a first-class command.** The video
  demonstrates locating from one faint one-minute curve when the recording
  time is known; `search-single` exposes that directly.

Kept unchanged on purpose: emission-time radial velocity (not
observation-time), propagation-delayed CPA times, slant distance with a DEM,
the inter-event offset filter, the silence filter, and locked two-event
scoring where event 1 absorbs measurement error and event 2 is placed purely
by flight geometry.

## Data sources (all free)

| Need | Source |
|---|---|
| Historical ADS-B | adsb.lol `globe_history_YYYY` GitHub releases (~4 GB/day) |
| Aircraft engine class | OpenSky mirror of ICAO Doc 8643 |
| Elevation | AWS Terrain Tiles (Terrarium) |

## Development

```bash
uv run pytest
```

## Releasing

Releases are driven by git tags. Pushing a tag `vX.Y.Z` that matches the
version in `pyproject.toml` runs `.github/workflows/release.yml`, which runs
the tests, builds the sdist and wheel, attaches them to a GitHub Release with
generated notes, and publishes to PyPI through trusted publishing (no API
token stored anywhere).

```bash
uv version 0.2.0            # bump pyproject.toml
git commit -am "Release 0.2.0"
git tag v0.2.0 && git push && git push --tags
```

One-time setup for PyPI: on pypi.org, add a *pending publisher* for project
`dopplertrack` with owner `mjshiggins`, repository `dopplertrack`, workflow
`release.yml`, environment `pypi`, and create a `pypi` environment in the
GitHub repository settings. Until that exists the `pypi` job fails and the
GitHub Release still succeeds.
