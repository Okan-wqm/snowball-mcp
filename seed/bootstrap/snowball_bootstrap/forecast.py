"""The Founder's forecast rows (`tohum/26g`, E534): what the signed result names of them, never a reason.

A forecast is a row of `founder-ledger.jsonl` with ``kind: forecast`` and ``payload.forecast`` in the form `26g`
gives. The referee does not judge it and never rejects a push for it: the ledger's own rules (`ledgercheck`) are the
gate, and a forecast is the Founder's memory like every other row. What the referee adds is the binding: on every
push it judges, it names in the signed result the forecast rows the head carries beyond the last accepted commit's
ledger (`listed`). A row is named only when it is in the head the run judged, so a forecast written after that run
was dispatched cannot be in it: it can never be read as the forecast of a verdict its author had already seen.

Each named row is ``{row_hash, line, forecast}`` when its form holds (``forecast`` is ``projection``: the numbers,
the capability, ``task_sha256`` and how many evidence ids and unknowns it gives, no free text of the Founder's) or
``{row_hash, line, invalid}`` naming the first rule it breaks. Scoring (which run a row binds to, the base rate a
push without one is scored at) is the operator's, outside the brain (`seed/founder/forecast_score.py`).
"""

from __future__ import annotations

import hashlib
from typing import Any

from . import canon, ledgercheck

KIND = "forecast"
CAPABILITIES = ("can", "can_with_question", "cannot_with_current_self")
PERMILLE = ("p_solve_permille", "p_accept_first_push_permille")
QUANTILES = ("p10", "p50", "p90")
SPREADS = ("cost_micros", "turns")
TEXTS = {"task": 200, "reason": 500}  # each a string of 1 to this many characters
LISTS = {"evidence": 200, "unknowns": 500}  # each a list of such strings
MAX_ITEMS = 20
HORIZON = (1, 10)  # horizon_runs, inclusive
FIELDS = frozenset(("task", "capability", "reason", "horizon_runs", *PERMILLE, *SPREADS, *LISTS))
MAX_LISTED = 50  # the newest rows past the last accepted commit; an older one was named by an earlier run


def _int(value: Any, low: int, high: int | None = None) -> bool:
    return type(value) is int and low <= value and (high is None or value <= high)


def _text(value: Any, limit: int) -> bool:
    return isinstance(value, str) and 1 <= len(value) <= limit


def _spread(value: Any) -> bool:
    return (isinstance(value, dict) and set(value) == set(QUANTILES) and all(_int(value[q], 0) for q in QUANTILES)
            and value["p10"] <= value["p50"] <= value["p90"])


def broken_rule(forecast: Any) -> str | None:
    """The first rule of `26g` the payload's ``forecast`` breaks, or None when its form holds."""
    if not isinstance(forecast, dict):
        return "not_an_object"
    if set(forecast) - FIELDS:
        return "unknown_field"
    missing = sorted(FIELDS - set(forecast))
    if missing:
        return f"missing:{missing[0]}"
    for name, limit in TEXTS.items():
        if not _text(forecast[name], limit):
            return f"field:{name}"
    if forecast["capability"] not in CAPABILITIES:
        return "field:capability"
    for name in PERMILLE:
        if not _int(forecast[name], 0, 1000):
            return f"field:{name}"
    if not _int(forecast["horizon_runs"], *HORIZON):
        return "field:horizon_runs"
    for name in SPREADS:
        if not _spread(forecast[name]):
            return f"field:{name}"
    for name, limit in LISTS.items():
        items = forecast[name]
        if not (isinstance(items, list) and len(items) <= MAX_ITEMS and all(_text(i, limit) for i in items)):
            return f"field:{name}"
    return None


def projection(forecast: dict[str, Any]) -> dict[str, Any]:
    """What the signed result keeps of a forecast whose form holds: what is scored, and no free text."""
    return {"task_sha256": hashlib.sha256(forecast["task"].encode("utf-8")).hexdigest(),
            "capability": forecast["capability"], "horizon_runs": forecast["horizon_runs"],
            **{name: forecast[name] for name in PERMILLE},
            **{name: {q: forecast[name][q] for q in QUANTILES} for name in SPREADS},
            "evidence_n": len(forecast["evidence"]), "unknowns_n": len(forecast["unknowns"])}


def valid_projection(value: Any) -> bool:
    """Whether a projection read back (from a signed result, or a record that copied one) has the form `projection`
    gives: the scorer reads the numbers through this, never trusting a record's shape."""
    return (isinstance(value, dict)
            and set(value) == {"task_sha256", "capability", "horizon_runs", *PERMILLE, *SPREADS, "evidence_n",
                               "unknowns_n"}
            and isinstance(value["task_sha256"], str) and len(value["task_sha256"]) == 64
            and value["capability"] in CAPABILITIES and _int(value["horizon_runs"], *HORIZON)
            and all(_int(value[name], 0, 1000) for name in PERMILLE) and all(_spread(value[n]) for n in SPREADS)
            and _int(value["evidence_n"], 0, MAX_ITEMS) and _int(value["unknowns_n"], 0, MAX_ITEMS))


def _rows(ledger: bytes | None) -> list[tuple[int, dict[str, Any] | None]]:
    """Each line of a ledger as (its number, the row or None when it is not one)."""
    out: list[tuple[int, dict[str, Any] | None]] = []
    for number, line in enumerate((ledger or b"").split(b"\n"), start=1):
        if not line:
            continue
        try:
            out.append((number, ledgercheck._row(line)))
        except ledgercheck._NotARow:
            out.append((number, None))
    return out


def listed(head: bytes | None, base: bytes | None) -> list[dict[str, Any]]:
    """The forecast rows of the head's ledger that the last accepted commit's ledger (``base``) does not hold, by
    ``row_hash``, in line order: each ``{row_hash, line, forecast}`` or ``{row_hash, line, invalid}``. A row whose
    declared ``row_hash`` is not its own has no hash to bind by and is left out (the ledger's check names it)."""
    accepted = {row.get("row_hash") for _n, row in _rows(base) if row is not None}
    found: list[dict[str, Any]] = []
    for number, row in _rows(head):
        if row is None or row.get("part") != "founder" or row.get("kind") != KIND:
            continue
        declared, prev = row.get("row_hash"), row.get("prev_hash")
        if not (isinstance(prev, str) and ledgercheck.HEX64_RE.match(prev)) or canon.row_hash(row) != declared:
            continue
        if declared in accepted:
            continue
        payload = row.get("payload")
        forecast = payload.get(KIND) if isinstance(payload, dict) else None
        rule = "payload" if not isinstance(payload, dict) else broken_rule(forecast)
        entry: dict[str, Any] = {"row_hash": declared, "line": number}
        if rule is None:
            entry[KIND] = projection(forecast)
        else:
            entry["invalid"] = rule
        found.append(entry)
    return found[-MAX_LISTED:]
