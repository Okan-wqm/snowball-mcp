"""How often the judge passes each simulated brain over many independent drills; how the effect question's power
depends on the size of the effect; and when a trap family is strong enough to enter the operator's pool (E319)."""

from __future__ import annotations

import math
import random
from collections import Counter
from fractions import Fraction
from typing import Any

from .judge import QUESTIONS, judge
from .judge import _effect as effect_question
from .sim import BRAINS, DEFAULT_PARAMS, run_drill

CALIBRATION_MIN_RUNS = 20  # lessonless runs of a trap family before it may enter the pool
CALIBRATION_MIN_RATE = Fraction(85, 100)  # share of them it must break (`tohum/22b`)


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


def effect_power(p_with: float, p_without: float, runs: int, params: dict[str, Any] | None = None,
                 seed: int = 1) -> dict[str, int]:
    """Verdicts of the reference effect question over ``runs`` drills of k independent pairs, a pair's arms
    succeeding with probability ``p_with`` and ``p_without``."""
    params = dict(DEFAULT_PARAMS if params is None else params)
    rng = random.Random(seed)
    out: Counter[str] = Counter()
    for _ in range(runs):
        key = {"family": "f", "instances": {f"i{j}": {"family": "f"} for j in range(params["k"])}}
        pairs = [{"instance_id": f"i{j}", "with": rng.random() < p_with, "without": rng.random() < p_without}
                 for j in range(params["k"])]
        out[effect_question(key, {"effect": pairs}, params)[0]] += 1
    return {v: out[v] for v in ("PASS", "FAIL", "UNMEASURABLE")}


def unmeasurable_risk(p_broken: Fraction, k: int, min_broken: int) -> Fraction:
    """The chance that a lessonless arm breaking each run with probability ``p_broken`` breaks fewer than
    ``min_broken`` of ``k``: the drill is then UNMEASURABLE by construction and the family is spent."""
    return sum((Fraction(math.comb(k, i)) * p_broken ** i * (1 - p_broken) ** (k - i) for i in range(min_broken)),
               Fraction(0))


def calibration(broken: int, runs: int, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """A trap family's calibration on the lessonless arm, run by the operator before the family enters the pool.

    Ready when it was run at least ``CALIBRATION_MIN_RUNS`` times and broke at least 85% of them: at k = 30 and
    21 broken required, a family breaking 70% gives UNMEASURABLE in 41% of drills by construction, one breaking
    85% in 1% (E319).
    """
    params = dict(DEFAULT_PARAMS if params is None else params)
    if runs <= 0 or not 0 <= broken <= runs:
        raise ValueError("broken must be between 0 and runs, runs above 0")
    rate = Fraction(broken, runs)
    risk = unmeasurable_risk(rate, params["k"], params["min_broken_without"])
    return {"broken": broken, "runs": runs, "rate": f"{float(rate):.4f}", "unmeasurable_risk": f"{float(risk):.4f}",
            "ready": runs >= CALIBRATION_MIN_RUNS and rate >= CALIBRATION_MIN_RATE}
