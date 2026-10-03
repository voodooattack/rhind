"""The machine-readable twin of a report section (<proof>_data.json)."""

import json
from fractions import Fraction

from proofreport._decorators import _jsonable, _section_data
from proofreport._types import finding, point, row


def test_exact_values_stay_exact():
    big = 3**200
    assert _jsonable(big) == big
    assert json.loads(json.dumps(_jsonable(big))) == big
    assert _jsonable(Fraction(-7, 3)) == "-7/3"
    assert _jsonable({"a": (1, Fraction(1, 2)), 2: None}) == {
        "a": [1, "1/2"],
        "2": None,
    }


def test_unknown_types_become_strings():
    class Thing:
        def __str__(self):
            return "thing"

    assert _jsonable(Thing()) == "thing"


def test_section_without_data_is_none():
    assert _section_data("empty", [], []) is None


def test_table_section_carries_rows_findings_and_column_metadata():
    formats = [
        (
            "table",
            {
                "headers": ["K", "r"],
                "labels": ["facts", "ratio"],
                "legend": {"r": "bits ÷ floor"},
                "align": ["r", "r"],
            },
        )
    ]
    ys = [row(K=10, r="1.30×"), row(K=30, r=Fraction(4, 3)), finding("P1", "held")]
    d = _section_data("P1", ys, formats)
    assert d["title"] == "P1"
    assert d["headers"] == ["K", "r"]
    assert d["labels"] == ["facts", "ratio"]
    assert d["legend"] == {"r": "bits ÷ floor"}
    assert d["rows"] == [{"K": 10, "r": "1.30×"}, {"K": 30, "r": "4/3"}]
    assert d["findings"] == [{"label": "P1", "value": "held"}]
    assert "points" not in d
    json.dumps(d)  # serialisable as is


def test_plot_section_carries_points_with_partial_series():
    ys = [point(10, exact=1000, other=300), point(3000, exact=1000)]
    d = _section_data("curve", ys, [("plot", {"kind": "line"})])
    assert d["points"] == [
        {"x": 10, "exact": 1000, "other": 300},
        {"x": 3000, "exact": 1000},
    ]
    assert "headers" not in d


def test_report_builder_accepts_section_data(tmp_path):
    """_ReportBuilder uses __slots__; the data list must be one of them."""
    from proofreport._report import _ReportBuilder

    src = tmp_path / "999_probe.py"
    src.write_text("x = 1\n")
    b = _ReportBuilder(title="probe", source_path=str(src))
    b.add_section_data({"title": "s", "rows": [{"a": 1}]})
    assert b.section_data == [{"title": "s", "rows": [{"a": 1}]}]
