"""Align detected events with ADS-B flights when the recording start time is uncertain.

For every (detected event, flight within 12 km of the site) combination this computes the
recording-start time the pairing implies and reports offsets that explain two or more
events - the hypotheses a `search --utc` or a manual fit/run can then be run against.
Research companion of the EU session in docs/experiments.md; not part of the CLI.

Usage: uv run python scripts/offset_scan.py DETECTED_JSON DAY_NPZ LAT LON
"""

import json
import sys
from datetime import UTC, datetime
from itertools import count

import numpy as np

from dopplertrack.geo import lla_to_enu
from dopplertrack.search import DayIndex

det = json.load(open(sys.argv[1]))
idx = DayIndex.load(sys.argv[2])
plat, plon = float(sys.argv[3]), float(sys.argv[4])
e, n, u = lla_to_enu(plat, plon, 50.0, idx.lat0, idx.lon0)
p = np.array([e, n, u])

flights = []
for s in range(len(idx.icao)):
    sl = slice(idx.off[s], idx.off[s + 1])
    if sl.stop - sl.start < 30:
        continue
    d = np.linalg.norm(idx.enu[sl] - p, axis=1)
    i = int(np.argmin(d))
    if d[i] <= 12000:
        flights.append((float(idx.t[sl.start + i]), float(d[i]), str(idx.icao[s]), float(np.nanmax(idx.spd[sl]))))
print(f"{len(flights)} flights within 12 km")

buckets: dict[int, list] = {}
for ev in det:
    for ft, fd, icao, fv in flights:
        buckets.setdefault(round((ft - ev["t_cpa"]) / 3), []).append((ft - ev["t_cpa"], ev, ft, fd, icao, fv))
rows = []
for _, lst in buckets.items():
    deltas = [x[0] for x in lst]
    if len(lst) >= 2 and max(deltas) - min(deltas) <= 8:
        rows.append((len(lst), lst[0][0], lst))
rows.sort(key=lambda r: -r[0])
for k, d0, lst in rows[:5]:
    print(f"recording starts {datetime.fromtimestamp(d0, UTC).strftime('%Y-%m-%d %H:%M:%SZ')}, explains {k} events:")
    for delta, ev, ft, fd, icao, fv in lst:
        print(
            f"   ev t={ev['t_cpa']:7.1f} f0={ev['f0']:6.1f} v={ev['v']:5.0f} d={ev['d']:6.0f}"
            f" <-> {icao} {datetime.fromtimestamp(ft, UTC).strftime('%H:%M:%SZ')} d={fd / 1000:5.2f}km vmax={fv:4.0f}"
        )
if not rows:
    print("no offset explains two or more events")
