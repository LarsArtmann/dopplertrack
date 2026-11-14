# ADS-B day-archive coverage

`dopplertrack coverage DATE BBOX` streams one day archive and reports what a search
would actually have to work with there: traces seen, parse failures, how many touch the
box, the propeller share (`adsb.AircraftTypes`, unknown designators counted separately),
registration-prefix countries, and the top type designators. Run it for a candidate date
and region before spending search time there. The machine-readable form is `--json`.

Method: the archive is streamed from the adsb.lol GitHub release (nothing large is
stored); a trace counts as touching the box when any of its points is inside. Prop
classification is by ICAO Doc 8643 engine type (Piston/Turboprop/Electric); a designator
missing from Doc 8643 counts as "unknown designator" and defaults to prop.

## Measured days

| date | box | traces seen | parse failed | touching box | prop share | note |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-11-12 | Germany 47.2-55.2, 5.5-15.5 | 28,879 | 21 | 2,034 | see below | the original EU readiness probe (2026-11-13 session) |
| 2024-05-25 | Malton UK 53.8-54.5, -1.4-0.3 | 56,300 | 62 | 261 | 115 (44%) | the whitethroat recording's day; P28A 19, DR40 6, C150 5, R44 6 |
| 2026-07-11 | Dunstable UK 51.6-52.1, -0.95--0.15 | 76,344 | 101 | 1,362 | 270 (20%) | the Whipsnade recordings' day; Luton corridor: B738 171, A320-family 246, P28A 39 |

The 2026-11-12 Germany probe found EU GA props with registration and type populated
(C172, P28A, DR40, FK9, C42, DA42 among them), and terrain/ENU verified at 48.35 N.

## What the numbers mean for a search

- The share of box traces that are props is the share of traffic the default search
  targets; `fetch --keep-jets` widens it to everything with ADS-B.
- Airliners are always in the feed and - as the EU validation session found - their low
  shaft harmonics sweep audibly in the 60-300 Hz band, which makes approach corridors
  the one EU environment with guaranteed-visible flyovers.
- Light aircraft and gliding-club traffic in Europe are frequently Mode-S-only or
  FLARM-only: recordings near small airfields hear more aircraft than the day index
  contains (see docs/experiments.md, EU section).
- Archive availability was verified back to 2023-06; 2020-2022 day releases do not
  exist (checked 2026-11-14 via the release API).
