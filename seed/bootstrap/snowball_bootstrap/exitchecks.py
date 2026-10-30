"""The (A) conditions of `asama-0/10` that `pull` checks on the brain archive it already holds (`29b`; the draft `29e`
"Tohum denetimleri": in `çek`, read from the archive, never run in a container): #kurucu-defteri, #is-akisi, #agac
and #genellik (E162's follow-up, E280-E285).

Each anchor's result is ``{status: ok | failed | undecided, reasons, why}`` in ``meta["exit_checks"]``; `decide` turns
it into the exit's conditions, and an absent or undecided result keeps the exit closed as ``not_checked``, never
passes. A check that cannot decide says why; it never becomes the Founder's ``pull_error``.
"""

from __future__ import annotations

import hashlib
from typing import Any, Callable

from . import ledgercheck, wiring
from .classify import is_agent_config
from .config import Target
from .treehash import TreeError, iter_files, tree_hash

ANCHORS = ("kurucu-defteri", "is-akisi", "agac", "genellik")
REFEREE = "referee"
TOY_DIR = "tests/fixtures/toy-repo"  # the toy target's content (`13`, `24a`), which the import copies (`25a`)
MAX_REASONS = 20


def outcome(reasons: list[str], why: str = "") -> dict[str, Any]:
    return {"status": "failed" if reasons else "ok", "reasons": list(reasons), "why": why}


def undecided(why: str) -> dict[str, Any]:
    return {"status": "undecided", "reasons": [], "why": why}


def referee_files(tar_bytes: bytes) -> dict[str, bytes]:
    """Every regular file under `referee/`, by its path in the brain."""
    return {path.as_posix(): content for path, content, _x in iter_files(tar_bytes) if path.parts[:1] == (REFEREE,)}


def referee_tree(files: dict[str, bytes], tar_bytes: bytes) -> tuple[dict[str, Any], str | None]:
    """#agac besides the operator names (the referee tree hash refuses those itself, `treehash.RESERVED_TOP`, as the
    pre-reason ``referee_tree:``): no agent configuration anywhere in `referee/` (`29f`; no exception for fixtures,
    E285), and the toy subtree's hash for the signed result, which the import's #oyuncak compares (`10a`, E131)."""
    reasons = [f"agent_config_in_referee:{path}" for path in sorted(files) if is_agent_config(path)][:MAX_REASONS]
    try:
        toy: str | None = tree_hash(tar_bytes, TOY_DIR, forbid_operator_names=False)
    except TreeError:
        toy = None
        reasons.append("toy_tree_missing")
    return outcome(reasons), toy


def _first(names: list[tuple[int, int, str]], text: str) -> tuple[int, int] | None:
    return next(((i, j) for i, j, name in names if name in text), None)


def generality(files: dict[str, bytes], targets: tuple[Target, ...] | None) -> dict[str, Any]:
    """#genellik (E284): no name from `setup/summary.json` ``targets[].identifiers`` in `referee/`, looked for
    case-insensitively as a substring of every path and of every file read as UTF-8.

    The names are never published: a file is named by its path, and a path that itself carries a name by the first 16
    hex characters of its sha256; ``why`` says which target and identifier by their index. Without a name to look for
    (no ``targets[]``, or a target without identifiers) nothing can be decided: the operator's step is missing.
    """
    if not targets or any(not t.identifiers for t in targets):
        return undecided("setup/summary.json does not name every target's identifiers in targets[] (`26c`, `25` 10a): "
                         "the operator's step, so nothing can be looked for yet (E99, E284)")
    names = [(i, j, name.casefold()) for i, t in enumerate(targets) for j, name in enumerate(t.identifiers)]
    reasons: list[str] = []
    found: list[str] = []
    for path in sorted(files):
        hit = _first(names, path[len(REFEREE) + 1:].casefold())
        shown = f"path-sha256:{hashlib.sha256(path.encode('utf-8')).hexdigest()[:16]}" if hit else path
        if hit is None:
            hit = _first(names, files[path].decode("utf-8", "replace").casefold())
        if hit is not None:
            reasons.append(f"target_name_in_referee:{shown}")
            found.append(f"{shown}: targets[{hit[0]}].identifiers[{hit[1]}]")
    return outcome(reasons[:MAX_REASONS], "; ".join(found[:MAX_REASONS]))


def _guarded(check: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    try:
        return check()
    except Exception as exc:  # noqa: BLE001  a check that breaks decides nothing: the exit stays closed and says why
        return undecided(f"the check could not run ({type(exc).__name__}); the exit stays closed until it can")


def run(tar_bytes: bytes, ledger_head: bytes | None, ledger_base: bytes | None,
        targets: tuple[Target, ...] | None) -> tuple[dict[str, dict[str, Any]], str | None]:
    """Every anchor's result, and the toy subtree's hash (None when it has none)."""
    toy: list[str | None] = [None]

    def tree() -> dict[str, Any]:
        result, toy[0] = referee_tree(referee_files(tar_bytes), tar_bytes)
        return result

    checks: dict[str, Callable[[], dict[str, Any]]] = {
        "kurucu-defteri": lambda: outcome(ledgercheck.check(ledger_head, ledger_base, whole=True)),
        "is-akisi": lambda: outcome(wiring.check(wiring.files_in(referee_files(tar_bytes)))),
        "agac": tree,
        "genellik": lambda: generality(referee_files(tar_bytes), targets),
    }
    return {anchor: _guarded(checks[anchor]) for anchor in ANCHORS}, toy[0]
