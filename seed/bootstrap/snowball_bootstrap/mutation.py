"""Mutation-kill ratchet on the Founder's code (E515; the A/F/G plan's WP7, watcher G1, red team T3).

Module-less red (`moduleless.py`) shows that a micro-feature's tests import its module, not that they test what it
does. This module breaks the Founder's code on purpose, one small change at a time (a mutant), and asks the push's
declared tests to notice. A push may not make the tests weaker: a mutant that the last accepted head's tests killed on
the last accepted head, and that the pushed tree still has, must be killed by the push's tests on the push. One that is
not names its unit in `mutation_kill_dropped:<unit>`.

- **Units.** One per finished micro-feature (`MFk`: the non-test `.py` files under its stage-table module path, under
  `referee/`) and one more, `rest`: every other non-test `.py` file under `referee/`. The Founder's work does not stay
  inside the module paths: of the brain's 55 non-test files at `4423ff3`, 38 (7025 lines) belong to no micro-feature,
  and the last three accepted code pushes added 0, 0 and 13 lines inside module paths against 235, 381 and 302 outside
  them (E515). A ratchet on the module paths alone would not see most of the code a push changes.
- **Mutants.** The operators of the operator's private measure (`measure/mutate_live.py`, adapted): a comparison
  flipped, a condition negated, an integer constant +1 and -1, a returned value made `None`, a `raise` dropped; made
  with the standard library's `ast` over whole files, not only the changed lines (a ratchet compares the lines that
  did not change). A mutant that does not compile is never run.
- **Identity.** A mutant is known across pushes by its key: the file, the operator, the enclosing def or class, the
  node as `ast.dump` prints it (no positions) and its ordinal among equal ones. A line moved, re-indented or
  reformatted keeps its mutants; a changed line makes new ones.
- **Selection.** With a share below 1, a mutant runs when its salted id falls below the share: the choice depends on
  the mutant alone, so a site that stays is chosen on every push, and without the salt nobody can tell which.
- **Running.** Each mutant runs its unit's own tests first (a micro-feature's stage-table tests) and, only if they
  all stay green, the rest of the declared suite: a test that fails in the subset fails in the suite, so the answer
  is the suite's, at the subset's cost when the subset kills (E502's follow-up). A failure kills, a timeout kills (a
  mutant that loops), a docker failure (125) is a fault and decides nothing. A test's timeout is a multiple of its
  unmutated duration, capped by the referee's own.
- **Import failures are excluded, and the referee decides what one is.** A failing test whose output names an import
  or syntax error triggers a probe the referee owns: importing the mutated module alone. If that import fails the
  mutant only broke the import (excluded); if it imports, the failure is a kill. The test's own output never decides:
  a test that prints `ImportError` to hide its kills hides nothing. Where the unmutated module does not import alone,
  the probe says nothing and the output's words decide, as in `mutate_live.py`.
- **The base is measured again, not read from a record.** For each selected mutant the head did not kill (survived or
  excluded) whose key the base also has, the same mutant runs on the base with the base's tests. Killed there and not
  killed here is a drop; it runs once more on both sides and counts only if both say it again (a flaky test is not a
  drop). A mutant the head killed cannot drop, so the base runs only for the head's survivors. Excluded at the head
  counts as not killed: a module that refuses to import once its own text changes hides nothing either.
- **Unmeasured.** A head or base that is red unmutated in this sandbox, or a fault, leaves the unit unmeasured:
  `unmeasured` names it and the caller treats it as an outage, never as the Founder's rejection. A drop seen twice on
  both sides stands even so.

The rows and the summary carry counts and salted mutant ids only: no file, line, function or operator of any mutant,
killed or not (the mechanics stay off the Founder's side; `explain` maps an id back for the operator's private use).
Python only: the target's TypeScript and Rust are not mutated here.
"""

from __future__ import annotations

import ast
import hashlib
import math
import re
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Iterable

from .container import Runner, RunResult
from .moduleless import DOCKER_ERROR
from .stages import MODULE_ROOT, StageTable
from .treehash import extract

REASON = "mutation_kill_dropped"
UNMEASURED = "mutation_unmeasured"
REST = "rest"
KILLED, SURVIVED, EXCLUDED, FAULT = "killed", "survived", "excluded", "fault"
# A failing test whose output names one of these may only have broken the import: the probe decides (never the text).
IMPORT_MARKERS = (b"ModuleNotFoundError", b"ImportError", b"SyntaxError", b"IndentationError", b"TabError")
MODULE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*\Z")
CONFIRM_RUNS = 2  # a drop is seen this many times on each side before it counts
TIMEOUT_FACTOR = 3  # a mutated test may take this many times its unmutated duration ...
TIMEOUT_FLOOR_S = 10  # ... and at least this many seconds, never more than the referee's own test timeout
SHARE_BITS = 64
FLIP = {ast.Eq: ast.NotEq, ast.NotEq: ast.Eq, ast.Lt: ast.GtE, ast.GtE: ast.Lt, ast.Gt: ast.LtE, ast.LtE: ast.Gt,
        ast.In: ast.NotIn, ast.NotIn: ast.In, ast.Is: ast.IsNot, ast.IsNot: ast.Is}
OPERATORS = ("flip_comparison", "negate_condition", "constant_plus_one", "constant_minus_one", "return_none",
             "drop_raise")


@dataclass(frozen=True)
class Unit:
    label: str  # "MFk" or "rest"
    root: str  # a module path, or `referee` for the rest
    named: tuple[str, ...] = ()  # the test ids that run first
    outside: tuple[str, ...] = ()  # module paths under ``root`` that are other units'


@dataclass(frozen=True)
class Mutant:
    path: str  # posix, relative to the tree's root
    op: str
    line: int
    key: str  # stable across pushes while the site stays (see the module's "Identity")
    source: bytes  # the whole mutated file


@dataclass(frozen=True)
class Outcome:
    status: str  # killed | survived | excluded | fault
    runs: int  # container runs it took
    ms: int  # their summed duration
    tier: str = ""  # "named" or "suite": which tests killed it


def units(table: StageTable, mfs: Iterable[int]) -> list[Unit]:
    """One unit per micro-feature in ``mfs`` (table order of the caller's list), then `rest`: everything under
    `referee/` that no module path of this table or a finished one owns."""
    found = [Unit(f"MF{k}", table.feature(k).module_path, tuple(f"T{n}" for n in table.feature(k).tests))
             for k in mfs]
    owned = [f.module_path for t in (*table.before, table) for f in t.mfs]
    return found + [Unit(REST, MODULE_ROOT, (), tuple(owned))]


def is_test(rel: str) -> bool:
    """A test file by the brain's conventions (as `mutate_live.py`): never mutated."""
    parts = PurePosixPath(rel).parts
    return "tests" in parts or "test" in parts or parts[-1].startswith("test_") or parts[-1].endswith("_test.py")


def _under(rel: str, root: str) -> bool:
    return rel == root or rel.startswith(root.rstrip("/") + "/")


def unit_files(tree: Path, unit: Unit) -> list[str]:
    """The non-test `.py` files of ``unit`` in ``tree``, sorted."""
    root = tree.joinpath(*PurePosixPath(unit.root).parts)
    files = [root] if root.is_file() else sorted(root.rglob("*.py")) if root.is_dir() else []
    rels = [f.relative_to(tree).as_posix() for f in files if f.is_file() and f.suffix == ".py"]
    return [r for r in rels if not is_test(r) and not any(_under(r, o) for o in unit.outside)]


def _scopes(tree: ast.AST) -> dict[int, str]:
    """id(node) -> the dotted name of the def or class it sits in ("" at module level)."""
    found: dict[int, str] = {}

    def visit(node: ast.AST, scope: str) -> None:
        for child in ast.iter_child_nodes(node):
            found[id(child)] = scope
            named = isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            visit(child, f"{scope}.{child.name}".lstrip(".") if named else scope)

    visit(tree, "")
    return found


def _offsets(src: bytes) -> list[int]:
    starts, pos = [0], 0
    for line in src.split(b"\n")[:-1]:
        pos += len(line) + 1
        starts.append(pos)
    return starts


def mutants(src: bytes, path: str, keep: Callable[[str], bool] = lambda key: True) -> list[Mutant]:
    """The mutants of one file whose key ``keep`` accepts, in source order; each compiles. A file that does not parse
    has none. Keys and ordinals are given before ``keep`` and the compile check, so they do not depend on either."""
    try:
        tree = ast.parse(src)
    except (SyntaxError, ValueError, RecursionError, MemoryError):
        return []
    starts, scopes = _offsets(src), _scopes(tree)

    def span(node: Any) -> tuple[int, int]:
        return starts[node.lineno - 1] + node.col_offset, starts[node.end_lineno - 1] + node.end_col_offset

    sites: list[tuple[int, int, int, str, Any, str]] = []

    def add(op: str, node: Any, anchor: Any, replacement: str) -> None:
        sites.append((anchor.lineno, anchor.col_offset, OPERATORS.index(op), op, node, replacement))

    for node in ast.walk(tree):
        if isinstance(node, ast.Compare) and len(node.ops) == 1 and type(node.ops[0]) in FLIP:
            flipped = ast.Compare(left=node.left, ops=[FLIP[type(node.ops[0])]()], comparators=node.comparators)
            add("flip_comparison", node, node, "(" + ast.unparse(flipped) + ")")
        if isinstance(node, (ast.If, ast.While, ast.IfExp, ast.Assert)):
            a, b = span(node.test)
            add("negate_condition", node.test, node, f"(not ({src[a:b].decode('utf-8')}))")
        if isinstance(node, ast.Constant) and type(node.value) is int:
            add("constant_plus_one", node, node, f"({node.value + 1})")
            add("constant_minus_one", node, node, f"({node.value - 1})")
        if isinstance(node, ast.Return) and node.value is not None:
            add("return_none", node, node, "return None")
        if isinstance(node, ast.Raise):
            add("drop_raise", node, node, "pass")
    out: list[Mutant] = []
    seen: dict[str, int] = {}
    for line, _col, _order, op, node, replacement in sorted(sites, key=lambda s: s[:3]):
        site = "\0".join((path, op, scopes.get(id(node), ""), ast.dump(node)))
        seen[site] = seen.get(site, -1) + 1
        key = f"{site}\0{seen[site]}"
        if not keep(key):
            continue
        a, b = span(node)
        mutated = src[:a] + replacement.encode("utf-8") + src[b:]
        try:
            compile(mutated, path, "exec", dont_inherit=True)
        except (SyntaxError, ValueError, RecursionError, MemoryError):
            continue
        out.append(Mutant(path, op, line, key, mutated))
    return out


def mutant_id(key: str, salt: bytes) -> str:
    """The id a record carries: the key hashed with the salt (G-2: evidence hashes are salted)."""
    return hashlib.sha256(salt + b"\0" + key.encode("utf-8")).hexdigest()


def chosen(key: str, salt: bytes, share: float) -> bool:
    """Whether a mutant runs at this share: its salted id below the share, so the choice is the mutant's alone."""
    return share >= 1 or int(mutant_id(key, salt)[:SHARE_BITS // 4], 16) < share * 2 ** SHARE_BITS


def plan(tree: Path, unit: Unit, keep: Callable[[str], bool] = lambda key: True) -> list[Mutant]:
    """The mutants of ``unit`` in ``tree`` whose key ``keep`` accepts."""
    found: list[Mutant] = []
    for rel in unit_files(tree, unit):
        found += mutants(tree.joinpath(*PurePosixPath(rel).parts).read_bytes(), rel, keep)
    return found


def explain(tree: Path, unit: Unit, ids: Iterable[str], salt: bytes) -> list[tuple[str, int, str]]:
    """(file, line, operator) of each id in ``tree``: for the operator's private evidence, never for a record."""
    wanted = set(ids)
    return [(m.path, m.line, m.op) for m in plan(tree, unit, lambda key: mutant_id(key, salt) in wanted)]


def import_name(path: str, root: str = MODULE_ROOT) -> str | None:
    """The dotted module a probe imports for ``path`` (``referee/ledger/chain.py`` -> ``ledger.chain``), run from
    ``root``; None when it has no importable name."""
    pure = PurePosixPath(path)
    if not pure.parts or pure.parts[0] != root or pure.suffix != ".py":
        return None
    parts = list(pure.with_suffix("").parts[1:])
    if parts and parts[-1] == "__init__":
        parts.pop()
    name = ".".join(parts)
    return name if MODULE_NAME_RE.match(name) else None


def _names_import(res: RunResult) -> bool:
    data = res.stdout + b"\n" + res.stderr
    return any(m in data for m in IMPORT_MARKERS)


@dataclass
class Side:
    """One tree (the head or the base) with its declared tests: extracted once; each mutant is written into it, run
    and put back."""

    make_runner: Callable[[Path], Runner]
    tar_bytes: bytes
    dest: Path
    tests: list[dict[str, Any]]  # the manifest's tests that run, in order
    timeout_s: int
    max_bytes: int
    _runner: Runner | None = None
    _durations: dict[str, int] = field(default_factory=dict)
    _green: bool | None = None
    _probe_ok: dict[str, bool] = field(default_factory=dict)

    @property
    def tree(self) -> Path:
        if self._runner is None:
            extract(self.tar_bytes, self.dest, self.max_bytes)
            self._runner = self.make_runner(self.dest)
        return self.dest

    @property
    def runner(self) -> Runner:
        _ = self.tree
        assert self._runner is not None
        return self._runner

    def green(self) -> bool:
        """Every test passes unmutated here (asked once): without it every mutant would look killed."""
        if self._green is None:
            self._green = bool(self.tests)
            for test in self.tests:
                res = self.runner.run(test["cmd"], timeout_s=self.timeout_s)
                self._durations[test["id"]] = res.duration_ms
                if not res.ok:
                    self._green = False
                    break
        return self._green

    def timeout(self, test_id: str) -> int:
        ms = self._durations.get(test_id, self.timeout_s * 1000)
        return min(self.timeout_s, max(TIMEOUT_FLOOR_S, math.ceil(TIMEOUT_FACTOR * ms / 1000)))

    def _probe(self, path: str) -> bool | None:
        """Whether the file at ``path``, as the tree has it now, imports on its own; None when no probe applies or
        docker failed."""
        name = import_name(path)
        if name is None:
            return None
        res = self.runner.run(f'python -c "import {name}"', cwd=MODULE_ROOT, timeout_s=TIMEOUT_FLOOR_S * 3)
        return None if res.exit_code == DOCKER_ERROR and not res.timed_out else res.ok

    def probe_applies(self, path: str) -> bool:
        """Whether the unmutated file imports by the probe: if not, the probe says nothing for this file."""
        if path not in self._probe_ok:
            self._probe_ok[path] = self._probe(path) is True
        return self._probe_ok[path]

    def judge(self, mutant: Mutant, named: Iterable[str]) -> Outcome:
        """Run one mutant: its unit's own tests first, the rest of the suite only if they all stay green."""
        wanted = set(named)
        tiers = (("named", [t for t in self.tests if t["id"] in wanted]),
                 ("suite", [t for t in self.tests if t["id"] not in wanted]))
        probe = self.probe_applies(mutant.path)
        target = self.tree.joinpath(*PurePosixPath(mutant.path).parts)
        original = target.read_bytes()
        target.write_bytes(mutant.source)
        runs = ms = 0
        try:
            for tier, tests in tiers:
                for test in tests:
                    res = self.runner.run(test["cmd"], timeout_s=self.timeout(test["id"]))
                    runs, ms = runs + 1, ms + res.duration_ms
                    if res.exit_code == DOCKER_ERROR and not res.timed_out:
                        return Outcome(FAULT, runs, ms)
                    if res.ok:
                        continue
                    if res.timed_out or not _names_import(res):
                        return Outcome(KILLED, runs, ms, tier)
                    if not probe:  # the probe says nothing here: the output's words decide (`mutate_live.py`)
                        return Outcome(EXCLUDED, runs, ms)
                    imports = self._probe(mutant.path)
                    if imports is None:
                        return Outcome(FAULT, runs + 1, ms)
                    return Outcome(KILLED, runs + 1, ms, tier) if imports else Outcome(EXCLUDED, runs + 1, ms)
            return Outcome(SURVIVED, runs, ms)
        finally:
            target.write_bytes(original)


def run(make_runner: Callable[[Path], Runner], work: Path, head_tar: bytes, head_tests: list[dict[str, Any]],
        todo_units: list[Unit], timeout_s: int, max_bytes: int, *, base_tar: bytes | None = None,
        base_tests: list[dict[str, Any]] | None = None, compared: Iterable[str] = (), salt: bytes = b"",
        share: float = 1.0, mine: Callable[[int], bool] = lambda place: True) -> list[dict[str, Any]]:
    """One row per selected mutant of each unit (in order; with ``mine``, only the rows whose place it names, as
    module-less red shares its runs out among parts, E440), or one row for a unit that could not be measured. A unit
    whose label is in ``compared`` (finished at the base) is compared with the base."""
    head = Side(make_runner, head_tar, work / "head", head_tests, timeout_s, max_bytes)
    base = (Side(make_runner, base_tar, work / "base", base_tests or [], timeout_s, max_bytes)
            if base_tar is not None else None)
    at_base = set(compared) if base is not None else set()
    planned: list[tuple[Unit, Mutant]] = []
    for unit in todo_units:
        planned += [(unit, m) for m in plan(head.tree, unit, lambda key: chosen(key, salt, share))]
    todo = [(unit, m) for place, (unit, m) in enumerate(planned) if mine(place)]
    if todo and not head.green():
        return [{"unit": label, "unmeasured": "head_red"} for label in dict.fromkeys(u.label for u, _m in todo)]
    twins: dict[str, dict[str, Mutant]] = {}
    rows: list[dict[str, Any]] = []
    for unit, m in todo:
        got = head.judge(m, unit.named)
        row = {"unit": unit.label, "id": mutant_id(m.key, salt), "head": got.status, "tier": got.tier,
               "common": False, "base": None, "dropped": False, "flaky": False, "runs": got.runs, "ms": got.ms}
        if base is not None and unit.label in at_base:
            if unit.label not in twins:
                twins[unit.label] = {b.key: b for b in plan(base.tree, unit, lambda key: chosen(key, salt, share))}
            twin = twins[unit.label].get(m.key)
            row["common"] = twin is not None
            if twin is not None and got.status in (SURVIVED, EXCLUDED):
                _compare(row, head, base, m, twin, unit.named)
        rows.append(row)
    return rows


def _compare(row: dict[str, Any], head: Side, base: Side, m: Mutant, twin: Mutant, named: tuple[str, ...]) -> None:
    """The base's answer for a mutant the head did not kill, and whether it is a drop both sides say again."""
    if not base.green():
        row["base"] = "red"
        return
    then = base.judge(twin, named)
    row.update(base=then.status, runs=row["runs"] + then.runs, ms=row["ms"] + then.ms)
    if then.status != KILLED:
        return
    for _ in range(CONFIRM_RUNS - 1):
        again_head, again_base = head.judge(m, named), base.judge(twin, named)
        row.update(runs=row["runs"] + again_head.runs + again_base.runs, ms=row["ms"] + again_head.ms + again_base.ms)
        if again_head.status in (KILLED, FAULT) or again_base.status != KILLED:
            row["flaky"] = True
            return
    row["dropped"] = True


def summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Per unit, in order of first appearance: the counts, the kill rate (killed over killed and survived, "k/n"),
    the drops by id, and why it went unmeasured (None when it did not)."""
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        s = out.setdefault(row["unit"], {"unit": row["unit"], KILLED: 0, SURVIVED: 0, EXCLUDED: 0, FAULT: 0,
                                         "killed_named": 0, "common": 0, "dropped": [], "flaky": 0, "runs": 0,
                                         "ms": 0, "unmeasured": None})
        if "unmeasured" in row:
            s["unmeasured"] = row["unmeasured"]
            continue
        s[row["head"]] += 1
        s["killed_named"] += row["tier"] == "named"
        s["common"] += row["common"]
        s["flaky"] += row["flaky"]
        s["runs"] += row["runs"]
        s["ms"] += row["ms"]
        if row["dropped"]:
            s["dropped"].append(row["id"])
        if row["base"] == "red":
            s["unmeasured"] = "base_red"
        elif FAULT in (row["head"], row["base"]) and not s["unmeasured"]:
            s["unmeasured"] = "fault"
    for s in out.values():
        s["rate"] = f"{s[KILLED]}/{s[KILLED] + s[SURVIVED]}"
    return list(out.values())


def reasons(found: list[dict[str, Any]]) -> list[str]:
    """`mutation_kill_dropped:<unit>` for each unit with a drop: each was seen twice on both sides, so a fault
    elsewhere in the unit does not take it back."""
    return [f"{REASON}:{s['unit']}" for s in found if s["dropped"]]


def unmeasured(found: list[dict[str, Any]]) -> list[str]:
    """`mutation_unmeasured:<unit>` for each unit this sandbox could not measure: an outage, not the Founder's."""
    return [f"{UNMEASURED}:{s['unit']}" for s in found if s["unmeasured"]]
