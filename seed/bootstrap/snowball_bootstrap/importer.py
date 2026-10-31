"""Operator import at the Stage 0 exit (`tohum/25a` 1-2, `asama-0/10a` #aktarim and #oyuncak). Run on the operator's
machine, with the kill switch on.

It never pushes. In order: the kill switch must be on in the referee checkout's ``control.json``; the signed result is
verified with Sigstore and must be accepted and transferable; the referee code tree is rebuilt from the pinned brain
commit and its hash compared with the signed one, the toy subtree's likewise; the operator's counter
(``setup/imports.jsonl``) must be a sound chain. Each tree is then opened into a sibling temporary directory and hashed
again as it lies on disk; only when both are the signed trees does the import touch the checkouts. In the referee
checkout it keeps the operator's files, the bootstrap referee's ``bootstrap/`` and ``.github/workflows/bootstrap.yml``
(the push judge stays, E100) and the git directory, and replaces everything else with the referee tree, so
``referee/.github/workflows/loop.yml`` lands at ``.github/workflows/loop.yml``. The checkout is hashed once more without
what it keeps, and then the counter gets its row (`26c:39-40`): ``{ts, stage, brain_sha, referee_tree_sha256,
result_sha256, toy_tree_sha256}`` in that order, chained (`26`), one line of compact JSON ended by LF. The toy checkout
(everything but its git directory) becomes the toy subtree. The operator reviews ``git status`` and pushes.

Spec sessiz, the narrowest choice each time (register E370): the kill switch is on only when ``kill_switch`` is exactly
true (`26c`'s fail-closed reading at its most restrictive for a command that must not run otherwise); ``stage`` is 0,
the only exit this seed signs as transferable (`02`), so with ``setup/stage.json`` in place the import stops;
``result_sha256`` is sha256 of the signed result file's bytes; ``ts`` is UTC to the second (`26c` vectors).
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
STAGE = 0  # the exit this seed's bootstrap signs as transferable (`02` "Önyükleme hakemi bugün yalnız Aşama 0 ...")


class ImportErrorStop(RuntimeError):
    """The import must not proceed; the message says why."""


def verify_signature(result: Path, bundle: Path, identity: str, sigstore_python: str) -> None:
    proc = subprocess.run([sigstore_python, "-m", "sigstore", "verify", "identity", "--bundle", str(bundle),
                           "--cert-identity", identity, "--cert-oidc-issuer", OIDC_ISSUER, str(result)],
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


def _lands_on_kept(rel: PurePosixPath) -> bool:
    """A referee path the operator's case-insensitive file system would write over something kept (E130, E289)."""
    return kept(PurePosixPath(*[part.casefold() for part in rel.parts]))


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


def run_import(result_path: Path, bundle_path: Path, identity: str, sigstore_python: str,
               brain_repo: Path, referee_dir: Path, toy_dir: Path | None) -> dict:
    kill_switch_on(referee_dir)
    verify_signature(result_path, bundle_path, identity, sigstore_python)
    result_bytes = result_path.read_bytes()
    result = json.loads(result_bytes.decode("utf-8"))
    exit_block = result.get("exit") or {}
    if result.get("verdict") != "accepted" or exit_block.get("transferable") is not True:
        raise ImportErrorStop("the signed result does not mark this commit transferable")
    if (referee_dir / stagelock.SETUP / stagelock.LOCK_FILE).exists():
        raise ImportErrorStop("setup/stage.json is there: the lock this Stage 0 result opened is not imported again")
    sha = exit_block["brain_sha"]
    expected = exit_block["referee_tree_sha256"]
    toy_expected = exit_block.get("toy_tree_sha256")
    if toy_expected is not None and toy_dir is None:
        raise ImportErrorStop("the signed result carries the toy's tree: give --toy, its checkout (`25a` 2)")
    if not gitio.has_commit(brain_repo, sha):
        raise ImportErrorStop(f"brain commit {sha} is not in {brain_repo}; fetch it first")
    tar_bytes = gitio.archive(brain_repo, sha)
    actual = tree_hash(tar_bytes, "referee")
    if actual != expected:
        raise ImportErrorStop(f"referee tree hash {actual} differs from the signed {expected}")
    for path, _content, _executable in iter_files(tar_bytes):
        if path.parts[:1] == ("referee",) and _lands_on_kept(path.relative_to("referee")):
            raise ImportErrorStop(f"{path.as_posix()} would land on what the import keeps (an operator file, "
                                  f"bootstrap/ or {BOOTSTRAP_WORKFLOW}, `25a` 1)")
    if toy_expected is not None:
        toy_actual = tree_hash(tar_bytes, TOY_DIR, forbid_operator_names=False, fold_case=True)
        if toy_actual != toy_expected:
            raise ImportErrorStop(f"toy tree hash {toy_actual} differs from the signed {toy_expected} (`25a` 2)")
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

        _clear(referee_dir, kept, _holds_kept)
        shutil.copytree(referee_tree, referee_dir, dirs_exist_ok=True)
        if disk_hash(referee_dir, skip=kept) != expected:
            raise ImportErrorStop("the referee checkout on disk, what the import keeps left out, is not the signed tree "
                                  "(`25a` 1): reset it before anything is pushed")
        toy_bytes = 0
        if toy_tree is not None:
            _clear(toy_dir, _git_dir, lambda rel: False)
            shutil.copytree(toy_tree, toy_dir, dirs_exist_ok=True)
            if disk_hash(toy_dir, skip=_git_dir) != toy_expected:
                raise ImportErrorStop("the toy checkout on disk is not the signed toy tree (`25a` 2): reset it")
            toy_bytes = sum(p.stat().st_size for p in toy_tree.rglob("*") if p.is_file())
    finally:
        for temp in temps:
            shutil.rmtree(temp, ignore_errors=True)

    row = {"ts": _now(), "stage": STAGE, "brain_sha": sha, "referee_tree_sha256": actual,
           "result_sha256": hashlib.sha256(result_bytes).hexdigest()}
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
