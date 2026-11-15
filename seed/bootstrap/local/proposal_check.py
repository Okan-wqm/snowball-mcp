"""The merge path's run of a Founder's seed proposal (`tohum/29w`, E594, E600, E601): what the static check cannot.

    cd seed/bootstrap && python3 local/proposal_check.py --record <id>.json --patch <id>.patch
        (--image <image@sha256:...> | --unsandboxed) [--full]
    cd seed/bootstrap && python3 local/proposal_check.py --isolate <base-rev>      # CI, on a proposal/<id> PR
    cd seed/bootstrap && python3 local/proposal_check.py --added-tests <base-rev>  # CI: the PR's new test modules

The base is this repository's committed HEAD, read from git (never the working tree, so what is hashed is what runs).
First the referee's own static check (`proposals.check`, the base bound to HEAD's tree hashes). Then two verdicts that
never meet (E601), because the Founder wrote the new tests and a test in the suite's process can reach the shared
``TestResult`` (override ``run``, clear ``result.failures``, set ``shouldStop``, or alias a shared class and rebind a
method of it), so no rule on its text can make its run trustworthy:

- the existing suite: the base's own tests and runner, byte for byte (`tests/` and `local/` are the base's; a patch
  that touches them is refused, `proposals.runner`), on the patch's pages and modules only, with the map redrawn by the
  base's `system_map.py` (it is drawn from the code, `docs/` is closed to the Founder); ``--full`` runs the whole unit
  suite in one process and the base's mutants anchored in a touched file, each in its own process (`mutate.py`);
- the evidence: every test the record names, each in its own process, red on the base with only the patch's new test
  files (it fails, or cannot import the module the patch brings) and green twice with the whole patch; ``--full`` adds
  the patch's new mutants (`mutate.py --only`, in a tree that holds the new tests).

The Founder's tests run where they can reach nothing (`29w` "Kanıt"): by default in a fresh container per run
(`container.DockerRunner`: no network, read-only source, no capabilities, an unprivileged user, no environment of the
operator's), the image pinned by digest. ``--unsandboxed`` runs them as a local process with a scrubbed environment (as
`mutate.py` does), only for an operator who read every added test body first; it says so on every run. Exit 0 is
necessary, not sufficient: a human or the panel reads every candidate (its test bodies and page lines) before a merge,
and the merge PR from a ``proposal/<id>`` branch runs the same split in the seed's CI (`ci.yml`). It never merges.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable

BOOT = Path(__file__).resolve().parents[1]
ROOT = BOOT.parents[1]
sys.path.insert(0, str(BOOT))
sys.path.insert(0, str(BOOT / "local"))

from mutate import ROOT_FILES_READ  # noqa: E402  (the root files the tests read: one list, `mutate.py`'s)
from snowball_bootstrap import gitio, proposals  # noqa: E402
from snowball_bootstrap.container import DockerRunner  # noqa: E402
from snowball_bootstrap.treehash import iter_files, tree_hash  # noqa: E402

PARTS = ("seed", "spec", "docs", ".github/workflows")  # what the suite reads, as `mutate.py` copies it
RUNNER_DIRS = (proposals.TESTS, proposals.BOOT_PREFIX + "local/")  # the base's, byte for byte, in the existing run
SYSTEM_MAP = "seed/bootstrap/local/system_map.py"
PINNED = re.compile(r"^\S+@sha256:[0-9a-f]{64}\Z")
KEPT_ENV = ("PATH", "SYSTEMROOT")  # what a local Python and git need; every other variable of the operator is dropped
TIMEOUT_S = 1800
SUITE = ["-m", "unittest", "discover", "-s", "tests", "-f"]
Run = Callable[[Path, list[str]], int]


class Isolation(RuntimeError):
    """The existing run's tree is not the base's tests and runner: nothing is run."""


def committed(root: Path, rev: str = "HEAD") -> bytes:
    """``rev``'s files the suite reads, as one tar: the base the check hashes, reads and runs."""
    def skip(path: str) -> bool:
        return path not in ROOT_FILES_READ and not any(path.startswith(d + "/") for d in PARTS)
    return gitio.archive(root, rev, skip=skip)


class Base:
    """The delivered seed HEAD is, as the referee binds a proposal to it (`seed_epochs[]`)."""

    def __init__(self, tar: bytes) -> None:
        self.spec_tohum_sha256 = tree_hash(tar, "spec/tohum", forbid_operator_names=False)
        self.bootstrap_sha256 = tree_hash(tar, "seed/bootstrap", forbid_operator_names=False)


def reader(files: dict[str, bytes]) -> Callable[[str], str | None]:
    def read(path: str) -> str | None:
        raw = files.get(path)
        return None if raw is None else proposals.committed_text(raw)
    return read


def patched_files(text: str, read: Callable[[str], str | None]) -> dict[str, tuple[str, str]]:
    """Every file the patch writes: its patched text and its part, ``test`` (a new test file), ``mutants`` (rows of
    `mutate.py`) or ``code`` (a page or a module: what the existing suite judges)."""
    out = {}
    for fp in proposals.parse(text):
        part = ("test" if fp.new and fp.path.startswith(proposals.TESTS) else
                "mutants" if fp.path == proposals.MUTATE else "code")
        out[fp.path] = (proposals.apply(read(fp.path), fp)[0], part)
    return out


def tree(files: dict[str, bytes], patched: dict[str, str], dest: Path) -> Path:
    """The base's files with ``patched`` written over them, under ``dest``; the root the runner sees."""
    for rel, content in files.items():
        (dest / rel).parent.mkdir(parents=True, exist_ok=True)
        (dest / rel).write_bytes(content)
    for rel, text in patched.items():
        (dest / rel).parent.mkdir(parents=True, exist_ok=True)
        (dest / rel).write_bytes(text.encode("utf-8"))
    return dest


def existing_overlay(files: dict[str, bytes], written: dict[str, tuple[str, str]]) -> dict[str, str]:
    """What the existing run writes over the base: the patch's pages and modules, nothing of its tests or its rows.
    A code path that is part of the runner never gets here (`proposals.runner`); if one did, nothing runs."""
    overlay = {p: t for p, (t, part) in written.items() if part == "code"}
    bad = sorted(p for p in overlay if proposals.runner(p, p not in files))
    if bad:
        raise Isolation(f"{proposals.RUNNER}:{bad[0]}")
    return overlay


def assert_isolated(files: dict[str, bytes], root: Path) -> None:
    """The existing run's tree holds exactly the base's ``tests/`` and ``local/`` (same paths, same bytes) and no
    start-up hook the base does not have: the suite that judges is the one the operator merged before."""
    for prefix in RUNNER_DIRS:
        base = {p: c for p, c in files.items() if p.startswith(prefix)}
        here = {p.relative_to(root).as_posix(): p.read_bytes() for p in (root / prefix).rglob("*")
                if p.is_file() and "__pycache__" not in p.parts}
        if here != base:
            raise Isolation(f"{proposals.RUNNER}:{prefix} differs from the base")
    for p in root.rglob("*"):
        rel = p.relative_to(root).as_posix()
        if p.is_file() and rel not in files and proposals.runner(rel, True) and not rel.startswith(RUNNER_DIRS):
            raise Isolation(f"{proposals.RUNNER}:{rel}")


def redraw_map(root: Path) -> None:
    """The base's `system_map.py` redraws `docs/harita.md` from the patched code (it reads with `ast`, runs nothing of
    the tree; `-I`: no environment, no script directory on the path). The map is derived; `docs/` is the merger's."""
    if not (root / SYSTEM_MAP).is_file():
        return
    subprocess.run([sys.executable, "-I", str(root / SYSTEM_MAP)], cwd=root / "seed" / "bootstrap", check=True,
                   capture_output=True, timeout=TIMEOUT_S, env=scrubbed_env(root))


def scrubbed_env(home: Path) -> dict[str, str]:
    """The environment of an unsandboxed run: ``KEPT_ENV`` and nothing else of the operator's (no token, no key)."""
    env = {k: os.environ[k] for k in KEPT_ENV if k in os.environ}
    env.update(HOME=str(home), USERPROFILE=str(home), TMP=str(home), TEMP=str(home), TMPDIR=str(home),
               PYTHONPATH=os.pathsep.join((".", "tests")), PYTHONDONTWRITEBYTECODE="1")
    return env


def local_runner(home: Path) -> Run:
    def run(root: Path, args: list[str]) -> int:
        proc = subprocess.run([sys.executable, *args], cwd=root / "seed" / "bootstrap", env=scrubbed_env(home),
                              capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=TIMEOUT_S)
        return proc.returncode
    return run


def docker_runner(image: str, empty: Path, docker: str = "docker") -> Run:
    def run(root: Path, args: list[str]) -> int:
        runner = DockerRunner(image=image, src_dir=str(root.resolve()), deps_dir=str(empty.resolve()),
                              vectors_dir=str(empty.resolve()), docker=docker)
        cmd = "PYTHONPATH=.:tests python " + shlex.join(args)
        result = runner.run(cmd, cwd="seed/bootstrap", timeout_s=TIMEOUT_S)
        return 124 if result.timed_out else result.exit_code
    return run


def evidence(run: Run, before: Path, after: Path, tests: list[str]) -> list[str]:
    """The evidence's findings, each test in its own process: green before (it proves nothing) or not green twice
    after. The Founder's code decides these exit codes; they never decide the existing suite's."""
    found = []
    for test_id in tests:
        if run(before, ["-m", "unittest", test_id]) == 0:
            found.append(f"proposal_evidence_not_red:{test_id}")
        elif run(after, ["-m", "unittest", test_id]) != 0:
            found.append(f"proposal_evidence_not_green:{test_id}")
        elif run(after, ["-m", "unittest", test_id]) != 0:
            found.append(f"proposal_evidence_unstable:{test_id}")
    return found


def existing_suite(run: Run, existing: Path, base_mutate: str, touched: list[str]) -> list[str]:
    """The base's suite on the patched pages and modules: the whole unit suite in one process, then the base's mutants
    anchored in a touched file (each in its own process, `mutate.run_mutant`) must all still die."""
    found = []
    if run(existing, SUITE) != 0:
        found.append("proposal_suite_red")
    names = sorted(proposals.mutant_names_in(base_mutate, set(touched)))
    if names and run(existing, ["local/mutate.py", "--only", ",".join(names)]) != 0:
        found.append("proposal_mutant_survived")
    return found


def check(root: Path, record: dict, patch: bytes, run: Run, full: bool,
          work: Path) -> tuple[list[str], dict[str, list[str]]]:
    """The review and the two verdicts (``existing``, ``evidence``) of one proposal against HEAD of ``root``; Refused
    by the static check, Isolation when the existing run's tree would not be the base's suite."""
    tar = committed(root)
    files = {p.as_posix(): content for p, content, _x in iter_files(tar)}
    read = reader(files)
    review = proposals.check(record, patch, Base(tar), [], read)
    written = patched_files(patch.decode("utf-8"), read)
    overlay = existing_overlay(files, written)
    tests = {p: t for p, (t, part) in written.items() if part == "test"}
    before = tree(files, tests, work / "before")
    after = tree(files, {**overlay, **tests}, work / "after")
    verdicts = {"existing": [], "evidence": evidence(run, before, after, record["evidence"]["tests"])}
    if full:
        existing = tree(files, overlay, work / "existing")
        redraw_map(existing)
        assert_isolated(files, existing)
        verdicts["existing"] = existing_suite(run, existing, read(proposals.MUTATE) or "", sorted(overlay))
        if proposals.MUTATE in written:
            full_tree = tree(files, {p: t for p, (t, _part) in written.items()}, work / "full")
            names = sorted(proposals.new_mutant_names(read(proposals.MUTATE) or "", written[proposals.MUTATE][0]))
            if run(full_tree, ["local/mutate.py", "--only", ",".join(names)]) != 0:
                verdicts["evidence"].append("proposal_new_mutant_survived")
    return review, verdicts


def isolate(root: Path, base_rev: str) -> list[str]:
    """CI on a ``proposal/<id>`` PR (`ci.yml`): put the base's ``tests/`` and ``local/`` back (the PR's new test files
    leave, its new `MUTANTS` rows with them) so the unit and mutation jobs run the base's suite on the patched code.
    Returns the refusals: a changed existing test, helper or runner file, or a start-up hook anywhere."""
    base = {p.as_posix(): c for p, c, _x in iter_files(committed(root, base_rev))}
    head = {p.as_posix(): c for p, c, _x in iter_files(committed(root, "HEAD"))}
    refused = sorted(p for p in head if p not in base and proposals.runner(p, True) and not p.startswith(RUNNER_DIRS))
    for p, c in head.items():
        if p.startswith(RUNNER_DIRS) and p in base and c != base[p] and p != proposals.MUTATE:
            refused.append(f"changed:{p}")
    for p in head:
        if p.startswith(RUNNER_DIRS) and p not in base:
            (root / p).unlink(missing_ok=True)
    for p, c in base.items():
        if p.startswith(RUNNER_DIRS):
            (root / p).parent.mkdir(parents=True, exist_ok=True)
            (root / p).write_bytes(c)
    return refused


def added_tests(root: Path, base_rev: str) -> list[str]:
    """The test modules a PR adds (``tests/test_<name>.py`` not in ``base_rev``), each run in its own process by CI."""
    base = {p.as_posix() for p, _c, _x in iter_files(committed(root, base_rev))}
    return sorted(p.as_posix().rsplit("/", 1)[-1][:-3] for p, _c, _x in iter_files(committed(root, "HEAD"))
                  if p.as_posix() not in base and proposals.TEST_FILE_RE.fullmatch(p.as_posix()))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--record")
    parser.add_argument("--patch")
    parser.add_argument("--full", action="store_true", help="also the whole unit suite and the mutants")
    parser.add_argument("--isolate", metavar="BASE_REV", help="CI: restore the base's tests/ and local/")
    parser.add_argument("--added-tests", metavar="BASE_REV", help="CI: print the test modules the head adds")
    where = parser.add_mutually_exclusive_group()
    where.add_argument("--image", help="the container image the tests run in, pinned by digest (name@sha256:...)")
    where.add_argument("--unsandboxed", action="store_true",
                       help="run the Founder's tests as a local process; only after reading every added test body")
    args = parser.parse_args(argv)
    if args.isolate:
        refused = isolate(ROOT, args.isolate)
        for line in refused:
            print(f"{proposals.RUNNER}:{line}", file=sys.stderr)
        return 1 if refused else 0
    if args.added_tests:
        print("\n".join(added_tests(ROOT, args.added_tests)))
        return 0
    if not (args.record and args.patch and (args.image or args.unsandboxed)):
        parser.error("--record, --patch and one of --image or --unsandboxed are required")
    if args.image and not PINNED.match(args.image):
        print("--image must be pinned by digest (name@sha256:<64 hex>)", file=sys.stderr)
        return 2
    record = json.loads(Path(args.record).read_text(encoding="utf-8"))
    patch = Path(args.patch).read_bytes()
    with tempfile.TemporaryDirectory(prefix="proposal-") as tmp:
        work = Path(tmp)
        (work / "empty").mkdir()
        (work / "home").mkdir()
        if args.unsandboxed:
            print("UNSANDBOXED: the Founder's tests run as this user's process (`29w`: read every test body first)",
                  file=sys.stderr)
        run = local_runner(work / "home") if args.unsandboxed else docker_runner(args.image, work / "empty")
        try:
            review, verdicts = check(ROOT, record, patch, run, args.full, work)
        except proposals.Refused as refused:
            print(refused.reason)
            return 1
        except Isolation as broken:
            print(str(broken))
            return 1
    print(json.dumps({"review": review, "existing": verdicts["existing"], "evidence": verdicts["evidence"],
                      "next": "a human or the panel reads the candidate; the merge PR from a proposal/<id> branch "
                      "runs the base's suite and every mutant in the seed's CI"}, indent=1))
    return 1 if verdicts["existing"] or verdicts["evidence"] else 0


if __name__ == "__main__":
    sys.exit(main())
