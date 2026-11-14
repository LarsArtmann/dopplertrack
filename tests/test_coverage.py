"""Coverage aggregation offline: registration-prefix country mapping, prop share via a
small Doc 8643 CSV, and the stats dict shape. The network is never touched."""

import numpy as np
import pytest

from dopplertrack.adsb import AircraftTypes, Trace
from dopplertrack.coverage import reg_country, summarize


@pytest.fixture
def types(tmp_path):
    p = tmp_path / "doc8643.csv"
    p.write_text("Designator,EngineType\nC172,Piston\nC25C,Jet\nTB20,Piston\n")
    return AircraftTypes(path=p)


def _trace(reg="D-EKAA", typ="C172"):
    return Trace(
        "a2f38b",
        reg,
        typ,
        "desc",
        np.array([0.0, 1.0]),
        np.array([48.0, 48.001]),
        np.array([11.0, 11.001]),
        np.array([500.0, 500.0]),
        np.array([50.0, 50.0]),
        np.array([False, False]),
    )


def test_reg_country_maps_prefixes():
    assert reg_country("D-EKAA") == "Germany"
    assert reg_country("N628TS") == "United States"
    assert reg_country("PH-ABC") == "Netherlands"
    assert reg_country("OO-SOM") == "Belgium"
    assert reg_country("9A-XYZ") == "Croatia"
    assert reg_country("cs-lav") == "Portugal"
    assert reg_country("XX-YYY") == "other"
    assert reg_country(None) == "unknown"
    assert reg_country("") == "unknown"


def test_summarize_counts_props_and_unknowns(types):
    trs = [
        _trace(typ="C172"),
        _trace(reg="N1", typ="C25C"),
        _trace(typ=None),
        _trace(reg="ZZ-1", typ="ZZZ"),
    ]
    st = summarize(trs, types)
    assert st.bbox_traces == 4
    assert st.props == 3
    assert st.unknown_designator == 2
    assert st.countries == {"Germany": 2, "United States": 1, "other": 1}
    assert st.to_dict()["prop_share"] == 0.75


def test_summarize_empty_is_well_formed(types):
    st = summarize([], types)
    assert st.to_dict() == {
        "traces_seen": 0,
        "parse_failed": 0,
        "bbox_traces": 0,
        "prop": 0,
        "prop_share": None,
        "unknown_designator": 0,
        "countries": {},
        "top_designators": {},
    }
