# Roadmap

Long-term direction and raw ideas not yet refined into actionable tasks.
Bounded, short-term work lives in TODO_LIST.md.

## Ideas

- Offer upstream an `AGENTS.md`-lite only if the maintainer signals interest —
  not cold (docs/status/2026-11-04_05-12_upstream-pr3-filed-and-verified.md §26).
- If stacked PRs become a real possibility, set up the jj colocate flow before
  the second PR; this repo is a git-only checkout today
  (docs/status/2026-11-04_05-12_upstream-pr3-filed-and-verified.md §38).
- European end-to-end validation beyond the first recording: geolocate a
  recording from several EU countries to exercise feed-density differences
  (AGENTS.md "EU readiness", verified 2026-11-13).
- Attack the thin score margins with the verdict machinery in mind (verdict.py
  now quantifies them; the brightness-only weakness remains).
- Generalize search beyond exactly two events (`refine --extra` exists; the
  search itself is 2-event).
- Auto-chain detect → search so the operator no longer picks events by hand
  from the table.
- Print search progress before the first 500 pairs (currently silent until
  then).
- Batch terrain prefetch for the whole grid up front instead of per-call tile
  sets.
- Reproducibility rerun: check the docs/results artifacts are still
  reproducible post-refactor (heavy; defer until asked).
