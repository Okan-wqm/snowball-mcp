"""Operator-written inputs, validated strictly. Anything missing or malformed stops the run.

Files, all in the referee repository and written only by the operator (`tohum/25`):
- ``bootstrap.json``: what this bootstrap watches and how it runs.
- ``control.json``: the kill switch.
- ``policy.json``: the constitutional policy (only the keys this bootstrap reads are checked).
- ``setup/summary.json``: the setup summary (seed commit and seed tree hash).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
REPO_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9._-]{1,100}$")
IMAGE_RE = re.compile(r"^[a-z0-9./_-]+(?::[A-Za-z0-9._-]+)?@sha256:[0-9a-f]{64}$")
BRANCH_RE = re.compile(r"^[A-Za-z0-9._/-]{1,200}$")


class ConfigError(ValueError):
    """An operator file is missing, malformed, or says stop."""


def _load(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"missing {path}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(f"{path} is not valid JSON: {exc}") from exc


def _req(obj: Any, key: str, kind: type, where: str) -> Any:
    if not isinstance(obj, dict) or key not in obj:
        raise ConfigError(f"{where}: missing key {key!r}")
    value = obj[key]
    if kind is int and isinstance(value, bool):
        raise ConfigError(f"{where}.{key} must be an integer")
    if not isinstance(value, kind):
        raise ConfigError(f"{where}.{key} must be {kind.__name__}")
    return value


def _pos_int(obj: Any, key: str, where: str) -> int:
    value = _req(obj, key, int, where)
    if value <= 0:
        raise ConfigError(f"{where}.{key} must be positive")
    return value


@dataclass(frozen=True)
class Prices:
    input: int
    output: int
    cache_write: int
    cache_read: int


@dataclass(frozen=True)
class RivalConfig:
    model: str
    effort: str
    max_turns: int
    max_tokens: int
    per_run_cap_usd_micros: int
    prices: Prices


@dataclass(frozen=True)
class Limits:
    test_timeout_s: int
    reproducer_timeout_s: int
    max_prompt_chars: int
    max_tree_bytes: int


@dataclass(frozen=True)
class Bootstrap:
    brain_repo: str
    brain_branch: str
    image: str
    rival: RivalConfig
    limits: Limits

    @property
    def brain_owner(self) -> str:
        return self.brain_repo.split("/", 1)[0]

    @property
    def brain_name(self) -> str:
        return self.brain_repo.split("/", 1)[1]


def load_bootstrap(root: Path) -> Bootstrap:
    data = _load(root / "bootstrap.json")
    where = "bootstrap.json"
    repo = _req(data, "brain_repo", str, where)
    if not REPO_RE.match(repo):
        raise ConfigError(f"{where}.brain_repo must be owner/name")
    branch = _req(data, "brain_branch", str, where)
    if not BRANCH_RE.match(branch) or ".." in branch:
        raise ConfigError(f"{where}.brain_branch is not a plain branch name")
    image = _req(data, "image", str, where)
    if not IMAGE_RE.match(image):
        raise ConfigError(f"{where}.image must be pinned by digest (name@sha256:<64 hex>)")
    rival = _req(data, "rival", dict, where)
    rw = f"{where}.rival"
    model = _req(rival, "model", str, rw)
    effort = _req(rival, "effort", str, rw)
    if effort not in {"low", "medium", "high", "xhigh", "max"}:
        raise ConfigError(f"{rw}.effort is not a known effort level")
    prices = _req(rival, "price_micros_per_mtok", dict, rw)
    pw = f"{rw}.price_micros_per_mtok"
    limits = _req(data, "limits", dict, where)
    lw = f"{where}.limits"
    return Bootstrap(
        brain_repo=repo,
        brain_branch=branch,
        image=image,
        rival=RivalConfig(
            model=model,
            effort=effort,
            max_turns=_pos_int(rival, "max_turns", rw),
            max_tokens=_pos_int(rival, "max_tokens", rw),
            per_run_cap_usd_micros=_pos_int(rival, "per_run_cap_usd_micros", rw),
            prices=Prices(
                input=_pos_int(prices, "input", pw),
                output=_pos_int(prices, "output", pw),
                cache_write=_pos_int(prices, "cache_write", pw),
                cache_read=_pos_int(prices, "cache_read", pw),
            ),
        ),
        limits=Limits(
            test_timeout_s=_pos_int(limits, "test_timeout_s", lw),
            reproducer_timeout_s=_pos_int(limits, "reproducer_timeout_s", lw),
            max_prompt_chars=_pos_int(limits, "max_prompt_chars", lw),
            max_tree_bytes=_pos_int(limits, "max_tree_bytes", lw),
        ),
    )


def check_control(root: Path) -> None:
    """Fail closed unless the kill switch is explicitly off and the budget state is ok."""
    data = _load(root / "control.json")
    if data.get("kill_switch") is not False:
        raise ConfigError("control.json: kill switch is on or not explicitly false")
    if data.get("budget_state") != "ok":
        raise ConfigError("control.json: budget_state is not 'ok'")


@dataclass(frozen=True)
class Policy:
    monthly_cap_usd_micros: int
    stage0_rival_usd_micros: int
    rival_min_attempts: int


def load_policy(root: Path) -> Policy:
    data = _load(root / "policy.json")
    const = _req(data, "constitutional", dict, "policy.json")
    cw = "policy.json.constitutional"
    params = _req(const, "stage_params", dict, cw)
    budgets = _req(const, "stage_budgets", dict, cw)
    stage0 = _req(budgets, "asama_0", dict, f"{cw}.stage_budgets")
    return Policy(
        monthly_cap_usd_micros=_pos_int(const, "monthly_cap_usd", cw) * 1_000_000,
        stage0_rival_usd_micros=_pos_int(stage0, "rival_usd", f"{cw}.stage_budgets.asama_0") * 1_000_000,
        rival_min_attempts=_pos_int(params, "rival_min_attempts", f"{cw}.stage_params"),
    )


@dataclass(frozen=True)
class Summary:
    seed_commit: str
    seed_tree_sha256: str


def load_summary(root: Path) -> Summary:
    data = _load(root / "setup" / "summary.json")
    where = "setup/summary.json"
    seed_commit = _req(data, "seed_commit", str, where)
    if not SHA_RE.match(seed_commit):
        raise ConfigError(f"{where}.seed_commit must be a 40-character commit SHA")
    seed_tree = _req(data, "seed_tree_sha256", str, where)
    if not HEX64_RE.match(seed_tree):
        raise ConfigError(f"{where}.seed_tree_sha256 must be 64 hex characters")
    return Summary(seed_commit=seed_commit, seed_tree_sha256=seed_tree)
