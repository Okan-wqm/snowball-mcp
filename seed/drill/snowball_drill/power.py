"""How often the judge passes each simulated brain, over many independent drills."""

from __future__ import annotations

from collections import Counter
from typing import Any

from .judge import QUESTIONS, judge
from .sim import BRAINS, run_drill


def power_table(runs: int, first_seed: int = 1) -> dict[str, Any]:
    table: dict[str, Any] = {}
    for name, traits in BRAINS.items():
        drills: Counter[str] = Counter()
        per_question = {q: Counter() for q in QUESTIONS}
        for seed in range(first_seed, first_seed + runs):
            result = judge(run_drill(traits, seed))
            drills[result["drill"]] += 1
            for q in QUESTIONS:
                per_question[q][result["verdicts"][q]] += 1
        table[name] = {"runs": runs, "drill_pass": drills["PASS"], "drill": dict(drills),
                       "questions": {q: dict(c) for q, c in per_question.items()}}
    return table
