# Status Report — Upstream PR #3 Filed, Verified, Policy Recorded

**Date:** 2026-11-04 05:12 CET
**Repo:** `github.com/LarsArtmann/dopplertrack` (fork of `mjshiggins/dopplertrack`), branch `main`
**Session span:** ~04:40–05:12 CET (third segment; prior reports:
`04-10` quality-gate fix, `04-36` first commit + upstream assessment)
**Trigger:** your directive: "Do all you think we should to add real value to the
upstream repo! … The WHOLE TODO LIST!" — scoped in practice to the upstream track
(section f items 1–8 of the 04:36 report).

---

## Scope of this report

**VERIFIED (fresh command output this segment):**

| Claim                                                                               | Verified via                                                                                       |
| ----------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| **PR #3 is OPEN** at upstream, base `main`, head `LarsArtmann:upstream-pr`, 5 files | `gh pr view 3 --json …` + `gh pr list`                                                             |
| 20/20 tests on the branch (19 upstream + 1 new)                                     | `uv run pytest -q` on `upstream-pr` (61.98 s)                                                      |
| Issue #1 crash reproduces by execution, not just grep                               | stubbed two-part asset day → `TypeError: '<' not supported between instances of 'dict' and 'dict'` |
| PR body passed the voice checker                                                    | `check-draft.go --kind body-issue --ai-drafted --unsolicited` → 0 FAIL, 0 WARN                     |
| Branch is exactly 3 commits off `a16b700`, +42/−14                                  | `git log upstream/main..HEAD`, `git diff --stat`                                                   |
| Fork `main` still green after everything                                            | `buildflow --build-mode fast` exit 0; `dprint check` exit 0; local pytest pass                     |
| Session docs committed                                                              | `2c69762` (AGENTS.md policy, report addendum, PR draft)                                            |

**NOT verified (and why):**

- **Upstream CI on PR #3**: `gh pr checks 3` → "no checks reported" ~4 min after
  filing, even though upstream's `ci.yml` declares a bare `pull_request:` trigger.
  Cause unknown from here (Actions possibly disabled on the repo, or still starting).
  Local equivalent (pytest on 3.12) was verified; remote is not.
- **PR #2 movement since 01:59 UTC** (SokolskyNikita may have pushed; I read its diff
  once and did not re-poll before filing).
- **Whether the maintainer accepts AI-banner PRs** — unknowable; the banner is there
  and honest, the reception is not.
- **The daemon's reaction** to the branch switch / new commits (no interference
  observed; nothing re-checked after the fact).

---

## a) FULLY DONE

1. **PR #3 filed and verified**: https://github.com/mjshiggins/dopplertrack/pull/3
   "Robustness micro-fixes (no behavior change)" — 3 commits off `a16b700`:
   1. `cli: close output files explicitly, load event fits via a helper`
   2. `adsb,fetch: skip only expected parse errors when scanning trace files` (+ the
      regression test, squashed in via fixup)
   3. `audio,cli: drop redundant int(round(...)); parse UTC without .replace`
2. **Issue #1 crash reproduced empirically** in our tree (execution evidence via
   stubbed `requests.get` returning two assets) — the earlier grep-only claim is
   upgraded to a run.
3. **Regression test added at the right contract**: corrupt tar members stream
   through `iter_tar_traces` without crashing (5 corruption classes). 20/20 pass.
4. **All five verify-before-filing gates re-run against fresh upstream state**;
   every `file:line` claim in the PR body pinned to `a16b700` (verified fresh:
   `adsb.py:129`, `fetch.py:88`, `cli.py:86/97/104/120/121/140/145`, `audio.py:75`,
   `load_region`→`ProcessPoolExecutor` at `adsb.py:142-145`).
5. **github-voice protocol followed end-to-end**: draft kept in `docs/drafts/`
   (not /tmp), provenance banner + TL;DR + evidence headers + Crush footer,
   mechanical checker 0 FAIL / 0 WARN, filed via `--body-file` (not piped), landing
   verified with `gh pr view`.
6. **jj-fork-pr-workflow pre-flight honored**: git-only checkout detected (no `.jj`,
   no conversion without asking), gh auth + identity checked, upstream commit style
   matched (lowercase prefix), push went to the fork only, PR filed as an
   **independent sibling** of PR #2 (correct per the skill: logically independent,
   textual overlap only) with an explicit rebase offer in the body.
7. **Fork policy recorded** in AGENTS.md: what goes upstream (correctness-framed
   fixes), what stays fork-only (fleet tooling; removals of helpers the maintainer
   may use privately), the filing gates, and the rebase trigger (PR #2 merge).
8. **04:36 report annotated** (addendum section, non-destructive) and everything
   committed: `2c69762`.

## b) PARTIALLY DONE

1. **"WHOLE TODO LIST" scope** — the mandate sentence named the upstream repo, so I
   executed upstream-track items 1–8 fully, but items 9–11 (BuildFlow bandit-parser
   issue — that's _your_ repo, not upstream) were **not** started. Flagging the
   scoping decision explicitly rather than silently dropping it.
2. **The inherited-bug fix in fork `main`** — the split-archive `TypeError` and the
   contrast-objective fit default both still live in our tree (deliberately: they are
   PR #2's content; taking them would be hostile to the first-time contributor).
   Cherry-pick is queued behind PR #2's merge.
3. **Issue #1 replication comment** — correctly _not_ posted (the bar set last turn
   — run the repro before claiming it — was only partially met: crash verified, full
   Oyster Bay flow not run). Stays unearned.
4. **PR #3 lifecycle** — filed and verified OPEN, but review responses, CI status and
   the post-#2 rebase are all future work.

## c) NOT STARTED

1. Watching/handling PR #3 review; rebase after PR #2 merges.
2. BuildFlow bandit findings-parser issue in the BuildFlow repo (own-repo upstream).
3. `TODO_LIST.md` HARVEST — now **three** report-resident backlogs (04:10, 04:36
   addendum, this report) and still no living TODO file. Each new report deepens the
   split brain this keeps documenting.
4. Cherry-picking PR #2's two fixes into fork `main` (blocked on #2 merging).
5. Everything carried from prior reports and untouched (mypy decision, `--strict`
   experiment, on-demand scans, TODO/FEATURES/ROADMAP build-out, `soundfile`
   removal, `hello()` removal, fixture rename, pre-commit/flake decisions).

## d) TOTALLY FUCKED UP

Final state: nothing broken — PR is up, branch green, main green, docs committed.
The segment's real mistakes, all caught before they reached upstream:

1. **I wrote the regression test against the wrong contract.** First version called
   `parse_trace_bytes` directly and asserted it returns `None` on corrupt bytes —
   but that function _raises_ by design; the None-on-corrupt contract lives in the
   callers (`_scan_one`, `_parse_quiet`, `iter_tar_traces`). The test suite caught it
   (1 failed, 19 passed), and I fixed it properly (test moved to `test_fetch.py`
   against the public streaming API, then `--fixup` + `--autosquash` rebase so the
   filed history shows no embarrassment). Root cause: I designed the test before
   re-reading the caller contract. Cost: one failed test cycle + history surgery.
2. **Two edit-rejections from stale reads.** `git switch` churned AGENTS.md's mtime
   (it doesn't exist on the upstream-based branch) and dprint had reformatted the
   04:36 report after my write; both edits bounced until re-read. Predictable —
   re-reading after branch switches should be automatic.
3. **Framing slip in the mandate**: "WHOLE TODO LIST" was ambiguous between "the
   upstream track" and "all ~50 items across three reports". I chose the former
   (scoped by your own sentence), and flag it here — if you meant all 50, say so
   and the fork-chore backlog runs next.

## e) WHAT WE SHOULD IMPROVE

1. **Contract-first tests**: before writing a test, name the function that OWNS the
   behavior (here: `iter_tar_traces`, not `parse_trace_bytes`). The mistake was
   caught by execution, which is the system working — but the system shouldn't have
   had to catch it.
2. **Poll fast-moving PRs at filing time.** PR #2 was opened 3.5 h before our PR;
   I diffed it once and never re-checked. One `gh pr view 2` before `git push` would
   have caught any new pushes.
3. **Check CI wiring of the target repo before filing** (upstream declares
   `pull_request:` yet no checks appeared — knowing whether Actions is even enabled
   sets expectations for "is it merged yet" monitoring).
4. **State scope interpretation explicitly at the START of a mandate turn**, not in
   the post-hoc report — one line ("scoped to the upstream track; fork chores
   excluded") would have made the choice reviewable mid-run.
5. **Auto-commit-daemon unpredictability around branch switches** — untracked docs
   survived fine, but mtime churn broke edit assumptions. Future: write branch-sensitive
   docs only from the branch they belong to, or after switching back.

## f) Up to 50 things we should get done next

_Supersedes prior lists where overlapping; upstream track first._

**PR #3 lifecycle:**

1. Monitor PR #3 for maintainer response; respond per github-voice terse register.
2. Diagnose why no CI checks appeared (Actions disabled upstream? ask if relevant).
3. When PR #2 merges: fetch, rebase `upstream-pr` onto `upstream/main`, push
   (--force-with-lease), confirm clean conflict resolution in `cli.py`/`fetch.py`.
4. After PR #3 merges: sync fork main from upstream, then delete `upstream-pr`.
5. If the maintainer requests changes: separate the four fixes into stacked PRs
   only if he asks — otherwise iterate in-place.
6. Re-poll PR #2's branch before any of the above (it may have moved since 01:59).

**Fork bug debt (inherited from #1, owned by PR #2):**
7. After #2 merges, cherry-pick its fetch-day sort fix + fit `objective` param into
fork `main` (with `uv run pytest -q` + a buildflow fast gate).
8. Independently: decide whether fork `main` should carry a temporary patch for the
split-archive crash NOW (your tree crashes on real multi-part days; PR #2 is
hours-to-days away) — needs your call, see g)3.

**BuildFlow upstream (own repo, items 9–11 of the 04:36 list):**
9. Investigate the bandit findings-parser artifact at BuildFlow source level.
10. Investigate the "patched findings missing identity fields … missing_file=176"
warning seen in the 02:39 run (same repo, possibly same parser).
11. File either/both with verified reproductions.

**Backlog hygiene:**
12. Run docs-health HARVEST across all three status reports → one `TODO_LIST.md`
(this is the highest-leverage chore; three parallel backlogs is a documented
split brain).
13. Sweep stale claims in both prior reports post-HARVEST (ANNOTATE mode).

**Fork chores (carried, still open, unchanged):**
14–24. From the 04:36 list verbatim: dependabot/SECURITY keep-or-kill (g)3 of that
report still unanswered); `soundfile` removal; `hello()` removal; notebook-docstring
fix; fixture rename to `.json.gz`; `.buildflow.yml` skips policy; pre-commit hook
decision; flake.nix decision; pytest-cov; on-demand scans (gitleaks/codespell/
markdown-lint); ruff-in-CI decision.

**Upstream hygiene (new, noticed this segment):**
25. Decide whether to offer upstream the corrupt-member regression test as a
standalone hardening PR if #3 stalls (it's independent of the other fixes).
26. Offer upstream an `AGENTS.md`-lite only if the maintainer signals interest —
not cold.
27. If PR #2 stalls > a week and the crash bites you: a polite issue #1 comment with
your verified repro snippet becomes earnable (bar from last turn).
28. Track upstream releases (tag-driven, PyPI) so fork syncs land promptly.
29. Check upstream's Actions-enabled state once (explains item 2 and sets monitor
expectations).
30. Keep `docs/drafts/` convention for future filings (worked well; corpus of
past drafts is revision history).

**Process:**
31. Add "read the caller contract before writing a test" to the personal test
checklist (the segment's one real mistake).
32. Re-verify `gh search` flag values + `NO_COLOR` habits still in AGENTS.md notes
(carried lesson, not yet written down — it is now in this report; move to
AGENTS.md next docs commit).
33. For any in-place branch switch, immediately re-`view` files you plan to edit.
34. Keep scoping statements at mandate-time, not report-time (e)4.
35. Consider pinning the upstream base commit in AGENTS.md whenever the fork
syncs, so "0 behind" claims stay auditable.
36. `gh pr checks` right after filing — don't assume CI will run.
37. Batch fork-doc commits (three docs commits today; a docs-train would do).
38. When stacking is a real possibility, set up the jj colocate flow _before_ the
second PR (skill's own advice — this repo is still git-only by choice).
39. Time-box future "WHOLE LIST" mandates with an explicit item range up front.
40. Archive the PR body draft after merge (docs/drafts/ hygiene).

**Deferred/roadmap-grade:**
41–50. Carried from 04:36 items 25–50 without change (fork strategy, security
posture, coverage/property tests, upstream lessons to crush-config, release
dry-run, pyproject URL fork-presence, AGENTS related-projects extraction, ffmpeg
nosec policy, vulture whitelist, mypy policy). None invalidated by this segment.

## g) Questions I cannot figure out yourself

1. **Should the fork carry a hotfix for the split-archive crash now?** Your `main`
   crashes on real multi-part days (verified). PR #2 fixes it but is unmerged. I can
   cherry-pick just that one hunk into fork `main` immediately (clean, no conflict
   with #2's authorship since we'd credit it) — or keep fork `main` purely
   upstream-tracking and live with the crash. Which policy?
2. **Do you want me to actively monitor PR #2/#3 and auto-rebase** (the jj sync loop
   equivalent, run when upstream moves), or do you prefer to trigger those manually?
   Auto-mode means pushes to your fork remote happen without a per-push ask.
3. **Is the BuildFlow bandit-parser issue worth a session this week?** It's your own
   repo, so this is prioritization: the artifact (≈222 of 224 "findings" are
   bandit's own INFO lines) inflates every Python repo's build summary fleet-wide.
   High annoyance value, low difficulty — but it needs a BuildFlow source
   investigation I haven't started.

---

_Report written per status-report skill (`.md` default, DECIDED 2026-10-27 D.g4).
Not committed — harness contract; daemon or your next "git commit" picks it up.
WAITING FOR INSTRUCTIONS._
