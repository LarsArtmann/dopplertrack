# Status Report — First Commit + Upstream Assessment Session

**Date:** 2026-11-04 04:36 CET
**Repo:** `github.com/LarsArtmann/dopplertrack` (fork of `mjshiggins/dopplertrack`), branch `main`
**Session span:** ~04:10–04:36 CET (continues the 02:37–04:00 quality-gate session;
see `docs/status/2026-11-04_04-10_buildflow-red-to-green-quality-gate-fix.md` for the
prior segment — that report's sections a–e are not repeated here)
**Trigger:** user requests: "git commit", then "Is any of the changes we made worth
upstreaming?"

---

## Scope of this report

**VERIFIED (fresh command output this segment):**

| Claim                                                                      | Verified via                                                                                 |
| -------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Commit `19c6112` exists, tree clean                                        | `git status --short` (empty), `git log --oneline`                                            |
| Commit shape: 31 files, +2098/−454, 6 new files                            | `git commit` output                                                                          |
| Fork is 3 ahead / 0 behind upstream                                        | `git fetch upstream` + `git rev-list --left-right --count HEAD...upstream/main` → `3  0`     |
| Upstream last push 2026-11-03 22:08 UTC                                    | `gh api repos/mjshiggins/dopplertrack --jq .pushed_at`                                       |
| All five fixed patterns exist verbatim upstream today                      | `git grep <pattern> upstream/main -- src/dopplertrack` (exact `file:line` for each; see a)2) |
| Upstream Python floor is `>=3.12`                                          | `git show upstream/main:pyproject.toml`                                                      |
| Upstream has no lint/tooling config                                        | `gh api .../contents/` → no ruff/dprint/AGENTS/SECURITY/dependabot files                     |
| No duplicate lint/cleanup issues upstream (Gate 5)                         | `gh search issues/prs --repo mjshiggins/dopplertrack` open + closed → empty                  |
| Upstream PR #2 exists, open, and touches `cli.py`, `fetch.py`, `tracks.py` | `gh pr view 2 --json files`                                                                  |
| `grid_lla`/`top_pairs` unreferenced in upstream docs/README                | `git grep` on upstream tree                                                                  |

**NOT verified (and why):**

- **Upstream PR #2's actual diff content** (only its file list was fetched) — overlap
  with our fixes is confirmed at file level, hunk-level conflict risk remains unquantified.
- **Whether the upstream maintainer privately uses `grid_lla`/`top_pairs`/notebooks**
  — `pipeline.py`'s docstring references notebooks that exist outside the repo; this is
  unknowable from here and is the reason dead-code removals are not upstream candidates.
- **GitHub search-index completeness** for Gate 5 (searches were keyword-based; a
  deliberately-closed discussion could evade keyword matching).
- **What the pre-existing working-tree WIP (landed inside `19c6112`) actually was** —
  still unreviewed as a unit; the user was asked about provenance and answered
  "git commit", which I read as commit-as-is consent (see d)2 and g)1).
- **Whether the auto-commit daemon is content** with a manually-made commit (no
  evidence of interference; daemon behavior not re-checked after the commit).

---

## a) FULLY DONE

1. **All session work committed.** `19c6112` "Make the BuildFlow quality gate pass:
   ruff fixes, dprint excludes" — 31 files, +2098/−454. Includes: the 23 ruff fixes,
   dprint.json excludes, dead-code removals, BuildFlow-generated files (dprint.json,
   `.github/dependabot.yml`, SECURITY.md), both status reports, and the pre-existing
   working-tree WIP. Working tree clean after; attribution format followed
   (`💘 Generated with Crush` / `Assisted-by:` per harness contract).
2. **Upstream assessment completed with all five verify-before-filing gates run,**
   each with fresh upstream evidence:
   - Gate 1/4 (effect + root cause): all five portable fixes correct on their own
     terms (narrowed exception tuple, context-managed CLI writes, native-`Z`
     `fromisoformat`, `round()` simplification).
   - Gate 2 (not already fixed upstream): every pattern still present verbatim on
     `upstream/main` — adsb.py:129, fetch.py:88, cli.py:86, cli.py:145,
     audio.py:75.
   - Gate 3 (platform relevance): upstream `requires-python = ">=3.12"` verified —
     native-`Z` `fromisoformat` (3.11+) and `from datetime import UTC` are valid there.
   - Gate 5 (no duplicates): zero lint/cleanup issues or PRs upstream, open or closed.
3. **Upstream divergence mapped.** Fork is 3 ahead / 0 behind `upstream/main` — the
   "pre-existing modifications" were **not** an upstream sync (hypothesis tested and
   falsified); they are fork-local work, now committed inside `19c6112`.
4. **Verdict delivered with rationale** (no PR filed — needs your go-ahead):
   - **Worth upstreaming:** ONE small correctness-framed PR (context-managed output
     writes; narrowed exception tuple; native-`Z` parsing; `round()` simplification).
     Pitch must be correctness, not lint — upstream has no lint infra (verified).
   - **Not worth upstreaming:** dead-code removals (`grid_lla`/`top_pairs`/`trace_idx`
     — maintainer's private-notebook risk, unverifiable), all fleet tooling,
     style-only renames.
   - **Different upstream entirely:** the BuildFlow bandit findings-parser artifact
     (~222 of 224 parsed "findings" are bandit's own INFO log lines) belongs in the
     BuildFlow repo, not dopplertrack.
5. **New conflict-risk evidence surfaced:** upstream PR #2 ("Reproduce the Oyster
   Bay result from raw audio again, fixes #1", opened 2026-11-04 01:59 UTC) touches
   `src/dopplertrack/cli.py`, `src/dopplertrack/fetch.py`, `src/dopplertrack/tracks.py`
   — the same files as two of our portable fixes. Any upstream branch must account
   for it (base on `upstream/main`, expect cli.py/fetch.py overlap).

## b) PARTIALLY DONE

1. **Upstream PR preparation** — the verdict and the gate evidence exist; the clean
   branch does not. `19c6112` entangles the portable fixes with fork-local WIP at
   hunk level in shared files, so branch prep requires surgical cherry-picking
   (this is the `jj-fork-pr-workflow` loop). Not started.
2. **Provenance resolution** — flagged in the 04:10 report as the top question;
   resolved in practice only by your one-word instruction ("git commit"). The WIP
   inside `19c6112` is committed but still unreviewed as a unit; nothing identifies
   which hunks were yours vs. mine in the shared files.
3. **HARVEST of the 04:10 report's section (f)** — still pending; the repo still has
   no `TODO_LIST.md`/`FEATURES.md`/`ROADMAP.md`, so 50 brainstormed items now exist
   across two timestamped reports and zero living docs.
4. **BuildFlow bandit findings-parser issue** — diagnosis sampled and real (2 of 224
   entries are actual findings); a source-level verify pass in the BuildFlow repo +
   filing has not happened.

## c) NOT STARTED

1. Pushing `main` to origin (nothing pushed this session; commit is local-only).
2. The upstream fix PR (branch, cherry-pick, `github-voice` draft, filing).
3. The BuildFlow bandit-parser issue in the BuildFlow repo.
4. Re-running a full `buildflow --build-mode full` on the **committed** state (the
   green verification ran on the working tree pre-commit; nothing changed since, but
   the post-commit state itself was never re-verified).
5. All unstarted items carried from the 04:10 report's section (c) — unchanged:
   TODO_LIST/FEATURES/ROADMAP build-out, on-demand scans (gitleaks/codespell/
   markdown-lint), `.buildflow.yml` skips policy, pre-commit hook decision,
   flake.nix decision, fixture rename to `.json.gz`, pytest-cov.

## d) TOTALLY FUCKED UP

Final state: nothing broken — tree clean, commit landed, upstream evidence fresh.
Honesty about this segment's stumbles:

1. **`gh search --state all` is invalid** — wasted two calls on a flag I didn't check
   (`--state` takes open/closed only). Trivial, but it's exactly the verify-your-tools
   class of error the session keeps reproducing.
2. **Committed mixed-provenance work as one commit.** The 04:10 report's own
   improvement list said "split pre-existing modifications from session fixes so
   history reads honestly" — and then I did the opposite when you said "git commit".
   Defensible (you were asked and answered; the daemon's staging had already lumped
   everything), but it contradicts my own recorded lesson. A file-group split
   (tooling / reports / code) was available and not taken.
3. **PR #2's file overlap was flagged as a "risk to check later" in the verdict
   message before I had checked it** — the check (`gh pr view 2 --json files`) took
   one call and confirmed real overlap in `cli.py`/`fetch.py`. Should have been part
   of the verdict, not an afterthought caught by the report pass.

## e) WHAT WE SHOULD IMPROVE

1. **Practice what the report preaches.** The 04:10 improvement "split by provenance
   before committing" was written down an hour before being violated. Either treat
   such lessons as blocking rules or stop writing them as if they bind.
2. **Complete the last verification before publishing a verdict.** The verdict
   message should never contain "rebase risk; diff it before branching" about a PR
   whose file list costs one API call.
3. **`gh` flag validation memory.** Record valid `gh search` flag values to stop
   rediscovering them; same for `NO_COLOR` for buildflow output (carried lesson).
4. **Carry-forward discipline for report sections.** This segment's (f) list should
   explicitly supersede the 04:10 list, not grow a third parallel inventory — until
   HARVEST runs, every new report risks three diverging backlog copies (split brain
   in documentation form).
5. **Answer-first report ordering for question-driven turns.** This turn was "is it
   worth upstreaming?" — the evidence gathering was right, but the verdict should
   have been deliverable in the same turn without a user nudge; it was (just), only
   because the report request interrupted. Fast gate runs → fast verdicts.

## f) Up to 50 things we should get done next

_Supersedes the 04:10 list (which remains valid where not repeated here). Ordering:
session fallout → upstream → BuildFlow upstream → repo hygiene → deferred._

**Upstream PR track (the actionable output of this segment):**

1. Decide go/no-go on the upstream correctness PR (question g)2).
2. If go: create a clean branch from `upstream/main`; cherry-pick only the four
   portable hunks (cli.py writes + fromisoformat, adsb.py/fetch.py exception tuple,
   audio.py round) — never the fork tooling or WIP.
3. Diff our hunks against upstream PR #2's cli.py/fetch.py changes; if conflict,
   decide: rebase onto PR #2, wait for it to land, or file anyway with a note.
4. Draft with `github-voice` after the verify gates (already passed this session);
   pin `file:line` citations to the exact upstream/main commit hash at filing time.
5. Include a tiny before/after snippet showing `open(...).write(...)` GC-flush
   reliance — the correctness evidence, not a linter complaint.
6. Decide whether `fromisoformat`-drop-`.replace` is in the same PR or a separate
   modernization PR (maintainer taste varies; one small PR is my default).
7. After filing: track PR in the fork's jj/git loop (`jj-fork-pr-workflow` sync
   cycle) so it stays rebaseable while PR #2 moves.
8. Optionally pair the PR with a comment on issue #1 (the repro issue) only if the
   maintainer's workflow visibly hits the same patterns — don't wedge the PR into
   someone else's thread otherwise.

**BuildFlow upstream track:**
9. Verify the bandit findings-parser artifact at BuildFlow source level (how are
bandit's stdout lines split into findings?).
10. If confirmed: file in the BuildFlow repo (verify-before-filing passed upstream —
this one needs its own gates run first).
11. Also check whether BuildFlow truncates `-format finding` output identity fields
(the earlier run warned "patched findings missing identity fields ... missing_file=176")
— same repo, possibly same parser area.
12. Decide whether to file the "dprint excludes durability" question (does
auto-configure preserve user excludes on refresh?) as an issue or test it
empirically on the next upgrade instead.

**Local repo track:**
13. Push `main` to origin (or confirm the daemon does it).
14. Re-run `buildflow --build-mode full` once on the committed state; record the run ID.
15. HARVEST both status reports' (f) lists into a fresh `TODO_LIST.md` (docs-health
BUILD mode), so item 16+ stop being report-resident.
16. Then maintain that TODO_LIST.md as the single backlog (this section shrinks to
deltas in future reports).
17. Commit-or-delete decision for `.crush/` and other untracked runtime dirs if any
appear in `git status` after daemon activity.
18. From the 04:10 list, still open and unchanged: vestigial `hello()` removal;
`soundfile` dependency removal; `pipeline.py` notebook-docstring fix; fixture
rename to `.json.gz`; `.gitignore` cache-dir check; link-scan exclusions check;
pytest-cov; on-demand scans; `.buildflow.yml` policy; pre-commit hook decision;
flake.nix decision; docs/results regeneration note; ruff-in-CI decision.
19. `--strict` gate experiment (still valuable, still unrun).
20. mypy minimal config decision (still unrun).

**Fork strategy track:**
21. Decide the fork's long-term role: upstream consumer + validation fork, or
diverging product (determines how aggressively fork-only WIP gets committed).
22. If diverging: start a CHANGELOG.md and tag 0.2.1 from this state.
23. If consuming: schedule a periodic `git fetch upstream` + rebase drift check
(upstream moves fast — pushed the day before this session).
24. Re-check upstream PR #2 / issue #1 weekly until landed; they define where
cli.py/fetch.py/tracks.py will move next.

**Documentation track:**
25. Record the upstream-assessment verdict in AGENTS.md (fork-specific policy:
what gets upstreamed, what doesn't — so the next session doesn't re-derive it).
26. Record `gh search --state` valid values + `NO_COLOR=1` for buildflow in
AGENTS.md Commands/Conventions.
27. Note the verified upstream facts (floor >=3.12, no lint infra, PR #2 files) in
AGENTS.md's related-projects paragraph — they age; date-stamp them.

**Deferred/roadmap-grade (carry-overs, compressed):**
28. Security posture: scheduled gitleaks for a recordings-handling repo.
29. Property tests for the pair-join bucket edges (beyond the brute-force test).
30. Coverage weighting for `score.py`/`search.py` edge paths.
31. Upstream the `TRACE_PARSE_ERRORS` pattern as a crush-config lesson if it
generalizes (commit there, not in-session).
32. Vulture whitelist mechanism decision (machine-readable acceptances).
33. bandit `# nosec` policy decision (still open from g)2 of the 04:10 report).
34. Split-brain register: BuildFlow fleet defaults vs per-repo `.buildflow.yml`.
35. Release flow dry-run from this fork (tag-driven, untested here).
36. pyproject Homepage/Issues URLs still point at upstream — fork-presence decision.
37. Upstream-PR template/CONTRIBUTING check (upstream has none — matches its PoC
nature; keep PRs small).
38. Consider whether `tests/data` fixture provenance (adsb.lol real trace) needs a
license/attribution note upstream and in the fork.
39. `docs/results/` artifacts: are both recordings' artifacts still reproducible
post-refactor (README validation rerun — heavy, defer until asked)?
40. Time-box budgets: full mode is ~1 min; default budgets could drop to 5 m.
41. Interrogate (docstring coverage) not in nixpkgs — decide if the check matters
or drops out of the expected-tool set.
42. Periodic `buildflow doctor` binary-freshness check cadence.
43. Keep `uv.lock` in sync policy (uv lock/sync only) — already followed; document.
44. Decide if `AGENTS.md` "related projects" research (DOPPLERGEIST, doppler-experiments,
pyfr24, traffic) should become a small `docs/related.md` instead of prose.
45. Sweep both status reports' stale claims after HARVEST lands (annotate, don't rewrite).
46. Add the jj-fork sync loop to AGENTS.md if this fork keeps contributing upstream.
47. `soundfile` removal should come with a `uv lock` run, not a hand-edit (already policy).
48. Consider `python -m pytest` vs `uv run pytest` in CI pinning (uv version drift).
49. Determine whether the fork wants GitHub branch protection on main (solo fork —
probably not; record the refusal).
50. End-of-session loop audit: every finding this session ended fixed / filed /
documented — re-audit once HARVEST lands so nothing lives only in reports.

## g) Questions I cannot figure out myself

1. **Was commit-as-is the intent, and does the WIP stand?** `19c6112` contains
   fork-local work I never authored or reviewed as a unit (all `src/`/`tests/`
   files were modified before either of my sessions). Tests pass and the gate is
   green on the combined tree — but if that WIP contains unfinished experiments,
   they're now permanent history on `main`. Should it have been split/scrubbed
   before the commit (amend still possible until push)?
2. **Do you want the upstream PR filed — and via which workflow?** If yes: I would
   create a clean branch from `upstream/main` with only the four portable hunks
   (git cherry-pick or the jj workflow — your fork loop is documented for jj).
   Also: file now (conflict risk with the actively-moving PR #2) or after #2 lands?
3. **Should the bandit findings-parser artifact go upstream in BuildFlow this
   week?** It's your own repo, so this is a prioritization question, not a
   permission question: is a BuildFlow issue with a reproduction worth a slot in
   your next BuildFlow session, or do you already know this parser behavior and
   accept it?

---

_Report written per status-report skill (`.md` default, DECIDED 2026-10-27 D.g4).
Section (f) supersedes the 04:10 list and is HARVEST-ready. Not committed —
Crush harness forbids commits without explicit request; the auto-commit daemon
picks the file up. WAITING FOR INSTRUCTIONS._

---

## Addendum (2026-11-04 05:12 CET) — upstream track executed

Section (f) items 1–8 done in the same session, on explicit go:

- **Issue #1 crash reproduced empirically** in our tree: stubbed two-part asset
  day → `'<' not supported between instances of 'dict' and 'dict'` (execution
  evidence, upgrading the earlier grep-only claim).
- **PR #3 filed**: https://github.com/mjshiggins/dopplertrack/pull/3 — branch
  `upstream-pr` (3 commits off `a16b700`, +42/−14, 5 files), 20/20 tests
  (19 upstream + 1 new corrupt-tar regression test), body passed the
  github-voice checker (0 FAIL / 0 WARN), verified OPEN via `gh pr view 3`.
- **No comments posted** on #1/#2: the conditional bar set last turn (run the
  repro before claiming it) was only partially met — crash verified, full
  Oyster Bay flow not run — so the replication comment stays unearned.
- **Inherited-bug status unchanged**: the fetch-day split-archive crash and the
  contrast-objective fit default are still in our `main` (both owned by PR #2);
  cherry-pick them after it merges.
- Commit-shape note: section (d)2's mixed-provenance commit stands (`19c6112`).
  Question g)1 was implicitly answered by the commit order; the amend window
  closed when `main` reached `origin` between turns.
