"""Command-line entry points: one subcommand per workflow step (`workflow/bootstrap.yml`)."""

from __future__ import annotations

import argparse
import dataclasses
import datetime
import hashlib
import importlib
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import canon, config, exitchecks, ghapi, gitio, ledgercheck, licenses, parts, stagelock, stages, state as st, wiring
from .classify import (LEDGER_FILE, REPORTS_DIR, SEED_DIRS, classify, is_founder_record, is_seed_path,
                       spec_stage_dirs)
from .container import DockerRunner
from .decide import OUTAGE_GIVE_UP_DAYS, OUTAGE_RETRY_LIMIT, REPORT_FIELDS, decide, utc_now
from .importer import ImportErrorStop, run_import, verify_signature
from .manifest import ManifestError, check_stage, declares, parse_lockfile, parse_manifest
from .moduleless import run_module_less, units
from .parts import PartError
from .reproduce import run_reproducers, run_state_reproducers
from .rival import (HIDDEN_DIRS, HIDDEN_NAMES, RivalOutcome, build_context, extract_seat_prompt, hidden, resolve_claude,
                    run_rival)
from .treehash import path_problem, TreeError, extract, is_utf8_name, iter_files, shown, tree_hash
from .vectors import applied, call_inputs, fixture_lookups, fixtures, missing_groups, visible_cases

EXIT_FILE = "exit-request.json"
MANIFEST_FILE = "snowball-tests.json"
STATE_ARTIFACT = "bootstrap-state"
SEATS_FILE = "29-tohum-koltuklari.md"
PIP_PLATFORMS = ("manylinux_2_39_x86_64", "manylinux_2_34_x86_64", "manylinux_2_28_x86_64",
                 "manylinux_2_17_x86_64", "manylinux2014_x86_64", "any")
SPEC_PAGES = ("00-", "00a-", "02-", "03-")
CODE_PAGES = ("00-", "00a-", "04-", "04a-", "08-", "29a-", "29b-", "29c-")  # and the open stage's (`stages.STAGE_PAGES`)


# ---------------------------------------------------------------- helpers

def output(**values: Any) -> None:
    """Write step outputs for GitHub Actions and echo them."""
    path = os.environ.get("GITHUB_OUTPUT")
    lines = [f"{k}={str(v).lower() if isinstance(v, bool) else v}" for k, v in values.items()]
    if path:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")
    print("\n".join(lines))


def summary(markdown: str) -> None:
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(markdown + "\n")


def month_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canon.dump(value), encoding="utf-8")


def pack_dir(src: Path, out: Path) -> str:
    """Deterministic tar of a directory; returns its sha256."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:", format=tarfile.PAX_FORMAT) as tar:
        for path in sorted(p for p in src.rglob("*") if p.is_file() and not p.is_symlink()):
            data = path.read_bytes()
            info = tarfile.TarInfo(path.relative_to(src).as_posix())
            info.size, info.mtime, info.mode = len(data), 0, 0o644
            tar.addfile(info, io.BytesIO(data))
    out.write_bytes(buf.getvalue())
    return hashlib.sha256(buf.getvalue()).hexdigest()


def unpack(tar_path: Path, expected_sha: str, dest: Path) -> None:
    data = tar_path.read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected_sha:
        raise SystemExit(f"artifact hash mismatch: {actual} != {expected_sha}")
    extract(data, dest, max_bytes=2_000_000_000)


def tar_file(tar_bytes: bytes, wanted: str) -> bytes | None:
    for path, content, _exec in iter_files(tar_bytes):
        if path.as_posix() == wanted:
            return content
    return None


def tar_page(tar_bytes: bytes, prefix: str) -> tuple[str, str] | None:
    for path, content, _exec in iter_files(tar_bytes):
        name = path.as_posix()
        if name.startswith(prefix) and name.endswith(".md"):
            return name, content.decode("utf-8", "replace")
    return None


def pinned_module(name: str, register: str) -> Any:
    """A package module the pinned exam needs (E516): imported only on a path that runs under a pin, so before the pin
    no run imports it. Missing under a pin is a deployment the operator made without it: the run stops (`26c`), it is
    never read as a module that found nothing."""
    try:
        return importlib.import_module(f".{name}", __package__)
    except ModuleNotFoundError as exc:
        if exc.name != f"{__package__}.{name}":
            raise
        raise config.ConfigError(f"the pinned exam needs snowball_bootstrap/{name}.py ({register}), which this "
                                 "bootstrap does not have") from None


def _signed_bytes(path: str | None) -> tuple[bytes | None, bytes | None]:
    """The last signed result's bytes and its Sigstore bundle's (`fetch-state` writes `<result>.sigstore.json` beside
    it and verified the pair in this job); None for either that is not there (the first run)."""
    if not path or not Path(path).is_file():
        return None, None
    bundle = Path(path + ".sigstore.json")
    return Path(path).read_bytes(), bundle.read_bytes() if bundle.is_file() else None


def signed_k6(path: str | None) -> Any:
    """The `k6` field of the last signed result (E516): what the next K6 evaluation names as the previous status and
    what the result carries when this run evaluated none. Read only from the bytes the bundle signs
    (`fence.signed_status`, E511); bytes no signature covers, or no result yet, are no K6 field."""
    fence = pinned_module("fence", "E511")
    raw, bundle = _signed_bytes(path)
    if fence.signed_status(raw, bundle) in (fence.MISSING, fence.UNBOUND):
        return None
    data = _json_or_none(raw)  # bound: these are the bytes the bundle signs
    block = data.get("k6") if isinstance(data, dict) else None
    return block if isinstance(block, dict) else None


def _pin_meta(meta: dict[str, Any], summary_cfg: config.Summary, prev_result: str | None) -> None:
    """Under a pinned exam the meta carries the pin `kos` compares the store with and the last signed `k6` field
    (E516); `yaz` reads the pin from the snapshot again. With no pin the meta is as it was."""
    if summary_cfg.exam_pin is not None:
        meta["k6_prev"] = signed_k6(prev_result)
        meta["exam_pin"] = summary_cfg.exam_pin


def remaining_budget(policy: config.Policy, prev: dict[str, Any], stage: int) -> int:
    """What the rival may still spend: the month's cap and the open stage's brake (`29b`, `26e`, E492), the stage's
    spend counted from its lock (``prev`` is `state.for_stage`'s)."""
    return min(policy.monthly_cap_usd_micros - prev["month_spend_usd_micros"],
               policy.rival_usd_micros(stage) - prev["stage_spend_usd_micros"])


# ---------------------------------------------------------------- commands

LOOP_FLAGS = ("control", "job", "event", "github_output")


def cmd_control(args: argparse.Namespace) -> int:
    """The kill switch, read live. With ``--root``: this workflow's operator files. With the loop's four flags (`29p`,
    `asama-0/01` D0): one loop job's first step, which writes ``go=true`` or ``go=false`` (a paused scheduled run) to
    ``--github-output``, or stops the job (exit 2) on the kill switch, the budget brake or a trigger or job the loop
    does not have."""
    given = [flag for flag in LOOP_FLAGS if getattr(args, flag) is not None]
    if given:
        if len(given) != len(LOOP_FLAGS):
            raise config.ConfigError("control: the loop's reading needs --control, --job, --event and --github-output")
        if args.job not in wiring.JOBS:
            raise config.ConfigError(f"control: {args.job!r} is not a loop job ({', '.join(wiring.JOBS)})")
        go = config.loop_goes(Path(args.control), args.event)
        with open(args.github_output, "a", encoding="utf-8") as handle:
            handle.write(f"go={str(go).lower()}\n")
        print(f"control {args.job}: " + ("go" if go else "paused (a scheduled run while loop_schedule is not true)"))
        return 0
    root = Path(args.root)
    config.check_control(root)
    config.load_bootstrap(root)
    config.load_policy(root)
    config.load_summary(root)
    stagelock.load(root)  # the stage lock and the counter it names (`asama-0/10a`, test 29)
    print("control ok: kill switch off, budget ok, operator files valid")
    return 0


def cmd_config_value(args: argparse.Namespace) -> int:
    boot = config.load_bootstrap(Path(args.root))
    output(image=boot.image)
    output(target_image=boot.target_image or "")  # E516: `kos_hedef`'s, which runs only under a pinned exam
    return 0


def _when(text: str) -> datetime.datetime:
    return datetime.datetime.fromisoformat(str(text).replace("Z", "+00:00"))


def _unsigned_rival_run(repo: str, token: str, head: str, signed_at: datetime.datetime,
                        now: datetime.datetime) -> bool:
    """E13, W4: the newest failed run judged this head with the rival (`cagir` succeeded) but never signed (`yaz`
    failed), and no state was signed since. Running it again would call the rival again, so it waits a day."""
    try:
        run = ghapi.latest_failed_run(repo, token)
        if run is None or _when(run["created_at"]) <= signed_at:
            return False
        if now - _when(run.get("updated_at") or run["created_at"]) >= datetime.timedelta(days=1):
            return False  # a day has passed: one more try
        jobs = ghapi.run_jobs(repo, run["id"], token)
        if jobs.get("cagir") != "success" or jobs.get("yaz") not in ("failure", "timed_out"):
            return False
        art = ghapi.run_artifact(repo, run["id"], "rival", token)
        if art is None:
            return False
        with zipfile.ZipFile(io.BytesIO(ghapi.download_zip(repo, art["id"], token))) as zf:
            rival_doc = json.loads(tar_file(zf.read("rival.tar"), "rival.json") or b"{}")
        return isinstance(rival_doc, dict) and rival_doc.get("head") == head
    except Exception as exc:  # the runs API only spares a rival call here: when it fails, judge as before
        print(f"::warning::poll could not read the previous failed run: {type(exc).__name__}")
        return False


def cmd_poll(args: argparse.Namespace) -> int:
    """Cheap first look: is there anything new to judge? Installs nothing and verifies nothing.

    The previous state is read unverified here only to decide whether to skip; skipping is the
    safe outcome. Anything that is evaluated goes through ``fetch-state``, which verifies it.
    A commit that keeps failing is parked (one retry a day), stops visibly after a week or at once after an
    isolation fault (E12); a run the operator starts by hand (`workflow_dispatch`) tries it anyway.
    """
    root, out = Path(args.root), Path(args.out)
    boot = config.load_bootstrap(root)
    token = os.environ["GH_TOKEN"]
    repo = os.environ["GITHUB_REPOSITORY"]
    remote = args.remote or f"https://github.com/{boot.brain_repo}.git"
    head = gitio.remote_head(remote, boot.brain_branch)
    art = ghapi.latest_artifact(repo, STATE_ARTIFACT, token)
    if art is None:
        output(skip=False, reupload=False, head=head)
        return 0
    prev_dir = out / "prev"
    prev_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(ghapi.download_zip(repo, art["id"], token))) as zf:
        for name in ("result.json", "result.json.sigstore.json"):
            (prev_dir / name).write_bytes(zf.read(name))
    now = datetime.datetime.now(datetime.timezone.utc)
    dispatched = os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"  # the operator asked for this run
    try:
        prev = read_json(prev_dir / "result.json")["state"]
        seen = {prev["last_accepted_sha"], prev["last_evaluated_sha"]}
        failing = prev.get("outage_sha") == head
        parked = failing and int(prev.get("outage_count", 0)) >= OUTAGE_RETRY_LIMIT
        stopped = prev.get("outage_stop") if failing else None
        since = prev.get("outage_since")
        given_up = bool(parked and since and now - _when(since) >= datetime.timedelta(days=OUTAGE_GIVE_UP_DAYS))
    except (KeyError, TypeError, ValueError, AttributeError, json.JSONDecodeError):
        seen, parked, stopped, given_up = set(), False, None, False
    created = _when(art["created_at"])
    age = now - created
    reupload = age.days >= 7
    if head not in seen and not dispatched and (stopped or given_up):
        why = f"an isolation fault ({stopped})" if stopped else f"infrastructure failures for {OUTAGE_GIVE_UP_DAYS} days"
        print(f"::error title=Commit stopped for the operator::{head} stopped after {why}. Fix the cause, then run "
              "the workflow by hand (workflow_dispatch) to try it again.")
        output(skip=True, reupload=reupload, head=head)
        return 1
    waiting = parked and age < datetime.timedelta(days=1) and not dispatched  # parked: one retry a day
    if waiting:
        print(f"::notice title=Commit parked::{head} failed {OUTAGE_RETRY_LIMIT} times for infrastructure "
              "reasons and is retried once a day")
    unsigned = head not in seen and not waiting and not dispatched and _unsigned_rival_run(repo, token, head, created, now)
    if unsigned:
        print(f"::notice title=Result never signed::{head} was judged by the rival but `yaz` failed; it is retried "
              "once a day instead of calling the rival every hour")
    output(skip=head in seen or waiting or unsigned, reupload=reupload, head=head)
    return 0


def cmd_licenses(args: argparse.Namespace) -> int:
    """Check a directory of wheels against the license allowlist; stop on any violation."""
    policy = config.load_policy(Path(args.root))
    report = licenses.check_dir(Path(args.wheels), policy.license_allowlist, policy.license_exceptions)
    if args.out:
        write_json(Path(args.out), report)
    for r in report:
        print(f"{r['name']}=={r['version']}: {r['expression']} ({'allowed' if r['allowed'] else 'NOT ALLOWED'})")
    bad = licenses.violations(report)
    if not report or bad:
        print(f"stop: license gate: {', '.join(bad) or 'no wheels found'}", file=sys.stderr)
        return 2
    return 0


def cmd_fetch_state(args: argparse.Namespace) -> int:
    root, out = Path(args.root), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    summary_cfg = config.load_summary(root)
    token = os.environ["GH_TOKEN"]
    repo = os.environ["GITHUB_REPOSITORY"]
    art = ghapi.latest_artifact(repo, STATE_ARTIFACT, token)
    reupload = False
    if art is None:
        missing = config.start_missing(summary_cfg)  # where Stage 0 starts: never without its setup (E293)
        if missing:
            raise config.ConfigError("setup/summary.json lacks what Stage 0 needs before it starts (`25`): "
                                     + "; ".join(missing))
        prev = st.initial(summary_cfg, month_now())
        summary("No previous bootstrap state artifact: starting from the setup summary's seed commit.")
    else:
        prev_dir = out / "prev"
        prev_dir.mkdir(exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(ghapi.download_zip(repo, art["id"], token))) as zf:
            for name in ("result.json", "result.json.sigstore.json"):
                (prev_dir / name).write_bytes(zf.read(name))
        verify_signature(prev_dir / "result.json", prev_dir / "result.json.sigstore.json",
                         args.identity, args.sigstore_python)
        signed = read_json(prev_dir / "result.json")
        raw = signed["state"]
        carried = st.migrate(raw, utc_now(), signed)  # an older schema is carried forward, never thrown away (`25`)
        if carried is not raw:
            summary(f"The previous state ({raw.get('schema')}) was carried forward to {st.SCHEMA}.")
        prev = st.rollover(st.validate(carried), month_now())
        created = datetime.datetime.fromisoformat(art["created_at"].replace("Z", "+00:00"))
        reupload = (datetime.datetime.now(datetime.timezone.utc) - created).days >= 7
    write_json(out / "state.json", prev)
    output(reupload=reupload)
    return 0


def cmd_pull(args: argparse.Namespace) -> int:
    root, out = Path(args.root), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    boot = config.load_bootstrap(root)
    policy = config.load_policy(root)
    summary_cfg = config.load_summary(root)
    # The seed's stage table is loaded here, outside the content guard below: a broken table stops the run
    # (a seed defect, `26a`) instead of turning into the Founder's `pull_error` rejection. It is the table that holds
    # (`stagelock.open_table`): Stage 0's before the operator's lock (`setup/stage.json`, `asama-0/10a`), then the open
    # batch's; a lock that does not match its counter stops the run too (`asama-0/09` test 29).
    table = stagelock.open_table(root)
    # The open stage's rival brake, read here, outside the content guard below: a policy without it stops the run (the
    # operator's to write), never the Founder's `pull_error` (E492). Past the lock the stage's spend counts from the
    # lock (`26e`); Stage 0's state is the one it always was.
    policy.rival_usd_micros(table.stage)
    prev = st.for_stage(read_json(Path(args.state)), table.stage)
    repo = Path(args.work) / "brain.git"
    remote = args.remote or f"https://github.com/{boot.brain_repo}.git"
    base = prev["last_accepted_sha"]
    head = gitio.fetch(repo, remote, boot.brain_branch, base)
    meta = _pull_meta(head, base, prev)
    if head in (base, prev["last_evaluated_sha"]):
        write_json(out / "meta.json", meta)
        output(skip=True, kind="none", head=head, run_tests=False, run_rival=False, repro=False)
        return 0
    if summary_cfg.epoch is not None:  # outside the content guard: a wrong row is the operator's to fix
        _check_epoch(repo, summary_cfg.epoch)
    waived = config.load_waivers(root)
    reverted = config.load_reverted_exits(root)  # the operator's file: a broken list stops the run, never a rejection
    faults = exam_faults_in_force(repo, summary_cfg, config.load_exam_faults(root))
    meta["exam_faults"] = faults
    _pin_meta(meta, summary_cfg, args.prev_result)
    try:
        return _pull_classify(boot, policy, summary_cfg, table, prev, repo, base, head, meta, out, waived, reverted)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RecursionError) as exc:
        # Content of the commit broke a step that should have named it. Rejecting it is the only safe
        # answer that does not wedge the referee: without a signed result the same head comes back every
        # hour and nothing is ever parked (E02). Git, network and operator-file errors still stop the run.
        print(f"::warning::pull could not classify {head}: {type(exc).__name__}: {str(exc)[:200]!r}")
        meta = _pull_meta(head, base, prev)
        meta.update(kind="rejected", pre_reasons=["pull_error"], waived=waived, exam_faults=faults)
        _pin_meta(meta, summary_cfg, args.prev_result)
        write_json(out / "meta.json", meta)
        output(skip=False, kind="rejected", head=head, run_tests=False, run_rival=False, repro=False)
        return 0


def _pull_meta(head: str, base: str, prev: dict[str, Any]) -> dict[str, Any]:
    # Nothing of the stage lock is here: every job reads the table that holds from the run's snapshot itself
    # (`stagelock.open_table`), so Stage 0's meta is the one it always was (E402).
    return {"schema": "snowball-bootstrap-pull/1", "head": head, "base": base, "state": prev,
            "kind": "none", "changed": [], "pre_reasons": [], "evaluate": True,
            "run_tests": False, "run_rival": False, "manifest": None, "exit_request": None, "exit_request_sha256": None,
            "referee_tree_sha256": None, "spec_dir_hashes": {}, "state_repro": [], "reuse_rival": False,
            "waived": [], "module_less": [], "exit_checks": {}, "toy_tree_sha256": None, "honesty_exception": None,
            "reports": [], "exam_faults": []}


def exam_faults_in_force(repo: Path, summary_cfg: config.Summary, faults: list[config.ExamFault]) -> list[str]:
    """The signatures of the operator's confirmed exam faults still in force (`29e` "Sınav hatası", E53, E426). An
    entry holds while the exam that judged its head is the one in force: while the last seed epoch's commit (the setup
    seed's when none was delivered) is an ancestor of the head. The next epoch, which brings the exam's fix, ends it
    by itself, so an entry left in place never keeps a later failure of the fixed exam off the Founder's streaks. A
    head the brain does not have is the operator's mistake: the run stops (git's own failure stops it too, E384)."""
    exam = summary_cfg.epoch.commit if summary_cfg.epoch is not None else summary_cfg.seed_commit
    held: set[str] = set()
    for fault in faults:
        if not gitio.has_commit(repo, fault.head):
            raise config.ConfigError(f"control.json exam_faults names {fault.head}, which the brain does not have")
        if gitio.is_ancestor(repo, exam, fault.head):
            held.add(fault.signature)
    return sorted(held)


MAX_REPORTS = 200
MAX_REPORT_FIELD = 500


def read_reports(tar_bytes: bytes) -> list[dict[str, Any]]:
    """The brain's reports (`26c` reports/*.json, E93): every regular file directly under the root `reports/` whose name
    ends in `.json`, by path, as ``{id, kind, ref, state, sha256}``; the hash is of the file's bytes. A field that is
    missing, not a string or longer than ``MAX_REPORT_FIELD``, or any field of a file that is not one JSON object, is
    null: the reader names what a report holds and never turns a report into a reason (it is the Founder's memory, not
    its code). An archive with something other than regular files has no reports to read here: `pull` names that."""
    found: list[tuple[str, dict[str, Any]]] = []
    try:
        for path, content, _exec in iter_files(tar_bytes):
            if len(path.parts) != 2 or path.parts[0] != REPORTS_DIR.rstrip("/") or not path.name.endswith(".json"):
                continue
            try:
                data = json.loads(content.decode("utf-8"))
            except (UnicodeDecodeError, ValueError, RecursionError):
                data = None
            row: dict[str, Any] = {}
            for key in REPORT_FIELDS:
                value = data.get(key) if isinstance(data, dict) else None
                row[key] = value if isinstance(value, str) and len(value) <= MAX_REPORT_FIELD else None
            row["sha256"] = hashlib.sha256(content).hexdigest()
            found.append((path.as_posix(), row))
    except TreeError:
        return []
    return [row for _path, row in sorted(found, key=lambda item: item[0])][:MAX_REPORTS]


def seed_trees(tar_bytes: bytes) -> tuple[str | None, str | None]:
    """The hashes of a brain tree's ``spec/tohum/`` and ``seed/`` (`26c` ``seed_epochs[]``); None for one with no files."""
    def one(prefix: str) -> str | None:
        try:
            return tree_hash(tar_bytes, prefix, forbid_operator_names=False)
        except TreeError:
            return None
    return one(SEED_DIRS[0]), one(SEED_DIRS[1])


def _check_epoch(repo: Path, epoch: config.SeedEpoch) -> None:
    """The last seed epoch names a brain commit and that commit's seed trees (`25` 10b). A row that is not its
    commit's is the operator's mistake: the run stops here, so no Founder push is judged against a seed that was
    never delivered."""
    if not gitio.has_commit(repo, epoch.commit):
        raise config.ConfigError(f"setup/summary.json: the last seed epoch's commit {epoch.commit} is not on the brain "
                                 "branch (push the delivery before writing its row)")
    if seed_trees(gitio.archive(repo, epoch.commit, SEED_DIRS)) != (epoch.spec_tohum_sha256, epoch.seed_sha256):
        raise config.ConfigError(f"setup/summary.json: the last seed epoch's hashes are not those of {epoch.commit} "
                                 "(print the row with `seed-epoch`)")


def _seed_update(repo: Path, base: str, head: str, meta: dict[str, Any], out: Path, waived: list[str]) -> int:
    """The operator's seed delivery itself (`25` 10b): nothing in it is the Founder's, so nothing is judged (E88)."""
    changed = gitio.changed_paths(repo, base, head) if gitio.has_commit(repo, base) else []
    meta.update(kind="seed_update", changed=[shown(p) for p in changed], waived=waived,
                reports=read_reports(gitio.archive(repo, head)))  # the brain's reports are named on every result
    write_json(out / "meta.json", meta)
    output(skip=False, kind="seed_update", head=head, run_tests=False, run_rival=False, repro=False)
    return 0


def _well_formed_exit_request(req: Any, table: stages.StageTable) -> bool:
    """`26c`: ``{stage, sha, spec_sha256}``; a batch's request is the same with ``batch`` (`26c:17`). Which form holds
    is the open table's, never the request's (E402): under Stage 0's table there is no batch, so a ``batch`` key is
    malformed as it always was; once the lock opened a stage, the request may name the batch it asks for."""
    batch_key = {"batch"} if table.stage else set()
    return (isinstance(req, dict) and set(req) - batch_key == {"stage", "sha", "spec_sha256"}
            and isinstance(req["stage"], int) and not isinstance(req["stage"], bool) and 0 <= req["stage"] <= 1000
            and isinstance(req["sha"], str) and bool(config.SHA_RE.match(req["sha"]))
            and isinstance(req["spec_sha256"], str) and bool(config.HEX64_RE.match(req["spec_sha256"]))
            and ("batch" not in req or (isinstance(req["batch"], str) and bool(stages.BATCH_RE.match(req["batch"])))))


def _base_done(repo: Path, base: str, table: stages.StageTable) -> set[int]:
    """The micro-features the last accepted commit had finished; none when it had no readable manifest (then every
    finished one is new, and module-less red runs for all of them). After the lock opened, a base whose manifest is
    not the open stage's (Stage 0's 18, still there until the Founder's first Stage 1 push) has finished none of it."""
    raw = gitio.file_at(repo, base, MANIFEST_FILE)
    try:
        found = parse_manifest(raw.decode("utf-8")) if raw is not None else None
    except (ManifestError, UnicodeDecodeError):
        return set()
    if found is None or (table.stage and not declares(found, table)):
        return set()
    return set(found.done_mf)


EXIT_MAY_CHANGE = ("candidates/", "targets/")  # what (B) may change after (A) (`asama-0/10a`, `asama-0/11`)


def exit_freeze(prev: dict[str, Any], reverted: list[str], stage: int) -> tuple[bool, bool]:
    """(frozen, released) for the accepted exit the signed state names (E333). From (A) the brain stays the one the
    exit was accepted with, but for (B)'s candidates and targets, while Stage 0 is open (`asama-0/11`); the operator's
    revert of the transfer after a red (B), named in ``control.json`` ``reverted_exits``, or a lock that opened a later
    stage ends it, and the state forgets that exit (`asama-0/10a` "Başarısızlık": the corrected SHA goes through (A)
    again)."""
    sha = prev.get("exit_accepted_sha")
    if not sha:
        return False, False
    released = stage != 0 or sha in reverted
    return not released, released


def _pull_classify(boot: config.Bootstrap, policy: config.Policy, summary_cfg: config.Summary,
                   table: stages.StageTable, prev: dict[str, Any], repo: Path, base: str, head: str,
                   meta: dict[str, Any], out: Path, waived: list[str], reverted: list[str]) -> int:
    epoch = summary_cfg.epoch
    frozen, meta["exit_released"] = exit_freeze(prev, reverted, table.stage)
    if epoch is not None and head == epoch.commit:
        return _seed_update(repo, base, head, meta, out, waived)
    pre: list[str] = []
    base_ok = gitio.has_commit(repo, base)
    if not base_ok:
        pre.append("base_unreachable")
    elif not gitio.is_ancestor(repo, base, head):
        pre.append("history_rewritten")
    changed = gitio.changed_paths(repo, base, head) if base_ok else []
    names = changed + gitio.tree_paths(repo, head)
    if not all(map(is_utf8_name, names)):
        pre.append("non_utf8_path")  # canonical JSON cannot hold such a name: keep it out of meta.json, say so once
    elif any(path_problem(p) for p in names):
        pre.append("unsafe_path")  # a control character, a .git component, ':' or '\\' (E03, E04)
    changed = [shown(p) for p in changed]
    tar_bytes = gitio.archive(repo, head)
    readable = not {"non_utf8_path", "unsafe_path"} & set(pre)
    trees = seed_trees(tar_bytes) if readable else (None, None)
    meta["reports"] = read_reports(tar_bytes) if readable else []  # `26c`, E93: named in the signed result
    # While the head's seed is the last epoch's commit's, the seed paths in the diff from the last accepted commit are
    # the operator's delivery, not the Founder's change (`25` 10b, E88); any other seed is checked below. Git compares
    # them: a mode change counts (the tree hashes leave the executable bit out) and an unreadable tree is no excuse
    # to charge the delivery to the Founder (E184).
    epoch_seed = epoch is not None and gitio.same_under(repo, epoch.commit, head, SEED_DIRS)
    own = [p for p in changed if not (epoch_seed and is_seed_path(p))]
    exit_raw = gitio.file_at(repo, head, EXIT_FILE)  # from its blob: readable even when another name is not
    exit_sha = hashlib.sha256(exit_raw).hexdigest() if exit_raw is not None else None
    judged = [p for p in own if not is_founder_record(p)]  # the Founder's ledger rows may ride along
    if judged == [EXIT_FILE]:
        kind = "exit"  # the same bytes asked for again alone are a request again, judged again
    else:
        # In a code push, a file byte for byte a request the referee rejected is ignored (`asama-0/10`, `26c`, E97):
        # left in place it does not make the push "not alone".
        left_in_place = exit_sha is not None and exit_sha == prev.get("rejected_exit_request")
        if left_in_place:
            own = [p for p in own if p != EXIT_FILE]
        kind, reasons = classify(own, exam_pinned=summary_cfg.exam_pin is not None)
        pre += reasons
        if EXIT_FILE in judged and not left_in_place:
            pre.append("exit_request_not_alone")
    if frozen and kind in ("spec", "code", "exit"):
        # After (A) the referee tree is the one the exit was accepted with: the import copies it and the loop runs
        # it; only (B)'s candidates and targets may change, the Founder's memory beside them (`asama-0/10a`
        # "Başarısızlık", `asama-0/11`, `25a` 8; E333).
        moved = [p for p in own if not is_founder_record(p) and not p.startswith(EXIT_MAY_CHANGE)]
        if any(p.startswith("referee/") for p in moved):
            pre.append("referee_changed_after_exit")
        pre += [f"changed_after_exit:{p}" for p in moved if not p.startswith("referee/")][:20]
    if {"base_unreachable", "history_rewritten", "non_utf8_path", "unsafe_path"} & set(pre):  # nothing can be read safely
        kind = "rejected"
    pre += [f"not_regular_file:{x}" for x in gitio.special_entries(repo, head)][:20]
    if len(tar_bytes) > boot.limits.max_tree_bytes:
        pre.append("tree_too_large")
    if readable:
        if trees[0] is None:
            pre.append("seed_tree_missing")
        elif not (epoch_seed if epoch is not None else trees[0] == summary_cfg.seed_tree_sha256):
            pre.append("seed_tree_mismatch")  # the head's seed is not the one the summary names (`29b`)

    manifest = None
    finished: set[int] = set()
    if kind in ("code", "exit"):
        for stage_dir in (f"spec/asama-{s}" for s in range(table.stage + 1)):  # code is built under a frozen spec (`02`)
            frozen = prev["frozen_specs"].get(stage_dir)
            try:
                current = tree_hash(tar_bytes, stage_dir, forbid_operator_names=False)
            except TreeError:
                current = None
            if frozen is None:
                pre.append("spec_not_frozen")
            elif frozen != current:
                pre.append("spec_changed_after_freeze")
        raw = tar_file(tar_bytes, MANIFEST_FILE)
        if raw is None:
            pre.append("manifest_missing")
        else:
            try:
                manifest = parse_manifest(raw.decode("utf-8"))
                pre += check_stage(manifest, table)
                for lock in manifest.lockfiles:
                    content = tar_file(tar_bytes, lock)
                    if content is None:
                        pre.append(f"lockfile_missing:{lock}")
                    else:
                        parse_lockfile(content.decode("utf-8"))
            except (ManifestError, UnicodeDecodeError) as exc:
                pre.append(f"manifest_invalid:{str(exc)[:200]}")
        meta["manifest"] = None if manifest is None else {
            "tests": [{"id": t.id, "cmd": t.cmd, "stage": t.stage} for t in manifest.tests],
            "done_mf": list(manifest.done_mf), "lockfiles": list(manifest.lockfiles)}
        if manifest is not None and base_ok:
            # Module-less red (`asama-0/14`): for the micro-features this push finishes, and at the exit for all.
            before = set() if kind == "exit" else _base_done(repo, base, table)
            meta["module_less"] = [k for k in manifest.done_mf if k not in before]
        # A finished micro-feature stays finished: its vector group, and for MF17 the wiring check, run on every push
        # after the one it entered done_mf in (`asama-0/14`, `29a`), so no push may declare fewer (E292).
        accepted_done = _base_done(repo, base, table) if base_ok else set()
        declared = set(manifest.done_mf) if manifest is not None else set()
        finished = accepted_done | declared
        if manifest is not None:
            pre += [f"done_mf_withdrawn:MF{k}" for k in sorted(accepted_done - declared)]

    # The Founder's ledger on every push the referee judges (`00a`; `asama-0/10` #kurucu-defteri, E107, E280): a spec
    # or code push has the rows it adds checked here, before the tests and the rival; the exit, the whole file.
    ledger_base = gitio.file_at(repo, base, LEDGER_FILE) if kind in ("spec", "code", "exit") else None
    if kind in ("spec", "code"):
        pre += ledgercheck.check(tar_file(tar_bytes, LEDGER_FILE), ledger_base, whole=False)
    # The loop workflow's wiring on every code push once its micro-feature is finished, and at the exit (`asama-0/14`).
    if kind == "code" and wiring.due(table, finished):
        pre += wiring.check(wiring.files_in(exitchecks.referee_files(tar_bytes)))

    if kind == "exit":
        meta["exit_request_sha256"] = exit_sha  # rejected, these bytes are ignored in later pushes (E97)
        try:
            req = json.loads((exit_raw or b"").decode("utf-8"))
        except (ValueError, RecursionError):  # bad UTF-8 or JSON, or nested deeper than the parser goes
            req = None
        if not _well_formed_exit_request(req, table):
            pre.append("exit_request_malformed")
        else:
            meta["exit_request"] = req
            # Which exit a request may ask for is the open table's (E402). Before the lock, Stage 0's alone, judged as it
            # always was (`02`; under Stage 0's table no request has a batch). Past it, this seed signs only the open
            # batch's (A), under its stage's frozen spec (`02` 6, `asama-1/13` 2, `26c:17`; E378): a request with no
            # batch is the stage's own exit, not this seed's to judge.
            batch = req.get("batch")
            if table.stage:
                wrong_stage = batch is None or req["stage"] != table.stage
                spec_dir = f"spec/asama-{req['stage']}" if batch is not None else "spec/asama-0"
            else:
                wrong_stage, spec_dir = req["stage"] != 0, "spec/asama-0"
            if wrong_stage:
                pre.append("exit_request_wrong_stage")
            elif batch != table.batch:
                pre.append("exit_request_wrong_batch")
            if req["sha"] != base:
                pre.append("exit_request_sha_is_not_last_accepted")
            if req["spec_sha256"] != prev["frozen_specs"].get(spec_dir):
                pre.append("exit_request_spec_hash_mismatch")
        try:
            meta["referee_tree_sha256"] = tree_hash(tar_bytes, "referee")
        except TreeError as exc:
            pre.append(f"referee_tree:{exc}")
        # The (A) conditions read from the archive (E162's follow-up): their results go to `decide`, not here, so the
        # tests still run and one request hears everything that is missing.
        meta["exit_checks"], meta["toy_tree_sha256"] = exitchecks.run(
            tar_bytes, tar_file(tar_bytes, LEDGER_FILE), ledger_base, summary_cfg.targets)
        # The exit's other reasons may quote the Founder's paths too; none says a target's name in clear (E290).
        names = exitchecks.target_names(summary_cfg.targets)
        pre = [exitchecks.withheld_reason(r, names) for r in pre]
        exception = summary_cfg.honesty_exception  # the owner's, named in the signed result (`02`, E287, E294)
        if exception is not None:  # with the commitment beside it, the carried stage's plant, or None (E297)
            meta["honesty_exception"] = {"stage": exception.stage, "carry_to": exception.carry_to,
                                         "reason": exitchecks.withheld(exception.reason, names),
                                         "carry_commitment": summary_cfg.honesty_commitment}

    if kind == "spec":
        for d in spec_stage_dirs(own):
            try:
                meta["spec_dir_hashes"][d] = tree_hash(tar_bytes, d, forbid_operator_names=False)
            except TreeError:
                pre.append(f"spec_dir_empty:{d}")

    needs_rival = kind in ("spec", "code")
    # A valid rival result whose reproducers never ran is reused for the same head, not asked for again (E20).
    pending = prev.get("pending_rival")
    reuse = needs_rival and isinstance(pending, dict) and pending.get("sha") == head
    if needs_rival and not reuse and remaining_budget(policy, prev, table.stage) <= 0:
        # Recorded once for this commit; re-evaluating it every poll would only churn signatures.
        # The founder pushes again after the month or the stage budget changes.
        pre.append("budget")
    meta.update(kind=kind, changed=own, pre_reasons=sorted(set(pre)), waived=waived)
    meta["run_tests"] = kind in ("code", "exit") and not pre
    meta["run_rival"] = needs_rival and not pre and not reuse
    meta["reuse_rival"] = reuse and not pre
    # Every code head (an exit request too) is checked again for the proven defects and open claims the state
    # keeps (E07, E08): the `yeniden` job runs them even when the rival finds nothing or is not called.
    if meta["run_tests"]:
        meta["state_repro"] = ([e["key"] for e in prev.get("open_refutations", []) if e["key"] not in waived]
                               + [c["id"] for c in prev.get("open_claims", []) if c["reproducer"] is not None])
    repro = bool(meta["state_repro"]) or (meta["reuse_rival"] and any("reproducer" in a for a in pending["rival"]["attempts"]))
    write_json(out / "meta.json", meta)
    (out / "brain.tar").write_bytes(tar_bytes)
    # The rival's diff holds neither the Founder's ledger and reports (E10, E153) nor a delivered seed: a seed path
    # still in it here is the epoch's (any other seed change is rejected before the rival), not the Founder's (E88).
    (out / "diff.patch").write_text(gitio.diff_text(repo, base, head, exclude=HIDDEN_NAMES, exclude_dirs=HIDDEN_DIRS + SEED_DIRS)
                                    if base_ok else "", encoding="utf-8")
    if summary_cfg.exam_pin is not None:  # E516: what the watchers' static pass reads of the base (`cmd_watch`)
        write_json(out / "base.json", _watch_base(repo, base) if base_ok else {"ledger": None, "tests": []})
    output(skip=False, kind=kind, head=head, run_tests=meta["run_tests"], run_rival=meta["run_rival"], repro=repro,
           exam_pinned=summary_cfg.exam_pin is not None)  # E516: the jobs that need the exam
    return 0


def cmd_fetch_deps(args: argparse.Namespace) -> int:
    pulled, out = Path(args.pulled), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    meta = read_json(pulled / "meta.json")
    tar_bytes = (pulled / "brain.tar").read_bytes()
    locks = (meta.get("manifest") or {}).get("lockfiles", [])
    scratch = Path(args.work)
    scratch.mkdir(parents=True, exist_ok=True)
    for i, lock in enumerate(locks):
        content = tar_file(tar_bytes, lock)
        if content is None:
            raise SystemExit(f"lock file {lock} disappeared")
        parse_lockfile(content.decode("utf-8"))
        lock_path = scratch / f"lock-{i}.txt"
        lock_path.write_bytes(content)
        argv = [sys.executable, "-m", "pip", "download", "--no-deps", "--only-binary=:all:", "--require-hashes",
                "--python-version", "3.12", "--implementation", "cp",
                "--abi", "cp312", "--abi", "abi3", "--abi", "none"]
        for plat in PIP_PLATFORMS:
            argv += ["--platform", plat]
        argv += ["--index-url", "https://pypi.org/simple", "--dest", str(out), "-r", str(lock_path)]
        proc = subprocess.run(argv, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise SystemExit(f"pip download failed for {lock}: {proc.stderr[-1000:]}")
    wheels = {p.name: canon.sha256_file(str(p)) for p in sorted(out.glob("*.whl"))}
    write_json(out / "wheels.json", wheels)
    return 0


def _runner(boot: config.Bootstrap, src: Path, deps: Path, vectors: Path, lockfiles: list[str]) -> DockerRunner:
    return DockerRunner(image=boot.image, src_dir=str(src.resolve()), deps_dir=str(deps.resolve()),
                        vectors_dir=str(vectors.resolve()), lockfiles=tuple(lockfiles))


@dataclass(frozen=True)
class Kos:
    """One push as `kos` reads it from the verified snapshot, pulled tree and wheels: the same for every part and the
    join (E440)."""

    boot: config.Bootstrap
    table: stages.StageTable
    meta: dict[str, Any]
    tar_bytes: bytes
    src: Path
    push: parts.Push


def _kos(args: argparse.Namespace) -> Kos:
    root, pulled = Path(args.root), Path(args.pulled)
    boot = config.load_bootstrap(root)
    policy = config.load_policy(root)
    meta = read_json(pulled / "meta.json")
    table = stagelock.open_table(root)  # the snapshot's lock and counter, as `pull` read them (`asama-0/10a`, E402)
    tar_bytes = (pulled / "brain.tar").read_bytes()
    src = Path(args.work) / "src"
    extract(tar_bytes, src, boot.limits.max_tree_bytes)
    manifest = meta["manifest"]
    done = tuple(manifest["done_mf"])
    groups = applied(root / "vectors", done, table=table, tree=src)
    push = parts.Push(
        head=meta.get("head"), tests=[t for t in manifest["tests"] if t["stage"] <= table.stage], groups=groups,
        asked=call_inputs(groups),
        units=[(k, t["id"]) for k, t in units(table, meta.get("module_less") or [], manifest["tests"])],
        lic=licenses.check_dir(Path(args.deps), policy.license_allowlist, policy.license_exceptions),
        missing=missing_groups(root / "vectors", done, table, tree=src))
    return Kos(boot, table, meta, tar_bytes, src, push)


def _run_part(args: argparse.Namespace, kos: Kos, part: int, count: int) -> dict[str, Any]:
    """Part ``part`` of ``count`` in this job's own sandbox: containers with the pushed tree, the locked wheels and
    `/vec`; module-less red on its own trees."""
    root, boot, manifest = Path(args.root), kos.boot, kos.meta["manifest"]
    vec = fixtures(root / "vectors", Path(args.work) / "vec")  # `/vec` without the expected values
    runner = _runner(boot, kos.src, Path(args.deps), vec, manifest["lockfiles"])

    def module_less(mine: Any) -> list[dict[str, Any]]:
        return run_module_less(
            lambda tree: _runner(boot, tree, Path(args.deps), vec, manifest["lockfiles"]),
            kos.tar_bytes, Path(args.work) / "module-less", kos.table, kos.meta.get("module_less") or [],
            manifest["tests"], boot.limits.test_timeout_s, boot.limits.max_tree_bytes, mine=mine)
    return parts.run_part(kos.push, part, count, runner, boot.limits.test_timeout_s, module_less)


def _write_run(out: Path, run: dict[str, Any]) -> int:
    write_json(out / "run.json", run)
    output(green=run["green"])
    return 0


def cmd_run_tests(args: argparse.Namespace) -> int:
    """`kos` in one job: the push as one part, joined at once (E440). The workflow runs `run-part` in parallel jobs and
    `join-parts` after them; on the same answers both write this `run.json`."""
    kos = _kos(args)
    return _write_run(Path(args.out), parts.join(kos.push, [_run_part(args, kos, 0, 1)]))


def cmd_run_part(args: argparse.Namespace) -> int:
    """One part of `kos` (E440): `part.json`, what this part ran and every vector call's answer; it judges nothing."""
    part, count = parts.part_of(args.part)
    kos = _kos(args)
    write_json(Path(args.out) / "part.json", _run_part(args, kos, part, count))
    return 0


def cmd_join_parts(args: argparse.Namespace) -> int:
    """`run.json` from every part's `part.json`, each read from its artifact only if the artifact's hash is the one its
    job output named (``--part TAR=SHA``, in part order). A part without its artifact or its hash stops the join.

    Under a pinned exam (E516) the vectors are judged on the visible answers of the exam store `kos` fetched
    (``--exam``), read and checked against the epoch's pin by `answers` (E509); a store that cannot be had so judges
    nothing, and `run.json` says the exam was unavailable, which `decide` retries. The same store gives the watchers'
    private parameters, under which their findings (``--gozcu``) are published (`watchers.publish`, E514), and the
    K6 exam's documents, from which the K6 status is evaluated (`k6.evaluate`, E512). With no pin neither is read."""
    kos = _kos(args)
    records = []
    for place, item in enumerate(args.part or []):
        tar, _sep, sha = item.rpartition("=")
        if not sha or not Path(tar).is_file():
            raise PartError(f"part {place}: no artifact or no hash ({item!r}): the part did not finish")
        dest = Path(args.work) / f"part-{place}"
        unpack(Path(tar), sha, dest)
        records.append(read_json(dest / "part.json"))
    pin = kos.meta.get("exam_pin")  # pull's, from this run's snapshot; `decide` compares it with the snapshot again
    if pin is None:
        return _write_run(Path(args.out), parts.join(kos.push, records))
    answers, watchers = pinned_module("answers", "E509"), pinned_module("watchers", "E514")
    root, out = Path(args.root), Path(args.out)

    def unavailable() -> int:  # one class: which file of the store failed is its layout (E520), in no artifact or log
        return _write_run(out, {"exam": {"status": "unavailable", "why": "store", "exam_sha256": None}, "green": False,
                                "tests": [], "vectors": [], "controls": [], "module_less": [], "licenses": []})
    try:
        store = exam_store(Path(args.exam) if args.exam else None, pin)
        groups = applied(root / "vectors", tuple(kos.meta["manifest"]["done_mf"]), table=kos.table, tree=kos.src,
                         exam=store.visible)
        raw_params = store.read(WATCHERS_FILE)
    except answers.AnswersError:  # before any broad handler: an unread store is an outage, never the Founder's (E509)
        return unavailable()
    try:
        params = watchers.load_params(raw_params or b"")  # no defaults: the epoch's store names them (E514)
    except watchers.ParamsError:
        return unavailable()
    if fixture_lookups(root / "vectors", store.visible):  # E244 on the answers: the Founder would read them in /vec
        raise config.ConfigError("a public fixture of vectors/ carries an answer its case must compute (E509): the "
                                 "operator installs the exam's admitted vectors only")
    run = parts.join(dataclasses.replace(kos.push, groups=groups), records)
    run["exam"] = {"status": "read", "exam_sha256": store.pin}
    run["watchers"] = _published(Path(args.gozcu) if args.gozcu else None, kos.meta.get("head"), params)
    run["k6"] = _k6_block(store, kos.meta, config.load_summary(root))
    traces = Path(args.target) / "hedef.json" if args.target else None
    if traces is not None and traces.is_file():  # `kos_hedef`'s base run of the copy target: counts, no verdict
        run["target"] = _target_counts(read_json(traces), kos.meta.get("head"))
    write_json(out / "run.json", run)
    if answers.canary_hits([out], store.visible.canary):  # what would carry the answers out is never uploaded
        (out / "run.json").unlink()
        raise config.ConfigError("run/ holds the exam's canary: nothing of it is uploaded (E509)")
    output(green=run["green"])
    return 0


WATCHERS_FILE = "watchers.json"  # the epoch's watcher parameters in the exam store (`watchers.load_params`, E514)
K6_FILES = ("k6/exam.json", "k6/runs.json", "k6/held_paths.json", "k6/live_ready.json")  # E512, all optional


@dataclass(frozen=True)
class PinnedStore:
    """The exam store `kos` fetched, at the epoch's pin (E516): the visible answers (`answers.Exam`) and every other
    file its manifest lists, each read only through the manifest (`answers.read_store`, `answers.verify`)."""

    root: Path
    pin: str
    manifest: bytes
    listed: dict[str, Any]
    salt: str
    visible: Any

    def read(self, rel: str) -> bytes | None:
        """A file of this exam version, checked against the manifest; None when the manifest does not list it."""
        if rel not in self.listed:
            return None
        answers = pinned_module("answers", "E509")
        _manifest, files = answers.read_store(self.root, self.pin, (rel,))
        answers.verify(self.manifest, files, self.pin)
        return files[rel]


def exam_store(where: Path | None, pin: str) -> PinnedStore:
    """The exam store at ``where`` (a checkout of it), at the pin (E516); `answers.AnswersError` when it is not there,
    cannot be read or is not the pinned bytes (`answers.load`, E509). The error names no file of the store."""
    answers = pinned_module("answers", "E509")
    if where is None or not where.is_dir():
        raise answers.AnswersError("the exam store was not fetched")
    manifest, files = answers.read_store(where, pin)
    exam = answers.load(manifest, files, pin)
    data = json.loads(manifest)  # `answers.load` held these bytes to the pin and read them as a store manifest
    return PinnedStore(where, pin, manifest, dict(data["files"]), data["salt"], exam)


def _json_or_none(raw: bytes | None) -> Any:
    try:
        return None if raw is None else json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, RecursionError):
        return None


def _published(gozcu: Path | None, head: str | None, params: Any) -> dict[str, Any]:
    """The watchers' verdict on this head (E516): `gozcu`'s findings published under the epoch's private parameters
    (`watchers.publish`: the one istismar rule, `watchers.level`, and the salted evidence hashes). A `gozcu` document
    of another head, or one whose findings are not the watchers' own, is no verdict: `decide` reads it as infra. The
    static pass confirms nothing (E521): a finding that says it was confirmed did not come from it."""
    watchers = pinned_module("watchers", "E514")
    doc = read_json(gozcu / "gozcu.json") if gozcu is not None and (gozcu / "gozcu.json").is_file() else None
    if not (isinstance(doc, dict) and doc.get("head") == head):
        return {"head": head, "status": "missing"}
    if doc.get("status") == "too_large":
        return {"head": head, "status": "too_large"}
    fields = {f.name for f in dataclasses.fields(watchers.Finding)}
    found = doc.get("findings")
    if doc.get("status") != "read" or not isinstance(found, list) or not all(
            isinstance(f, dict) and set(f) == fields and f["watcher"] in watchers.WATCHERS
            and f["proposed"] in watchers.LEVELS and isinstance(f["declared"], bool)
            and type(f["confirmed"]) is int and f["confirmed"] == 0 for f in found):
        return {"head": head, "status": "malformed"}
    published = watchers.publish([watchers.Finding(**f) for f in found], params)
    return {"head": head, "status": "read", "published": published, "unverifiable": 0}


def _k6_block(store: PinnedStore, meta: dict[str, Any], summary_cfg: config.Summary) -> dict[str, Any]:
    """The signed `k6` field of this run (E516, plan D7): `k6.public_field` (E520) of the evaluation `k6.evaluate`
    (E512) makes from the exam store's K6 documents (none yet: `not_live`), the epoch's salt and pin, the one copy
    target's base, the fence's recall measured with the referee's own matcher (`fence.touches_safety` on the owner's
    list), and the last signed status."""
    k6, fence = pinned_module("k6", "E512"), pinned_module("fence", "E511")
    exam, runs, held, ready = (_json_or_none(store.read(rel)) for rel in K6_FILES)
    copies = [t for t in summary_cfg.targets or () if t.kind == "copy"]
    copy = copies[0] if len(copies) == 1 else None
    recall = None
    if copy is not None and copy.safety_paths and isinstance(held, list) and all(isinstance(p, str) for p in held):
        recall = k6.fence_recall(held, lambda path: bool(fence.touches_safety([path], copy.safety_paths)))
    prev = meta.get("k6_prev")
    previous = prev.get("status") if isinstance(prev, dict) and prev.get("status") in k6.STATUSES else None
    salt = bytes.fromhex(store.salt)
    evaluation = k6.evaluate(exam, runs, salt=salt, exam_sha256=store.pin,
                             base_commit=copy.base_sha if copy is not None else None, recall=recall,
                             live_ready=ready, previous=previous)
    return k6.public_field(evaluation, salt)  # E520: the status and a sealed hash; counts and unmet stay private


def _target_counts(doc: Any, head: str | None) -> dict[str, Any] | None:
    """`kos_hedef`'s base run as counts per suite (E516): what the run artifact keeps of it; no verdict reads it."""
    if not (isinstance(doc, dict) and doc.get("head") == head and isinstance(doc.get("traces"), dict)):
        return None
    return {tid: {"fetch_ok": (t.get("fetch") or {}).get("ok") is True,
                  "suites": [{k: s.get(k) for k in ("suite", "ok", "counts", "runner_fault")}
                             for s in t.get("suites") or [] if isinstance(s, dict)]}
            for tid, t in sorted(doc["traces"].items()) if isinstance(t, dict)}


def cmd_check_snapshot(args: argparse.Namespace) -> int:
    """`cek`'s check before the snapshot is packed (E516, E509 `cek`): under a pinned exam the referee's `vectors/`
    must be the inputs alone; one that carries answers by its form (`answers.carrying`) stops the run before any
    artifact holds it. With no pin nothing is read."""
    root = Path(args.root)
    if config.load_summary(root).exam_pin is None:
        return 0
    found = pinned_module("answers", "E509").carrying([root / "vectors"])
    if found:
        raise config.ConfigError(f"vectors/ carries answers in {len(found)} file(s): under a pinned exam the operator "
                                 "installs the inputs alone (`vectors.public_vectors`, E509)")
    return 0


def cmd_watch(args: argparse.Namespace) -> int:
    """`gozcu` (E516, plan D9): the static watchers (`watchers.static_pass`, E514) on the pulled push. Keyless and runs
    no brain code; its inputs are pull's: the diff, the changed paths, the push's own ledger rows (the base's ledger
    from `base.json`), the visible cases' inputs and the changed code files at the head. It writes `gozcu.json`, the
    findings `kos` publishes under the epoch's private parameters, for this head only."""
    watchers = pinned_module("watchers", "E514")
    root, pulled, out = Path(args.root), Path(args.pulled), Path(args.out)
    meta = read_json(pulled / "meta.json")
    head, tar_bytes = meta["head"], (pulled / "brain.tar").read_bytes()
    base = read_json(pulled / "base.json")
    changed = [p for p in meta.get("changed") or [] if isinstance(p, str)]
    rows = watchers.push_rows(tar_file(tar_bytes, LEDGER_FILE),
                              base["ledger"].encode("utf-8") if isinstance(base.get("ledger"), str) else None)
    cases = visible_cases(root / "vectors")
    texts = {}
    for path in changed:
        raw = tar_file(tar_bytes, path) if watchers.is_code_path(path) else None
        if raw is not None:
            texts[path] = raw.decode("utf-8", "replace")
    try:
        findings, _suspects = watchers.static_pass((pulled / "diff.patch").read_text(encoding="utf-8"), changed, rows,
                                                   cases, head=head, base_tests=base.get("tests") or [],
                                                   head_texts=texts)
        doc = {"head": head, "status": "read", "findings": [dataclasses.asdict(f) for f in findings]}
    except watchers.InputTooLarge:
        doc = {"head": head, "status": "too_large", "findings": []}
    write_json(out / "gozcu.json", doc)
    return 0


def _watch_base(repo: Path, base: str) -> dict[str, Any]:
    """What the watchers' static pass reads of the base (E516): its ledger, so the push's own rows are told apart
    (`watchers.push_rows`), and its manifest's tests, whose ids a row may name (`watchers.Declared.covers`)."""
    ledger = gitio.file_at(repo, base, LEDGER_FILE)
    raw = gitio.file_at(repo, base, MANIFEST_FILE)
    try:
        tests = [] if raw is None else [{"id": t.id, "cmd": t.cmd, "stage": t.stage}
                                        for t in parse_manifest(raw.decode("utf-8")).tests]
    except (ManifestError, UnicodeDecodeError):
        tests = []
    try:
        text = None if ledger is None else ledger.decode("utf-8")
    except UnicodeDecodeError:
        text = None  # a ledger the referee cannot read declares nothing (`watchers.push_rows`)
    return {"ledger": text, "tests": tests}


def cmd_run_target(args: argparse.Namespace) -> int:
    """`kos_hedef` (E516, plan D8): each copy target at its base, in the pinned target image (`target_run`, E513):
    the tree fetched by its commit and copied out without `.git`, its dependencies fetched with nothing of the tree
    run (`target_run.fetch`), then each of the operator's suites run with no network (`TargetRunner`,
    `target_run.run_suite`). It writes `hedef.json`; it holds no secret and reads no answer."""
    target_run = pinned_module("target_run", "E513")
    root, pulled, out, work = Path(args.root), Path(args.pulled), Path(args.out), Path(args.work)
    boot = config.load_bootstrap(root)
    if boot.target_image is None:
        raise config.ConfigError("bootstrap.json has no target_image: the pinned exam runs the copy target in it "
                                 "(E516, plan D8)")
    traces: dict[str, Any] = {}
    copies = [t for t in config.load_summary(root).targets or () if t.kind == "copy" and t.base_sha]
    for place, target in enumerate(copies):
        repo, tree, deps = work / f"repo-{place}", work / f"tree-{place}", work / f"deps-{place}"
        repo.mkdir(parents=True, exist_ok=True)
        gitio.git(repo, "init", "--bare", "--quiet")
        gitio.git(repo, "fetch", "--quiet", "--no-tags", "--depth", "1", f"https://github.com/{target.repo}.git",
                  target.base_sha)
        extract(gitio.archive(repo, target.base_sha), tree, boot.limits.max_tree_bytes)
        fetched = target_run.fetch(tree, boot.target_suites, deps, image=boot.target_image,
                                   timeout_s=boot.limits.test_timeout_s)
        suites = []
        if fetched["ok"]:
            runner = target_run.TargetRunner.for_suites(boot.target_image, str(tree.resolve()), str(deps.resolve()),
                                                        boot.target_suites)
            suites = [target_run.run_suite(runner, s, boot.limits.test_timeout_s) for s in boot.target_suites]
        traces[target.id] = {"base_sha": target.base_sha, "suites": suites,
                             "fetch": {k: fetched[k] for k in ("ok", "problems", "files")}}
    write_json(out / "hedef.json", {"head": read_json(pulled / "meta.json")["head"], "traces": traces})
    return 0


def cmd_fence(args: argparse.Namespace) -> int:
    """The referee's K6 fence on a copy diff (E516, plan D6), with the fence's own rules (`fence`, E511): the copy
    target's changed paths against the owner's `safety_paths` while the last signed `k6.status` is not live
    (`fence.closed_reasons`; the status read only from the bytes the bundle beside ``--prev-result`` signs,
    `fence.signed_status`, never the brain's), and a brain-derived list (``--derived``, `{"security_paths": [...]}`)
    that does not cover the owner's (`fence.narrowed_reasons`). It writes `fence.json`, which `decide --fence` reads."""
    fence = pinned_module("fence", "E511")
    summary_cfg = config.load_summary(Path(args.root))
    found = [t for t in summary_cfg.targets or () if t.id == args.target]
    if not found or found[0].kind != "copy" or not found[0].safety_paths:
        raise config.ConfigError(f"fence: {args.target!r} is not a copy target with safety_paths")
    owner = list(found[0].safety_paths)
    status = fence.signed_status(*_signed_bytes(args.prev_result))
    changed = gitio.changed_paths(Path(args.copy), args.base, args.head)
    reasons = fence.closed_reasons(changed, owner, status)
    if args.derived is not None:
        derived = read_json(Path(args.derived)).get("security_paths")
        if derived is not None and not (isinstance(derived, list) and all(isinstance(d, str) for d in derived)):
            raise config.ConfigError("--derived: security_paths must be a list of path patterns")
        reasons += fence.narrowed_reasons(derived, owner)
    write_json(Path(args.out) / "fence.json", {"head": args.head, "k6_status": status, "reasons": reasons})
    return 0


def _pages(tar_bytes: bytes, kind: str, stage: int) -> dict[str, str]:
    """The pages beside the rival's diff: the seed's for the kind of push and, beside code, the stage pages the open
    table copies (`stages.STAGE_PAGES`, `26e`; E493): Stage 0's before the lock, Stage 1's past it."""
    pages: dict[str, str] = {}
    prefixes = [f"spec/tohum/{p}" for p in (SPEC_PAGES if kind == "spec" else CODE_PAGES)]
    if kind != "spec":
        prefixes += [f"spec/{p}" for p in stages.STAGE_PAGES[stage]]
    for prefix in prefixes:
        found = tar_page(tar_bytes, prefix)
        if found:
            pages[found[0]] = found[1]
    return pages


def cmd_rival(args: argparse.Namespace) -> int:
    root, pulled, out = Path(args.root), Path(args.pulled), Path(args.out)
    boot = config.load_bootstrap(root)
    policy = config.load_policy(root)
    stage = stagelock.open_table(root).stage  # the snapshot's lock, as `pull` read it: the brake and the stage pages
    meta = read_json(pulled / "meta.json")
    tar_bytes = (pulled / "brain.tar").read_bytes()
    tree = Path(args.work) / "tree"
    extract(tar_bytes, tree, boot.limits.max_tree_bytes)
    seat = extract_seat_prompt((root / "seats" / SEATS_FILE).read_text(encoding="utf-8"))
    changed = [p for p in meta["changed"] if not hidden(p)]  # the Founder's ledger is not the rival's to see (E10)
    context = build_context(meta["kind"], meta["base"], meta["head"], changed,
                            (pulled / "diff.patch").read_text(encoding="utf-8"), _pages(tar_bytes, meta["kind"], stage),
                            open_claims=meta["state"].get("open_claims", []))
    outcome = RivalOutcome()
    try:
        run_rival(boot.rival, claude_bin=resolve_claude(args.claude), seat_prompt=seat, context=context,
                  tree_root=tree, budget_usd_micros=remaining_budget(policy, meta["state"], stage),
                  max_prompt_chars=boot.limits.max_prompt_chars, out=outcome)
    finally:  # on every path, an interrupt too: what the run spent must reach `decide` (E13)
        result = outcome.as_dict()
        result["head"] = meta["head"]  # `poll` reads it from a run whose result was never signed
        write_json(out / "rival.json", result)
    output(has_repro=result["reproducer_count"] > 0 and result["verdict"] in ("refuted", "not_refuted"))
    outage = [r for r in result["reasons"] if str(r).startswith("api_error")]
    if outage:  # the job stays green so rival.json reaches `decide`, which books the cost and retries the commit
        print(f"::warning title=The seed rival could not run::{', '.join(outage)}")
    rejected = [r for r in result["reasons"] if str(r).startswith("request_rejected")]
    if rejected:
        print(f"::warning title=The API rejected the rival's request::{', '.join(rejected)}")
    return 0


def cmd_reproduce(args: argparse.Namespace) -> int:
    """The rival's reproducers (of this run, or of the pending result a retry reuses, E20) and the state's
    (proven defects and open claims, E07 E08), each on the head and, if it showed, on an empty tree (E09)."""
    root, pulled, out = Path(args.root), Path(args.pulled), Path(args.out)
    boot = config.load_bootstrap(root)
    meta = read_json(pulled / "meta.json")
    state = meta.get("state") or {}
    rival_file = Path(args.rival) / "rival.json"
    rival = read_json(rival_file) if rival_file.exists() else None
    if rival is None and meta.get("reuse_rival"):
        rival = (state.get("pending_rival") or {}).get("rival")
    attempts = rival["attempts"] if rival and rival.get("verdict") in ("refuted", "not_refuted") else []
    work = Path(args.work)
    src = work / "src"
    extract((pulled / "brain.tar").read_bytes(), src, boot.limits.max_tree_bytes)
    work.mkdir(parents=True, exist_ok=True)
    empty = Path(tempfile.mkdtemp(prefix="control-", dir=work))  # the control tree: nothing in it at all
    empty.chmod(0o755)  # mkdtemp makes it 0700; the container's user (65534) must be able to copy it like /src
    locks = (meta.get("manifest") or {}).get("lockfiles", [])
    vec = fixtures(root / "vectors", work / "vec")  # `/vec` without the expected values, as in run-tests
    runner = _runner(boot, src, Path(args.deps), vec, locks)
    control = _runner(boot, empty, Path(args.deps), vec, [])
    timeout = boot.limits.reproducer_timeout_s
    repro = run_reproducers(runner, attempts, timeout, control=control)
    wanted = set(meta.get("state_repro") or [])
    entries = ([{"key": e["key"], "source": "refutation", "reproducer": e["reproducer"]}
                for e in state.get("open_refutations", []) if e["key"] in wanted]
               + [{"key": c["id"], "source": "claim", "reproducer": c["reproducer"]}
                  for c in state.get("open_claims", []) if c["id"] in wanted and c["reproducer"] is not None])
    state_results = run_state_reproducers(runner, entries, timeout, control=control)
    write_json(out / "repro.json", {"results": repro, "state": state_results})
    return 0


def cmd_decide(args: argparse.Namespace) -> int:
    root, pulled, out = Path(args.root), Path(args.pulled), Path(args.out)
    policy = config.load_policy(root)
    meta = read_json(pulled / "meta.json")

    def optional(path: str | None, name: str) -> Any:
        if not path:
            return None
        p = Path(path) / name
        return read_json(p) if p.exists() else None

    run = optional(args.run, "run.json")
    rival = optional(args.rival, "rival.json")
    repro_doc = optional(args.repro, "repro.json")
    jobs = dict(item.split("=", 1) for item in args.job or [])
    pin = config.load_summary(root).exam_pin  # the snapshot's row, checked again against what `kos` measured (E516)
    result = decide(meta, run, rival, None if repro_doc is None else repro_doc["results"], jobs,
                    policy.rival_min_attempts, policy.repeat_reject_limit,
                    state_repro=None if repro_doc is None else repro_doc.get("state", []), now=utc_now(),
                    exam_pin=pin, fence=optional(args.fence, "fence.json") if pin else None,
                    table=stagelock.open_table(root))  # the snapshot's, as `pull` read it (E402)
    result["run"] = {"id": os.environ.get("GITHUB_RUN_ID", "local"),
                     "attempt": os.environ.get("GITHUB_RUN_ATTEMPT", "1")}
    write_json(out / "result.json", result)
    lines = [f"## Bootstrap referee: {result['verdict']}", "",
             f"- kind: `{result['kind']}`", f"- head: `{result['head']}`", f"- base: `{result['base']}`"]
    for r in result["reasons"]:
        lines.append(f"- reason: `{r['kind']}` {r.get('test_id', '')} `{r['ref']}`")
    for sig in result["learning"]["not_learning"]:
        lines.append(f"- **not learning**: `{sig}` rejected {policy.repeat_reject_limit} or more times in a row")
    for warning in result["warnings"]:
        lines.append(f"- **warning**: `{warning}`")
    if result["exit"].get("transferable"):
        lines.append(f"- **transferable**: referee tree `{result['exit']['referee_tree_sha256']}`")
    summary("\n".join(lines))
    # What only the operator can act on is said where GitHub shows it; the run itself stays green and signs.
    streak = [w for w in result["warnings"] if w.startswith("rival_side_streak")]
    if streak:
        print(f"::warning title=Rival-side failures::{streak[0]}: the rival itself failed on consecutive pushes "
              "(model, verdict, refusal, budget); none of it counts against the Founder")
    rejected = [w for w in result["warnings"] if w.startswith("request_rejected")]
    if rejected:
        print(f"::warning title=Request rejected by the API::{', '.join(rejected)}")
    groups = [w.split(":", 1)[1] for w in result["warnings"] if w.startswith("vector_group_missing:")]
    if groups:
        print(f"::warning title=Seed vector groups missing::{', '.join(groups)}: a finished micro-feature owns them "
              "but the seed has no vectors yet; the exit waits for them (a seed epoch adds them, not the Founder)")
    if result["state"].get("outage_stop"):
        print(f"::error title=Stopped for the operator::{result['state']['outage_stop']} on {result['head']}: the "
              "referee will not retry it by itself")
    output(verdict=result["verdict"])
    return 0


def cmd_pack(args: argparse.Namespace) -> int:
    output(sha256=pack_dir(Path(args.dir), Path(args.out)))
    return 0


def cmd_unpack(args: argparse.Namespace) -> int:
    unpack(Path(args.tar), args.sha256, Path(args.out))
    return 0


def cmd_seed_hash(args: argparse.Namespace) -> int:
    tar_bytes = gitio.archive(Path(args.brain), args.commit)
    print(tree_hash(tar_bytes, "spec/tohum", forbid_operator_names=False))
    return 0


def cmd_seed_epoch(args: argparse.Namespace) -> int:
    """The ``seed_epochs[]`` row of a seed delivery (`25` 10b, `26c`): the delivered brain commit with its seed trees,
    and the ``seed/bootstrap/`` the referee runs (read from ``--source``, by default the brain commit itself)."""
    brain = Path(args.brain)
    commit = gitio.git(brain, "rev-parse", "--verify", f"{args.commit}^{{commit}}").decode().strip()
    spec_tohum, seed = seed_trees(gitio.archive(brain, commit, SEED_DIRS))
    if spec_tohum is None:
        raise TreeError(f"no files under spec/tohum/ at {commit}: that is not a seed delivery")
    source = Path(args.source) if args.source else brain
    bootstrap = tree_hash(gitio.archive(source, args.source_commit or commit, ("seed/bootstrap",)), "seed/bootstrap",
                          forbid_operator_names=False)
    row = {"commit": commit, "spec_tohum_sha256": spec_tohum, "seed_sha256": seed, "bootstrap_sha256": bootstrap}
    if args.exam_sha256 is not None:  # E516: the epoch that pins the private exam, and every epoch after it
        if not config.HEX64_RE.match(args.exam_sha256):
            raise config.ConfigError("--exam-sha256 is the sha256 of the exam store's manifest: 64 hex characters")
        row["exam_sha256"] = args.exam_sha256
    print(canon.dump(row), end="")
    return 0


def cmd_import(args: argparse.Namespace) -> int:
    log = run_import(Path(args.result), Path(args.bundle), args.identity, args.sigstore_python,
                     args.brain, args.referee, args.toy)  # `--toy ""` stops (E498)
    print(json.dumps(log, indent=2, sort_keys=True))
    return 0


def cmd_stage_open(args: argparse.Namespace) -> int:
    """`25a` 9, `asama-0/10a` "Kilidin açılışı": after Stage 0's PASS row, write ``setup/stage.json`` (`26c`)."""
    lock = stagelock.open_stage(Path(args.referee), Path(args.toy), Path(args.copy), args.ref, args.identity,
                                args.sigstore_python, Path(args.result))
    print(json.dumps(lock, indent=2, sort_keys=True))
    print("Review setup/stage.json in the referee checkout, then commit and push it yourself.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="snowball_bootstrap")
    sub = parser.add_subparsers(dest="command", required=True)

    def add(name: str, fn, *opts: tuple[str, dict]) -> None:
        p = sub.add_parser(name)
        for flag, kw in opts:
            p.add_argument(flag, **kw)
        p.set_defaults(fn=fn)

    root = ("--root", {"default": "."})
    req = {"required": True}
    add("control", cmd_control, root, ("--control", {"help": "a loop job's control.json (`29p`)"}),
        ("--job", {}), ("--event", {}), ("--github-output", {}))
    add("config-value", cmd_config_value, root)
    add("poll", cmd_poll, root, ("--out", req), ("--remote", {}))
    add("licenses", cmd_licenses, root, ("--wheels", req), ("--out", {}))
    add("fetch-state", cmd_fetch_state, root, ("--out", req), ("--identity", req), ("--sigstore-python", req))
    add("pull", cmd_pull, root, ("--state", req), ("--work", req), ("--out", req), ("--remote", {}),
        ("--prev-result", {"help": "the last signed result fetch-state verified; read only under a pinned exam"}))
    add("fetch-deps", cmd_fetch_deps, ("--pulled", req), ("--work", req), ("--out", req))
    add("run-tests", cmd_run_tests, root, ("--pulled", req), ("--deps", req), ("--work", req), ("--out", req))
    add("run-part", cmd_run_part, root, ("--part", {"required": True, "help": "K/N: part K of N, from 0 (E440)"}),
        ("--pulled", req), ("--deps", req), ("--work", req), ("--out", req))
    add("join-parts", cmd_join_parts, root, ("--pulled", req), ("--deps", req), ("--work", req), ("--out", req),
        ("--part", {"action": "append", "help": "TAR=SHA256 of each part's artifact, in part order"}),
        ("--exam", {"help": "the exam store kos fetched; read only under a pinned exam (E516)"}),
        ("--gozcu", {"help": "gozcu's output directory (gozcu.json); read only under a pinned exam (E516)"}),
        ("--target", {"help": "kos_hedef's output directory (hedef.json); read only under a pinned exam"}))
    add("check-snapshot", cmd_check_snapshot, root)
    add("watch", cmd_watch, root, ("--pulled", req), ("--out", req))
    add("run-target", cmd_run_target, root, ("--pulled", req), ("--work", req), ("--out", req))
    add("fence", cmd_fence, root, ("--copy", dict(req, help="a local clone of the copy target")), ("--base", req),
        ("--head", req), ("--target", dict(req, help="the copy target's id in setup/summary.json")),
        ("--derived", {"help": "a JSON file {security_paths: [...]}, the brain-derived list"}),
        ("--prev-result", {"help": "the last signed result, whose k6.status opens the fence"}), ("--out", req))
    add("rival", cmd_rival, root, ("--pulled", req), ("--work", req), ("--out", req),
        ("--claude", {"help": "path of the claude CLI (default: the one on PATH)"}))
    add("reproduce", cmd_reproduce, root, ("--pulled", req), ("--deps", req), ("--rival", req),
        ("--work", req), ("--out", req))
    add("decide", cmd_decide, root, ("--pulled", req), ("--run", {}), ("--rival", {}), ("--repro", {}),
        ("--job", {"action": "append"}), ("--out", req),
        ("--fence", {"help": "a fence.json of the copy diff (cmd fence); read only under a pinned exam"}))
    add("pack", cmd_pack, ("--dir", req), ("--out", req))
    add("unpack", cmd_unpack, ("--tar", req), ("--sha256", req), ("--out", req))
    add("seed-hash", cmd_seed_hash, ("--brain", req), ("--commit", req))
    add("seed-epoch", cmd_seed_epoch, ("--brain", req), ("--commit", req),
        ("--source", {"help": "repository whose seed/bootstrap/ the referee runs (default: the brain)"}),
        ("--source-commit", {"help": "commit of --source (default: --commit)"}),
        ("--exam-sha256", {"help": "the exam store manifest's sha256, from the epoch that pins it on (E516)"}))
    add("import", cmd_import, ("--result", req), ("--bundle", req), ("--identity", req),
        ("--sigstore-python", req), ("--brain", dict(req, help="the brain repository (URL or path) the commit is in")),
        ("--referee", dict(req, help="the referee repository (URL or path): its main is cloned bare, built on and "
                                     "pushed to; no checkout is read or written")),
        ("--toy", {"help": "the toy target's repository (URL or path), at Stage 0's exit"}))
    add("stage-open", cmd_stage_open, ("--referee", dict(req, help="the referee repository's local checkout")),
        ("--toy", dict(req, help="a local clone of the toy target")),
        ("--copy", dict(req, help="a local clone of the copy target")),
        ("--ref", {"default": stagelock.DEFAULT_REF, "help": "the targets' brain/state in those clones"}),
        ("--identity", dict(req, help="the loop workflow's signing identity (its yaz job anchors the roots; each "
                                      "root's bundle is read from brain/state, .brain/chain/<root>.sigstore.json)")),
        ("--sigstore-python", req),
        ("--result", dict(req, help="the signed (A) result the last transfer imported (its result_sha256)")))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.fn(args)
    except (config.ConfigError, ImportErrorStop, gitio.GitError, TreeError, PartError) as exc:
        print(f"stop: {exc}", file=sys.stderr)
        return 2
