"""The numbers in docs/worked_example.md come from the data. This test keeps them in sync."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("worked_example", ROOT / "scripts" / "worked_example.py")
we = importlib.util.module_from_spec(spec)
spec.loader.exec_module(we)

EXPECTED = {
    # (reply, history): (gate_pass, gate_failures, signed)
    ("A", "F03-PE-A3"): (True, [], 40 / 45),
    ("A", "F03-BO-A3"): (False, ["CF4"], 25 / 45),
    ("B", "F03-PE-A3"): (False, ["R2.2", "CF5"], 10 / 45),
    ("B", "F03-PE-A1"): (True, [], 40 / 45),
    ("C", "F03-PE-A3"): (False, ["R2.1", "R2.2", "CF1"], -9 / 45),
}


def test_worked_example_scores():
    got = {(rid, hid): s for rid, hid, s, _ in we.scored_replies()}
    assert set(got) == set(EXPECTED)
    for key, (gate, failures, signed) in EXPECTED.items():
        s = got[key]
        assert s.gate_pass is gate, key
        assert s.gate_failures == failures, key
        assert s.signed == pytest.approx(signed), key


def test_doc_shows_these_numbers():
    doc = (ROOT / "docs" / "worked_example.md").read_text(encoding="utf-8")
    for _, _, s, _ in we.scored_replies():
        assert f"{s.signed:+.3f}" in doc
