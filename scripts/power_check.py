"""Check the power statement in the analysis plan.

Planning assumption: the within-family access gap has SD 0.15. With 120 test
families and a two-sided test at alpha = 0.05/6 (Holm across six models, most
stringent step), what is the power to detect a 5-point (0.05) gap, and what is
the 95% half-width?

    python scripts/power_check.py
"""

from __future__ import annotations

import random
from math import sqrt
from statistics import NormalDist, mean, stdev

N_FAMILIES = 120
SD = 0.15
GAP = 0.05
ALPHA = 0.05 / 6


def analytic(n=N_FAMILIES, sd=SD, gap=GAP, alpha=ALPHA) -> tuple[float, float]:
    z = NormalDist()
    se = sd / sqrt(n)
    crit = z.inv_cdf(1 - alpha / 2)
    power = z.cdf(gap / se - crit) + z.cdf(-gap / se - crit)
    half_width = z.inv_cdf(0.975) * se
    return power, half_width


def simulated(n=N_FAMILIES, sd=SD, gap=GAP, alpha=ALPHA, sims=20000, seed=1) -> float:
    """Draw family gaps, test the mean with a z statistic on the sample SD."""
    rng = random.Random(seed)
    crit = NormalDist().inv_cdf(1 - alpha / 2)
    hits = 0
    for _ in range(sims):
        xs = [rng.gauss(gap, sd) for _ in range(n)]
        hits += abs(mean(xs) / (stdev(xs) / sqrt(n))) > crit
    return hits / sims


if __name__ == "__main__":
    p, hw = analytic()
    print(f"Analytic power:  {p:.4f}  (proposal: 85%)")
    print(f"95% half-width:  +/-{hw * 100:.1f} points (proposal: +/-2.7)")
    print(f"Simulated power: {simulated():.3f}")
