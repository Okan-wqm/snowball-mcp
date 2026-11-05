"""The operator's scorer of the Founder's forecasts (register E534; `tohum/26g`; the autonomy plan, section 3). Stdlib
only, outside the brain and the capsule: the Founder never writes it and it never reaches the Founder.

Its input is the launcher's metrics rows (<work>/pilot-metrics.jsonl), each with the referee's signed `forecasts[]`
of the head that cycle dispatched (`launch.py` copies it). Nothing else is read and nothing is written; the daily
report (`daily_report.py` line 5) prints what `score` returns.

Binding. The events are the judged pushes, in record order: a session row that pushed and has the verdict
`accepted`, `frozen` (both 1) or `rejected` (0); a run without a verdict (an outage, a `noop`) is no event. A forecast
row binds to the first judged push whose signed listing names it: the referee names only rows in the head it judged,
so a row written after that run was dispatched is not in its listing, and a row named again by a later run (still
past the last accepted commit) stays bound to the first. Of the rows a push newly names, the last whose form holds
counts for it; the others are counted as extra or invalid and never scored.

Scores, each the Founder's against a base-rate forecaster on the same events, prequential (no event sees a later
one). A push without a counted forecast is scored at the base rate, so it adds nothing either way.
- p_accept_first_push: Brier and log-loss (p clipped to [0.001, 0.999]) against the Laplace rate of the earlier
  pushes' verdicts, (accepted + 1) / (pushes + 2).
- p_solve: the counted forecast's task is solved (1) at the first judged push, from its own on and within its
  `horizon_runs` pushes, that is accepted with a counted forecast naming the same task (`task_sha256`); 0 once the
  horizon has passed without one; open until then. Base: the Laplace rate of the solve events resolved earlier.
- cost and turns: pinball loss at p10, p50 and p90 (cost in USD, the session's `cost_usd`; turns, its `turns`)
  against the earlier pushes' empirical quantiles; scored only once MIN_HISTORY earlier outcomes exist.
A confidence map is drawn from FAIL_EVENTS failures (rejections with a counted forecast) on; until then the report
says how few there are. No map is drawn here yet.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "bootstrap"))
from snowball_bootstrap import forecast  # noqa: E402  (the form `26g` gives, the referee's own reader)

JUDGED = {"accepted": 1, "frozen": 1, "rejected": 0}
CLIP = 0.001
MIN_HISTORY = 10
FAIL_EVENTS = 30  # failure events before a confidence map may be drawn (the plan, section 3)
QUANTILES = (("p10", 0.1), ("p50", 0.5), ("p90", 0.9))


def laplace(ys: list[int]) -> float:
    return (sum(ys) + 1) / (len(ys) + 2)


def brier(p: float, y: int) -> float:
    return (p - y) ** 2


def log_loss(p: float, y: int) -> float:
    p = min(max(p, CLIP), 1 - CLIP)
    return -math.log(p) if y else -math.log(1 - p)


def quantile(xs: list[float], q: float) -> float:
    """The q-quantile of xs, linearly interpolated between order statistics."""
    s = sorted(xs)
    h = (len(s) - 1) * q
    lo = math.floor(h)
    return s[lo] if lo + 1 >= len(s) else s[lo] + (h - lo) * (s[lo + 1] - s[lo])


def pinball(predicted: dict[str, float], y: float) -> float:
    """The mean pinball loss of a p10/p50/p90 forecast for the outcome y."""
    return sum(max(q * (y - predicted[k]), (q - 1) * (y - predicted[k])) for k, q in QUANTILES) / len(QUANTILES)


def _number(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def bind(rows: list[Any]) -> list[dict[str, Any]]:
    """The judged pushes in record order, each with its outcome and the forecast that counts for it (or None)."""
    seen: set[str] = set()
    runs = []
    for row in rows:
        if not isinstance(row, dict) or not row.get("pushed") or row.get("verdict") not in JUDGED:
            continue
        listing = row.get("forecasts") if isinstance(row.get("forecasts"), list) else []
        named = [e for e in listing if isinstance(e, dict) and isinstance(e.get("row_hash"), str)]
        new = [e for e in named if e["row_hash"] not in seen]
        valid = [e["forecast"] for e in new if forecast.valid_projection(e.get("forecast"))]
        seen.update(e["row_hash"] for e in named)
        runs.append({"stamp": row.get("stamp"), "y": JUDGED[row["verdict"]],
                     "cost": row["cost_usd"] if _number(row.get("cost_usd")) else None,
                     "turns": row["turns"] if _number(row.get("turns")) else None,
                     "forecast": valid[-1] if valid else None,
                     "extra": max(len(valid) - 1, 0), "invalid": len(new) - len(valid)})
    return runs


def _pair() -> dict[str, Any]:
    return {"n": 0, "founder": 0.0, "base": 0.0}


def _add(tally: dict[str, Any], founder: float, base: float) -> None:
    tally["n"] += 1
    tally["founder"] += founder
    tally["base"] += base


def _means(tally: dict[str, Any]) -> dict[str, Any]:
    n = tally["n"]
    return {"n": n, "founder": tally["founder"] / n if n else None, "base": tally["base"] / n if n else None}


def score(rows: list[Any]) -> dict[str, Any]:
    """Every score of the module's docstring, from the metrics rows."""
    runs = bind(rows)
    accept = {"brier": _pair(), "log": _pair()}
    solve = {"brier": _pair(), "log": _pair()}
    spread = {"cost": _pair(), "turns": _pair()}
    verdicts: list[int] = []
    resolved: list[tuple[int, int]] = []  # (the push it resolved at, outcome)
    pending: list[dict[str, Any]] = []
    history: dict[str, list[float]] = {"cost": [], "turns": []}
    fails = forecasted = 0
    for k, run in enumerate(runs):
        f, y = run["forecast"], run["y"]
        base = laplace(verdicts)
        p = f["p_accept_first_push_permille"] / 1000 if f else base
        _add(accept["brier"], brier(p, y), brier(base, y))
        _add(accept["log"], log_loss(p, y), log_loss(base, y))
        verdicts.append(y)
        forecasted += f is not None
        fails += f is not None and y == 0
        if f:
            pending.append({"k": k, "task": f["task_sha256"], "horizon": f["horizon_runs"],
                            "p": f["p_solve_permille"] / 1000, "base": laplace([o for j, o in resolved if j < k])})
        for s in list(pending):
            if y == 1 and f and f["task_sha256"] == s["task"]:
                outcome = 1
            elif k - s["k"] + 1 >= s["horizon"]:
                outcome = 0
            else:
                continue
            pending.remove(s)
            resolved.append((k, outcome))
            _add(solve["brier"], brier(s["p"], outcome), brier(s["base"], outcome))
            _add(solve["log"], log_loss(s["p"], outcome), log_loss(s["base"], outcome))
        for name, field, unit in (("cost", "cost_micros", 1e6), ("turns", "turns", 1)):
            outcome = run[name]
            if outcome is None:
                continue
            if len(history[name]) >= MIN_HISTORY:
                base_q = {key: quantile(history[name], q) for key, q in QUANTILES}
                said = {key: f[field][key] / unit for key, _q in QUANTILES} if f else base_q
                _add(spread[name], pinball(said, outcome), pinball(base_q, outcome))
            history[name].append(outcome)
    return {"pushes": len(runs), "forecasted": forecasted, "fail_events": fails, "fail_needed": FAIL_EVENTS,
            "extra": sum(r["extra"] for r in runs), "invalid": sum(r["invalid"] for r in runs),
            "accept": {k: _means(v) for k, v in accept.items()},
            "solve": {k: _means(v) for k, v in solve.items()}, "solve_open": len(pending),
            "cost": _means(spread["cost"]), "turns": _means(spread["turns"])}
