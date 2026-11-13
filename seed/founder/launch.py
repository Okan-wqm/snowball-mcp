"""Run the Founder pilot on the operator's machine (register E32, E90, E91). Stdlib only.

One cycle:
  1. download the referee's last signed result (`bootstrap-state` artifact of the referee's main branch);
  2. rebuild <work>/vec from the `vectors/` of the referee repo's main (E244); if that fails, no session: stop;
  3. run one Founder session in the capsule (seed/founder/Dockerfile);
  4. if the brain moved, dispatch the referee (its schedule fires rarely and irregularly, E32) and wait for it;
  5. write the session's cost as a `kind: cost` founder row on the brain's main (`tohum/24a` 4), when that commit is
     memory alone to the referee; otherwise keep it in <work>/cost-pending.jsonl for a later cycle;
  6. append what happened to <work>/pilot-log.md (with the brain's open reports and their age, and apart those no
     changelog of the brain's seed names, the operator's unanswered ones, E527) and one metrics line that names what
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
                                seed-050, E577), and operating.json, policy.json's operating{} read for that session
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
from collections import Counter
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEED = HERE.parent
sys.path.insert(0, str(SEED / "bootstrap"))
from snowball_bootstrap import canon, config, gitio, ledgercheck  # noqa: E402  (the chain rule, the referee's git,
# its strict reading of targets[] and its ledger check)
from snowball_bootstrap.classify import (LEDGER_FILE, SEED_DIRS, is_founder_record,  # noqa: E402  (what is memory
                                         is_seed_path)  # and what is the operator's delivery to the referee)
from snowball_bootstrap.decide import counts_against_founder, is_brake_stop  # noqa: E402  (the referee's rule)
from snowball_bootstrap.exitchecks import fold, target_names  # noqa: E402  (the referee's folded names, E290, E291)
from snowball_bootstrap.vectors import founder_inputs  # noqa: E402  (the referee's projection, not a copy: E244)
IMAGE = "snowball-founder:pilot"
REFEREE_WORKFLOW = "bootstrap.yml"
STATE_ARTIFACT = "bootstrap-state"
VERDICT_LOOKBACK = 10  # results scanned for a head's own verdict: seed epochs and scheduled runs come between (E420)
REFEREE_VECTORS = "vectors"  # the referee repo's copy of seed/bootstrap/vectors (README, seed delivery step 3)
MAX_REFEREE_RETRIES = 2  # with the first run, as many as the referee's own retries (decide.RIVAL_SIDE_WARN)
BUILD_FILES = ("founder/Dockerfile", "founder/entrypoint.sh", "founder/prompt.md", "founder/brain_defs.py",
               "founder/ledger_index.py",
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
READY_RETRY_S = 30
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


def gh_read(*args: str, timeout: float = 120) -> bytes:
    """Stdout of a read-only `gh` call, retried on a failure or a timeout: one dropped connection must not end
    the pilot (E245). Writes (`gh workflow run`) never come through here; repeating one is not harmless."""
    last = ""
    for delay in (*GH_RETRY_DELAYS_S, None):
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


def report_ages(reports: list[dict], seen: dict[str, str], ts: str) -> list[tuple[str, int]]:
    """The open reports and the hours since the launcher first saw each (``seen`` is updated): a report carries no
    time of its own, and the ledger's and commits' times are written in the capsule (E316)."""
    now_dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
    out = []
    for r in reports:
        rid = str(r.get("id") or r.get("file"))
        first = seen.setdefault(rid, ts)
        if r.get("state") == "open":
            out.append((rid, int((now_dt - datetime.strptime(first, "%Y-%m-%dT%H:%M:%SZ")).total_seconds() // 3600)))
    return sorted(out, key=lambda item: (-item[1], item[0]))


CHANGELOG_RE = re.compile(r"CHANGELOG[^/]*\.md")  # the seed's changelogs: spec/tohum/CHANGELOG.md, CHANGELOG-<n>.md


def names_report(text: str, rid: str) -> bool:
    """Whether text names the report by its whole id: `seed-040` is not named by `seed-0401` or `seed-040-x`."""
    return re.search(r"(?<![\w-])" + re.escape(rid) + r"(?![\w-])", text) is not None


def unanswered_reports(ages: list[tuple[str, int]], changelogs: list[str],
                       unchanged: Callable[[str], bool]) -> list[tuple[str, int]]:
    """The open reports the operator still owes (E527, E552): the operator answers a report in an epoch's changelog
    row (`<id> → <page:lines>` or `declined: <id>`, E342), so one named in no seed changelog was never answered or
    declined, and one the Founder changed after the latest epoch that names it (its update, a re-report) was answered
    only up to the bytes it had then. ``unchanged(id)`` says, for an id some changelog names, whether its file is byte
    for byte what it was at that latest naming (`unchanged_since_naming`; never a commit time, E316). For the operator
    alone (pilot-log, metrics)."""
    text = "\n".join(changelogs)
    return [(rid, age) for rid, age in ages if not names_report(text, rid) or not unchanged(rid)]


CHANGELOG_PATHSPEC = ":(glob)spec/tohum/CHANGELOG*.md"


def naming_epochs(clone: Path, rid: str, head: str, additions: dict[str, Counter] | None = None) -> list[str]:
    """The commits up to head, newest first (history order, never commit times, E316), whose changelog diff adds a line
    that names the report (E552). A line moved from one changelog to another, which the compaction of a full changelog
    does verbatim, is not an addition: a naming is the answer being written, not the page it was filed on. ``additions``
    keeps each commit's added lines across calls (a commit never changes)."""
    additions = additions if additions is not None else {}
    literal = re.sub(r"[^\w-]", lambda m: chr(92) + m.group(0), rid)  # git's -G reads an extended regular expression
    found = gitio.git(clone, "log", "--topo-order", "--format=%H", "-G", literal, head, "--", CHANGELOG_PATHSPEC,
                      timeout=GIT_NETWORK_TIMEOUT_S).decode().split()
    out = []
    for commit in found:
        if commit not in additions:
            diff = gitio.git(clone, "diff-tree", "-p", "--root", "-m", "--first-parent", "--no-renames",
                             "--no-ext-diff", "-U0", commit, "--", CHANGELOG_PATHSPEC,
                             timeout=GIT_NETWORK_TIMEOUT_S).decode("utf-8", "replace").splitlines()
            gone = Counter(line[1:] for line in diff if line.startswith("-") and not line.startswith("---"))
            additions[commit] = Counter(line[1:] for line in diff if line.startswith("+")
                                        and not line.startswith("+++")) - gone
        if any(names_report(line, rid) for line in additions[commit]):
            out.append(commit)
    return out


def unchanged_since_naming(clone: Path, rid: str, file: str, head: str,
                           additions: dict[str, Counter] | None = None) -> bool:
    """Whether the report's file at head is byte for byte what it was at the latest commit that names it (git compares
    the two blobs' ids, in a tree the blob-less clone has). False when no commit names it or the file was not there
    then: an answer written before the report existed answers nothing (E552)."""
    for commit in naming_epochs(clone, rid, head, additions)[:1]:
        def blob(at: str) -> str:
            return gitio.git(clone, "rev-parse", f"{at}:reports/{file}", timeout=GIT_LOCAL_TIMEOUT_S).decode().strip()
        try:
            then = blob(commit)
        except gitio.GitError:
            return False
        return then == blob(head)
    return False


def target_ids(summary: dict) -> list[dict]:
    """``[{id, kind, base_sha, unit_candidates}]`` of `setup/summary.json` ``targets[]``, in its order: what a session
    needs to name a target's folder (`24a`, seed-049, E571) and to propose its unit against the row the referee judges
    it by (seed-050, E577), never a target's repo, excluded paths or names (E290). The rows are read by the referee's
    own rule (`config.target`), so a row the referee refuses is refused here too; an id or a unit candidate that holds
    a target's name once folded (`exitchecks.fold`) would carry the name to the session, so it stops the start too,
    named by its field and index only (E290). ``base_sha`` is not folded: the referee's rule already holds it to 40
    hex digits or null, which carry no text. No ``targets[]`` is no target yet: an empty list."""
    rows = summary.get("targets")
    if rows is None:
        return []
    if not isinstance(rows, list):
        raise ValueError("setup/summary.json targets must be a list (`26c`)")
    try:
        targets = tuple(config.target(row, f"setup/summary.json targets[{i}]") for i, row in enumerate(rows))
    except config.ConfigError as exc:
        raise ValueError(str(exc)) from exc
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
        self.brain_remote = f"https://github.com/{brain}.git"
        self.prompt_sha256: str | None = None  # what this launcher start built the capsule with (E313)
        self.context_sha256: str | None = None  # and every build file the image holds (E506)
        self.image_id: str | None = None

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
                self.targets = target_ids(self.summary())
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

    def policy(self):
        """The referee repo's `policy.json` from its main, parsed, read now: raises GitHubUnavailable or ValueError,
        never another error for what the file holds (nesting past Python's recursion limit is a ValueError too)."""
        raw = gh_read("api", "-H", "Accept: application/vnd.github.raw", f"repos/{self.referee}/contents/policy.json")
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

    def ledger_rows(self, sha: str) -> list[dict]:
        proc = run("gh", "api", "-H", "Accept: application/vnd.github.raw",
                   f"repos/{self.brain}/contents/founder-ledger.jsonl?ref={sha}", check=False)
        rows = []
        for line in proc.stdout.decode(errors="replace").splitlines() if proc.returncode == 0 else []:
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
                  "object(expression:$expr){... on Tree{entries{name object{... on Blob{text isTruncated}}}}}}}")

    def tree_blobs(self, expr: str) -> list[dict] | None:
        """The entries of the brain's tree `<sha>:<path>`, each `{name, object: {text, isTruncated}}`, in one read-only
        GraphQL call; [] for no such tree, None when it cannot be read."""
        owner, name = self.brain.split("/", 1)
        proc = run("gh", "api", "graphql", "-f", f"query={self.TREE_QUERY}", "-f", f"owner={owner}", "-f",
                   f"name={name}", "-f", f"expr={expr}", check=False, timeout=120)
        try:
            tree = json.loads(proc.stdout)["data"]["repository"]["object"] if proc.returncode == 0 else None
        except (ValueError, TypeError, KeyError):
            return None
        return list((tree or {}).get("entries") or []) if proc.returncode == 0 else None

    def seed_changelogs(self, sha: str) -> list[str] | None:
        """The texts of the brain's `spec/tohum/CHANGELOG*.md` at sha: the seed it holds (E527). None when they cannot
        be read whole (a failed call, no changelog, a truncated or binary blob): unknown, never "unanswered"."""
        entries = self.tree_blobs(f"{sha}:spec/tohum")
        logs = [e.get("object") or {} for e in entries or [] if CHANGELOG_RE.fullmatch(str(e.get("name", "")))]
        if not logs or any(o.get("isTruncated") or not isinstance(o.get("text"), str) for o in logs):
            return None
        return [o["text"] for o in logs]

    def open_reports(self, sha: str) -> list[dict] | None:
        """The brain's root `reports/*.json` at sha, each `{file, id, state}`, in one read-only GraphQL call; None when
        it cannot be read."""
        entries = self.tree_blobs(f"{sha}:reports")
        if entries is None:
            return None
        out = []
        for entry in entries:
            if not str(entry.get("name", "")).endswith(".json"):
                continue
            try:
                doc = json.loads(((entry.get("object") or {}).get("text")) or "")
            except ValueError:
                doc = None
            doc = doc if isinstance(doc, dict) else {}
            out.append({"file": entry["name"], "id": doc.get("id"), "state": doc.get("state")})
        return out

    def observe(self, head: str) -> dict:
        """What this cycle's outcome is attributed to, read after the session (E313): the brain's seed text and open
        reports at head, which of them no changelog of the seed it holds names (E527), and the target commit the capsule
        mounted."""
        reports = self.open_reports(head)
        seen_path = self.work / REPORTS_SEEN
        try:
            seen = json.loads(seen_path.read_text(encoding="utf-8")) if seen_path.is_file() else {}
        except ValueError:
            seen = {}
        ages = report_ages(reports or [], seen, now())
        seen_path.write_text(json.dumps(seen, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        changelogs = self.seed_changelogs(head) if reports is not None else None
        return {"spec_tohum_tree": self.spec_tohum_tree(head), "target_sha": self.target_head(),
                "reports_open": None if reports is None else ages,
                "reports_unanswered": (None if changelogs is None
                                       else self.owed_reports(head, reports, ages, changelogs))}

    def owed_reports(self, head: str, reports: list[dict], ages: list[tuple[str, int]],
                     changelogs: list[str]) -> list[tuple[str, int]] | None:
        """`unanswered_reports` with the brain's history for the ids a changelog names (E527, E552): one blob-less
        clone, made only when some open report is named at all. None when the history cannot be read: unknown, never
        "owed"."""
        files = {str(r.get("id") or r.get("file")): str(r["file"]) for r in reports}
        text = "\n".join(changelogs)
        if not any(names_report(text, rid) for rid, _ in ages):
            return unanswered_reports(ages, changelogs, lambda rid: False)
        additions: dict[str, Counter] = {}
        try:
            with tempfile.TemporaryDirectory(prefix="snowball-reports-") as tmp:
                clone = Path(tmp) / "brain"
                gitio.git(Path(tmp), "-c", GH_CREDENTIAL, "clone", "--quiet", "--no-checkout", "--filter=blob:none",
                          "--branch", "main", self.brain_remote, str(clone), timeout=GIT_NETWORK_TIMEOUT_S)
                return unanswered_reports(ages, changelogs,
                                          lambda rid: unchanged_since_naming(clone, rid, files[rid], head, additions))
        except (gitio.GitError, OSError):
            return None

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
        tarball = gh_read("api", f"repos/{self.referee}/tarball/main", timeout=600)  # an outage is waited out (E245)
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

    def capsule_argv(self, stamp: str, model: str, max_turns: int, budget_usd: int) -> list[str]:
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
               IMAGE]

    def session(self, stamp: str, model: str, max_turns: int, budget_usd: int, timeout_s: int) -> dict:
        self.session_logs(stamp).mkdir(parents=True, exist_ok=True)
        cmd = self.capsule_argv(stamp, model, max_turns, budget_usd)
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

    def operating_note(self, stamp: str) -> None:
        """`operating_values` of the referee repo's `policy.json`, read for this session, into its folder as
        `operating.json` (seed-050, E577): the operator writes `operating{}` while the pilot runs (E579), so it is
        never kept from an earlier read. A policy that cannot be read, or whose `operating` is not `26c`'s shape,
        leaves no file and a warning; never ``{}``, which says the operator wrote none."""
        try:
            note = operating_values(self.policy())
        except (GitHubUnavailable, ValueError) as exc:
            say(f"{OPERATING_NOTE} not written for {stamp}: {exc}")
            return
        folder = self.session_logs(stamp)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / OPERATING_NOTE).write_text(json.dumps(note, sort_keys=True) + "\n", encoding="utf-8")

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
        self.operating_note(stamp)
        sess = self.session(stamp, args.model, args.max_turns, args.budget_usd, args.session_timeout)
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
        seen = self.observe(after)
        lines.append(f"- Maliyet satırı (`kind: cost`): {cost}")
        if seen["reports_open"] is None:
            lines.append("- Açık raporlar: okunamadı")
        else:
            lines.append(f"- Açık raporlar ({len(seen['reports_open'])}, beyin `{after[:7]}`; yaş: başlatıcının ilk "
                         "görmesinden bu yana saat): " + ", ".join(f"`{rid}` {age} sa" for rid, age in seen["reports_open"]))
        # E527: an open report no changelog of the brain's seed names was never answered nor declined: the operator's
        # move (a seed epoch). Its own line, so it cannot hide among the open ones; nothing of it reaches the Founder.
        if seen.get("reports_unanswered") is None:
            lines.append("- CEVAPSIZ (operatör): okunamadı (raporlar ya da beyindeki `spec/tohum/CHANGELOG*.md`)")
        else:
            lines.append(f"- CEVAPSIZ (operatör) ({len(seen['reports_unanswered'])}; beyindeki tohumun hiçbir "
                         "`spec/tohum/CHANGELOG*.md`'si adlandırmıyor, yanıt ya da `declined:` bekliyor): "
                         + (", ".join(f"`{rid}` {age} sa" for rid, age in seen["reports_unanswered"]) or "yok"))
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
            "cli_version": sess.get("cli_version"), "model_served": sess.get("model_served"), "seed_commit": self.seed,
            "spec_tohum_tree": seen["spec_tohum_tree"], "target_sha": seen["target_sha"],
            "rival_config": ({k: ((verdict or {}).get("rival") or {}).get(k) for k in RIVAL_CONFIG}
                             if (verdict or {}).get("rival") else None),
            "timed_out": bool(sess.get("timed_out")), "cost_row": cost,
            "reports_open": None if seen["reports_open"] is None else len(seen["reports_open"]),
            "reports_unanswered": (None if seen.get("reports_unanswered") is None
                                   else len(seen["reports_unanswered"])),
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
