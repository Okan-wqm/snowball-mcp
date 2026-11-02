"""The target's toolchain in the referee (plan D8, register E513): the target's own tests and the rival's reproducers of
a defect in target code run with node, npm and cargo, with no network.

Two steps, two containers of one image (`images/target/Dockerfile`, pinned by digest in the operator's config):

- ``fetch`` has the network and executes nothing the tree holds. The locks are checked first (`lock_problems`): every
  package comes from the public registry with its integrity hash, or from the tree itself. npm then sees only a
  skeleton of the tree (`npm_skeleton`): the ``package.json`` and ``package-lock.json`` of the lock's directory and the
  ``package.json`` of each workspace the lock names, with their ``scripts`` removed; no ``.npmrc``, no source.
  ``npm ci --ignore-scripts`` then installs exactly the lock and has no script of the tree to run. cargo reads the
  tree's manifests from a working directory outside the tree, so no ``.cargo/config.toml`` and no
  ``rust-toolchain.toml`` of the tree is read, and ``cargo vendor --locked`` downloads exactly the lock and builds
  nothing (`fetch`).
- ``run`` has no network (`container.sandbox_flags`, the confinement every untrusted run has). It copies the tree to
  ``/tmp/work``, unpacks what fetch made (each tar's sha256 is pinned in ``deps.json``) and runs one command there
  (`TargetRunner`, a `container.Runner`: `reproduce` runs the rival's target reproducers with it as it runs the Python
  image). A suite's output is read into case ids and counts (`run_suite`): a suite that exits 0 but shows no test, or
  whose per-test lines disagree with its own summary, is not green.

What a suite's process prints is the tree's code speaking: a test can print a forged line. The cross-check of each
runner's summary against its per-test lines catches a careless forgery, not a deliberate one; per-test evidence that
holds against the tree's own code is the watchers' (`D9`), which compare case ids at base and head.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import tomllib
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .config import ConfigError
from .container import RUN, RunResult, check_cwd, container_name, execute, sandbox_flags

KINDS = ("cargo", "node")
NPM_REGISTRY = "https://registry.npmjs.org/"
CRATES_IO = "registry+https://github.com/rust-lang/crates.io-index"
VENDOR_TAR = "cargo-vendor.tar"
DEPS_MANIFEST = "deps.json"
DOCKER_ERROR = 125  # `docker run` exits with this when docker itself failed (as in `reproduce`)
ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,62}\Z")
REL_RE = re.compile(r"^[A-Za-z0-9._@+-]+(?:/[A-Za-z0-9._@+-]+)*\Z")
HEX64_RE = re.compile(r"^[0-9a-f]{64}\Z")


class TargetError(ValueError):
    """The tree cannot be fetched as it stands: a lock outside the rules, a manifest missing or not a plain file."""


@dataclass(frozen=True)
class Suite:
    """One of the target's own test suites, as the operator names it: run ``cmd`` (a shell command) at ``cwd`` with
    the dependencies of the lock in ``root`` (``.`` for the tree's root). ``workspaces``: for node, the npm workspaces
    installed (``npm ci --workspace``); empty installs every one."""

    id: str
    kind: str
    root: str
    cwd: str
    cmd: str
    workspaces: tuple[str, ...] = ()


def _rel(value: Any, where: str) -> str:
    if value == ".":
        return value
    if not isinstance(value, str) or not REL_RE.match(value) or ".." in value.split("/"):
        raise ConfigError(f"{where} must be a relative path inside the tree")
    return value


def load_suites(raw: Any, where: str) -> tuple[Suite, ...]:
    """The operator's list of target suites, every key checked (the caller names where it was read)."""
    if not isinstance(raw, list) or not raw:
        raise ConfigError(f"{where} must be a non-empty list")
    suites = []
    for i, item in enumerate(raw):
        w = f"{where}[{i}]"
        if not isinstance(item, dict):
            raise ConfigError(f"{w} must be an object")
        unknown = sorted(set(item) - {"id", "kind", "root", "cwd", "cmd", "workspaces"})
        if unknown:
            raise ConfigError(f"{w}: unknown key(s) {', '.join(unknown)}")
        sid, kind, cmd = item.get("id"), item.get("kind"), item.get("cmd")
        if not isinstance(sid, str) or not ID_RE.match(sid):
            raise ConfigError(f"{w}.id must be lowercase letters, digits, '-' or '_'")
        if kind not in KINDS:
            raise ConfigError(f"{w}.kind must be one of {', '.join(KINDS)}")
        if not isinstance(cmd, str) or not cmd.strip() or any(ord(c) < 32 for c in cmd):
            raise ConfigError(f"{w}.cmd must be a one-line shell command")
        workspaces = item.get("workspaces", [])
        if kind != "node" and workspaces:
            raise ConfigError(f"{w}.workspaces is for node suites only")
        if not isinstance(workspaces, list):
            raise ConfigError(f"{w}.workspaces must be a list")
        suites.append(Suite(sid, kind, _rel(item.get("root"), f"{w}.root"), _rel(item.get("cwd"), f"{w}.cwd"), cmd,
                            tuple(_rel(ws, f"{w}.workspaces") for ws in workspaces)))
    if len({s.id for s in suites}) != len(suites):
        raise ConfigError(f"{where}: suite ids must be unique")
    return tuple(suites)


def _plain_file(tree: Path, rel: str) -> Path:
    """A regular file inside the tree, never a link: what fetch reads of the tree it reads only through here."""
    path = tree / rel
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(tree.resolve()):
        raise TargetError(f"{rel} is missing or not a plain file inside the tree")
    return path


def npm_lock_problems(text: str) -> list[str]:
    """What keeps an npm lock from being installed exactly and offline: a package from anywhere but the public
    registry, one without a sha512 integrity hash, a link that leaves the tree, a lock without a packages map."""
    try:
        lock = json.loads(text)
    except ValueError:
        return ["package-lock.json is not JSON"]
    packages = lock.get("packages") if isinstance(lock, dict) else None
    if not isinstance(packages, dict) or lock.get("lockfileVersion") not in (2, 3):
        return ["package-lock.json must be lockfileVersion 2 or 3, with a packages map"]
    problems = []
    for key, pkg in sorted(packages.items()):
        if not isinstance(pkg, dict):
            problems.append(f"{key}: not an object")
        elif key == "" or "node_modules" not in key.split("/"):
            if key and not REL_RE.match(key) or ".." in key.split("/"):
                problems.append(f"{key}: a workspace outside the tree")
        elif pkg.get("link"):
            resolved = pkg.get("resolved")
            if not isinstance(resolved, str) or not REL_RE.match(resolved) or ".." in resolved.split("/"):
                problems.append(f"{key}: a link outside the tree")
        elif pkg.get("inBundle"):
            continue  # inside its parent's tarball, which carries the integrity hash
        elif not str(pkg.get("resolved", "")).startswith(NPM_REGISTRY):
            problems.append(f"{key}: resolved outside {NPM_REGISTRY}")
        elif not str(pkg.get("integrity", "")).startswith("sha512-"):
            problems.append(f"{key}: no sha512 integrity")
    return problems


def cargo_lock_problems(text: str) -> list[str]:
    """The same for a Cargo lock: every package from crates.io with its checksum, or from the tree (no source)."""
    try:
        lock = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return ["Cargo.lock is not TOML"]
    if lock.get("version") not in (3, 4) or not isinstance(lock.get("package"), list):
        return ["Cargo.lock must be version 3 or 4, with packages"]
    problems = []
    for pkg in lock["package"]:
        label = f"{pkg.get('name')} {pkg.get('version')}" if isinstance(pkg, dict) else repr(pkg)[:60]
        source = pkg.get("source") if isinstance(pkg, dict) else ""
        if source is None:
            continue  # a member of the workspace or a path dependency: in the tree
        if source != CRATES_IO:
            problems.append(f"{label}: source {str(source)[:80]} is not crates.io")
        elif not HEX64_RE.match(str(pkg.get("checksum", ""))):
            problems.append(f"{label}: no checksum")
    return problems


def _lock_name(kind: str) -> str:
    return "Cargo.lock" if kind == "cargo" else "package-lock.json"


def lock_problems(tree: Path, suites: tuple[Suite, ...]) -> list[str]:
    """Every lock the suites name, checked before anything is fetched; empty means fetch may go ahead."""
    problems = []
    for kind, root in sorted({(s.kind, s.root) for s in suites}):
        rel = f"{root}/{_lock_name(kind)}" if root != "." else _lock_name(kind)
        try:
            text = _plain_file(tree, rel).read_text(encoding="utf-8")
        except (TargetError, UnicodeDecodeError) as exc:
            problems.append(f"{rel}: {exc}")
            continue
        found = cargo_lock_problems(text) if kind == "cargo" else npm_lock_problems(text)
        problems += [f"{rel}: {p}" for p in found]
    return problems


def npm_skeleton(tree: Path, root: str, out: Path) -> list[str]:
    """Copy what ``npm ci`` reads and nothing else: the lock directory's ``package-lock.json``, its ``package.json``
    and the ``package.json`` of every workspace the lock names, each without its ``scripts``. ``--ignore-scripts`` is
    not enough on its own: npm 10.9 still runs a linked workspace's ``prepare`` under it (measured, E513), and a
    script is the tree's code. Returns the paths written, relative to the tree."""
    base = "" if root == "." else root + "/"
    lock = json.loads(_plain_file(tree, base + "package-lock.json").read_text(encoding="utf-8"))
    names = [base + "package.json", base + "package-lock.json"]
    names += [f"{base}{key}/package.json" for key in sorted(lock["packages"])
              if key and "node_modules" not in key.split("/")]
    for rel in names:
        source = _plain_file(tree, rel)
        (out / rel).parent.mkdir(parents=True, exist_ok=True)
        if rel.endswith("package-lock.json"):
            shutil.copyfile(source, out / rel)
            continue
        try:
            manifest = json.loads(source.read_text(encoding="utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            raise TargetError(f"{rel} is not JSON") from exc
        if not isinstance(manifest, dict):
            raise TargetError(f"{rel} is not a JSON object")
        manifest.pop("scripts", None)
        (out / rel).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return names


# Runs in the fetch container, with the network: install the lock into the skeleton, then pack every node_modules
# directory it made (each at its place in the tree) into one tar. The arguments come after the script ($1: the lock's
# directory, $2: the tar's name, then npm's own), so nothing is interpolated into it.
FETCH_NPM = r"""set -eu
cp -R /skel/. /tmp/w/
root=$1; tar=$2; shift 2
cd "/tmp/w/$root"
npm ci --ignore-scripts --no-audit --no-fund --registry=https://registry.npmjs.org/ --cache=/tmp/npm-cache "$@"
cd /tmp/w
find . -name node_modules -type d -prune -print0 | tar --null -T - -cf "/out/$tar"
"""

# Runs in the fetch container, with the network, from /tmp: outside the tree, so cargo reads no configuration and no
# toolchain file of the tree. $1 is the first lock's manifest, the rest are synced into the same vendor directory.
FETCH_CARGO = r"""set -eu
cd /tmp
first=$1; shift
for m in "$@"; do set -- "$@" --sync "$m"; shift; done
mkdir -p /tmp/vendor
cargo vendor --locked --manifest-path "$first" "$@" /tmp/vendor >/dev/null
tar -cf /out/""" + VENDOR_TAR + r""" -C /tmp vendor
"""


def _fetch_argv(docker: str, image: str, name: str, mounts: list[str], script: str, args: list[str]) -> list[str]:
    argv = [docker, "run", "--rm", "--name", name, *sandbox_flags(network="bridge", tmpfs="8g", memory="8g")]
    for mount in mounts:
        argv += ["--mount", mount]
    return argv + ["--entrypoint", "sh", image, "-c", script, "fetch", *args]


def fetch_npm_argv(docker: str, image: str, name: str, skeleton: Path, out: Path, suite: Suite) -> list[str]:
    args = [suite.root, f"npm-{suite.id}.tar"] + [f"--workspace={ws}" for ws in suite.workspaces]
    return _fetch_argv(docker, image, name, [f"type=bind,src={skeleton},dst=/skel,readonly",
                                             f"type=bind,src={out},dst=/out"], FETCH_NPM, args)


def fetch_cargo_argv(docker: str, image: str, name: str, tree: Path, out: Path, roots: list[str]) -> list[str]:
    manifests = [f"/src/{r}/Cargo.toml" if r != "." else "/src/Cargo.toml" for r in roots]
    return _fetch_argv(docker, image, name, [f"type=bind,src={tree},dst=/src,readonly",
                                             f"type=bind,src={out},dst=/out"], FETCH_CARGO, manifests)


def fetch(tree: Path, suites: tuple[Suite, ...], out: Path, *, image: str, timeout_s: int,
          docker: str = "docker") -> dict[str, Any]:
    """The fetch job's work: check the locks, then fetch what every suite needs into ``out``. Returns
    ``{"ok", "problems", "files": {tar: sha256}, "runs": [...]}``, also written to ``out/deps.json``; nothing in the
    tree runs."""
    out.mkdir(parents=True, exist_ok=True)
    out.chmod(0o777)  # the container's user (65534) writes the tars here
    doc: dict[str, Any] = {"ok": False, "problems": lock_problems(tree, suites), "files": {}, "runs": []}
    if not doc["problems"]:
        jobs = []
        for suite in (s for s in suites if s.kind == "node"):
            skeleton = out / f"skeleton-{suite.id}"
            skeleton.mkdir()
            npm_skeleton(tree, suite.root, skeleton)
            jobs.append(fetch_npm_argv(docker, image, container_name(), skeleton.resolve(), out.resolve(), suite))
        roots = sorted({s.root for s in suites if s.kind == "cargo"})
        if roots:
            jobs.append(fetch_cargo_argv(docker, image, container_name(), tree.resolve(), out.resolve(), roots))
        for argv in jobs:
            res = execute(docker, argv[argv.index("--name") + 1], argv, b"", timeout_s)
            doc["runs"].append({"exit": res.exit_code, "timed_out": res.timed_out, "duration_ms": res.duration_ms,
                                "stderr_tail": res.stderr.decode("utf-8", "replace")[-2000:]})
        for skeleton in out.glob("skeleton-*"):
            shutil.rmtree(skeleton)
        doc["files"] = {p.name: _sha256(p) for p in sorted(out.glob("*.tar"))}
        doc["ok"] = all(r["exit"] == 0 and not r["timed_out"] for r in doc["runs"])
    (out / DEPS_MANIFEST).write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return doc


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def deps_problems(deps: Path, pinned: dict[str, str]) -> list[str]:
    """The run job's check that the tars it mounts are the bytes fetch made (``deps.json`` as the fetch job signed or
    passed it on), and nothing more."""
    found = {p.name: _sha256(p) for p in sorted(deps.glob("*.tar"))}
    return [f"{name}: {'missing' if name not in found else 'not the fetched bytes'}"
            for name in sorted(pinned) if found.get(name) != pinned[name]] + \
           [f"{name}: not fetched" for name in sorted(set(found) - set(pinned))]


# Runs in the run container, with no network: the tree to /tmp/work, the fetched node_modules into it at their places,
# the cargo vendor directory to /tmp/vendor with a cargo configuration that reads only it. Then the command (`RUN`).
PRELUDE = r"""set -eu
mkdir -p /tmp/work "$CARGO_HOME"
cp -R /src/. /tmp/work/
for t in ${SNOWBALL_NPM:-}; do tar -xf "/deps/$t" -C /tmp/work; done
if [ -n "${SNOWBALL_VENDOR:-}" ]; then
  tar -xf /deps/""" + VENDOR_TAR + r""" -C /tmp
  printf '%s\n' '[source.crates-io]' 'replace-with = "snowball-vendor"' '[source.snowball-vendor]' \
    'directory = "/tmp/vendor"' '[net]' 'offline = true' > "$CARGO_HOME/config.toml"
fi
cd "/tmp/work/${SNOWBALL_CWD:-.}"
""" + RUN


@dataclass
class TargetRunner:
    """Each call is one fresh container of the target image with no network: the tree and the fetched tars mounted
    read-only (`PRELUDE`). With ``deps_dir`` None it is the empty control tree's runner: the same image and nothing
    fetched, as `reproduce` needs it."""

    image: str
    src_dir: str
    deps_dir: str | None = None
    npm: tuple[str, ...] = ()
    vendor: bool = False
    tmpfs: str = "8g"
    memory: str = "10g"
    docker: str = "docker"
    executed: list[list[str]] = field(default_factory=list)

    @classmethod
    def for_suites(cls, image: str, src_dir: str, deps_dir: str, suites: tuple[Suite, ...], **kw: Any) -> TargetRunner:
        return cls(image, src_dir, deps_dir, tuple(f"npm-{s.id}.tar" for s in suites if s.kind == "node"),
                   any(s.kind == "cargo" for s in suites), **kw)

    def argv(self, name: str, cmd: str, cwd: str) -> list[str]:
        argv = [self.docker, "run", "--rm", "-i", "--name", name,
                *sandbox_flags(network="none", tmpfs=self.tmpfs, memory=self.memory),
                "--mount", f"type=bind,src={self.src_dir},dst=/src,readonly"]
        if self.deps_dir is not None:
            argv += ["--mount", f"type=bind,src={self.deps_dir},dst=/deps,readonly"]
        return argv + ["--env", f"SNOWBALL_NPM={' '.join(self.npm) if self.deps_dir else ''}",
                       "--env", f"SNOWBALL_VENDOR={'1' if self.vendor and self.deps_dir else ''}",
                       "--env", f"SNOWBALL_CWD={cwd}", "--env", f"SNOWBALL_CMD={cmd}",
                       "--entrypoint", "sh", self.image, "-c", PRELUDE]

    def run(self, cmd: str, *, cwd: str = ".", stdin: bytes = b"", timeout_s: int) -> RunResult:
        check_cwd(cwd)
        name = container_name()
        argv = self.argv(name, cmd, cwd)
        self.executed.append(argv)
        return execute(self.docker, name, argv, stdin, timeout_s)


LIBTEST_RUNNING = re.compile(r"^\s*Running (?:unittests )?(\S+) \((?:.*/)?([^/()]+?)(?:-[0-9a-f]{8,})?\)\s*$")
LIBTEST_DOC = re.compile(r"^\s*Doc-tests (\S+)\s*$")
LIBTEST_CASE = re.compile(r"^test (.+) \.\.\. (ok|FAILED|ignored)(?:, .*)?$")
LIBTEST_SUMMARY = re.compile(r"^test result: (?:ok|FAILED)\. (\d+) passed; (\d+) failed; (\d+) ignored;")
LIBTEST_STATUS = {"ok": "passed", "FAILED": "failed", "ignored": "skipped"}


def parse_libtest(text: str) -> tuple[list[tuple[str, str]], bool]:
    """``cargo test ... 2>&1``: the case ids (``<test binary>::<test>``) with their status, and whether the per-test
    lines add up to every binary's own summary line."""
    cases: list[tuple[str, str]] = []
    summed: Counter[str] = Counter()
    binary = "?"
    for line in text.splitlines():
        if m := LIBTEST_RUNNING.match(line):
            binary = m.group(2)
        elif m := LIBTEST_DOC.match(line):
            binary = f"doc-tests:{m.group(1)}"
        elif m := LIBTEST_CASE.match(line):
            cases.append((f"{binary}::{m.group(1)}", LIBTEST_STATUS[m.group(2)]))
        elif m := LIBTEST_SUMMARY.match(line):
            summed.update(passed=int(m.group(1)), failed=int(m.group(2)), skipped=int(m.group(3)))
    seen = Counter(status for _, status in cases)
    return cases, all(seen[k] == summed[k] for k in ("passed", "failed", "skipped"))


JEST_STATUS = {"passed": "passed", "failed": "failed", "pending": "skipped", "skipped": "skipped", "todo": "skipped",
               "disabled": "skipped"}


def _report(text: str) -> dict[str, Any] | None:
    """The last JSON object in the output that is a jest-shaped report (jest ``--json``, vitest ``--reporter=json``)."""
    decoder = json.JSONDecoder()
    starts = [m.start() for m in re.finditer(r"(?m)^\{", text)]
    for start in reversed(starts):
        try:
            doc, _ = decoder.raw_decode(text, start)
        except ValueError:
            continue
        if isinstance(doc, dict) and isinstance(doc.get("testResults"), list):
            return doc
    return None


def parse_jest_json(text: str, work: str = "/tmp/work/") -> tuple[list[tuple[str, str]], bool]:
    """A jest-shaped JSON report: the case ids (``<spec file>::<full name>``) with their status, a spec file that
    failed to load as one failed case, and whether the cases add up to the report's own totals."""
    doc = _report(text)
    if doc is None:
        return [], False
    cases: list[tuple[str, str]] = []
    for result in doc["testResults"]:
        if not isinstance(result, dict):
            return [], False
        name = str(result.get("name", "?")).removeprefix(work)
        asserts = result.get("assertionResults") or []
        if not asserts and result.get("status") == "failed":
            cases.append((f"{name}::(spec file failed to load)", "failed"))
        for a in asserts:
            if not isinstance(a, dict) or a.get("status") not in JEST_STATUS:
                return [], False
            cases.append((f"{name}::{a.get('fullName') or a.get('title')}", JEST_STATUS[a["status"]]))
    seen = Counter(status for _, status in cases)
    totals = {k: doc.get(k) for k in ("numPassedTests", "numFailedTests", "numPendingTests", "numTodoTests")}
    if not all(isinstance(v, int) for v in totals.values()):
        return cases, False
    loaded_failed = sum(1 for c, _ in cases if c.endswith("::(spec file failed to load)"))
    consistent = (seen["passed"] == totals["numPassedTests"]
                  and seen["failed"] - loaded_failed == totals["numFailedTests"]
                  and seen["skipped"] == totals["numPendingTests"] + totals["numTodoTests"])
    return cases, consistent


def run_suite(runner: Any, suite: Suite, timeout_s: int) -> dict[str, Any]:
    """Run one suite and read it. ``ok`` only when the command exited 0 on its own, showed at least one test, no test
    failed and the per-test lines agree with the runner's own summary."""
    res = runner.run(suite.cmd, cwd=suite.cwd, timeout_s=timeout_s)
    text = res.stdout.decode("utf-8", "replace")
    cases, consistent = parse_libtest(text) if suite.kind == "cargo" else parse_jest_json(text)
    counts = Counter(status for _, status in cases)
    ok = (res.exit_code == 0 and not res.timed_out and consistent and bool(cases) and counts["failed"] == 0)
    return {"suite": suite.id, "ok": ok, "exit": res.exit_code, "timed_out": res.timed_out,
            "runner_fault": res.exit_code == DOCKER_ERROR, "consistent": consistent,
            "counts": {"passed": counts["passed"], "failed": counts["failed"], "skipped": counts["skipped"],
                       "total": len(cases)},
            "cases": sorted(cases), "duration_ms": res.duration_ms,
            "stdout_sha256": hashlib.sha256(res.stdout).hexdigest(),
            "stderr_sha256": hashlib.sha256(res.stderr).hexdigest()}


def toolchain_drift(tree: Path, rustc_version: str) -> str | None:
    """The Rust toolchain the tree names (``rust-toolchain.toml``) when it is not the image's: the referee runs its
    own toolchain and says so, it never follows the tree's (`images/target/Dockerfile`)."""
    try:
        doc = tomllib.loads(_plain_file(tree, "rust-toolchain.toml").read_text(encoding="utf-8"))
    except (TargetError, UnicodeDecodeError, tomllib.TOMLDecodeError):
        return None
    channel = (doc.get("toolchain") or {}).get("channel") if isinstance(doc.get("toolchain"), dict) else None
    if isinstance(channel, str) and channel != rustc_version:
        return f"rust-toolchain.toml names {channel[:40]}; the referee ran {rustc_version}"
    return None
