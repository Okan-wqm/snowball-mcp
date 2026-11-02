"""Held cases: run only inside the private exam repository, published only as a salted commitment (plan D5, E510).

A held case is a data case (`29d`: ``{id, purpose, cmd, stdin?, fixture, expect, changed: {..., expect_not}}``) the
Founder never saw. Its input, its answer and how the Founder's code did on it never enter a public repository, artifact,
log or job duration: the held runner is ``workflow/held.yml``, a template the operator installs in the private exam
repository, where it works from the referee's public signed results alone and needs no secret of the referee's. Its jobs
and what each may hold (the referee's rule, `tohum/08` 1: no job that holds a secret runs brain or target code):

  hazir   contents: read (the held set), actions: read (its own ledger)       - runs no brain code
          the referee's newest signed result is read and, when new, verified with Sigstore exactly as the import does
          (`25a` 1); its head is fetched from the public brain; the held inputs go out blinded (every ``expect`` empty)
  imza    actions: read, id-token: write                                       - runs no brain code
          signs the statements an earlier run judged, at the start of this run: a statement's Rekor time is a run's
          start (the schedule), never how long brain code took on a held input
  kos     nothing (``permissions: {}``); brain code only in --network none containers, as the referee's `kos_parca`
          its trace names each call by an HMAC under a per-run key, never by the input or its plain hash
  yargi   contents: read, actions: read                                        - runs no brain code
          judges the trace with the held answers (`vectors.replay`), commits to the outcome and appends a ledger row

The only thing a run makes public is Rekor's record of a signed statement, ``{schema, head, result_sha256,
held_set_sha256, commitment}``, where ``commitment = sha256(canonical({bits, n, pass, salt}))`` with a fresh 256-bit
salt the trace's key never shares. Without the salt the statement cannot be opened, so even the count of held cases is
not public (no per-push aggregate, the ladder problem, critique A-5). The plain counts, the per-case bits and the salt
stay in the ledger: one private artifact, ``held-ledger``, hash-chained like the Founder's ledger (`tohum/26`), carried
from run to run by the hash each job names and revealed at the epoch's end (`reveal`), when anyone can check every row
against its signed statement.

What the operator sets in the exam repository (never in a public one): the repository variables ``REFEREE_REPO`` (the
referee repository, owner/name) and ``HELD_SET`` (the held set's folder inside the exam repository: a ``vectors.json``
of data groups and the fixtures beside it, the referee's `vectors/` layout); optionally the secret
``REFEREE_READ_TOKEN``, a token that reads public repositories only, when the run's own token cannot download the
referee's public artifacts (unmeasured, see E510). Artifact retention of at least 8 days: the run's own artifacts keep 1
day, the ledger 8 and is carried forward at least weekly.

    python3 -m snowball_bootstrap.heldrun poll|prepare|run|judge|ledger-get|sign|reveal ...
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import hmac
import io
import json
import os
import re
import secrets
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Callable

from . import canon, config, ghapi, gitio, stagelock, stages, vectors
from .cli import MANIFEST_FILE, STATE_ARTIFACT, _runner, output, pack_dir, read_json, tar_file, write_json
from .decide import utc_now
from .importer import verify_signature
from .manifest import ManifestError, parse_manifest
from .treehash import TreeError, extract

STATEMENT_SCHEMA = "snowball-held-attestation/1"
STATEMENT_KEYS = ("schema", "head", "result_sha256", "held_set_sha256", "commitment")
ROW_KEYS = ("row_id", "ts", "head", "result_sha256", "held_set_sha256", "salt", "n", "pass", "bits", "fault",
            "seconds", "commitment", "statement_sha256", "prev_hash", "row_hash")
LEDGER_ARTIFACT = "held-ledger"
LEDGER_TAR = "ledger.tar"  # the one file of a ledger artifact: `pack` of the ledger folder
LEDGER_FILE = "ledger.jsonl"
STATEMENTS = "statements"
BUNDLES = "bundles"
TRACE_FILE = "trace.json"
RUN_FILE = "run.json"
NONE = "none"  # no ledger yet: the first run starts one
GENESIS = "0" * 64
SALT_BYTES = 32  # 256 bits: a salt no one guesses, so neither a commitment nor a trace name can be brute-forced
ELIGIBLE = ("code", "exit")  # the kinds of push whose head runs code the held cases can ask
CARRY_DAYS = 7  # an idle ledger is uploaded again after a week, before its 8 days run out
MAX_LEDGER_BYTES = 200_000_000
REFEREE_WORKFLOW = ".github/workflows/bootstrap.yml"
HELD_WORKFLOW = ".github/workflows/held.yml"
SANDBOX_FAULT = "sandbox"
HEX64 = re.compile(r"^[0-9a-f]{64}\Z")
SHA40 = re.compile(r"^[0-9a-f]{40}\Z")
BITS = re.compile(r"^[01]*\Z")


class HeldError(RuntimeError):
    """The held run must not go on; the message says why. Nothing is written to the ledger."""


# ---------------------------------------------------------------- the commitment and the statement

def new_salt() -> str:
    return secrets.token_hex(SALT_BYTES)


def commitment(salt: str, n: int, passed: int, bits: str) -> str:
    """sha256 of the outcome with its salt: binding (the reveal opens it to exactly these counts) and hiding
    (without the salt no count can be tried against it)."""
    if not isinstance(salt, str) or not HEX64.match(salt):
        raise HeldError("a commitment's salt is 256 random bits in hex")
    counts = all(isinstance(v, int) and not isinstance(v, bool) and v >= 0 for v in (n, passed))
    if not counts or not isinstance(bits, str) or not BITS.match(bits) or len(bits) != n or bits.count("1") != passed:
        raise HeldError("an outcome is n cases, the passed ones counted, one bit a case")
    return canon.sha256_hex(canon.canonical({"bits": bits, "n": n, "pass": passed, "salt": salt}))


def statement(head: str, result_sha256: str, held_set_sha256: str, commit: str) -> dict[str, str]:
    """What a held run signs: which signed result's head it ran, on which held set, and the commitment. No count."""
    return {"schema": STATEMENT_SCHEMA, "head": head, "result_sha256": result_sha256,
            "held_set_sha256": held_set_sha256, "commitment": commit}


def statement_bytes(stmt: dict[str, str]) -> bytes:
    return canon.canonical(stmt)


# ---------------------------------------------------------------- the trace

def _mac(key: str, value: str) -> str:
    return hmac.new(bytes.fromhex(key), value.encode("ascii"), hashlib.sha256).hexdigest()


def keyed(tape: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    """A part's tape (`vectors.run_part`) as the trace carries it: each call named by its HMAC under the run's key.
    The plain name is sha256 of the command and its stdin, which confirms a guessed input; the keyed one confirms
    nothing."""
    return [dict(entry, input=_mac(key, entry["input"])) for entry in tape]


def unkeyed(tape: list[dict[str, Any]], key: str, planned: list[str]) -> list[dict[str, Any]]:
    """The trace's calls named again by the inputs the judges plan; a name no planned call has is no call of this
    run."""
    names = {_mac(key, k): k for k in planned}
    out = []
    for place, entry in enumerate(tape):
        name = entry.get("input") if isinstance(entry, dict) else None
        if name not in names:
            raise vectors.TapeError(f"trace call {place} is none the held judges make under this run's key")
        out.append(dict(entry, input=names[name]))
    return out


# ---------------------------------------------------------------- the held set

def blinded(spec: Any) -> dict[str, Any]:
    """The held set as `kos` gets it: every group a data group (`29d`), each case's inputs as the Founder's projection
    reads them (`vectors._inputs`) and its answers empty. The calls the judges make, and their order, depend on the
    inputs alone, so `kos` runs exactly the calls `yargi` judges."""
    if not isinstance(spec, dict) or not spec:
        raise HeldError("a held set is a non-empty object of data groups")
    out: dict[str, Any] = {}
    for name, group in spec.items():
        if not isinstance(group, dict) or group.get("runner") != vectors.DATA_RUNNER:
            raise HeldError(f"held group {name!r} is not a data group (`29d`): only data cases run held")
        cases = []
        for case in group.get("cases") or []:
            shown = vectors._inputs(case)
            shown["expect"] = {}
            shown["changed"]["expect_not"] = {}
            cases.append(shown)
        out[name] = {"runner": vectors.DATA_RUNNER, "interface": group.get("interface"), "cases": cases}
    return out


def named_fixtures(held_dir: Path, spec: dict[str, Any], dest: Path) -> None:
    """Only the fixtures a held case names (a file or a folder, as `vectors._given` reads them): nothing else of the
    held set's folder reaches `kos`, whatever else the operator keeps beside them."""
    for group in spec.values():
        for case in group.get("cases") or []:
            for rel in [*case["fixture"], *case["changed"]["fixture"]]:
                source = inside(held_dir, rel)
                files = [source] if source.is_file() else sorted(p for p in source.rglob("*") if p.is_file())
                if not files:
                    raise HeldError(f"a held case names a fixture that is not there: {rel!r}")
                for path in files:
                    target = dest / path.relative_to(held_dir)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(path.read_bytes())


def tree_sha(folder: Path) -> str:
    """The sha256 of a folder as `pack` writes it (names, bytes; no times)."""
    with tempfile.TemporaryDirectory() as tmp:
        return pack_dir(folder, Path(tmp) / "t.tar")


def inside(base: Path, rel: str) -> Path:
    """``rel`` under ``base``, never outside it (an operator's variable is still checked)."""
    rel = str(rel or "")
    parts = rel.split("/")
    if "\\" in rel or ":" in rel or any(p in ("", ".", "..") for p in parts):
        raise HeldError(f"{rel!r} is not a relative path inside the folder it must stay in")
    return base.joinpath(*parts)


# ---------------------------------------------------------------- which signed result

def referee_identity(referee_repo: str) -> str:
    return f"https://github.com/{referee_repo}/{REFEREE_WORKFLOW}@refs/heads/main"


def held_identity(exam_repo: str) -> str:
    return f"https://github.com/{exam_repo}/{HELD_WORKFLOW}@refs/heads/main"


def eligible(result: Any) -> str | None:
    """The head a signed result asks the held cases about: a code or exit push's (a spec push runs no code)."""
    if not isinstance(result, dict) or result.get("kind") not in ELIGIBLE:
        return None
    head = result.get("head")
    return head if isinstance(head, str) and SHA40.match(head) else None


def todo(result: Any, rows: list[dict[str, Any]]) -> str | None:
    """The head to run now: the newest signed result's, unless the ledger has it (each head runs once)."""
    head = eligible(result)
    return None if head is None or head in {r["head"] for r in rows} else head


# ---------------------------------------------------------------- the ledger

def _row_ok(row: Any) -> bool:
    if not isinstance(row, dict) or set(row) != set(ROW_KEYS) or not SHA40.match(str(row["head"])):
        return False
    if row["seconds"] is not None and not (isinstance(row["seconds"], int) and not isinstance(row["seconds"], bool)
                                           and row["seconds"] >= 0):
        return False
    try:
        opened = commitment(row["salt"], row["n"], row["pass"], row["bits"])
    except HeldError:
        return False
    stmt = statement(row["head"], row["result_sha256"], row["held_set_sha256"], row["commitment"])
    return (opened == row["commitment"] and row["fault"] in (None, SANDBOX_FAULT)
            and canon.sha256_hex(statement_bytes(stmt)) == row["statement_sha256"])


def read_ledger(folder: Path) -> list[dict[str, Any]]:
    """Every row, each chained to the one before (`canon.row_hash`), numbered h1, h2, ..., and each opening its own
    commitment and statement; anything else stops the run."""
    path = folder / LEDGER_FILE
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    prev = GENESIS
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        try:
            row = json.loads(line)
        except (json.JSONDecodeError, RecursionError):
            row = None
        if not _row_ok(row) or row["row_id"] != f"h{number}" or row["prev_hash"] != prev \
                or canon.row_hash(row) != row["row_hash"]:
            raise HeldError(f"held ledger row {number} is not the chained, opening row it must be")
        prev = row["row_hash"]
        rows.append(row)
    return rows


def append_row(folder: Path, rows: list[dict[str, Any]], fields: dict[str, Any], ts: str) -> dict[str, Any]:
    """The next row, written with its statement (``statements/<sha256>.json``, the bytes `sign` signs)."""
    stmt = statement(fields["head"], fields["result_sha256"], fields["held_set_sha256"], fields["commitment"])
    data = statement_bytes(stmt)
    row = {"row_id": f"h{len(rows) + 1}", "ts": ts, **fields, "statement_sha256": canon.sha256_hex(data),
           "prev_hash": rows[-1]["row_hash"] if rows else GENESIS}
    row = {k: row[k] for k in ROW_KEYS if k != "row_hash"}
    row["row_hash"] = canon.row_hash(row)
    if not _row_ok(row):
        raise HeldError("the new held ledger row does not open its own commitment")
    (folder / STATEMENTS).mkdir(parents=True, exist_ok=True)
    (folder / STATEMENTS / f"{row['statement_sha256']}.json").write_bytes(data)
    with open(folder / LEDGER_FILE, "ab") as handle:
        handle.write(canon.canonical(row) + b"\n")
    return row


def bundle_path(folder: Path, row: dict[str, Any]) -> Path:
    return folder / BUNDLES / f"{row['statement_sha256']}.sigstore.json"


def statement_path(folder: Path, row: dict[str, Any]) -> Path:
    return folder / STATEMENTS / f"{row['statement_sha256']}.json"


def pending(folder: Path, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The rows whose statement no bundle signs yet."""
    return [r for r in rows if not bundle_path(folder, r).exists()]


def sign_pending(folder: Path, signer: Callable[[Path, Path], None]) -> list[str]:
    """Each statement left to sign, signed (``signer(statement, bundle)``); its bytes are checked against the row
    first, so a statement file swapped in the artifact is never signed."""
    signed = []
    for row in pending(folder, read_ledger(folder)):
        path = statement_path(folder, row)
        if not path.is_file() or canon.sha256_hex(path.read_bytes()) != row["statement_sha256"]:
            raise HeldError(f"{row['row_id']}: its statement file is not the one its row names")
        bundle_path(folder, row).parent.mkdir(parents=True, exist_ok=True)
        signer(path, bundle_path(folder, row))
        signed.append(row["row_id"])
    return signed


def reveal(folder: Path, verify: Callable[[Path, Path], None]) -> list[dict[str, Any]]:
    """The epoch's end (owner rule: the plain counts are revealed then, plan D5): every row opened, its signed
    statement verified (``verify(statement, bundle)`` raises on a bad one). A row not yet signed is named, never counted
    as one."""
    out = []
    for row in read_ledger(folder):
        signed = bundle_path(folder, row).exists()
        if signed:
            verify(statement_path(folder, row), bundle_path(folder, row))
        out.append({"row_id": row["row_id"], "head": row["head"], "n": row["n"], "pass": row["pass"],
                    "bits": row["bits"], "fault": row["fault"], "seconds": row["seconds"], "signed": signed,
                    "statement_sha256": row["statement_sha256"]})
    return out


# ---------------------------------------------------------------- hazir, kos, yargi

def pack_inputs(out: Path, result_bytes: bytes, held_dir: Path, brain_tar: bytes, head: str, key: str) -> None:
    """`hazir`'s artifact: the head's tree and manifest (public), the blinded held inputs and the run's facts; no
    answer. A held set whose fixture carries an answer a case must compute is refused (`vectors._lookups`, E244)."""
    spec = vectors._seed(held_dir)
    shown = blinded(spec)
    found = vectors._lookups(held_dir, spec)
    if found:
        raise HeldError("a held fixture carries an answer its case must compute: " + "; ".join(found))
    raw = tar_file(brain_tar, MANIFEST_FILE)
    try:
        manifest = parse_manifest(raw.decode("utf-8")) if raw is not None else None
    except (ManifestError, UnicodeDecodeError):
        manifest = None  # the referee rejected this head; no micro-feature is done, so no held group runs
    meta = {"head": head, "manifest": {"tests": [], "done_mf": list(manifest.done_mf) if manifest else [],
                                       "lockfiles": list(manifest.lockfiles) if manifest else []}}
    (out / "pulled").mkdir(parents=True, exist_ok=True)
    (out / "pulled" / "brain.tar").write_bytes(brain_tar)
    write_json(out / "pulled" / "meta.json", meta)
    named_fixtures(held_dir, spec, out / "inputs")
    (out / "inputs" / vectors.SEED_FILE).write_text(json.dumps(shown, ensure_ascii=False, indent=2) + "\n",
                                                    encoding="utf-8")
    write_json(out / RUN_FILE, {"head": head, "result_sha256": canon.sha256_hex(result_bytes),
                                "held_set_sha256": tree_sha(held_dir), "key": key})


def _groups(spec_dir: Path, held_in: Path, table: stages.StageTable, src: Path) -> vectors.Applied:
    done = tuple(read_json(held_in / "pulled" / "meta.json")["manifest"]["done_mf"])
    return vectors.applied(spec_dir, done, table=table, tree=src)


def run_held(held_in: Path, table: stages.StageTable, src: Path, runner_for: Callable[[Path], Any],
             timeout_s: int) -> dict[str, Any]:
    """`kos`: every call the held judges plan, run as the referee's parts run theirs (`vectors.run_part`); the trace
    names them by key and carries what the calls answered, nothing of the inputs."""
    run = read_json(held_in / RUN_FILE)
    groups = _groups(held_in / "inputs", held_in, table, src)
    planned = vectors.call_inputs(groups)
    started = datetime.datetime.now(datetime.timezone.utc)
    tape: list[dict[str, Any]] = []
    if planned:
        tape, _known = vectors.run_part(runner_for(held_in / "inputs"), groups, set(planned), timeout_s)
    seconds = int((datetime.datetime.now(datetime.timezone.utc) - started).total_seconds())
    return {"head": run["head"], "seconds": seconds, "tape": keyed(tape, run["key"])}


def outcome(records: list[dict[str, Any]]) -> tuple[int, int, str, str | None]:
    """n, passed, the bits in the judges' order, and the fault: a call docker itself failed (exit 125, E141) is the
    sandbox's, never the brain's, so such a run counts nothing and says so."""
    if any(r.get("runner_fault") for r in records):
        return 0, 0, "", SANDBOX_FAULT
    bits = "".join("1" if r["ok"] else "0" for r in records)
    return len(bits), bits.count("1"), bits, None


def judge_held(held_in: Path, held_dir: Path, trace: dict[str, Any], ledger: Path, table: stages.StageTable,
               src: Path, ts: str) -> dict[str, Any]:
    """`yargi`: the trace judged on the held answers, the outcome committed, the row appended."""
    run = read_json(held_in / RUN_FILE)
    if tree_sha(held_dir) != run["held_set_sha256"]:
        raise HeldError("the held set is not the one `hazir` packed the inputs of")
    if trace.get("head") != run["head"]:
        raise HeldError("the trace is another head's")
    groups = _groups(held_dir, held_in, table, src)
    records = vectors.replay(unkeyed(trace["tape"], run["key"], vectors.call_inputs(groups)), groups)
    n, passed, bits, fault = outcome(records)
    salt = new_salt()  # yargi's own: the trace's key is in `kos`, beside brain code, and opens nothing
    commit = commitment(salt, n, passed, bits)
    seconds = trace.get("seconds")
    fields = {"head": run["head"], "result_sha256": run["result_sha256"], "held_set_sha256": run["held_set_sha256"],
              "salt": salt, "n": n, "pass": passed, "bits": bits, "fault": fault,
              "seconds": seconds if isinstance(seconds, int) and not isinstance(seconds, bool) else None,
              "commitment": commit}
    return append_row(ledger, read_ledger(ledger), fields, ts)


# ---------------------------------------------------------------- the commands

def _zip_file(blob: bytes, name: str) -> bytes:
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        return zf.read(name)


def _ledger_from(data: bytes, folder: Path) -> list[dict[str, Any]]:
    extract(data, folder, MAX_LEDGER_BYTES)
    return read_ledger(folder)


def cmd_poll(args: argparse.Namespace) -> int:
    """Cheap first look, as the referee's `poll`: a new signed result to run, a statement to sign or a ledger to carry?
    The result is read unverified only to decide; `prepare` verifies what is run."""
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    own, token = os.environ["GITHUB_REPOSITORY"], os.environ["GH_TOKEN"]
    result = None
    art = ghapi.latest_artifact(args.referee_repo, STATE_ARTIFACT, os.environ["REFEREE_TOKEN"])
    if art is not None:
        blob = ghapi.download_zip(args.referee_repo, art["id"], os.environ["REFEREE_TOKEN"])
        for name in ("result.json", "result.json.sigstore.json"):
            (out / name).write_bytes(_zip_file(blob, name))
        try:
            result = json.loads((out / "result.json").read_bytes())
        except (ValueError, RecursionError):
            result = None
    rows: list[dict[str, Any]] = []
    ledger, carry = NONE, False
    found = ghapi.latest_artifact(own, LEDGER_ARTIFACT, token)
    if found is not None:
        data = _zip_file(ghapi.download_zip(own, found["id"], token), LEDGER_TAR)
        with tempfile.TemporaryDirectory() as tmp:
            rows = _ledger_from(data, Path(tmp))
            left = pending(Path(tmp), rows)
        ledger = f"{found['id']}={canon.sha256_hex(data)}"
        created = datetime.datetime.fromisoformat(found["created_at"].replace("Z", "+00:00"))
        stale = datetime.datetime.now(datetime.timezone.utc) - created >= datetime.timedelta(days=CARRY_DAYS)
        carry = bool(left) or stale
    head = todo(result, rows)
    output(new=head is not None, carry=carry, ledger=ledger)
    return 0


def cmd_prepare(args: argparse.Namespace) -> int:
    """`hazir` past the poll: the signed result verified as the import verifies it (`25a` 1), its head fetched from the
    public brain, the held inputs packed blinded."""
    signed, referee = Path(args.signed), Path(args.referee)
    verify_signature(signed / "result.json", signed / "result.json.sigstore.json",
                     referee_identity(args.referee_repo), args.sigstore_python)
    raw = (signed / "result.json").read_bytes()
    head = eligible(json.loads(raw))
    if head is None:
        raise HeldError("the signed result names no code head to run")
    boot = config.load_bootstrap(referee)
    repo = Path(args.work) / "brain.git"
    gitio.fetch(repo, f"https://github.com/{boot.brain_repo}.git", boot.brain_branch, head)
    if not gitio.has_commit(repo, head):
        raise HeldError(f"the brain no longer has {head}")
    held_dir = inside(Path(args.exam), args.held_set)
    pack_inputs(Path(args.out), raw, held_dir, gitio.archive(repo, head), head, new_salt())
    return 0


def _context(args: argparse.Namespace) -> tuple[config.Bootstrap, stages.StageTable, Path]:
    referee, held_in = Path(args.referee), Path(args.held_in)
    boot = config.load_bootstrap(referee)
    src = Path(args.work) / "src"
    extract((held_in / "pulled" / "brain.tar").read_bytes(), src, boot.limits.max_tree_bytes)
    return boot, stagelock.open_table(referee), src


def cmd_run(args: argparse.Namespace) -> int:
    held_in = Path(args.held_in)
    boot, table, src = _context(args)
    lockfiles = read_json(held_in / "pulled" / "meta.json")["manifest"]["lockfiles"]

    def runner_for(inputs: Path):
        subprocess.run(["docker", "pull", "--quiet", boot.image], check=True, capture_output=True)
        vec = vectors.fixtures(inputs, Path(args.work) / "vec")  # `/vec`: the held fixtures, no vectors.json
        return _runner(boot, src, Path(args.deps), vec, lockfiles)
    write_json(Path(args.out) / TRACE_FILE, run_held(held_in, table, src, runner_for, boot.limits.test_timeout_s))
    return 0


def cmd_judge(args: argparse.Namespace) -> int:
    _boot, table, src = _context(args)
    trace = read_json(Path(args.trace) / TRACE_FILE)
    ledger = Path(args.ledger)
    ledger.mkdir(parents=True, exist_ok=True)
    row = judge_held(Path(args.held_in), inside(Path(args.exam), args.held_set), trace, ledger, table, src, utc_now())
    print(f"held ledger: {row['row_id']} appended")  # nothing of the outcome: the run's log is a surface too
    return 0


def cmd_ledger_get(args: argparse.Namespace) -> int:
    """The ledger artifact a job named (``ID=SHA``), only if its bytes are that hash; ``none`` starts an empty one."""
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if args.artifact == NONE:
        return 0
    art_id, _sep, sha = args.artifact.partition("=")
    own, token = os.environ["GITHUB_REPOSITORY"], os.environ["GH_TOKEN"]
    data = _zip_file(ghapi.download_zip(own, int(art_id), token), LEDGER_TAR)
    if canon.sha256_hex(data) != sha:
        raise HeldError("the held ledger artifact is not the one its job named")
    _ledger_from(data, out)
    return 0


def _sigstore_signer(python: str) -> Callable[[Path, Path], None]:
    def sign(path: Path, bundle: Path) -> None:
        proc = subprocess.run([python, "-m", "sigstore", "sign", "--bundle", str(bundle), str(path)],
                              capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise HeldError(f"sigstore sign failed: {proc.stderr.strip()[:300]}")
    return sign


def cmd_sign(args: argparse.Namespace) -> int:
    signed = sign_pending(Path(args.ledger), _sigstore_signer(args.sigstore_python))
    print(f"held statements signed: {len(signed)}")
    return 0


def cmd_reveal(args: argparse.Namespace) -> int:
    identity = held_identity(args.exam_repo)
    rows = reveal(Path(args.ledger), lambda s, b: verify_signature(s, b, identity, args.sigstore_python))
    print(json.dumps(rows, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python3 -m snowball_bootstrap.heldrun")
    sub = parser.add_subparsers(dest="command", required=True)

    def add(name, func, *flags):
        p = sub.add_parser(name)
        for flag in flags:
            p.add_argument(flag, required=True)
        p.set_defaults(func=func)

    add("poll", cmd_poll, "--referee-repo", "--out")
    add("prepare", cmd_prepare, "--referee", "--referee-repo", "--signed", "--exam", "--held-set",
        "--sigstore-python", "--work", "--out")
    add("run", cmd_run, "--referee", "--held-in", "--deps", "--work", "--out")
    add("judge", cmd_judge, "--referee", "--held-in", "--trace", "--exam", "--held-set", "--ledger", "--work")
    add("ledger-get", cmd_ledger_get, "--artifact", "--out")
    add("sign", cmd_sign, "--ledger", "--sigstore-python")
    add("reveal", cmd_reveal, "--ledger", "--exam-repo", "--sigstore-python")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (HeldError, vectors.TapeError, TreeError, config.ConfigError) as exc:
        print(f"stop: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
