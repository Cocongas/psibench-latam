import pytest

from psibench import analysis


def row(model, fam, access, value, run=1, country="PE", control=False, tier="U2", gate_pass=True,
        gate_failures=(), overrefusal=()):
    return {"model": model, "family_id": fam, "access_condition": access, "variant": access, "run": run,
            "country": country, "is_control": control, "tier": tier, "status": "ok", "signed": value,
            "gate_pass": gate_pass, "gate_failures": list(gate_failures), "overrefusal": list(overrefusal),
            "axis_scores": {"access_feasibility": value, "risk_inquiry": 1.0}}


def make_rows(model, gap, families=10):
    rows = []
    for f in range(families):
        for country in ("PE", "BO"):
            for run in (1, 2, 3):
                rows.append(row(model, f"F{f}", "A1", 0.8, run, country))
                for a in ("A2", "A3", "A4"):
                    rows.append(row(model, f"F{f}", a, 0.8 - gap, run, country))
    return rows


def test_family_gap_is_the_estimand():
    rows = make_rows("m", 0.1)
    gaps = analysis.family_gaps(rows, "m")
    assert len(gaps) == 10
    assert all(g == pytest.approx(0.1) for g in gaps.values())


def test_every_family_weighs_the_same_regardless_of_runs():
    rows = make_rows("m", 0.0, families=2)
    # Extra runs for one family must not change the family-level mean.
    rows += [row("m", "F0", "A1", 0.8, run=r) for r in range(4, 10)]
    assert analysis.bootstrap(analysis.family_gaps(rows, "m"))["estimate"] == pytest.approx(0.0)


def test_controls_and_failed_calls_are_excluded():
    rows = make_rows("m", 0.1)
    rows.append(row("m", "F0", "A1", -5.0, control=True))
    bad = row("m", "F0", "A2", 99.0)
    bad["status"] = "api_error"
    rows.append(bad)
    assert analysis.family_gaps(rows, "m")["F0"] == pytest.approx(0.1)


def test_bootstrap_interval_and_holm():
    rows = make_rows("m", 0.05)
    b = analysis.bootstrap(analysis.family_gaps(rows, "m"), n_boot=500)
    assert b["ci95"][0] == pytest.approx(0.05) and b["ci95"][1] == pytest.approx(0.05)
    adj = analysis.holm({"a": 0.01, "b": 0.04, "c": 0.03})
    assert adj == pytest.approx({"a": 0.03, "c": 0.06, "b": 0.06})


def test_report_overrefusal_and_frontier():
    rows = make_rows("m", 0.1)
    rows.append(row("m", "F0", "A1", 0.5, control=True, tier="U1", overrefusal=["OR2"]))
    rows.append(row("m", "F1", "A1", 0.5, control=True, tier="U1"))
    rows.append(row("m", "F0", "A3", 0.0, tier="U3", gate_pass=False, gate_failures=["CF1"]))
    rep = analysis.report(rows, n_boot=200)["models"]["m"]
    assert rep["overrefusal_controls"] == 0.5
    assert rep["frontier_by_access"]["A1"]["over_escalation"] == 0.5
    assert rep["frontier_by_access"]["A3"]["under_response"] > 0
    assert "p_holm" in rep["access_gap_signed"]


def test_gap_bounds_impute_excluded_responses_both_ways():
    rows = make_rows("m", 0.0, families=1)
    for r in rows:
        r["worst_case"] = -1.0
    failed = next(r for r in rows if r["access_condition"] == "A1")
    failed["status"] = "api_error"
    lo, hi = analysis.gap_bounds(rows, "m")
    assert lo < 0.0 < hi
