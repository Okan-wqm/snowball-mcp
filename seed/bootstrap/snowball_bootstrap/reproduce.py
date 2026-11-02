"""Run reproducers in the same sandbox as the tests (`tohum/29`, "Rakibin kuralları").

A refutation counts only when its reproducer, run by the referee, shows the symptom the rival named (exit
code, a substring of stdout, a substring of stderr) because of the defect. Three rules make a showing
symptom ``reproduced`` (E06, E09):

- a run that timed out never shows anything;
- a reproducer whose symptom shows is run again on an empty control tree (same image, prelude and working
  directory, no lock file to install); if it shows there too it is ``tautological`` and does not count: a
  missing module or a bare ``true`` would show it whatever the code did;
- what the command printed is kept, as secret-scanned tails, so the rival and the operator can see it.

The referee sees whether a text shows, never whether it is the defect's or what correct code prints: that
polarity is the rival's to name, by both sides of the reproducer (`rival.SYMPTOM`, `rival.CORRECT`, E260).
Whether the head also shows what the reproducer calls correct is kept beside ``reproduced`` as
``contradicted``; what it means on which head is `decide`'s rule.

The rival's own reproducers (``run_reproducers``) and those the signed state keeps (``run_state_reproducers``:
proven defects and open claims, E07 E08) run the same way.
"""

from __future__ import annotations

import hashlib
from typing import Any

from . import canon, secretscan
from .container import Runner, RunResult
from .rival import MAX_REPRODUCERS, SYMPTOM, TARGET_IMAGE, side_holds

DOCKER_ERROR = 125  # `docker run` exits with this when docker itself failed, before the command ran
TAIL_CHARS = 2000
WITHHELD = "(withheld: the output matches a secret pattern)"


def reproducer_key(rep: dict[str, Any]) -> str:
    """What makes two reproducers the same defect: the command and its symptom, not the claim's wording (E08), nor
    how the rival words what correct code prints (E260), so every key signed before E260 is still the key."""
    doc = {"cmd": rep["cmd"], **{k: rep.get(k) for k in SYMPTOM}}
    if rep.get("image") == TARGET_IMAGE:  # the same command in another image is another defect; the key of every
        doc["image"] = TARGET_IMAGE  # Python reproducer stays what it was (E513)
    return hashlib.sha256(canon.canonical(doc)).hexdigest()[:16]


def _tail(data: bytes) -> str:
    tail = data.decode("utf-8", "replace")[-TAIL_CHARS:]
    return WITHHELD if secretscan.scan(tail) else tail


def _holds(rep: dict[str, Any], side: str, res: RunResult) -> bool:
    """One side of the reproducer (``expect``: the symptom, ``correct``: what correct code shows) holds in what the
    command printed (`rival.side_holds`), and the run finished on its own."""
    if res.timed_out:  # whatever a killed run printed is no answer
        return False
    return side_holds(rep, side, {"exit": res.exit_code, "stdout_contains": res.stdout.decode("utf-8", "replace"),
                                  "stderr_contains": res.stderr.decode("utf-8", "replace")})


def _not_run(rep: dict[str, Any], fault: bool) -> dict[str, Any]:
    """A target reproducer where no target image is set (E513): it shows nothing. For the rival's own reproducer that
    is all (the protocol told it which images the review offers); for one the signed state keeps it is a runner
    fault, so a proven defect is never read as fixed because its image went missing."""
    empty = hashlib.sha256(b"").hexdigest()
    return {"key": reproducer_key(rep), "reproduced": False, "shown": False, "contradicted": False,
            "tautological": None, "runner_fault": fault, "exit": DOCKER_ERROR if fault else None, "timed_out": False,
            "stdout_sha256": empty, "stderr_sha256": empty, "stdout_tail": "",
            "stderr_tail": "not run: this review offers no target image"}


def run_one(runner: Runner, control: Runner, rep: dict[str, Any], timeout_s: int, *,
            target: tuple[Runner, Runner] | None = None, missing_is_fault: bool = False) -> dict[str, Any]:
    """``target``: the (head, control) runners of the target image, where the referee has one (E513)."""
    if rep.get("image") == TARGET_IMAGE:
        if target is None:
            return _not_run(rep, missing_is_fault)
        runner, control = target
    res = runner.run(rep["cmd"], timeout_s=timeout_s)
    shown = _holds(rep, "expect", res)
    fault = res.exit_code == DOCKER_ERROR  # the sandbox failed: nothing was shown either way
    tautological = None
    if shown and not fault:  # only a symptom that showed needs the empty tree to tell it from the defect
        empty = control.run(rep["cmd"], timeout_s=timeout_s)
        fault = empty.exit_code == DOCKER_ERROR
        tautological = _holds(rep, "expect", empty)
    return {
        "key": reproducer_key(rep),
        "reproduced": shown and not fault and tautological is False,
        "shown": shown,
        "contradicted": _holds(rep, "correct", res),  # the head shows what the reproducer itself calls correct
        "tautological": tautological,
        "runner_fault": fault,
        "exit": res.exit_code,
        "timed_out": res.timed_out,
        "stdout_sha256": hashlib.sha256(res.stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(res.stderr).hexdigest(),
        "stdout_tail": _tail(res.stdout),
        "stderr_tail": _tail(res.stderr),
    }


def run_reproducers(runner: Runner, attempts: list[dict], timeout_s: int, *, control: Runner,
                    target: tuple[Runner, Runner] | None = None) -> list[dict]:
    """The rival's reproducers of this run (at most five, E05)."""
    with_repro = [(i, a) for i, a in enumerate(attempts) if "reproducer" in a][:MAX_REPRODUCERS]
    return [dict(run_one(runner, control, attempt["reproducer"], timeout_s, target=target), attempt_index=index)
            for index, attempt in with_repro]


def run_state_reproducers(runner: Runner, entries: list[dict], timeout_s: int, *, control: Runner,
                          target: tuple[Runner, Runner] | None = None) -> list[dict]:
    """The signed state's reproducers: ``{key, source, reproducer}``, source ``refutation`` or ``claim``."""
    return [dict(run_one(runner, control, entry["reproducer"], timeout_s, target=target, missing_is_fault=True),
                 key=entry["key"], source=entry["source"])
            for entry in entries]
