"""The stage lock and the counter it is bound to (`tohum/02` 5, `asama-0/10a` "Kilidin açılışı", `tohum/25a` 9, `26c`).

``setup/imports.jsonl`` is the operator's human-touch counter: one chained row per touch (`26c:39-40`, `26`), a
transfer's row the one that carries ``referee_tree_sha256`` (`29n`, `29o`). ``setup/stage.json`` is the lock:
``{stage, pass_row_sha256, toy_state_head, copy_state_head, import_line_sha256}`` (`26c:40-41`). After it the counter
holds the open stage's batch transfers (`asama-1/13`, `26c` ``batch``), and `batches_done` reads them.

`stage-open` (`open_stage`; the operator's, after the PASS row, `25a` 9) reads the PASS row in the toy target's
`brain/state`, verifies both targets' chains with the seed's code and each one's last root with Sigstore, and writes the
lock. Nothing is pushed: the operator reviews the file and pushes it. The bootstrap reads the lock on every `pull` and
in `control` (`load`): the Stage 1 tables and the ``stage: 1`` tests hold only once it is there, and a lock that is not
exactly `26c`'s, or whose import line is not a Stage 0 transfer of a sound counter, stops the run (`asama-0/09` test 29:
a transition that does not match is refused).

What `stage-open` binds, before it writes anything (`02` 5: only the PASS row opens the lock):
- the referee that ran (B): the import line is the counter's last transfer, Stage 0's, and it is the line both targets'
  genesis rows name (`29o` ``import_line_sha256``; `25a` 7: the loop opens `brain/state` with the genesis row, so it is
  the ledger's first row). A transfer after the one (B) ran on opens nothing (E377).
- the two targets: each clone's genesis names its `setup/summary.json` ``targets[]`` row, the toy's and the copy's, the
  copy's on its ``base_sha`` (`29o`); the PASS row carries the copy's genesis and merge rows' hashes (`10a` #pass), and
  they are rows of the copy clone it is given (E376).
- the PASS row itself: the referee's own row, not a player's proposal (`26`, `13`: those carry ``proposed_by`` and
  ``trust: inferred``) (E388), and the owner's exception exactly as the signed (A) result the last transfer imported
  names it (`02` "Sahip istisnası": the PASS row carries it by name; `--result`, bound by its ``result_sha256``) (E379).
- each root: the bundle's transparency log entry is the root row's, its entry hash is the root (`29j`
  ``entry_root_mismatch``, `vectors/root/rekor.json`), and Sigstore verifies the bundle against the digest
  ``sha256:<root>`` (`13`: Rekor carries only the hash) (E375).

Spec sessiz, the narrowest choice each time (register E371, E375-E379, E388):
- ``<state_root>`` is the top of the target's `brain/state` (`asama-1/12`): `ledger.jsonl` and `chain/root.jsonl`
  there, read at the commit ``--ref`` names in the operator's local clone (default ``refs/remotes/origin/brain/state``);
  that commit is the state head the lock records.
- The PASS row is the toy ledger's one ``events`` row (`27a`: `stage-open` reads `events`) whose ``payload`` has
  ``stage: 0`` and ``verdict: "PASS"`` (`02` 4, `19`); none or two stop. Its ``pass_row_sha256``, like
  ``import_line_sha256`` (`29o`), is the sha256 of its line without the LF. The referee's own: no ``proposed_by``,
  ``trust: verified``, a ``derivation`` merge evidence may have (`26`: the first three). The copy's rows it carries:
  ``payload.copy_genesis_row_hash`` and ``payload.copy_merge_row_hashes`` (one or more), each a ``row_hash`` (`26`).
  The owner's exception: ``payload.owner_exception`` is the signed result's ``exit.owner_exception``, canonically the
  same, and is absent when that is.
- A chained file (`26`): every line ends with LF and has no CR, is one JSON object with no key twice, and its
  ``row_hash`` is `canon.row_hash`'s with ``prev_hash`` the previous row's, 64 zeros first.
- A root (`13`, `29j`): the last ``chain/root.jsonl`` row's ``root`` is sha256 of the RFC 8785 bytes of the ledger's
  tips (each part's last ``row_hash``) at the head. The bundle (its home is not in the spec) is one the operator hands
  in, signed by ``--identity`` (the loop workflow's); its log entry is the one the row names: its leaf hash,
  sha256(0x00 ‖ canonicalized body), is ``rekor_uuid`` (the last 64 characters when a 16-character tree id leads), and
  the body is a ``hashedrekord`` whose ``spec.data.hash`` is ``{algorithm: sha256, value: <root>}``.
- Stage 0 → 1 is the only lock this seed opens (`03`: Stages 0 and 1 are the ladder's fixed root); a lock already in
  place is never written over. Past the lock's line, every transfer is a batch transfer of the lock's stage.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import canon, config, gitio
from .config import ConfigError, Target
from .stages import BATCH_RE

SETUP = "setup"
LOCK_FILE = "stage.json"
COUNTER_FILE = "imports.jsonl"
LOCK_KEYS = ("stage", "pass_row_sha256", "toy_state_head", "copy_state_head", "import_line_sha256")
OPENS = 1  # the stage the seed's lock opens: Stage 0 -> 1 (`03`)
LEDGER = "ledger.jsonl"
ROOTS = "chain/root.jsonl"
DEFAULT_REF = "refs/remotes/origin/brain/state"
# The derivations merge evidence may have (`26`: "yalnız ilk üç derivation"): the PASS row is the referee's measurement.
REFEREE_DERIVATIONS = ("tool", "static_analysis", "test_verified")
ZERO = "0" * 64
HEX64 = re.compile(r"^[0-9a-f]{64}\Z")
SHA = re.compile(r"^[0-9a-f]{40}\Z")
UUID = re.compile(r"^(?:[0-9a-f]{16})?([0-9a-f]{64})\Z")


class LockStop(ConfigError):
    """The lock cannot be read, or `stage-open` must not write it; the message says why."""


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    found: dict[str, Any] = {}
    for key, value in pairs:
        if key in found:
            raise ValueError(f"key {key!r} twice")
        found[key] = value
    return found


def _constant(name: str) -> Any:
    raise ValueError(f"{name} is not JSON a hash can hold")


def chained_lines(data: bytes, where: str) -> list[tuple[bytes, dict[str, Any]]]:
    """Each line of a chained JSONL file (without its LF) with its row; an empty file has none. Stops on the first line
    that is not a sound link of the chain (`26`), naming ``where`` and the line."""
    if not data:
        return []
    if not data.endswith(b"\n"):
        raise LockStop(f"{where}: the last line has no newline")
    found: list[tuple[bytes, dict[str, Any]]] = []
    prev = ZERO
    for number, line in enumerate(data[:-1].split(b"\n"), start=1):
        try:
            if b"\r" in line:
                raise ValueError("a carriage return")
            row = json.loads(line.decode("utf-8"), object_pairs_hook=_unique, parse_constant=_constant)
            if not isinstance(row, dict):
                raise ValueError("not an object")
            if row.get("prev_hash") != prev:
                raise ValueError("prev_hash is not the previous row's row_hash")
            if row.get("row_hash") != canon.row_hash(row):
                raise ValueError("row_hash is not the row's")
        except (UnicodeDecodeError, ValueError, RecursionError) as exc:
            raise LockStop(f"{where} line {number} breaks the chain: {exc}") from exc
        prev = row["row_hash"]
        found.append((line, row))
    return found


def line_sha256(line: bytes) -> str:
    """A row's line hash: its bytes without the LF (`29o` ``import_line_sha256``)."""
    return hashlib.sha256(line).hexdigest()


def is_transfer(row: dict[str, Any]) -> bool:
    """A transfer's counter row, as against another touch (`29n`, `29o`)."""
    return "referee_tree_sha256" in row


def read_counter(referee: Path) -> list[tuple[bytes, dict[str, Any]]]:
    """The operator's counter, verified; none when the file is not there yet."""
    path = referee / SETUP / COUNTER_FILE
    try:
        data = path.read_bytes()
    except FileNotFoundError:
        return []
    except OSError as exc:
        raise LockStop(f"{SETUP}/{COUNTER_FILE} cannot be read: {type(exc).__name__}") from exc
    return chained_lines(data, f"{SETUP}/{COUNTER_FILE}")


@dataclass(frozen=True)
class Lock:
    stage: int
    pass_row_sha256: str
    toy_state_head: str
    copy_state_head: str
    import_line_sha256: str


def _after_the_lock(counter: list[tuple[bytes, dict[str, Any]]], lock: Lock) -> list[dict[str, Any]] | None:
    """The transfer rows after the lock's import line; None when no transfer row has that line."""
    for index, (line, row) in enumerate(counter):
        if is_transfer(row) and line_sha256(line) == lock.import_line_sha256:
            return [r for _l, r in counter[index + 1:] if is_transfer(r)]
    return None


def load(root: Path) -> Lock | None:
    """The lock as the bootstrap reads it on every pull; None before `stage-open` wrote it (Stage 0)."""
    path = root / SETUP / LOCK_FILE
    if not path.exists():
        return None
    where = f"{SETUP}/{LOCK_FILE}"
    try:
        data = json.loads(path.read_bytes().decode("utf-8"), object_pairs_hook=_unique, parse_constant=_constant)
    except (OSError, UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise LockStop(f"{where} is not readable JSON: {exc}") from exc
    if not isinstance(data, dict) or set(data) != set(LOCK_KEYS):
        raise LockStop(f"{where} must have exactly the keys {', '.join(LOCK_KEYS)} (`26c`)")
    if type(data["stage"]) is not int or data["stage"] != OPENS:
        raise LockStop(f"{where}.stage must be {OPENS}: the seed's lock opens Stage {OPENS} after Stage 0's PASS")
    for key in ("pass_row_sha256", "import_line_sha256"):
        if not isinstance(data[key], str) or not HEX64.match(data[key]):
            raise LockStop(f"{where}.{key} must be 64 lowercase hex characters")
    for key in ("toy_state_head", "copy_state_head"):
        if not isinstance(data[key], str) or not SHA.match(data[key]):
            raise LockStop(f"{where}.{key} must be a 40-character commit SHA")
    lock = Lock(**data)
    counter = read_counter(root)
    named = [row for line, row in counter if is_transfer(row) and line_sha256(line) == lock.import_line_sha256]
    if not named:
        raise LockStop(f"{where}.import_line_sha256 names no transfer row of {SETUP}/{COUNTER_FILE}")
    if named[0].get("stage") != lock.stage - 1 or type(named[0].get("stage")) is not int:
        raise LockStop(f"{where}.import_line_sha256 names a transfer that is not Stage {lock.stage - 1}'s")
    for row in _after_the_lock(counter, lock) or []:  # `asama-1/13`: past the lock, only the open stage's batches
        if type(row.get("stage")) is not int or row["stage"] != lock.stage or not isinstance(row.get("batch"), str) \
                or not BATCH_RE.match(row["batch"]):
            raise LockStop(f"{SETUP}/{COUNTER_FILE}: a transfer after the lock's line is not a Stage {lock.stage} "
                           "batch's (`asama-1/13`, `26c` batch)")
    return lock


def batches_done(root: Path, lock: Lock) -> tuple[str, ...]:
    """The batches transferred since the lock opened, in the counter's order (`26c` ``batch``, `asama-1/13`); `load`
    has checked that each later transfer is one."""
    return tuple(row["batch"] for row in _after_the_lock(read_counter(root), lock) or [])


# ---------------------------------------------------------------- stage-open

def _state(repo: Path, ref: str, name: str) -> tuple[str, list[tuple[bytes, dict[str, Any]]], dict[str, Any]]:
    """A target's state head, its ledger rows (chain verified) and its last root row (chain verified, the tips' root)."""
    try:
        head = gitio.git(repo, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}").decode().strip()
    except gitio.GitError as exc:
        raise LockStop(f"{name}: {ref} is not a commit in {repo} (fetch the target's brain/state first)") from exc
    ledger = gitio.file_at(repo, head, LEDGER)
    roots = gitio.file_at(repo, head, ROOTS)
    if ledger is None or roots is None:
        raise LockStop(f"{name} brain/state {head}: no {LEDGER if ledger is None else ROOTS}")
    rows = chained_lines(ledger, f"{name} brain/state {LEDGER}")
    anchors = chained_lines(roots, f"{name} brain/state {ROOTS}")
    if not rows or not anchors:
        raise LockStop(f"{name} brain/state {head}: {LEDGER if not rows else ROOTS} has no row")
    tips: dict[str, str] = {}
    for _line, row in rows:
        if not isinstance(row.get("part"), str):
            raise LockStop(f"{name} brain/state {LEDGER}: a row has no part")
        tips[row["part"]] = row["row_hash"]
    last = anchors[-1][1]
    root = hashlib.sha256(canon.canonical(tips)).hexdigest()
    if last.get("root") != root:
        raise LockStop(f"{name} brain/state {head}: the ledger's tips are not the last anchored root (`13`, `29j`)")
    if not isinstance(last.get("rekor_uuid"), str) or not UUID.match(last["rekor_uuid"]):
        raise LockStop(f"{name} brain/state {ROOTS}: the last root row has no rekor_uuid")
    return head, rows, last


def _log_body(bundle: Path, name: str) -> bytes:
    """The canonicalized body of the bundle's one transparency log entry."""
    try:
        data = json.loads(bundle.read_text(encoding="utf-8"))
        entries = data["verificationMaterial"]["tlogEntries"]
        if not isinstance(entries, list) or len(entries) != 1:
            raise ValueError("not one log entry")
        return base64.b64decode(entries[0]["canonicalizedBody"], validate=True)
    except (OSError, UnicodeDecodeError, ValueError, KeyError, TypeError, binascii.Error) as exc:
        raise LockStop(f"{name} root bundle {bundle} is not a Sigstore bundle with one log entry: {exc}") from exc


def _entry_hash(body: bytes) -> Any:
    """The hash a `hashedrekord` log entry records (`spec.data.hash`), or None when the body is not one."""
    try:
        data = json.loads(body.decode("utf-8"))
        return data["spec"]["data"]["hash"] if data.get("kind") == "hashedrekord" else None
    except (UnicodeDecodeError, ValueError, RecursionError, KeyError, TypeError, AttributeError):
        return None


def _verify_root(root_row: dict[str, Any], bundle: Path, identity: str, sigstore_python: str, name: str) -> None:
    named = UUID.match(root_row["rekor_uuid"]).group(1)  # type: ignore[union-attr]
    body = _log_body(bundle, name)
    if hashlib.sha256(b"\x00" + body).hexdigest() != named:
        raise LockStop(f"{name}: the root bundle's log entry is not the last root row's rekor_uuid")
    if _entry_hash(body) != {"algorithm": "sha256", "value": root_row["root"]}:
        raise LockStop(f"{name}: the root bundle's log entry does not record the root as its hash (`29j` "
                       "entry_root_mismatch)")
    from . import importer  # the seed's one call into Sigstore, the import's (imported here: it reads this module)
    importer.verify_signature(f"sha256:{root_row['root']}", bundle, identity, sigstore_python)


def _pass_line(rows: list[tuple[bytes, dict[str, Any]]]) -> tuple[bytes, dict[str, Any]]:
    found = [(line, row) for line, row in rows if row.get("part") == "events" and isinstance(row.get("payload"), dict)
             and type(row["payload"].get("stage")) is int and row["payload"]["stage"] == OPENS - 1
             and row["payload"].get("verdict") == "PASS"]
    if len(found) != 1:
        raise LockStop(f"toy brain/state {LEDGER}: " + ("no PASS row" if not found else f"{len(found)} PASS rows")
                       + f" (an events row whose payload is stage {OPENS - 1}, verdict PASS)")
    row = found[0][1]
    if "proposed_by" in row or row.get("trust") != "verified" or row.get("derivation") not in REFEREE_DERIVATIONS:
        raise LockStop("the PASS row is not the referee's own verified row: a player's proposal carries proposed_by and "
                       f"trust inferred (`26`, `13`); trust must be verified, derivation one of "
                       f"{', '.join(REFEREE_DERIVATIONS)}")
    return found[0]


def _targets(summary: config.Summary) -> tuple[Target, Target]:
    """`setup/summary.json`'s toy and copy target, one of each (`26c` ``targets[]``)."""
    kinds = {kind: [t for t in summary.targets or () if t.kind == kind] for kind in ("toy", "copy")}
    if any(len(found) != 1 for found in kinds.values()):
        raise LockStop("setup/summary.json targets[] must name one toy and one copy target (`26c`, `25` 10a)")
    return kinds["toy"][0], kinds["copy"][0]


def _genesis(rows: list[tuple[bytes, dict[str, Any]]], name: str, target: Target, import_line: str) -> dict[str, Any]:
    """The target's genesis row, its ledger's first (`25a` 7), bound to its ``targets[]`` row and to the transfer the
    lock records (`29o`)."""
    row = rows[0][1]
    payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
    if payload.get("target") != target.id:
        raise LockStop(f"{name} brain/state: the first ledger row is not the genesis of setup/summary.json's {name} "
                       f"target {target.id!r} (payload.target, `29o`; is --{name} that target's clone?)")
    if name == "copy" and payload.get("base_sha") != target.base_sha:
        raise LockStop("copy brain/state: the genesis row's base_sha is not targets[]'s for the copy (`29o`)")
    if payload.get("import_line_sha256") != import_line:
        raise LockStop(f"{name} brain/state: the genesis row names another transfer than the counter's last one "
                       "(payload.import_line_sha256, `29o`): the lock binds the referee (B) ran on")
    return row


def _carries_the_copy(payload: dict[str, Any], copy_rows: list[tuple[bytes, dict[str, Any]]]) -> None:
    """`10a` #pass: the PASS row carries the copy's genesis and merge rows' hashes, rows of the copy clone given."""
    if payload.get("copy_genesis_row_hash") != copy_rows[0][1]["row_hash"]:
        raise LockStop("the PASS row does not name the copy's genesis row (payload.copy_genesis_row_hash, `10a` #pass)")
    merges = payload.get("copy_merge_row_hashes")
    later = {row["row_hash"] for _line, row in copy_rows[1:]}
    if not isinstance(merges, list) or not merges or not all(isinstance(h, str) and h in later for h in merges) \
            or len(set(merges)) != len(merges):
        raise LockStop("the PASS row does not name the copy's merge rows, each once and each a row of the copy's "
                       "ledger after its genesis (payload.copy_merge_row_hashes, `10a` #pass)")


def _signed_exit(result: Path, transfer: dict[str, Any]) -> dict[str, Any]:
    """The ``exit`` block of the signed (A) result the transfer imported: its bytes are the row's ``result_sha256``."""
    try:
        data = result.read_bytes()
    except OSError as exc:
        raise LockStop(f"--result {result} cannot be read: {type(exc).__name__}") from exc
    if hashlib.sha256(data).hexdigest() != transfer.get("result_sha256"):
        raise LockStop("--result is not the signed result the counter's last transfer imported (its result_sha256)")
    try:
        exit_block = json.loads(data.decode("utf-8")).get("exit")
    except (UnicodeDecodeError, ValueError, RecursionError, AttributeError) as exc:
        raise LockStop(f"--result is not a result: {exc}") from exc
    if not isinstance(exit_block, dict):
        raise LockStop("--result has no exit block")
    return exit_block


def _carries_the_exception(payload: dict[str, Any], exit_block: dict[str, Any]) -> None:
    """`02` "Sahip istisnası": the PASS row carries the owner's exception by name, as the signed (A) result names it
    (``{anchor, stage, carry_to, reason, carry_commitment, measured: false}``), so the carried condition is not lost."""
    if ("owner_exception" in payload) != ("owner_exception" in exit_block):
        raise LockStop("the PASS row's owner_exception is not the signed result's: one names an owner's exception, the "
                       "other none (`02` 'Sahip istisnası')")
    if "owner_exception" in payload:
        try:
            same = canon.canonical(payload["owner_exception"]) == canon.canonical(exit_block["owner_exception"])
        except ValueError:
            same = False
        if not same:
            raise LockStop("the PASS row does not carry the owner's exception as the signed result names it "
                           "(payload.owner_exception, exit.owner_exception: anchor, stage, carry_to, reason, "
                           "carry_commitment, measured; `02`)")


def open_stage(referee: Path, toy: Path, copy: Path, ref: str, identity: str, sigstore_python: str,
               toy_bundle: Path, copy_bundle: Path, result: Path) -> dict[str, Any]:
    """Write ``setup/stage.json`` after Stage 0's PASS row; return what was written. Nothing is pushed."""
    path = referee / SETUP / LOCK_FILE
    if path.exists():
        raise LockStop(f"{SETUP}/{LOCK_FILE} is already there: the lock is open (revert its commit to close it)")
    if not (referee / SETUP / COUNTER_FILE).exists():
        raise LockStop(f"no {SETUP}/{COUNTER_FILE}: nothing accepted and transferable was imported")
    transfers = [(line, row) for line, row in read_counter(referee) if is_transfer(row)]
    if not transfers or transfers[-1][1].get("stage") != OPENS - 1 or type(transfers[-1][1].get("stage")) is not int:
        raise LockStop(f"{SETUP}/{COUNTER_FILE}: the last transfer is not Stage {OPENS - 1}'s accepted, transferable "
                       "exit (import it first)")
    import_line, transfer = line_sha256(transfers[-1][0]), transfers[-1][1]
    exit_block = _signed_exit(result, transfer)
    toy_target, copy_target = _targets(config.load_summary(referee))
    toy_head, toy_rows, toy_root = _state(toy, ref, "toy")
    copy_head, copy_rows, copy_root = _state(copy, ref, "copy")
    _genesis(toy_rows, "toy", toy_target, import_line)
    _genesis(copy_rows, "copy", copy_target, import_line)
    pass_line, pass_row = _pass_line(toy_rows)
    _carries_the_copy(pass_row["payload"], copy_rows)
    _carries_the_exception(pass_row["payload"], exit_block)
    _verify_root(toy_root, toy_bundle, identity, sigstore_python, "toy")
    _verify_root(copy_root, copy_bundle, identity, sigstore_python, "copy")
    lock = {"stage": OPENS, "pass_row_sha256": line_sha256(pass_line), "toy_state_head": toy_head,
            "copy_state_head": copy_head, "import_line_sha256": import_line}
    path.write_bytes(canon.dump(lock).encode("utf-8"))
    return lock
