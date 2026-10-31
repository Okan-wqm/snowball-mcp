"""The stage lock and the counter it is bound to (`tohum/02` 5, `asama-0/10a` "Kilidin açılışı", `tohum/25a` 9, `26c`).

``setup/imports.jsonl`` is the operator's human-touch counter: one chained row per touch (`26c:39-40`, `26`), a
transfer's row the one that carries ``referee_tree_sha256`` (`29n`, `29o`). ``setup/stage.json`` is the lock:
``{stage, pass_row_sha256, toy_state_head, copy_state_head, import_line_sha256}`` (`26c:40-41`).

`stage-open` (`open_stage`; the operator's, after the PASS row, `25a` 9) reads the PASS row in the toy target's
`brain/state`, verifies both targets' chains with the seed's code and each one's last root with Sigstore, and writes the
lock. Nothing is pushed: the operator reviews the file and pushes it. The bootstrap reads the lock on every `pull` and
in `control` (`load`): the Stage 1 table and the ``stage: 1`` tests hold only once it is there, and a lock that is not
exactly `26c`'s, or whose import line is not a Stage 0 transfer of a sound counter, stops the run (`asama-0/09` test 29:
a transition that does not match is refused).

Spec sessiz, the narrowest choice each time (register E371):
- ``<state_root>`` is the top of the target's `brain/state` (`asama-1/12`): `ledger.jsonl` and `chain/root.jsonl`
  there, read at the commit ``--ref`` names in the operator's local clone (default ``refs/remotes/origin/brain/state``);
  that commit is the state head the lock records.
- The PASS row is the toy ledger's one ``events`` row (`27a`: `stage-open` reads `events`) whose ``payload`` has
  ``stage: 0`` and ``verdict: "PASS"`` (`02` 4, `19`); none or two stop. Its ``pass_row_sha256``, like
  ``import_line_sha256`` (`29o`), is the sha256 of its line without the LF. With the owner's exception in the summary
  the row names it: ``payload.owner_exception.anchor`` is the excepted anchor (`02` "Sahip istisnası", E294).
- A chained file (`26`): every line ends with LF and has no CR, is one JSON object with no key twice, and its
  ``row_hash`` is `canon.row_hash`'s with ``prev_hash`` the previous row's, 64 zeros first.
- A root (`13`, `29j`): the last ``chain/root.jsonl`` row's ``root`` is sha256 of the RFC 8785 bytes of the ledger's
  tips (each part's last ``row_hash``) at the head. Sigstore verifies a bundle the operator hands in (its home is not
  in the spec) against the root's 64 lowercase hex characters, no newline, signed by ``--identity`` (the loop
  workflow's); the bundle's log entry is the one the row names: its leaf hash, sha256(0x00 ‖ canonicalized body), is
  ``rekor_uuid`` (the last 64 characters when a 16-character tree id leads).
- Stage 0 → 1 is the only lock this seed opens (`03`: Stages 0 and 1 are the ladder's fixed root); the import line is
  the last transfer, of Stage 0; a lock already in place is never written over.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import canon, config, gitio
from .config import ConfigError

SETUP = "setup"
LOCK_FILE = "stage.json"
COUNTER_FILE = "imports.jsonl"
LOCK_KEYS = ("stage", "pass_row_sha256", "toy_state_head", "copy_state_head", "import_line_sha256")
OPENS = 1  # the stage the seed's lock opens: Stage 0 -> 1 (`03`)
LEDGER = "ledger.jsonl"
ROOTS = "chain/root.jsonl"
DEFAULT_REF = "refs/remotes/origin/brain/state"
EXCEPTED_ANCHOR = "durustluk"  # the one anchor an owner's exception names (`02`; `decide.OWNER_EXCEPTABLE`)
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
    named = [row for line, row in read_counter(root) if is_transfer(row) and line_sha256(line) == lock.import_line_sha256]
    if not named:
        raise LockStop(f"{where}.import_line_sha256 names no transfer row of {SETUP}/{COUNTER_FILE}")
    if named[0].get("stage") != lock.stage - 1 or type(named[0].get("stage")) is not int:
        raise LockStop(f"{where}.import_line_sha256 names a transfer that is not Stage {lock.stage - 1}'s")
    return lock


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


def _log_entry(bundle: Path, name: str) -> str:
    """The leaf hash of the bundle's transparency log entry (the Rekor entry UUID without its tree id)."""
    try:
        data = json.loads(bundle.read_text(encoding="utf-8"))
        entries = data["verificationMaterial"]["tlogEntries"]
        if not isinstance(entries, list) or len(entries) != 1:
            raise ValueError("not one log entry")
        body = base64.b64decode(entries[0]["canonicalizedBody"], validate=True)
    except (OSError, UnicodeDecodeError, ValueError, KeyError, TypeError, binascii.Error) as exc:
        raise LockStop(f"{name} root bundle {bundle} is not a Sigstore bundle with one log entry: {exc}") from exc
    return hashlib.sha256(b"\x00" + body).hexdigest()


def _verify_root(root_row: dict[str, Any], bundle: Path, identity: str, sigstore_python: str, name: str) -> None:
    named = UUID.match(root_row["rekor_uuid"]).group(1)  # type: ignore[union-attr]
    if _log_entry(bundle, name) != named:
        raise LockStop(f"{name}: the root bundle's log entry is not the last root row's rekor_uuid")
    from . import importer  # the seed's one call into Sigstore, the import's (imported here: it reads this module)
    with tempfile.TemporaryDirectory(prefix="snowball-root-") as tmp:
        artifact = Path(tmp) / "root"
        artifact.write_bytes(root_row["root"].encode("ascii"))
        importer.verify_signature(artifact, bundle, identity, sigstore_python)


def _pass_line(rows: list[tuple[bytes, dict[str, Any]]]) -> tuple[bytes, dict[str, Any]]:
    found = [(line, row) for line, row in rows if row.get("part") == "events" and isinstance(row.get("payload"), dict)
             and type(row["payload"].get("stage")) is int and row["payload"]["stage"] == OPENS - 1
             and row["payload"].get("verdict") == "PASS"]
    if len(found) != 1:
        raise LockStop(f"toy brain/state {LEDGER}: " + ("no PASS row" if not found else f"{len(found)} PASS rows")
                       + f" (an events row whose payload is stage {OPENS - 1}, verdict PASS)")
    return found[0]


def open_stage(referee: Path, toy: Path, copy: Path, ref: str, identity: str, sigstore_python: str,
               toy_bundle: Path, copy_bundle: Path) -> dict[str, Any]:
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
    summary = config.load_summary(referee)
    toy_head, toy_rows, toy_root = _state(toy, ref, "toy")
    copy_head, _copy_rows, copy_root = _state(copy, ref, "copy")
    pass_line, pass_row = _pass_line(toy_rows)
    if summary.honesty_exception is not None:
        named = pass_row["payload"].get("owner_exception")
        if not isinstance(named, dict) or named.get("anchor") != EXCEPTED_ANCHOR:
            raise LockStop(f"the PASS row does not carry the owner's exception by name (payload.owner_exception.anchor "
                           f"{EXCEPTED_ANCHOR!r}, `02`)")
    _verify_root(toy_root, toy_bundle, identity, sigstore_python, "toy")
    _verify_root(copy_root, copy_bundle, identity, sigstore_python, "copy")
    lock = {"stage": OPENS, "pass_row_sha256": line_sha256(pass_line), "toy_state_head": toy_head,
            "copy_state_head": copy_head, "import_line_sha256": line_sha256(transfers[-1][0])}
    path.write_bytes(canon.dump(lock).encode("utf-8"))
    return lock
