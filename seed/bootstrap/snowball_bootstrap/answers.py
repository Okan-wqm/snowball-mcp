"""The exam's answers apart from its inputs, and the pin that binds them to an epoch (E509).

The seed's vectors file holds every case's inputs and its expected answer side by side. What the referee publishes
(the snapshot every job unpacks, the vectors the operator installs, the Founder's `/vec`) holds the inputs alone:
``split`` takes the answers out, ``fill`` puts them back, and nothing else in the referee knows where an answer sits.
A field the projection does not know is refused, never published: a new kind of answer cannot ride along unnamed.

The answers live in a private store, read by one step of the one job that runs no Founder code (`kos`). The store is
content-addressed: ``exams/<pin>/manifest.json`` lists every file of that exam version with its sha256 and a 256-bit
salt, and the pin, the epoch row's ``exam_sha256``, is the sha256 of the manifest's bytes. A job reads only the files
it needs; each one must be listed with its hash, and the manifest must hash to the pin, so one flipped byte anywhere
stops the run. A store that cannot be read or does not match its pin is ``answers_unavailable``: an outage, not the
Founder's red, never green (``AnswersError``).

The visible answers file carries a canary, a random token in no public place; ``canary_hits`` finds it in files, trees
and tar archives (nested ones too), so a job can refuse to publish what would carry the answers file out.
"""

from __future__ import annotations

import copy
import hmac
import io
import json
import re
import secrets
import tarfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Iterator, Mapping

from . import canon

REASON = "answers_unavailable"  # an outage the Founder did not cause: retried, never waived, never green (D3)
STORE_SCHEMA = "snowball-exam-store/1"
ANSWERS_SCHEMA = "snowball-exam-answers/1"
SEED_SCHEMA = "snowball-seed-vectors/1"
EXAMS = "exams"  # exams/<pin>/: one exam version, content-addressed
MANIFEST = "manifest.json"
VISIBLE = "visible/answers.json"  # the answers of the cases whose inputs are public
CANARY_PREFIX = "SBX-ANS-"
_HEX64 = re.compile("[0-9a-f]{64}")
_CANARY = re.compile(re.escape(CANARY_PREFIX) + "[0-9a-f]{32}")
_ANSWER_KEYS = ("expect", "expect_not")  # the data runner's answer fields, wherever a JSON file holds them

# Where each kind of group keeps its answers (a path below the group; `*` is every element of a list), and which
# fields its inputs may have. The kinds are the judges of `vectors.py`: its own judges by name, the data runner by
# ``"runner": "data"``.
SLOTS: dict[str, tuple[str, ...]] = {
    "chain": ("v3_broken_row", "rows/*/row_hash"),
    "cp_lower": ("cases/*/2",),
    "mcnemar": ("cases/*/2",),
    "match": ("cases/*/hits",),
    "drill": ("cases/*/drill", "cases/*/verdicts"),
    "data": ("cases/*/expect", "cases/*/changed/expect_not"),
}
# What a judge reads for the plan of its calls when no answer is at hand (`blank`): a value of each slot's type, so a
# judge runs and asks every call in order. Nothing is judged on it (`vectors.replay` refuses blank groups).
_BLANK = {"v3_broken_row": None, "row_hash": None, "2": "0", "hits": None, "drill": None, "verdicts": None,
          "expect": {}, "expect_not": {}}
_INPUT_KEYS: dict[str, dict[str, frozenset[str]]] = {
    "chain": {"": frozenset({"owner", "rows", "verify_good", "verify_v3"}), "rows/*": frozenset({"row"})},
    "cp_lower": {"": frozenset({"owner", "alpha", "cases"})},
    "mcnemar": {"": frozenset({"owner", "cases"})},
    "match": {"": frozenset({"owner", "cases"}), "cases/*": frozenset({"findings", "cases"})},
    "drill": {"": frozenset({"owner", "source", "cases"}), "cases/*": frozenset({"name", "file"})},
    "data": {"": frozenset({"owner", "runner", "interface", "source", "cases"}),
             "cases/*": frozenset({"id", "purpose", "cmd", "stdin", "fixture", "changed"}),
             "cases/*/changed": frozenset({"description", "cmd", "stdin", "fixture"})},
}
_LIST_WIDTH = {"cp_lower": 2, "mcnemar": 2}  # [x, n] and [b, c]: the answer is the third element
_TOP_KEYS = frozenset({"schema", "source"})


class AnswersError(ValueError):
    """The exam's answers cannot be had as pinned: unreadable, missing, not the pinned bytes, or not the answers of
    these inputs. Nothing is judged; the push is an outage (``REASON``), not the Founder's."""

    reason = REASON


# ---- Where the answers sit ---------------------------------------------------------------------------------------

def kind(name: str, group: Any) -> str | None:
    """The judge a group of the seed has, which says where its answers sit; None for an entry no judge knows."""
    if not isinstance(group, dict):
        return None
    if name in SLOTS and name != "data":
        return name
    return "data" if group.get("runner") == "data" else None


def unknown(spec: dict[str, Any]) -> list[str]:
    """The entries of a seed no judge knows (`schema` and `source` aside). The referee runs nothing of them; what
    publishes the seed refuses them, since their fields cannot be told apart from answers."""
    return [name for name, group in spec.items()
            if kind(name, group) is None and not (name in _TOP_KEYS and isinstance(group, str))]


def _escape(token: str) -> str:
    return token.replace("~", "~0").replace("/", "~1")


def _expand(node: Any, parts: list[str], at: list[str]) -> Iterator[tuple[list[str], Any]]:
    """Every concrete path a slot pattern names under ``node``, with the container that holds its last step."""
    if len(parts) == 1:
        yield at + [parts[0]], node
        return
    head, rest = parts[0], parts[1:]
    if head == "*":
        if not isinstance(node, list):
            raise ValueError(f"/{'/'.join(at)} must be a list")
        for i, item in enumerate(node):
            yield from _expand(item, rest, at + [str(i)])
        return
    if not isinstance(node, dict) or head not in node:
        raise ValueError(f"/{'/'.join(at + [head])} is missing")
    yield from _expand(node[head], rest, at + [head])


def _slots(spec: dict[str, Any]) -> Iterator[tuple[str, Any, str]]:
    """``(pointer, container, key)`` for every answer slot of every group, in the seed's order."""
    for name, group in spec.items():
        what = kind(name, group)
        for pattern in SLOTS[what] if what else ():
            for path, holder in _expand(group, pattern.split("/"), [name]):
                yield "/" + "/".join(_escape(p) for p in path), holder, path[-1]


def slot_pointers(spec: dict[str, Any]) -> list[str]:
    """The pointer of every answer slot of ``spec`` (seed or inputs alike), in the seed's order."""
    return [pointer for pointer, _holder, _key in _slots(spec)]


def _has(holder: Any, key: str) -> bool:
    if isinstance(holder, list):
        return key.isdigit() and int(key) < len(holder)
    return isinstance(holder, dict) and key in holder


def _nodes(node: Any, parts: list[str], at: list[str]) -> Iterator[tuple[str, Any]]:
    """Every node a pattern names under ``node`` (`*` is every element of a list), with its pointer."""
    if not parts:
        yield "/" + "/".join(_escape(p) for p in at), node
        return
    head, rest = parts[0], parts[1:]
    if head == "*":
        if not isinstance(node, list):
            raise ValueError(f"/{'/'.join(at)} must be a list")
        for i, item in enumerate(node):
            yield from _nodes(item, rest, at + [str(i)])
        return
    if not isinstance(node, dict) or head not in node:
        raise ValueError(f"/{'/'.join(at + [head])} is missing")
    yield from _nodes(node[head], rest, at + [head])


def _check_inputs(inputs: dict[str, Any]) -> None:
    """Every field of the projection is a named input: one the projection does not know might be an answer."""
    for name, group in inputs.items():
        what = kind(name, group)
        if what is None:
            continue
        for pattern, allowed in _INPUT_KEYS[what].items():
            for where, node in _nodes(group, pattern.split("/") if pattern else [], [name]):
                extra = sorted(set(node) - allowed) if isinstance(node, dict) else ["(not an object)"]
                if extra:
                    raise ValueError(f"{where}: fields the projection does not know: {', '.join(extra)}")
        width = _LIST_WIDTH.get(what)
        if width is not None and any(not isinstance(c, list) or len(c) != width for c in group.get("cases", [])):
            raise ValueError(f"{name}: every case's inputs are a list of {width}")


def split(spec: dict[str, Any], *, strict: bool = True) -> tuple[dict[str, Any], dict[str, Any]]:
    """The seed as its inputs alone and its answers apart, ``{pointer: value}``. A seed that holds no answer gives
    itself and ``{}``; one that holds some of its answers and not others is refused (half a projection). ``strict``
    (what publishes) refuses an entry no judge knows; the referee's own reading leaves it, unjudged, where it is."""
    if not isinstance(spec, dict):
        raise ValueError("a seed's vectors are a JSON object")
    if strict and unknown(spec):
        raise ValueError(f"no judge knows {', '.join(unknown(spec))}: its answers cannot be told from its inputs")
    inputs = copy.deepcopy(spec)
    slots = list(_slots(inputs))
    present = [(pointer, holder, key) for pointer, holder, key in slots if _has(holder, key)]
    if present and len(present) != len(slots):
        missing = sorted(set(p for p, _h, _k in slots) - set(p for p, _h, _k in present))
        raise ValueError(f"the seed holds some answers and not others, e.g. {missing[0]}")
    found = {}
    for pointer, holder, key in reversed(present):  # from the end, so a list keeps its earlier places
        found[pointer] = holder.pop(int(key)) if isinstance(holder, list) else holder.pop(key)
    _check_inputs(inputs)
    return inputs, dict(reversed(list(found.items())))


def fill(inputs: dict[str, Any], answers: Mapping[str, Any]) -> dict[str, Any]:
    """The seed again: ``inputs`` with every answer in its slot. Each slot takes exactly one answer: one missing,
    one the inputs already hold and one no slot names are refused, so a short store never judges a case on nothing."""
    spec = copy.deepcopy(inputs)
    slots = list(_slots(spec))
    held = [pointer for pointer, holder, key in slots if _has(holder, key)]
    if held:
        raise AnswersError(f"{held[0]}: the public inputs hold an answer")
    try:
        _check_inputs(spec)
    except ValueError as exc:
        raise AnswersError(f"the public inputs are not the projection: {exc}") from None
    used = set()
    for pointer, holder, key in slots:
        if pointer not in answers:
            raise AnswersError(f"{pointer}: no answer in the store")
        value = copy.deepcopy(answers[pointer])
        if isinstance(holder, list):
            holder.insert(int(key), value)
        else:
            holder[key] = value
        used.add(pointer)
    extra = sorted(set(answers) - used)
    if extra:
        raise AnswersError(f"the store answers {len(extra)} slots these inputs do not have, e.g. {extra[0]}")
    return spec


def blank(inputs: dict[str, Any]) -> dict[str, Any]:
    """``inputs`` with a placeholder of the right type in every slot: the judges can ask every call in order (the plan
    of `kos`'s parts, which hold no answer). Nothing may be judged on it; `vectors` marks the groups it gives."""
    spec = copy.deepcopy(inputs)
    _check_inputs(spec)
    for _pointer, holder, key in list(_slots(spec)):
        if isinstance(holder, list):
            holder.insert(int(key), copy.deepcopy(_BLANK[key]))
        else:
            holder[key] = copy.deepcopy(_BLANK[key])
    return spec


def inputs_sha256(inputs: dict[str, Any]) -> str:
    """What binds an answers file to the inputs it answers: the canonical inputs' sha256. Inputs reordered or changed
    after the answers were written are not these inputs, and their answers would land in the wrong slots."""
    return canon.sha256_hex(canon.canonical(inputs))


# ---- The store and its pin -----------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Exam:
    """One exam version's visible answers, read from the store and checked against the epoch's pin."""

    pin: str  # sha256 of the manifest's bytes: the epoch row's `exam_sha256`
    canary: str
    inputs_sha256: str
    burned: bool  # answers published before (the old seed's): a regression floor with no secrecy credit
    answers: Mapping[str, Any]


def new_salt() -> str:
    return secrets.token_hex(32)  # 256 bits: the pin cannot be searched for the content it commits to


def new_canary() -> str:
    return CANARY_PREFIX + secrets.token_hex(16)


def manifest_bytes(files: Mapping[str, bytes], salt: str) -> bytes:
    """A manifest over ``files`` (path below the exam's directory → bytes). Its sha256 is the pin."""
    if not _HEX64.fullmatch(salt):
        raise ValueError("the salt is 64 hex characters")
    for path in files:
        _safe(path)
    return canon.canonical({"schema": STORE_SCHEMA, "salt": salt,
                            "files": {p: canon.sha256_hex(files[p]) for p in sorted(files)}}) + b"\n"


def pin_of(manifest: bytes) -> str:
    return canon.sha256_hex(manifest)


def _safe(path: Any) -> str:
    """A path of the store: relative, '/'-separated, no empty, '.' or '..' step."""
    parts = PurePosixPath(path).parts if isinstance(path, str) else ()
    if (not isinstance(path, str) or not parts or path.startswith("/") or "\\" in path
            or any(p in ("", ".", "..") for p in path.split("/"))):
        raise AnswersError(f"{path!r} is not a path of the store")
    return path


def verify(manifest: bytes, files: Mapping[str, bytes], pin: str | None) -> dict[str, Any]:
    """The manifest, once its bytes hash to ``pin`` and every file given is one it lists, with the hash it lists. A
    job may hold only some of the files; it may not hold one the manifest does not name."""
    if not isinstance(pin, str) or not _HEX64.fullmatch(pin):
        raise AnswersError("the epoch pins no exam (exam_sha256 is not 64 hex characters)")
    if not hmac.compare_digest(pin_of(manifest), pin):
        raise AnswersError("the store's manifest is not the one the epoch pins")
    try:
        data = json.loads(manifest)
    except (ValueError, RecursionError):
        raise AnswersError("the manifest is not JSON") from None
    listed = data.get("files") if isinstance(data, dict) else None
    if (not isinstance(data, dict) or data.get("schema") != STORE_SCHEMA or not isinstance(listed, dict)
            or not isinstance(data.get("salt"), str) or not _HEX64.fullmatch(data["salt"])):
        raise AnswersError(f"the manifest is not a {STORE_SCHEMA} manifest")
    for path, content in files.items():
        _safe(path)
        if path not in listed:
            raise AnswersError(f"{path}: not a file the manifest lists")
        if not hmac.compare_digest(canon.sha256_hex(content), str(listed[path])):
            raise AnswersError(f"{path}: not the bytes the manifest lists")
    return data


def read_store(store: Path, pin: str | None, wanted: Iterable[str] = (VISIBLE,)) -> tuple[bytes, dict[str, bytes]]:
    """The manifest and the ``wanted`` files of the exam ``pin`` names, from a checkout of the store. A file not there
    is the store unavailable, never an empty exam."""
    if not isinstance(pin, str) or not _HEX64.fullmatch(pin):
        raise AnswersError("the epoch pins no exam (exam_sha256 is not 64 hex characters)")
    base = Path(store) / EXAMS / pin
    try:
        manifest = (base / MANIFEST).read_bytes()
        return manifest, {rel: (base / _safe(rel)).read_bytes() for rel in wanted}
    except OSError as exc:
        name = Path(exc.filename or "").name
        raise AnswersError(f"the store cannot be read: {type(exc).__name__} on {name}") from None


def load(manifest: bytes, files: Mapping[str, bytes], pin: str | None) -> Exam:
    """The visible answers of the exam ``pin`` names, checked against it."""
    verify(manifest, files, pin)
    if VISIBLE not in files:
        raise AnswersError(f"{VISIBLE}: not read")
    try:
        data = json.loads(files[VISIBLE])
    except (ValueError, RecursionError):
        raise AnswersError(f"{VISIBLE} is not JSON") from None
    if (not isinstance(data, dict) or data.get("schema") != ANSWERS_SCHEMA
            or not isinstance(data.get("canary"), str) or not _CANARY.fullmatch(data["canary"])
            or not isinstance(data.get("inputs_sha256"), str) or not _HEX64.fullmatch(data["inputs_sha256"])
            or not isinstance(data.get("burned"), bool) or not isinstance(data.get("answers"), dict)
            or not all(isinstance(p, str) and p.startswith("/") for p in data["answers"])):
        raise AnswersError(f"{VISIBLE} is not a {ANSWERS_SCHEMA} file")
    return Exam(pin, data["canary"], data["inputs_sha256"], data["burned"], data["answers"])


def open_store(store: Path, pin: str | None) -> Exam:
    """`kos`'s one read of the store: the visible answers of the pinned exam, or ``AnswersError``."""
    manifest, files = read_store(store, pin)
    return load(manifest, files, pin)


def join(inputs: dict[str, Any], exam: Exam) -> dict[str, Any]:
    """The seed the judges run: the public ``inputs`` with ``exam``'s answers, once they are the inputs it answers."""
    if not hmac.compare_digest(inputs_sha256(inputs), exam.inputs_sha256):
        raise AnswersError("the public inputs are not the inputs the store's answers answer")
    return fill(inputs, exam.answers)


def write_exam(dest: Path, inputs: dict[str, Any], answers: Mapping[str, Any], *, burned: bool,
               extra: Mapping[str, bytes] | None = None) -> tuple[str, str]:
    """A new exam version in a store at ``dest``: ``exams/<pin>/`` with the manifest and the visible answers (and any
    other files of the version, e.g. held cases). Returns ``(pin, canary)``. Nothing is overwritten."""
    fill(inputs, answers)  # the answers fit the inputs, slot for slot
    canary = new_canary()
    visible = json.dumps({"schema": ANSWERS_SCHEMA, "canary": canary, "inputs_sha256": inputs_sha256(inputs),
                          "burned": burned, "answers": dict(answers)}, ensure_ascii=False, indent=1) + "\n"
    files = {VISIBLE: visible.encode("utf-8"), **dict(extra or {})}
    manifest = manifest_bytes(files, new_salt())
    pin = pin_of(manifest)
    base = Path(dest) / EXAMS / pin
    if base.exists():
        raise FileExistsError(base)
    for rel, content in {MANIFEST: manifest, **files}.items():
        path = base / _safe(rel)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    return pin, canary


# ---- What carries answers out -----------------------------------------------------------------------------------

def blobs(paths: Iterable[Path]) -> Iterator[tuple[str, bytes]]:
    """``(name, bytes)`` of every file under ``paths`` (a `.git` folder skipped), and of every member of every tar
    archive among them, nested archives too."""
    for path in paths:
        path = Path(path)
        files = [path] if path.is_file() else sorted(
            p for p in path.rglob("*") if p.is_file() and ".git" not in p.relative_to(path).parts)
        for file in files:
            yield from _unpacked(file.as_posix(), file.read_bytes())


def _unpacked(name: str, data: bytes, depth: int = 0) -> Iterator[tuple[str, bytes]]:
    yield name, data
    if depth >= 4:
        return
    try:
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:*") as tar:
            members = [(m.name, tar.extractfile(m)) for m in tar.getmembers() if m.isfile()]
            for member, handle in members:
                if handle is not None:
                    yield from _unpacked(f"{name}!{member}", handle.read(), depth + 1)
    except (tarfile.TarError, EOFError, OSError, ValueError):
        return


def canary_hits(paths: Iterable[Path], token: str) -> list[str]:
    """Every file, or archive member, under ``paths`` whose bytes hold the canary ``token``."""
    if not _CANARY.fullmatch(token or ""):
        raise ValueError("not a canary token")
    raw = token.encode("ascii")
    return [name for name, data in blobs(paths) if raw in data]


def canary_absent(paths: Iterable[Path], token: str) -> bool:
    return not canary_hits(paths, token)


def _holds_answer_keys(value: Any) -> bool:
    if isinstance(value, dict):
        return any(k in _ANSWER_KEYS for k in value) or any(_holds_answer_keys(v) for v in value.values())
    if isinstance(value, list):
        return any(_holds_answer_keys(v) for v in value)
    return False


def carrying(paths: Iterable[Path]) -> list[str]:
    """Every JSON file, or JSON archive member, under ``paths`` that carries answers by its form: an ``expect`` or
    ``expect_not`` field anywhere in it, or a seed vectors file whose answers ``split`` finds. What a snapshot must
    never hold; this needs no answer at hand, so the job that packs the snapshot can run it."""
    found = []
    for name, data in blobs(paths):
        if not name.endswith(".json"):
            continue
        try:
            value = json.loads(data)
        except (ValueError, RecursionError):
            continue
        if _holds_answer_keys(value):
            found.append(name)
        elif isinstance(value, dict) and value.get("schema") == SEED_SCHEMA:
            try:
                if split(value)[1]:
                    found.append(name)
            except ValueError:
                found.append(name)  # a seed file the projection cannot read may hold anything
    return found
