"""Quantify one day's ADS-B archive for a bounding box: how many traces touch it, how
many are propeller aircraft, and where the registrations come from. The EU readiness
probe of 2026-11-13 as a command - run it for any date and box before spending search
time there. Only the archive stream is pulled; nothing large is stored."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field

from .adsb import AircraftTypes, Trace
from .fetch import fetch_day

# ICAO registration prefix -> country, long prefixes first: enough to group a day's
# box traffic by origin without shipping the full Annex table.
REG_COUNTRY = {
    "9A": "Croatia",
    "9H": "Malta",
    "5B": "Cyprus",
    "EC": "Spain",
    "CS": "Portugal",
    "EI": "Ireland",
    "HB": "Switzerland",
    "OK": "Czechia",
    "OM": "Slovakia",
    "HA": "Hungary",
    "S5": "Slovenia",
    "YL": "Latvia",
    "LY": "Lithuania",
    "SP": "Poland",
    "LX": "Luxembourg",
    "YR": "Romania",
    "LZ": "Bulgaria",
    "TC": "Türkiye",
    "OO": "Belgium",
    "PH": "Netherlands",
    "OE": "Austria",
    "SE": "Sweden",
    "LN": "Norway",
    "OY": "Denmark",
    "OH": "Finland",
    "SX": "Greece",
    "ES": "Estonia",
    "UR": "Ukraine",
    "RA": "Russia",
    "D": "Germany",
    "F": "France",
    "G": "United Kingdom",
    "I": "Italy",
    "N": "United States",
    "C": "Canada",
    "VH": "Australia",
}


def reg_country(reg: str | None) -> str:
    r = (reg or "").strip().upper()
    for n in (2, 1):
        if r[:n] in REG_COUNTRY:
            return REG_COUNTRY[r[:n]]
    return "unknown" if not r else "other"


@dataclass
class CoverageStats:
    seen: int = 0
    failed: int = 0
    bbox_traces: int = 0
    props: int = 0
    unknown_designator: int = 0
    countries: Counter = field(default_factory=Counter)
    designators: Counter = field(default_factory=Counter)

    def to_dict(self) -> dict:
        n = self.bbox_traces
        return {
            "traces_seen": self.seen,
            "parse_failed": self.failed,
            "bbox_traces": n,
            "prop": self.props,
            "prop_share": round(self.props / n, 3) if n else None,
            "unknown_designator": self.unknown_designator,
            "countries": dict(self.countries.most_common()),
            "top_designators": dict(self.designators.most_common(15)),
        }


def summarize(
    traces: Iterable[Trace], types: AircraftTypes | None = None
) -> CoverageStats:
    """Aggregate bbox traces (from fetch_day or any source) into prop/country counts."""
    types = types or AircraftTypes()
    st = CoverageStats()
    for tr in traces:
        st.bbox_traces += 1
        st.designators[tr.typ or "?"] += 1
        if types.engine(tr.typ) is None:
            st.unknown_designator += 1
        if types.is_prop(tr.typ):
            st.props += 1
        st.countries[reg_country(tr.reg)] += 1
    return st


def collect(
    date: str,
    bbox,
    pod: str = "planes-readsb-prod-0",
    types: AircraftTypes | None = None,
    progress: Callable[[int, int], None] | None = None,
) -> CoverageStats:
    counts: dict[str, int] = {}
    traces = fetch_day(date, bbox, pod=pod, progress=progress, stats=counts)
    st = summarize(traces, types)
    st.seen, st.failed = counts.get("seen", 0), counts.get("failed", 0)
    return st
