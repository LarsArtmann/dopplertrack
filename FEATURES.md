# Features

Honest inventory of what `dopplertrack` does, with status. Status vocabulary:
FULLY_FUNCTIONAL (code present, works, tested or exercised end-to-end),
PARTIALLY_FUNCTIONAL (ships with known gaps), PLANNED (no code yet, next on
the build path). Evidence points at code and tests. Counts computed from the
repo on 2026-11-14 (62 tests: 57 pass, 2 xfail, 3 skip, 5 slow-marked;
7 CLI subcommands; 16 source modules).

## Pipeline stages - FULLY_FUNCTIONAL

| Feature | What it does | Evidence |
| --- | --- | --- |
| Spectrogram | ffmpeg-decodes any audio/video, whitened per-bin STFT of the 40-450 Hz band | `src/dopplertrack/audio.py:13`, `tests/test_audio.py` |
| Doppler physics | ideal curve, curve from a real trajectory, emission-time kinematics, speed of sound | `src/dopplertrack/doppler.py`, `tests/test_physics.py` |
| Event detection (`detect`) | scans whole recordings, ranks flyovers, train/truck burst rejection | `src/dopplertrack/tracks.py` (`detect_events`), `tests/test_detect_burst.py` |
| Event fitting (`fit`) | ideal-curve fit in a chosen window, harmonics | `src/dopplertrack/tracks.py` (`fit_event`), `tests/test_fit_objective.py` |
| ADS-B parsing + classification | readsb trace JSON to `Trace`, jet/prop split via ICAO Doc 8643 | `src/dopplertrack/adsb.py`, `tests/test_adsb.py` |
| Day-archive streaming (`fetch`) | adsb.lol day tar streamed with Range resume, bbox filter, 1 Hz `DayIndex` | `src/dopplertrack/fetch.py`, `tests/test_fetch.py`; live EU probe 2026-11-13 |
| Coverage probe (`coverage`) | day archive quantified per bbox: trace counts, parse failures, prop share, registrations | `src/dopplertrack/coverage.py`, `tests/test_coverage.py` |
| Regional search (`search`) | flight-pair join, lens lattice, silence filter, locked two-event scoring over a grid | `src/dopplertrack/search.py`, `src/dopplertrack/score.py`, `tests/test_search.py`, `tests/test_score_coverage.py`, `tests/test_score_ridge.py` |
| Fine refine (`refine`) | 50 m grid around one result, extra events locked to the same clock | `src/dopplertrack/pipeline.py` (`refine`), `tests/test_pipeline_synthetic.py` |
| Verdict | location-independent null distribution, calibrated p for the top candidate | `src/dopplertrack/verdict.py`, `tests/test_verdict.py` |
| CLI ergonomics | `--version`, friendly errors for missing ffmpeg / wrong path / corrupt event JSON | `src/dopplertrack/cli.py`, `tests/test_cli.py` |

## Validated results - FULLY_FUNCTIONAL

| Feature | Evidence |
| --- | --- |
| Oyster Bay, NY recording located (123 m on 200 m grid; 918 s offset filter) | `docs/experiments.md` (Oyster Bay), `docs/results/oyster_bay_*.csv` |
| Eagle-nest recording located blind from 12 h (917 m), faint single flyover fallback | `docs/experiments.md` (Howell Wye), `docs/results/howell_wye_*` |
| Atlanta railcam, 11.9 h busy airspace: 2 detected flyovers locate the camera | `docs/experiments.md` (third recording), `docs/results/swfl_*` |
| End-to-end synthetic gate: detect - fit - search - refine recovers the truth | `tests/test_pipeline_synthetic.py` |

## PARTIALLY_FUNCTIONAL

| Feature | Gap | Evidence |
| --- | --- | --- |
| Terrain elevation | works (README validations, EU probe: Munich 526 m, Zugspitze 2935 m) but has no unit tests in the suite | `src/dopplertrack/terrain.py` |
| Diagnostics plots | programmatic matplotlib API only, no CLI; produced the committed PNGs | `src/dopplertrack/plots.py` |
| Type coverage | `py.typed` shipped, annotations partial, no type-check gate | `src/dopplertrack/*.py` |
| EU data path | feed, parser, terrain, geodesy all verified EU-side (2026-11-13 probe: 2,034 Germany-bbox traces in one day) but no EU recording validated end-to-end | `AGENTS.md` (EU readiness), task A of the 2026-11-14 plan |

## PLANNED

| Feature | Why next | Evidence |
| --- | --- | --- |
| EU end-to-end geolocation | converts "EU-ready" into a validated result; unblocks EU claims | `docs/planning/2026-11-14_00-42_pareto-eu-proof-first-execution-plan.md` (A1-A5) |
| `coverage.md` with EU numbers | quantify readiness for any bbox, recorded durably | same plan (B4) |
| Search-margin experiment (verdict-aware) | margin thresholds are guesses; verdict makes them measurable | same plan (D12) |
| detect-to-search auto-chain | one command from recording to ranked candidates | `ROADMAP.md` |
| More than two events in one search | current scorer locks pairs; >2 needs a design, not a patch | `ROADMAP.md` |
