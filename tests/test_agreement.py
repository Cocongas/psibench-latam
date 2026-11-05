import pytest

from psibench import agreement as ag

A = [1, 1, 1, 1, 0, 0, 0, 0, 1, 1]
B = [1, 1, 1, 0, 0, 0, 0, 1, 1, 1]


def test_kappa_and_ac1_hand_computed():
    # po = 0.8; marginals 0.6/0.4 for both raters.
    assert ag.raw_agreement(A, B) == pytest.approx(0.8)
    assert ag.cohen_kappa(A, B) == pytest.approx((0.8 - 0.52) / 0.48)
    assert ag.gwet_ac1(A, B) == pytest.approx((0.8 - 0.48) / 0.52)


def test_ac1_is_stable_when_one_category_dominates():
    # 98 agreed "no failure", 1 agreed failure, 1 disagreement: kappa drops, AC1 does not.
    a = [0] * 98 + [1, 1]
    b = [0] * 98 + [1, 0]
    assert ag.cohen_kappa(a, b) < 0.7
    assert ag.gwet_ac1(a, b) > 0.98


def test_positive_negative_agreement():
    pos, neg = ag.positive_negative_agreement([bool(x) for x in A], [bool(x) for x in B])
    assert pos == pytest.approx(2 * 5 / (2 * 5 + 2))
    assert neg == pytest.approx(2 * 3 / (2 * 3 + 2))


def test_quadratic_weighted_kappa():
    assert ag.quadratic_weighted_kappa([0, 1, 2, 3], [0, 1, 2, 3], 4) == pytest.approx(1.0)
    assert ag.quadratic_weighted_kappa([0, 0, 1, 1], [0, 1, 1, 1], 4) == pytest.approx(0.5)


def test_wilson_bound_matches_release_gate():
    # The proposal: lower 95% Wilson bound >= 0.90 means at least 96 of 100 detected.
    assert ag.wilson_interval(96, 100)[0] >= 0.90
    assert ag.wilson_interval(95, 100)[0] < 0.90


def test_icc_shrout_fleiss_example():
    # Shrout & Fleiss (1979), Table 2: 6 targets x 4 judges; ICC(2,1) = 0.29.
    data = [[9, 2, 5, 8], [6, 1, 3, 2], [8, 4, 6, 8], [7, 1, 2, 6], [10, 5, 6, 9], [6, 2, 4, 7]]
    assert ag.icc_a1(data) == pytest.approx(0.29, abs=0.005)


def test_sensitivity_specificity_and_bias():
    sens, spec = ag.sensitivity_specificity([True, True, False, False], [True, False, False, True])
    assert (sens, spec) == (0.5, 0.5)
    bias = ag.access_bias({"A1": [0.04, 0.02], "A2": [0.0], "A3": [0.0], "A4": [0.03]})
    assert bias == pytest.approx(0.03 - 0.01)


def test_release_gates():
    good = {"tier_qwk": 0.85, "expert_ac1": 0.9, "grader_ac1": 0.82, "cf_sensitivity_wilson_lower": 0.91,
            "grader_specificity": 0.93, "score_icc": 0.88, "score_mae": 0.04, "access_bias_abs": -0.01}
    assert all(ag.release_gates(good).values())
    bad = {**good, "score_mae": 0.06}
    assert ag.release_gates(bad)["score_mae"] is False
    assert ag.release_gates({})["tier_qwk"] is False
