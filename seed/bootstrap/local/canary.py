"""The rival canary (register E126, E311): does the seed rival catch a defect nobody told it about? Stdlib only.

An operator-side measurement, never a verdict: it changes neither the rival nor the referee, signs nothing, and pushes
nothing anywhere. It takes the last accepted commit of the brain (the signed state's ``last_accepted_sha``), plants one
known defect from ``canary_catalog.json`` into a copy of it, and has the push judged the way the referee judges one:

1. ``pull`` (the referee's own command) reads the planted commit from a local repository the canary made, never from
   the brain's remote, with the signed state, so the request carries the same pages and open claims;
2. the plant's hidden oracle, a command that passes on the accepted code and fails on the planted copy, proves the
   defect is real; it runs in the referee's container and is never shown to the rival;
3. the tests that cover the planted file (and, for a micro-feature named, its seed vectors) run on the planted copy:
   a plant they catch never reaches the rival in the live loop, so it is not sent here either;
4. ``rival`` (the referee's own command, so the same model, effort, turns, cap and prompt from the referee repository's
   ``bootstrap.json`` and ``seats/``) reviews the push; the canary keeps the request and the CLI's stream, which
   ``rival.py`` keeps nowhere (its run directory is temporary);
5. every reproducer runs with the referee's code (``reproduce.run_reproducers``) on the planted head and on the accepted
   base, and the referee's ``decide`` says which attempts prove a defect: a plant is caught when an attempt proves one
   whose symptom does not show on the accepted base.

Controls are pushes without a defect (a change that alters no behaviour); an attempt the referee would accept on one is
a false refutation. Recall is reported per kind with the seed's one-sided Clopper-Pearson lower bound (``cp_lower``,
the `29a` vectors' alpha, 1 - ``confidence_level`` 0.90 of `18a`; `19`).

    cd seed/bootstrap && python local/canary.py --work F:/snowball-work/canary --referee <referee clone>
    cd seed/bootstrap && python local/canary.py --work F:/snowball-work/canary --referee <referee clone> --live

Without ``--live`` the rival is a fake that knows each plant's oracle and always catches it: a positive control of the
whole measurement chain (containers included) that spends nothing. With ``--live`` the real rival runs through the
operator's own ``claude`` login. Everything a run writes goes under ``--work`` (a private folder, never the repository):
``brain.git`` (a read-only mirror of the brain), ``plants.git`` (the planted commits), and ``runs/<stamp>/`` with one
folder per entry (``record.json``, the pulled request, ``rival/rival.json``, ``rival/transcript/``) plus
``results.json`` and ``report.md``. Not measured here, by construction: a defect hidden among other changes (the diff
is the plant alone), a plant the covering tests catch, the rival on a spec push.
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import datetime
import hashlib
import json
import shlex
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol

HERE = Path(__file__).resolve().parent
BOOT = HERE.parent
sys.path.insert(0, str(BOOT))
sys.path.insert(0, str(BOOT / "tests"))

from snowball_bootstrap import cli, config, gitio, reproduce, rival, stages, state as st, vectors  # noqa: E402
from snowball_bootstrap.container import RunResult  # noqa: E402
from snowball_bootstrap.decide import decide  # noqa: E402  (the referee's own rule of what proves a defect)
from snowball_bootstrap.treehash import extract  # noqa: E402
from helpers import cp_lower  # noqa: E402  (the seed's one-sided Clopper-Pearson lower bound, held to `29a`)

CATALOG = HERE / "canary_catalog.json"
CATALOG_SCHEMA = "snowball-rival-canary-catalog/1"
RESULTS_SCHEMA = "snowball-rival-canary-results/1"
CONTROL = "control"
ALPHA = float(json.loads((BOOT / "vectors" / "vectors.json").read_text(encoding="utf-8"))["cp_lower"]["alpha"])
FIRST_BATCH = (6, 2)  # plants and controls of one run unless the operator names more (E126's first batch)
MAX_USD = 12.0  # the run stops before a review once the rival's booked spend reaches this (a runaway brake)
FALSE_REFUTATION = ("caught", "proven_on_base")  # a control the referee would reject
SYMPTOM, CORRECT = "canary-symptom", "canary-correct"
PLANTER = {"GIT_AUTHOR_NAME": "canary", "GIT_AUTHOR_EMAIL": "canary@example.invalid",
           "GIT_AUTHOR_DATE": "2026-01-01T00:00:00Z", "GIT_COMMITTER_NAME": "canary",
           "GIT_COMMITTER_EMAIL": "canary@example.invalid", "GIT_COMMITTER_DATE": "2026-01-01T00:00:00Z"}


class CanaryError(RuntimeError):
    """The measurement cannot be made as asked (a stale anchor, a bad catalog, a state that is no accepted commit)."""


class Runner(Protocol):
    def run(self, cmd: str, *, cwd: str = ".", stdin: bytes = b"", timeout_s: int) -> RunResult: ...


# ---- the catalog ------------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Entry:
    """One push to judge: a plant (a defect of ``kind``, with its oracle) or a control (``kind`` "control", no defect).
    ``old`` must occur exactly once in ``path`` at the base; ``suite`` names the manifest tests covering the file and
    ``mfs`` the micro-features whose seed vectors cover it."""
    id: str
    kind: str
    path: str
    old: str
    new: str
    suite: tuple[str, ...]
    mfs: tuple[int, ...]
    oracle: str | None
    why: str

    @property
    def control(self) -> bool:
        return self.kind == CONTROL


def oracle_reproducer(entry: Entry) -> dict[str, Any]:
    """The fake rival's reproducer for a plant: the oracle, run where the planted file exists (on the referee's empty
    tree it prints nothing, so it is not tautological), its symptom what a failing oracle prints."""
    cmd = (f"if [ -f {shlex.quote(entry.path)} ]; then if ( {entry.oracle} ) >/dev/null 2>&1; "
           f"then echo {CORRECT}; else echo {SYMPTOM}; fi; fi")
    return {"cmd": cmd, "expect_stdout_contains": SYMPTOM, "correct_stdout_contains": CORRECT}


def load_catalog(path: Path = CATALOG) -> tuple[dict[str, str], list[Entry]]:
    """The defect kinds (name -> what it stands for) and the entries, checked whole: a bad catalog stops the run."""
    doc = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict) or doc.get("schema") != CATALOG_SCHEMA:
        raise CanaryError(f"{path.name}: schema must be {CATALOG_SCHEMA}")
    kinds = doc.get("kinds")
    if not isinstance(kinds, dict) or not kinds or CONTROL in kinds:
        raise CanaryError(f"{path.name}: kinds must name the defect kinds (and not {CONTROL!r})")
    entries, seen = [], set()
    for raw in doc.get("entries", []):
        entry = Entry(id=raw["id"], kind=raw["kind"], path=raw["path"], old=raw["old"], new=raw["new"],
                      suite=tuple(raw["suite"]), mfs=tuple(raw.get("mfs", [])), oracle=raw.get("oracle"),
                      why=raw["why"])
        where = f"{path.name}: {entry.id}"
        if entry.id in seen:
            raise CanaryError(f"{where}: id used twice")
        seen.add(entry.id)
        if entry.kind != CONTROL and entry.kind not in kinds:
            raise CanaryError(f"{where}: unknown kind {entry.kind!r}")
        if not entry.old or entry.old == entry.new:
            raise CanaryError(f"{where}: old must be non-empty and differ from new")
        if not entry.suite:
            raise CanaryError(f"{where}: name the manifest tests that cover {entry.path}")
        if entry.control and entry.oracle is not None:
            raise CanaryError(f"{where}: a control has no defect, so no oracle")
        if not entry.control:
            if not entry.oracle:
                raise CanaryError(f"{where}: a plant needs its oracle")
            if len(oracle_reproducer(entry)["cmd"]) > rival.MAX_CMD_CHARS:
                raise CanaryError(f"{where}: the oracle is too long for a reproducer ({rival.MAX_CMD_CHARS} characters)")
        entries.append(entry)
    if not any(e.control for e in entries) or all(e.control for e in entries):
        raise CanaryError(f"{path.name}: needs plants and controls")
    return dict(kinds), entries


def plant(text: str, entry: Entry) -> str:
    found = text.count(entry.old)
    if found != 1:
        raise CanaryError(f"{entry.id}: its anchor occurs {found} times in {entry.path} at this base: re-anchor it")
    return text.replace(entry.old, entry.new)


def touched(text: str, entry: Entry) -> tuple[int, int]:
    """The head's lines the plant wrote (1-based, both ends); for a deletion, the two lines it now lies between."""
    first = text.count("\n", 0, text.index(entry.old)) + 1
    count = entry.new.count("\n") + (0 if entry.new.endswith("\n") else 1)
    return (first - 1, first) if not entry.new else (first, first + max(count, 1) - 1)


# ---- git: a read-only mirror of the brain and the canary's own planted commits ------------------------------------------

def _git(repo: Path, *args: str, stdin: bytes | None = None, env: dict[str, str] | None = None) -> str:
    proc = subprocess.run(["git", *gitio.SAFE_CONFIG, "-C", str(repo), *args], input=stdin, capture_output=True,
                          env={**gitio._env(), **(env or {})}, check=False)
    if proc.returncode != 0:
        raise CanaryError(f"git {args[0]} failed: {proc.stderr.decode('utf-8', 'replace')[:300]}")
    return proc.stdout.decode().strip()


def plant_store(work: Path, mirror: Path) -> Path:
    """``plants.git``: the canary's own repository, borrowing the mirror's objects; the mirror is never written."""
    store = work / "plants.git"
    if not (store / "HEAD").exists():
        store.mkdir(parents=True, exist_ok=True)
        _git(store, "init", "--bare", "--quiet")
    (store / "objects" / "info" / "alternates").write_text((mirror / "objects").resolve().as_posix() + "\n",
                                                           encoding="utf-8", newline="\n")
    return store


def plant_commit(store: Path, base: str, entry: Entry) -> tuple[str, tuple[int, int]]:
    """A commit on ``base`` that changes ``entry.path`` alone, and the lines the plant wrote there."""
    raw = gitio.file_at(store, base, entry.path)
    if raw is None:
        raise CanaryError(f"{entry.id}: {entry.path} is not a file at {base}")
    text = raw.decode("utf-8")
    mode = _git(store, "ls-tree", base, "--", entry.path).split()[0]
    with tempfile.TemporaryDirectory(prefix="canary-index-") as tmp:
        index = {"GIT_INDEX_FILE": str(Path(tmp) / "index")}
        _git(store, "read-tree", base, env=index)
        blob = _git(store, "hash-object", "-w", "--stdin", stdin=plant(text, entry).encode("utf-8"))
        _git(store, "update-index", "--cacheinfo", f"{mode},{blob},{entry.path}", env=index)
        tree = _git(store, "write-tree", env=index)
    sha = _git(store, "commit-tree", tree, "-p", base, "-m", f"canary: {entry.id}", env=PLANTER)
    return sha, touched(text, entry)


# ---- what the referee's own code says --------------------------------------------------------------------------------

def proven(meta: dict[str, Any], rival_doc: dict[str, Any], head_results: list[dict[str, Any]], policy: config.Policy,
           ) -> set[int]:
    """The attempts the referee's ``decide`` holds proven on the head (`29`, E260): only this rival's reproducers are
    judged (the state's own were not part of the plant), and the tests count as green, whose own result the canary
    keeps apart (``check_suite``)."""
    meta = copy.deepcopy(meta)
    meta["state_repro"] = []
    run = {"green": True, "tests": [{"id": "canary", "cmd_sha256": "", "ok": True, "output_tail": ""}],
           "vectors": [], "controls": [], "licenses": [], "module_less": []}
    jobs = {"getir": "success", "kos": "success", "cagir": "success", "yeniden": "success"}
    result = decide(meta, run, rival_doc, head_results, jobs, policy.rival_min_attempts, policy.repeat_reject_limit,
                    state_repro=[], table=stages.load(0))
    keys = {r["ref"].removeprefix("repro:") for r in result["reasons"] if r["kind"] == "refutation_reproduced"}
    return {r["attempt_index"] for r in head_results if r["key"] in keys}


def classify(entry: Entry, rival_doc: dict[str, Any], proofs: set[int], on_base: list[dict[str, Any]],
             lines: tuple[int, int]) -> dict[str, Any]:
    """What the rival did with one push. ``caught``: an attempt the referee holds proven whose symptom does not show
    on the accepted base; ``proven_on_base``: proven, but the base shows the symptom too (not this push's defect);
    ``refuted_unproven``: a refutation without a proof; ``unresolved``: no verdict (a turn or budget limit, a malformed
    verdict, a refusal); ``outage``: the CLI or its login failed, nothing was judged (left out of every rate)."""
    reasons = [str(r) for r in rival_doc.get("reasons", [])]
    verdict = rival_doc.get("verdict")
    attempts = rival_doc.get("attempts", []) if verdict in ("refuted", "not_refuted") else []
    base_shown = {r["attempt_index"]: r["shown"] for r in on_base}
    new = sorted(i for i in proofs if not base_shown[i])
    old = sorted(i for i in proofs if base_shown[i])
    if any(r.startswith("api_error") for r in reasons):
        outcome = "outage"
    elif verdict not in ("refuted", "not_refuted"):
        outcome = "unresolved"
    elif new:
        outcome = "caught"
    elif old:
        outcome = "proven_on_base"
    elif verdict == "refuted":
        outcome = "refuted_unproven"
    else:
        outcome = "not_refuted"
    pointed = any(ref["path"] == entry.path and ref["line_start"] <= lines[1] and ref["line_end"] >= lines[0]
                  for a in attempts for ref in a["evidence_refs"])
    return {"outcome": outcome, "proven_new": new, "proven_on_base": old, "attempts": len(attempts),
            "with_reproducer": sum(1 for a in attempts if "reproducer" in a), "pointed_at_plant": pointed,
            "reasons": reasons}


def _rate(x: int, n: int) -> dict[str, Any]:
    return {"x": x, "n": n, "rate": round(x / n, 4) if n else None,
            "cp_lower": round(cp_lower(x, n, ALPHA), 4) if n else None}


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Recall per kind and overall over the plants the rival judged (an outage is not judged), false refutations over
    the controls it judged, and what the reviews cost (the CLI's list-price estimate, outages included)."""
    judged = [r for r in records if r["status"] == "reviewed" and r["outcome"] != "outage"]
    plants = [r for r in judged if r["kind"] != CONTROL]
    controls = [r for r in judged if r["kind"] == CONTROL]
    by_kind = {kind: _rate(sum(r["outcome"] == "caught" for r in plants if r["kind"] == kind),
                           sum(1 for r in plants if r["kind"] == kind)) for kind in sorted({r["kind"] for r in plants})}
    reviewed = [r for r in records if r["status"] == "reviewed"]
    judged_ids = {r["id"] for r in judged}
    return {"alpha": ALPHA,
            "recall": {"overall": _rate(sum(r["outcome"] == "caught" for r in plants), len(plants)), "by_kind": by_kind},
            "pointed_at_plant": {"x": sum(r["pointed_at_plant"] for r in plants), "n": len(plants)},
            "false_refutations": {"x": sum(r["outcome"] in FALSE_REFUTATION for r in controls), "n": len(controls)},
            "cost_usd_micros": sum(r["cost_usd_micros"] for r in reviewed),
            "turns": sum(r["turns"] for r in reviewed), "reviews": len(reviewed),
            "not_judged": {r["id"]: r["outcome"] or r["status"] for r in records if r["id"] not in judged_ids}}


# ---- the rival: the real one through the referee's command, or the oracle-informed fake --------------------------------

Reviewer = Callable[[Entry, Path, Path], dict[str, Any]]


@contextlib.contextmanager
def _log(path: Path):
    """A referee command's step outputs and notices go to a file in the entry's folder, not to the console."""
    with open(path, "w", encoding="utf-8") as log, contextlib.redirect_stdout(log):
        yield


@contextlib.contextmanager
def keep_transcript(dest: Path):
    """Every rival CLI run inside the block leaves its request, system prompt, arguments and stream-json output in
    ``dest``. The call is passed through unchanged: ``rival._run_cli`` is wrapped, not replaced, and restored."""
    original = rival._run_cli

    def tee(argv: list[str], stdin: str, cwd: Path, env: dict[str, str], on_init: Any = None) -> tuple[int, str]:
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "request.txt").write_text(stdin, encoding="utf-8", newline="\n")
        shutil.copyfile(Path(cwd).parent / "system.txt", dest / "system.txt")
        (dest / "argv.json").write_text(json.dumps(argv[1:]), encoding="utf-8")  # the binary's path left out
        code, out = original(argv, stdin, cwd, env, on_init=on_init)
        (dest / "transcript.jsonl").write_text(out, encoding="utf-8", newline="\n")
        return code, out

    rival._run_cli = tee
    try:
        yield
    finally:
        rival._run_cli = original


def live_reviewer(root: Path, claude: str | None) -> Reviewer:
    """The referee's ``rival`` command over the pulled request alone: the entry is not passed on (no hint)."""
    def review(_entry: Entry, pulled: Path, out: Path) -> dict[str, Any]:
        argv = ["rival", "--root", str(root), "--pulled", str(pulled), "--work", str(out / "work"), "--out", str(out)]
        out.mkdir(parents=True, exist_ok=True)
        with keep_transcript(out / "transcript"), _log(out / "rival.log"):
            code = cli.main(argv + (["--claude", claude] if claude else []))
        if code != 0 or not (out / "rival.json").is_file():
            raise CanaryError(f"the rival command stopped (exit {code}) before writing rival.json")
        return json.loads((out / "rival.json").read_text(encoding="utf-8"))
    return review


def first_changed_line(diff: str, path: str) -> int:
    """The head line where the diff first changes ``path`` (for a deletion, the line now after it), read from its first
    hunk the way a reviewer of the diff would."""
    lines = diff.split("\n")
    start = lines.index(f"diff --git a/{path} b/{path}")
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("@@ "):
            line = int(lines[i].split("+")[1].split(",")[0].split(" ")[0])
            for body in lines[i + 1:]:
                if body[:1] in ("+", "-"):
                    return max(line, 1)
                line += 1
    raise CanaryError(f"the diff does not change {path}")


def oracle_reviewer(entry: Entry, pulled: Path, out: Path) -> dict[str, Any]:
    """The dry run's fake rival: it refutes every plant with its own oracle and finds nothing in a control. Its verdict
    passes the referee's validator like the real rival's must."""
    meta = json.loads((pulled / "meta.json").read_text(encoding="utf-8"))
    tree = out / "tree"
    tar = (pulled / "brain.tar").read_bytes()
    extract(tar, tree, len(tar))
    raw: dict[str, Any] = {"verdict": "not_refuted", "attempts": []}
    if not entry.control:
        line = first_changed_line((pulled / "diff.patch").read_text(encoding="utf-8"), entry.path)
        raw = {"verdict": "refuted", "attempts": [{
            "claim": f"{entry.path}:{line} breaks what its oracle checks.",
            "evidence_refs": [{"path": entry.path, "line_start": line, "line_end": line}],
            "reproducer": oracle_reproducer(entry)}]}
    verdict = rival.validate_verdict(raw, rival.ToolBox(tree))
    doc = rival.RivalOutcome(verdict=verdict["verdict"], attempts=verdict["attempts"], model_requested="fake:oracle",
                             model_served="fake:oracle").as_dict()
    doc["head"] = meta["head"]
    out.mkdir(parents=True, exist_ok=True)
    (out / "rival.json").write_text(json.dumps(doc, indent=1), encoding="utf-8", newline="\n")
    return doc


# ---- one entry, one batch --------------------------------------------------------------------------------------------

def _ran(res: RunResult) -> dict[str, Any]:
    return {"exit": res.exit_code, "timed_out": res.timed_out,
            "tail": (res.stdout + b"\n" + res.stderr).decode("utf-8", "replace")[-1500:]}


def check_oracle(runner_for: Callable[[Path], Runner], base_tree: Path, head_tree: Path, entry: Entry,
                 timeout_s: int) -> dict[str, Any]:
    """The plant is a defect only when its oracle passes on the accepted base and fails, on its own, on the plant."""
    base = _ran(runner_for(base_tree).run(entry.oracle, timeout_s=timeout_s))
    head = _ran(runner_for(head_tree).run(entry.oracle, timeout_s=timeout_s))
    valid = (base["exit"] == 0 and not base["timed_out"] and not head["timed_out"]
             and head["exit"] not in (0, reproduce.DOCKER_ERROR))
    return {"base": base, "head": head, "valid": valid}


def check_suite(runner: Runner, manifest: dict[str, Any], entry: Entry, full: bool, root: Path, head_tree: Path,
                timeout_s: int) -> dict[str, Any]:
    """The covering tests (every stage-0 test with ``full``) and the named micro-features' seed vectors on the head."""
    tests = {t["id"]: t for t in manifest["tests"] if t["stage"] == 0}
    wanted = sorted(tests) if full else list(entry.suite)
    missing = [i for i in wanted if i not in tests]
    if missing:
        raise CanaryError(f"{entry.id}: the manifest has no test {', '.join(missing)}: update the catalog")
    ran = [{"id": i, **_ran(runner.run(tests[i]["cmd"], timeout_s=timeout_s))} for i in wanted]
    vec = vectors.run_vectors(runner, root / "vectors", entry.mfs, table=stages.load(0), tree=head_tree) if entry.mfs else []
    green = all(t["exit"] == 0 and not t["timed_out"] for t in ran) and all(v["ok"] for v in vec)
    return {"tests": ran, "vectors_failed": [v["id"] for v in vec if not v["ok"]], "vectors": len(vec), "green": green}


@dataclass
class Batch:
    root: Path  # the referee repository's clone (read-only): bootstrap.json, policy.json, seats/, setup/, vectors/
    state: dict[str, Any]  # the signed state whose last_accepted_sha is the base
    mirror: Path  # the brain, read-only
    store: Path  # plants.git (``plant_store``)
    run_dir: Path
    entries: list[Entry]
    runner_for: Callable[[Path], Runner]
    reviewer: Reviewer
    mode: str
    full_suite: bool = False
    max_usd: float = MAX_USD


def run_entry(batch: Batch, base: str, base_tree: Path, empty: Path, entry: Entry, boot: config.Bootstrap,
              policy: config.Policy) -> dict[str, Any]:
    store, out = batch.store, batch.run_dir / entry.id
    out.mkdir(parents=True, exist_ok=True)
    rec: dict[str, Any] = {"id": entry.id, "kind": entry.kind, "path": entry.path, "base": base, "status": "",
                           "outcome": None, "cost_usd_micros": 0, "turns": 0, "pointed_at_plant": False}
    head, lines = plant_commit(store, base, entry)
    rec.update(head=head, lines=list(lines))
    _git(store, "update-ref", "refs/heads/" + boot.brain_branch, head)
    state_file = out / "state.json"
    state_file.write_text(json.dumps(batch.state), encoding="utf-8")
    pulled = out / "pulled"
    with _log(out / "pull.log"):
        code = cli.main(["pull", "--root", str(batch.root), "--state", str(state_file), "--work",
                         str(batch.run_dir / "git"), "--out", str(pulled), "--remote", str(store)])
    if code != 0:
        raise CanaryError(f"{entry.id}: pull stopped (see {out / 'pull.log'})")
    meta = json.loads((pulled / "meta.json").read_text(encoding="utf-8"))
    rec["pull"] = {"kind": meta["kind"], "pre_reasons": meta["pre_reasons"], "run_rival": meta["run_rival"]}
    if meta["kind"] != "code" or meta["pre_reasons"] or not meta["run_rival"] or meta["module_less"]:
        rec["status"] = "not_reviewable"
        return rec
    head_tree = out / "head-tree"
    extract((pulled / "brain.tar").read_bytes(), head_tree, boot.limits.max_tree_bytes)
    if not entry.control:
        rec["oracle"] = check_oracle(batch.runner_for, base_tree, head_tree, entry, boot.limits.test_timeout_s)
        if not rec["oracle"]["valid"]:
            rec["status"] = "oracle_invalid"
            return rec
    rec["suite"] = check_suite(batch.runner_for(head_tree), meta["manifest"], entry, batch.full_suite, batch.root,
                               head_tree, boot.limits.test_timeout_s)
    if not rec["suite"]["green"]:
        rec["status"] = "caught_by_suite"
        return rec
    rival_doc = batch.reviewer(entry, pulled, out / "rival")
    rec.update(status="reviewed", cost_usd_micros=int(rival_doc.get("cost_usd_micros", 0)),
               turns=int(rival_doc.get("turns", 0)), model_served=rival_doc.get("model_served", ""),
               verdict=rival_doc.get("verdict"))
    attempts = rival_doc["attempts"] if rival_doc.get("verdict") in ("refuted", "not_refuted") else []
    timeout = boot.limits.reproducer_timeout_s
    control = batch.runner_for(empty)
    on_head = reproduce.run_reproducers(batch.runner_for(head_tree), attempts, timeout, control=control)
    on_base = reproduce.run_reproducers(batch.runner_for(base_tree), attempts, timeout, control=control)
    rec["reproducers"] = {"head": on_head, "base": on_base}
    rec.update(classify(entry, rival_doc, proven(meta, rival_doc, on_head, policy), on_base, lines))
    return rec


def run_batch(batch: Batch) -> dict[str, Any]:
    boot, policy = config.load_bootstrap(batch.root), config.load_policy(batch.root)
    state = st.validate(copy.deepcopy(batch.state))
    base = state["last_accepted_sha"]
    if not gitio.has_commit(batch.mirror, base):
        raise CanaryError(f"the brain mirror lacks the accepted base {base}")
    batch.run_dir.mkdir(parents=True, exist_ok=True)
    base_tree, empty = batch.run_dir / "base-tree", batch.run_dir / "empty-tree"
    extract(gitio.archive(batch.store, base), base_tree, boot.limits.max_tree_bytes)
    empty.mkdir(exist_ok=True)
    empty.chmod(0o755)  # the container's user (65534) copies it like /src
    records: list[dict[str, Any]] = []
    for entry in batch.entries:
        spent = sum(r["cost_usd_micros"] for r in records)
        if spent >= batch.max_usd * 1_000_000:
            records.append({"id": entry.id, "kind": entry.kind, "status": "cost_brake", "outcome": None,
                            "cost_usd_micros": 0, "turns": 0, "pointed_at_plant": False})
            continue
        rec = run_entry(batch, base, base_tree, empty, entry, boot, policy)
        (batch.run_dir / entry.id / "record.json").write_text(json.dumps(rec, indent=1), encoding="utf-8",
                                                               newline="\n")
        records.append(rec)
        print(f"{entry.id:28} {entry.kind:22} {rec['status']:16} {rec['outcome'] or '':18} "
              f"{rec['cost_usd_micros'] / 1e6:.2f} USD", flush=True)
    results = {"schema": RESULTS_SCHEMA, "mode": batch.mode, "base": base,
               "rival": {"model": boot.rival.model, "effort": boot.rival.effort, "max_turns": boot.rival.max_turns,
                         "per_run_cap_usd_micros": boot.rival.per_run_cap_usd_micros},
               "referee_files_sha256": {name: hashlib.sha256((batch.root / name).read_bytes()).hexdigest()
                                        for name in ("bootstrap.json", "policy.json", "seats/29-tohum-koltuklari.md")},
               "records": records, "summary": summarize(records)}
    (batch.run_dir / "results.json").write_text(json.dumps(results, indent=1), encoding="utf-8", newline="\n")
    (batch.run_dir / "report.md").write_text(report(results), encoding="utf-8", newline="\n")
    return results


def report(results: dict[str, Any]) -> str:
    s = results["summary"]

    def rate(r: dict[str, Any]) -> str:
        return f"{r['x']}/{r['n']}" + (f" (lower bound {r['cp_lower']:.4f})" if r["n"] else "")

    lines = [f"# Rival canary, {results['mode']} run", "",
             f"Base `{results['base']}`; rival {results['rival']['model']}, effort {results['rival']['effort']}, "
             f"{results['rival']['max_turns']} turns, cap {results['rival']['per_run_cap_usd_micros'] / 1e6:.2f} USD.",
             f"One-sided Clopper-Pearson lower bounds at alpha {s['alpha']}.", "",
             f"- Recall: {rate(s['recall']['overall'])}",
             *[f"  - {kind}: {rate(r)}" for kind, r in s["recall"]["by_kind"].items()],
             f"- Attempts pointing at the planted lines: {s['pointed_at_plant']['x']}/{s['pointed_at_plant']['n']}",
             f"- False refutations on controls: {s['false_refutations']['x']}/{s['false_refutations']['n']}",
             f"- Cost: {s['cost_usd_micros'] / 1e6:.2f} USD over {s['reviews']} reviews, {s['turns']} turns",
             f"- Not judged: {json.dumps(s['not_judged'])}", "",
             "| entry | kind | status | outcome | attempts | with reproducer | pointed | USD | turns |",
             "|---|---|---|---|---|---|---|---|---|"]
    for r in results["records"]:
        lines.append(f"| {r['id']} | {r['kind']} | {r['status']} | {r['outcome'] or ''} | {r.get('attempts', '')} | "
                     f"{r.get('with_reproducer', '')} | {r['pointed_at_plant']} | {r['cost_usd_micros'] / 1e6:.2f} | "
                     f"{r['turns']} |")
    return "\n".join(lines) + "\n"


# ---- command line ----------------------------------------------------------------------------------------------------

def select(entries: list[Entry], only: str | None, plants: int, controls: int) -> list[Entry]:
    if only:
        wanted = only.split(",")
        unknown = sorted(set(wanted) - {e.id for e in entries})
        if unknown:
            raise CanaryError(f"no such entry: {', '.join(unknown)}")
        return [e for e in entries if e.id in wanted]
    return [e for e in entries if not e.control][:plants] + [e for e in entries if e.control][:controls]


def load_state(path: Path) -> dict[str, Any]:
    """A signed result (``result.json``, whose ``state`` is read) or a bare state."""
    doc = json.loads(path.read_text(encoding="utf-8"))
    return doc["state"] if isinstance(doc, dict) and "state" in doc and "verdict" in doc else doc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--work", required=True, help="a private folder outside the repository")
    parser.add_argument("--referee", required=True, help="a clone of the referee repository (read only)")
    parser.add_argument("--result", help="the referee's signed result or state (default: <work>/../referee/result.json)")
    parser.add_argument("--brain-remote", help="where the brain is read (default: the public repository bootstrap.json names)")
    parser.add_argument("--live", action="store_true", help="the real rival through your claude login (spends)")
    parser.add_argument("--claude", help="path of the claude CLI (default: the one on PATH)")
    parser.add_argument("--only", help="entry ids, comma-separated")
    parser.add_argument("--plants", type=int, default=FIRST_BATCH[0])
    parser.add_argument("--controls", type=int, default=FIRST_BATCH[1])
    parser.add_argument("--full-suite", action="store_true", help="every stage-0 test on each plant, not the covering ones")
    parser.add_argument("--max-usd", type=float, default=MAX_USD)
    args = parser.parse_args(argv)
    work, root = Path(args.work).resolve(), Path(args.referee).resolve()
    boot = config.load_bootstrap(root)
    state = load_state(Path(args.result) if args.result else work.parent / "referee" / "result.json")
    mirror = work / "brain.git"
    gitio.fetch(mirror, args.brain_remote or f"https://github.com/{boot.brain_repo}.git", boot.brain_branch,
                state["last_accepted_sha"])
    _kinds, entries = load_catalog()
    mode = "live" if args.live else "dry"
    run_dir = work / "runs" / (datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + mode)
    deps = run_dir / "deps"
    deps.mkdir(parents=True)
    vec = vectors.fixtures(root / "vectors", run_dir / "vec")
    batch = Batch(root=root, state=state, mirror=mirror, store=plant_store(work, mirror), run_dir=run_dir,
                  entries=select(entries, args.only, args.plants, args.controls),
                  runner_for=lambda tree: cli._runner(boot, tree, deps, vec, []),
                  reviewer=live_reviewer(root, args.claude) if args.live else oracle_reviewer, mode=mode,
                  full_suite=args.full_suite, max_usd=args.max_usd)
    results = run_batch(batch)
    print(report(results))
    print("written:", run_dir)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (CanaryError, config.ConfigError, gitio.GitError) as exc:
        print(f"stop: {exc}", file=sys.stderr)
        sys.exit(2)
