"""Tree hashes over git-archive tarballs, and safe extraction of regular files only.

The referee code tree hash is what the operator import compares (`tohum/25a` 1). It covers the
regular files under ``referee/`` at a pinned commit, by relative path and content:
``sha256( "".join(sorted(f"{sha256(content)}  {relpath}\\n")) )``.
"""

from __future__ import annotations

import hashlib
import io
import tarfile
from pathlib import Path, PurePosixPath

# Operator-only names: the import never overwrites them, so the referee code may not carry them.
OPERATOR_NAMES = frozenset({"policy.json", "control.json", "setup", "seats", "vectors", "bootstrap.json"})


class TreeError(ValueError):
    """The archive contains something other than regular files and directories."""


def _clean(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts:
        raise TreeError(f"unsafe path in archive: {name}")
    return path


def iter_files(tar_bytes: bytes):
    """Yield (path, content, executable) for regular files; refuse links and special files."""
    with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:") as tar:
        for member in tar.getmembers():
            if member.name == "pax_global_header" or member.type == tarfile.XGLTYPE:
                continue
            path = _clean(member.name)
            if member.isdir():
                continue
            if not member.isfile():
                raise TreeError(f"not a regular file: {member.name}")
            handle = tar.extractfile(member)
            assert handle is not None
            yield path, handle.read(), bool(member.mode & 0o111)


def tree_hash(tar_bytes: bytes, prefix: str, forbid_operator_names: bool = True) -> str:
    """Hash of the regular files under ``prefix`` in a git-archive tarball."""
    pre = PurePosixPath(prefix)
    lines = []
    for path, content, _exec in iter_files(tar_bytes):
        try:
            rel = path.relative_to(pre)
        except ValueError:
            continue
        if forbid_operator_names and rel.parts and rel.parts[0] in OPERATOR_NAMES:
            raise TreeError(f"{prefix}/{rel.parts[0]} is an operator-only name")
        lines.append(f"{hashlib.sha256(content).hexdigest()}  {rel.as_posix()}\n")
    if not lines:
        raise TreeError(f"no files under {prefix}/")
    return hashlib.sha256("".join(sorted(lines)).encode("utf-8")).hexdigest()


def extract(tar_bytes: bytes, dest: Path, max_bytes: int, prefix: str = "") -> int:
    """Extract regular files (optionally only under ``prefix``) into ``dest``; return total bytes."""
    total = 0
    pre = PurePosixPath(prefix) if prefix else None
    dest.mkdir(parents=True, exist_ok=True)
    for path, content, executable in iter_files(tar_bytes):
        if pre is not None:
            try:
                path = path.relative_to(pre)
            except ValueError:
                continue
        total += len(content)
        if total > max_bytes:
            raise TreeError(f"tree larger than {max_bytes} bytes")
        target = dest.joinpath(*path.parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        target.chmod(0o755 if executable else 0o644)
    return total
