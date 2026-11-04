# Status Report — BuildFlow Red→Green: Quality Gate Fix Session

**Date:** 2026-11-04 04:10 CET
**Repo:** `github.com/LarsArtmann/dopplertrack` (fork of `mjshiggins/dopplertrack`), branch `main`
**Session span:** ~02:37–04:00 CET, 2026-11-04
**Trigger:** `buildflow --fix --build-mode full` exited **69** with a 4-consecutive-run
identical-failure loop on `dprint-format` and `ruff-check-fix` (23 ruff errors + 1
dprint hard error). User instruction: "fix all".

---

## Scope of this report

**VERIFIED (fresh command output this session):**

| Claim                                  | Verified via                                                                                                                                       |
| -------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| BuildFlow full pipeline passes, exit 0 | `buildflow --fix --build-mode full` → "passed with warnings 27/30, 1m5s"; second full run + `buildflow --build-mode fast` → exit 0 (cached, 66 ms) |
| Ruff clean                             | `ruff check src tests` → "All checks passed!" (was 23 errors)                                                                                      |
| Tests pass post-ruff-format            | `uv run pytest -q` → 19 passed in 60–69 s (run **twice**: before and after BuildFlow's ruff-format rewrote 3 files)                                |
| dprint clean                           | `dprint check` → no findings (was 1 hard parse error + 5 unformatted files)                                                                        |
| Fixture is gzip                        | `od -c` on `tests/data/trace_full_a2f38b.json` → magic bytes `1f 8b`                                                                               |
| Bandit real findings = 2               | `buildflow -s bandit-check --format finding` parsed: 224 entries, of which 2 actual issues (B404, B603, both `audio.py`)                           |
| Vulture 12 → 8                         | `buildflow -s vulture --format finding` before/after dead-code removal                                                                             |

**NOT verified (and why):**

- **Provenance of the pre-existing working-tree modifications.** All `src/` and
  `tests/` files were already modified before this session started (session-start
  git snapshot). I never determined who made them or whether they were complete;
  per the global AGENTS.md auto-commit-daemon contract I built on top and did not
  revert anything. Diff-stat vs HEAD therefore conflates their work with mine.
- **Release/CI pipelines still work after dprint touched `release.yml`** (comment
  alignment only — whitespace-level, low risk, but no actionlint or dry-run done).
- **Full bandit/mypy finding lists** (sampled only; counts and the 2 real bandit
  items verified).
- **Whether BuildFlow's dprint auto-configure will preserve my custom excludes on a
  future config refresh** (survived 3 subsequent runs today; a version upgrade is
  the real test — mitigated by AGENTS.md documentation).
- **The 9-unavailable-tools health warning** was not itemized or resolved beyond
  installing ruff + dprint (interrogate is not in nixpkgs; others look irrelevant
  to a Python repo — not exhaustively checked).
- **PyPI/npm-class release readiness** — untouched, out of scope.

---

## a) FULLY DONE

1. **BuildFlow failure loop broken.** Exit 69 → exit 0. Both failing steps green;
   second consecutive full run green (loop detector has nothing more to report).
2. **All 23 ruff errors fixed by hand** (none auto-fixed blind; every fix reviewed):
   - `adsb.py`: blind `except Exception` in `_scan_one` → narrowed `TRACE_PARSE_ERRORS`
     tuple `(OSError, ValueError, KeyError, IndexError, TypeError, zlib.error, EOFError)`
     — covers gzip corruption, truncated/invalid JSON, unexpected structure; deliberately
     excludes `MemoryError`/`RecursionError` (crash-loudly is correct there).
   - `fetch.py`: new `_parse_quiet()` helper — kills the BLE001 blind except AND the
     S112 try/except/continue by moving the guard out of the loop (mirrors `adsb._scan_one`).
   - `score.py`: B008 (call in argument defaults) ×4 → module constants
     `DEFAULT_SHIFTS` / `DEFAULT_F0_SCALES`; verified `sweep_scores` never mutates
     them, so sharing is safe. RUF059 `_r` in `modelled_curve`.
   - `audio.py`: RUF046 — `int(round(x))` → `round(x)` (round() already returns int).
   - `cli.py`: SIM115 ×6 — new `load_event()` context-managed JSON→EventFit loader
     (4 sites), 2 `with open(a.out)` write blocks; FURB162 — dropped `.replace("Z",
     "+00:00")` (`fromisoformat` handles `Z` natively on the 3.12 floor).
   - `tracks.py`: unused `score0` unpack ×2 → `_`.
   - Tests: `_`-prefixed unused unpack targets in `test_physics.py` (×4),
     `test_pipeline_synthetic.py` (×2).
3. **dprint hard error fixed** via `dprint.json` excludes: `tests/data/**` (the
   gzip fixture masquerading as JSON) and `docs/results/**` (committed CLI-output
   artifacts — formatting them would churn on every regeneration).
4. **Formatting debt paid**: `dprint fmt` → `release.yml` comment alignment + 4
   markdown files normalized (README, AGENTS, docs/status report, design spec).
   Diff reviewed line-by-line: benign (table padding, `*x*`→`_x_` emphasis style).
5. **Toolchain installed per `buildflow doctor` recommendation**: `nix profile add
   nixpkgs#ruff nixpkgs#dprint` — also locally reproducible now (ruff 0.17.3
   reproduces BuildFlow's finding set exactly: 23/23).
6. **Dead code removed** (vulture-detected, zero callers verified by grep first):
   `Segment.trace_idx` field (+2 construction sites), `search.grid_lla()`,
   `pipeline.run_search(top_pairs=)` ignored param, unused `tk` loop var in
   `test_score_coverage.py`. Vulture findings 12 → 8.
7. **AGENTS.md updated** (memory protocol): stale "no linter/formatter configured"
   claim replaced with BuildFlow-ownership reality; `dprint.json` excludes marked
   load-bearing with rationale; the 8 accepted warning findings documented with
   reasons; new ruff-compatible idioms added to Conventions.
8. **Verification loop closed properly**: pytest run twice (before AND after
   BuildFlow's ruff-format rewrote adsb/cli/tracks — the rewrite landed after my
   first test pass; caught and re-verified).

## b) PARTIALLY DONE

1. **Vulture cleanup** — 4 genuinely-dead items removed, 8 remain **by documented
   choice** (io.RawIOBase interface methods, documented-vestigial `hello()`,
   3 diagnostic plot helpers that are the programmatic API, 2 test-stub params).
   Acceptable, but a whitelist mechanism could make the intent machine-readable.
2. **mypy noise (45 findings)** — triaged as import-not-found noise (numpy/requests
   stubs absent in the nix-run env; project deliberately has no type-check gate).
   Documented, not config-fixed. A minimal `[tool.mypy]` + `types-requests` could
   cut it to signal, but that is a policy change I chose not to make unilaterally.
3. **Bandit (224 parsed entries, 2 real)** — the 2 real findings (B404 import
   subprocess, B603 subprocess-without-shell on `audio.py`'s ffmpeg call) accepted
   and documented; **not** silenced with `# nosec`. Note: ~222 of the 224 "findings"
   are bandit's own INFO log lines parsed as findings — smells like a BuildFlow
   finding-parser artifact (candidate upstream issue, not yet verified/filed).
4. **Tools-unavailable health check** — reduced from the original set by installing
   ruff + dprint; `interrogate` is not packaged in nixpkgs (install failed, retried
   without it); the rest of the 9 were not itemized.
5. **`TODO_LIST.md` harvest** — section (f) below is brainstorm-grade; the repo has
   no TODO_LIST.md/FEATURES.md/ROADMAP.md, so per docs-health this report needs a
   HARVEST/BUILD pass. Not done yet (awaiting instruction).
6. **BuildFlow-generated files** — `.github/dependabot.yml` and `SECURITY.md` were
   created by auto-configure mid-run, found unformatted by dprint, formatted by me.
   Still **untracked**; committed or not is your call.
7. **AGENTS.md** — updated, but edits landed mid-buildflow-run (dprint step had
   already executed); I reformatted after. Final state is clean, but the sequence
   was sloppy.

## c) NOT STARTED

1. Committing **this session's changes** (harness forbids commit without explicit
   request; auto-commit daemon may pick them up — untracked files at risk of
   lingering).
2. Committing/suppressing the **pre-existing modifications** (provenance unknown —
   see Questions).
3. `TODO_LIST.md` / `FEATURES.md` / `ROADMAP.md` / `CHANGELOG.md` (docs-health
   BUILD pass — none exist in this repo).
4. On-demand BuildFlow scans never run: `markdown-lint`, `gitleaks`, `codespell`.
5. A project `.buildflow.yml` (documented skips/rationale) — repo is pure
   auto-detect right now.
6. Pre-commit hook (`buildflow precommit install`) — not installed.
7. CI gate beyond pytest (no ruff/buildflow step in `.github/workflows/ci.yml`;
   whether that belongs in-repo or fleet-upstream is undecided).
8. `flake.nix` — none exists (global norm says dev envs live in flakes; here
   BuildFlow + uv fill that role — decision pending).
9. Fixture rename `trace_full_a2f38b.json` → `.json.gz` (honest extension; touches
   `test_adsb.py` + the dprint exclude) — flagged, not done.
10. Upstream filing of the bandit-parser findings-count artifact (would need
    verify-before-filing pass first).

## d) TOTALLY FUCKED UP

Final state: **nothing** — the build is green and every problem found this session
ended in one of: fixed, documented-deliberate, or listed as a question. But full
honesty about mid-session stumbles (all recovered):

1. **Edit-before-View violations** — fired 3 multiedit/edit calls before reading the
   files with the View tool; all 3 rejected, wasted calls. Fundamental rule, no excuse.
2. **First nix install included `interrogate`** → whole command failed (not in
   nixpkgs); had to retry with just ruff+dprint. Should have checked availability
   first (doctor already told me the set).
3. **Backgrounded buildflow runs obscured the headline verdict** — `tail -30` /
   `job_output` kept returning summary tails without the "passed/failed" line or
   exit code, forcing an extra cached fast-mode run just to capture exit 0.
4. **Grep against ANSI-colored buildflow output failed** twice before adding
   `NO_COLOR=1`. Known pitfall, walked into it anyway.
5. **`uv run ruff` first attempt failed** (ruff is not a project dependency) — I
   knew BuildFlow provisions its own tools and still reached for the project venv first.
6. **Original state was the fucked-up thing**: 4 consecutive identical build failures
   with an active loop-detector complaint; nobody had triaged them before this session.

## e) WHAT WE SHOULD IMPROVE

1. **Close the loop at the tool, not the repo, for fleet-level artifacts.** The
   bandit findings-parser counting its own log lines (~222 of 224) as findings is a
   likely BuildFlow bug — a candidate upstream issue (verify at source first per
   verify-before-filing, then file in the BuildFlow repo, not here).
2. **Make deliberate non-fixes machine-readable.** The 8 accepted vulture items and
   the bandit B404/B603 acceptances currently live only in AGENTS.md prose. A
   whitelist/`# nosec` mechanism would let the gate tighten later without re-triage.
3. **Provenance discipline on shared working trees.** I built atop uncommitted
   modifications I did not author. Next time: note provenance explicitly at session
   start (done here in Scope, but only after the work).
4. **Format-then-verify ordering.** Edit files → run formatters → run tests in one
   settled sequence, instead of interleaving AGENTS.md edits with a running pipeline.
5. **Read tool-availability up front** (`buildflow doctor` was step 2 in the skill
   and I skipped it until things felt off — it would have saved the nix-install
   detour).
6. **ruff-format interplay**: BuildFlow runs `ruff format` as a separate step; my
   hand-edits got rewrapped afterwards (cosmetic, but each rewrite invalidates my
   just-run test verification). Either pre-run `ruff format` mentally (compact style)
   or expect the rewrite and re-test — the latter is what happened; make it deliberate.
7. **dprint.json excludes durability**: they survived 3 runs but are one auto-config
   refresh away from vanishing; consider whether BuildFlow supports exclude
   preservation via `.buildflow.yml` so policy lives where the tool expects it.

## f) Up to 50 things we should get done next

_Brainstorm, not commitment — most are ROADMAP fuel; a docs-health HARVEST pass
should route them._

**Immediate (session fallout):**

1. Commit `.github/dependabot.yml` + `SECURITY.md` or suppress via `.buildflow.yml`.
2. Commit the session's fixes (or confirm the auto-commit daemon did).
3. Resolve provenance of pre-existing src/tests modifications (see Questions) and commit.
4. Run docs-health HARVEST on this report → seed `TODO_LIST.md`.
5. docs-health ANNOTATE the 02:51 status report if it contains now-stale claims
   (e.g. "no linter configured").
6. Re-run one full `buildflow` after everything is committed (green on committed
   state, not just working tree).
7. Itemize the "9 tools unavailable" list; classify relevant vs irrelevant for a
   Python repo; install or dismiss each.
8. Decide `# nosec B404,B603` on `audio.py` vs keep-as-accepted (needs your policy call).
9. Add `types-requests` (+ numpy stubs decision) to dev deps to cut mypy import noise.
10. Decide on minimal `[tool.mypy]` in pyproject vs keep no-gate stance.
11. Verify dprint excludes survive a BuildFlow upgrade (`buildflow upgrade` then check).
12. Investigate the bandit findings-parser artifact; if real, file upstream in
    BuildFlow (verify-before-filing + github-voice).
13. Run the on-demand scans once: `buildflow -s gitleaks`, `-s codespell`, `-s markdown-lint`.
14. actionlint (or a workflow-dispatch dry run) on the dprint-touched `release.yml`.
15. Review the diff-vs-HEAD boundary: split pre-existing modifications from session
    fixes before any commit so history reads honestly.

**Repo hygiene (noticed this session, unaddressed):**
16. Delete vestigial `src/dopplertrack/__init__.py::hello()` (documented vestigial).
17. Remove `soundfile` from pyproject dependencies (declared, never imported).
18. Fix `pipeline.py` docstring that references notebooks that don't exist.
19. Rename `tests/data/trace_full_a2f38b.json` → `.json.gz` (touches test + exclude).
20. Create `TODO_LIST.md`/`FEATURES.md`/`ROADMAP.md` (docs-health BUILD).
21. Create a minimal `.buildflow.yml` with documented skips (repo currently has zero
config; unknown-key warnings will nag if it ever drifts).
22. Decide pre-commit hook: `buildflow precommit install` or documented refusal.
23. Decide flake.nix/devShell policy for this repo (uv+BuildFlow vs flake norm).
24. Check `.gitignore` covers `.ruff_cache/`, `.pytest_cache/`, `.venv/` (they exist
on disk; verify ignored, not untracked-noise).
25. Identify the "1 file under excluded paths (unscanned)" and "2 URLs excluded by
config" from the link scan; confirm intentional.
26. Consider pytest-cov so BuildFlow's coverage step has something to consume.
27. `docs/results/`: add a README note on how artifacts are regenerated (they're now
format-excluded; provenance matters).
28. Decide whether ruff belongs in CI as a fast gate (or accept BuildFlow-only
enforcement; fleet-consistency question).

**Quality-gate depth (now that the gate is green):**
29. Tighten buildflow gate: try `--strict` (warnings→failures) to see the real cost.
30. mypy triage pass on real (non-import) findings — currently all noise; first real
finding should trigger the policy decision.
31. bandit: review the full 2-finding context (ffmpeg invocation argv construction)
once, then either nosec with justification or close.
32. Vulture whitelist file for the 8 accepted names (if BuildFlow supports passing
one) so the count can go to zero honestly.
33. Evaluate pyupgrade/go-auto-upgrade equivalents for Python (`buildflow --fix`
already surfaces them; check nothing was skipped).
34. Coverage of `score.py`/`search.py` edge paths (pair join bucket edges) — the
brute-force-equality test exists; consider property tests.

**Upstream/fork concerns (this is a fork):**
35. Decide upstream contribution policy for the fixes made here (mjshiggins/dopplertrack
is the upstream; ruff-idiom changes are portable).
36. Track upstream for changes that would conflict with the fork's working tree.
37. Homepage/Issues URLs in pyproject still point at upstream — correct if the fork
is the living repo.
38. Consider tagging a release (0.2.1?) once the tree is committed — release flow is
tag-driven and untested from this fork.

**Documentation:**
39. README: mention BuildFlow as the quality gate for contributors.
40. AGENTS.md: add the nix-profile tool list (ruff, dprint) to Commands.
41. Document the three time bases / TRACE_PARSE_ERRORS rationale where the code
lives (docstrings), not only in AGENTS.md.
42. Sweep all docs for claims invalidated by this session ("no formatter exists" etc.).

**Process:**
43. Capture `NO_COLOR=1` as default for buildflow invocations in scripts.
44. Add `buildflow history --step <tool> --last-error` to the debugging playbook in
AGENTS.md (it carried the full ruff output that the pipeline summary truncated).
45. Record the "View before edit, even when sed already showed the text" lesson.
46. Keep ruff-format parity: run `ruff format --check` locally before handoff to
avoid BuildFlow rewrites invalidating verifications.
47. Timebox: budget flag (15 m) was never a constraint here — note that full mode is
~1 m for this repo; tune budgets downward.

**Deferred/roadmap-grade:**
48. Split-brain risk register: BuildFlow fleet defaults vs per-repo policy — one
place (`.buildflow.yml`) with rationale, reviewed on each BuildFlow upgrade.
49. Security posture: bandit is Low-severity-only here; decide if gitleaks
scheduled runs (not on-demand) are wanted for a repo that handles recordings.
50. Upstream the useful bits: TRACE_PARSE_ERRORS-style narrowed exception tuples are
a pattern other fleet repos might want — candidate for a lesson in crush-config
`references/lessons.md` (commit there, not in-session).

## g) Questions I cannot figure out myself

1. **Whose are the pre-existing uncommitted modifications?** All `src/` and `tests/`
   files were modified before this session (per the session-start snapshot); I
   verified none of my edits conflict with them and the full suite passes on the
   combined tree — but I cannot know if they are finished work, another agent's
   WIP, or abandoned. Commit as-is, or should someone review them first?
2. **Policy call: silence or accept?** Should bandit B404/B603 on `audio.py` get
   `# nosec` annotations (machine-readable, tightens future gates) or stay
   accepted-in-prose? Same question for a vulture whitelist. This sets the fleet
   precedent for how this repo treats warning-severity findings.
3. **Should `.github/dependabot.yml` + `SECURITY.md` stay?** BuildFlow auto-created
   them (dependabot now watches numpy/pandas/etc. for a PoC fork; SECURITY.md
   publishes a private-vulnerability channel for an upstream-owned project). Keep,
   commit, or add a `.buildflow.yml` skip — your intent decides, and dependabot
   PRs will start arriving the moment it's committed.

---

_Report written per status-report skill (`.md` default, DECIDED 2026-10-27 D.g4).
Not committed — Crush harness forbids commits without explicit request; the
auto-commit daemon picks the file up. WAITING FOR INSTRUCTIONS._
