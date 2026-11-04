# AGENTS.md

Context for AI agents working in this repository.

## What this is

`dopplertrack` locates where an audio recording was made by matching the Doppler
frequency sweeps of propeller-aircraft flyovers (60–400 Hz, usually inaudible) in
the recording against historical ADS-B flight tracks. Proof of concept (v0.2.0),
validated end-to-end on two real recordings with known answers (see README Results).

`origin` points at the fork `github.com/LarsArtmann/dopplertrack`; the upstream
project is `github.com/mjshiggins/dopplertrack` (also the homepage in pyproject).
`docs/superpowers/specs/` holds the design document; the README is the
authoritative product story and explains the method, results, and the deliberate
deviations from the original technique.

Related open-source work (verified 2026-11-04 via GitHub API): the sibling
project `1337isnot1337/DOPPLERGEIST` pursues the same goal (geolocate audio from
aircraft Doppler shifts + historical flight tracks), and
`cbonitz/doppler-experiments` validates the underlying claim from first
principles — useful comparison points for technique decisions. For ADS-B data
sourcing beyond adsb.lol, the standard Python libraries are `stiles/pyfr24`
(Flightradar24 API client, requires an API token; verified on PyPI) and
`xoolive/traffic` (air traffic analysis toolbox).

Upstream contribution policy (2026-11-04): robustness fixes go upstream as
small correctness-framed PRs (never lint-compliance framing — upstream has no
lint infra); fleet tooling (dprint.json, BuildFlow, dependabot, SECURITY.md)
and removals of helpers upstream may use privately (`grid_lla`, `top_pairs`)
stay fork-only. First PR: mjshiggins/dopplertrack#3 (branch `upstream-pr`,
3 commits off `a16b700`), filed as a sibling of the active PR #2 / issue #1
(same files, different functions); once #2 merges, rebase `upstream-pr` on
fresh `upstream/main` and push --force-with-lease. This is a git-only
checkout (no jj). Every upstream filing runs the five verify-before-filing
gates with evidence pinned to the exact upstream commit, and the draft goes
through the github-voice checker before posting.

## Commands

```bash
uv sync --dev            # deps + venv (Python >= 3.12; CI also runs 3.13)
uv run pytest -q         # whole suite, ~1 min (19 tests)
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
  fixture is gzip bytes with a `.json` name, so dprint cannot parse it) and
  `docs/results/**` (committed artifacts written by `json.dump`; formatting them
  would churn on every regeneration). Keep them when the auto-generated config is
  refreshed.
- **Warning-level findings accepted deliberately (gate passes at error severity)**:
  bandit B404/B603 on `audio.py` (ffmpeg subprocess is the architecture; argv-list
  form without shell is already the safe one); mypy import-not-found noise (no
  type-check gate exists and stubs are absent by design); vulture hits on
  `fetch._ChainedHTTP.readable/readinto` (`io.RawIOBase` interface), `plots.py`
  helpers (diagnostic programmatic API), and `__init__.hello` (documented
  vestigial). Dead code vulture found (search `Segment.trace_idx`, `grid_lla`,
  pipeline `top_pairs`) was removed 2026-11-04.
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
adsb.lol day archive ──fetch-day / extract-region──► list[Trace] (.npz)
DEM (AWS Terrain Tiles) ──► grid elevation
Spectrogram + EventFit ×2 + Trace ──search──► ranked candidates CSV
best candidate ──refine──► fine 50 m grid CSV, optionally with extra events
```

Module map (`src/dopplertrack/`, flat src-layout package):

| Module        | Role                                                                                                                          |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `audio.py`    | ffmpeg decode, chunked STFT, per-bin whitening; `Spectrogram` dataclass                                                       |
| `doppler.py`  | Physics: ideal curve, curve from a real trajectory, CPA, speed of sound                                                       |
| `geo.py`      | WGS-84 ↔ ECEF ↔ ENU, haversine                                                                                                |
| `tracks.py`   | Ridge extraction (Viterbi), coarse grid search + Nelder-Mead → `EventFit`; `detect_events` scans whole recordings             |
| `adsb.py`     | readsb `trace_full_*.json` parsing, `Trace` dataclass, jet/prop classification via ICAO Doc 8643                              |
| `fetch.py`    | Streams a ~4 GB adsb.lol day tar from GitHub releases; chained HTTP with Range resume; nothing stored but the filtered result |
| `terrain.py`  | Terrarium tile elevation, disk+memory cached                                                                                  |
| `search.py`   | `Grid`, 1 Hz `Segment`s, KD-tree-corridor CPA table, bucketed pair join + silence filter                                      |
| `score.py`    | `EventWindow`, `locked_score` (two-event), `single_score`                                                                     |
| `pipeline.py` | Orchestration shared by CLI and programmatic users (`run_search`, `refine`, `run_single_search`)                              |
| `cli.py`      | argparse CLI: `spectrogram, fit, detect, extract-region, fetch-day, search, refine, search-single`                            |
| `plots.py`    | Matplotlib (Agg) diagnostics                                                                                                  |

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

- **Segment indices are ephemeral.** `build_segments` output order depends on the
  grid origin and clip box, so `seg1`/`seg2` indexes from a search CSV do not
  survive a rebuild. `refine` re-derives segments via `segments_for_search`
  (bbox padded by `max_range_m`) and re-finds the flights by ICAO + heard time
  (`relocate_row`). The error `flight {icao} not in these traces` comes from there.
- **The CPA table cache (`search --cpa-cache`) is fingerprinted** on grid size/origin,
  segment count/total samples, `max_range_m`, and `c`. A mismatch is detected and the
  table silently recomputed — don't weaken the fingerprint.
- **`pair_candidates` joins on (grid point, time bucket)** rather than per-point
  cross products (billions of rows otherwise). A test (`test_search_pairs.py`)
  asserts exact equality with brute force including bucket-edge cases; keep it
  exact if you touch the join.
- Filter defaults encode domain assumptions: aircraft are audible within
  `max_range_m=12000`; the silence filter drops points that hear another prop
  within 6000 m between the two events (±40 s margins); pair filters accept
  speed ±35% and CPA distance 0.4×–2.5× of the measured fit.
- `Grid.make` floors elevation at 0 m (`--no-dem` uses zeros). Chunked BLAS
  distance kernels subtract a chunk-mean before the matmul on purpose (float64
  cancellation); preserve that when editing `cpa_table`.
- `detect_events` parallelizes windows with `ProcessPoolExecutor`; pass
  `workers=1` (tests do) to run in-process.

## Scoring invariant

`EventWindow.sweep_scores` scores brightness summed along the modelled curve as a
**mean over the whole measured window, with uncovered parts counting as zero**.
This is deliberate: an earlier version averaged over covered parts only and a
flight that left the data mid-pass won on its bright half alone (README, "What
this second recording changed"). `test_score_coverage.py` enforces proportionality.
A contrastive (sideband) score was tried and rejected — do not reintroduce it
without re-validating against both reference recordings.

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
- Terrain, adsb.lol fetching, and the real-recording validation are exercised by
  the README validation runs, not by tests.

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
- `src/dopplertrack/__init__.py::hello()` is vestigial — the real entry point is
  `dopplertrack.cli:main`. Don't route new features through the package init.
- `.gitignore` ignores generated data (`*.wav *.npz *.csv`, `/data/ /cache/ /results/`)
  but force-includes `tests/data/*` and `docs/results/*`. The PNG/CSV/JSON files in
  `docs/results/` are committed artifacts the README references — treat edits there
  as documentation changes.
- Commit messages so far are short, stage-first subjects (`"detect: automatic
  Doppler event detection over a whole recording"`, `"Release 0.2.0: ..."`).
- `uv.lock` is committed; update dependencies with `uv lock` / `uv sync`, never
  by hand.
- `soundfile` is declared in pyproject but never imported — audio decoding goes
  through ffmpeg. Don't assume it is load-bearing.
