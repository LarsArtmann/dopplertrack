> [!NOTE]
> This PR was drafted by GLM (glm-5.3-flash) via Crush from an AI-run investigation, with multiple rounds of feedback from me.
>
> - [x] MANUALLY REVIEWED by `@Lars Artmann` at `[2026-11-04 05:08 CET]`

TL;DR: the archive scanners behind `fetch-day`/`extract-region` swallow every exception while parsing trace files — including `MemoryError` and real parser bugs — and the CLI writes output files through `open()` without closing them. This PR narrows the catch to the corruption a scraped archive can actually contain, closes all CLI file handles explicitly, and drops two stdlib redundancies. No behavior change on valid data.

## Problem

Three spots ignore failures too broadly or rely on implicit cleanup, all at `a16b700` (current `main` as of 2026-11-04; line numbers cited at that commit):

- `adsb.py:129` (`_scan_one`, the `ProcessPoolExecutor` scan behind `load_region`, `adsb.py:142-145`) and `fetch.py:88` (`iter_tar_traces`, the streaming path behind `fetch-day`) catch a blind `Exception` around `parse_trace_bytes`. That hides `MemoryError` and any future parser bug as a silently skipped trace.
- `cli.py:86` and `cli.py:97` write output through `open(a.out, "w")` without closing; the flush relies on refcount finalization. `cli.py:104`, `cli.py:120`, `cli.py:121`, `cli.py:140` load event JSONs the same way.
- `cli.py:145` does `.replace("Z", "+00:00")` before `datetime.fromisoformat`, and `audio.py:75` wraps `round()` in `int()` — both redundant on this project's `requires-python = ">=3.12"`.

## What changed

- `adsb.TRACE_PARSE_ERRORS` — the exception family a corrupt archive can actually produce (`OSError`, `ValueError`, `IndexError`, `TypeError`, `zlib.error`, `EOFError`); `KeyError` is deliberately absent, since the parser only uses `.get` and numeric indexing and nothing can raise it. Both scan sites catch exactly that list, `fetch.py` via a small `_parse_quiet` helper so the two paths can't drift apart.
- `parse_trace_bytes` treats a non-object JSON document (a list, a string) as missing outright — upstream's blind catch swallowed those silently; the narrowed list alone would have turned them into crashes.
- `cli.load_event` — every event-JSON read goes through one context-managed helper; both output writes use `with`.
- `datetime.fromisoformat` handles a trailing `Z` natively (3.11+), and `round(x)` already returns `int`.

## Verification

- `uv run pytest -q`: 20 passed — the 19 existing tests unchanged, plus one new.
- New `tests/test_fetch.py::test_iter_tar_traces_skips_corrupt_members` streams ten corrupt tar members through the scanner — one input per tuple member (labeled in the test), plus a non-object document: all skipped, none crash, and the 19 existing tests confirm no behavior change on valid data.

Relationship to #2: independent of it, but both touch `fetch.py` and `cli.py` (different functions). Happy to rebase on top once #2 lands.

💘 Generated with Crush
