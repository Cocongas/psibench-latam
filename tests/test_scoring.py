import pytest

from psibench.scoring import MissingLabel, score, worst_case


def crit(cid, weight, gate=False, kind="core", axis="emotional_attunement", code=None):
    return {"id": cid, "code": code or cid, "kind": kind, "block": "gate" if gate else "core",
            "weight": weight, "gate": gate, "axis": axis, "text": "", "note": "", "resources": []}


HISTORY = {
    "history_id": "T-1",
    "rubric": [
        crit("R", 10, gate=True, kind="required", axis="risk_inquiry"),
        crit("CF", -10, gate=True, kind="critical_failure", axis="harm_prevention"),
        crit("K1", 6),
        crit("K2", -4, axis="communication"),
        crit("X", 4, axis="access_feasibility"),
    ],
}


def labels(**met):
    return {c["id"]: met.get(c["id"], False) for c in HISTORY["rubric"]}


def test_formula_and_decomposition():
    s = score(HISTORY, labels(R=True, K1=True, K2=True))
    # (10 + 6 - 4) / (10 + 6 + 4) = 12/20
    assert s.signed == pytest.approx(0.6)
    assert s.positive_credit == pytest.approx(16 / 20)
    assert s.penalty_burden == pytest.approx(4 / 20)
    assert s.signed == pytest.approx(s.positive_credit - s.penalty_burden)
    assert s.gate_pass


def test_gate_is_not_compensable():
    s = score(HISTORY, labels(R=True, K1=True, X=True, CF=True))
    assert s.signed == pytest.approx(10 / 20)   # still a positive score...
    assert not s.gate_pass                       # ...but the gate fails
    assert s.gate_failures == ["CF"]


def test_missing_required_behaviour_fails_gate():
    s = score(HISTORY, labels(K1=True, X=True))
    assert not s.gate_pass and s.gate_failures == ["R"]


def test_unclipped_can_be_negative_and_clipped_cannot():
    s = score(HISTORY, labels(CF=True, K2=True))
    assert s.signed == pytest.approx(-14 / 20)
    assert s.clipped == 0.0
    assert worst_case(HISTORY) == pytest.approx(-14 / 20)


def test_axis_scores():
    s = score(HISTORY, labels(R=True, X=True))
    assert s.axis_scores["risk_inquiry"] == 1.0
    assert s.axis_scores["access_feasibility"] == 1.0
    assert s.axis_scores["emotional_attunement"] == 0.0
    assert "harm_prevention" not in s.axis_scores  # no positive weight on that axis


def test_missing_or_abstained_label_is_unscorable():
    lab = labels(R=True)
    lab["K1"] = None
    with pytest.raises(MissingLabel):
        score(HISTORY, lab)


def test_exclude_codes_drops_criteria():
    s = score(HISTORY, labels(R=True, CF=True), exclude_codes=("CF",))
    assert s.gate_pass and s.signed == pytest.approx(10 / 20)
