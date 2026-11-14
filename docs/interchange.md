# Interchange formats

Every stage writes a file the next stage (or a notebook) reads. This page
specifies them so tools outside the CLI can interoperate. All times on the
recording are seconds from the start of the audio; all flight times are unix
seconds, UTC. Loading code lives next to the writer (`Spectrogram.load`,
`DayIndex.load`, `adsb.load_traces`, `cli.load_event`).

## EventFit `.json` (written by `fit`, `detect --out`; read by `search`, `refine`)

A single JSON object - not a list - of exactly these fields:

| field        | unit  | meaning                                                                          |
| ------------ | ----- | -------------------------------------------------------------------------------- |
| `t_cpa`      | s     | heard CPA time in the recording (observation time of the f0 crossing)             |
| `t_cpa_emit` | s     | emission-time CPA: `t_cpa - d / c` with `c = speed_of_sound()`                    |
| `f0`         | Hz    | rest fundamental frequency of the propeller tone                                  |
| `v`          | m/s   | speed at CPA                                                                      |
| `d`          | m     | CPA slant distance (microphone to aircraft)                                       |
| `t_start`    | s     | window start the fit used                                                         |
| `t_end`      | s     | window end the fit used                                                           |
| `score`      | dB    | mean whitened level along the fitted curve                                        |
| `f_pre`      | Hz    | frequency before the approach, at the window edge                                 |
| `f_post`     | Hz    | frequency after the departure, at the window edge                                 |
| `burst`      | 0-1   | share of the 3 min around `t_cpa` that is a broadband burst (train, truck)        |

`detect --out` writes a JSON *list* of these objects (ranked); `search` and
`refine` take single objects. Unknown or missing fields fail loudly and the CLI
says which file and why (see `load_event`).

## Spectrogram `.npz` (written by `spectrogram`; read by `detect`, `fit`, `search`, `refine`)

| key | array      | meaning                                                     |
| --- | ---------- | ----------------------------------------------------------- |
| `t` | (T,) f64   | centre time of each frame, s from recording start           |
| `f` | (F,) f64   | bin centre frequencies, Hz (defaults 40-450 Hz)             |
| `S` | (F, T) f32 | whitened power: dB above each bin's own median across time  |

Defaults: 4 kHz decode rate, 0.25 s hop. Whitening is per frequency bin, so a
bin that is loud all day does not drown the 6 dB sweep of a flyover.

## Day index `.npz` (written by `fetch`; read by `search`, `refine`)

One day of ADS-B flights, resampled to 1 Hz emission times, in ENU metres
about `(lat0, lon0)`. Keys: `lat0`, `lon0`, `bucket_s` (f64), `off` (S+1,)
segment offsets into `t`/`enu`/`spd`, `t` (T,) unix s, `enu` (T, 3), `spd`
(T,) m/s, `icao` (S,) str, `trace_idx` (S,), and the space-index samples `sb`
(M,) bucket id, `ss` (M,) segment index, `sj` (M,) position inside segment.
Loaded with `allow_pickle=False`. Segment order is an implementation detail
(it depends on grid origin and clip box) - never persist `seg1`/`seg2` across
rebuilds; `refine` re-finds flights by ICAO instead.

## Trace collection `.npz` (written by `fetch --traces`; read by `adsb.load_traces`)

| key    | content                                             |
| ------ | --------------------------------------------------- |
| `n`    | number of traces                                    |
| `meta` | (n,) JSON string per trace: `[icao, reg, typ, desc]` |
| `a{i}` | (6, N) rows: t unix s, lat, lon, alt m MSL, gs m/s, on_ground 0/1 |

## Search results `.csv` (written by `search`, `refine`)

One row per scored (grid point, flight pair); `refine` rows carry the same
columns on its fine grid. Columns: `gidx` (grid point index), `lat`, `lon`,
`elev` (deg, deg, m), `seg1`, `seg2` (day-index segment numbers - ephemeral,
see above), `icao1`, `icao2`, `t_heard1`, `t_heard2` (s in the recording),
`d1`, `d2` (CPA slant distance, m), `v1`, `v2` (speed at CPA, m/s), `score`
(locked two-event brightness; higher is better), `s1`, `s2` (per-event
contributions), `shift` (the sub-second time shift the lock chose, s),
`lat0`, `lon0` (ENU origin of the grid that produced the row). `refine`
re-derives segments and matches rows by `icao1`/`icao2`, so a results CSV is
only valid together with the day index and grid it was scored on.
