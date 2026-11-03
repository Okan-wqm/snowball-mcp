"""Deliver one seed epoch with one command (`seed/founder/README.md` "Tohum teslimi", E88, E242, E385; E526).

    python seed/founder/deliver_epoch.py S [--dry-run] [--work F:\\snowball-work] [--summary-edit edit.json]

S is the snowball-mcp commit delivered. The tool does the eight steps of the README section, numbered as there, and
refuses to go on at the first mismatch; a run that stopped is run again with the same S and continues where it
stopped (each step is skipped when what it makes is already there; <work>/epoch-delivery.json says what it did):

  1. S is on main of the source repository and its last `ci.yml` push run on main is completed and green;
  2. <work>/STOP is set (unless it is already there), the launcher's lock is taken (no launcher runs, none can start
     until the delivery ends), the Founder's last push is judged (E385: accepted, or its rejection read by a
     session); then the referee's `control.json` `kill_switch` goes on (main) and no referee run is queued or running;
  3. the referee copy (`bootstrap/`, `vectors/`, `seats/29-tohum-koltuklari.md`, `.github/workflows/bootstrap.yml`) is
     staged in a fresh clone from S's git objects (`git archive`, `core.autocrlf=false`), refusing a stray untracked or
     ignored file, an index entry that is not S's blob and mode, and any CR byte in the staged diff;
  4. `spec/tohum` is replaced by S's in a fresh brain clone as one commit D (nothing else changes; D's `spec/tohum`
     tree is S's), pushed fast-forward to the brain's main;
  5. S's own `seed-epoch` prints D's row, appended to `setup/summary.json` `seed_epochs` (the file's format kept);
     `--summary-edit` may change fields of `targets[]` entries, each naming the value it replaces;
  6. the referee commit is pushed, then the kill switch goes off;
  7. `bootstrap.yml` is dispatched and its signed result must be `kind: seed_update`, `verdict: noop`, `head: D`;
  8. one touch row goes into <work>/pilot-log.md (a seed epoch is a human touch, `27`); STOP is removed only when this
     tool set it. The launcher is not started: the operator starts it.

`--dry-run` resolves S, reads its CI, prints the plan and writes nothing. The tool never reads
<work>/snowball-founder.env. Writes to GitHub go through the operator's own `gh` login (git's `gh` credential helper,
`gh workflow run`), as the launcher's. Exit 0: delivered (or the dry run's plan); 2: refused (the message says what
and what is left as it is); 1: an error.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def _load_launch():
    """The launcher, for its lock, its reads of the referee's results and its dispatch: one source of truth."""
    spec = importlib.util.spec_from_file_location("founder_launch_for_epoch", HERE / "launch.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


launch = _load_launch()
from snowball_bootstrap.decide import NOTHING_TO_JUDGE  # noqa: E402  (launch put seed/bootstrap on sys.path)

SOURCE_REPO = "Okan-wqm/snowball-mcp"
CI_WORKFLOW = "ci.yml"
# README step 3: what of S the referee repository holds, and where (`25` 3).
REFEREE_MAP = (("seed/bootstrap", "bootstrap"), ("seed/bootstrap/vectors", "vectors"),
               ("spec/tohum/29-tohum-koltuklari.md", "seats/29-tohum-koltuklari.md"),
               ("seed/bootstrap/workflow/bootstrap.yml", ".github/workflows/bootstrap.yml"))
BRAIN_MAP = (("spec/tohum", "spec/tohum"),)  # README step 4: nothing else of the brain changes (E180)
SUMMARY, CONTROL = "setup/summary.json", "control.json"
JOURNAL = "epoch-delivery.json"
FILE_MODES = ("100644", "100755")
NO_CRLF = ("-c", "core.autocrlf=false", "-c", "core.eol=lf", "-c", "core.safecrlf=false",
           "-c", "core.fsmonitor=false")
GH_CREDENTIAL = ("-c", launch.GH_CREDENTIAL)
WAIT_POLL_S = 30
ACTIVE = ("queued", "in_progress", "waiting", "pending", "requested")


class Refused(Exception):
    """The delivery stops here: what was found is not what the step needs. Nothing after it ran."""


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def say(msg: str) -> None:
    print(f"[{now()}] {msg}", flush=True)


def git(cwd: Path, *args: str, stdin: bytes | None = None, network: bool = False, timeout: float = 600) -> bytes:
    """Stdout of one git command with no line-end conversion (E242); the operator's identity and `gh` login."""
    argv = ["git", *NO_CRLF, *(GH_CREDENTIAL if network else ()), "-C", str(cwd), *args]
    proc = subprocess.run(argv, input=stdin, capture_output=True, check=False, timeout=timeout,
                          env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args[:2])} failed: {proc.stderr.decode('utf-8', 'replace')[-500:]}")
    return proc.stdout


def head_text(clone: Path, path: str) -> str:
    """A file of the clone's HEAD as git holds it: the bytes a commit has, whatever a checkout made of them."""
    return git(clone, "show", f"HEAD:{path}").decode("utf-8")


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


# ---- S's files, from git objects ---------------------------------------------------------------------------------
def source_files(source: Path, commit: str, src: str, dest: str) -> dict[str, tuple[str, str, bytes]]:
    """{dest path: (mode, blob sha, bytes)} of S's `src` (a folder or one file) placed at `dest`. The bytes are
    `git archive`'s with `core.autocrlf=false`, each checked against the blob `ls-tree` names, so no conversion of the
    archive can pass. Only regular files: a link or a submodule refuses."""
    listed = {}
    for entry in git(source, "ls-tree", "-r", "-z", "--full-tree", commit, "--", src).split(b"\0"):
        if not entry:
            continue
        meta, path = entry.decode("utf-8").split("\t", 1)
        mode, kind, sha = meta.split()
        if path != src and not path.startswith(src + "/"):
            continue
        if kind != "blob" or mode not in FILE_MODES:
            raise Refused(f"{commit[:7]}:{path} is a {kind} of mode {mode}: only regular files are delivered")
        listed[path] = (mode, sha)
    if not listed:
        raise Refused(f"{commit[:7]} has nothing at {src}")
    blob = git(source, "archive", "--format=tar", commit, "--", src)
    out = {}
    with tarfile.open(fileobj=io.BytesIO(blob)) as tar:
        for member in tar.getmembers():
            if not member.isfile() or (member.name != src and not member.name.startswith(src + "/")):
                continue
            if member.name not in listed:
                raise Refused(f"git archive of {commit[:7]} gave {member.name}, which ls-tree does not list")
            data = tar.extractfile(member).read()
            mode, sha = listed[member.name]
            if blob_sha(data) != sha:
                raise Refused(f"git archive of {commit[:7]}:{member.name} is not its blob {sha[:12]} (line ends?)")
            rel = dest if member.name == src else dest + member.name[len(src):]
            out[rel] = (mode, sha, data)
    if len(out) != len(listed):
        raise Refused(f"git archive of {commit[:7]} {src} gave {len(out)} files, ls-tree lists {len(listed)}")
    return out


def expected_files(source: Path, commit: str, mapping) -> dict[str, dict[str, tuple[str, str, bytes]]]:
    return {dest: source_files(source, commit, src, dest) for src, dest in mapping}


# ---- a clone's state ---------------------------------------------------------------------------------------------
def strays(clone: Path) -> list[str]:
    """Every path whose work tree file is not what the index holds: untracked, ignored, changed or deleted beside
    the index (a fresh clone has none; what is staged is the index's own and is held to S by `check_index`). On
    2026-11-02 a `__pycache__` in the referee clone was staged with the copy."""
    out = git(clone, "status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignored", "--no-renames")
    fields = [entry.decode("utf-8", "replace") for entry in out.split(b"\0") if entry]
    return [f for f in fields if f[:2] in ("??", "!!") or f[1:2] != " "]


def index_entries(clone: Path, dest: str) -> dict[str, tuple[str, str]]:
    found = {}
    for entry in git(clone, "ls-files", "-s", "-z", "--", dest).split(b"\0"):
        if entry:
            meta, path = entry.decode("utf-8").split("\t", 1)
            mode, sha, _stage = meta.split()
            if path == dest or path.startswith(dest + "/"):
                found[path] = (mode, sha)
    return found


def check_index(clone: Path, expected: dict[str, dict[str, tuple[str, str, bytes]]]) -> None:
    """Every staged entry under each destination is S's blob with S's mode, and nothing else is there (E242)."""
    problems = []
    for dest, files in expected.items():
        have = index_entries(clone, dest)
        want = {path: (mode, sha) for path, (mode, sha, _data) in files.items()}
        for path in sorted(set(have) | set(want)):
            if have.get(path) != want.get(path):
                problems.append(f"{path}: staged {have.get(path)}, S has {want.get(path)}")
    if problems:
        raise Refused(f"staged blobs are not S's ({len(problems)}): " + "; ".join(problems[:8]))


def staged_paths(clone: Path) -> list[str]:
    out = git(clone, "diff", "--cached", "--name-only", "--no-renames", "-z")
    return [p.decode("utf-8") for p in out.split(b"\0") if p]


def check_staged_only(clone: Path, allowed: tuple[str, ...]) -> None:
    other = [p for p in staged_paths(clone) if not any(p == a or p.startswith(a + "/") for a in allowed)]
    if other:
        raise Refused(f"staged paths outside the delivery: {', '.join(other[:8])}")


def check_no_cr(clone: Path) -> None:
    """README step 3: `git diff --cached | tr -cd '\\r' | wc -c` is 0 before a push."""
    count = git(clone, "diff", "--cached", "--no-renames").count(b"\r")
    if count:
        raise Refused(f"the staged diff has {count} CR bytes (E242): a line-end conversion reached the copy")


def stage(clone: Path, expected: dict[str, dict[str, tuple[str, str, bytes]]]) -> None:
    """Replace each destination with S's files, deletions included, and stage it; then hold the index to S."""
    found = strays(clone)
    if found:
        raise Refused(f"the clone {clone} has stray files: {', '.join(found[:8])}")
    for dest, files in expected.items():
        git(clone, "rm", "-r", "-q", "--cached", "--ignore-unmatch", "--", dest)
        target = clone / dest
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()
        for rel, (mode, _sha, data) in files.items():
            path = clone / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            if mode == "100755":
                path.chmod(0o755)
        git(clone, "add", "-A", "--", dest)
        have = index_entries(clone, dest)
        for rel, (mode, _sha, _data) in files.items():  # Windows has no executable bit: the index carries S's
            if rel in have and have[rel][0] != mode:
                git(clone, "update-index", "--chmod=" + ("+x" if mode == "100755" else "-x"), "--", rel)
    found = strays(clone)
    if found:
        raise Refused(f"files appeared in {clone} beside the copy and are not staged: {', '.join(found[:8])}")
    check_index(clone, expected)


# ---- the referee's two files -------------------------------------------------------------------------------------
def json_doc(raw: str, name: str) -> dict:
    """A JSON object whose bytes are exactly `json.dumps(indent=2, ensure_ascii=False)` and a newline: the format a
    rewrite keeps, so the commit's diff is the change alone."""
    doc = json.loads(raw)
    if not isinstance(doc, dict) or json.dumps(doc, indent=2, ensure_ascii=False) + "\n" != raw:
        raise Refused(f"{name} is not in the format this tool rewrites (indent 2, one newline): edit it by hand")
    return doc


def dumps(doc: dict) -> str:
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def with_kill_switch(raw: str, on: bool) -> str:
    doc = json_doc(raw, CONTROL)
    if not isinstance(doc.get("kill_switch"), bool):
        raise Refused(f"{CONTROL} has no boolean kill_switch")
    doc["kill_switch"] = on
    return dumps(doc)


def with_epoch(raw: str, row: dict, edits: dict | None) -> str:
    """setup/summary.json with the epoch row appended to `seed_epochs` (opened on the first delivery) and the
    `--summary-edit` changes to `targets[]`: `{"targets": {"<id>": {"<field>": {"from": old, "to": new}}}}`. A field
    whose value is not `from`, an id or a field the file does not have, refuses. Nothing else changes."""
    doc = json_doc(raw, SUMMARY)
    epochs = doc.setdefault("seed_epochs", [])
    if not isinstance(epochs, list):
        raise Refused(f"{SUMMARY} seed_epochs is not a list")
    if epochs and isinstance(epochs[-1], dict) and epochs[-1].get("commit") == row["commit"]:
        raise Refused(f"{SUMMARY} already ends with the row of {row['commit'][:7]}")
    epochs.append(row)
    if edits:
        if set(edits) != {"targets"} or not isinstance(edits["targets"], dict):
            raise Refused('--summary-edit holds one key, "targets": {"<id>": {"<field>": {"from": .., "to": ..}}}')
        targets = {t.get("id"): t for t in doc.get("targets") or [] if isinstance(t, dict)}
        for tid, fields in edits["targets"].items():
            if tid not in targets or not isinstance(fields, dict):
                raise Refused(f"--summary-edit: {SUMMARY} has no target {tid!r}")
            for field, change in fields.items():
                if field == "id" or field not in targets[tid]:
                    raise Refused(f"--summary-edit: target {tid!r} has no field {field!r} to change")
                if not isinstance(change, dict) or set(change) != {"from", "to"}:
                    raise Refused(f"--summary-edit: {tid}.{field} needs exactly from and to")
                if targets[tid][field] != change["from"]:
                    raise Refused(f"--summary-edit: {tid}.{field} is {targets[tid][field]!r}, not {change['from']!r}")
                targets[tid][field] = change["to"]
    return dumps(doc)


# ---- what the referee and the CI say (pure, so each refusal is tested) -------------------------------------------
def ci_green(runs: list[dict], sha: str) -> tuple[bool, str]:
    """README step 1: S's newest `ci.yml` run on a push to main is completed and green. A rerun is newer."""
    mine = [r for r in runs or [] if r.get("headSha") == sha and r.get("headBranch") == "main"
            and r.get("event") == "push"]
    if not mine:
        return False, f"no {CI_WORKFLOW} push run on main for {sha[:7]}"
    last = max(mine, key=lambda r: str(r.get("createdAt")))
    if last.get("status") != "completed" or last.get("conclusion") != "success":
        return False, f"{CI_WORKFLOW} run {last.get('databaseId')} is {last.get('status')}/{last.get('conclusion')}"
    return True, f"{CI_WORKFLOW} run {last.get('databaseId')} green"


def founder_chain(log: list[tuple[str, str, str]], epoch_commits: set[str]) -> list[str]:
    """The brain's main from its head down (first parents) to the Founder's last push: the launcher's cost commits and
    earlier seed deliveries above it are not the Founder's push (E385). Empty: no Founder commit in the log."""
    chain = []
    for sha, name, email in log:
        chain.append(sha)
        if (name, email) != (launch.LAUNCHER_NAME, launch.LAUNCHER_EMAIL) and sha not in epoch_commits:
            return chain
    return []


def judgement(chain: list[str], results: list[dict], cycles: list[dict]) -> tuple[str, str]:
    """("ok" | "unjudged" | "unread", why) for the Founder's last push (README step 2, E385). results: the referee's
    newest signed results, newest first; cycles: the launcher's metrics rows. Judged: the newest result evaluated a
    head of the chain. Its verdict is the newest evaluated result on the chain that is not a noop on a commit above the
    push; a rejection (or a verdict no longer among the results) must have been read: a cycle's session started at a
    head of the chain, after the launcher had judged it (E168)."""
    if not chain:
        return "unjudged", "the brain's main has no Founder commit"
    newest = results[0] if results else {}
    if (newest.get("state") or {}).get("last_evaluated_sha") not in chain:
        return "unjudged", f"the referee's newest result has not evaluated {chain[-1][:7]} (or a commit above it)"
    verdict = next((r for r in results if r.get("head") in chain
                    and (r.get("state") or {}).get("last_evaluated_sha") == r.get("head")
                    and (r.get("head") == chain[-1] or r.get("kind") not in NOTHING_TO_JUDGE)), None)
    if verdict is not None and verdict.get("verdict") != "rejected":
        return "ok", f"{chain[-1][:7]}: {verdict.get('kind')}/{verdict.get('verdict')}"
    read = any(c.get("brain_before") in chain for c in cycles if c.get("kind") != launch.INTERVENTION)
    what = "rejected" if verdict is not None else "its verdict is no longer among the recent results"
    if read:
        return "ok", f"{chain[-1][:7]} {what}; a session has read it"
    return "unread", f"{chain[-1][:7]} {what} and no session has read it (E385)"


def delivered(result: dict | None, d: str) -> str | None:
    """README step 7: the signed result on D is the delivery itself. None when it is; else what is wrong."""
    if not result:
        return "no signed result for the dispatched run"
    got = (result.get("kind"), result.get("verdict"), result.get("head"))
    if got != ("seed_update", "noop", d):
        return f"the signed result is {got[0]}/{got[1]}/{str(got[2])[:7]}, not seed_update/noop/{d[:7]}"
    return None


# ---- GitHub, through the operator's gh (the reads and the dispatch are the launcher's own) ------------------------
class GitHub:
    def __init__(self, work: Path, brain: str, referee: str, source_repo: str) -> None:
        self.source_repo, self.referee_repo, self.brain_repo = source_repo, referee, brain

        class Reader(launch.Pilot):
            def stopped(self) -> bool:  # this tool's STOP stops the launcher, not its own wait for the referee
                return False
        self.pilot = Reader(work, brain, referee, "aquaculture_platform")

    def remote(self, repo: str) -> str:
        return f"https://github.com/{repo}.git"

    def ci_runs(self, sha: str) -> list[dict]:
        return launch.gh_json("run", "list", "-R", self.source_repo, "--workflow", CI_WORKFLOW, "--commit", sha,
                              "--limit", "20", "--json", "databaseId,status,conclusion,headSha,headBranch,event,"
                              "createdAt") or []

    def on_main(self, sha: str) -> bool:
        cmp = launch.gh_json("api", f"repos/{self.source_repo}/compare/{sha}...main") or {}
        return cmp.get("status") in ("identical", "ahead")

    def results(self) -> list[dict]:
        """The referee's newest signed results, newest first (the launcher's look-back, E420)."""
        out = []
        for art in self.pilot.state_artifacts()[:launch.VERDICT_LOOKBACK]:
            files = self.pilot.artifact_files(art)
            if "result.json" in files:
                out.append(dict(json.loads(files["result.json"]), _run=(art.get("workflow_run") or {}).get("id")))
        return out

    def active_runs(self) -> int:
        runs = launch.gh_json("run", "list", "-R", self.referee_repo, "--workflow", launch.REFEREE_WORKFLOW,
                              "--limit", "20", "--json", "databaseId,status") or []
        return sum(1 for r in runs if r.get("status") in ACTIVE)

    def dispatch(self, timeout_s: int) -> tuple[dict, dict | None]:
        """Dispatch the referee on main, wait for that run and return it with its signed result."""
        run = self.pilot.dispatch_referee(timeout_s)
        if run.get("conclusion") != "success" or not run.get("id"):
            return run, None
        for _ in range(10):  # the artifact can be listed a little after the run ends
            for result in self.results():
                if str(result.get("_run")) == str(run["id"]):
                    return run, result
            time.sleep(15)
        return run, None


# ---- the delivery ------------------------------------------------------------------------------------------------
class Delivery:
    def __init__(self, s: str, work: Path, source: Path, gh, scratch: Path, summary_edit: dict | None = None,
                 note: str = "", wait_s: int = 4 * 3600, referee_timeout_s: int = 90 * 60,
                 epoch_code: Path | None = None) -> None:
        self.s_arg, self.work, self.source, self.gh, self.scratch = s, work, source, gh, scratch
        self.summary_edit, self.note = summary_edit, note
        self.wait_s, self.referee_timeout_s = wait_s, referee_timeout_s
        self.epoch_code = epoch_code  # where seed-epoch runs from; None: S's own seed/bootstrap (tests pass the seed's)
        self.journal_path = work / JOURNAL
        self.journal: dict = {}
        self.lock = launch.LauncherLock(work / launch.LOCK_FILE)

    # -- the journal: what this tool did, so a second run continues and removes only its own STOP
    def save(self, **fields) -> None:
        self.journal.update(fields)
        tmp = self.journal_path.with_name(JOURNAL + ".tmp")
        tmp.write_text(json.dumps(self.journal, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(tmp, self.journal_path)

    def load(self, s: str) -> None:
        if not self.journal_path.is_file():
            self.journal = {}
            return
        self.journal = json.loads(self.journal_path.read_text(encoding="utf-8"))
        if self.journal.get("source_commit") != s:
            raise Refused(f"{self.journal_path} is an unfinished delivery of {self.journal.get('source_commit')}: run "
                          "it again with that commit, or read it and remove it")

    # -- step 1
    def resolve(self) -> str:
        s = git(self.source, "rev-parse", "--verify", f"{self.s_arg}^{{commit}}").decode().strip()
        ok, why = ci_green(self.gh.ci_runs(s), s)
        if not ok:
            raise Refused(f"step 1: {why}")
        if not self.gh.on_main(s):
            raise Refused(f"step 1: {s[:7]} is not on {SOURCE_REPO} main")
        self.ci = why
        return s

    def plan(self, s: str) -> str:
        stop = "is already there (left in place)" if (self.work / "STOP").exists() else "is set (removed at the end)"
        running = "exists" if (self.work / launch.RUNNING_FILE).exists() else "none"
        edits = f"; targets edits {json.dumps(self.summary_edit, ensure_ascii=False)}" if self.summary_edit else ""
        lines = [f"Seed epoch of snowball-mcp {s[:7]} ({self.ci}); work {self.work}",
                 f"  journal: {'continues ' + str(self.journal) if self.journal else 'none, a new delivery'}",
                 f"  2. STOP {stop}, the launcher's lock is taken (RUNNING {running}), the Founder's last push must be "
                 f"judged (E385); {self.gh.referee_repo} {CONTROL} kill_switch true on main, no referee run going",
                 "  3. stage " + ", ".join(f"{a} -> {b}" for a, b in REFEREE_MAP) + " from git objects (no strays, "
                 "S's blobs and modes, 0 CR)",
                 f"  4. brain: spec/tohum = {s[:7]}:spec/tohum, one commit D on main, D's tree checked",
                 f"  5. seed-epoch row of D appended to {SUMMARY}{edits}",
                 "  6. push the referee, then kill_switch false",
                 "  7. dispatch bootstrap.yml: the signed result must be seed_update/noop/D",
                 "  8. touch row in pilot-log.md; STOP removed only if step 2 set it; start the launcher yourself"]
        return "\n".join(lines)

    # -- step 2
    def stop_and_wait(self, s: str) -> None:
        stop = self.work / "STOP"
        if not stop.exists():
            self.save(source_commit=s, stop_created=True)
            stop.write_text(f"seed epoch delivery of {s} ({now()})\n", encoding="utf-8")
        else:
            self.save(source_commit=s, stop_created=bool(self.journal.get("stop_created")))
        deadline = time.monotonic() + self.wait_s
        while not self.lock.acquire():
            if time.monotonic() > deadline:
                raise Refused("step 2: the launcher still runs (its lock is held) after the wait")
            say("step 2: STOP is set; waiting for the launcher to end its step")
            time.sleep(WAIT_POLL_S)

    def judged(self, brain: Path, epoch_commits: set[str]) -> str:
        log = [tuple(line.split("\x1f")) for line in git(brain, "log", "--first-parent", "-n", "300",
                                                          "--format=%H%x1f%cn%x1f%ce", "HEAD").decode().splitlines()]
        chain = founder_chain(log, epoch_commits)
        metrics = self.work / "pilot-metrics.jsonl"
        cycles = [row for row in map(launch._json_or_none,
                                     metrics.read_text(encoding="utf-8").splitlines() if metrics.is_file() else [])
                  if isinstance(row, dict)]
        deadline = time.monotonic() + self.wait_s
        while True:
            state, why = judgement(chain, self.gh.results(), cycles)
            if state == "ok":
                return why
            if state == "unjudged" and self.gh.active_runs() and time.monotonic() < deadline:
                say(f"step 2: {why}; a referee run is going, waiting")
                time.sleep(WAIT_POLL_S)
                continue
            hint = ("start the launcher for one cycle (it judges an unjudged push first, E168)" if state == "unjudged"
                    else "let one launcher cycle run so a session reads the rejection")
            raise Refused(f"step 2: {why}: {hint}, then run this again")

    # -- clones
    def clone(self, repo: str, name: str) -> Path:
        dest = Path(tempfile.mkdtemp(prefix=name + "-", dir=self.scratch))  # always fresh, never a used clone
        git(self.scratch, "clone", "-q", "-c", "core.autocrlf=false", "-c", "core.eol=lf", "--branch", "main",
            self.gh.remote(repo), str(dest), network=True)
        return dest

    def commit(self, clone: Path, message: str, allow_empty: bool = False) -> str:
        git(clone, "commit", "-q", *(["--allow-empty"] if allow_empty else []), "-m", message)
        return git(clone, "rev-parse", "HEAD").decode().strip()

    def push(self, clone: Path) -> None:
        git(clone, "push", "-q", "origin", "HEAD:main", network=True)

    def control(self, referee: Path, on: bool, s: str) -> str | None:
        """Steps 3 and 7: the kill switch; the commit, or None when it already was so."""
        if not git(referee, "ls-files", "--", CONTROL).strip():
            raise Refused(f"the referee repository has no {CONTROL}")
        raw = head_text(referee, CONTROL)
        if json_doc(raw, CONTROL).get("kill_switch") is on:
            return None
        (referee / CONTROL).write_text(with_kill_switch(raw, on), encoding="utf-8", newline="")
        git(referee, "add", "--", CONTROL)
        check_staged_only(referee, (CONTROL,))
        check_no_cr(referee)
        sha = self.commit(referee, f"Seed epoch {s[:7]}: kill switch {'on' if on else 'off'}")
        self.push(referee)
        return sha

    def epoch_row(self, brain: Path, d: str, s: str, files: dict) -> dict:
        """Step 5: S's own `seed-epoch`, run from S's seed/bootstrap written out of git objects, with no
        bytecode left behind; the row must name D and no brain seed/ (E150)."""
        code = self.epoch_code
        if code is None:
            code = Path(tempfile.mkdtemp(prefix="s-bootstrap-", dir=self.scratch))
            for rel, (_mode, _sha, data) in files["bootstrap"].items():
                path = code / rel[len("bootstrap/"):]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
        env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONHOME")}
        proc = subprocess.run([sys.executable, "-X", "utf8", "-B", "-m", "snowball_bootstrap", "seed-epoch", "--brain",
                               str(brain), "--commit", d, "--source", str(self.source), "--source-commit", s],
                              cwd=code, capture_output=True, check=False, timeout=600,
                              env={**env, "PYTHONDONTWRITEBYTECODE": "1"})
        if proc.returncode != 0:
            raise Refused(f"step 5: seed-epoch failed: {proc.stderr.decode('utf-8', 'replace')[-600:]}")
        row = json.loads(proc.stdout)
        hex64 = re.compile(r"[0-9a-f]{64}")
        if (row.get("commit") != d or row.get("seed_sha256") is not None
                or not hex64.fullmatch(str(row.get("spec_tohum_sha256")))
                or not hex64.fullmatch(str(row.get("bootstrap_sha256")))):
            raise Refused(f"step 5: the seed-epoch row is not D's delivery: {row}")
        return row

    # -- the run
    def run(self, dry_run: bool = False) -> int:
        """The delivery, or Refused. A refusal before the kill switch went on leaves the work folder as it was found
        (the STOP this run set and its journal go); a later one leaves everything, and a second run continues."""
        try:
            return self._run(dry_run)
        except Refused:
            if not self.journal.get("kill_on") and self.journal.get("stop_created"):
                (self.work / "STOP").unlink(missing_ok=True)
                self.journal_path.unlink(missing_ok=True)
                self.journal = {}
            raise

    def _run(self, dry_run: bool) -> int:
        s = git(self.source, "rev-parse", "--verify", f"{self.s_arg}^{{commit}}").decode().strip()
        self.load(s)
        s = self.resolve()
        if dry_run:
            print(self.plan(s))
            return 0
        say(f"step 1: {s[:7]} on main, {self.ci}")
        self.stop_and_wait(s)
        try:
            self.deliver(s)
        finally:
            self.lock.release()
        return 0

    def deliver(self, s: str) -> None:
        j = self.journal
        self.scratch.mkdir(parents=True, exist_ok=True)
        referee, brain = self.clone(self.gh.referee_repo, "referee"), self.clone(self.gh.brain_repo, "brain")
        summary_raw = head_text(referee, SUMMARY)
        epochs = json_doc(summary_raw, SUMMARY).get("seed_epochs") or []
        if not j.get("kill_on"):
            say("step 2: " + self.judged(brain, {str(e.get("commit")) for e in epochs if isinstance(e, dict)}))
            if json_doc(head_text(referee, CONTROL), CONTROL).get("kill_switch"):
                raise Refused("step 2: the kill switch is already on and this tool did not set it: whose stop is it?")
            self.save(kill_on=self.control(referee, True, s))
            say(f"step 2: kill switch on ({j['kill_on'][:7]})")
        elif not j.get("kill_off") and not json_doc(head_text(referee, CONTROL),
                                                     CONTROL).get("kill_switch"):
            raise Refused("step 2: this delivery set the kill switch on, and someone turned it off: look first")
        deadline = time.monotonic() + self.wait_s
        while self.gh.active_runs():
            if time.monotonic() > deadline:
                raise Refused("step 2: a referee run is still queued or running after the wait")
            say("step 2: a referee run is queued or running; waiting")
            time.sleep(WAIT_POLL_S)
        last = epochs[-1].get("commit") if epochs and isinstance(epochs[-1], dict) else None
        if not j.get("synced"):
            expected = expected_files(self.source, s, REFEREE_MAP)
            stage(referee, expected)
            copy_paths = tuple(dest for _src, dest in REFEREE_MAP)
            check_staged_only(referee, copy_paths)
            check_no_cr(referee)  # the whole copy is checked before anything reaches the brain
            say(f"step 3: referee copy staged from {s[:7]} ({sum(map(len, expected.values()))} files)")
            d = self.deliver_brain(brain, s)
            row = self.epoch_row(brain, d, s, expected)
            if last == d:
                raise Refused(f"step 5: {SUMMARY} already names {d[:7]} but the journal has no referee commit")
            (referee / SUMMARY).write_text(with_epoch(summary_raw, row, self.summary_edit), encoding="utf-8",
                                           newline="")
            git(referee, "add", "--", SUMMARY)
            check_index(referee, expected)
            check_staged_only(referee, copy_paths + (SUMMARY,))
            check_no_cr(referee)
            edited = "; targets edited (--summary-edit)" if self.summary_edit else ""
            sha = self.commit(referee, f"Seed epoch: referee synced to snowball-mcp main {s[:7]}; seed_epochs row for "
                                       f"brain {d[:7]}{edited}")
            self.push(referee)
            self.save(synced=sha)
            say(f"step 5: seed_epochs row for {d[:7]} pushed ({sha[:7]})")
        elif last != j.get("D"):
            raise Refused(f"step 5: the journal's referee commit is pushed but {SUMMARY} ends with {last}")
        if not j.get("kill_off"):
            self.save(kill_off=self.control(referee, False, s) or "already-off")
            say("step 6: kill switch off")
        if not j.get("verified"):
            run, result = self.gh.dispatch(self.referee_timeout_s)
            problem = delivered(result, j["D"])
            if problem:
                raise Refused(f"step 7: referee run {run.get('id')} ({run.get('conclusion')}): {problem}; the kill "
                              "switch is off and STOP stays: fix the row or the push and run this again")
            self.save(verified=str(run["id"]))
            say(f"step 7: run {run['id']}: seed_update/noop/{j['D'][:7]}")
        self.finish(s)

    def deliver_brain(self, brain: Path, s: str) -> str:
        """Step 5: D, once. A journal's D must still be the brain's head with S's tree; else a fresh commit."""
        want = git(self.source, "rev-parse", f"{s}:spec/tohum").decode().strip()
        head = git(brain, "rev-parse", "HEAD").decode().strip()
        if self.journal.get("D"):
            if head != self.journal["D"] or git(brain, "rev-parse", f"{head}:spec/tohum").decode().strip() != want:
                raise Refused(f"step 4: the brain's main is {head[:7]}, not the journal's D {self.journal['D'][:7]}")
            return head
        expected = expected_files(self.source, s, BRAIN_MAP)
        stage(brain, expected)
        check_staged_only(brain, ("spec/tohum",))
        check_no_cr(brain)
        d = self.commit(brain, f"Tohum dönemi: snowball-mcp {s[:7]}", allow_empty=not staged_paths(brain))
        changed = git(brain, "diff", "--name-only", "--no-renames", head, d).decode().splitlines()
        tree = git(brain, "rev-parse", f"{d}:spec/tohum").decode().strip()
        if tree != want or any(not p.startswith("spec/tohum/") for p in changed):
            raise Refused(f"step 4: D's spec/tohum tree is {tree[:12]}, S's {want[:12]}; changed {changed[:5]}")
        self.push(brain)
        self.save(D=d)
        say(f"step 4: D = {d[:7]} on the brain's main (spec/tohum tree {tree[:12]})")
        return d

    def finish(self, s: str) -> None:
        """Step 8: the touch row once, then STOP only when this tool set it, then the journal goes."""
        j = self.journal
        if not j.get("touched"):
            edits = (f", targets: {json.dumps(self.summary_edit['targets'], ensure_ascii=False)}"
                     if self.summary_edit else "")
            row = (f"\n- {now()} operatör: tohum dönemi teslim edildi (insan dokunuşu, `27`; `deliver_epoch.py`). "
                   f"Kaynak snowball-mcp `{s[:7]}` (CI: {self.ci}); beyin `{j['D'][:7]}`; hakem `{j['kill_on'][:7]}` "
                   f"(kill switch açık) → `{j['synced'][:7]}` (senkron, seed_epochs satırı{edits}) → kill switch "
                   f"kapalı; doğrulama {j['verified']}: seed_update/noop/`{j['D'][:7]}`."
                   + (f" {self.note}" if self.note else "") + "\n")
            with (self.work / "pilot-log.md").open("a", encoding="utf-8") as fh:  # as the launcher writes it
                fh.write(row)
            self.save(touched=True)
        if j.get("stop_created"):
            (self.work / "STOP").unlink(missing_ok=True)
            say("step 8: STOP removed (this delivery set it); start the launcher")
        else:
            say("step 8: STOP was there before this delivery and stays")
        self.journal_path.unlink(missing_ok=True)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("commit", help="S: the snowball-mcp commit delivered (green CI on main)")
    p.add_argument("--work", type=Path, default=Path(r"F:\snowball-work"))
    p.add_argument("--source", type=Path, default=ROOT, help="a snowball-mcp clone holding S (its git objects)")
    p.add_argument("--source-repo", default=SOURCE_REPO)
    p.add_argument("--brain", default="Okan-wqm/snowball-rehearsal-brain")
    p.add_argument("--referee", default="Okan-wqm/snowball-rehearsal-referee")
    p.add_argument("--summary-edit", type=Path, help="JSON: changes to targets[] entries, each with from and to")
    p.add_argument("--note", default="", help="one sentence for the touch row (what the epoch carries)")
    p.add_argument("--wait", type=int, default=4 * 3600, help="seconds to wait for the launcher and the referee")
    p.add_argument("--referee-timeout", type=int, default=90 * 60)
    p.add_argument("--dry-run", action="store_true", help="resolve S, read its CI, print the plan, write nothing")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.work.is_dir():
        sys.exit(f"{args.work} is not a folder")
    edit = json.loads(args.summary_edit.read_text(encoding="utf-8")) if args.summary_edit else None
    scratch = Path(tempfile.mkdtemp(prefix="snowball-epoch-"))
    delivery = Delivery(args.commit, args.work, args.source, GitHub(args.work, args.brain, args.referee,
                                                                     args.source_repo),
                        scratch, edit, args.note, args.wait, args.referee_timeout)
    try:
        return delivery.run(dry_run=args.dry_run)
    except (Refused, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"{'refused' if isinstance(exc, Refused) else 'error'}: {exc}", file=sys.stderr)
        if delivery.journal:
            print(f"left as it is: {delivery.journal}; run this again with the same commit", file=sys.stderr)
        else:
            print("nothing was written to GitHub or the work folder", file=sys.stderr)
        return 2 if isinstance(exc, Refused) else 1
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
