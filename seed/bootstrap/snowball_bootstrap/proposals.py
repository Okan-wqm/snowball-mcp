"""The Founder's seed proposals, checked by the referee (`tohum/29w`; the owner's decision of 2026-11-14, E594).

The seed is the operator's: the Founder never writes to `snowball-mcp` or the referee repository. It may write an
additive change to the seed as a proposal: ``reports/<id>.json`` (the record) and ``reports/<id>.patch`` (a ``git diff``
against the delivered seed), with at least one evidence test the patch adds. `pull` checks every proposal here,
mechanically and failing closed, without running anything; a proposal that passes is only a ``candidate``: the panel or
the owner merges it through the ordinary seed epoch, after the seed's CI ran it (its evidence red before and green
after, `local/proposal_check.py`; the whole suite and every mutant, `15` 4). A proposal is never a reason, a streak or
an acceptance condition, so nothing the Founder proposes moves its own verdict.

"Additive" is decided by structure, never by intent (a test that turns red to green proves a loosening as well as a
fix, so evidence alone cannot tell them apart):
- the diff only adds lines: no ``-`` line, no deleted, renamed, re-moded, binary or linked file;
- it touches only the open surface (``OPEN``) and nothing on the closed list (``CLOSED``);
- in Python, the base's statements are all there, unchanged and in order (the patched module with the added
  statements taken out is the base module, AST for AST); an added statement is a module-level import, ``def``,
  ``class`` or literal constant under a name the base never uses, so nothing the base runs can reach it (inert);
  nothing is added inside an existing function or class, nothing runs at import (no call, decorator, class keyword
  or foreign base);
- added code reaches only an allow-list (``reach``): a few standard modules and their named members, and the
  package's or the tests' own modules that import nothing of ``EFFECTS``, by the names they define; no dunder, no
  private attribute, none of ``BANNED_NAMES``/``BANNED_ATTRS``, no ``global``, and nothing it does changes a
  module-level name. A new test runs in the suite's one process: what it could change there, it cannot name;
- `local/mutate.py` only gains rows at the end of ``MUTANTS``, each anchored exactly once; every old row's anchor in a
  touched file is still found exactly once, so every mutant the base kills is still applied to code that did not move;
- a page keeps its 80-line cap, an added line its 120 characters, no CR; no added line holds a secret, an e-mail, a
  commit trailer or a target's name (`29e`).
What structure cannot tell, the meaning of added page text (named by its lines) and of a new test's body, is listed in
``review`` for the human who merges; the merge PR's CI runs every mutant on the patched tree (`29w` "İnceleme").
"""

from __future__ import annotations

import ast
import builtins
import hashlib
import json
import re
import sys
import unittest
from pathlib import Path
from typing import Any, Callable

from . import exitchecks, secretscan
from .treehash import TreeError, iter_files, path_problem

KIND = "seed_proposal"
STATES = ("open", "withdrawn")
RECORD_KEYS = frozenset({"id", "kind", "ref", "state", "base", "patch_sha256", "evidence"})
BASE_KEYS = frozenset({"spec_tohum_sha256", "bootstrap_sha256"})
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,79}\Z")
TEST_ID_RE = re.compile(r"^(test_[a-z0-9_]+)\.([A-Za-z_][A-Za-z0-9_]*)\.(test[A-Za-z0-9_]*)\Z")
REPORTS = "reports"
MAX_JUDGED = 3  # open proposals one head checks; the rest are `deferred`
MAX_EVIDENCE = 5
MAX_ADDED = 2000  # added lines in one patch
MAX_PATCH_BYTES = 256 * 1024
PAGE_LINES = 80
LINE_CHARS = 120
STATUSES = ("candidate", "rejected", "incomplete", "deferred", "withdrawn")

PAGES = "spec/tohum/"
BOOT_PREFIX = "seed/bootstrap/"
PKG = BOOT_PREFIX + "snowball_bootstrap/"
TESTS = BOOT_PREFIX + "tests/"
MUTATE = BOOT_PREFIX + "local/mutate.py"
TEST_FILE_RE = re.compile(r"seed/bootstrap/tests/test_[a-z0-9_]+\.py")  # a new test file (fullmatch)
# The open surface: an existing tohum page, a module of the referee's package (existing or new), a new test file,
# `MUTANTS` rows. Everything else, the stage tables, vectors, workflows, the founder capsule and the docs, is closed.
OPEN = (PAGES + "*.md", PKG + "*.py", TESTS + "test_*.py (new)", MUTATE + " (MUTANTS)")
# Closed inside the open surface (`29w` "Kapalı yüzey"): the laws and the independence page, the pages of these two
# rules, the changelog (the merger's record); the sandbox, secret, supply chain, the rival and its reproducers, the
# import, the push class, the signed state, the stage lock and tables, the operator's files, the canonical form and
# tree hash, git and the API, the ledger chain, this check and the claims book; the package's entry points.
CLOSED = (
    "spec/tohum/00-cekirdek.md", "spec/tohum/09a-bagimsizlik.md", "spec/tohum/29w-tohum-teklifi.md",
    "spec/tohum/29x-acik-iddialar.md", "spec/tohum/CHANGELOG*.md",
    PKG + "__init__.py", PKG + "__main__.py", PKG + "canon.py", PKG + "claims.py", PKG + "classify.py",
    PKG + "config.py", PKG + "container.py", PKG + "controls.py", PKG + "ghapi.py", PKG + "gitio.py",
    PKG + "importer.py", PKG + "ledgercheck.py", PKG + "licenses.py", PKG + "proposals.py", PKG + "reproduce.py",
    PKG + "rival.py", PKG + "rival_mcp.py", PKG + "secretscan.py", PKG + "stagelock.py", PKG + "stages.py",
    PKG + "state.py", PKG + "treehash.py",
)
# Findings; a reason names the first thing wrong in its part. `proposal_unread` makes a proposal `incomplete`.
MALFORMED = "proposal_malformed"
BASE_UNKNOWN = "proposal_base_unknown"
NOT_A_DIFF = "proposal_not_a_diff"
NOT_ADDITIVE = "proposal_not_additive"
SURFACE_CLOSED = "proposal_surface_closed"
MEANING = "proposal_meaning"
PAGE_CAP = "proposal_page_cap"
LINE_ENDING = "proposal_line_ending"
IDENTITY = "proposal_identity"
TOO_LARGE = "proposal_too_large"
EVIDENCE = "proposal_evidence"
ANCHOR = "proposal_anchor"
UNREAD = "proposal_unread"
UNCHECKED = "proposal_unchecked"
RUNNER = "proposal_runner"
NAMES = (MALFORMED, BASE_UNKNOWN, NOT_A_DIFF, NOT_ADDITIVE, SURFACE_CLOSED, MEANING, PAGE_CAP, LINE_ENDING, IDENTITY,
         TOO_LARGE, EVIDENCE, ANCHOR, UNREAD, UNCHECKED, RUNNER)
MAX_REASON = 200  # characters of one finding: a path or a name in it comes from the Founder's bytes (E601)
MAX_PATH = 200
# What runs, collects or reports the suite (`29w` "Kanıt", E601): the existing tests and their helpers, the runner
# scripts in `local/` (of `mutate.py` only rows may be appended, and the merge path runs the base's copy), the
# interpreter's start-up hooks and anything named like `unittest`. A patch touching one is refused, never a candidate.
RUNNER_FILES = frozenset({"conftest.py", "sitecustomize.py", "usercustomize.py"})
# A new test may not redefine what `unittest.TestCase` has (`run`, `debug`, `failureException`, `_callTestMethod`...):
# the case's own run and its result would be the Founder's. `setUp` and `tearDown` are what a test is for.
TESTCASE_MEMBERS = frozenset(dir(unittest.TestCase)) - {"setUp", "tearDown"}
# Names an addition may not bind: the import machinery's and unittest's hooks run without a caller.
HOOKS = frozenset({"setUpModule", "tearDownModule", "load_tests", "expectedFailure"})
# What added code may reach (`29w` "Erişim", E600): an allow-list, not a list of what is refused. A standard module and
# the members of it that read and compute; nothing that opens a file, a process, the network or the interpreter.
STDLIB = {
    "__future__": frozenset({"annotations"}),
    "unittest": frozenset({"TestCase"}),
    "json": frozenset({"loads", "dumps", "JSONDecodeError"}),
    "re": frozenset({"compile", "search", "match", "fullmatch", "findall", "finditer", "sub", "split", "escape",
                     "IGNORECASE", "MULTILINE", "DOTALL"}),
    "hashlib": frozenset({"sha256"}),
    "textwrap": frozenset({"dedent", "wrap"}),
    "math": frozenset({"ceil", "floor", "isfinite", "inf"}),
    "statistics": frozenset({"median", "mean"}),
    "datetime": frozenset({"datetime", "timedelta", "timezone"}),
    "collections": frozenset({"Counter", "OrderedDict", "defaultdict"}),
    "itertools": frozenset({"chain", "combinations", "islice", "product"}),
    "io": frozenset({"BytesIO", "StringIO"}),
    "copy": frozenset({"deepcopy"}),
    "typing": frozenset({"Any"}),
}
# A local module (the package's or a test module) that itself imports one of these is out of reach: what it defines
# can run a process, open the network, change files or the interpreter (`cli`, `__main__` and `gitio` among them).
EFFECTS = frozenset({"os", "subprocess", "shutil", "socket", "urllib", "http", "tempfile", "signal", "threading",
                     "multiprocessing", "ctypes", "asyncio", "importlib", "pty", "runpy", "code", "pdb", "webbrowser",
                     "ssl", "socketserver", "ftplib", "smtplib", "xmlrpc", "gc", "inspect", "builtins", "sys"})
BANNED_NAMES = frozenset({"type", "object", "vars", "getattr", "setattr", "delattr", "globals", "locals", "open",
                          "exec", "eval", "compile", "breakpoint", "input", "exit", "quit", "memoryview", "super",
                          "help", "BaseException", "SystemExit", "KeyboardInterrupt", "GeneratorExit"})
BANNED_ATTRS = frozenset({"mock", "patch", "start", "stop", "run", "write_text", "write_bytes", "unlink", "rmdir",
                          "mkdir", "rename", "touch", "chmod", "symlink_to", "hardlink_to", "open", "system", "popen",
                          "kill", "putenv", "unsetenv", "chdir", "remove", "removedirs", "makedirs", "environ",
                          "modules", "addClassCleanup", "doClassCleanups", "wasSuccessful", "debug", "f_globals",
                          "f_locals", "f_back", "f_builtins", "gi_frame", "cr_frame", "tb_frame", "tb_next",
                          "skipTest"})  # a skipped evidence test reads as green (E601)
SAFE_BASES = frozenset({"object", "Exception", "ValueError", "TypeError", "RuntimeError", "KeyError", "LookupError"})
MUTATORS = frozenset({"append", "extend", "insert", "remove", "pop", "popitem", "clear", "update", "setdefault", "add",
                      "discard", "__setitem__", "__delitem__", "start", "sort", "reverse"})
LIVE = (ast.Call, ast.Lambda, ast.NamedExpr, ast.Await, ast.Yield, ast.YieldFrom, ast.ListComp, ast.SetComp,
        ast.DictComp, ast.GeneratorExp, ast.Subscript)
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
TRAILER_RE = re.compile(r"co-authored-by|signed-off-by", re.IGNORECASE)
CODING_RE = re.compile(r"^[ \t\f]*#.*?coding[:=]")
HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
INDEX_RE = re.compile(r"^index [0-9a-f]{7,64}\.\.[0-9a-f]{7,64}(?: 100644)?\Z")
BOOT = Path(__file__).resolve().parents[1]  # the referee's copy of the delivered `seed/bootstrap/` (`25` 10b)


class Refused(Exception):
    """One finding that ends the check of a proposal."""

    def __init__(self, reason: str) -> None:
        reason = reason[:MAX_REASON]  # bounded however long the path or name the Founder wrote
        super().__init__(reason)
        self.reason = reason


def is_closed(path: str) -> bool:
    return any(path == c or (c.endswith("*.md") and path.startswith(c[:-4]) and path.endswith(".md")) for c in CLOSED)


def runner(path: str, new: bool) -> bool:
    """Whether a path is part of what runs the suite (``RUNNER_FILES``): such a patch is refused before the surface."""
    name = path.rsplit("/", 1)[-1]
    if name in RUNNER_FILES or name.endswith(".pth") or name.startswith("unittest"):
        return True
    if path.startswith(TESTS):
        return not (new and TEST_FILE_RE.fullmatch(path))
    return path.startswith(BOOT_PREFIX + "local/") and path != MUTATE


def surface(path: str, new: bool) -> bool:
    """Whether a path is on the open surface for a new (``new``) or an existing file, and not closed."""
    name = path.rsplit("/", 1)[-1]
    if is_closed(path):
        return False
    if path.startswith(PAGES) and path.count("/") == 2:
        return path.endswith(".md") and not new
    if path.startswith(PKG) and path.count("/") == 3:
        return bool(re.fullmatch(r"[a-z][a-z0-9_]*\.py", name)) and not (
            new and (name[:-3] in sys.stdlib_module_names or name[:-3].endswith("customize")))
    if path.startswith(TESTS):
        return not runner(path, new)  # a new `test_<name>.py`; what the runner owns is `runner`'s to name
    return path == MUTATE and not new


# ---------------------------------------------------------------- the diff


class FilePatch:
    def __init__(self, path: str, new: bool) -> None:
        self.path, self.new = path, new
        self.hunks: list[tuple[int, int, int, int, list[tuple[str, str]]]] = []

    def added(self) -> list[str]:
        return [text for hunk in self.hunks for tag, text in hunk[4] if tag == "+"]


def parse(text: str) -> list[FilePatch]:
    """``git diff`` output that only adds lines; anything else is refused with its finding."""
    if "\r" in text:
        raise Refused(f"{LINE_ENDING}:patch")
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    if not lines:
        raise Refused(NOT_A_DIFF)
    files: list[FilePatch] = []
    i = 0
    while i < len(lines):
        head = lines[i]
        found = re.fullmatch(r"diff --git a/(\S+) b/(\S+)", head)  # a mail header or an author line is no diff
        if not found or found.group(1) != found.group(2) or path_problem(found.group(1)):
            raise Refused(NOT_A_DIFF)
        path = found.group(1)
        if len(path) > MAX_PATH or any(f.path == path for f in files):
            raise Refused(NOT_A_DIFF)
        i += 1
        new = False
        while i < len(lines) and not lines[i].startswith("--- "):
            if lines[i] == "new file mode 100644":
                new = True
            elif not INDEX_RE.match(lines[i]):  # deleted, renamed, copied, re-moded, binary, a link, a submodule
                raise Refused(f"{NOT_ADDITIVE}:{path}")
            i += 1
        if i + 1 >= len(lines) or lines[i] != ("--- /dev/null" if new else f"--- a/{path}") \
                or lines[i + 1] != f"+++ b/{path}":
            raise Refused(f"{NOT_ADDITIVE}:{path}")
        i += 2
        fp = FilePatch(path, new)
        while i < len(lines) and lines[i].startswith("@@"):
            m = HUNK_RE.match(lines[i])
            if not m:
                raise Refused(NOT_A_DIFF)
            a, b, c, d = (int(g) if g is not None else 1 for g in m.groups())
            i += 1
            body: list[tuple[str, str]] = []
            while i < len(lines) and lines[i][:1] in (" ", "+", "-", "\\"):
                if lines[i][:1] in ("-", "\\"):  # a removed line, or a changed end of file
                    raise Refused(f"{NOT_ADDITIVE}:{path}")
                body.append((lines[i][0], lines[i][1:]))
                i += 1
            if sum(1 for t, _ in body if t == " ") != b or len(body) != d or d == b:
                raise Refused(NOT_A_DIFF)
            fp.hunks.append((a, b, c, d, body))
        if not fp.hunks:
            raise Refused(f"{NOT_ADDITIVE}:{path}")
        files.append(fp)
    return files


def apply(base: str | None, fp: FilePatch) -> tuple[str, set[int]]:
    """The patched text and the line numbers (1-based) of the added lines. Every context line must be the base's."""
    if fp.new:
        if base is not None or len(fp.hunks) != 1 or fp.hunks[0][:3] != (0, 0, 1):
            raise Refused(f"{NOT_ADDITIVE}:{fp.path}")
        old: list[str] = []
    else:
        if base is None or not base.endswith("\n"):
            raise Refused(f"{UNREAD}:{fp.path}")
        old = base.split("\n")[:-1]
    out: list[str] = []
    added: set[int] = set()
    pos = 0
    for a, b, c, _d, body in fp.hunks:
        start = a - 1 if b else a
        if start < pos or start > len(old):
            raise Refused(NOT_A_DIFF)
        out += old[pos:start]
        pos = start
        if c != len(out) + 1:
            raise Refused(NOT_A_DIFF)
        for tag, text in body:
            if tag == " ":
                if pos >= len(old) or old[pos] != text:
                    raise Refused(NOT_A_DIFF)
                out.append(text)
                pos += 1
            else:
                out.append(text)
                added.add(len(out))
    out += old[pos:]
    return "\n".join(out) + "\n", added


# ---------------------------------------------------------------- Python


def _span(node: ast.AST) -> range:
    first = min([node.lineno] + [d.lineno for d in getattr(node, "decorator_list", [])])
    return range(first, node.end_lineno + 1)


def _identifiers(tree: ast.AST) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            found.add(node.id)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            found.add(node.name)
        elif isinstance(node, ast.arg):
            found.add(node.arg)
        elif isinstance(node, ast.alias):
            found.add(node.asname or node.name.split(".")[0])
        elif isinstance(node, ast.Attribute):
            found.add(node.attr)
    return found


def _literal(node: ast.AST) -> bool:
    try:
        ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError, RecursionError, MemoryError):
        return False
    return True


def _lazy(tree: ast.Module) -> bool:
    return any(isinstance(n, ast.ImportFrom) and n.module == "__future__"
               and any(a.name == "annotations" for a in n.names) for n in tree.body)


def _live(node: ast.AST | None) -> bool:
    return node is not None and any(isinstance(n, LIVE) for n in ast.walk(node))


def _signature_live(fn: ast.FunctionDef | ast.AsyncFunctionDef, lazy: bool) -> bool:
    a = fn.args
    if any(not _literal(d) for d in a.defaults + [d for d in a.kw_defaults if d is not None]):
        return True
    notes = [x.annotation for x in a.posonlyargs + a.args + a.kwonlyargs + [a.vararg, a.kwarg] if x is not None]
    notes.append(fn.returns)
    return not lazy and any(_live(n) for n in notes)


def _bound(node: ast.stmt) -> list[str]:
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        return [a.asname or a.name.split(".")[0] for a in node.names]
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return [node.name]
    if isinstance(node, ast.Assign):
        return [t.id for t in node.targets if isinstance(t, ast.Name)]
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return [node.target.id]
    return []


def _top(node: ast.stmt, tree: ast.Module, test: bool, classes: set[str]) -> str | None:
    """Why one added module-level statement is not inert (None when it is). What an import, a class keyword or a
    dunder name may reach is ``reach``'s to say, once."""
    lazy = _lazy(tree)
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        return None
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if node.decorator_list or getattr(node, "type_params", None) or _signature_live(node, lazy):
            return "def"
        return None
    if isinstance(node, ast.ClassDef):
        if node.decorator_list or getattr(node, "type_params", None):
            return "class"
        for base in node.bases:
            if test and isinstance(base, (ast.Name, ast.Attribute)) and not _live(base):
                continue
            if not (isinstance(base, ast.Name) and (base.id in SAFE_BASES or base.id in classes)):
                return "class_base"
        for item in node.body:
            if test and set(_bound(item)) & TESTCASE_MEMBERS:
                return "testcase_member"
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if item.decorator_list or getattr(item, "type_params", None) or _signature_live(item, lazy):
                    return "method"
            elif isinstance(item, ast.Assign):
                if len(item.targets) != 1 or not isinstance(item.targets[0], ast.Name) or not _literal(item.value):
                    return "class_body"
            elif not isinstance(item, ast.Pass) and not (isinstance(item, ast.Expr)
                                                         and isinstance(item.value, ast.Constant)
                                                         and isinstance(item.value.value, str)):
                return "class_body"
        return None
    if isinstance(node, ast.Assign):
        ok = len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and _literal(node.value)
        return None if ok else "assign"
    if isinstance(node, ast.AnnAssign):
        ok = (isinstance(node.target, ast.Name) and node.value is not None and _literal(node.value)
              and (lazy or not _live(node.annotation)))
        return None if ok else "assign"
    return "statement"


def _root(node: ast.AST) -> str | None:
    while isinstance(node, (ast.Attribute, ast.Subscript, ast.Call)):
        node = node.func if isinstance(node, ast.Call) else node.value
    return node.id if isinstance(node, ast.Name) else None


def _defined(path: str, current: Callable[[str], str | None]) -> frozenset[str] | None:
    """The public names a local module defines (``def``, ``class``, assignment), or None when it is out of reach: it
    is missing, unreadable or imports one of ``EFFECTS`` itself."""
    text = current(path)
    if text is None:
        return None
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError, RecursionError, MemoryError):
        return None
    for node in ast.walk(tree):
        roots = ([a.name.split(".")[0] for a in node.names] if isinstance(node, ast.Import) else
                 [(node.module or "").split(".")[0]] if isinstance(node, ast.ImportFrom) and not node.level else [])
        if set(roots) & EFFECTS:
            return None
    names = {n for node in tree.body if not isinstance(node, (ast.Import, ast.ImportFrom)) for n in _bound(node)}
    return frozenset(n for n in names if not n.startswith("_"))


def imports(node: ast.Import | ast.ImportFrom, test: bool,
            current: Callable[[str], str | None]) -> dict[str, frozenset[str] | None]:
    """What one import binds, each name with the members it may reach when it is a module (None for a value); Refused
    when it reaches past the allow-list. A test imports the package absolutely, the package itself relatively."""
    if isinstance(node, ast.Import):
        if any(a.name not in STDLIB or a.name == "__future__" for a in node.names):
            raise Refused("import")
        return {a.asname or a.name: STDLIB[a.name] for a in node.names}
    module, names = node.module or "", [a.name for a in node.names]
    if not node.level and module in STDLIB:
        if not set(names) <= STDLIB[module]:
            raise Refused("import")
        return {a.asname or a.name: None for a in node.names}
    if (test and not node.level and module == "snowball_bootstrap") or (not test and node.level == 1 and not module):
        bound: dict[str, frozenset[str] | None] = {}
        for a in node.names:
            found = _defined(f"{PKG}{a.name}.py", current) if re.fullmatch(r"[a-z][a-z0-9_]*", a.name) else None
            if found is None:
                raise Refused("import")
            bound[a.asname or a.name] = found
        return bound
    if test and not node.level and re.fullmatch(r"snowball_bootstrap\.[a-z][a-z0-9_]*", module):
        path = f"{PKG}{module.split('.')[1]}.py"
    elif not test and node.level == 1 and re.fullmatch(r"[a-z][a-z0-9_]*", module):
        path = f"{PKG}{module}.py"
    elif test and not node.level and re.fullmatch(r"test_[a-z0-9_]+", module):
        path = f"{TESTS}{module}.py"
    else:
        raise Refused("import")
    found = _defined(path, current)
    if found is None or not set(names) <= found:
        raise Refused("import")
    return {a.asname or a.name: None for a in node.names}


def _changes(node: ast.AST, module_names: set[str]) -> bool:
    """Whether one node changes a module-level name: an assignment, ``del`` or changing call rooted at one."""
    targets: list[ast.AST] = []
    if isinstance(node, (ast.Assign, ast.Delete)):
        targets = list(node.targets)
    elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
        targets = [node.target]
    elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in MUTATORS:
        return _root(node.func.value) in module_names
    return any(isinstance(leaf, (ast.Attribute, ast.Subscript)) and _root(leaf) in module_names
               for target in targets for leaf in ast.walk(target))


def _foreign_store(top: ast.stmt) -> int | None:
    """The first line where added code assigns to or deletes an attribute of anything but its own instance: the first
    parameter of a method of a class the patch defines, and not a member ``unittest.TestCase`` has. Through an alias a
    shared object is reachable by any name (``t = unittest.TestCase; t.assertEqual = f``, E601)."""
    def walk(node: ast.AST, own: str | None) -> int | None:
        for child in ast.iter_child_nodes(node):
            inner = own
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                args = child.args.posonlyargs + child.args.args
                inner = args[0].arg if isinstance(node, ast.ClassDef) and args else None
            elif isinstance(child, ast.ClassDef):
                inner = None
            if isinstance(child, ast.Attribute) and isinstance(child.ctx, (ast.Store, ast.Del)) and not (
                    own is not None and isinstance(child.value, ast.Name) and child.value.id == own
                    and child.attr not in TESTCASE_MEMBERS):
                return child.lineno
            if (found := walk(child, inner)) is not None:
                return found
        return None
    return walk(ast.Module(body=[top], type_ignores=[]), None)


def reach(added: list[ast.stmt], tree: ast.Module, test: bool, current: Callable[[str], str | None]) -> int | None:
    """The first line where added code reaches past what it may (`29w` "Erişim"; None when it does not): an import
    off the allow-list, a module-level name the base imported from off it, a member of an imported module the module
    does not offer, a dunder or private name, a banned name or attribute, ``global`` or ``nonlocal``, a dunder method
    other than ``__init__``, a class keyword, or a change to a module-level name. A test body runs in the suite's one
    process: what it could change there, it cannot name."""
    module_names: set[str] = set()
    reachable: dict[str, frozenset[str] | None] = {}
    blocked: set[str] = set()
    for node in tree.body:
        module_names |= set(_bound(node))
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            try:
                reachable.update(imports(node, test, current))
            except Refused:
                blocked |= set(_bound(node))
    for top in added:
        if (line := _foreign_store(top)) is not None:
            return line
        local = dict(reachable)
        for node in ast.walk(top):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                try:
                    local.update(imports(node, test, current))
                except Refused:
                    return node.lineno
        for node in ast.walk(top):
            line = getattr(node, "lineno", top.lineno)
            if isinstance(node, (ast.Global, ast.Nonlocal)) or _changes(node, module_names):
                return line
            if isinstance(node, ast.Name) and (node.id in BANNED_NAMES or node.id.startswith("__")
                                               or (node.id in blocked and node.id not in local)):
                return line
            if isinstance(node, ast.Attribute):
                members = local.get(node.value.id) if isinstance(node.value, ast.Name) else None
                if node.attr.startswith("_") or node.attr in BANNED_ATTRS or (
                        members is not None and node.attr not in members):
                    return line
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("__") \
                    and node.name != "__init__":
                return line
            if isinstance(node, ast.ClassDef) and node.keywords:
                return line
    return None


def check_python(path: str, base: str | None, text: str, added: set[int], test: bool,
                 current: Callable[[str], str | None]) -> list[str]:
    """Review entries of an inert Python addition; Refused when it is not one."""
    try:
        tree = ast.parse(text, filename=path)
        old = ast.parse(base, filename=path) if base is not None else ast.Module(body=[], type_ignores=[])
    except (SyntaxError, ValueError, RecursionError, MemoryError):
        raise Refused(f"{MEANING}:{path}:0") from None
    lines = text.split("\n")
    cookie = next((n for n in sorted(added) if n <= 2 and CODING_RE.match(lines[n - 1])), None)
    if cookie is not None:  # an encoding declaration changes how every byte of the file is read
        raise Refused(f"{MEANING}:{path}:{cookie}")
    kept, inserted = [], []
    for node in tree.body:
        (inserted if set(_span(node)) <= added else kept).append(node)
    if base is None and inserted and isinstance(inserted[0], ast.Expr) and isinstance(inserted[0].value, ast.Constant) \
            and isinstance(inserted[0].value.value, str):
        inserted = inserted[1:]  # a new file's docstring
    covered = {n for node in inserted for n in _span(node)}
    if base is None:
        covered |= set(_span(tree.body[0])) if tree.body else set()
    stray = sorted(n for n in added - covered if lines[n - 1].strip() and not lines[n - 1].lstrip().startswith("#"))
    if stray:  # an addition inside an existing statement: the base's code would run differently
        raise Refused(f"{MEANING}:{path}:{stray[0]}")
    stripped = ast.Module(body=kept, type_ignores=[])
    if base is not None and ast.dump(stripped) != ast.dump(old):
        raise Refused(f"{MEANING}:{path}:{min(added) if added else 0}")
    if base is not None and old.body and inserted and tree.body.index(inserted[0]) == 0:
        raise Refused(f"{MEANING}:{path}:{inserted[0].lineno}")  # before the docstring or the __future__ import
    taken = _identifiers(old) | set(dir(builtins))
    classes = {n.name for n in inserted if isinstance(n, ast.ClassDef)}
    review = []
    bound: set[str] = set()
    for node in inserted:
        why = _top(node, tree, test, classes)
        future = isinstance(node, ast.ImportFrom) and node.module == "__future__"
        names = [] if future else _bound(node)
        clash = [n for n in names if n in taken or n in bound or n in HOOKS or n.startswith("skip")]
        if why or clash:
            raise Refused(f"{MEANING}:{path}:{node.lineno}")
        bound |= set(names)
        if base is not None and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            review.append(f"appended:{path}:{node.name}")
    if (line := reach(inserted, tree, test, current)) is not None:
        raise Refused(f"{MEANING}:{path}:{line}")
    if base is None:
        review.append(f"{'tests' if test else 'new_module'}:{path}")
    return review


# ---------------------------------------------------------------- the mutants


def _strings(node: ast.AST, consts: dict[str, str]) -> str | None:
    """The value of a string expression `mutate.py` writes its rows with: a literal, an f-string over its own string
    constants, or a sum of these; None for anything else."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        parts = []
        for v in node.values:
            if isinstance(v, ast.Constant) and isinstance(v.value, str):
                parts.append(v.value)
            elif (isinstance(v, ast.FormattedValue) and isinstance(v.value, ast.Name) and v.value.id in consts
                  and v.conversion == -1 and v.format_spec is None):
                parts.append(consts[v.value.id])
            else:
                return None
        return "".join(parts)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _strings(node.left, consts), _strings(node.right, consts)
        return None if left is None or right is None else left + right
    return None


def _mutants(tree: ast.Module) -> tuple[ast.Assign, dict[str, str]]:
    consts: dict[str, str] = {}
    found = None
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name == "MUTANTS" and isinstance(node.value, ast.List):
                found = node
            elif (value := _strings(node.value, consts)) is not None:
                consts[name] = value
    if found is None:
        raise Refused(f"{MEANING}:{MUTATE}:0")
    return found, consts


def _row(node: ast.AST, consts: dict[str, str]) -> tuple[str, ...] | None:
    if not (isinstance(node, ast.Tuple) and len(node.elts) == 5):
        return None
    values = tuple(_strings(e, consts) for e in node.elts)
    return None if any(v is None for v in values) else values  # type: ignore[return-value]


def check_mutants(base: str, text: str, added: set[int], files: Callable[[str], str | None]) -> list[str]:
    """New rows only at the end of `MUTANTS`, each new and anchored once; every old row in a touched file still once."""
    try:
        old, new = ast.parse(base), ast.parse(text)
    except (SyntaxError, ValueError, RecursionError, MemoryError):
        raise Refused(f"{MEANING}:{MUTATE}:0") from None
    old_list, consts = _mutants(old)
    new_list, _ = _mutants(new)
    count = len(old_list.value.elts)
    appended = new_list.value.elts[count:]
    if not appended:
        raise Refused(f"{MEANING}:{MUTATE}:{min(added) if added else 0}")
    new_list.value.elts = new_list.value.elts[:count]
    if ast.dump(new) != ast.dump(old):
        raise Refused(f"{MEANING}:{MUTATE}:{min(added)}")
    names = {r[0] for e in old_list.value.elts if (r := _row(e, consts)) is not None}
    for node in appended:
        row = _row(node, consts)
        if row is None or not re.fullmatch(r"[a-z0-9_]{3,80}", row[0]) or row[0] in names or row[2] == row[3]:
            raise Refused(f"{MEANING}:{MUTATE}:{node.lineno}")
        names.add(row[0])
        target = files(row[1])
        if target is None:
            raise Refused(f"{UNREAD}:{row[1]}")
        if target.count(row[2]) != 1:
            raise Refused(f"{ANCHOR}:{row[0]}")
    return [f"mutants:+{len(appended)}"]


def mutant_names_in(text: str, paths: set[str]) -> list[str]:
    """The names of `MUTANTS` rows anchored in one of ``paths`` (the merge path runs the base's rows of a touched file
    on the patched tree); none for a text that is no readable `mutate.py`."""
    try:
        rows, consts = _mutants(ast.parse(text))
    except (Refused, SyntaxError, ValueError, RecursionError, MemoryError):
        return []
    return [row[0] for e in rows.value.elts if (row := _row(e, consts)) is not None and row[1] in paths]


def new_mutant_names(base: str, text: str) -> list[str]:
    """The names of the rows a checked patch appended to `MUTANTS` (the merge path runs exactly these)."""
    old_list, consts = _mutants(ast.parse(base))
    new_list, _ = _mutants(ast.parse(text))
    return [row[0] for e in new_list.value.elts[len(old_list.value.elts):] if (row := _row(e, consts)) is not None]


def old_anchors(base_mutate: str | None, patched: dict[str, str]) -> None:
    """Every base row anchored in a touched file is still found there exactly once (its mutant still applies)."""
    if base_mutate is None:
        raise Refused(f"{UNREAD}:{MUTATE}")
    try:
        old_list, consts = _mutants(ast.parse(base_mutate))
    except (SyntaxError, ValueError, RecursionError, MemoryError):
        raise Refused(f"{UNREAD}:{MUTATE}") from None
    for node in old_list.value.elts:
        row = _row(node, consts)
        if row is not None and row[1] in patched and patched[row[1]].count(row[2]) != 1:
            raise Refused(f"{ANCHOR}:{row[0]}")


# ---------------------------------------------------------------- one proposal


def _ranges(lines: set[int]) -> str:
    """The added lines of a page as the merger reads them: ``3-5,9``."""
    out: list[list[int]] = []
    for n in sorted(lines):
        if out and out[-1][1] == n - 1:
            out[-1][1] = n
        else:
            out.append([n, n])
    return ",".join(str(a) if a == b else f"{a}-{b}" for a, b in out)


def _hygiene(files: list[FilePatch], names: list[tuple[int, int, str]]) -> None:
    """Size, line width, then the identity rules. The width comes before any pattern, so no expression ever scans a
    line longer than ``LINE_CHARS`` (the e-mail pattern backtracks on one long line for minutes, E601)."""
    added = [line for fp in files for line in fp.added()]
    if len(added) > MAX_ADDED:
        raise Refused(TOO_LARGE)
    for fp in files:
        if any(len(t) > LINE_CHARS for t in fp.added()):
            raise Refused(f"{PAGE_CAP}:{fp.path}")
    for line in added:
        if secretscan.scan(line):
            raise Refused(f"{IDENTITY}:secret")
        if EMAIL_RE.search(line):
            raise Refused(f"{IDENTITY}:email")
        if TRAILER_RE.search(line):
            raise Refused(f"{IDENTITY}:trailer")
        if exitchecks.withheld(line, names) != line:
            raise Refused(f"{IDENTITY}:target_name")


def check(record: Any, patch: bytes, epoch: Any, names: list[tuple[int, int, str]],
          base_file: Callable[[str], str | None]) -> list[str]:
    """The review list of a proposal that passes; Refused with the first finding otherwise."""
    if epoch is None or record["base"] != {"spec_tohum_sha256": epoch.spec_tohum_sha256,
                                           "bootstrap_sha256": epoch.bootstrap_sha256}:
        raise Refused(BASE_UNKNOWN)  # a proposal is judged against the delivered seed only, never stacked
    if len(patch) > MAX_PATCH_BYTES:
        raise Refused(TOO_LARGE)
    try:
        text = patch.decode("utf-8")
    except UnicodeDecodeError:
        raise Refused(NOT_A_DIFF) from None
    files = parse(text)
    for fp in files:
        if runner(fp.path, fp.new):
            raise Refused(f"{RUNNER}:{fp.path}")
        if not surface(fp.path, fp.new):
            raise Refused(f"{SURFACE_CLOSED}:{fp.path}")
    _hygiene(files, names)
    patched: dict[str, str] = {}
    added_at: dict[str, set[int]] = {}
    for fp in files:
        patched[fp.path], added_at[fp.path] = apply(base_file(fp.path), fp)

    def current(path: str) -> str | None:
        return patched[path] if path in patched else base_file(path)

    review: list[str] = []
    for fp in files:
        text_now, added = patched[fp.path], added_at[fp.path]
        if fp.path.startswith(PAGES):
            if len(text_now.split("\n")) - 1 > PAGE_LINES:
                raise Refused(f"{PAGE_CAP}:{fp.path}")
            review.append(f"page_text:{fp.path}:{_ranges(added)}")
        elif fp.path == MUTATE:
            review += check_mutants(base_file(fp.path) or "", text_now, added, current)
        else:
            review += check_python(fp.path, base_file(fp.path), text_now, added, fp.path.startswith(TESTS),
                                   current)
    old_anchors(base_file(MUTATE), patched)
    tests = record["evidence"]["tests"]
    for test_id in tests:
        m = TEST_ID_RE.match(test_id)
        path = f"{TESTS}{m.group(1)}.py" if m else ""
        fp = next((f for f in files if f.path == path and f.new), None)
        if fp is None:
            raise Refused(f"{EVIDENCE}:{test_id}")
        cls = next((n for n in ast.parse(patched[path]).body if isinstance(n, ast.ClassDef) and n.name == m.group(2)),
                   None)
        if cls is None or not any(isinstance(f, ast.FunctionDef) and f.name == m.group(3) for f in cls.body):
            raise Refused(f"{EVIDENCE}:{test_id}")
    return review


def _record(data: Any, stem: str) -> dict[str, Any] | None:
    ok = (isinstance(data, dict) and set(data) == RECORD_KEYS and data["kind"] == KIND and data["id"] == stem
          and ID_RE.match(stem) and data["state"] in STATES and isinstance(data["ref"], str) and len(data["ref"]) <= 500
          and isinstance(data["base"], dict) and set(data["base"]) == BASE_KEYS
          and isinstance(data["patch_sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", data["patch_sha256"])
          and isinstance(data["evidence"], dict) and set(data["evidence"]) == {"tests"}
          and isinstance(data["evidence"]["tests"], list) and 1 <= len(data["evidence"]["tests"]) <= MAX_EVIDENCE
          and all(isinstance(t, str) for t in data["evidence"]["tests"]))
    return data if ok else None


def committed_text(raw: bytes) -> str | None:
    """A base file's text as git holds it, whatever the checkout did to its line endings: a checkout with
    ``core.autocrlf=true`` writes every LF of a text file as CRLF (E601), so bytes whose every newline is CRLF and
    that hold no other CR read as LF. Every file a patch may touch is LF in the seed's git (``-text`` is only under
    ``vectors/``, closed), and a patch carries no CR at all. None for bytes that are not UTF-8."""
    if b"\r\n" in raw and raw.count(b"\r") == raw.count(b"\r\n") == raw.count(b"\n"):
        raw = raw.replace(b"\r\n", b"\n")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return None


def base_reader(tar_bytes_files: dict[str, bytes]) -> Callable[[str], str | None]:
    """The delivered seed as the referee holds it: `spec/tohum/` from the brain head (the seed tree check holds it to
    the epoch, `29b`), `seed/bootstrap/` from the referee's own copy (`bootstrap_sha256`), each as git holds it
    (``committed_text``): a Windows checkout reads the same base as a Linux one."""
    def read(path: str) -> str | None:
        if path.startswith(PAGES):
            raw = tar_bytes_files.get(path)
        elif path.startswith(BOOT_PREFIX) and path_problem(path) is None:
            local = BOOT / path[len(BOOT_PREFIX):]
            raw = local.read_bytes() if local.is_file() else None
        else:
            raw = None
        return None if raw is None else committed_text(raw)
    return read


def judge(tar_bytes: bytes, epoch: Any, names: list[tuple[int, int, str]]) -> list[dict[str, Any]]:
    """Every proposal record directly under `reports/`, by path: ``{id, json_sha256, patch_sha256, status, reasons,
    review}``. At most ``MAX_JUDGED`` open ones are checked, the rest are ``deferred``; a check that cannot finish is
    ``incomplete``, never a candidate."""
    try:
        files = {p.as_posix(): content for p, content, _x in iter_files(tar_bytes)}
    except TreeError:
        return []
    rows = []
    judged = 0
    read = base_reader(files)
    for path in sorted(files):
        parts = path.split("/")
        if len(parts) != 2 or parts[0] != REPORTS or not parts[1].endswith(".json"):
            continue
        raw = files[path]
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError, RecursionError):
            continue
        if not isinstance(data, dict) or data.get("kind") != KIND:
            continue
        stem = parts[1][:-5]
        patch = files.get(f"{REPORTS}/{stem}.patch")
        row: dict[str, Any] = {"id": stem[:80], "json_sha256": hashlib.sha256(raw).hexdigest(),
                               "patch_sha256": None if patch is None else hashlib.sha256(patch).hexdigest(),
                               "status": "rejected", "reasons": [], "review": []}
        rows.append(row)
        record = _record(data, stem)
        if record is None or patch is None or record["patch_sha256"] != row["patch_sha256"]:
            row["reasons"] = [MALFORMED]
            continue
        if record["state"] == "withdrawn":
            row["status"] = "withdrawn"
            continue
        if judged >= MAX_JUDGED:
            row["status"] = "deferred"
            continue
        judged += 1
        try:
            row["review"] = check(record, patch, epoch, names, read)
            row["status"] = "candidate"
        except Refused as found:
            row["reasons"] = [found.reason]
            row["status"] = "incomplete" if found.reason.startswith(UNREAD) else "rejected"
        except (ValueError, TypeError, KeyError, IndexError, AttributeError, RecursionError, MemoryError) as exc:
            row["reasons"] = [f"{UNCHECKED}:{type(exc).__name__}"]
            row["status"] = "incomplete"
    return rows
