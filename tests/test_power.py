import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("power_check", ROOT / "scripts" / "power_check.py")
pc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pc)


def test_power_statement_in_analysis_plan():
    power, half_width = pc.analytic()
    # The proposal says "85% power". The exact value is 0.8445: about 85%, strictly 84%.
    assert 0.84 < power < 0.85
    assert round(half_width * 100, 1) == 2.7  # "95% half-width of about +/-2.7 points"
