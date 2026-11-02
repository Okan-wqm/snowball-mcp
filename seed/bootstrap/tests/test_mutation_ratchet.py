"""The mutation-kill ratchet on the Founder's code (E515; the A/F/G plan's WP7, watcher G1, red team T3).

A push may not make the tests weaker: a mutant the base's tests killed on the base, still in the pushed tree, must be
killed by the push's tests on the push. Two kinds of runner stand in for the referee's container: `LocalRunner` runs
the synthetic brain's real unittest commands in a subprocess (so a mutant really breaks the code), and `ScriptRunner`
answers each command from the mutant in the tree (faults, flaky tests, import failures, forged output).
"""

import io
import shlex
import subprocess
import sys
import tarfile
import tempfile
import time
import unittest
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from snowball_bootstrap import mutation
from snowball_bootstrap.container import RunResult
from snowball_bootstrap.stages import MicroFeature, StageTable

MODULE = "referee/calc/ops.py"
OPS = '''"""A tiny module for the ratchet's tests."""


def clamp(x, lo, hi):
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x
'''
STRONG = '''import unittest

from calc.ops import clamp


class OpsTest(unittest.TestCase):
    def test_clamp(self):
        self.assertEqual(clamp(-5, 0, 10), 0)
        self.assertEqual(clamp(15, 0, 10), 10)
        self.assertEqual(clamp(5, 0, 10), 5)
        self.assertEqual(clamp(0, 0, 10), 0)
        self.assertEqual(clamp(10, 0, 10), 10)
'''
# The same test with all but the lower bound's first assertion taken out: what T3's weakening looks like.
WEAK = STRONG.split("        self.assertEqual(clamp(15, 0, 10), 10)\n")[0]
T1 = "cd referee && python -m unittest discover -s tests -p test_ops.py"
T2 = "cd referee && python -m unittest discover -s tests -p test_other.py"
TABLE = StageTable(stage=0, mfs=(MicroFeature(1, (1,), (), "calc/ops.py", ()),))
LIMIT = 10_000_000


def tar_of(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        for name, text in files.items():
            data = text.encode("utf-8")
            info = tarfile.TarInfo(name)
            info.size, info.mode = len(data), 0o644
            tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def brain(test: str = STRONG, ops: str = OPS, **extra: str) -> bytes:
    return tar_of({MODULE: ops, "referee/calc/__init__.py": "", "referee/tests/test_ops.py": test, **extra})


def tests_of(*cmds: str) -> list[dict]:
    return [{"id": f"T{i}", "cmd": cmd, "stage": 0} for i, cmd in enumerate(cmds, 1)]


@dataclass
class LocalRunner:
    """Runs `cd D && python ARGS` in the tree with this Python, no shell: the container's job, without docker."""

    tree: Path
    calls: list = field(default_factory=list)

    def run(self, cmd: str, *, cwd: str = ".", stdin: bytes = b"", timeout_s: int) -> RunResult:
        self.calls.append(cmd)
        argv = shlex.split(cmd)
        if argv[0] == "cd" and argv[2] == "&&":
            cwd, argv = argv[1], argv[3:]
        argv = [sys.executable if a == "python" else a for a in argv]
        start = time.monotonic()
        proc = subprocess.run(argv, cwd=self.tree / cwd, capture_output=True, timeout=timeout_s, check=False,
                              env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "", "SYSTEMROOT": "C:\\Windows"})
        return RunResult(proc.returncode, proc.stdout, proc.stderr, int((time.monotonic() - start) * 1000))


@dataclass
class ScriptRunner:
    """Answers each command from the module as the tree holds it now: ``answer(side, cmd, cwd, mutated)`` where
    ``mutated`` is the module's bytes when a mutant is in place and None when it is the original."""

    tree: Path
    answer: Callable[[str, str, str, bytes | None], RunResult]
    original: bytes
    calls: list = field(default_factory=list)

    def run(self, cmd: str, *, cwd: str = ".", stdin: bytes = b"", timeout_s: int) -> RunResult:
        self.calls.append((self.tree.name, cmd, timeout_s))
        now = (self.tree / MODULE).read_bytes()
        return self.answer(self.tree.name, cmd, cwd, None if now == self.original else now)


def ok() -> RunResult:
    return RunResult(0, b"OK\n", b"", 5)


def fail(text: bytes = b"AssertionError: 1 != 2\n") -> RunResult:
    return RunResult(1, b"", text, 5)


class Measured:
    """A ratchet run over the synthetic brain with one runner kind; keeps the runners for their calls."""

    def __init__(self, test_case: unittest.TestCase, make: Callable[[Path], object]):
        self.runners: dict[str, object] = {}
        tmp = tempfile.TemporaryDirectory()
        test_case.addCleanup(tmp.cleanup)
        self.work = Path(tmp.name)

        def make_runner(tree: Path):
            self.runners[tree.name] = make(tree)
            return self.runners[tree.name]
        self.make_runner = make_runner

    def run(self, head: bytes, base: bytes | None, head_tests: list[dict], base_tests: list[dict] | None = None,
            **kw) -> list[dict]:
        self.rows = mutation.run(self.make_runner, self.work, head, head_tests, mutation.units(TABLE, [1])[:1], 60,
                                 LIMIT, base_tar=base, base_tests=base_tests or head_tests,
                                 compared=["MF1"] if base is not None else [], **kw)
        self.found = mutation.summary(self.rows)
        return self.found


def scripted(test_case: unittest.TestCase, answer) -> Measured:
    return Measured(test_case, lambda tree: ScriptRunner(tree, answer, OPS.encode()))


class RealRunTest(unittest.TestCase):
    """E515: the ratchet with real test commands on a real (synthetic) module."""

    def test_a_weakened_test_is_a_drop_and_names_its_unit(self):  # ratchet_ignores_drop
        m = Measured(self, LocalRunner)
        found = m.run(brain(WEAK), brain(STRONG), tests_of(T1))
        self.assertEqual(mutation.reasons(found), ["mutation_kill_dropped:MF1"])
        self.assertEqual(mutation.unmeasured(found), [])
        s = found[0]
        self.assertEqual((s["killed"], s["survived"], s["common"]), (3, 4, 7))
        self.assertEqual(len(s["dropped"]), 4)  # every mutant only the taken-out assertions killed
        self.assertEqual(s["rate"], "3/7")

    def test_the_same_tests_on_the_same_code_drop_nothing(self):
        m = Measured(self, LocalRunner)
        found = m.run(brain(STRONG), brain(STRONG), tests_of(T1))
        self.assertEqual(mutation.reasons(found), [])
        self.assertEqual((found[0]["killed"], found[0]["survived"], found[0]["rate"]), (7, 0, "7/7"))
        self.assertEqual(found[0]["killed_named"], 7)

    def test_a_kill_the_named_tests_miss_comes_from_the_suite(self):  # named_tier_never_falls_back named_first_ignored
        """E502's follow-up: the unit's own tests first; another declared test kills what they miss, and the suite
        runs only for those."""
        other = STRONG.replace("class OpsTest", "class OtherTest")
        m = Measured(self, LocalRunner)
        suite = [{"id": "T2", "cmd": T2, "stage": 0}, {"id": "T1", "cmd": T1, "stage": 0}]  # the named one last
        found = m.run(brain(WEAK, **{"referee/tests/test_other.py": other}), None, suite)
        s = found[0]
        self.assertEqual((s["killed"], s["killed_named"], s["survived"]), (7, 3, 0))
        mutated_runs = m.runners["head"].calls[2:]  # after the unmutated T2 and T1
        self.assertEqual(mutated_runs.count(T1), 7)
        self.assertEqual(mutated_runs.count(T2), 4)  # only the four the named test missed

    def test_the_head_is_red_unmutated_so_nothing_is_measured(self):  # head_red_judged
        broken = OPS.replace("return x\n", "return -x\n")
        m = Measured(self, LocalRunner)
        found = m.run(brain(STRONG, ops=broken), brain(STRONG), tests_of(T1))
        self.assertEqual(mutation.reasons(found), [])
        self.assertEqual(mutation.unmeasured(found), ["mutation_unmeasured:MF1"])
        self.assertEqual(found[0]["unmeasured"], "head_red")


class IdentityTest(unittest.TestCase):
    """E515: a mutant keeps its key while its site stays, so base and head can be compared."""

    def test_a_moved_or_reformatted_line_keeps_its_mutants(self):  # key_carries_line_number
        before = {m.key for m in mutation.mutants(OPS.encode(), MODULE)}
        moved = OPS.replace('"""A tiny module for the ratchet\'s tests."""\n',
                            '"""A tiny module."""\n\nLIMIT = None\n\n\ndef other(y):\n    return y\n')
        moved = moved.replace("if x < lo:", "if x   <   lo:")
        after = {m.key for m in mutation.mutants(moved.encode(), MODULE)}
        self.assertTrue(before <= after)
        self.assertEqual(len(before), 7)

    def test_a_changed_line_makes_new_mutants_and_equal_sites_get_ordinals(self):
        changed = OPS.replace("if x > hi:", "if x >= hi:")
        keys = [m.key for m in mutation.mutants(changed.encode(), MODULE)]
        self.assertEqual(len(keys), len(set(keys)))
        before = {m.key for m in mutation.mutants(OPS.encode(), MODULE)}
        self.assertEqual(len(set(keys) - before), 2)  # the flip and the negation of the changed comparison
        twice = "def f(a):\n    if a < 0:\n        return 1\n    if a < 0:\n        return 1\n    return 0\n"
        keys = [m.key for m in mutation.mutants(twice.encode(), "referee/x.py")]
        self.assertEqual(len(keys), len(set(keys)))

    def test_every_mutant_compiles_and_differs_from_the_original(self):
        found = mutation.mutants(OPS.encode(), MODULE)
        self.assertEqual(sorted({m.op for m in found}), ["flip_comparison", "negate_condition", "return_none"])
        for m in found:
            compile(m.source, MODULE, "exec")
            self.assertNotEqual(m.source, OPS.encode())
        self.assertEqual(mutation.mutants(b"def broken(:\n", MODULE), [])

    def test_the_share_is_salted_and_stable_per_mutant(self):  # share_ignored share_unsalted
        src = "\n".join(f"def f{i}(a):\n    if a < {i}:\n        return {i}\n    return a\n" for i in range(40))
        every = mutation.mutants(src.encode(), "referee/x.py")
        half = [m.key for m in every if mutation.chosen(m.key, b"one", 0.5)]
        other = [m.key for m in every if mutation.chosen(m.key, b"two", 0.5)]
        self.assertTrue(0.3 * len(every) < len(half) < 0.7 * len(every))
        self.assertNotEqual(half, other)
        kept = mutation.mutants(src.encode(), "referee/x.py", lambda key: mutation.chosen(key, b"one", 0.5))
        self.assertEqual([m.key for m in kept], half)


class UnitTest(unittest.TestCase):
    """E515: the units are the micro-features' module paths and `rest`, everything else under `referee/`."""

    def test_rest_owns_what_no_module_path_owns(self):  # rest_unit_dropped rest_owns_module_paths test_files_mutated
        us = mutation.units(TABLE, [1])
        self.assertEqual([(u.label, u.root, u.named) for u in us],
                         [("MF1", MODULE, ("T1",)), ("rest", "referee", ())])
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp)
            for rel in (MODULE, "referee/calc/__init__.py", "referee/loop/job.py", "referee/tests/test_ops.py",
                        "referee/loop/test_job.py", "referee/loop/data.json", "tests/test_top.py"):
                (tree / rel).parent.mkdir(parents=True, exist_ok=True)
                (tree / rel).write_text("x = 1\n", encoding="utf-8")
            self.assertEqual(mutation.unit_files(tree, us[0]), [MODULE])
            self.assertEqual(mutation.unit_files(tree, us[1]), ["referee/calc/__init__.py", "referee/loop/job.py"])

    def test_import_names(self):
        self.assertEqual(mutation.import_name("referee/ledger/chain.py"), "ledger.chain")
        self.assertEqual(mutation.import_name("referee/gate/__init__.py"), "gate")
        self.assertIsNone(mutation.import_name("referee/a-b/c.py"))
        self.assertIsNone(mutation.import_name("other/c.py"))
        self.assertIsNone(mutation.import_name('referee/x";rm.py'))


class OutcomeTest(unittest.TestCase):
    """E515: what counts as a kill, an exclusion, a fault and a drop."""

    def test_an_import_breaking_mutant_is_excluded_not_killed(self):  # import_error_counted_as_kill
        def answer(side, cmd, cwd, mutated):
            if mutated is None:
                return ok()
            if cmd.startswith("python -c"):  # the probe: every mutant breaks the import here
                return fail(b"ModuleNotFoundError: No module named 'calc'\n")
            return fail(b"ImportError: Failed to import test module: test_ops\n")
        found = scripted(self, answer).run(brain(), None, tests_of(T1))
        self.assertEqual((found[0]["killed"], found[0]["excluded"], found[0]["rate"]), (0, 7, "0/0"))

    def test_a_test_printing_import_error_does_not_hide_its_kills(self):  # exclusion_trusts_output_text
        def answer(side, cmd, cwd, mutated):
            if mutated is None or cmd.startswith("python -c"):  # the module imports, mutated or not
                return ok()
            return fail(b"AssertionError\nImportError: (printed by the test)\n")
        found = scripted(self, answer).run(brain(), None, tests_of(T1))
        self.assertEqual((found[0]["killed"], found[0]["excluded"]), (7, 0))

    def test_a_docker_failure_is_a_fault_never_a_kill(self):  # fault_counted_as_kill
        def answer(side, cmd, cwd, mutated):
            return ok() if mutated is None else RunResult(125, b"", b"docker: error\n", 5)
        found = scripted(self, answer).run(brain(), brain(), tests_of(T1))
        self.assertEqual((found[0]["killed"], found[0]["fault"]), (0, 7))
        self.assertEqual(mutation.unmeasured(found), ["mutation_unmeasured:MF1"])
        self.assertEqual(mutation.reasons(found), [])

    def test_a_timeout_kills_and_the_timeout_follows_the_unmutated_duration(self):  # timeout_not_scaled
        def answer(side, cmd, cwd, mutated):
            return ok() if mutated is None else RunResult(124, b"", b"", 9000, timed_out=True)
        m = scripted(self, answer)
        found = m.run(brain(), None, tests_of(T1))
        self.assertEqual(found[0]["killed"], 7)
        timeouts = [t for _side, cmd, t in m.runners["head"].calls if cmd == T1]
        self.assertEqual(timeouts[0], 60)  # unmutated: the referee's own
        self.assertEqual(set(timeouts[1:]), {mutation.TIMEOUT_FLOOR_S})  # 3 x 5 ms, floored

    def test_excluded_at_the_head_but_killed_at_the_base_is_a_drop(self):  # excluded_at_head_not_a_drop
        """A module that refuses to import once its own text changes turns every kill into an exclusion."""
        def answer(side, cmd, cwd, mutated):
            if mutated is None:
                return ok()
            if side == "head":
                return fail(b"ImportError: integrity\n")
            return ok() if cmd.startswith("python -c") else fail()
        found = scripted(self, answer).run(brain(), brain(), tests_of(T1))
        self.assertEqual(mutation.reasons(found), ["mutation_kill_dropped:MF1"])
        self.assertEqual(len(found[0]["dropped"]), 7)

    def test_a_kill_the_base_does_not_repeat_is_flaky_not_a_drop(self):  # drop_not_confirmed
        seen: dict[bytes, int] = {}

        def answer(side, cmd, cwd, mutated):
            if mutated is None or side == "head":
                return ok()
            seen[mutated] = seen.get(mutated, 0) + 1
            return fail() if seen[mutated] == 1 else ok()  # the base's test fails once, then passes
        found = scripted(self, answer).run(brain(), brain(), tests_of(T1))
        self.assertEqual(mutation.reasons(found), [])
        self.assertEqual(found[0]["flaky"], 7)

    def test_a_red_base_is_unmeasured_never_a_rejection(self):  # base_red_still_judged
        def answer(side, cmd, cwd, mutated):
            return ok() if side == "head" else fail()
        found = scripted(self, answer).run(brain(), brain(), tests_of(T1))
        self.assertEqual(mutation.reasons(found), [])
        self.assertEqual(found[0]["unmeasured"], "base_red")

    def test_the_base_runs_only_for_what_the_head_did_not_kill(self):  # base_runs_for_every_mutant
        def answer(side, cmd, cwd, mutated):
            return ok() if mutated is None else fail()
        m = scripted(self, answer)
        found = m.run(brain(), brain(), tests_of(T1))
        self.assertEqual(found[0]["common"], 7)
        self.assertEqual(m.runners["base"].calls, [])  # every mutant died at the head: the base never ran

    def test_records_carry_no_mechanics(self):  # row_carries_key
        m = Measured(self, LocalRunner)
        found = m.run(brain(WEAK), brain(STRONG), tests_of(T1), salt=b"s")
        text = repr(m.rows) + repr(found)
        for secret in ("calc", "ops.py", "clamp", "flip_comparison", "negate_condition", "return_none", "Compare"):
            self.assertNotIn(secret, text)
        ids = {r["id"] for r in m.rows}
        self.assertEqual(len(ids), 7)
        with tempfile.TemporaryDirectory() as tmp:
            mutation.Side(LocalRunner, brain(STRONG), Path(tmp), [], 1, LIMIT).tree
            where = mutation.explain(Path(tmp), mutation.units(TABLE, [1])[0], found[0]["dropped"], b"s")
        self.assertEqual(len(where), 4)
        self.assertTrue(all(path == MODULE for path, _line, _op in where))


if __name__ == "__main__":
    unittest.main()
