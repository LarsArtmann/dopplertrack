# Status report: Pareto plan execution — EU validation phase 1 + tooling/trust work

> Written 2026-11-14 09:15 CET by GLM (glm-5.3-flash) via Crush, executing
> docs/planning/2026-11-14_00-42_pareto-eu-proof-first-execution-plan.md under the
> owner's "WHOLE TODO LIST" mandate. This report covers that execution session only.

## Context

The session executed the committed Pareto plan: tiers 1%/4% and most of the 20% tier.
The founding question ("does the product work in EU?") advanced from "data path
verified" to **two single-event matches of heard flyovers to their ADS-B aircraft at
the published microphone positions** — with the full two-event EU verdict still open
(the feed, not the code, is the limit). Eleven commits landed on `main`, all passing
the three-way gate (pytest, docs-gates, buildflow) at commit time except one process
slip documented in §d.

- Commits this session (chronological): `ea6dc7a` --version, `f7b28ea` friendly CLI
  errors, `6d1e523` slow marker, `4c934ca` coverage command, `d09cda8` interchange
  formats doc, `5f93742` FEATURES.md, `c3c81e2` DOMAIN_LANGUAGE.md, `f6e9638` chores
  (fixed re-commit of a bad `git add -A`, see §d), `4966662` EU validation phase 1,
  `99b8ebf` test coverage, `7c33c02` CI cache/badge. Working tree at report time:
  AGENTS.md trim (220-line cap restored) + TODO_LIST rows pending commit with this report.
- Suite: 49 → 78 tests (73 pass, 3 skip, 2 xfail in the full ~2 min run; `-m "not slow"`
  fast loop is ~4 s). docs-gates 5/5 green at every commit; buildflow exit 0 at every
  commit except `4966662` (committed at exit 75, retried green — §d).

## a) Fully done

1. **C1** `--version` flag + test (`ea6dc7a`; src/dopplertrack/cli.py, tests/test_cli.py).
2. **C2** Friendly CLI errors for the three families a stranger hits first — missing
   ffmpeg, wrong path, corrupt/non-object event JSON — each printing what/why/fix and
   exiting 1 (`f7b28ea`; CliError, _fail, tests/test_cli.py).
3. **C3** `slow` marker on the five minute-scale tests; fast inner loop 128 s → 4 s
   (`6d1e523`; pyproject [tool.pytest.ini_options]).
4. **B1+B2+B3** `coverage DATE BBOX` command: streams a day archive, reports seen/failed/
   bbox counts, prop share, unknown-designator count, registration countries, top
   designators, `--json` output (`4c934ca`; src/dopplertrack/coverage.py, fetch.py stats
   dict, cli.py; tests in test_coverage.py/test_fetch.py). The standalone probe script was
   superseded by the command (plan B3.4 resolved by absorption, noted in the commit).
5. **C4** docs/interchange.md: every pipeline file format specified with units and time
   bases, linked from README (`d09cda8`).
6. **C5** FEATURES.md: honest status inventory with evidence pointers (`5f93742`).
7. **C6** docs/DOMAIN_LANGUAGE.md: the domain vocabulary (`c3c81e2`).
8. **D1** chores: hello() removed, soundfile removed via `uv remove`, fixture renamed to
   `.json.gz`, AGENTS notes updated (`f6e9638`).
9. **D3-D5** 24 new tests: terrain (Terrarium decode, projection, disk+memory cache,
   prefetch, damaged-tile recovery vs a mocked tile server), CLI argument contracts,
   Agg-backend plot smoke, offline-fitting AircraftTypes fixture, an autouse socket guard
   enforcing the offline-suite invariant, and a pair-join completeness property test over
   brute force across bucket-edge deltas (`99b8ebf`).
10. **D6** CI: setup-uv `enable-cache`, `workflow_dispatch`, README badge; actionlint
    clean on both workflows (`7c33c02`). release.yml deliberately untouched.
11. **EU phase A** A1-A5 executed to phase-1 depth (see b): archive availability
    verified per candidate date via the repo's own `release_asset_urls`; five radio
    aporee recordings downloaded, spectrogrammed, detected; offset-scan method invented
    and preserved as scripts/offset_scan.py; two single-event matches at the true pins;
    everything documented (docs/experiments.md EU section, docs/coverage.md,
    docs/results/eu_2026_lgc/) and committed (`4966662`).
12. **D7 partial** gitleaks clean, codespell one warning-level finding (accepted:
    "unparseable" is correct US spelling; gate exits 0); ODbL-1.0 confirmed as the
    adsb.lol archive license (verified: GitHub API repo adsblol/globe_history_2026,
    2026-11-14) — attribution note still to write (§f).
13. AGENTS.md restored under its 220-line cap after the EU paragraph push (buildflow
    doctor caught it; trimmed to 218).

## b) Partially done

1. **EU validation (A1-A5)**: phase 1 landed — two 2026 UK recordings under the Luton
   approach matched single heard events to their airliners at the published pins
   (HA-LDE A320neo d=692 m score 4.15; EI-DWC B737 d=625 m score 2.90; both needed
   `fetch --keep-jets` and `--d-tol 0.3 4.0`). NOT done: the full two-event verdict.
   Two independent blockers: (i) partner aircraft are feed-invisible (EU GA is heavily
   Mode-S/FLARM-only — LGC day: 1,362 box traces, 270 props, and the heard-but-unlisted
   aircraft repeated across all five recordings); (ii) jet shaft-harmonic sweeps fit
   with 2-10x underestimated CPA distance, so the default 0.4-2.5x gate rejects true
   flights. The loose-gate null is unconvincing on its own (a wrong flight scores 4.39
   vs the winner's 4.30) — docs/experiments.md states this plainly.
2. **coverage.md** written with three measured days, but the "regenerate these numbers"
   note and a per-country table live only partially there.
3. **D7** ODbL assessment half-done (license identified, attribution/DATA_LICENSE note
   for adsb.lol-derived docs/results artifacts not yet written).
4. **TODO_LIST refresh** for this session's done rows (chores row, FEATURES/DOMAIN row,
   EU row) is staged but the full docs-health HARVEST/ANNOTATE pass over older reports
   (D10.3) has not run.

## c) Not started

- **D2** type annotations sweep (adsb/audio/doppler/geo/terrain/fetch/score/verdict).
- **D8** upstream/BuildFlow filings (bandit findings-parser artifact, missing-identity-
  fields warning; verify-before-filing gates + github-voice; upstream PR template check).
- **D9** BuildFlow follow-ups (vulture whitelist file, split-brain register, doctor
  cadence, pyupgrade equivalents, unavailable-tools list, dprint-excludes upgrade test).
- **D10** sweeps: annotate older status reports; gh-search/NO_COLOR re-verify;
  TRACE_PARSE_ERRORS lesson to crush-config; push `main`; delete `origin/upstream-pr`
  (owner authorized under this mandate — not yet executed).
- **D11** EU data edges: mlatonly pod probe, terrain above 60 N, retention question.
- **D12** roadmap spikes (margin experiment, auto-chain, >2-event design).
- **D6.5** workflow_dispatch dry run on GitHub (needs the push first).
- **Final** full-gate verification pass + push + loop audit.

## d) Totally fucked up

1. **Committed against a red gate.** The EU docs commit `4966662` ran in one chained
   command where a `;` let `git add`/`git commit` execute after buildflow exited 75
   (transient spawn starvation at 15-min load 25). The gate is the point of the loop;
   the commit preceded its green retry. Fixed ex post (`--failed-only` exit 0), but the
   ordering bug was mine: gates must gate the commit, not decorate it.
2. **`git add -A` swept the hold-aside release.yml** into the D1 commit — the exact file
   a standing decision kept uncommitted. Caught immediately (soft reset, restage
   without it, recommit as `f6e9638`), but the mistake was the `-A` reflex; explicit
   paths are the rule in this repo.
3. **Four subagent dispatches burned on provider limits** (zai rate limit, gemini out
   of credits, huggingface and hyper payment-walled) before doing the A1 research
   myself; ~35 min of wall clock lost to retries that a first-result fallback would
   have avoided.
4. **Malton fit-window thrash**: three re-fits drifted to neighbouring peaks before
   recognizing detect's own per-window fits should be used directly as event JSONs —
   ~40 min spent re-deriving what the pipeline already computes.
5. **The EU result can oversell itself.** "Two matches at the true pins" is real but
   thin: verdict says "insufficient", the loose-gate null has a wrong flight above the
   winner, and both matches needed widened gates chosen while knowing the answer's
   location. The write-up states this; any quoting of this session should too.
6. **AGENTS.md cap violated** by my own EU paragraph (226 > 220) — the repo's own
   doctor warned at the next buildflow run. Caught by the machine, not by me.

## e) Improvements made on the way

- The pair-join property test re-derived the deleted upstream brute-force equality
  test as a completeness property, and caught a real semantic subtlety in the process:
  `b_min`/`b_max` are flight-1-side buckets (tests/test_pair_join_property.py).
- The offline invariant is now enforced by a socket guard, not promised (tests/conftest.py).
- The offset-scan method (event/flight Δt alignment under unknown recording start) is
  the session's reusable invention: scripts/offset_scan.py, documented in
  docs/experiments.md.
- coverage.md + `coverage` turned the EU readiness question into a one-command answer
  with three measured days.
- The A320neo/B737 discovery (airliner shaft harmonics sweep audibly and match under
  the pipeline) reframes EU validation: approach corridors are the one EU environment
  with guaranteed-visible flyovers — recorded in docs/experiments.md and TODO_LIST.
- All external facts in this session's docs carry verification stamps (archive dates
  probed via the release API 2026-11-14; ODbL-1.0 via GitHub API 2026-11-14; aircraft
  types via api.adsb.lol /v2/icao live lookups).

## f) Next tasks (ranked; sources cited; TODO_LIST carries these)

1. Push `main` to origin (mandate-authorized), then `gh workflow run ci.yml` as the
   D6.5 dry run and verify the badge resolves. — evidence: this report §c; TODO_LIST CI row.
2. Delete `origin/upstream-pr` (`git push origin --delete upstream-pr`; PR #3 merged at
   c3ffa15 upstream). — TODO_LIST High row; docs/status/2026-11-04_05-12 §4.
3. Decide the hold-aside release.yml action bump (BLOCKED on owner). — TODO_LIST row added this session.
4. File the BuildFlow bandit findings-parser artifact + missing-identity-fields warning
   after source-level verification (repo: BuildFlow; five verify-before-filing gates +
   github-voice). — TODO_LIST High row.
5. Write the ODbL attribution/DATA_LICENSE note for adsb.lol-derived artifacts in
   docs/results (license verified ODbL-1.0, GitHub API 2026-11-14). — fork-housekeeping row.
6. Jet-approach fit mode so approach-corridor recordings can carry a full two-event EU
   verdict. — TODO_LIST row; docs/experiments.md EU section.
7. Offset-scan as a CLI subcommand (scripts/offset_scan.py is the research version). — TODO_LIST row.
8. EU validation phase 2: source a recording with two feed-visible flyovers (approach
   corridor or drop zone), run the pair-level verdict. — TODO_LIST EU row.
9. D2 type annotations sweep. — TODO_LIST chores row.
10. D9 BuildFlow follow-ups bundle (vulture whitelist, split-brain register, doctor
    cadence, pyupgrade, unavailable tools, dprint-excludes upgrade test). — TODO_LIST row.
11. D10 annotate stale claims in the four 2026-11-04 status reports (docs-health
    ANNOTATE, per-item, never per-block). — TODO_LIST row.
12. D11 mlatonly pod probe + usefulness note. — TODO_LIST EU follow-ups row.
13. D11 terrain above 60 N verification. — TODO_LIST EU follow-ups row.
14. Ask adsb.lol the retention question (2020-2022 404; oldest verified 2023-06). — TODO_LIST row added this session.
15. D8 upstream PR template/CONTRIBUTING check before the next filing. — TODO_LIST row.
16. TRACE_PARSE_ERRORS lesson to crush-config (repo: crush-config). — TODO_LIST row.
17. Re-verify `gh search` flags + NO_COLOR habits against current tooling. — TODO_LIST row.
18. CHANGELOG fork-local entry for this session's changes (coverage command, tests,
    docs, EU phase 1). — fork-housekeeping row.
19. Security posture: scheduled gitleaks decision + nosec policy write-up for audio.py. — TODO_LIST security row.
20. Track upstream releases and sync promptly (0.3.0 synced 2026-11-13). — TODO_LIST row.
21. Inventory docs/results artifacts with a regeneration note; add the tests/data
    fixture provenance/attribution note. — FEATURES-row remainder in TODO_LIST.
22. Document how to obtain DOPPLERTRACK_OYSTER_BAY test assets. — fork-housekeeping row.
23. Test-gap remainder: plots-Agg edge paths, pytest-cov adoption decision (deliberate
    non-adopt is acceptable if written down), Hypothesis install decision. — test-gaps row.
24. Runtime-artifact hygiene: decide untracked runtime dirs (.docs-gates-preflight.json,
    .crush/) commit-or-ignore. — hygiene row.
25. Run one full buildflow on the committed state, record the run, and close the loop
    audit for every finding (fixed / filed / documented). — TODO_LIST row.
26. Verify AGENTS.md survives a dprint markdown-format run (or format once, commit). — TODO_LIST row.
27. D12 margin experiment design (verdict-aware) on saved results. — TODO_LIST/planning row.
28. D12 detect→search auto-chain spike. — TODO_LIST row.
29. D12 >2-event search design note. — TODO_LIST row.
30. D12 progress printing before the first 500 pairs (UX). — TODO_LIST row.
31. D12 terrain prefetch batching. — TODO_LIST row.
32. Coverage-per-country aggregation table into docs/coverage.md (registration-prefix
    country counts are collected but not yet tabulated per-country in the doc). —
    docs/coverage.md.
33. EU numbers table in docs/coverage.md: add the Germany 2026-11-12 prop rate
    (collected in the probe, not yet in the doc's table). — docs/coverage.md.
34. Verify the README badge + cache behavior on the first CI run after push. — this report §c item 1.
35. Personal-process items P1-P8 from the plan (batch fork-doc commits into docs-trains,
    `gh pr checks` after filing, re-view after branch switches). — plan micro-plan.

## g) Questions I cannot answer myself

1. **release.yml**: the working tree holds an action-gh-release v3.0.3→v3.0.4 SHA-pinned
   bump whose provenance is unknown (not authored this session). Commit it, revert it,
   or tell me who/what produced it so it can be attributed?
2. **ODbL share-alike**: the adsb.lol archives the pipeline consumes are ODbL-1.0
   (verified via GitHub API). The committed docs/results artifacts derived from them
   (EU CSVs/JSONs, and upstream's US artifacts) — keep them with an attribution +
   share-alike note (my recommendation), or drop derived artifacts from the repo and
   regenerate on demand?
3. **EU verdict target**: is a full two-event EU verdict worth a jet-approach fit mode
   (fork branch first, upstream filing only after it produces a located verdict), or
   should the fork instead validate on a recording with two feed-visible GA props in a
   high-ADS-B-adoption region? Both reach the same gate; the first builds new fitting
   code, the second depends on finding the recording.
