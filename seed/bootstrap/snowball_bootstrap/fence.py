"""The K6 fence, kept by the referee (E511; `tohum/05` "Fiziksel güvenlik", `tohum/03` `class_requires`).

Safety paths are touched "K6 canlı olana kadar hiç, sonra yalnız K6 kapısından" (`05`). Until E511 nothing on the
referee's side held that: the operator's ``targets[].safety_paths`` were read for their form only, the classifier that
derives the safety paths is the Founder's own code, and the check guarding ``brain/integration`` is posted by the
Founder's own App. This module is the referee's part of the rule, pure and stdlib-only:

- ``owner_paths``: a ``targets[]`` row's safety paths, required (and not empty) for a copy target, each a well-formed
  path pattern; a ConfigError otherwise, like every other operator list (`26c`).
- ``signed_status``: the ``k6.status`` of the referee's last signed result, read only from the bytes its Sigstore bundle
  signs. No result, a bundle that signs other bytes, or a result that cannot be read is never ``live``.
- ``closed_reasons``: ``safety_path_closed:<path>`` for each path of a copy head's diff the operator's list covers, and
  for each git attribute or submodule file (they change a checkout's bytes without touching the files they change),
  unless that status is ``live``. The brain's own list never decides what is fenced.
- ``narrowed_reasons`` and ``superset_ok``: a list the brain derives may only widen the operator's; an operator entry
  it is not sure to cover is ``safety_list_narrowed:<entry>``.
- ``review_step`` and ``merged_since_live``: the heads accepted through the open gate, listed in the result that signs
  the gate closed again, for the owner to review.

Paths are compared as a file system the target is checked out on reads them: case-folded, without the code points HFS+
ignores (``importer.fold``) and canonically composed. A wider match fences more, so every doubt falls closed.
"""

from __future__ import annotations

import base64
import binascii
import fnmatch
import functools
import hashlib
import json
import unicodedata
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from .config import ConfigError, _texts
from .importer import GIT_NAMES, fold
from .treehash import path_problem

LIVE = "live"  # the one k6.status that opens the fence (`03` `class_requires`)
NOT_LIVE = "not_live"  # a signed result that names no k6.status
MISSING = "missing"  # no signed result at all: the first run, or a lost state
UNBOUND = "unbound"  # bytes no signature covers, or a result that cannot be read
CLOSED = "safety_path_closed"
NARROWED = "safety_list_narrowed"
CHECK_NAME = "snowball-fence"  # the copy's second required check, the referee's gate App's (`25a` 3)
MAX_NAMED = 20  # paths named in the reasons, as pull names other path lists
# Files git reads for itself: attributes rewrite a checked-out file's bytes (eol, filters, working-tree-encoding), a
# submodule fetches from elsewhere (E478). Changing one changes fenced files without a fenced path in the diff.
GIT_INDIRECT = frozenset(fold(name) for name in GIT_NAMES)
GLOB = frozenset("*?[]")  # a `]` may close a set (`a[]c]`), so plain text never holds one


def _fold(text: str) -> str:
    return unicodedata.normalize("NFC", fold(text))


def _parts(text: str) -> tuple[str, ...]:
    """A path or pattern as its folded names; a trailing ``/`` (a directory) adds none."""
    return tuple(_fold(text).rstrip("/").split("/"))


def pattern_problem(entry: str) -> str | None:
    """Why ``entry`` is no safety path pattern; None when it is one. A pattern is a path below the target's top whose
    names may hold ``*``, ``?`` and ``[...]`` (within one name) or be ``**`` (any depth); a trailing ``/`` is
    allowed."""
    problem = path_problem(entry)
    if problem:
        return problem
    if any(name in ("", ".") for name in entry.rstrip("/").split("/")):
        return "empty or `.` name"
    return None


def owner_paths(row: Mapping[str, Any], where: str) -> tuple[str, ...]:
    """A ``targets[]`` row's ``safety_paths`` (`26c`, `05` "Fiziksel güvenlik"). A copy target must name them, and
    not none: the fence keeps exactly this list, and a missing list would fence nothing. The toy's content is the
    Founder's own fixture, so its list is optional. Each entry is a ``pattern_problem``-free pattern."""
    copy = row.get("kind") == "copy"
    if "safety_paths" not in row:
        if copy:
            raise ConfigError(f"{where}.safety_paths is required for a copy target: the K6 fence keeps it (`05`)")
        return ()
    entries = _texts(row, "safety_paths", where)
    if copy and not entries:
        raise ConfigError(f"{where}.safety_paths must name at least one path for a copy target (`05`)")
    for entry in entries:
        problem = pattern_problem(entry)
        if problem:
            raise ConfigError(f"{where}.safety_paths: {entry!r} is no path pattern ({problem})")
    return entries


def _signed_digest(bundle: bytes) -> bytes | None:
    """The sha256 a Sigstore bundle signs (``messageSignature.messageDigest``, as `sigstore sign` writes it for a
    file); None for any other shape."""
    try:
        digest = json.loads(bundle.decode("utf-8"))["messageSignature"]["messageDigest"]
        if digest["algorithm"] != "SHA2_256":
            return None
        raw = base64.b64decode(digest["digest"], validate=True)
    except (UnicodeDecodeError, ValueError, KeyError, TypeError, binascii.Error):
        return None
    return raw if len(raw) == 32 else None


def signed_status(result: bytes | None, bundle: bytes | None) -> str:
    """The ``k6.status`` of the referee's last signed result (``result.json``) whose Sigstore ``bundle`` the caller
    has verified (`fetch-state`). The status is read only from the bytes that bundle signs: a status from anywhere
    else, the brain's tree, a report or a result rewritten after the check, is never the signed one."""
    if result is None or bundle is None:
        return MISSING
    digest = _signed_digest(bundle)
    if digest is None or digest != hashlib.sha256(result).digest():
        return UNBOUND
    try:
        data = json.loads(result.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return UNBOUND
    k6 = data.get("k6") if isinstance(data, dict) else None
    status = k6.get("status") if isinstance(k6, dict) else None
    return status if isinstance(status, str) and status else NOT_LIVE


def _covers(pattern: tuple[str, ...], path: tuple[str, ...]) -> bool:
    """Whether ``pattern`` names ``path`` or a directory above it. A name is an fnmatch pattern for one name (``*``
    never crosses ``/``); a ``**`` name stands for any number of names."""

    @functools.cache
    def at(i: int, j: int) -> bool:
        if i == len(pattern):
            return True
        if pattern[i] == "**":
            return any(at(i + 1, k) for k in range(j, len(path) + 1))
        return j < len(path) and fnmatch.fnmatchcase(path[j], pattern[i]) and at(i + 1, j + 1)

    return at(0, 0)


def touches_safety(diff: Iterable[str], paths: Sequence[str]) -> list[str]:
    """The paths of ``diff`` (``git diff --name-only --no-renames``: a rename is both names) that the patterns
    ``paths`` cover, and every git attribute or submodule file at any depth; sorted, each once."""
    patterns = [_parts(p) for p in paths]
    hit = set()
    for path in diff:
        parts = _parts(path)
        if parts[-1] in GIT_INDIRECT or any(_covers(p, parts) for p in patterns):
            hit.add(path)
    return sorted(hit)


def closed_reasons(diff: Iterable[str], owner: Sequence[str], status: str) -> list[str]:
    """What a copy head's diff gets while the gate is shut: ``safety_path_closed:<path>`` for the first MAX_NAMED
    fenced paths it touches, unless ``status`` (``signed_status``) is ``live``. Only the operator's list fences."""
    if status == LIVE:
        return []
    return [f"{CLOSED}:{path}" for path in touches_safety(diff, owner)[:MAX_NAMED]]


def _name_wider(d: str, e: str) -> bool:
    """Whether the name pattern ``d`` matches every name the name pattern ``e`` matches, surely: the two are equal, or
    ``d`` is one ``*`` between a head and a tail that ``e`` begins and ends with as plain text. Any other pair is
    not sure, so it is not covered."""
    if d == e:
        return True
    if e == "**" or (GLOB - {"*"}) & set(d) or d.count("*") != 1:
        return False
    head, tail = d.split("*")
    if len(e) < len(head) + len(tail) or not (e.startswith(head) and e.endswith(tail)):
        return False
    return not GLOB & set(e[:len(head)]) and not GLOB & set(e[len(e) - len(tail):])


def _wider(d: tuple[str, ...], e: tuple[str, ...]) -> bool:
    """Whether the pattern ``d`` covers every path the pattern ``e`` covers (``_covers``), surely."""

    @functools.cache
    def at(i: int, j: int) -> bool:
        if i == len(d):
            return True
        if d[i] == "**":
            return any(at(i + 1, k) for k in range(j, len(e) + 1))
        return j < len(e) and e[j] != "**" and _name_wider(d[i], e[j]) and at(i + 1, j + 1)

    return at(0, 0)


def uncovered(derived: Sequence[str], owner: Sequence[str]) -> list[str]:
    """The operator's entries no entry of the brain's derived list surely covers, in the operator's order."""
    wide = [_parts(d) for d in derived]
    return [e for e in owner if not any(_wider(d, _parts(e)) for d in wide)]


def superset_ok(derived: Sequence[str], owner: Sequence[str]) -> bool:
    """Whether the brain's derived list only widens the operator's (`05`, `14`)."""
    return not uncovered(derived, owner)


def narrowed_reasons(derived: Sequence[str] | None, owner: Sequence[str]) -> list[str]:
    """``safety_list_narrowed:<entry>`` for the first MAX_NAMED operator entries the derived list leaves out; none
    when the brain derives no list (then the operator's list is the whole fence)."""
    if derived is None:
        return []
    return [f"{NARROWED}:{entry}" for entry in uncovered(derived, owner)[:MAX_NAMED]]


@dataclass(frozen=True)
class Passage:
    """One judged copy head: the signed status it was judged under (the previous result's), whether it was accepted,
    the fenced paths it touched (``touches_safety``) and the status the run that judged it signs."""
    head: str
    status: str
    accepted: bool
    touched: tuple[str, ...]
    status_after: str


def review_step(carried: tuple[str, ...], passage: Passage) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """One run of the review list: (what the state carries on, what this result lists for the owner). A head accepted
    through the open gate with a fenced path is carried; the result that signs the gate shut again lists them all once,
    and the list starts empty with the next ``live``."""
    if passage.accepted and passage.touched and passage.status == LIVE and passage.head not in carried:
        carried = carried + (passage.head,)
    if passage.status_after != LIVE:
        return (), carried
    return carried, ()


def merged_since_live(history: Iterable[Passage]) -> tuple[str, ...]:
    """The heads the newest result of ``history`` (oldest first) lists for review: ``review_step`` folded over it.
    The referee keeps no history (its memory is the signed state, `state`), so it runs ``review_step`` once a run."""
    carried: tuple[str, ...] = ()
    review: tuple[str, ...] = ()
    for passage in history:
        carried, review = review_step(carried, passage)
    return review
