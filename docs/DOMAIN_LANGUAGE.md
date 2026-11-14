# Domain language

The vocabulary of `dopplertrack`: what each term means here, and where the
code lives that embodies it. Terms are the contract between physics, data,
and search - new code should reuse these names, not invent parallel ones.

## Signals

- **Recording** - the audio (or video's audio track) whose location is the
  unknown. All recording times are seconds from its start.
- **Spectrogram** - whitened STFT of the 40-450 Hz band, 0.25 s hop. Stored
  as `.npz` (`audio.Spectrogram`).
- **Whitening** - each frequency bin is converted to dB above its own median
  across the whole recording, so a tone that is loud all day does not drown
  a faint 6 dB sweep (`audio.py`).
- **Flyover / event** - one aircraft pass close enough that its propeller
  tone sweeps measurably: high on approach, `f0` at closest approach, low on
  departure.
- **f0, harmonics** - the propeller blade-pass fundamental; `harmonics 2`
  scores the fundamental and its second multiple, which adds brightness on
  quieter aircraft.
- **Burst** - a broadband pass of a train or truck that mimics a sweep;
  detect measures the share of surrounding time that is a burst
  (`tracks.burst_mask`) and the CLI can drop high-burst events.
- **Ridge** - the bright curve traced through the spectrogram; the `ridge`
  score mode measures how closely a candidate curve follows it, for faint
  events where absolute brightness misleads.

## Geometry and physics

- **CPA (closest point of approach)** - the moment an aircraft passes nearest
  the microphone; `d` is the slant distance (straight line, metres), `v` the
  ground speed at that moment.
- **Emission time vs observation time** - the heard frequency at time `t_obs`
  was produced at `t_e` where `t_obs = t_e + r(t_e)/c`. All Doppler math uses
  **emission-time kinematics**; modelling with observation-time radial
  velocity gives a visibly wrong curve, not just a shifted one
  (`doppler.py`; `tests/test_physics.py` proves the distinction).
- **ENU** - East-North-Up metres about an origin `(lat0, lon0)`; the frame all
  search geometry lives in (`geo.py`).
- **Grid** - candidate observer positions on a fixed spacing (200 m regional,
  50 m refined) with elevations from terrain tiles.

## Data

- **Trace** - one aircraft's ADS-B points for one day: time (unix s), lat,
  lon, altitude, ground speed, on-ground flags, plus registration/type
  metadata (`adsb.Trace`).
- **Day archive** - adsb.lol's single daily tar (possibly split `.tar.aa`,
  `.tar.ab`) under a pod name; streamed, never stored whole (`fetch.py`).
- **Pod** - the feed variant: `planes-readsb-prod-0` (default) vs the
  `mlatonly` pod, where aircraft without ADS-B transponders but with MLAT
  fixes appear.
- **Day index** - the day's flights resampled to 1 Hz emission times in one
  ENU frame plus per-10 s space samples; what a search actually reads
  (`search.DayIndex`).
- **Segment** - one continuous airborne stretch of one flight inside the day
  index. Segment *numbers* depend on grid origin and clip box - they are
  ephemeral and never reused across rebuilds; matches are re-found by ICAO.
- **Bucket** - the 10 s time slot that lets the pair join find co-located
  flights without a per-point cross product (`search.py`).

## Search

- **Pair join** - candidate (grid point, flight pair) generation: two events
  heard Δt apart at slant distances d1, d2 require two aircraft that were
  within d1 + d2 of each other, Δt apart. Bucketed, then filtered on speed
  and distance ratio (`search.pair_candidates`).
- **Lens lattice** - precomputed per-point spatial neighbourhoods (the
  "lens") so distance gates and silence checks are table lookups, not
  per-pair distance computations (`search.py`).
- **Silence filter** - drops a grid point for a pair if a third aircraft was
  within 6 km of it between the two events (± 40 s margin): a louder prop
  would have masked the recording's tones (`LensParams.silence_d_m`).
- **Locked scoring** - the two events are scored as one: event 1's sub-second
  time shift and f0 scale are swept, and event 2 must use the *same* shift,
  via the clock bridge `t0_map = t_cpa - t_heard` (unix to audio offset)
  (`score.locked_score`). This is what makes two flyovers locate a site.
- **Coverage weighting** - a candidate's score is the mean brightness over
  the whole measured window with uncovered parts counting as zero, so a
  flight that only half-overlaps the data cannot win on its bright half.
- **Known-point search** - `search --point` scores one location against all
  flights: the quickest check when the answer is already known.
- **Verdict** - a location-independent null distribution over wrong
  candidates, giving the top result a calibrated p (located / ambiguous /
  no match) (`verdict.py`).
