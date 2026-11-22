"""Run the Founder pilot on the operator's machine (register E32, E90, E91). Stdlib only.

One cycle:
  1. download the referee's last signed result (`bootstrap-state` artifact of the referee's main branch);
  2. rebuild <work>/vec from the `vectors/` of the referee repo's main (E244); if that fails, no session: stop;
  3. run one Founder session in the capsule (seed/founder/Dockerfile);
  4. if the brain moved, dispatch the referee (its schedule fires rarely and irregularly, E32) and wait for it;
  5. write the session's cost as a `kind: cost` founder row on the brain's main (`tohum/24a` 4), when that commit is
     memory alone to the referee; otherwise keep it in <work>/cost-pending.jsonl for a later cycle;
  6. append what happened to <work>/pilot-log.md (the brain's open reports and their age, split by the referee's own
     rule into the operator's debt and the Founder's unconfirmed ones, `26l`, E694; and the brain's `wip/` branches that
     hold the Founder's memory or have fallen behind the last accepted head, E592) and one metrics line that names what
     the cycle ran on (prompt, image, model, CLI, seed, rival configuration, target commit).

Everything lives in one folder, <work> (the operator deletes it to remove the pilot):
  <work>/snowball-founder.env   the Founder's two secrets; written by the operator, never read by this script
  <work>/aquaculture_platform   the target clone, mounted read-only
  <work>/referee/               the last referee result the Founder reads
  <work>/vec/                   the vectors' inputs, mounted read-only at /vec: cases.json (every data case's command,
                                stdin and fixtures) and the fixtures; no expected value is there. A vector that
                                contradicts its page stays red until the operator answers with a seed epoch.
  <work>/logs/                  session transcripts; each session's folder also holds previous-session.json,
                                targets.json, the targets' [{id, kind, base_sha, unit_candidates}] (seed-049, E571;
                                seed-050, E577), operating.json, policy.json's operating{} read for that session, and
                                policy.json, the referee repo's file byte for byte from that same read (seed-053, E588),
                                and loop-runs.jsonl, the referee repo's newest loop.yml runs, their jobs and summary
                                lines, read with the operator's login; what could not be read is null (`29y`, E596),
                                and lessons.json, the id and claim of the ledger's newest live `lesson` rows at the
                                head the session starts from, and how many were left out (`26g`, E610), and
                                mirror.json, the measurement mirror: facts only, from these records and the referee
                                tarball read for /vec (`mirror.py`; the owner's decision of 2026-11-19, E647)
  <work>/pilot-log.md           the operator's report
  <work>/STOP                   create this file to stop after the current step
  <work>/cost-pending.jsonl     cost rows not written yet: the brain held work the referee had not accepted
  <work>/reports-seen.json      when the launcher first saw each brain report (a report's age)
  <work>/launcher.lock          the running launcher's exclusive OS lock: one launcher at a time; the OS frees it when
                                the process ends, a crash or a reboot too (E505)
  <work>/RUNNING                the run in progress (JSON): its options, the cycles left, when it started and was last
                                updated; written after the preflight, removed when the run ends by STOP, two sessions
                                without a push, a timed-out session, no vector inputs, Ctrl+C or its last cycle. A
                                crash, a kill or a reboot leaves it, and `--resume` continues that run (E505). No
                                secret is in it

The operator's own `gh` login dispatches the referee and reads results; it never enters the capsule. It writes to the
brain only the cost rows, as the launcher's own identity, through git's `gh` credential helper.

Resume (E505): `--install-service` registers a Windows Scheduled Task for the current user (no admin) that runs
`launch.py --resume --work <work>` at logon and every 15 minutes; `--uninstall-service` removes it. `--resume` does
nothing while another launcher holds the lock, when there is no RUNNING, or when STOP exists (a deliberate stop is
never overridden: the run's RUNNING is then removed); else it waits for docker and gh to answer and runs the stored
options for the cycles left. An unjudged push is judged first, as at every start (E168). A start by hand replaces a
cut run.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import xml.sax.saxutils
import zipfile
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEED = HERE.parent
sys.path.insert(0, str(SEED / "bootstrap"))
from snowball_bootstrap import canon, config, gitio, ledgercheck, reportlife, secretscan  # noqa: E402  (the chain
# rule, the referee's git, its strict reading of targets[], its ledger check, its report counts and secret patterns)
from snowball_bootstrap.treehash import RESERVED_TOP  # noqa: E402  (what of the referee repo is not referee/)
from snowball_bootstrap.classify import (LEDGER_FILE, SEED_DIRS, is_founder_record,  # noqa: E402  (what is memory
                                         is_seed_path)  # and what is the operator's delivery to the referee)
from snowball_bootstrap.decide import counts_against_founder, is_brake_stop  # noqa: E402  (the referee's rule)
from snowball_bootstrap.exitchecks import fold, target_names, withheld  # noqa: E402  (the referee's folded names and
# its one rule for showing a text that may carry one, E290, E291)
from snowball_bootstrap.vectors import founder_inputs  # noqa: E402  (the referee's projection, not a copy: E244)


def _sibling(name: str, file: str):
    """A script beside this one, loaded by path: the launcher runs as a script and its tests load it by path."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, HERE / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# The capsule's own read-only ledger index (`ledger_index.py`, E506): the lesson index folds the ledger with its
# `unclosed` rule, the one the Founder's `unclosed --tag closes` answers by (`26g`, E610).
LEDGER_INDEX = _sibling("founder_ledger_index", "ledger_index.py")
MIRROR = _sibling("founder_mirror", "mirror.py")  # the measurement mirror's facts (E647)
IMAGE = "snowball-founder:pilot"
REFEREE_WORKFLOW = "bootstrap.yml"
STATE_ARTIFACT = "bootstrap-state"
VERDICT_LOOKBACK = 10  # results scanned for a head's own verdict: seed epochs and scheduled runs come between (E420)
REFEREE_VECTORS = "vectors"  # the referee repo's copy of seed/bootstrap/vectors (README, seed delivery step 3)
MAX_REFEREE_RETRIES = 2  # with the first run, as many as the referee's own retries (decide.RIVAL_SIDE_WARN)
BUILD_FILES = ("founder/Dockerfile", "founder/entrypoint.sh", "founder/prompt.md", "founder/brain_defs.py",
               "founder/ledger_index.py",
               "founder/git-hooks/commit-msg",
               "bootstrap/requirements/claude-cli/package.json", "bootstrap/requirements/claude-cli/package-lock.json")
LAUNCHER_NAME, LAUNCHER_EMAIL = "Snowball launcher", "launcher@snowball.invalid"  # its commits are not the Founder's
GH_CREDENTIAL = "credential.helper=!gh auth git-credential"  # the operator's login, never a token on a command line
COST_PENDING = "cost-pending.jsonl"
GIT_NETWORK_TIMEOUT_S = 300  # a clone, a blob fetch or a push of the cost row; past it the rows wait for a later cycle
GIT_LOCAL_TIMEOUT_S = 60
REPORTS_SEEN = "reports-seen.json"
RIVAL_CONFIG = ("prompt_sha256", "model_served", "effort", "cli_version")  # of the result's rival block
INTERVENTION = "intervention"  # a launcher start's metrics row (E313); no verdict kind is ever this word
PROMPT_LABEL = "snowball.prompt_sha256"  # the image's own record of the prompt bytes it was built with (E313)
CONTEXT_LABEL = "snowball.context_sha256"  # and of every build file's bytes (E506)
# The Founder's report rows the cycle log shows: kinds of the closed set (`26`). A missing capability is a seed_issue
# whose text starts missing_capability: (prompt.md), never a kind of its own (E158).
REPORT_KINDS = ("seed_issue", "blocked")
LOCK_FILE = "launcher.lock"  # E505: one launcher per work folder
RUNNING_FILE = "RUNNING"  # E505: the run in progress, for --resume
NOT_RERUN = ("help", "work", "cycles", "resume", "install_service", "uninstall_service")  # not stored in RUNNING
READY_CHECKS = (("docker", "info"), ("gh", "auth", "status"))  # what a resumed run needs before its preflight
READY_WAIT_S = 10 * 60  # past it the resume gives up; the task's next trigger tries again
TARGETS_NOTE = "targets.json"  # each session's targets, never their names (seed-049, E571; seed-050, E577)
OPERATING_NOTE = "operating.json"  # policy.json's operating{} alone, read for each session (seed-050, E577)
OPERATING_KEYS = ("unit_inputs_bytes", "deps_bytes", "worktree_bytes", "container_mem_bytes", "kos_wall_s",
                  "test_total_s", "output_bytes")  # `26c`'s seven, in its order
POLICY_NOTE = "policy.json"  # the referee repo's policy.json byte for byte, read for each session (seed-053, E588)
POLICY_NOTE_MAX = 256 * 1024  # a larger file is no policy of thresholds and brakes: no copy (`29v`)
# The live loop's newest runs on the referee repo, read for each session with the operator's login (`29y`; the owner's
# decision of 2026-11-15). Every bound below is the page's; the four tuples are every word the file's classes can say.
LOOP_NOTE = "loop-runs.jsonl"
LOOP_WORKFLOW = "loop.yml"
LOOP_RUNS_MAX, LOOP_JOBS_MAX = 3, 8
LOOP_SUMMARY_MAX = 16 * 1024  # a job's summary line, raw and again as written
LOOP_DEPTH_MAX = 32
LOOP_OUTPUT_LINES, LOOP_OUTPUT_LINE_MAX = 5, 300
LOOP_LOG_MAX = 8 * 1024 * 1024
LOOP_CALL_S, LOOP_BUDGET_S = 30, 90  # one attempt per call, never a retry; the next session reads again
LOOP_STATE = ("runs", "no_loop", "unavailable")
LOOP_WHY = ("timeout", "gh", "bad_reply", "launcher_error")
LOOP_SUMMARY_WHY = ("none", "unread", "not_run", "too_large", "too_deep", "duplicate_key", "non_finite",
                    "secret_shape")
LOOP_OUTPUT_WHY = ("unread", "secret_shape")
READY_RETRY_S = 30
# The index of the Founder's live lessons, written for each session (`26g`; the owner's decision of 2026-11-17, E610).
LESSONS_NOTE = "lessons.json"
LESSON_KIND = "lesson"  # `26`'s founder kind for a lesson (E609)
LESSON_CLOSING_TAG = "closes"  # a later row's `closes:<row_id>` ref retires a lesson (`26g`)
LESSONS_MAX = 100  # the newest live lessons listed; the older ones are counted in `left_out`
LESSON_CLAIM_MAX = 500  # characters of a claim in the index; a longer one is cut and says so
# The measurement mirror, written for each session (`mirror.py`; the owner's decision of 2026-11-19, E647).
MIRROR_NOTE = "mirror.json"
TASK_NAME = "Snowball Founder launcher"
TASK_EVERY = "PT15M"


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run(*args: str, check: bool = True, timeout: float | None = None, stdin: bytes | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(args, check=check, timeout=timeout, input=stdin, capture_output=True)


class Outage(RuntimeError):
    """The cycle cannot go on now and is tried again after a wait: it is not a reason to end the pilot (E245)."""


class GitHubUnavailable(Outage):
    """A read from GitHub still failed after the retries, or a dispatch failed: the network or GitHub is down (E245)."""


class NoVerdict(Outage):
    """The Founder's last push has no verdict yet: no session works blind on it (E168, E248)."""


GH_RETRY_DELAYS_S = (10, 20, 40, 60, 60)  # about three minutes before a read counts as an outage
GH_OUTAGE_WAIT_S = 300


def gh_read(*args: str, timeout: float = 120, delays: tuple[int, ...] = GH_RETRY_DELAYS_S) -> bytes:
    """Stdout of a read-only `gh` call, retried on a failure or a timeout: one dropped connection must not end
    the pilot (E245). Writes (`gh workflow run`) never come through here; repeating one is not harmless. ``delays=()``
    is one attempt, for a read whose failure is a recorded null and must not hold the session (E679)."""
    last = ""
    for delay in (*delays, None):
        try:
            proc = run("gh", *args, check=False, timeout=timeout)
            if proc.returncode == 0:
                return proc.stdout
            last = proc.stderr.decode(errors="replace").strip()[-300:]
        except subprocess.TimeoutExpired:
            last = "timed out"
        if delay is None:
            break
        time.sleep(delay)
    raise GitHubUnavailable(f"gh {' '.join(args[:2])}: {last}")


def gh_json(*args: str):
    return json.loads(gh_read(*args) or b"null")


def _json_or_none(line: str):
    """One JSON line, or None for a blank or broken one (a record file cut by a power loss must not stop the pilot)."""
    try:
        return json.loads(line)  # a blank line is a ValueError too
    except ValueError:
        return None


def say(msg: str) -> None:
    print(f"[{now()}] {msg}", flush=True)


def reason_owner(reason: dict) -> str:
    """Whose move a rejection reason asks for, by the referee's own rule (one source of truth): the measure of
    whether every rejection the Founder sees is one it can act on (E166, E167)."""
    item = {"kind": str(reason.get("kind", "")), "ref": str(reason.get("ref") or "")}
    if counts_against_founder(item):
        return "founder"
    if is_brake_stop(item):  # the operator's brake, whether pull or the rival's call met it (E550)
        return "referee"
    return "rival" if item["kind"] in ("rival_unresolved", "rival_missing") else "referee"


LIMIT_RESET_RE = re.compile(r"resets\s+(\d{1,2})(?::(\d{2}))?\s*([ap]m)\s*\(UTC\)", re.IGNORECASE)
LIMIT_FALLBACK_S = 30 * 60
LIMIT_MAX_WAIT_S = 6 * 3600


BRAKES = ("error_max_turns", "error_max_budget_usd")  # the CLI's closing subtypes for a turn or budget brake


def usage_limited(sess: dict) -> bool:
    """Whether the account's usage limit ended the session (the CLI's closing result: api_error_status 429,
    api_error usage_limit_reached): the one predicate the wait and the next session's note read (E243, E568)."""
    return sess.get("api_error") == "usage_limit_reached" or sess.get("api_error_status") == 429


def session_end(sess: dict) -> str:
    """How a session ended, as the next session reads it (E360, E568): ``usage_limit`` (the account's limit, never the
    Founder's doing), ``timeout`` (the wall-clock limit, exit -1), ``brake`` (the turn or budget brake), ``exit``
    (exit 0) or ``error`` (any other exit). A session record or its metrics row; the limit is named first because a
    cut session also exits non-zero."""
    if usage_limited(sess):
        return "usage_limit"
    code = sess.get("session_exit", sess.get("exit"))
    if code == -1:
        return "timeout"
    if sess.get("subtype") in BRAKES:
        return "brake"
    return "exit" if code == 0 else "error"


def usage_limit_wait(sess: dict, at: datetime) -> int | None:
    """Seconds to wait when the session could not work because the account's usage limit was reached
    (`usage_limited`), else None. Such a session is an outage, not a Founder that chose not to push (E243): the wait
    runs to the reset the CLI names, plus two minutes."""
    if not usage_limited(sess):
        return None
    m = LIMIT_RESET_RE.search(str(sess.get("final") or ""))
    if not m:
        return LIMIT_FALLBACK_S
    hour = int(m.group(1)) % 12 + (12 if m.group(3).lower() == "pm" else 0)
    reset = at.replace(hour=hour, minute=int(m.group(2) or 0), second=0, microsecond=0)
    wait = (reset - at).total_seconds()
    if wait <= 0:
        wait += 24 * 3600
    return int(min(wait + 120, LIMIT_MAX_WAIT_S))


def prompt_sha256() -> str:
    """The checkout's prompt as `write_build_context` would copy it (LF): what a build now would put in the image. The
    prompt a running image holds is its build's label (`Pilot.image_prompt`); with --no-build the two can differ."""
    return hashlib.sha256((SEED / "founder" / "prompt.md").read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def context_sha256(root: Path | None = None) -> str:
    """One hash of every file the image is built from (`BUILD_FILES`), with LF line ends as `write_build_context` copies
    them: sha256 over the sorted lines `<path>\\0<sha256 of its bytes>\\n`. Of the checkout by default, of a build
    context when `root` names one; the two agree when the context was copied from this checkout (E506)."""
    base = SEED if root is None else root
    digests = {rel: hashlib.sha256((base / rel).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
               for rel in BUILD_FILES}
    return hashlib.sha256("".join(sorted(f"{rel}\0{digest}\n" for rel, digest in digests.items())).encode()).hexdigest()


TOKEN_FIELDS = (("in", "input_tokens"), ("out", "output_tokens"), ("cache_read", "cache_read_input_tokens"),
                ("cache_write", "cache_creation_input_tokens"))  # the CLI's closing usage, named as the row names them


def _count(value) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def cost_summary(fact: dict) -> str:
    """A session's bare facts, no interpretation: what the CLI and the launcher saw (`tohum/24a` 4): the exit, minutes,
    turns, USD, the model the CLI was served and every model the session's calls used, and the CLI's token totals
    (input, output, read from and written to the provider's cache). A fact the CLI did not report reads unknown."""
    turns = _count(fact.get("turns"))
    cost = fact.get("cost_usd")
    micros = round(cost * 1_000_000) if isinstance(cost, (int, float)) and not isinstance(cost, bool) else None
    tokens = fact.get("tokens") if isinstance(fact.get("tokens"), dict) else {}
    models = [m for m in fact.get("models") or [] if isinstance(m, str)]
    counts = " ".join(f"{name} {'unknown' if _count(tokens.get(name)) is None else tokens[name]}"
                      for name, _key in TOKEN_FIELDS)
    return (f"session {fact['stamp']}: exit {fact.get('exit')}, {fact.get('minutes')} min, "
            f"turns {'unknown' if turns is None else turns}, "
            f"cost_usd_micros {'unknown' if micros is None else micros}, CLI result {fact.get('subtype') or 'none'}, "
            f"model {fact.get('model_served') or 'unknown'}, models {'+'.join(sorted(models)) or 'unknown'}, "
            f"tokens {counts}")


def cost_line(ledger: bytes, fact: dict, ts: str) -> bytes:
    """One `kind: cost` founder row appended to the ledger's bytes, chained by `tohum/26`'s rule (the seed's own
    `canon.row_hash`, ``prev_hash`` the last row's). ValueError when the ledger cannot take it as the referee checks a
    pushed row (`ledgercheck`): a row the referee would hold against the Founder is never written for it."""
    if ledger and not ledger.endswith(b"\n"):
        raise ValueError("the ledger's last row has no final newline")
    lines = ledger.splitlines()
    try:
        prev = json.loads(lines[-1])["row_hash"] if lines else ledgercheck.ZERO
    except (ValueError, KeyError, TypeError) as exc:
        raise ValueError(f"the ledger's last row gives no row_hash ({type(exc).__name__})") from None
    row = {"row_id": f"f{len(lines) + 1}", "ts": ts, "part": "founder", "kind": "cost",
           "payload": {"summary": cost_summary(fact),
                       "refs": [f"logs/{fact['stamp']}/session-{fact['stamp']}.jsonl"]},
           "derivation": "tool", "trust": "observed", "snapshot_id": fact["head"], "evidence_refs": [],
           "prev_hash": prev}
    row["row_hash"] = canon.row_hash(row)
    line = (json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
    problems = ledgercheck.check(ledger + line, ledger, whole=False)
    if problems:
        raise ValueError("the row would not pass the referee's ledger check: " + ", ".join(problems))
    return line


def push_cost_rows(remote: str, facts: list[dict], last_accepted: str | None, ts: str, epoch: str | None = None,
                   credential: bool = True) -> str:
    """Append one cost row per fact to the brain's ledger on `main` and push it as the launcher, only when every path the
    head changed since the referee's last accepted commit is the Founder's memory (`classify.is_founder_record`) or, while
    the head's seed is the last epoch commit's, the operator's delivery (`epoch`; `cli._pull_classify` reads it so): then
    the referee reads the commit as memory alone (`none`: no tests, no rival, a `noop`). On a head that carries work the
    referee has not accepted, the commit would make it judge that work again and count its rejection twice: nothing is
    written. Returns the new head, or "deferred: <why>".

    Every git call has a limit (a stalled clone or push must not hang the loop) and a session's row is written once: a
    push that timed out after it reached GitHub leaves the facts pending, and the next attempt finds their rows there."""
    config = ("-c", GH_CREDENTIAL) if credential else ()
    if not last_accepted:
        return "deferred: the referee has no accepted commit"
    with tempfile.TemporaryDirectory(prefix="snowball-cost-") as tmp:
        clone = Path(tmp) / "brain"
        gitio.git(Path(tmp), *config, "clone", "--quiet", "--filter=blob:none", "--branch", "main", remote, str(clone),
                  timeout=GIT_NETWORK_TIMEOUT_S)
        head = gitio.git(clone, "rev-parse", "HEAD", timeout=GIT_LOCAL_TIMEOUT_S).decode().strip()
        try:
            work = work_since(clone, last_accepted, head, epoch)
        except gitio.GitError:
            return "deferred: the last accepted commit is not on main"
        if work:
            return f"deferred: {len(work)} path(s) changed since the last accepted {last_accepted[:7]}"
        ledger_path = clone / LEDGER_FILE
        ledger = ledger_path.read_bytes() if ledger_path.is_file() else b""
        written = cost_stamps(ledger)
        todo = [fact for fact in facts if fact["stamp"] not in written]
        if not todo:
            return head
        for fact in todo:
            ledger += cost_line(ledger, fact, ts)
        ledger_path.write_bytes(ledger)
        who = ("-c", f"user.name={LAUNCHER_NAME}", "-c", f"user.email={LAUNCHER_EMAIL}")
        gitio.git(clone, "add", LEDGER_FILE, timeout=GIT_LOCAL_TIMEOUT_S)
        gitio.git(clone, *who, "commit", "--quiet", "-m", f"Launcher: {len(todo)} cost row(s) (tohum/24a 4)",
                  timeout=GIT_LOCAL_TIMEOUT_S)
        gitio.git(clone, *config, "push", "--quiet", "origin", "HEAD:main", timeout=GIT_NETWORK_TIMEOUT_S)
        return gitio.git(clone, "rev-parse", "HEAD", timeout=GIT_LOCAL_TIMEOUT_S).decode().strip()


def work_since(clone: Path, last_accepted: str, head: str, epoch: str | None) -> list[str]:
    """The paths changed from the referee's last accepted commit to head that are neither the Founder's memory
    (`classify.is_founder_record`) nor, while head's seed is the last epoch commit's, the operator's delivery: what the
    referee would judge at head (`cli._pull_classify` reads them so). None of them: it reads head as memory alone, a
    `noop`. GitError when last_accepted is not in the clone."""
    if head == last_accepted:
        return []
    # The blob-less clone fetches what the diff reads, so these are network calls too.
    changed = gitio.git(clone, "diff", "--name-only", "--no-renames", last_accepted, head,
                        timeout=GIT_NETWORK_TIMEOUT_S).decode()
    delivered = bool(epoch) and gitio.same_under(clone, epoch, head, SEED_DIRS, timeout=GIT_NETWORK_TIMEOUT_S)
    return [p for p in changed.splitlines() if p and not is_founder_record(p) and not (delivered and is_seed_path(p))]


def memory_alone(remote: str, last_accepted: str | None, evaluated: str | None, head: str, epoch: str | None,
                 credential: bool = True) -> bool:
    """Whether head adds only the Founder's memory to what the referee last evaluated, and the referee would read it as
    memory alone: True only when main is still head, ``evaluated`` (the newest result's own, evaluated head) and the last
    accepted commit are its ancestors, nothing from ``evaluated`` to head but Founder records changed (so a delivery or
    any work there is judged first: a seed epoch gets its `seed_update` result) and nothing since the last accepted
    commit is work (`work_since`). Unknown (a git failure or timeout, main moved on) is False: head is judged first."""
    if not last_accepted or not evaluated:
        return False
    config = ("-c", GH_CREDENTIAL) if credential else ()
    try:
        with tempfile.TemporaryDirectory(prefix="snowball-memory-") as tmp:
            clone = Path(tmp) / "brain"
            gitio.git(Path(tmp), *config, "clone", "--quiet", "--filter=blob:none", "--branch", "main", remote,
                      str(clone), timeout=GIT_NETWORK_TIMEOUT_S)
            if gitio.git(clone, "rev-parse", "HEAD", timeout=GIT_LOCAL_TIMEOUT_S).decode().strip() != head:
                return False
            if not (gitio.is_ancestor(clone, evaluated, head) and gitio.is_ancestor(clone, last_accepted, head)):
                return False
            since = gitio.git(clone, "diff", "--name-only", "--no-renames", evaluated, head,
                              timeout=GIT_NETWORK_TIMEOUT_S).decode().splitlines()
            if any(p and not is_founder_record(p) for p in since):
                return False
            return not work_since(clone, last_accepted, head, epoch)
    except (gitio.GitError, OSError):
        return False


def cost_stamps(ledger: bytes) -> set[str]:
    """The sessions the ledger already has a launcher cost row for, by the transcript each one names (`cost_line`)."""
    found = set()
    for line in ledger.splitlines():
        try:
            row = json.loads(line)
            refs = row["payload"]["refs"] if row.get("kind") == "cost" and row.get("part") == "founder" else []
        except (ValueError, KeyError, TypeError, AttributeError):
            continue
        for ref in refs if isinstance(refs, list) else []:
            m = re.fullmatch(r"logs/([0-9]{8}T[0-9]{6}Z)/session-\1\.jsonl", str(ref))
            if m:
                found.add(m.group(1))
    return found


def report_ages(reports: list[dict], seen: dict[str, str], ts: str) -> dict[str, int]:
    """Every report's hours since the launcher first saw it, by file name (``seen`` is updated): a report carries no
    time of its own, and the ledger's and commits' times are written in the capsule (E316)."""
    now_dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
    out = {}
    for r in reports:
        rid = str(r.get("stem"))
        first = seen.setdefault(rid, ts)
        out[rid] = int((now_dt - datetime.strptime(first, "%Y-%m-%dT%H:%M:%SZ")).total_seconds() // 3600)
    return out


def aged(rows: list[dict], ages: dict[str, int]) -> list[tuple[str, int]]:
    """The rows as ``(file name, age in hours)``, oldest first."""
    return sorted(((str(r.get("stem")), ages.get(str(r.get("stem")), 0)) for r in rows), key=lambda i: (-i[1], i[0]))


def lesson_index(data: bytes, commit: str) -> dict:
    """`/work/logs/lessons.json` from the ledger's bytes at the session's brain head (`26g`, E610): every live `lesson`
    row's id and claim, the newest LESSONS_MAX of them in ledger order, and how many were left out. A lesson is live
    when no later row names it by `closes:<row_id>` (the capsule index's own `unclosed` fold, not a copy of its rule)
    and no later row's `supersedes` holds its `row_hash` (`13`). Only reads: no re-check is run, nothing is ranked,
    and the chain is not judged here (the referee's and the Founder's own check)."""
    li = LEDGER_INDEX
    ledger = li.Ledger(LEDGER_FILE, data)
    every = [line for line, row in ledger.rows if row.get("kind") == LESSON_KIND]
    superseding = ledger.index("supersedes")
    live = []
    for line, _item in li.unclosed(ledger, LESSON_CLOSING_TAG, [LESSON_KIND], False):
        row = ledger.by_line[line]
        named = superseding.get(row["row_hash"], ()) if isinstance(row.get("row_hash"), str) else ()
        if not any(at > line for at, _where in named):
            live.append((line, row))
    shown = live[-LESSONS_MAX:]
    rows = []
    for line, row in shown:
        claim = li.summary(row)
        rows.append({"row_id": row["row_id"], "line": line,
                     "claim": claim[:LESSON_CLAIM_MAX] if claim is not None else None,
                     "claim_cut": claim is not None and len(claim) > LESSON_CLAIM_MAX})
    return {"ledger": {"commit": commit, "bytes": ledger.size, "sha256": ledger.sha256, "rows": len(ledger.rows),
                       "unreadable": len(ledger.unreadable)},
            "lessons": len(every), "live": len(live), "shown": len(shown), "left_out": len(live) - len(shown),
            "rows": rows}


def target_rows(summary: dict) -> tuple:
    """`setup/summary.json` ``targets[]`` read by the referee's own rule (`config.target`), so a row the referee
    refuses is refused here too (ValueError); () when there is no target yet."""
    rows = summary.get("targets")
    if rows is None:
        return ()
    if not isinstance(rows, list):
        raise ValueError("setup/summary.json targets must be a list (`26c`)")
    try:
        return tuple(config.target(row, f"setup/summary.json targets[{i}]") for i, row in enumerate(rows))
    except config.ConfigError as exc:
        raise ValueError(str(exc)) from exc


def target_ids(summary: dict) -> list[dict]:
    """``[{id, kind, base_sha, unit_candidates}]`` of `setup/summary.json` ``targets[]``, in its order: what a session
    needs to name a target's folder (`24a`, seed-049, E571) and to propose its unit against the row the referee judges
    it by (seed-050, E577), never a target's repo, excluded paths or names (E290). The rows are read by the referee's
    own rule (`config.target`), so a row the referee refuses is refused here too; an id or a unit candidate that holds
    a target's name once folded (`exitchecks.fold`) would carry the name to the session, so it stops the start too,
    named by its field and index only (E290). ``base_sha`` is not folded: the referee's rule already holds it to 40
    hex digits or null, which carry no text. No ``targets[]`` is no target yet: an empty list."""
    targets = target_rows(summary)
    names = target_names(targets)
    for i, t in enumerate(targets):
        if any(name in fold(t.id) for _t, _j, name in names):
            raise ValueError(f"setup/summary.json targets[{i}].id holds a target's name (E290): it would reach the "
                             "session in targets.json")
        for k, path in enumerate(t.unit_candidates):
            if any(name in fold(path) for _t, _j, name in names):
                raise ValueError(f"setup/summary.json targets[{i}].unit_candidates[{k}] holds a target's name (E290): "
                                 "it would reach the session in targets.json")
    return [{"id": t.id, "kind": t.kind, "base_sha": t.base_sha, "unit_candidates": list(t.unit_candidates)}
            for t in targets]


def _number(value) -> bool:
    """A JSON number: an int of any size (``math.isfinite`` overflows on one past a float's range) or a finite float;
    a bool is not one."""
    if isinstance(value, bool):
        return False
    return isinstance(value, int) or (isinstance(value, float) and math.isfinite(value))


def operating_values(policy) -> dict:
    """``{"operating": {...}}`` of `policy.json`'s content, the shape `29g`'s `unit_verify check` takes, or ``{}``
    when it has no ``operating`` (the operator wrote none; `26c`'s missing field fails closed): seed-050, E577. Only
    `26c`'s seven keys pass, each exactly ``{value, band: [min, max]}`` of finite numbers, rebuilt from those numbers:
    any other key, field or value is operator text that would reach the session (E290), so it raises ValueError
    naming a known key or the position of an unknown one, never its text. The numbers are the operator's (`18a`);
    their bands are not judged here."""
    if not isinstance(policy, dict):
        raise ValueError("policy.json is not a JSON object")
    if "operating" not in policy:
        return {}
    found = policy["operating"]
    if not isinstance(found, dict):
        raise ValueError("policy.json operating is not an object (`26c`)")
    shown = {}
    for n, (key, entry) in enumerate(found.items()):
        if key not in OPERATING_KEYS:
            raise ValueError(f"policy.json operating's key number {n + 1} is not one of `26c`'s seven")
        band = entry.get("band") if isinstance(entry, dict) else None
        if not (isinstance(entry, dict) and set(entry) == {"value", "band"} and _number(entry["value"])
                and isinstance(band, list) and len(band) == 2 and all(_number(b) for b in band)):
            raise ValueError(f"policy.json operating.{key} is not {{value, band: [min, max]}} of numbers (`26c`)")
        shown[key] = {"value": entry["value"], "band": [band[0], band[1]]}
    return {"operating": shown}


def _no_repeated_key(pairs: list) -> dict:
    if len({key for key, _value in pairs}) != len(pairs):
        raise ValueError("duplicate_key")
    return dict(pairs)


def _non_finite(_constant: str):
    raise ValueError("non_finite")


def _finite(text: str) -> float:
    """A number literal out of the float range (1e999) parses to an infinity: no JSON value either."""
    value = float(text)
    if not math.isfinite(value):
        raise ValueError("non_finite")
    return value


def _texts(value):
    """Every key and string value of a parsed JSON document."""
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _texts(item)
    elif isinstance(value, list):
        for item in value:
            yield from _texts(item)
    elif isinstance(value, str):
        yield value


def strict_object(raw: bytes, limit: int, names: list) -> dict:
    """``raw`` as a strict JSON object of operator or loop text, or ValueError naming the class only, never the text:
    larger than ``limit`` bytes (`too_large`), other than UTF-8 (`not_utf8`), nesting past the parser (`too_deep`), a
    key twice at any depth (`duplicate_key`), `NaN` or an infinity (`non_finite`), no JSON (`not_json`), no object
    (`not_an_object`), a secret's shape (`secretscan`) in the text or in any key or string as parsed, so an escaped
    one (``\\u0041KIA...``) is caught too (`secret_shape`), or a target's folded name in a key or a string (``names``,
    `target_names`, E290: `target_name`). The policy copy (`29v`) and the loop's summary lines (`29y`) share it."""
    if len(raw) > limit:
        raise ValueError("too_large")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("not_utf8") from None
    try:
        doc = json.loads(text, object_pairs_hook=_no_repeated_key, parse_constant=_non_finite, parse_float=_finite)
    except RecursionError:
        raise ValueError("too_deep") from None
    except ValueError as exc:
        raise ValueError(str(exc) if str(exc) in ("duplicate_key", "non_finite") else "not_json") from None
    if not isinstance(doc, dict):
        raise ValueError("not_an_object")
    if secretscan.scan(text) or any(secretscan.scan(item) for item in _texts(doc)):
        raise ValueError("secret_shape")
    if any(name in fold(item) for item in _texts(doc) for _t, _j, name in names):
        raise ValueError("target_name")
    return doc


def policy_copy(raw: bytes, names: list) -> bytes:
    """What `/work/logs/policy.json` holds (`24a` 3, `29v`; seed-053, E588): the referee repo's `policy.json` byte for
    byte, so the Founder runs its own readers over the real file. The file holds thresholds and brakes, no secret, but
    it is operator text: one `strict_object` refuses, or larger than POLICY_NOTE_MAX, is not copied: ValueError naming
    the class only, never the text."""
    try:
        strict_object(raw, POLICY_NOTE_MAX, names)
    except ValueError as exc:
        raise ValueError(f"policy.json is not copied: {exc} (`29v`)") from None
    return raw


class LoopUnread(Exception):
    """A read of the loop's runs that did not answer (`29y`): its class alone (`timeout`, `gh`, `not_found`,
    `bad_reply`), never what GitHub printed."""


_LOG_STAMP = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z ")  # GitHub's stamp before each log line
_GH_WORD = re.compile(r"[a-z_]{1,40}")  # `event`, `status`, `conclusion`, a workflow's `state`
_GH_TIME = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ")


def _gh_word(value):
    return value if isinstance(value, str) and _GH_WORD.fullmatch(value) else None


def _gh_id(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def log_lines(body: bytes) -> list[str]:
    """A job's log as GitHub serves it, as its lines: without the byte order mark and each line's time stamp."""
    text = body.decode("utf-8", "replace").lstrip("\ufeff")
    return [line[m.end():] if (m := _LOG_STAMP.match(line)) else line for line in text.splitlines()]


def loop_shown(value, names: list, depth: int = 0):
    """``value`` as the loop file writes it (`29y`): every key and string holding a target's name hashed by the
    referee's one rule (`withheld`, E290), the rest as it is; nesting past LOOP_DEPTH_MAX levels is
    ValueError("too_deep")."""
    if isinstance(value, (dict, list)) and depth >= LOOP_DEPTH_MAX:
        raise ValueError("too_deep")
    if isinstance(value, dict):
        return {withheld(key, names): loop_shown(item, names, depth + 1) for key, item in value.items()}
    if isinstance(value, list):
        return [loop_shown(item, names, depth + 1) for item in value]
    return withheld(value, names) if isinstance(value, str) else value


def loop_line(row: dict) -> bytes:
    """One row of the loop file: a JSON object on one line, ASCII (an escape never fails to encode)."""
    return json.dumps(row, ensure_ascii=True, sort_keys=True, allow_nan=False).encode("ascii") + b"\n"


def job_summary(lines: list[str], job: str, names: list) -> tuple:
    """(summary, None) or (None, class) (`29y`): the last line of a job's log that is a JSON object whose `job` is the
    job's own name (`29p:34`; never a prefix: the keys are sorted), held to `strict_object` and LOOP_SUMMARY_MAX raw
    and again as written; `none` when the log holds no such line."""
    for line in reversed(lines):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            doc = json.loads(line)
        except (ValueError, RecursionError):
            continue
        if not isinstance(doc, dict) or doc.get("job") != job:
            continue
        try:
            shown = loop_shown(strict_object(line.encode("utf-8"), LOOP_SUMMARY_MAX, []), names)
        except ValueError as exc:
            return None, str(exc) if str(exc) in LOOP_SUMMARY_WHY else "unread"
        if len(loop_line(shown)) - 1 > LOOP_SUMMARY_MAX:  # as written, without its newline
            return None, "too_large"
        return shown, None
    return None, "none"


def job_output(lines: list[str], names: list) -> tuple:
    """(lines, None) or (None, class) of a failed job that printed no summary (`29y`): the failing step's own last
    LOOP_OUTPUT_LINES non-blank lines, between the step's `##[endgroup]` and the first `##[error]`; withheld whole on a
    secret's shape, then each line's target names hashed, then cut to LOOP_OUTPUT_LINE_MAX characters. `unread` when
    the log marks no failing step."""
    end = next((i for i, line in enumerate(lines) if line.startswith("##[error]")), None)
    start = None if end is None else max((i for i in range(end) if lines[i].startswith("##[endgroup]")), default=None)
    if start is None:
        return None, "unread"
    step = [line for line in lines[start + 1:end] if line.strip()][-LOOP_OUTPUT_LINES:]
    if any(secretscan.scan(line) for line in step) or secretscan.scan("\n".join(step)):
        return None, "secret_shape"
    return [withheld(line, names)[:LOOP_OUTPUT_LINE_MAX] for line in step], None


class LoopReads:
    """The loop file's reads of GitHub: `gh api <path>` alone, one attempt per call, LOOP_CALL_S each and LOOP_BUDGET_S
    for them all (`29y`); a call that does not answer is LoopUnread and is never repeated."""

    def __init__(self) -> None:
        self.deadline = time.monotonic() + LOOP_BUDGET_S

    def get(self, path: str) -> bytes:
        left = self.deadline - time.monotonic()
        if left <= 0:
            raise LoopUnread("timeout")
        try:
            proc = run("gh", "api", path, check=False, timeout=min(LOOP_CALL_S, left))
        except subprocess.TimeoutExpired:
            raise LoopUnread("timeout") from None
        if proc.returncode != 0:
            raise LoopUnread("not_found" if b"HTTP 404" in (proc.stderr or b"") else "gh")
        return proc.stdout

    def json(self, path: str):
        try:
            return json.loads(self.get(path))
        except (ValueError, RecursionError):
            raise LoopUnread("bad_reply") from None


WIP_PREFIX = "wip/"  # the Founder's side branches (prompt.md "İşi bitirerek ilerle"); memory lives on main (E592)
COMPARE_FILES_MAX = 300  # GitHub's compare lists at most this many files: a full list may be cut, so it is unknown


def is_memory(path: str) -> bool:
    """The Founder's memory as the owner named it (2026-11-14, `15` 9, E592): the ledger, the reports and the maps."""
    return is_founder_record(path) or path.startswith("docs/map/")


def wip_findings(branches: list[dict], compare: Callable[[str, str], dict], last_accepted: str | None) -> list[str]:
    """What the operator is told of the brain's `wip/` branches (`15` 9, E592), each ``{name, sha}``: a branch with
    commits `main` lacks that touch the Founder's memory (`wip_memory_off_main:<branch>`), and one with such commits
    that lacks the last accepted head (`wip_unmerged_behind:<branch>`: topological, no clock). A branch `main` holds
    whole is merged and says nothing. ``compare(base, head)`` is GitHub's compare of two commits; it raises, or the
    file list is cut, and the whole answer is unknown (ValueError): never "none"."""
    found = []
    for branch in sorted(branches, key=lambda b: b["name"]):
        mine = compare("main", branch["sha"])
        if not mine.get("ahead_by"):
            continue
        files = [str(f.get("filename", "")) for f in mine.get("files") or []]
        if len(files) >= COMPARE_FILES_MAX:
            raise ValueError(f"{WIP_PREFIX}{branch['name']}: the compare lists {len(files)} files, maybe not all")
        if any(is_memory(f) for f in files):
            found.append(f"wip_memory_off_main:{WIP_PREFIX}{branch['name']}")
        if last_accepted and compare(last_accepted, branch["sha"]).get("behind_by"):
            found.append(f"wip_unmerged_behind:{WIP_PREFIX}{branch['name']}")
    return found


def write_build_context(ctx: Path) -> None:
    """Copy exactly the files the image needs, with LF line ends: a Windows checkout may hand over CRLF, and a CR
    after the entrypoint's shebang makes the container fail before it starts (E152)."""
    for rel in BUILD_FILES:
        dest = ctx / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((SEED / rel).read_bytes().replace(b"\r\n", b"\n"))


def referee_vectors(blob: bytes, dest: Path) -> Path:
    """Unpack the `vectors/` of a referee repository tarball (`gh api .../tarball/main`) into dest, and nothing else of
    it: the referee's code never lands on the way to the capsule. Returns the unpacked `vectors/` folder."""
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r:*") as tar:
        members = [m for m in tar.getmembers() if m.name.split("/")[1:2] == [REFEREE_VECTORS]]
        tops = {m.name.split("/", 1)[0] for m in members}
        if len(tops) != 1:
            raise ValueError(f"the referee's tarball has {len(tops)} top folders with {REFEREE_VECTORS}/, not one")
        tar.extractall(dest, members=members, filter="data")
    return dest / tops.pop() / REFEREE_VECTORS


class Pilot:
    def __init__(self, work: Path, brain: str, referee: str, target: str) -> None:
        self.work, self.brain, self.referee = work, brain, referee
        self.target = work / target
        self.env_file = work / "snowball-founder.env"
        self.result_dir = work / "referee"
        self.inputs = work / "vec"  # the vectors' inputs, rebuilt before each session (E244)
        self.logs = work / "logs"
        self.report = work / "pilot-log.md"
        self.metrics = work / "pilot-metrics.jsonl"  # one machine-readable line per cycle (what docs/pilot-gunlugu.md counts)
        self.seed = ""  # the brain commit the referee's setup summary pins; the capsule cuts history there
        self.epoch: str | None = None  # the last seed epoch's brain commit (`26c` seed_epochs[]), if any
        self.targets: list[dict] = []  # `target_ids` of the summary, each session's targets.json (E571, E577)
        self.withheld: list = []  # the targets' folded names (`target_names`), kept out of policy.json's copy (E588)
        self.brain_remote = f"https://github.com/{brain}.git"
        self.prompt_sha256: str | None = None  # what this launcher start built the capsule with (E313)
        self.context_sha256: str | None = None  # and every build file the image holds (E506)
        self.image_id: str | None = None
        self._ledger_read: tuple[str, bytes] | None = None  # the last ledger read, by commit (`ledger_bytes`)
        self.referee_facts: dict | None = None  # what the mirror reads of this cycle's referee tarball (E647)

    # ---- checks -------------------------------------------------------------------------------------------
    def stopped(self) -> bool:
        return (self.work / "STOP").exists()

    def preflight(self) -> None:
        problems = []
        if not self.env_file.is_file() or self.env_file.stat().st_size < 40:
            problems.append(f"{self.env_file} is missing or empty")
        if not self.target.is_dir():
            problems.append(f"target clone {self.target} is missing")
        if run("docker", "info", check=False).returncode != 0:
            problems.append("docker is not running")
        if run("gh", "auth", "status", check=False).returncode != 0:
            problems.append("gh is not logged in")
        else:
            self.seed = self.seed_commit()
            self.epoch = self.last_epoch()
            if not re.fullmatch(r"[0-9a-f]{40}", self.seed):
                problems.append(f"{self.referee} setup/summary.json has no seed_commit")
            try:
                summary = self.summary()
                self.targets = target_ids(summary)
                self.withheld = target_names(target_rows(summary))
            except ValueError as exc:  # a summary the referee refuses, or an id that would carry a name (E290)
                problems.append(f"{self.referee} {exc}")
        if problems:
            sys.exit("preflight failed:\n  " + "\n  ".join(problems))
        self.result_dir.mkdir(exist_ok=True)
        self.logs.mkdir(exist_ok=True)

    def summary(self) -> dict:
        raw = run("gh", "api", "-H", "Accept: application/vnd.github.raw",
                  f"repos/{self.referee}/contents/setup/summary.json", check=False).stdout
        try:
            data = json.loads(raw)
        except ValueError:
            return {}
        return data if isinstance(data, dict) else {}

    def policy_raw(self) -> bytes:
        """The referee repo's `policy.json` from its main, its bytes, read now: raises GitHubUnavailable."""
        return gh_read("api", "-H", "Accept: application/vnd.github.raw", f"repos/{self.referee}/contents/policy.json")

    @staticmethod
    def policy(raw: bytes):
        """``raw`` parsed: raises ValueError, never another error for what the file holds (nesting past Python's
        recursion limit is a ValueError too)."""
        try:
            return json.loads(raw)
        except RecursionError:
            raise ValueError("policy.json nests deeper than it can be read") from None

    def seed_commit(self) -> str:
        return str(self.summary().get("seed_commit", ""))

    def last_epoch(self) -> str | None:
        epochs = self.summary().get("seed_epochs") or []
        last = epochs[-1] if isinstance(epochs, list) and epochs and isinstance(epochs[-1], dict) else {}
        return str(last["commit"]) if re.fullmatch(r"[0-9a-f]{40}", str(last.get("commit", ""))) else None

    def image(self) -> str | None:
        """The capsule image's id, or None when docker cannot say."""
        proc = run("docker", "image", "inspect", "--format", "{{.Id}}", IMAGE, check=False, timeout=60)
        return proc.stdout.decode().strip() or None if proc.returncode == 0 else None

    def image_label(self, name: str) -> str | None:
        """A sha256 the capsule image's build wrote as a label (`build`); None for an image built before the label
        existed or when docker cannot say: unknown, never the checkout's guess."""
        proc = run("docker", "image", "inspect", "--format", "{{json .Config.Labels}}", IMAGE, check=False, timeout=60)
        try:
            labels = json.loads(proc.stdout) if proc.returncode == 0 else None
        except ValueError:
            labels = None
        value = labels.get(name) if isinstance(labels, dict) else None
        return value if isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) else None

    def image_prompt(self) -> str | None:
        """The sha256 of the prompt the capsule image holds (E313)."""
        return self.image_label(PROMPT_LABEL)

    def image_context(self) -> str | None:
        """The `context_sha256` of the files the capsule image was built from (E506)."""
        return self.image_label(CONTEXT_LABEL)

    def intervention(self, args) -> None:
        """One metrics row per launcher start: every start is the operator's touch, and what it ran with is what a later
        difference is attributed to (E313). The prompt is the image's own (with --no-build an older image runs); the
        checkout's is written beside it, and a difference is said. So are all the image's build files together (E506):
        a tool or loader file changed in the checkout and not rebuilt is said too, not only the prompt."""
        self.prompt_sha256, self.image_id = self.image_prompt(), self.image()
        self.context_sha256 = self.image_context()
        checkout, checkout_context = prompt_sha256(), context_sha256()
        if self.prompt_sha256 != checkout:
            say(f"the capsule image's prompt is {self.prompt_sha256 or 'unknown'}, the checkout's {checkout}: "
                "the sessions run the image's")
        if self.context_sha256 != checkout_context:
            say(f"the capsule image's build files are {self.context_sha256 or 'unknown'}, the checkout's "
                f"{checkout_context}: the sessions run the image's")
        self.record_metrics({"kind": INTERVENTION, "ts": now(), "args": {k: str(v) for k, v in sorted(vars(args).items())},
                             "image_id": self.image_id, "prompt_sha256": self.prompt_sha256,
                             "checkout_prompt_sha256": checkout, "context_sha256": self.context_sha256,
                             "checkout_context_sha256": checkout_context, "seed_commit": self.seed})

    def build(self) -> None:
        """Build from a copy of exactly the files the image needs: a synced folder (iCloud) can hand docker
        placeholders it cannot read, and nothing else of the repository belongs in the capsule. The image is labelled
        with the sha256 of the prompt bytes it holds, so a later start without a build still knows them (E313), and with
        the `context_sha256` of every file it was built from (E506)."""
        say("building the capsule image")
        with tempfile.TemporaryDirectory(prefix="snowball-founder-") as ctx:
            write_build_context(Path(ctx))
            built = hashlib.sha256(Path(ctx, "founder/prompt.md").read_bytes()).hexdigest()
            proc = run("docker", "build", "--quiet", "--label", f"{PROMPT_LABEL}={built}", "-t", IMAGE,
                       "--label", f"{CONTEXT_LABEL}={context_sha256(Path(ctx))}",
                       "-f", str(Path(ctx, "founder/Dockerfile")), ctx, check=False, timeout=3600)
        if proc.returncode != 0:
            sys.exit("image build failed:\n" + proc.stderr.decode(errors="replace")[-4000:])

    # ---- GitHub -------------------------------------------------------------------------------------------
    def brain_head(self) -> str:
        return gh_json("api", f"repos/{self.brain}/commits/main")["sha"]

    def ledger_bytes(self, sha: str) -> bytes | None:
        """The brain's ledger at sha, byte for byte; None when it cannot be read (no ledger yet, a failed call). The
        last commit's bytes are kept: a cycle reads the same head for its rows and for the lesson index (`26g`)."""
        if self._ledger_read is not None and self._ledger_read[0] == sha:
            return self._ledger_read[1]
        proc = run("gh", "api", "-H", "Accept: application/vnd.github.raw",
                   f"repos/{self.brain}/contents/{LEDGER_FILE}?ref={sha}", check=False)
        data = proc.stdout if proc.returncode == 0 else None
        self._ledger_read = (sha, data) if data is not None else None
        return data

    def ledger_rows(self, sha: str) -> list[dict]:
        data = self.ledger_bytes(sha)
        rows = []
        for line in data.decode(errors="replace").splitlines() if data is not None else []:
            try:
                rows.append(json.loads(line))
            except ValueError:
                rows.append({"kind": "<unreadable line>"})
        return rows

    def target_head(self) -> str | None:
        """The commit of the target clone the capsule mounts (read-only `rev-parse`)."""
        proc = run("git", "-C", str(self.target), "rev-parse", "HEAD", check=False, timeout=60)
        return proc.stdout.decode().strip() or None if proc.returncode == 0 else None

    def spec_tohum_tree(self, sha: str) -> str | None:
        """Git's tree id of the brain's `spec/tohum` at sha: the seed text the session read, one GET."""
        proc = run("gh", "api", f"repos/{self.brain}/contents/spec?ref={sha}", check=False, timeout=120)
        try:
            entries = json.loads(proc.stdout) if proc.returncode == 0 else []
            return next((e["sha"] for e in entries if e.get("name") == "tohum" and e.get("type") == "dir"), None)
        except (ValueError, TypeError, KeyError):
            return None

    TREE_QUERY = ("query($owner:String!,$name:String!,$expr:String!){repository(owner:$owner,name:$name){"
                  "object(expression:$expr){... on Tree{entries{name object{... on Blob{text isTruncated oid}}}}}}}")

    def tree_blobs(self, expr: str) -> list[dict] | None:
        """The entries of the brain's tree `<sha>:<path>`, each `{name, object: {text, isTruncated, oid}}`, in one read-only
        GraphQL call; [] for no such tree, None when it cannot be read."""
        owner, name = self.brain.split("/", 1)
        proc = run("gh", "api", "graphql", "-f", f"query={self.TREE_QUERY}", "-f", f"owner={owner}", "-f",
                   f"name={name}", "-f", f"expr={expr}", check=False, timeout=120)
        try:
            tree = json.loads(proc.stdout)["data"]["repository"]["object"] if proc.returncode == 0 else None
        except (ValueError, TypeError, KeyError):
            return None
        return list((tree or {}).get("entries") or []) if proc.returncode == 0 else None

    WIP_QUERY = ("query($owner:String!,$name:String!){repository(owner:$owner,name:$name){refs(refPrefix:"
                 "\"refs/heads/wip/\",first:100){pageInfo{hasNextPage} nodes{name target{oid}}}}}")

    def wip_branches(self) -> list[dict] | None:
        """The brain's `wip/` branches, each ``{name, sha}`` (name without the prefix), in one read-only GraphQL call;
        None when they cannot be read or more than one page holds them."""
        owner, name = self.brain.split("/", 1)
        proc = run("gh", "api", "graphql", "-f", f"query={self.WIP_QUERY}", "-f", f"owner={owner}", "-f",
                   f"name={name}", check=False, timeout=120)
        try:
            refs = json.loads(proc.stdout)["data"]["repository"]["refs"] if proc.returncode == 0 else None
            if refs is None or refs["pageInfo"]["hasNextPage"]:
                return None
            return [{"name": str(n["name"]), "sha": str(n["target"]["oid"])} for n in refs["nodes"]]
        except (ValueError, TypeError, KeyError):
            return None

    def wip(self, last_accepted: str | None) -> list[str] | None:
        """`wip_findings` of the brain's `wip/` branches against `main` and the last accepted head; None when any read
        fails (unknown, never "none", E527's rule)."""
        branches = self.wip_branches()
        if branches is None:
            return None

        def compare(base: str, head: str) -> dict:
            found = gh_json("api", f"repos/{self.brain}/compare/{base}...{head}")
            if not isinstance(found, dict):
                raise ValueError("compare: not an object")
            return found
        try:
            return wip_findings(branches, compare, last_accepted)
        except (GitHubUnavailable, ValueError, TypeError, KeyError):
            return None

    def open_reports(self, sha: str) -> list[dict] | None:
        """The brain's root `reports/*.json` at sha, each read by the referee's own `reportlife.read_row` (`26l`), in
        one read-only GraphQL call; None when the tree cannot be read. A blob's text counts only when its UTF-8 bytes
        are the blob git names (its `oid`); a truncated, binary or mismatched one is read as unreadable, so it counts
        open."""
        entries = self.tree_blobs(f"{sha}:reports")
        if entries is None:
            return None
        out = []
        for entry in entries:
            name = str(entry.get("name", ""))
            if not name.endswith(".json"):
                continue
            blob = entry.get("object") or {}
            text = blob.get("text")
            data = text.encode("utf-8") if isinstance(text, str) and not blob.get("isTruncated") else None
            if data is not None and hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest() != blob.get("oid"):
                data = None
            out.append(reportlife.read_row(name, data))
        return out

    def observe(self, head: str, last_accepted: str | None = None) -> dict:
        """What this cycle's outcome is attributed to, read after the session (E313): the brain's seed text and its open
        reports at head split by the referee's rule (`reportlife.split`, `26l`): the operator's debt (`reports_open`)
        and the Founder's unconfirmed ones (`reports_unconfirmed`), each with its age; the target commit the capsule
        mounted, and the brain's `wip/` branches the operator should hear of (E592). Unknown is None, never "none"."""
        reports = self.open_reports(head)
        seen_path = self.work / REPORTS_SEEN
        try:
            seen = json.loads(seen_path.read_text(encoding="utf-8")) if seen_path.is_file() else {}
        except ValueError:
            seen = {}
        ages = report_ages(reports or [], seen, now())
        seen_path.write_text(json.dumps(seen, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        try:
            owed, unconfirmed = reportlife.split(reports, reportlife.load_answers()) if reports is not None else (None, None)
        except reportlife.AnswersError:
            owed, unconfirmed = None, None
        return {"spec_tohum_tree": self.spec_tohum_tree(head), "target_sha": self.target_head(),
                "reports_open": None if owed is None else aged(owed, ages),
                "reports_unconfirmed": None if unconfirmed is None else aged(unconfirmed, ages),
                "wip": self.wip(last_accepted)}

    def record_cost(self, stamp: str, sess: dict, head: str, last_accepted: str | None) -> str:
        """The session's cost row (`tohum/24a` 4), with any rows an earlier cycle had to keep; what happened, as a line
        for the report. A killed session gets its row too: that is what the next session can learn from (E340)."""
        pending_path = self.work / COST_PENDING
        facts = []
        if pending_path.is_file():  # a broken line is kept out, never a reason to lose the session's own row
            facts = [row for row in map(_json_or_none, pending_path.read_text(encoding="utf-8").splitlines())
                     if isinstance(row, dict)]
        facts.append({"stamp": stamp, "head": head, **{k: sess.get(k) for k in ("exit", "minutes", "turns", "cost_usd",
                                                                               "subtype", "model_served", "models",
                                                                               "tokens")}})
        try:
            outcome = push_cost_rows(self.brain_remote, facts, last_accepted, now(), self.epoch)
        except (gitio.GitError, ValueError, OSError) as exc:
            outcome = f"deferred: {type(exc).__name__}: {str(exc)[:200]}"
        if outcome.startswith("deferred"):
            pending_path.write_text("".join(json.dumps(f, sort_keys=True) + "\n" for f in facts), encoding="utf-8")
            return f"{len(facts)} satır bekliyor ({outcome})"
        pending_path.unlink(missing_ok=True)
        return f"{len(facts)} satır yazıldı, beyin `{outcome[:7]}`"

    def fetch_result(self) -> dict | None:
        """The newest bootstrap-state artifact made on the referee's main branch, unpacked into <work>/referee.

        A `none` result on a head that adds only this script's own commits (its cost rows) to the previous result's
        head is not the Founder's verdict: the referee's schedule can judge the launcher's commit at any time, and
        mounting that `noop` would hide the verdict on the Founder's own last push (its rival block, tests, warnings).
        The previous result is mounted instead; the state in both is the same, so nothing is lost."""
        arts = self.state_artifacts()
        for old in self.result_dir.iterdir():
            old.unlink()
        if not arts:
            return None
        files = self.artifact_files(arts[0])
        result = json.loads(files["result.json"]) if "result.json" in files else None
        if result and result.get("kind") == "none" and len(arts) > 1:
            older_files = self.artifact_files(arts[1])
            older = json.loads(older_files["result.json"]) if "result.json" in older_files else None
            if older and older.get("head") and self.launcher_commits_only(older["head"], str(result.get("head"))):
                files, result = older_files, older
        for name, data in files.items():
            (self.result_dir / name).write_bytes(data)
        return result

    def state_artifacts(self) -> list[dict]:
        """The referee's unexpired bootstrap-state artifacts made on its main branch, newest first."""
        listing = gh_json("api", f"repos/{self.referee}/actions/artifacts?name={STATE_ARTIFACT}&per_page=30")
        return sorted((a for a in (listing or {}).get("artifacts", [])
                       if not a["expired"] and (a.get("workflow_run") or {}).get("head_branch") == "main"),
                      key=lambda a: a["created_at"], reverse=True)

    def verdict_on(self, head: str) -> dict | None:
        """The newest signed result that evaluated head, among the referee's last VERDICT_LOOKBACK results (E420): a
        result on another head made after it (a seed epoch's `noop`, a scheduled run) does not hide it. None when no
        such result is among them or GitHub cannot be read."""
        try:
            for art in self.state_artifacts()[:VERDICT_LOOKBACK]:
                files = self.artifact_files(art)
                result = json.loads(files["result.json"]) if "result.json" in files else None
                if self.evaluated(result, head):
                    return result
        except (GitHubUnavailable, ValueError, zipfile.BadZipFile):
            return None
        return None

    def artifact_files(self, art: dict) -> dict[str, bytes]:
        """An artifact's top-level files (no paths, no dot files), as bytes."""
        blob = gh_read("api", f"repos/{self.referee}/actions/artifacts/{art['id']}/zip")
        with zipfile.ZipFile(io.BytesIO(blob)) as zf:
            return {name: zf.read(name) for name in zf.namelist()
                    if not ("/" in name or "\\" in name or name.startswith("."))}

    def launcher_commits_only(self, base: str, head: str) -> bool:
        """Whether every commit from base to head is this script's own (its committer name and e-mail); False when
        the brain cannot be read or base is not an ancestor of head, so the newest result is then mounted as it is."""
        try:
            cmp = gh_json("api", f"repos/{self.brain}/compare/{base}...{head}")
        except (GitHubUnavailable, ValueError):
            return False
        commits = (cmp or {}).get("commits") or []
        return ((cmp or {}).get("status") == "ahead" and bool(commits)
                and all(((c.get("commit") or {}).get("committer") or {}).get("name") == LAUNCHER_NAME
                        and ((c.get("commit") or {}).get("committer") or {}).get("email") == LAUNCHER_EMAIL
                        for c in commits))

    def refresh_inputs(self) -> None:
        """Rebuild <work>/vec from the `vectors/` of the referee repo's main, with the referee's own projection
        (`vectors.founder_inputs`): what the referee will run next, never an older copy. Raises when it cannot."""
        self.referee_facts = None  # an earlier cycle's facts are never this cycle's
        tarball = gh_read("api", f"repos/{self.referee}/tarball/main", timeout=600)  # an outage is waited out (E245)
        try:  # the mirror's facts, from the same download (E647); never a reason to lose the inputs
            self.referee_facts = MIRROR.referee_facts(tarball, RESERVED_TOP)
        except Exception as exc:  # a tarball the mirror cannot read is the mirror's null, said by its class
            self.referee_facts = {"error": type(exc).__name__}
        with tempfile.TemporaryDirectory(prefix="snowball-vec-") as tmp:
            founder_inputs(referee_vectors(tarball, Path(tmp)), self.inputs)

    def dispatch_referee(self, timeout_s: int) -> dict:
        """Dispatch the referee on main and wait for that run; returns {id, conclusion, url}."""
        since = datetime.now(timezone.utc)
        proc = run("gh", "workflow", "run", REFEREE_WORKFLOW, "--repo", self.referee, "--ref", "main", check=False,
                   timeout=120)
        if proc.returncode != 0:  # a write is not repeated here; the cycle is tried again after the outage (E248)
            raise GitHubUnavailable(f"gh workflow run: {proc.stderr.decode(errors='replace').strip()[-300:]}")
        run_id = None
        try:
            for _ in range(30):
                time.sleep(5)
                runs = gh_json("run", "list", "--repo", self.referee, "--workflow", REFEREE_WORKFLOW, "--branch", "main",
                               "--event", "workflow_dispatch", "--limit", "5", "--json", "databaseId,createdAt,headBranch")
                # Only main's runs are this dispatch's: an operator's trial dispatched on a branch in the same window
                # is not the Founder's verdict (E461).
                fresh = [r for r in runs if r.get("headBranch") == "main"
                         and datetime.fromisoformat(r["createdAt"].replace("Z", "+00:00")) >= since]
                if fresh:
                    run_id = str(min(fresh, key=lambda r: r["createdAt"])["databaseId"])
                    break
            if run_id is None:
                return {"id": None, "conclusion": "not_started", "url": ""}
            deadline = time.monotonic() + timeout_s
            while time.monotonic() < deadline:
                view = gh_json("run", "view", run_id, "--repo", self.referee, "--json", "status,conclusion,url")
                if view["status"] == "completed":
                    return {"id": run_id, "conclusion": view["conclusion"], "url": view["url"]}
                if self.stopped():
                    break
                time.sleep(30)
        except GitHubUnavailable as exc:  # the run goes on at GitHub; the next start judges the head (E168, E245)
            say(f"referee run {run_id or '?'}: GitHub unreachable while waiting ({exc})")
            return {"id": run_id, "conclusion": "github_unavailable", "url": ""}
        return {"id": run_id, "conclusion": "still_running", "url": ""}

    # ---- the session --------------------------------------------------------------------------------------
    def session_logs(self, stamp: str) -> Path:
        return self.logs / stamp

    def capsule_argv(self, stamp: str, model: str, max_turns: int, budget_usd: int,
                     effort: str | None = None) -> list[str]:
        def bind(src: Path, dst: str, ro: bool) -> list[str]:
            return ["--mount", f"type=bind,src={src},dst={dst}" + (",readonly" if ro else "")]

        return ["docker", "run", "--rm", "--name", f"snowball_founder_{stamp.lower()}",
               "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
               "--pids-limit", "1024", "--memory", "8g", "--cpus", "4",
               "--tmpfs", "/tmp:rw,exec,size=2g,mode=1777",
               "--tmpfs", "/home/founder:rw,size=256m,mode=1777",
               "--tmpfs", "/work/brain:rw,exec,size=2g,mode=1777",
               *bind(self.env_file, "/run/secrets/founder.env", True),
               *bind(self.result_dir, "/work/referee", True),
               *bind(self.target, "/work/target", True),
               *bind(self.inputs, "/vec", True),  # where each case's command reads its fixtures, as in the referee's
               *bind(self.session_logs(stamp), "/work/logs", False),  # its own folder: memory is the ledger (E155)
               "-e", f"BRAIN_REPO={self.brain}", "-e", f"BRAIN_SEED={self.seed}", "-e", f"SESSION_STAMP={stamp}",
               "-e", f"FOUNDER_MODEL={model}", "-e", f"FOUNDER_MAX_TURNS={max_turns}",
               "-e", f"FOUNDER_MAX_BUDGET_USD={budget_usd}",
               *(["-e", f"FOUNDER_EFFORT={effort}"] if effort else []),  # the CLI's --effort; none: its default
               IMAGE]

    def session(self, stamp: str, model: str, max_turns: int, budget_usd: int, timeout_s: int,
                effort: str | None = None) -> dict:
        self.session_logs(stamp).mkdir(parents=True, exist_ok=True)
        cmd = self.capsule_argv(stamp, model, max_turns, budget_usd, effort)
        started = time.monotonic()
        err = ""
        try:
            proc = run(*cmd, check=False, timeout=timeout_s)
            exit_code, tail = proc.returncode, proc.stdout.decode(errors="replace").strip().splitlines()[-1:]
            err = proc.stderr.decode(errors="replace").strip()[-600:]  # docker's own complaint; the CLI's goes to logs/
        except subprocess.TimeoutExpired:
            run("docker", "stop", f"snowball_founder_{stamp.lower()}", check=False)  # the container this script started
            exit_code, tail = -1, ["session timed out"]
        out = {"exit": exit_code, "minutes": round((time.monotonic() - started) / 60, 1), "line": tail[0] if tail else "",
               "stderr": err}
        out.update(self.transcript_summary(self.session_logs(stamp) / f"session-{stamp}.jsonl"))
        out.update(self.transcript_init(self.session_logs(stamp) / f"session-{stamp}.jsonl"))
        out["timed_out"] = exit_code == -1 and tail == ["session timed out"]
        return out

    @staticmethod
    def transcript_init(path: Path) -> dict:
        """The CLI's opening `system`/`init` event: its version and the model it was served (E313)."""
        if path.is_file():
            with path.open("r", encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    try:
                        event = json.loads(line)
                    except ValueError:
                        continue
                    if isinstance(event, dict) and event.get("type") == "system" and event.get("subtype") == "init":
                        return {"cli_version": event.get("claude_code_version"), "model_served": event.get("model")}
        return {"cli_version": None, "model_served": None}

    @staticmethod
    def transcript_summary(path: Path) -> dict:
        """The CLI's closing `result` event: turns, cost, whether it ended in an error."""
        if not path.is_file():
            return {"transcript": "missing"}
        last = None
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if '"type":"result"' in line.replace(" ", ""):
                try:
                    last = json.loads(line)
                except ValueError:
                    pass
        if last is None:
            return {"transcript": "no result event"}
        usage = last.get("usage") if isinstance(last.get("usage"), dict) else {}
        models = last.get("modelUsage") if isinstance(last.get("modelUsage"), dict) else {}
        return {"turns": last.get("num_turns"), "cost_usd": last.get("total_cost_usd"),
                "subtype": last.get("subtype"), "final": str(last.get("result") or "")[:1500],
                "api_error": last.get("api_error"), "api_error_status": last.get("api_error_status"),
                "tokens": {name: _count(usage.get(key)) for name, key in TOKEN_FIELDS},
                "models": sorted(m for m in models if isinstance(m, str))}

    # ---- the report ---------------------------------------------------------------------------------------
    def write(self, text: str) -> None:
        with self.report.open("a", encoding="utf-8") as fh:
            fh.write(text)

    def record_metrics(self, row: dict) -> None:
        with self.metrics.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    def previous_session_note(self, stamp: str, timeout_s: int, prior: dict | None = None) -> None:
        """How the last session ended, from this script's own record of it, into the next session's folder (E360): a
        session killed at the wall-clock limit leaves no ledger row, so without this the Founder could not see that it
        happened. Facts only (end, minutes, the limit it ran under, push, ledger rows, verdict), never its transcript
        (E155).

        The verdict is the metrics row's unless the referee judged that session's push later (the cycle's judgement
        did not finish, this start caught it up): then it is the signed verdict on that head (E381), looked up among the
        recent results when the newest is another head's (E420: a seed epoch delivered between). A session that did
        not push keeps the row's: the verdict on its head is an earlier session's. The row is never rewritten, so
        readers of the last row see what the cycle saw."""
        lines = self.metrics.read_text(encoding="utf-8").splitlines() if self.metrics.is_file() else []
        # The last cycle's row, not the last line: every launcher start appends its own row first (E313), and the start
        # after a timed-out session is exactly the case this note is for (the operator's card skips those rows too).
        cycles = [row for row in map(_json_or_none, lines)
                  if isinstance(row, dict) and row.get("kind") != INTERVENTION]
        if not cycles:
            return
        last = cycles[-1]
        limit_s = last.get("session_timeout_s") or timeout_s
        verdict = last.get("verdict")
        head = last.get("brain_after")
        if last.get("pushed") and head and not self.evaluated(prior, head):
            prior = self.verdict_on(head)  # the newest result is another head's: a seed epoch came between (E420)
        if last.get("pushed") and prior and head and prior.get("head") == head and self.evaluated(prior, head):
            verdict = prior.get("verdict")
        note = {"stamp": last.get("stamp"), "ended": session_end(last),
                "exit": last.get("session_exit"), "minutes": last.get("minutes"), "limit_minutes": round(limit_s / 60, 1),
                "pushed": bool(last.get("pushed")), "ledger_rows_added": sum((last.get("ledger_new") or {}).values()),
                "verdict": verdict}
        folder = self.session_logs(stamp)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "previous-session.json").write_text(json.dumps(note, ensure_ascii=False, sort_keys=True) + "\n",
                                                      encoding="utf-8")

    def targets_note(self, stamp: str) -> None:
        """The targets' rows (`target_ids`) into the session's folder as `targets.json` (seed-049, E571; seed-050,
        E577): they are in the referee repo's summary, which a session never reads; their names are not."""
        folder = self.session_logs(stamp)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / TARGETS_NOTE).write_text(json.dumps(self.targets, ensure_ascii=False, sort_keys=True) + "\n",
                                           encoding="utf-8")

    def policy_notes(self, stamp: str) -> None:
        """The referee repo's `policy.json`, read once for this session, into its folder twice (`24a` 3): as
        `operating.json`, `operating_values` of it (seed-050, E577), and as `policy.json`, `policy_copy` of its bytes
        (seed-053, E588). The operator writes the file while the pilot runs (E579), so it is never kept from an earlier
        read. Each file is written or withheld on its own; a withheld one leaves a warning and no file, never ``{}``,
        which says the operator wrote no `operating`."""
        folder = self.session_logs(stamp)
        folder.mkdir(parents=True, exist_ok=True)
        try:
            raw = self.policy_raw()
        except GitHubUnavailable as exc:
            say(f"{OPERATING_NOTE} not written, nor {POLICY_NOTE}, for {stamp}: {exc}")
            return
        try:
            note = operating_values(self.policy(raw))
        except ValueError as exc:
            say(f"{OPERATING_NOTE} not written for {stamp}: {exc}")
        else:
            (folder / OPERATING_NOTE).write_text(json.dumps(note, sort_keys=True) + "\n", encoding="utf-8")
        try:
            copy = policy_copy(raw, self.withheld)
        except ValueError as exc:
            say(f"{POLICY_NOTE} not written for {stamp}: {exc}")
        else:
            (folder / POLICY_NOTE).write_bytes(copy)

    def loop_runs(self) -> list[dict]:
        """The rows of `/work/logs/loop-runs.jsonl` (`29y`; the owner's decision of 2026-11-15): a `read` row, then the
        referee repo's newest LOOP_RUNS_MAX runs of `loop.yml` on main, each with its newest attempt's jobs. The
        workflow's own record decides whether an import ever ran (it stays, `deleted`, after a reverted one); a 404
        is `no_loop` only when the same repo answers another read. What could not be read is null, never empty."""
        reads = LoopReads()
        actions = f"repos/{self.referee}/actions"
        head = {"kind": "read", "read_at": now(), "state": "runs", "why": None, "workflow_state": None}

        def unavailable(why: str) -> list[dict]:
            return [dict(head, state="unavailable", why="gh" if why == "not_found" else why)]
        try:
            flow = reads.json(f"{actions}/workflows/{LOOP_WORKFLOW}")
        except LoopUnread as exc:
            if str(exc) != "not_found":
                return unavailable(str(exc))
            try:
                reads.get(f"{actions}/workflows?per_page=1")  # the repo answers: the 404 is the workflow's own
            except LoopUnread as again:
                return unavailable(str(again))
            return [dict(head, state="no_loop")]
        if not isinstance(flow, dict) or not _gh_id(flow.get("id")):
            return unavailable("bad_reply")
        head["workflow_state"] = _gh_word(flow.get("state"))
        try:
            listing = reads.json(f"{actions}/workflows/{LOOP_WORKFLOW}/runs?branch=main&per_page={LOOP_RUNS_MAX}")
        except LoopUnread as exc:
            return unavailable(str(exc))
        runs = listing.get("workflow_runs") if isinstance(listing, dict) else None
        if not isinstance(runs, list) or not all(isinstance(r, dict) and _gh_id(r.get("id")) for r in runs):
            return unavailable("bad_reply")
        rows = [head]
        for one in sorted(runs, key=lambda r: (str(r.get("created_at")), r["id"]), reverse=True)[:LOOP_RUNS_MAX]:
            rows += self.loop_run(reads, actions, one)
        return [{key: loop_shown(value, self.withheld) for key, value in row.items()} for row in rows]

    def loop_run(self, reads: LoopReads, actions: str, one: dict) -> list[dict]:
        """A run's row and, when its jobs could be listed, its newest attempt's first LOOP_JOBS_MAX jobs' rows."""
        created = one.get("created_at")
        row = {"kind": "run", "id": one["id"],
               "created_at": created if isinstance(created, str) and _GH_TIME.fullmatch(created) else None,
               "event": _gh_word(one.get("event")), "status": _gh_word(one.get("status")),
               "conclusion": _gh_word(one.get("conclusion")),
               "attempt": one.get("run_attempt") if _gh_id(one.get("run_attempt")) else None, "jobs_total": None}
        try:
            listing = reads.json(f"{actions}/runs/{one['id']}/jobs?filter=latest&per_page=30")
        except LoopUnread:
            return [row]
        jobs = listing.get("jobs") if isinstance(listing, dict) else None
        total = listing.get("total_count") if isinstance(listing, dict) else None
        if not isinstance(jobs, list) or not all(isinstance(j, dict) for j in jobs) \
                or not (_gh_id(total) or total == 0):
            return [row]
        row["jobs_total"] = total
        return [row] + [self.loop_job(reads, actions, one["id"], job) for job in jobs[:LOOP_JOBS_MAX]]

    def loop_job(self, reads: LoopReads, actions: str, run_id: int, job: dict) -> dict:
        """A job's row: its name, status and conclusion, its summary line or the class that kept it out, and for a
        failed job that printed none, the failing step's last lines. A skipped job's log is never asked for."""
        name = job.get("name") if isinstance(job.get("name"), str) else None
        row = {"kind": "job", "run": run_id,
               "name": None if name is None or secretscan.scan(name) else withheld(name, self.withheld)[:80],
               "status": _gh_word(job.get("status")), "conclusion": _gh_word(job.get("conclusion")),
               "summary": None, "summary_why": "unread", "output": None, "output_why": None}
        if row["conclusion"] == "skipped":
            row["summary_why"] = "not_run"
            return row
        failed = row["conclusion"] == "failure"
        body = None
        if row["status"] == "completed" and name is not None and _gh_id(job.get("id")):
            try:
                body = reads.get(f"{actions}/jobs/{job['id']}/logs")
            except LoopUnread:
                pass
        if body is None or len(body) > LOOP_LOG_MAX or body.lstrip(b"\xef\xbb\xbf \t\r\n").startswith(b"<?xml"):
            row["output_why"] = "unread" if failed else None
            return row
        lines = log_lines(body)
        row["summary"], row["summary_why"] = job_summary(lines, name, self.withheld)
        if failed and row["summary_why"] == "none":
            row["output"], row["output_why"] = job_output(lines, self.withheld)
        return row

    def loop_note(self, stamp: str) -> None:
        """`/work/logs/loop-runs.jsonl` for this session (`29y`), written before it starts and never read back. A read
        that fails in any way still writes the file, `unavailable`; the warning names the class, never the text."""
        folder = self.session_logs(stamp)
        folder.mkdir(parents=True, exist_ok=True)
        try:
            rows = self.loop_runs()
            data = b"".join(loop_line(row) for row in rows)
        except Exception as exc:  # the session still starts; the exception's text may carry a log's content
            say(f"{LOOP_NOTE} for {stamp}: the read failed ({type(exc).__name__})")
            rows = [{"kind": "read", "read_at": now(), "state": "unavailable", "why": "launcher_error",
                     "workflow_state": None}]
            data = b"".join(loop_line(row) for row in rows)
        (folder / LOOP_NOTE).write_bytes(data)
        if rows[0]["state"] != "runs":
            say(f"{LOOP_NOTE} for {stamp}: {rows[0]['state']} {rows[0]['why'] or ''}".rstrip())

    def lessons_note(self, stamp: str, head: str) -> None:
        """`/work/logs/lessons.json` for this session (`26g`, E610): the live lessons of the ledger at the brain head the
        session starts from (`lesson_index`). A ledger that cannot be read, or an index that fails, leaves no file and a
        warning that names the class only; the session still starts."""
        folder = self.session_logs(stamp)
        folder.mkdir(parents=True, exist_ok=True)
        try:
            data = self.ledger_bytes(head)
            if data is None:
                say(f"{LESSONS_NOTE} not written for {stamp}: the ledger at {head[:7]} could not be read")
                return
            note = lesson_index(data, head)
        except Exception as exc:  # no session is lost to the index; the text may carry a row's content
            say(f"{LESSONS_NOTE} not written for {stamp}: {type(exc).__name__}")
            return
        (folder / LESSONS_NOTE).write_text(json.dumps(note, ensure_ascii=False, sort_keys=True) + "\n",
                                           encoding="utf-8")

    def accepted_manifest(self, prior: dict | None) -> dict:
        """The mirror's `path` input (epoch Z, `26h`): the `done_mf` of the brain's `snowball-tests.json` at the signed
        state's last accepted SHA, read with `gh api`; ``{"error": <class>}`` when there is no signed state or the read
        fails, which is the mirror's null and never stops the cycle. One attempt, no retry (E679): the three minutes of
        retries an outage costs every other read would hold each session's start for a fact that may be null."""
        sha = ((prior or {}).get("state") or {}).get("last_accepted_sha")
        if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
            return {"error": "no_signed_state"}
        try:
            data = json.loads(gh_read("api", f"repos/{self.brain}/contents/snowball-tests.json?ref={sha}",
                                      "-H", "Accept: application/vnd.github.raw", delays=()))
        except Exception as exc:  # GitHub down, no file, not JSON: the mirror says which class, the session starts
            return {"error": type(exc).__name__}
        return {"sha": sha, "done_mf": data.get("done_mf") if isinstance(data, dict) else None}

    def mirror_note(self, stamp: str, prior: dict | None = None) -> None:
        """`/work/logs/mirror.json` for this session (`mirror.py`, E647): facts only, from the launcher's own records on
        disk, this cycle's referee tarball, the seed's P1 table and the accepted manifest's `done_mf` (`accepted_manifest`,
        from ``prior``, the signed result this cycle mounted), after this session's loop runs were written. Shown by the
        referee's rule for a target's name (`loop_shown`); a text of a secret's shape, or a mirror that fails, leaves no
        file and a warning that names the class only; the session still starts."""
        folder = self.session_logs(stamp)
        folder.mkdir(parents=True, exist_ok=True)
        try:
            note = MIRROR.mirror(stamp, self.metrics, self.logs, self.referee_facts, SEED.parent / "spec",
                                 self.accepted_manifest(prior), SEED / "bootstrap" / "stages")
            data = json.dumps(loop_shown(note, self.withheld), ensure_ascii=False, sort_keys=True,
                              allow_nan=False) + "\n"
        except Exception as exc:  # no session is lost to the mirror; the text may carry a row's content
            say(f"{MIRROR_NOTE} not written for {stamp}: {type(exc).__name__}")
            return
        if secretscan.scan(data):
            say(f"{MIRROR_NOTE} not written for {stamp}: secret_shape")
            return
        (folder / MIRROR_NOTE).write_text(data, encoding="utf-8")

    def memory_alone(self, prior: dict | None, head: str) -> bool:
        """Whether head adds only memory to the newest signed result's own evaluated head (`memory_alone`)."""
        evaluated = (prior or {}).get("head") if self.evaluated(prior, str((prior or {}).get("head"))) else None
        return memory_alone(self.brain_remote, ((prior or {}).get("state") or {}).get("last_accepted_sha"), evaluated,
                            head, self.epoch)

    @staticmethod
    def evaluated(verdict: dict | None, head: str) -> bool:
        return bool(verdict) and verdict.get("head") == head and (verdict.get("state") or {}).get("last_evaluated_sha") == head

    def fetched(self) -> dict | None:
        """The newest signed result, or None while GitHub cannot be read: a verdict that cannot be fetched now is
        judged at the next start (E168, E245)."""
        try:
            return self.fetch_result()
        except GitHubUnavailable as exc:
            say(f"the referee's result could not be fetched: {exc}")
            return None

    def judge(self, n: int, head: str, timeout_s: int) -> tuple[dict, dict | None, int]:
        """Dispatch the referee for head, and again while it leaves head unevaluated (the rival failed on its own
        side, or an outage): the Founder is never asked to fix what was not its fault (E166). A head a brake stopped
        is not sent again: the referee's poll passes it until the operator raises the brake (E550).

        The verdict returned is head's or None: the newest signed result belongs to another head whenever the run
        did not finish (STOP while waiting, a timeout, a run that never started), and an older head's verdict
        written as this head's is a false record (E241)."""
        dispatched = self.dispatch_referee(timeout_s)
        verdict, retries = self.fetched(), 0
        while (retries < MAX_REFEREE_RETRIES and verdict and verdict.get("head") == head
               and not self.evaluated(verdict, head) and not verdict.get("budget_stop") and not self.stopped()):
            retries += 1
            say(f"cycle {n}: {head[:7]} was not evaluated ({verdict.get('warnings')}); referee again, retry {retries}")
            dispatched = self.dispatch_referee(timeout_s)
            verdict = self.fetched()
        if not verdict or verdict.get("head") != head:
            say(f"cycle {n}: no verdict for {head[:7]} yet (referee run {dispatched['conclusion']}); "
                "the next start judges it first (E168)")
            return dispatched, None, retries
        return dispatched, verdict, retries

    def cycle(self, n: int, args) -> bool:
        """One cycle; False when the pilot should stop."""
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        prior = self.fetch_result()
        before = self.brain_head()
        if (before != self.seed and not self.evaluated(prior, before) and not self.stopped()
                and not self.memory_alone(prior, before)):
            # A push the referee never judged (the launcher stopped in between, an outage): judge it before the
            # Founder works on, so its next session reads the verdict on its own last push (E168). A head the referee
            # would read as memory alone (the launcher's own cost commit above the accepted push) is not judged first:
            # its `noop` would replace, in what the capsule mounts, the verdict on the Founder's own last push.
            say(f"cycle {n}: {before[:7]} has no verdict yet; referee first")
            dispatched, caught_up, _ = self.judge(n, before, args.referee_timeout)
            if caught_up is None:  # a session now would read an older verdict and work blind (E168, E248)
                raise NoVerdict(f"{before[:7]} is still unjudged (referee run {dispatched['conclusion']})")
            prior = caught_up
        rows_before = self.ledger_rows(before)
        try:
            self.refresh_inputs()
        except GitHubUnavailable as exc:  # no session on stale inputs; the outage is waited out (E244, E245)
            say(f"cycle {n}: the vector inputs could not be fetched ({exc}); no session")
            self.write(f"\n## Döngü {n} — {stamp}\n\n- GitHub'a ulaşılamadı, vektör girdileri yenilenemedi, oturum yok: "
                       f"`{str(exc).replace('`', chr(39))}`\n")
            raise
        except (OSError, ValueError, KeyError, tarfile.TarError, subprocess.SubprocessError) as exc:
            # No session on stale or missing inputs: the Founder would test against vectors the referee no longer runs.
            say(f"cycle {n}: the vector inputs could not be rebuilt ({exc}); no session, stopping")
            self.write(f"\n## Döngü {n} — {stamp}\n\n- Vektör girdileri yenilenemedi, oturum yok: "
                       f"`{str(exc).replace('`', chr(39))}`\n")
            return False
        say(f"cycle {n}: Founder session {stamp} (brain {before[:7]})")
        self.previous_session_note(stamp, args.session_timeout, prior)
        self.targets_note(stamp)
        self.policy_notes(stamp)
        self.lessons_note(stamp, before)
        self.loop_note(stamp)
        self.mirror_note(stamp, prior)
        sess = self.session(stamp, args.model, args.max_turns, args.budget_usd, args.session_timeout,
                            getattr(args, "effort", None))
        after = self.brain_head()
        rows_after = self.ledger_rows(after)
        new_rows = rows_after[len(rows_before):] if rows_after[:len(rows_before)] == rows_before else rows_after
        verdict = None
        dispatched = None
        retries = 0
        if after != before and not self.stopped():
            say(f"cycle {n}: brain moved to {after[:7]}, dispatching the referee")
            dispatched, verdict, retries = self.judge(n, after, args.referee_timeout)
        kinds: dict[str, int] = {}
        for row in new_rows:
            kinds[str(row.get("kind"))] = kinds.get(str(row.get("kind")), 0) + 1
        lines = [f"\n## Döngü {n} — {stamp}\n",
                 f"- Beyin: `{before[:7]}` → `{after[:7]}`" + (" (push yok)" if after == before else ""),
                 f"- Oturum: çıkış {sess.get('exit')}, {sess.get('minutes')} dk, tur {sess.get('turns')}, "
                 f"maliyet {sess.get('cost_usd')} USD, sonuç {sess.get('subtype', sess.get('transcript'))}",
                 f"- Hakemin önceki kararı (Kurucu'nun okuduğu): {(prior or {}).get('verdict', 'yok')}",
                 f"- Defter: {len(new_rows)} yeni satır " + (json.dumps(kinds, ensure_ascii=False) if kinds else ""),
                 ]
        if sess.get("exit") not in (0, None) and sess.get("stderr"):
            lines.append(f"- Kapsül hatası: `{sess['stderr'].replace('`', chr(39))}`")
        for row in new_rows:
            if row.get("kind") in REPORT_KINDS:
                lines.append(f"  - **{row.get('kind')}**: {json.dumps(row, ensure_ascii=False)[:600]}")
        last_accepted = ((verdict or prior or {}).get("state") or {}).get("last_accepted_sha")
        cost = self.record_cost(stamp, sess, after, last_accepted)
        seen = self.observe(after, last_accepted)
        lines.append(f"- Maliyet satırı (`kind: cost`): {cost}")
        # `26l`, E694: the referee's own split (`reportlife.split`): what the operator owes (a seed epoch) and what the
        # Founder owes (a confirmation, decline or supersession), each on its own line; nothing of it reaches the Founder.
        for key, label in (("reports_open", "Açık raporlar, operatörün borcu (`reports_open`"),
                           ("reports_unconfirmed", "Teyit bekleyen raporlar, Kurucu'nun borcu (`reports_unconfirmed`")):
            if seen.get(key) is None:
                lines.append(f"- {label}): okunamadı")
            else:
                lines.append(f"- {label}; {len(seen[key])}, beyin `{after[:7]}`; yaş: başlatıcının ilk görmesinden bu "
                             "yana saat): " + (", ".join(f"`{rid}` {age} sa" for rid, age in seen[key]) or "yok"))
        # E592: memory lives on main only; a wip/ branch holding it, or left behind the last accepted head, is the
        # operator's to see (the Founder reads `15` 9, never this log). Unknown is said, never "none".
        if seen.get("wip") is None:
            lines.append("- WIP dalları (operatör): okunamadı")
        else:
            lines.append("- WIP dalları (operatör; `15` 9): " + (", ".join(f"`{w}`" for w in seen["wip"]) or "yok"))
        if dispatched is not None:
            lines.append(f"- Hakem koşusu: {dispatched['conclusion']} {dispatched['url']}"
                         + (f" (aynı commit {retries} kez yeniden incelendi)" if retries else ""))
            if verdict:
                lines.append(f"- Hakemin kararı: **{verdict.get('verdict')}**, nedenler {verdict.get('reasons')}")
                if verdict.get("learning"):
                    lines.append(f"- Öğrenme ölçümü: {json.dumps(verdict.get('learning'), ensure_ascii=False)[:600]}")
                if verdict.get("warnings"):
                    lines.append(f"- Uyarılar: {verdict.get('warnings')}")
        if sess.get("final"):
            lines.append("- Kurucu'nun kapanış notu:\n\n  > " + sess["final"].replace("\n", "\n  > "))
        self.write("\n".join(lines) + "\n")
        self.record_metrics({
            "stamp": stamp, "brain_before": before, "brain_after": after, "pushed": after != before,
            "session_exit": sess.get("exit"), "minutes": sess.get("minutes"), "turns": sess.get("turns"),
            "session_timeout_s": args.session_timeout,
            "cost_usd": sess.get("cost_usd"), "verdict": (verdict or {}).get("verdict"), "kind": (verdict or {}).get("kind"),
            "reasons": [{"kind": r.get("kind"), "ref": r.get("ref"), "owner": reason_owner(r)}
                        for r in (verdict or {}).get("reasons", [])],
            "warnings": (verdict or {}).get("warnings", []), "referee_retries": retries,
            "rival_attempts": len(((verdict or {}).get("rival") or {}).get("attempts", [])),
            # The referee's judgement, not the raw runs (E260): a run whose head also shows what the reproducer calls
            # correct proves nothing, and an open claim's re-run is an observation, never a proof.
            "reproduced": sum(1 for r in (verdict or {}).get("reasons") or [] if r.get("kind") == "refutation_reproduced"),
            "old_refutations_still_reproducing": sum(1 for r in (verdict or {}).get("reasons") or []
                                                     if r.get("kind") == "refutation_still_reproduces"),
            "ledger_new": kinds, "api_error": sess.get("api_error"), "api_error_status": sess.get("api_error_status"),
            "subtype": sess.get("subtype"), "end": session_end(sess),
            # What the outcome is attributed to (E313): the launcher start's prompt and image, the model asked for and
            # served, the CLI, the seed, the rival's configuration, the target commit, and whether time ran out (E340).
            "prompt_sha256": self.prompt_sha256, "image_id": self.image_id, "model": args.model,
            "effort": getattr(args, "effort", None),
            "cli_version": sess.get("cli_version"), "model_served": sess.get("model_served"), "seed_commit": self.seed,
            "spec_tohum_tree": seen["spec_tohum_tree"], "target_sha": seen["target_sha"],
            "rival_config": ({k: ((verdict or {}).get("rival") or {}).get(k) for k in RIVAL_CONFIG}
                             if (verdict or {}).get("rival") else None),
            "timed_out": bool(sess.get("timed_out")), "cost_row": cost,
            "reports_open": None if seen.get("reports_open") is None else len(seen["reports_open"]),
            "reports_unconfirmed": (None if seen.get("reports_unconfirmed") is None
                                    else len(seen["reports_unconfirmed"])),
            "wip": seen.get("wip"),  # E592: the wip/ findings, None when unknown
            "reports_new": [r.get("payload", {}).get("summary", "")[:120] for r in new_rows
                            if r.get("kind") in REPORT_KINDS],
        })
        say(f"cycle {n}: done, verdict {(verdict or {}).get('verdict', '-')}")
        limit_wait = usage_limit_wait(sess, datetime.now(timezone.utc))
        if limit_wait is not None and after == before:  # it could not work: an outage, not an idle session (E243)
            say(f"cycle {n}: the session hit the account's usage limit; waiting {limit_wait // 60} min for the reset")
            self.wait(limit_wait)
            return not self.stopped()
        self.idle = self.idle + 1 if after == before else 0
        return not (self.stopped() or self.idle >= 2 or sess.get("exit") == -1)

    def wait(self, seconds: int) -> None:
        """Sleep, waking each minute to honour STOP."""
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline and not self.stopped():
            time.sleep(min(60, max(0.0, deadline - time.monotonic())))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--work", type=Path, default=Path(r"F:\snowball-work"))
    p.add_argument("--brain", default="Okan-wqm/snowball-rehearsal-brain")
    p.add_argument("--referee", default="Okan-wqm/snowball-rehearsal-referee")
    p.add_argument("--target", default="aquaculture_platform")
    p.add_argument("--cycles", type=int, default=1)
    p.add_argument("--model", default="claude-opus-5-5")
    p.add_argument("--effort", choices=("low", "medium", "high", "xhigh", "max"), default=None,
                   help="the Founder CLI's reasoning effort; omitted: the CLI's default")
    p.add_argument("--max-turns", type=int, default=200)
    p.add_argument("--budget-usd", type=int, default=50, help="runaway brake per session, not a budget")
    p.add_argument("--session-timeout", type=int, default=3 * 3600)
    p.add_argument("--referee-timeout", type=int, default=90 * 60)
    p.add_argument("--no-build", action="store_true")
    p.add_argument("--resume", action="store_true",
                   help="continue the run <work>/RUNNING names, after a crash or a reboot (E505)")
    p.add_argument("--install-service", action="store_true",
                   help="register the Scheduled Task that runs --resume at logon and every 15 minutes (E505)")
    p.add_argument("--uninstall-service", action="store_true", help="remove that Scheduled Task")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.install_service or args.uninstall_service:
        return service(args)
    if not args.work.is_dir():
        sys.exit(f"{args.work} is not a folder")
    lock = LauncherLock(args.work / LOCK_FILE)
    if not lock.acquire():  # another launcher lives: it runs, this one does nothing (E505)
        say(f"another launcher holds {lock.path}; this one does nothing")
        return 0
    try:
        return start(parser, args)
    finally:
        lock.release()


def start(parser: argparse.ArgumentParser, args) -> int:
    """One launcher run, under the lock. The run's RUNNING is written once the preflight passed and goes when the run
    ends deliberately (`run_cycles`) or by the operator's Ctrl+C; any other end leaves it for `--resume` (E505)."""
    intent = Intent(args.work)
    try:
        if args.resume:
            args = resumed(parser, args.work, intent)
            if args is None:
                return 0
        else:
            intent.clear()  # a start by hand replaces a cut run, also when its preflight then fails
        if shutil.which("gh") is None or shutil.which("docker") is None:
            sys.exit("gh and docker must be on PATH")
        pilot = Pilot(args.work, args.brain, args.referee, args.target)
        pilot.idle = int(intent.state.get("idle") or 0) if args.resume else 0
        pilot.preflight()
        if not args.resume:
            intent.write(rerun_argv(parser, args), args.cycles)
        if not args.no_build:
            pilot.build()
        pilot.intervention(args)
        if not pilot.report.exists():
            pilot.write("# Snowball pilot günlüğü\n\nHer döngü: Kurucu oturumu → push → hakem → karar.\n")
        if args.resume:
            pilot.write(f"\n- {now()} başlatıcı yeniden başladı (çökme/yeniden açılış sonrası): kalan {args.cycles} "
                        f"döngü (`RUNNING`: başlangıç {intent.state.get('started')}, son güncelleme "
                        f"{intent.state.get('updated')})\n")
        run_cycles(pilot, args, intent)
    except KeyboardInterrupt:  # the operator's Ctrl+C is a deliberate stop; a crash, a kill or a reboot is not
        intent.clear()
        raise
    return 0


def run_cycles(pilot: Pilot, args, intent: Intent | None = None) -> None:
    for n in range(1, args.cycles + 1):
        if pilot.stopped():
            say("STOP file found; stopping")
            break
        try:
            go_on = pilot.cycle(n, args)
        except Outage as exc:  # an outage is waited out, not a reason to end the pilot (E245, E248)
            say(f"cycle {n}: {exc}; waiting {GH_OUTAGE_WAIT_S // 60} min, then the next cycle judges any unjudged "
                "push first (E168)")
            pilot.wait(GH_OUTAGE_WAIT_S)
            go_on = not pilot.stopped()
        if intent is not None:
            intent.update(args.cycles - n, pilot.idle)
        if not go_on:
            say("stopping (STOP file, two sessions without a push, a timed-out session, or no vector inputs)")
            break
    if intent is not None:  # every end that reaches here is deliberate, or the last cycle ran: nothing to resume
        intent.clear()


# ---- resume after a crash or a reboot (E505) -------------------------------------------------------------------
class LauncherLock:
    """An exclusive OS lock on <work>/launcher.lock, held for the launcher's lifetime: the OS frees it when the process
    ends, however it ends (a crash, a kill, a reboot), so no stale lock ever needs clearing by hand."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.fh = None

    def acquire(self) -> bool:
        """True when this process now holds the lock; False when another holder has it."""
        fh = open(self.path, "a+b")  # not inherited by the children (PEP 446): a docker CLI cannot keep it alive
        try:
            if os.name == "nt":
                import msvcrt
                fh.seek(0)
                msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            fh.close()
            return False
        self.fh = fh
        return True

    def release(self) -> None:
        if self.fh is None:
            return
        try:
            if os.name == "nt":
                import msvcrt
                self.fh.seek(0)
                msvcrt.locking(self.fh.fileno(), msvcrt.LK_UNLCK, 1)
        finally:
            self.fh.close()  # closing frees an flock
            self.fh = None


class Intent:
    """<work>/RUNNING: the run in progress, what `--resume` continues. Only the launcher's own options and counts are
    in it, never a secret (the env file is not read here)."""

    def __init__(self, work: Path) -> None:
        self.path = work / RUNNING_FILE
        self.state: dict = {}

    def read(self) -> dict | None:
        """The stored run, or None when there is none or it cannot be read as one."""
        try:
            state = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        argv, left = (state.get("argv"), state.get("cycles_left")) if isinstance(state, dict) else (None, None)
        if (not isinstance(argv, list) or not all(isinstance(a, str) for a in argv)
                or not isinstance(left, int) or isinstance(left, bool)):
            return None
        self.state = state
        return state

    def write(self, argv: list[str], left: int) -> None:
        ts = now()
        self.state = {"argv": argv, "cycles_left": left, "idle": 0, "started": ts, "updated": ts}
        self.save()

    def update(self, left: int, idle: int) -> None:
        self.state.update(cycles_left=left, idle=idle, updated=now())
        self.save()

    def save(self) -> None:
        """Whole or not at all: a power loss in the middle leaves the previous file."""
        tmp = self.path.with_name(RUNNING_FILE + ".tmp")
        tmp.write_text(json.dumps(self.state, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(tmp, self.path)

    def clear(self) -> None:
        self.path.unlink(missing_ok=True)


def rerun_argv(parser: argparse.ArgumentParser, args) -> list[str]:
    """The options that run this launcher again, each spelled out: not the work folder (RUNNING lives in it), not the
    cycles (RUNNING counts what is left), never `--resume` or the service options."""
    out = []
    for action in parser._actions:
        if not action.option_strings or action.dest in NOT_RERUN:
            continue
        value = getattr(args, action.dest)
        if isinstance(action, argparse._StoreTrueAction):
            out += [action.option_strings[0]] if value else []
        elif value is None:  # an option left at no value (e.g. --effort): omitted, so the rerun parses the same
            continue
        else:
            out += [action.option_strings[0], str(value)]
    return out


def resumed(parser: argparse.ArgumentParser, work: Path, intent: Intent):
    """The options of the run RUNNING names, with its cycles left, or None when there is nothing to resume: no RUNNING,
    STOP (a deliberate stop is never overridden: its RUNNING goes), or no cycle left. Exits while docker or gh do not
    answer: RUNNING stays, and the task's next trigger tries again."""
    plan = intent.read()
    if plan is None:
        if intent.path.exists():
            say(f"{intent.path} cannot be read as a run; nothing resumed")
        return None
    if (work / "STOP").exists() or plan["cycles_left"] <= 0:
        intent.clear()
        return None
    if not wait_ready(work):
        if (work / "STOP").exists():
            intent.clear()
            return None
        sys.exit(f"docker or gh did not answer within {READY_WAIT_S // 60} min; {intent.path} stays for the next try")
    args = parser.parse_args([*plan["argv"], "--work", str(work), "--cycles", str(plan["cycles_left"])])
    args.resume = True  # the start's intervention row names it a resume
    say(f"resuming the run of {plan.get('started')}: {plan['cycles_left']} cycle(s) left")
    return args


def wait_ready(work: Path, limit_s: float = READY_WAIT_S) -> bool:
    """Whether docker and gh answer within limit_s (after a reboot docker can take minutes); False past it or on
    STOP."""
    deadline = time.monotonic() + limit_s
    while not (work / "STOP").exists():
        if all(ready(*cmd) for cmd in READY_CHECKS):
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(READY_RETRY_S)
    return False


def ready(*cmd: str) -> bool:
    try:
        return run(*cmd, check=False, timeout=60).returncode == 0
    except (OSError, subprocess.SubprocessError):  # not on PATH yet, or hung
        return False


def task_xml(python: str, script: str, work: str, cwd: str, user: str, start: str) -> str:
    """The Scheduled Task that resumes the launcher: as the current user while logged on (no admin, the user's docker
    and gh login), at logon and every 15 minutes from `start` (local time), one instance at a time, no time limit (the
    scheduler's default of three days would kill a long run), on battery too."""
    esc = xml.sax.saxutils.escape
    every = f"<Repetition><Interval>{TASK_EVERY}</Interval><StopAtDurationEnd>false</StopAtDurationEnd></Repetition>"
    arguments = subprocess.list2cmdline(["-u", script, "--resume", "--work", work])
    return f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Snowball: resume the Founder launcher after a crash or a reboot (E505)</Description>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger>{every}<Enabled>true</Enabled><UserId>{esc(user)}</UserId></LogonTrigger>
    <TimeTrigger>{every}<StartBoundary>{esc(start)}</StartBoundary><Enabled>true</Enabled></TimeTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>{esc(user)}</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <StartWhenAvailable>true</StartWhenAvailable>
    <Enabled>true</Enabled>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{esc(python)}</Command>
      <Arguments>{esc(arguments)}</Arguments>
      <WorkingDirectory>{esc(cwd)}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"""


def schtasks_argv(xml_path: str | None) -> list[str]:
    """Register the task from its XML (replacing an older one), or remove it when there is no XML."""
    if xml_path is None:
        return ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"]
    return ["schtasks", "/Create", "/TN", TASK_NAME, "/XML", xml_path, "/F"]


def service(args) -> int:
    """--install-service / --uninstall-service: the Scheduled Task that runs `--resume` (E505)."""
    if shutil.which("schtasks") is None:
        sys.exit("the service is a Windows Scheduled Task: schtasks is not on PATH")
    if args.uninstall_service:
        proc = run(*schtasks_argv(None), check=False, timeout=120)
    else:
        user = f"{os.environ.get('USERDOMAIN', '')}\\{os.environ.get('USERNAME', '')}".lstrip("\\")
        text = task_xml(sys.executable, str(HERE / "launch.py"), str(args.work.resolve()), str(SEED.parent), user,
                        datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
        with tempfile.TemporaryDirectory(prefix="snowball-task-") as tmp:
            path = Path(tmp) / "task.xml"
            path.write_bytes(text.encode("utf-16"))  # schtasks reads the XML as its declaration says
            proc = run(*schtasks_argv(str(path)), check=False, timeout=120)
    say((proc.stdout + proc.stderr).decode(errors="replace").strip())
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
