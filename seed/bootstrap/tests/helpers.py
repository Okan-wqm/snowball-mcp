"""Test doubles for the outside world: the container runtime, the model provider and git remotes."""

from __future__ import annotations

import json
import math
import shlex
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from snowball_bootstrap.canon import row_hash
from snowball_bootstrap.container import RunResult

# ---------------------------------------------------------------- reference founder implementation


def _beta_cdf(a: float, b: float, x: float, steps: int = 4000) -> float:
    """Regularized incomplete beta by Simpson's rule in log space (reference only)."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    lb = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)

    def f(t: float) -> float:
        if t <= 0 or t >= 1:
            return 0.0
        return math.exp((a - 1) * math.log(t) + (b - 1) * math.log(1 - t) - lb)

    h = x / steps
    s = f(0) + f(x)
    for i in range(1, steps):
        s += (4 if i % 2 else 2) * f(i * h)
    return s * h / 3


def cp_lower(x: float, n: int, alpha: float) -> float:
    if x <= 0:
        return 0.0
    if x >= n:
        return alpha ** (1 / n)
    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if _beta_cdf(x, n - x + 1, mid) > alpha:
            hi = mid
        else:
            lo = mid
    return lo


def mcnemar(b: int, c: int) -> float:
    m = b + c
    return sum(math.comb(m, k) for k in range(c, m + 1)) / 2 ** m


def score(findings: list[dict], cases: list[dict]) -> int:
    hits, used = 0, set()
    for case in cases:
        for i, f in enumerate(findings):
            if i in used:
                continue
            if (f.get("tool") == case.get("tool") and f.get("rule_id") == case.get("rule_id")
                    and any(ref["path"] == tp["path"] and any(h["start"] <= ref["line_start"] <= h["end"]
                                                              for h in tp["hunks"])
                            for ref in f["evidence_refs"] for tp in case["touched_paths"])):
                hits += 1
                used.add(i)
                break
    return hits


def verify_file(path: Path) -> dict[str, Any]:
    prev = "0" * 64
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row["prev_hash"] != prev or row_hash(row) != row["row_hash"]:
            return {"valid": False, "broken_row": row["row_id"]}
        prev = row["row_hash"]
    return {"valid": True}


@dataclass
class FakeRunner:
    """Emulates the container: answers the vector interface with a reference implementation.

    ``vec_dir`` stands in for the /vec mount. ``wrong`` names behaviours to break on purpose.
    ``commands`` maps other commands to (exit, stdout).
    """

    vec_dir: Path
    wrong: set[str] = field(default_factory=set)
    commands: dict[str, tuple[int, bytes]] = field(default_factory=dict)
    calls: list[tuple[str, str]] = field(default_factory=list)

    def run(self, cmd: str, *, cwd: str = ".", stdin: bytes = b"", timeout_s: int) -> RunResult:
        self.calls.append((cmd, cwd))
        if cmd in self.commands:
            code, out = self.commands[cmd]
            return RunResult(code, out, b"", 1)
        argv = shlex.split(cmd)

        def ok(value: dict) -> RunResult:
            return RunResult(0, (json.dumps(value) + "\n").encode(), b"", 1)

        if argv[:3] == ["python", "-m", "ledger.chain"]:
            if argv[3] == "hash":
                row = json.loads(stdin)
                if "chain_ignores_input" in self.wrong:
                    return ok({"row_hash": "3bae91580aca99362572e9f5f41b3e46c2bc0c29236f72e867faa5cd46ca603a"})
                return ok({"row_hash": row_hash(row)})
            if argv[3] == "verify":
                path = self.vec_dir / argv[4].removeprefix("/vec/")
                if "verify_always_valid" in self.wrong:
                    return ok({"valid": True})
                return ok(verify_file(path))
        if argv[:3] == ["python", "-m", "harness.stats"]:
            if argv[3] == "cp_lower":
                x, n, alpha = float(argv[4]), int(argv[5]), float(argv[6])
                lb = cp_lower(x, n, alpha)
                if "cp_wilson" in self.wrong:
                    lb = lb + 0.01
                return ok({"lb": f"{lb:.6f}"})
            if argv[3] == "mcnemar":
                return ok({"p": f"{mcnemar(int(argv[4]), int(argv[5])):.6f}"})
        if argv[:3] == ["python", "-m", "harness.score"]:
            findings = json.loads((self.vec_dir / argv[3].removeprefix("/vec/")).read_text())
            cases = json.loads((self.vec_dir / argv[4].removeprefix("/vec/")).read_text())
            hits = score(findings, cases)
            if "score_counts_twice" in self.wrong:
                hits = len(cases)
            return ok({"hits": hits})
        if cmd == "exit 0":
            return RunResult(0, b"", b"", 1)
        return RunResult(1, b"", b"unknown command", 1)


# ---------------------------------------------------------------- model provider double


@dataclass
class Block:
    type: str
    id: str = ""
    name: str = ""
    input: Any = None
    text: str = ""


@dataclass
class Usage:
    input_tokens: int = 1000
    output_tokens: int = 200
    cache_creation_input_tokens: int | None = 0
    cache_read_input_tokens: int | None = 0


@dataclass
class Response:
    content: list[Block]
    stop_reason: str
    model: str = "claude-sonnet-5-5"
    usage: Usage = field(default_factory=Usage)
    stop_details: Any = None


class FakeMessages:
    def __init__(self, script: list[Callable[[dict], Response]]):
        self.script = list(script)
        self.requests: list[dict] = []

    def create(self, **kwargs: Any) -> Response:
        self.requests.append(kwargs)
        if not self.script:
            raise RuntimeError("no scripted response left")
        return self.script.pop(0)(kwargs)


class FakeClient:
    def __init__(self, script: list[Callable[[dict], Response]]):
        self.messages = FakeMessages(script)


# ---------------------------------------------------------------- git helpers


def sh(cwd: Path, *argv: str) -> str:
    return subprocess.run(argv, cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def make_repo(path: Path, files: dict[str, str]) -> str:
    path.mkdir(parents=True, exist_ok=True)
    sh(path, "git", "init", "-q", "-b", "main")
    sh(path, "git", "config", "user.email", "t@example.invalid")
    sh(path, "git", "config", "user.name", "t")
    return commit(path, files, "seed")


def commit(path: Path, files: dict[str, str | None], message: str) -> str:
    for rel, content in files.items():
        target = path / rel
        if content is None:
            target.unlink()
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
    sh(path, "git", "add", "-A")
    sh(path, "git", "commit", "-q", "-m", message)
    return sh(path, "git", "rev-parse", "HEAD")
