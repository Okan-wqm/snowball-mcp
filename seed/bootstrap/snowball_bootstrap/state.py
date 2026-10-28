"""The bootstrap's memory between runs: the last signed result's ``state`` block.

There is no writable store in the referee repository (only the operator writes it), so state
travels in the signed ``bootstrap-state`` artifact of the previous run and is verified with
Sigstore before use. If none exists, the run starts from the setup summary and says so.
"""

from __future__ import annotations

import re
from typing import Any

from .config import ConfigError, Summary

SCHEMA = "snowball-bootstrap-state/1"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
MONTH_RE = re.compile(r"^\d{4}-\d{2}$")
KEYS = {"schema", "origin", "last_accepted_sha", "last_evaluated_sha", "frozen_specs", "rival_artifacts",
        "month", "month_spend_usd_micros", "stage_spend_usd_micros", "runs"}


def initial(summary: Summary, month: str) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "origin": "initial",
        "last_accepted_sha": summary.seed_commit,
        "last_evaluated_sha": None,
        "frozen_specs": {},
        "rival_artifacts": [],
        "month": month,
        "month_spend_usd_micros": 0,
        "stage_spend_usd_micros": 0,
        "runs": 0,
    }


def validate(state: Any) -> dict[str, Any]:
    if not isinstance(state, dict) or set(state) != KEYS or state.get("schema") != SCHEMA:
        raise ConfigError("previous state has an unexpected shape")
    if not SHA_RE.match(str(state["last_accepted_sha"])):
        raise ConfigError("previous state: bad last_accepted_sha")
    if state["last_evaluated_sha"] is not None and not SHA_RE.match(str(state["last_evaluated_sha"])):
        raise ConfigError("previous state: bad last_evaluated_sha")
    if not isinstance(state["frozen_specs"], dict) or not all(
            isinstance(k, str) and isinstance(v, str) and HEX64_RE.match(v) for k, v in state["frozen_specs"].items()):
        raise ConfigError("previous state: bad frozen_specs")
    if not isinstance(state["rival_artifacts"], list) or not all(
            isinstance(s, str) and SHA_RE.match(s) for s in state["rival_artifacts"]):
        raise ConfigError("previous state: bad rival_artifacts")
    if not MONTH_RE.match(str(state["month"])):
        raise ConfigError("previous state: bad month")
    for key in ("month_spend_usd_micros", "stage_spend_usd_micros", "runs"):
        if not isinstance(state[key], int) or isinstance(state[key], bool) or state[key] < 0:
            raise ConfigError(f"previous state: bad {key}")
    return state


def rollover(state: dict[str, Any], month: str) -> dict[str, Any]:
    new = dict(state)
    if new["month"] != month:
        new["month"] = month
        new["month_spend_usd_micros"] = 0
    new["origin"] = state["origin"]
    return new
