"""Score the worked-example replies and print the tables used in docs/worked_example.md.

    python scripts/worked_example.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from psibench.build import load_histories  # noqa: E402
from psibench.scoring import score  # noqa: E402


def labels_by_id(history: dict, by_code: dict[str, bool]) -> dict[str, bool]:
    codes = {c["code"] for c in history["rubric"]}
    if codes != set(by_code):
        raise ValueError(f"{history['history_id']}: labels {sorted(set(by_code) ^ codes)} do not match the rubric")
    return {c["id"]: by_code[c["code"]] for c in history["rubric"]}


def scored_replies() -> list[tuple[str, str, object, int]]:
    histories = {h["history_id"]: h for h in load_histories(ROOT / "data" / "dev" / "dev.jsonl")}
    with open(ROOT / "data" / "worked_example" / "F03_replies.yaml", encoding="utf-8") as f:
        spec = yaml.safe_load(f)
    out = []
    for reply in spec["replies"]:
        words = len(reply["text"].split())
        for hid, block in reply["scored_against"].items():
            h = histories[hid]
            out.append((reply["id"], hid, score(h, labels_by_id(h, block["labels"])), words))
    return out


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    print("| Reply | History | Gate | Gate failures | Signed | Clipped | Credit | Penalty | Words |")
    print("|---|---|---|---|---:|---:|---:|---:|---:|")
    for rid, hid, s, words in scored_replies():
        print(f"| {rid} | {hid} | {'pass' if s.gate_pass else 'fail'} | {', '.join(s.gate_failures) or '-'} | "
              f"{s.signed:+.3f} | {s.clipped:.3f} | {s.positive_credit:.3f} | {s.penalty_burden:.3f} | {words} |")


if __name__ == "__main__":
    main()
