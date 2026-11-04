# Status report: AGENTS.md creation, fork setup, external-claims triage

Date: 2026-11-04 02:51 CET
Scope: this session only (single working session in `/home/lars/forks/dopplertrack`).

**Verified in this report** (command → result):

- `uv sync --dev && uv run pytest -q` → 19 passed in 55.90 s (fresh venv, before reformat)
- `uv run pytest -q` → 19 passed in 60.16 s (re-run _after_ the foreign reformat)
- `uv run dopplertrack --help` → 8 subcommands present
- `uv build` + `unzip -l` → wheel ships `py.typed`; `dist/` removed afterwards
- `git remote set-url origin https://github.com/LarsArtmann/dopplertrack` → stored URL confirmed via
  `git config --get`; reachability via `git ls-remote` (display shows SSH form due to a global
  `url.git@github.com:.insteadOf https://github.com/` rewrite — display quirk only)
- Pushes: `a16b700..cb9b3e6` (AGENTS.md) and `cb9b3e6..a7f77f8` (related-projects note)
- `gh api repos/1337isnot1337/DOPPLERGEIST` / `repos/cbonitz/doppler-experiments` / `repos/xoolive/traffic`
  → all exist, descriptions captured verbatim
- PyPI `https://pypi.org/pypi/pyfr24/json` → v0.3.0, author Matt Stiles, homepage `stiles/pyfr24`
- `rg -l soundfile src tests` → zero matches (declared-but-unused dependency)
- `git ls-files` → `uv.lock` is tracked
- `git diff --stat` of the unexpected working-tree diff → 22 files, +1402/−377
- `git ls-remote https://github.com/mjshiggins/dopplertrack` → upstream main at `a16b700`;
  fork is **2 commits ahead, 0 behind**
- `cat .config/metadata.yaml` → bare `created_at`/`updated_at` (2026-11-04T01:36:14Z), tags empty,
  **no tool attribution**

**NOT verified in this report:**

- Who or what ran the whole-repo reformat (no provenance anywhere I looked)
- The pasted context's video-timestamp claims (Audacity 03:42, QGIS 03:14/22:20, Sonic Visualiser,
  USGS 3DEP) — would require watching the video; deliberately not encoded anywhere
- Whether a `dprint` markdown-format run would alter AGENTS.md (not executed)
- Upstream issues/PRs (not looked at)

---

## a) FULLY DONE

| # | Work                                                                                                                                                                                                                                                                                                                                                                                             | Evidence                             |
| - | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------ |
| 1 | Full repo analysis (README, design spec, all 13 source modules, 7 test files, both workflows, pyproject, gitignore, git history)                                                                                                                                                                                                                                                                 | files read in full this session      |
| 2 | **AGENTS.md created** (~180 lines): commands, undeclared-ffmpeg gotcha, no-lint reality, pipeline architecture, module map, interchange formats, emission-time physics invariant, three time bases + `t0_map` bridge, segment-ephemeralness/`relocate_row`, CPA-cache fingerprint, bucketed pair join, scoring invariant with regression history, testing patterns, runtime caching, conventions | commit `cb9b3e6`, pushed             |
| 3 | Critical self-review pass on AGENTS.md before commit: added `soundfile`-unused and `uv.lock`-tracked notes, fixed paragraph flow                                                                                                                                                                                                                                                                 | included in `cb9b3e6`                |
| 4 | Origin remote changed to the LarsArtmann fork, verified stored + reachable                                                                                                                                                                                                                                                                                                                       | `git config --get remote.origin.url` |
| 5 | Pasted external context triaged under `verify-external-claims`: 4/4 durable claims verified (DOPPLERGEIST, doppler-experiments, pyfr24, traffic); unverifiable video claims refused; verified facts encoded as a related-projects note                                                                                                                                                           | commit `a7f77f8`, pushed             |
| 6 | Fork position established: 2 ahead / 0 behind upstream `mjshiggins`                                                                                                                                                                                                                                                                                                                              | `git ls-remote` both remotes         |
| 7 | Safety check on the foreign reformat: full suite still green on the reformatted tree                                                                                                                                                                                                                                                                                                             | 19 passed in 60.16 s                 |
| 8 | Wheel contents claim checked before claiming it (`py.typed` really ships)                                                                                                                                                                                                                                                                                                                        | `unzip -l dist/*.whl`                |

## b) PARTIALLY DONE

1. **AGENTS.md accuracy over time** — correct today, but two claims are drift-prone: the hard-coded
   "(19 tests)" count, and "no formatter configured" which becomes false the moment the
   uncommitted `dprint.json` is kept. Needs a refresh after the reformat decision.
2. **Formatter story** — `dprint.json` appeared (JSON/YAML/Markdown/Dockerfile plugins only,
   _no Python plugin_), yet all 22 Python files got a black-style reformat from some other tool.
   The Python formatter is unidentified and unwired; the two configs contradict each other.
3. **Pasted-context integration** — the durable, verifiable half is encoded; the video-workflow
   half (Audacity/QGIS/Sonic Visualiser/3DEP) remains unverified leads, correctly not encoded.
4. **`.config/metadata.yaml`** — read; contents are bare timestamps with no provenance, so it
   documents nothing actionable yet.

## c) NOT STARTED

Everything in section (f) below beyond what this session touched: no TODO_LIST.md/FEATURES.md,
no DOMAIN_LANGUAGE.md, no linter/type-checker/pytest-config, no upstream remote, no fork
versioning/PyPI decisions, no tests for terrain/AircraftTypes/CLI, no ffmpeg-missing UX, no
`--version` flag. None of these were in this session's mandate; listed for harvest.

## d) TOTALLY FUCKED UP

Nothing I produced is broken — both commits are pushed, verified, and green. The one genuinely
bad _situation_ (not my doing, but now the repo's state):

- **The working tree is dirty with a 22-file, +1402/−377 reformat of unknown provenance**
  (every source and test file reformatted black-style, plus new untracked `dprint.json` and
  `.config/metadata.yaml`). Per the never-touch-work-you-didn't-author rule I inspected it,
  verified the suite still passes on it, and left it untouched — but it blocks a clean tree and
  its origin is unidentified (`.config/metadata.yaml` holds only timestamps, created
  2026-11-04T01:36Z; `dprint.json` lacks any Python plugin, so it did not cause the Python diff).

Near-miss worth recording: had that formatter run _before_ my commits instead of after, my
AGENTS.md diffs would have been mixed with reformat noise and much harder to review.

## e) WHAT WE SHOULD IMPROVE (self-critique: forgotten / could do better)

1. **I forgot to stop and flag the foreign diff the moment I saw it.** I reported it at the end of
   the turn instead of interrupting with a provenance question immediately.
2. **I forgot to read `.config/metadata.yaml` during the first inspection** (only `ls`'d it);
   read it only during this report. It contains no attribution anyway, but that was luck, not method.
3. **Two commits where one would do** — the related-projects note (`a7f77f8`) landed minutes after
   the main AGENTS.md commit because the pasted context arrived in between; harmless but sloppy
   sequencing on my part.
4. **Drift-prone phrasing in AGENTS.md** — "(19 tests)" should have been written drift-proof;
   "no formatter configured" should have been conditioned on the repo's flux.
5. **I verified upstream sync only now, during this report** — it belonged in the same breath as
   the remote change.
6. **I didn't run `dprint` (or any formatter check) against AGENTS.md itself** after `dprint.json`
   appeared, so I can't say whether a future format run would churn it.
7. The wheel-build verification left `dist/` for a moment — cleaned, but could have built to a
   temp dir.

## f) Up to 50 things to get done next

_A brainstorm to harvest, not a commitment list. Ordered roughly by impact within each group._

**Decisions & cleanup (blocked on your answers, see g):**

1. Decide the fate of the 22-file foreign reformat: keep + commit, or revert (Q1)
2. Identify the tool that produced the Python reformat (candidates: BuildFlow hook, ruff/black via
   another agent session — `dprint.json` demonstrably has no Python plugin)
3. If kept: reconcile formatter configs — add a Python formatter to `dprint.json` or document the
   deliberate split (dprint for MD/JSON/YAML/Dockerfile, X for Python)
4. If kept: update AGENTS.md "no formatter configured" conventions bullet
5. Commit or remove `dprint.json` + `.config/metadata.yaml` alongside decision 1
6. After decision: re-run full suite and push the resulting clean state

**Docs (harvest targets):**
7. HARVEST section (f) into `TODO_LIST.md` (docs-health HARVEST mode) — the repo currently has none
8. Create `FEATURES.md` (honest inventory: pipeline stages, validation status on two recordings)
9. Create `docs/DOMAIN_LANGUAGE.md` (Doppler, ENU, CPA, emission vs observation time, whitening,
ridge, locked scoring, silence filter — AGENTS.md currently carries fragments of this)
10. Document the `EventFit` JSON schema (fields, units, time conventions) for consumers
11. Document the two `.npz` interchange formats (Spectrogram `t/f/S`; Trace `meta` + `a{i}` arrays)
12. Inventory `docs/results/` artifacts (what each PNG/CSV/JSON is, which README section cites it)
13. README: mention `DOPPLERTRACK_CACHE` (currently only in code + AGENTS.md)
14. README: state the ffmpeg runtime requirement explicitly (not pip-installed)
15. Decide whether AGENTS.md should be contributed upstream as a PR (needs `verify-before-filing`

- `github-voice` skills before opening anything)

**Quality & tooling:**
16. Add ruff (lint + format) with committed config
17. Add mypy/pyright — `py.typed` is shipped while nothing checks types
18. Add a `[tool.pytest.ini_options]` section to pyproject (none exists)
19. Mark the ~60 s synthetic pipeline test as `slow` so fast loops can `-m "not slow"`
20. Pre-commit hook running formatter + linter once decided
21. CI: cache uv dependencies for speed
22. Friendly error when ffmpeg is missing (`audio.load_audio` currently surfaces a raw
FileNotFoundError from subprocess)
23. Remove the unused `soundfile` dependency (or justify keeping it)
24. Remove vestigial `hello()` from `__init__.py` (real entry point is `cli:main`)
25. Add `--version` flag to the CLI
26. Type-annotate the remaining untyped public functions
27. Wrap CLI errors in friendly messages instead of raw tracebacks (missing file, bad JSON, etc.)

**Domain / feature ideas (ROADMAP fuel):**
28. Attack the thin score margins (README: 4.9 % Oyster Bay / 2.5 % eagle cam) — the known
weakness of brightness-only scoring
29. Generalize `search` beyond exactly two events (`refine --extra` exists; the search itself is 2-event)
30. Auto-chain `detect` → `search` (currently the operator picks events by hand from the table)
31. Parallelize the serial `locked_score` loop in `run_search`
32. Print search progress before the first 500 pairs (currently silent until then)
33. Make CPA-cache recompute loud: log _why_ a fingerprint mismatched
34. Chain `detect` → `search-single` automatically for known-absolute-time recordings
35. Batch terrain prefetch for the whole grid up front instead of per-call tile sets

**Fork / repo management:**
36. Add an `upstream` remote (`mjshiggins`) + a documented sync routine
37. Decide fork versioning (both repos sit at 0.2.0; divergence strategy undefined)
38. Decide the PyPI job's fate in the fork: `release.yml` publishes via trusted publishing scoped
to `mjshiggins/dopplertrack` — tags on the fork will fail that job until configured or disabled
39. Optional: CI badge on the fork README
40. Optional: branch protection requiring CI on fork main

**Test gaps (noticed while reading the suite):**
41. Tests for `terrain.py` (currently zero; HTTP mockable)
42. Tests for `adsb.AircraftTypes` offline path (fixture CSV)
43. Tests for `cli.py` argument parsing
44. Test for `pipeline.relocate_row`'s "flight not in these traces" error path
45. Smoke test for `plots.py` (Agg backend)
46. Guard test asserting no test performs network I/O (protects the offline-suite invariant)

**AGENTS.md upkeep:**
47. Re-verify all AGENTS.md claims after decisions 1–6 land (formatter bullet, test count)
48. Check AGENTS.md survives a dprint markdown-format run unchanged (or format it once, commit)
49. Add a pointer to the `docs/status/` convention now that it exists
50. Record the `insteadOf` display quirk + fork/upstream distinction in AGENTS.md if the fork
strategy (Q2) makes it durable

## g) Questions I cannot figure out myself

1. **The 22-file reformat, `dprint.json`, and `.config/metadata.yaml`: keep or revert?** I verified
   nothing identifies the author (metadata.yaml is bare timestamps; dprint.json has no Python
   plugin, so it didn't cause the Python diff). If it's yours or a tool you ran: I'll commit it
   with a clear message and wire the Python formatter properly. If not: I'll revert it.
2. **What should this fork be?** Stay synced with `mjshiggins/dopplertrack` and PR work back
   (AGENTS.md, docs), or diverge as your own line? This decides versioning, whether the PyPI job
   in `release.yml` should be disabled (it will fail on fork tags without trusted-publisher setup
   for `LarsArtmann/dopplertrack`), and whether README edits are even welcome here.
3. **Which direction first for the 50-item list:** repo hygiene/tooling (formatter/lint/types/CI,
   items 16–27) or domain work (score margins, multi-event search, auto-chaining, items 28–35)?
   Both are legitimate; I cannot infer your priority.
