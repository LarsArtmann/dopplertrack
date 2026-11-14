# AGENTS.md

Context for AI agents working in this repository.

## What this is

`dopplertrack` locates where an audio recording was made by matching the Doppler
frequency sweeps of propeller-aircraft flyovers (60–400 Hz, usually inaudible) in
the recording against historical ADS-B flight tracks. v0.3.0, validated
end-to-end on three real recordings (two located with known answers, one honest
negative; see README Results and docs/experiments.md).

`origin` points at the fork `github.com/LarsArtmann/dopplertrack`; the upstream
project is `github.com/mjshiggins/dopplertrack` (also the homepage in pyproject).
`docs/superpowers/specs/` holds the design document; the README is the
authoritative product story and explains the method, results, and the deliberate
deviations from the original technique.

Related open-source work (verified 2026-11-04 via GitHub API):
`1337isnot1337/DOPPLERGEIST` (geolocate audio from Doppler shifts + flight
tracks) and `cbonitz/doppler-experiments` (first-principles validation) are
comparison points; for ADS-B beyond adsb.lol, `stiles/pyfr24` (FR24 client,
API token; on PyPI) and `xoolive/traffic` are the standard libraries.

EU readiness (verified live 2026-11-13): the pipeline is region-agnostic by
construction (WGS-84/ENU geodesy, Web Mercator terrain, readsb parsing, global
ICAO Doc 8643), and the data path was verified on real EU data: streaming
2026-11-12's `planes-readsb-prod-0` archive parsed 28,858/28,879 trace files,
2,034 touched a Germany bbox, including EU GA props (C172, P28A, DR40, FK9,
C42, DA42) with reg/type populated. Terrain returns correct EU elevations
(Munich 526 m, Zugspitze 2935 m, NL polder -1 m). The prod pod is one global
feed (two replicas; staging is the fallback); `mlatonly` is a separate pod for
aircraft without ES positions (`fetch --pod`). Not yet done: an EU recording
validation (all three reference recordings are US). FLARM-only aircraft
(gliders, tugs) are invisible to ADS-B — a feed limitation, not a code gap.

Upstream contribution policy (updated 2026-11-13): robustness fixes go
upstream as small correctness-framed PRs (never lint-compliance framing —
upstream has no lint infra); fleet tooling (dprint.json, BuildFlow,
dependabot, SECURITY.md) stays fork-only. PRs #2 and #3 both merged
2026-11-04; fork `main` synced onto `upstream/main` (0.3.0) on 2026-11-13
(merge 6d4c6f4) and local branch `upstream-pr` was deleted; origin's copy
still needs `git push origin --delete upstream-pr`. Future filings still
run the five verify-before-filing gates with evidence pinned to the exact
upstream commit, and go through the github-voice checker before posting.
This is a git-only checkout (no jj).

## Commands

```bash
uv sync --dev            # deps + venv (Python >= 3.12; CI also runs 3.13)
uv run pytest -q         # whole suite, several minutes (count drifts; don't hardcode it)
uv run dopplertrack --help
```

- **ffmpeg is a hard runtime dependency but is NOT in pyproject.toml.** `audio.py`
  shells out to it to decode any audio/video file. CI installs it via apt. The test
  suite never invokes it (audio is synthesized in numpy), so tests pass without
  ffmpeg, but the `spectrogram` CLI command and `pipeline.make_spectrogram` need it.
- **Quality tooling is owned by BuildFlow, not by repo config.** There is no
  in-repo ruff/mypy configuration; `buildflow --fix` (BuildFlow fleet pipeline)
  runs ruff (default rule set) and dprint (config auto-generated in `dprint.json`).
  CI (`.github/workflows/ci.yml`) is still just `uv sync --dev && uv run pytest -q`
  on Python 3.12 and 3.13. The `.gitignore` mentions ruff/mypy caches but no
  in-repo linter config exists.
- **`dprint.json` excludes are load-bearing**: `tests/data/**` (the readsb trace
  fixture is gzip bytes; renamed to `.json.gz` 2026-11-14 so the name tells the
  truth, the exclude stays) and
  `docs/results/**` (committed artifacts written by `json.dump`; formatting them
  would churn on every regeneration). Keep them when the auto-generated config is
  refreshed.
- **Warning-level findings accepted deliberately (gate passes at error severity)**:
  bandit B404/B603 on `audio.py` (ffmpeg subprocess is the architecture; argv-list
  form without shell is already the safe one); mypy import-not-found noise (no
  type-check gate exists and stubs are absent by design); vulture hits on
  `fetch._ChainedHTTP.readable/readinto` (`io.RawIOBase` interface) and `plots.py`
  helpers (diagnostic programmatic API). Dead code vulture found (search
  `Segment.trace_idx`, `grid_lla`, pipeline `top_pairs`) was removed 2026-11-04.
- **Releases are tag-driven** (`.github/workflows/release.yml`): the tag `vX.Y.Z`
  must equal the `pyproject.toml` version (the workflow fails otherwise), then runs
  tests, `uv build`, a GitHub Release, and PyPI trusted publishing.

```bash
uv version X.Y.Z && git commit -am "Release X.Y.Z"
git tag vX.Y.Z && git push && git push --tags
```

## Architecture

Pipeline (each stage's output feeds the next; CLI subcommands map 1:1):

```
audio/video ──spectrogram──► whitened low-band Spectrogram (.npz)
            ──fit / detect──► EventFit JSON per flyover (t_cpa, f0, v, d, ...)
adsb.lol day archive ──fetch──► DayIndex (.npz, one per day, reused by searches)
DEM (AWS Terrain Tiles) ──► grid elevation
Spectrogram + EventFit ×2 + DayIndex ──search──► ranked candidates CSV + verdict p
best candidate ──refine──► fine 50 m grid CSV, optionally with extra events
```

Module map (`src/dopplertrack/`, flat src-layout package):

| Module        | Role                                                                                                                       |
| ------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `audio.py`    | ffmpeg decode, chunked STFT, per-bin whitening; `Spectrogram` dataclass                                                    |
| `doppler.py`  | Physics: ideal curve, curve from a real trajectory, CPA, speed of sound                                                    |
| `geo.py`      | WGS-84 ↔ ECEF ↔ ENU, haversine                                                                                             |
| `tracks.py`   | Ridge extraction (Viterbi), coarse grid search + Nelder-Mead → `EventFit`; `detect_events` scans whole recordings          |
| `adsb.py`     | readsb `trace_full_*.json` parsing, `Trace` dataclass, jet/prop classification via ICAO Doc 8643                           |
| `fetch.py`    | Streams a ~4 GB adsb.lol day tar from GitHub releases (chained HTTP with Range resume) into a 1 Hz `DayIndex` for searches |
| `terrain.py`  | Terrarium tile elevation, disk+memory cached                                                                               |
| `search.py`   | `DayIndex`, `pair_join`/`single_join` on flight-pair geometry, lens lattices with exact gates + silence filter             |
| `score.py`    | `EventWindow` sweep scoring (brightness or ridge), `locked_score` (two-event), `single_score`                              |
| `verdict.py`  | Exponential-tail verdict: p that a wrong winner would lead the next wrong pair by the observed gap                         |
| `pipeline.py` | Orchestration shared by CLI and programmatic users (`make_spectrogram`, `fetch`, `refine`, `best_per_pair`)                |
| `cli.py`      | argparse CLI: `spectrogram, detect, fit, fetch, search, refine`                                                            |
| `plots.py`    | Matplotlib (Agg) diagnostics                                                                                               |

Interchange formats: spectrograms and traces are `.npz`; event fits are JSON
dicts (`EventFit.to_dict()`, reloaded as `EventFit(**json)`); search results are
pandas DataFrames → CSV. `pipeline.py`'s docstring mentions notebooks, but none
exist in the repo; it is the programmatic API.

## Physics and time invariants (do not break)

- **All Doppler math uses emission-time kinematics**: the heard frequency at
  observation time `t_obs` was produced at `t_e` where `t_obs = t_e + r(t_e)/c`,
  with range rate evaluated at `t_e`. Modelling with observation-time radial
  velocity produces a _visibly wrong curve_, not just a shifted one
  (`test_emission_time_delay_shifts_curve_not_just_in_time` exists to prove it).
- **Three time bases coexist and are easy to mix up**:
  - recording seconds — spectrogram `t`, `EventFit.t_cpa` (the _heard_ CPA),
    `EventFit.t_cpa_emit`;
  - unix seconds — `Trace.t`, `Segment.t`;
  - the bridge is `t0_map = ev1.fit.t_cpa - t_heard1` (unix → audio offset),
    computed in `locked_score`/`refine`/`pick_flight`. New code touching times
    must state which base it uses.
- `speed_of_sound()` defaults to 15 °C everywhere; pass `c` explicitly in tests.

## Search internals: gotchas

- **Candidates are cached with a fingerprint**: `save_candidates`/`load_candidates`
  carry a fingerprint dict; a mismatched load returns None and the search recomputes.
  Don't weaken the fingerprint.
- **Segments are ephemeral.** `build_segments` output order depends on the trace
  list and clip; never persist segment indices across a rebuild — match flights
  by ICAO + heard time instead.
- Filter defaults encode domain assumptions (`LensParams`): aircraft are audible
  within `max_range_m=12000`; the silence filter drops candidates that hear another
  prop within `silence_d_m=6000` between the two events (±`silence_margin_s=40` s).
- `Grid.make` floors elevation at 0 m (`--no-dem` uses zeros). Preserve chunk-mean
  subtraction in chunked distance kernels (float64 cancellation).
- `detect_events` parallelizes windows with `ProcessPoolExecutor`; pass
  `workers=1` (tests do) to run in-process. Nationwide pair joins parallelize via
  `default_workers()`.

## Scoring invariant

`EventWindow.sweep_scores` scores brightness summed along the modelled curve as a
**mean over the whole measured window, with uncovered parts counting as zero**.
This is deliberate: an earlier version averaged over covered parts only and a
flight that left the data mid-pass won on its bright half alone
(docs/experiments.md). `test_score_coverage.py` enforces proportionality.
A contrastive (sideband) score was tried and rejected — do not reintroduce it
without re-validating against the reference recordings.

## Testing patterns

- Physics and geodesy are tested against closed forms; the pipeline is tested
  **end-to-end on synthetic data** (`test_pipeline_synthetic.py`): build flights in
  ENU → `enu_to_lla` → `Trace`, synthesize the audio the origin hears with
  `curve_from_trajectory`, then detect → fit → search → refine and assert the true
  observer wins. This test is the integration gate.
- Everything is deterministic: fixed `default_rng(seed)`; synthetic trajectories;
  `workers=1` in `detect_events`.
- Network code is tested with `monkeypatch` only (`test_fetch.py`); no test hits
  the network. One real readsb trace fixture lives in `tests/data/`.
- Verdicts are checked against archived wrong-pair tables (`test_verdict.py`);
  ridge scoring in `test_score_ridge.py`; burst flagging in `test_detect_burst.py`.
- The real-recording Oyster Bay check is opt-in: set `DOPPLERTRACK_OYSTER_BAY`
  to a directory with `rec.npz` + `traces_ny.npz` (`test_oyster_bay.py`).

## Network and caching at runtime

First use downloads and caches (offline afterwards):

- ICAO Doc 8643 aircraft-type CSV (OpenSky mirror) — `adsb.AircraftTypes`
- AWS Terrain Tiles PNGs — `terrain.Terrain`

Cache root: `~/.cache/dopplertrack`, overridable with the `DOPPLERTRACK_CACHE`
env var (both modules honor it). `fetch-day` streams the day's tar from
adsb.lol GitHub releases with Range-resume retries and writes only the filtered
output, so a 4 GB day needs no local scratch space.

## Conventions

- BuildFlow's ruff (default rule set) must stay clean; code keeps ruff-compatible
  idioms: `adsb.TRACE_PARSE_ERRORS` is the narrowed exception family for skipping
  corrupt trace documents (`_scan_one`, `fetch._parse_quiet`); sweep defaults are
  the module constants `score.DEFAULT_SHIFTS` / `score.DEFAULT_F0_SCALES` (ruff
  B008 forbids calls in argument defaults); `cli.load_event` is the only JSON ->
  EventFit file loader. Underscore-prefix intentionally unused unpack targets.
- Compact numerical style: semicolon-joined short statements, one-line argparse
  definitions, vectorized numpy over loops, dataclasses as typed containers.
  Match it; don't reformat surrounding code.
- `py.typed` is shipped but nothing type-checks the code; annotations are
  partial (`from __future__ import annotations` everywhere).
- The package `__init__.py` is deliberately empty: the real entry point is
  `dopplertrack.cli:main`. Don't route new features through the package init
  (the vestigial `hello()` there was removed 2026-11-14).
- `.gitignore` ignores generated data (`*.wav *.npz *.csv`, `/data/ /cache/ /results/`)
  but force-includes `tests/data/*` and `docs/results/*`. The PNG/CSV/JSON files in
  `docs/results/` are committed artifacts the README references — treat edits there
  as documentation changes.
- Commit messages so far are short, stage-first subjects (`"detect: automatic
  Doppler event detection over a whole recording"`, `"Release 0.2.0: ..."`).
- `uv.lock` is committed; update dependencies with `uv lock` / `uv sync`, never
  by hand.
- `soundfile` was declared-but-unused and removed 2026-11-14; audio decoding
  goes through ffmpeg. Don't add Python audio libraries — the ffmpeg
  subprocess is the architecture.
