"""Operator import at the Stage 0 exit and at each batch exit after it (`tohum/25a` 1-2, `asama-0/10a` #aktarim and
#oyuncak, `asama-1/13` 3: "aynı komut"). Run on the operator's machine, with the kill switch on.

It never pushes. In order: the kill switch must be on in the referee checkout's ``control.json``; the signed result is
verified with Sigstore and must be accepted and transferable; it is Stage 0's exit while no lock is in place, or the
open batch's once ``setup/stage.json`` opened Stage 1; the referee code tree is rebuilt from the pinned brain commit and
its hash compared with the signed one, the toy subtree's likewise at Stage 0's exit; the operator's counter
(``setup/imports.jsonl``) must be a sound chain. Each tree is then opened into a sibling temporary directory and hashed
again as it lies on disk. Before anything in a checkout is touched, no path the copy writes may reach, under another
name than its own, something the checkout keeps (an 8.3 short name such as ``BOOTST~1``, another case, a trailing dot
or space: the operator's Windows file system resolves them, E130, E374), at any depth. Only then are the checkouts
changed, and what each keeps is read as it lies on disk, every entry with its bytes, before and after the copy: a path
that reached a kept entry under a name the check above did not foresee changed it, and the import stops before the
counter is written (E403). In the referee checkout the import keeps the operator's files, the bootstrap referee's
``bootstrap/`` and ``.github/workflows/bootstrap.yml`` (the push judge stays, E100) and the git directory, and
replaces everything else with the referee tree, so ``referee/.github/workflows/loop.yml`` lands at
``.github/workflows/loop.yml``. The checkout is hashed once more without what it keeps, and then the counter gets its
row (`26c:39-40`): ``{ts, stage, batch?, brain_sha, referee_tree_sha256, result_sha256, toy_tree_sha256?}`` in that
order, chained (`26`), one line of compact JSON ended by LF. At Stage 0's exit the toy checkout (everything but its
git directory) becomes the toy subtree; a batch transfer leaves the toy as it is (`asama-1/13`; `25a` 2 is the Stage 0
exit's). The operator reviews ``git status`` and pushes.

Spec sessiz, the narrowest choice each time (register E370, E374, E378): the kill switch is on only when
``kill_switch`` is exactly true (`26c`'s fail-closed reading at its most restrictive for a command that must not run
otherwise); a result without ``exit.batch`` is Stage 0's exit (``stage`` 0), imported only before the lock; one with
it is a batch's, imported only while that batch is the lock's stage's open one (`stagelock.open_table`), with
``stage`` and ``batch`` from the signed result and no toy; ``result_sha256`` is sha256 of the signed result file's
bytes; ``ts`` is UTC to the second (`26c` vectors); a path that names an existing entry of the checkout under another
name stops the import when that entry is kept or on the way to it, and when the directory lists nothing it could be.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path, PurePosixPath
from typing import Callable

from . import canon, gitio, stagelock
from .treehash import OPERATOR_NAMES, extract, iter_files, tree_hash

OIDC_ISSUER = "https://token.actions.githubusercontent.com"
TOY_DIR = "tests/fixtures/toy-repo"
# What the import never touches in the referee checkout: the operator's files and directories, the bootstrap referee
# and its workflow (`25a` 1), and the git directory.
KEEP_TOP = OPERATOR_NAMES | {".git", "bootstrap"}
BOOTSTRAP_WORKFLOW = PurePosixPath(".github/workflows/bootstrap.yml")
STAGE = 0  # the stage exit this seed's bootstrap signs as transferable (`02` "Önyükleme hakemi bugün yalnız Aşama 0 ...")


class ImportErrorStop(RuntimeError):
    """The import must not proceed; the message says why."""


def verify_signature(subject: Path | str, bundle: Path, identity: str, sigstore_python: str) -> None:
    """Sigstore verifies ``bundle`` for ``subject``: a file, or a digest ``sha256:<hex>`` (a root, `stagelock`)."""
    proc = subprocess.run([sigstore_python, "-m", "sigstore", "verify", "identity", "--bundle", str(bundle),
                           "--cert-identity", identity, "--cert-oidc-issuer", OIDC_ISSUER, str(subject)],
                          capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise ImportErrorStop(f"signature verification failed: {proc.stderr.strip()[:500]}")


def kill_switch_on(referee_dir: Path) -> None:
    """`25a` 1: the import runs only with the kill switch on, read from the checkout it imports into."""
    try:
        data = json.loads((referee_dir / "control.json").read_bytes().decode("utf-8"))
    except (OSError, UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise ImportErrorStop(f"the kill switch is not on: control.json cannot be read ({type(exc).__name__})") from exc
    if not isinstance(data, dict) or data.get("kill_switch") is not True:
        raise ImportErrorStop("the kill switch is not on: control.json kill_switch must be true while importing "
                              "(`25a` 1)")


def kept(rel: PurePosixPath) -> bool:
    """What the import keeps in the referee checkout (a path relative to it)."""
    return bool(rel.parts) and (rel.parts[0] in KEEP_TOP or rel == BOOTSTRAP_WORKFLOW)


def _holds_kept(rel: PurePosixPath) -> bool:
    """A directory on the way to something kept below the top (`.github/`, `.github/workflows/`)."""
    return BOOTSTRAP_WORKFLOW.parts[:len(rel.parts)] == rel.parts and rel != BOOTSTRAP_WORKFLOW


def _git_dir(rel: PurePosixPath) -> bool:
    return rel.parts[:1] == (".git",)


def _nothing(rel: PurePosixPath) -> bool:
    return False


def _lands_on_kept(rel: PurePosixPath) -> bool:
    """A referee path the operator's case-insensitive file system would write over something kept (E130, E289)."""
    return kept(PurePosixPath(*[part.casefold() for part in rel.parts]))


def _same(a: Path, b: Path) -> bool:
    try:
        return os.path.samefile(a, b)
    except OSError:
        return False


def _reaches_kept(checkout: Path, rel: PurePosixPath, keep: Callable[[PurePosixPath], bool],
                  holds: Callable[[PurePosixPath], bool], listing: dict[Path, list[str]]) -> PurePosixPath | None:
    """Where the copy of ``rel`` into ``checkout`` lands when that is something kept, or a directory on the way to one
    reached under another name (E374); None when it lands on nothing kept. Asked of the file system, before anything is
    written: each part of ``rel`` that exists is matched to the name its directory lists (itself, or the entry the file
    system says it is: an 8.3 short name, another case, a trailing dot or space). A part the directory lists under no
    name is refused too. The walk goes on only through a directory that holds something kept (`.github/`,
    `.github/workflows/`); any other existing entry is an earlier tree's, cleared before the copy."""
    parent, at = checkout, PurePosixPath()
    for part in rel.parts:
        path = parent / part
        if not os.path.lexists(path):
            return None  # a new name: everything below it is new too
        names = listing.setdefault(parent, sorted(os.listdir(parent)))
        name = part if part in names else next((n for n in names if _same(path, parent / n)), None)
        if name is None:
            return at / part
        at, parent = at / name, parent / name
        if keep(at) or (name != part and holds(at)):
            return at
        if not holds(at):
            return None
    return None


def _refuse_aliases(checkout: Path, paths: list[PurePosixPath], keep: Callable[[PurePosixPath], bool],
                    holds: Callable[[PurePosixPath], bool], what: str) -> None:
    listing: dict[Path, list[str]] = {}
    for rel in paths:
        reached = _reaches_kept(checkout, rel, keep, holds, listing)
        if reached is not None:
            raise ImportErrorStop(f"{what}/{rel.as_posix()} would land on {reached.as_posix()} in the checkout, what the "
                                  "import keeps, under another name (an 8.3 short name, another case, a trailing dot "
                                  "or space; `25a` 1, E130): nothing was written")


def kept_state(checkout: Path, keep: Callable[[PurePosixPath], bool],
               holds: Callable[[PurePosixPath], bool]) -> dict[str, str]:
    """What ``checkout`` keeps as it lies on disk (E403): every entry at or under each kept path, by its path relative
    to the checkout, with what it is: its bytes' sha256 (a regular file), ``dir``, ``link:<target>`` or ``special``.
    The walk goes down only where ``holds`` says something kept lies below (`.github/`, `.github/workflows/`) and never
    through a link. The import reads it before anything is written and again after the copy, so any path that reached
    a kept entry, under whatever name the file system resolved, shows as a change: an entry changed, added or gone."""
    found: dict[str, str] = {}
    stack = [(checkout, PurePosixPath(), False)]
    while stack:
        directory, rel, inside = stack.pop()
        for child in sorted(directory.iterdir()):
            child_rel = rel / child.name
            whole = inside or keep(child_rel)
            if child.is_symlink():
                if whole:
                    found[child_rel.as_posix()] = "link:" + os.readlink(child)
            elif child.is_dir():
                if whole:
                    found[child_rel.as_posix()] = "dir"
                if whole or holds(child_rel):
                    stack.append((child, child_rel, whole))
            elif whole:
                found[child_rel.as_posix()] = _file_sha256(child) if child.is_file() else "special"
    return found


def _file_sha256(path: Path) -> str:
    with open(path, "rb") as handle:  # in chunks: a kept git directory may hold large packs
        return hashlib.file_digest(handle, "sha256").hexdigest()


def _kept_unchanged(before: dict[str, str], after: dict[str, str], what: str) -> None:
    changed = sorted(rel for rel in set(before) | set(after) if before.get(rel) != after.get(rel))
    if changed:
        raise ImportErrorStop(f"the copy changed what the {what} checkout keeps: {', '.join(changed[:5])} (a path of the "
                              "signed tree reached it under another name, `25a` 1, E403): reset the checkout before "
                              "anything is pushed; no counter row was written")


def disk_hash(root: Path, skip: Callable[[PurePosixPath], bool] = lambda rel: False) -> str:
    """`treehash.tree_hash`'s formula over the regular files under ``root`` as they lie on disk; ``skip`` leaves a
    relative path (a directory with all below it) out. A link or a special file stops the import."""
    lines = []
    for dirpath, dirnames, filenames in os.walk(root):
        base = Path(dirpath)
        rel_base = PurePosixPath(base.relative_to(root).as_posix())
        for name in list(dirnames):
            if (base / name).is_symlink():
                raise ImportErrorStop(f"{(rel_base / name).as_posix()} on disk is a link")
            if skip(rel_base / name):
                dirnames.remove(name)
        for name in filenames:
            rel, path = rel_base / name, base / name
            if skip(rel):
                continue
            if path.is_symlink() or not path.is_file():
                raise ImportErrorStop(f"{rel.as_posix()} on disk is not a regular file")
            lines.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {rel.as_posix()}\n")
    return hashlib.sha256("".join(sorted(lines)).encode("utf-8")).hexdigest()


def _clear(directory: Path, keep: Callable[[PurePosixPath], bool], holds: Callable[[PurePosixPath], bool],
           rel: PurePosixPath = PurePosixPath()) -> None:
    """Remove everything under ``directory`` that is not kept, descending only where something kept lies below."""
    for child in sorted(directory.iterdir()):
        child_rel = rel / child.name
        if keep(child_rel):
            continue
        if child.is_dir() and not child.is_symlink():
            if holds(child_rel):
                _clear(child, keep, holds, child_rel)
            else:
                shutil.rmtree(child)
        else:
            child.unlink()


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _transfer_of(exit_block: dict, referee_dir: Path, toy_dir: Path | None) -> tuple[int, str | None]:
    """The stage and batch this signed result transfers: Stage 0's exit before the lock, the open batch after it."""
    if "batch" not in exit_block:
        if (referee_dir / stagelock.SETUP / stagelock.LOCK_FILE).exists():
            raise ImportErrorStop("setup/stage.json is there: the lock this Stage 0 result opened is not imported again")
        return STAGE, None
    lock = stagelock.load(referee_dir)  # the lock and the counter it names; a broken one stops here
    if lock is None:
        raise ImportErrorStop("a batch's result is imported only once setup/stage.json opened its stage (`asama-1/13`)")
    stage, batch = exit_block.get("stage"), exit_block["batch"]
    if type(stage) is not int or stage != lock.stage:
        raise ImportErrorStop(f"the signed batch result is Stage {stage!r}'s, the lock opened Stage {lock.stage}")
    open_batch = stagelock.open_table(referee_dir).batch
    if batch != open_batch:
        raise ImportErrorStop(f"the signed result is batch {batch!r}'s; the open batch is {open_batch!r} (`asama-1/13`: "
                              "each batch's transfer once, in order)")
    if toy_dir is not None:
        raise ImportErrorStop("a batch transfer leaves the toy as it is (`asama-1/13`; `25a` 2 is Stage 0's exit): "
                              "run it without --toy")
    return stage, batch


def run_import(result_path: Path, bundle_path: Path, identity: str, sigstore_python: str,
               brain_repo: Path, referee_dir: Path, toy_dir: Path | None) -> dict:
    kill_switch_on(referee_dir)
    verify_signature(result_path, bundle_path, identity, sigstore_python)
    result_bytes = result_path.read_bytes()
    result = json.loads(result_bytes.decode("utf-8"))
    exit_block = result.get("exit") or {}
    if result.get("verdict") != "accepted" or exit_block.get("transferable") is not True:
        raise ImportErrorStop("the signed result does not mark this commit transferable")
    stage, batch = _transfer_of(exit_block, referee_dir, toy_dir)
    sha = exit_block["brain_sha"]
    expected = exit_block["referee_tree_sha256"]
    toy_expected = exit_block.get("toy_tree_sha256") if batch is None else None
    if toy_expected is not None and toy_dir is None:
        raise ImportErrorStop("the signed result carries the toy's tree: give --toy, its checkout (`25a` 2)")
    if not gitio.has_commit(brain_repo, sha):
        raise ImportErrorStop(f"brain commit {sha} is not in {brain_repo}; fetch it first")
    tar_bytes = gitio.archive(brain_repo, sha)
    actual = tree_hash(tar_bytes, "referee")
    if actual != expected:
        raise ImportErrorStop(f"referee tree hash {actual} differs from the signed {expected}")
    referee_paths = [path.relative_to("referee") for path, _c, _x in iter_files(tar_bytes)
                     if path.parts[:1] == ("referee",)]
    for rel in referee_paths:
        if _lands_on_kept(rel):
            raise ImportErrorStop(f"referee/{rel.as_posix()} would land on what the import keeps (an operator file, "
                                  f"bootstrap/ or {BOOTSTRAP_WORKFLOW}, `25a` 1)")
    toy_paths: list[PurePosixPath] = []
    if toy_expected is not None:
        toy_actual = tree_hash(tar_bytes, TOY_DIR, forbid_operator_names=False, fold_case=True)
        if toy_actual != toy_expected:
            raise ImportErrorStop(f"toy tree hash {toy_actual} differs from the signed {toy_expected} (`25a` 2)")
        toy_paths = [path.relative_to(TOY_DIR) for path, _c, _x in iter_files(tar_bytes)
                     if path.parts[:len(PurePosixPath(TOY_DIR).parts)] == PurePosixPath(TOY_DIR).parts]
    counter = stagelock.read_counter(referee_dir)  # a broken chain stops here, before anything is written
    prev = counter[-1][1]["row_hash"] if counter else stagelock.ZERO

    temps: list[Path] = []
    try:
        referee_tree = Path(tempfile.mkdtemp(prefix=".snowball-import-", dir=referee_dir.parent))
        temps.append(referee_tree)
        copied = extract(tar_bytes, referee_tree, max_bytes=200_000_000, prefix="referee")
        if disk_hash(referee_tree) != expected:
            raise ImportErrorStop("the referee tree as it lies on disk is not the signed tree (`25a` 1)")
        toy_tree = None
        if toy_expected is not None:
            toy_tree = Path(tempfile.mkdtemp(prefix=".snowball-import-", dir=toy_dir.parent))
            temps.append(toy_tree)
            extract(tar_bytes, toy_tree, max_bytes=50_000_000, prefix=TOY_DIR)
            if disk_hash(toy_tree) != toy_expected:
                raise ImportErrorStop("the toy tree as it lies on disk is not the signed toy tree (`25a` 2)")
        # The file system, not the names, says where each file lands: nothing kept is reached under another name.
        _refuse_aliases(referee_dir, referee_paths, kept, _holds_kept, "referee")
        if toy_tree is not None:
            _refuse_aliases(toy_dir, toy_paths, _git_dir, _nothing, TOY_DIR)
        # And what is kept is read before anything is written, to be read again after the copy (E403).
        referee_kept = kept_state(referee_dir, kept, _holds_kept)
        toy_kept = kept_state(toy_dir, _git_dir, _nothing) if toy_tree is not None else {}

        _clear(referee_dir, kept, _holds_kept)
        shutil.copytree(referee_tree, referee_dir, dirs_exist_ok=True)
        _kept_unchanged(referee_kept, kept_state(referee_dir, kept, _holds_kept), "referee")
        if disk_hash(referee_dir, skip=kept) != expected:
            raise ImportErrorStop("the referee checkout on disk, what the import keeps left out, is not the signed tree "
                                  "(`25a` 1): reset it before anything is pushed")
        toy_bytes = 0
        if toy_tree is not None:
            _clear(toy_dir, _git_dir, _nothing)
            shutil.copytree(toy_tree, toy_dir, dirs_exist_ok=True)
            _kept_unchanged(toy_kept, kept_state(toy_dir, _git_dir, _nothing), "toy")
            if disk_hash(toy_dir, skip=_git_dir) != toy_expected:
                raise ImportErrorStop("the toy checkout on disk is not the signed toy tree (`25a` 2): reset it")
            toy_bytes = sum(p.stat().st_size for p in toy_tree.rglob("*") if p.is_file())
    finally:
        for temp in temps:
            shutil.rmtree(temp, ignore_errors=True)

    row: dict = {"ts": _now(), "stage": stage}
    if batch is not None:
        row["batch"] = batch
    row.update(brain_sha=sha, referee_tree_sha256=actual, result_sha256=hashlib.sha256(result_bytes).hexdigest())
    if toy_expected is not None:
        row["toy_tree_sha256"] = toy_expected
    row["prev_hash"] = prev
    row["row_hash"] = canon.row_hash(row)
    setup = referee_dir / stagelock.SETUP
    setup.mkdir(exist_ok=True)
    with open(setup / stagelock.COUNTER_FILE, "ab") as handle:  # bytes: LF on every platform
        handle.write(json.dumps(row, separators=(",", ":")).encode("utf-8") + b"\n")
    print(f"referee: {copied} bytes; toy: {toy_bytes} bytes")
    return row
