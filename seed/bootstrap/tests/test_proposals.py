"""The Founder's seed proposals, checked by the referee (`tohum/29w`; the owner's decision of 2026-11-14, E594). The
trailing comment on a test names the mutants it kills (`local/mutate.py`). Every patch here is written against this
checkout, the delivered seed as the referee's copy holds it."""

import ast
import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from snowball_bootstrap import config, proposals
from snowball_bootstrap.decide import decide
from snowball_bootstrap.exitchecks import target_names

from helpers import commit, make_repo
from test_decision import green_run, meta_, not_refuted, state0

BOOT = Path(__file__).resolve().parents[1]
ROOT = BOOT.parents[1]
EPOCH = config.SeedEpoch(commit="1" * 40, spec_tohum_sha256="2" * 64, seed_sha256=None, bootstrap_sha256="3" * 64)
BASE = {"spec_tohum_sha256": "2" * 64, "bootstrap_sha256": "3" * 64}
PAGE = "spec/tohum/29t-kendi-harita-denetimi.md"
MODULE = "seed/bootstrap/snowball_bootstrap/selfmap.py"
NEW_MODULE = "seed/bootstrap/snowball_bootstrap/mapcheck.py"
NEW_TEST = "seed/bootstrap/tests/test_mapcheck.py"
MUTATE = "seed/bootstrap/local/mutate.py"


def read(path: str) -> str | None:
    target = ROOT / path
    return target.read_text(encoding="utf-8") if target.is_file() else None


def insert(path: str, after: int, lines: list[str], context: bool = True) -> str:
    """A `git diff` that inserts ``lines`` after line ``after`` of ``path`` (0: at the top), with one context line."""
    old = read(path).split("\n")[:-1]
    head = f"diff --git a/{path} b/{path}\nindex 1111111..2222222 100644\n--- a/{path}\n+++ b/{path}\n"
    if context and after:
        body = [" " + old[after - 1]] + ["+" + x for x in lines]
        return head + f"@@ -{after},1 +{after},{len(lines) + 1} @@\n" + "\n".join(body) + "\n"
    return head + f"@@ -{after},0 +{after + 1},{len(lines)} @@\n" + "".join(f"+{x}\n" for x in lines)


def insert_text(path: str, old: str, lines: list[str]) -> str:
    """A `git diff` appending ``lines`` to a file whose text is ``old`` (one line), for a seed made up in a test."""
    return (f"diff --git a/{path} b/{path}\nindex 1111111..2222222 100644\n--- a/{path}\n+++ b/{path}\n"
            f"@@ -1,1 +1,{len(lines) + 1} @@\n {old.rstrip(chr(10))}\n" + "".join(f"+{x}\n" for x in lines))


def new_file(path: str, lines: list[str]) -> str:
    return (f"diff --git a/{path} b/{path}\nnew file mode 100644\nindex 0000000..2222222\n--- /dev/null\n+++ b/{path}\n"
            f"@@ -0,0 +1,{len(lines)} @@\n" + "".join(f"+{x}\n" for x in lines))


MODULE_LINES = ['"""A new inert module."""', "", "from __future__ import annotations", "", "LIMIT = 3", "", "",
                "def over(n: int) -> bool:", "    return n > LIMIT"]
TEST_LINES = ['"""Evidence."""', "", "import unittest", "", "from snowball_bootstrap import mapcheck", "", "",
              "class Over(unittest.TestCase):", "    def test_over(self):", "        self.assertTrue(mapcheck.over(4))"]


def mutants_end() -> int:
    text = read(MUTATE)
    return text[:text.index("\n]\n\n\ndef stale_anchors")].count("\n") + 1


def good_patch() -> str:
    mutant = ['    ("mapcheck_limit_moved", f"{PKG}/mapcheck.py", "LIMIT = 3", "LIMIT = 9",',
              '     "E594: an example row"),']
    return (insert(MODULE, len(read(MODULE).split("\n")) - 1, ["", "", "def unused_helper(x):", "    return x"])
            + new_file(NEW_MODULE, MODULE_LINES) + new_file(NEW_TEST, TEST_LINES)
            + insert(PAGE, 41, ["", "Ek bir paragraf."]) + insert(MUTATE, mutants_end(), mutant))


def record(patch: str, **over) -> dict:
    rec = {"id": "prop-001", "kind": "seed_proposal", "ref": "spec/tohum/29t-kendi-harita-denetimi.md:1",
           "state": "open", "base": BASE, "patch_sha256": hashlib.sha256(patch.encode()).hexdigest(),
           "evidence": {"tests": ["test_mapcheck.Over.test_over"]}}
    rec.update(over)
    return rec


def check(patch: str, names=(), **over):
    return proposals.check(record(patch, **over), patch.encode(), EPOCH, list(names), read)


def refused(patch: str, **over) -> str:
    try:
        check(patch, **over)
    except proposals.Refused as found:
        return found.reason
    return "candidate"


class Candidate(unittest.TestCase):
    def test_an_inert_addition_with_its_evidence_is_a_candidate_with_its_review(self):  # proposal_review_unwritten
        self.assertEqual(check(good_patch()), [
            f"appended:{MODULE}:unused_helper", f"new_module:{NEW_MODULE}", f"tests:{NEW_TEST}",
            f"page_text:{PAGE}:42-43",
            "mutants:+1"])

    def test_the_new_mutant_names_are_what_the_merge_path_runs(self):
        text = read(MUTATE)
        patch = insert(MUTATE, mutants_end(), ['    ("x_row", f"{PKG}/decide.py", "RESULT_SCHEMA", "R", "w"),'])
        fp = proposals.parse(patch)[0]
        self.assertEqual(proposals.new_mutant_names(text, proposals.apply(text, fp)[0]), ["x_row"])


class DiffForm(unittest.TestCase):
    def test_only_added_lines_of_a_plain_diff(self):  # proposal_deletion_allowed proposal_mode_change_allowed
        good = insert(PAGE, 41, ["x"])
        cases = {
            good.replace("+x\n", "-x\n"): f"proposal_not_additive:{PAGE}",
            good.replace("index 1111111..2222222 100644\n", "old mode 100644\nnew mode 100755\n"):
                f"proposal_not_additive:{PAGE}",
            good.replace("index 1111111..2222222 100644\n", "similarity index 90%\nrename from a\nrename to b\n"):
                f"proposal_not_additive:{PAGE}",
            good + "\\ No newline at end of file\n": f"proposal_not_additive:{PAGE}",
            f"diff --git a/{PAGE} b/{PAGE}\nindex 1111111..2222222\nBinary files differ\n":
                f"proposal_not_additive:{PAGE}",
            "From abc Mon Sep 17 00:00:00 2001\nSubject: x\n\n" + good: "proposal_not_a_diff",
            good.replace(f"b/{PAGE}\n", "b/other.md\n", 1): "proposal_not_a_diff",
            good.replace("+x", "+x\r"): "proposal_line_ending:patch",
            good.replace("@@ -41,1 +41,2 @@", "@@ -40,1 +40,2 @@"): "proposal_not_a_diff",  # a context not the base's
            # proposal_hunk_count_unchecked
            good.replace("@@ -41,1 +41,2 @@", "@@ -41,1 +41,3 @@"): "proposal_not_a_diff",
        }
        for patch, reason in cases.items():
            with self.subTest(reason=reason, patch=patch[-80:]):
                self.assertEqual(refused(patch), reason)

    def test_a_new_file_must_not_exist_and_an_old_one_must(self):  # proposal_new_file_overwrites
        self.assertEqual(refused(new_file(MODULE, ['"""x"""'])), f"proposal_not_additive:{MODULE}")
        self.assertEqual(refused(insert(MODULE, 1, ["x"]).replace(MODULE, NEW_MODULE)), f"proposal_unread:{NEW_MODULE}")
        self.assertEqual(refused(new_file("seed/bootstrap/snowball_bootstrap/decide.py", ['"""x"""'])),
                         "proposal_not_additive:seed/bootstrap/snowball_bootstrap/decide.py")


class Surface(unittest.TestCase):
    def test_the_closed_list_and_everything_off_the_surface_is_refused(self):  # proposal_closed_file_open
        for path in proposals.CLOSED:
            path = path.replace("*", "")
            with self.subTest(path=path):
                self.assertFalse(proposals.surface(path, False))
        for path, new in (("seed/bootstrap/stages/stage0.json", False), ("seed/bootstrap/vectors/x/y.json", True),
                          (".github/workflows/ci.yml", False), ("docs/eksik-kaydi.md", False),
                          ("seed/founder/launch.py", False), ("spec/INDEX.md", False), ("spec/tohum/new.md", True),
                          ("seed/bootstrap/tests/test_flow.py", False), ("seed/bootstrap/tests/helpers2.py", True),
                          ("seed/bootstrap/snowball_bootstrap/json.py", True),  # proposal_customize_allowed
                          ("seed/bootstrap/snowball_bootstrap/sitecustomize.py", True),
                          ("seed/bootstrap/snowball_bootstrap/sub/x.py", True), (MUTATE, True)):
            with self.subTest(path=path):
                self.assertFalse(proposals.surface(path, new))  # proposal_surface_open
        for path, new in ((PAGE, False), (MODULE, False), (NEW_MODULE, True), (NEW_TEST, True), (MUTATE, False)):
            self.assertTrue(proposals.surface(path, new))
        rival = "seed/bootstrap/snowball_bootstrap/rival.py"
        self.assertEqual(refused(insert(rival, 10, ["# x"])), f"proposal_surface_closed:{rival}")
        self.assertEqual(refused(insert("spec/tohum/CHANGELOG.md", 7, ["- x"])),
                         "proposal_surface_closed:spec/tohum/CHANGELOG.md")


class Inert(unittest.TestCase):
    END = len(read(MODULE).split("\n")) - 1

    def top(self, lines, path=MODULE, after=None):
        return refused(insert(path, self.END if after is None else after, lines))

    def test_inert_module_level_additions_pass(self):
        for lines in (["", "", "def helper(a, b=1, *c, d=(1, 2)):", "    return helper(a)"],
                      ["", "", "class Finding(ValueError):", '    """x"""', "    LEVEL = 1", "", "    def go(self):",
                       "        return 1"],
                      ["", "NEW_LIMIT = {'a': (1, -2)}"], ["", "import statistics as stats2"],
                      ["", "from . import canon as canon2"],
                      ["", "# a comment"]):
            with self.subTest(lines=lines):  # every check passed; only the evidence is missing
                self.assertEqual(refused(insert(MODULE, self.END, lines)),
                                 "proposal_evidence:test_mapcheck.Over.test_over")

    def test_whatever_could_run_or_change_the_bases_code_is_refused(self):  # proposal_decorator_allowed
        line = self.END
        body = next(i for i, x in enumerate(read(MODULE).split("\n"), 1) if x.startswith("    return"))
        cases = {
            "in_body": (["    return None"], body - 1),  # an early return inside an old function
            "rebind": (["MISSING = 'x'"], line),  # proposal_name_rebound
            "tuple_rebind": (["MISSING, X_NEW = 'x', 1"], line),  # proposal_attr_assign_allowed
            "rebind_import": (["import re as hashlib"], line),
            "shadow_builtin": (["def pow(x):", "    return 0"], line),  # proposal_builtin_shadow_allowed
            "dunder": (["def __getattr__(name):", "    return 1"], line),  # proposal_dunder_def_allowed
            "call": (["print('x')"], line),  # proposal_module_level_call_allowed
            "decorator": (["@staticmethod", "def deco(x):", "    return x"], line),
            "metaclass": (["class K(metaclass=type):", "    pass"], line),  # proposal_class_keyword_allowed
            "foreign_base": (["class K(dict):", "    pass"], line),  # proposal_foreign_base_allowed
            "default_call": (["def f(x=print()):", "    return x"], line),
            "hook": (["def load_tests(a, b, c):", "    return b"], line),
            "skip": (["def skipper(x):", "    return x"], line),
            "star": (["from os import *"], line),
            "future": (["from __future__ import division"], line),
            "assign_call": (["X_NEW = len('x')"], line),
            "attr_assign": (["re.X_NEW = 1"], line),
            "global": (["global X"], line),
            "before_docstring": (["X_NEW = 1"], 0),
            "cookie": (["# -*- coding: latin-1 -*-"], 0),
        }
        for name, (lines, after) in cases.items():
            with self.subTest(case=name):
                self.assertRegex(refused(insert(MODULE, after, lines, context=bool(after))),
                                 rf"^proposal_meaning:{re.escape(MODULE)}:\d+$")

    def test_an_addition_inside_old_code_is_named_at_its_line(self):  # proposal_in_body_unlocated
        text = read(MODULE).splitlines()
        body = next(i for i, x in enumerate(text, 1) if x.startswith("    return"))
        doc_end = next(i for i, x in enumerate(text, 1) if i > 1 and x.endswith('"""'))
        top = insert(MODULE, doc_end + 1, ["", "def early(x):", "    return x"], context=False)
        inner = insert(MODULE, body - 1, ["    return None"], context=False)
        hunk = inner[inner.index("@@"):].replace(f"+{body},1 @@", f"+{body + 3},1 @@")
        # The early def is inert; the return inside an old function is not, and is named at its own line.
        self.assertEqual(refused(top + hunk), f"proposal_meaning:{MODULE}:{body + 3}")

    def test_a_comment_line_inside_an_old_string_changes_the_string(self):  # proposal_old_ast_unchecked
        self.assertEqual(refused(insert(MODULE, 2, ["# not a comment: inside the docstring"])),
                         f"proposal_meaning:{MODULE}:3")

    def test_a_call_in_an_annotation_runs_where_annotations_are_not_lazy(self):  # proposal_call_in_annotation
        eager = ['"""x"""', "", "def f(x: print()) -> None:", "    return None", "", "", "def over(n):",
                 "    return n > 3"]
        self.assertRegex(refused(new_file(NEW_MODULE, eager) + new_file(NEW_TEST, TEST_LINES)), "^proposal_meaning")
        lazy = ['"""x"""', "", "from __future__ import annotations", "", "def f(x: print()) -> None:",
                "    return None", "", "", "def over(n):", "    return n > 3"]
        self.assertNotRegex(refused(new_file(NEW_MODULE, lazy) + new_file(NEW_TEST, TEST_LINES)), "^proposal_meaning")

    def test_a_new_test_file_changes_nothing_outside_itself(self):  # proposal_hook_allowed
        base = TEST_LINES[:7]
        leaks = {
            "hook": ["def setUpModule():", "    pass"],
            "aug": ["class T(unittest.TestCase):", "    def test_a(self):", "        mapcheck.LIMIT += 1"],
            "setattr": ["class T(unittest.TestCase):", "    def test_a(self):",
                        "        setattr(mapcheck, 'LIMIT', 0)"],
            "mutator": ["class T(unittest.TestCase):", "    def test_a(self):", "        unittest.defaultTestLoader"
                        ".testMethodPrefix.clear()"],
            "patcher": ["from unittest import mock", "class T(unittest.TestCase):", "    def test_a(self):",
                        "        mock.patch.object(mapcheck, 'LIMIT', 0).start()"],
            "global": ["class T(unittest.TestCase):", "    def test_a(self):", "        global LIMIT"],
            "main": ["if __name__ == '__main__':", "    unittest.main()"],
        }
        for name, extra in leaks.items():
            with self.subTest(case=name):
                patch = new_file(NEW_MODULE, MODULE_LINES) + new_file(NEW_TEST, base + extra + TEST_LINES[7:])
                self.assertRegex(refused(patch), rf"^proposal_meaning:{re.escape(NEW_TEST)}:\d+$")


class Reach(unittest.TestCase):
    """Added code reaches an allow-list (`29w` "Erişim", E600). Each case is a construction that passed the round-1
    blacklist and weakened or escaped the suite (the verifier of epoch L): it is now refused at its own line."""

    def body(self, *lines):
        test = TEST_LINES[:7] + ["class T(unittest.TestCase):", "    def test_a(self):"]
        test += ["        " + x for x in lines]
        return refused(new_file(NEW_MODULE, MODULE_LINES) + new_file(NEW_TEST, test + TEST_LINES[7:]))

    def top(self, *lines):
        return refused(new_file(NEW_MODULE, MODULE_LINES) + new_file(NEW_TEST, TEST_LINES[:7] + list(lines)
                                                                       + TEST_LINES[7:]))

    def test_what_a_test_body_may_not_name(self):  # proposal_reach_off proposal_banned_name_allowed
        cases = {
            "type": ("type.__setattr__(unittest.TestResult, 'wasSuccessful', lambda s: True)",),
            "result": ("unittest.TestResult.wasSuccessful",),  # proposal_member_unchecked
            "dunder": ("d = unittest.__dict__",),
            "open": ("open('x', 'w').write('1')",),
            "exit": ("raise SystemExit(0)",),
            "private": ("self._outcome.success = True",),  # proposal_private_attr_allowed
            "module_aug": ("mapcheck.LIMIT += 1",),  # proposal_module_change_allowed
            "module_call": ("mapcheck.over.__defaults__",),
            "nested_import": ("import os", "os.chdir('/')"),
            "dunder_method": ("class K:", "    def __del__(s):", "        return None"),
            "class_keyword": ("class K(T, x=1):", "    pass"),
            "attr_run": ("self.run()",),  # proposal_banned_attr_allowed
        }
        for name, lines in cases.items():
            with self.subTest(case=name):
                self.assertRegex(self.body(*lines), rf"^proposal_meaning:{re.escape(NEW_TEST)}:\d+$")

    def test_what_a_test_file_may_not_import(self):  # proposal_import_allowed proposal_effect_module_allowed
        for line in ("import os", "import shutil", "import subprocess", "import importlib", "import time",
                     "import antigravity", "import sys", "import unittest.mock", "from unittest import mock",
                     "from pathlib import Path", "from typing import get_type_hints",
                     "from snowball_bootstrap import gitio", "from snowball_bootstrap import cli",
                     "from snowball_bootstrap import rival", "from snowball_bootstrap.config import Path",
                     "from snowball_bootstrap.config import _load", "from helpers import sh",
                     "from test_decision import meta_", "import snowball_bootstrap",
                     "from snowball_bootstrap import *"):
            with self.subTest(line=line):
                self.assertRegex(self.top(line), rf"^proposal_meaning:{re.escape(NEW_TEST)}:\d+$")

    def test_a_member_must_be_one_the_module_offers(self):  # proposal_member_unchecked
        head = TEST_LINES[:5] + ["from snowball_bootstrap import config"] + TEST_LINES[5:]
        for line in ("x = config.Path('.')", "config.json.dumps(1)", "config._load", "config.CLAIM_RE = None"):
            with self.subTest(line=line):
                patch = new_file(NEW_MODULE, MODULE_LINES) + new_file(NEW_TEST, head + ["        " + line])
                self.assertRegex(refused(patch), rf"^proposal_meaning:{re.escape(NEW_TEST)}:12$")

    def test_appended_code_cannot_use_what_its_module_imported_from_off_the_list(self):  # proposal_blocked_alias_used
        end = len(read(MODULE).split("\n")) - 1
        self.assertTrue(re.search(r"^from pathlib import Path$", read(MODULE), re.M))
        self.assertEqual(refused(insert(MODULE, end, ["", "", "def leak(p):", "    return Path(p).read_text()"])),
                         f"proposal_meaning:{MODULE}:{end + 4}")

    def test_what_evidence_needs_is_in_reach(self):  # proposal_reach_too_tight
        lines = ['"""Evidence."""', "", "import json", "import unittest", "from collections import Counter", "",
                 "from snowball_bootstrap import claims, config, decide, mapcheck",
                 "from snowball_bootstrap.decide import decide as decide_fn", "", "",
                 "class Over(unittest.TestCase):", "    def test_over(self):", "        seen = {}",
                 "        seen['a'] = Counter([1, 1])",
                 "        self.assertTrue(mapcheck.over(4) and decide_fn and claims.BOOK)",
                 "        self.assertEqual(json.loads('[1]'), [1])",
                 "        self.assertTrue(config.HEX64_RE and decide)"]
        self.assertEqual(refused(new_file(NEW_MODULE, MODULE_LINES) + new_file(NEW_TEST, lines)), "candidate")


class Mutants(unittest.TestCase):
    def row(self, *rows):
        return insert(MUTATE, mutants_end(), list(rows))

    def test_rows_are_only_appended_new_and_anchored_once(self):  # proposal_anchor_twice_allowed
        good = '    ("x_new_row", f"{PKG}/decide.py", "RESULT_SCHEMA = ", "RESULT_SCHEMA = 1 or ", "w"),'
        self.assertEqual(refused(self.row(good)), "proposal_evidence:test_mapcheck.Over.test_over")  # rows pass
        cases = {
            '    ("x_twice", f"{PKG}/decide.py", "import", "x", "w"),': "proposal_anchor:x_twice",
            '    ("x_none", f"{PKG}/decide.py", "no such text anywhere", "x", "w"),': "proposal_anchor:x_none",
            '    ("outage_check_removed", f"{PKG}/decide.py", "RESULT_SCHEMA = ", "x", "w"),':
                f"proposal_meaning:{MUTATE}:{mutants_end() + 1}",  # proposal_mutant_name_reused
            '    ("x_same", f"{PKG}/decide.py", "RESULT_SCHEMA = ", "RESULT_SCHEMA = ", "w"),':
                f"proposal_meaning:{MUTATE}:{mutants_end() + 1}",
            '    ("x_short", f"{PKG}/decide.py", "RESULT_SCHEMA = "),':
                f"proposal_meaning:{MUTATE}:{mutants_end() + 1}",
            '    ("x_far", "seed/founder/nope.py", "import", "x", "w"),': "proposal_unread:seed/founder/nope.py",
        }
        for line, reason in cases.items():
            with self.subTest(reason=reason):
                self.assertEqual(refused(self.row(line)), reason)

    def test_nothing_but_rows_changes_in_mutate(self):  # proposal_mutant_row_changed
        self.assertRegex(refused(insert(MUTATE, mutants_end() + 1, ["", "EXTRA = 1"])), "^proposal_meaning")
        end = mutants_end()
        row = insert(MUTATE, end, ['    ("x_new_row", f"{PKG}/decide.py", "RESULT_SCHEMA = ", "R = ", "w"),'],
                     context=False)
        extra = insert(MUTATE, end + 1, ["", "EXTRA = 1"], context=False)
        both = row + extra[extra.index("@@"):].replace(f"+{end + 2},2 @@", f"+{end + 3},2 @@")
        self.assertRegex(refused(both), "^proposal_meaning")  # a row appended does not carry anything else
        mid = '    ("x_mid", f"{PKG}/decide.py", "RESULT_SCHEMA = ", "x", "w"),'
        self.assertRegex(refused(insert(MUTATE, 60, [mid])),
                         "^proposal_meaning")

    def test_an_old_rows_anchor_found_twice_is_a_mutant_that_no_longer_applies(self):  # proposal_old_anchor_unchecked
        patch = insert(PAGE, 41, ["- `self_map_unstable`: çıktı"])
        self.assertEqual(refused(patch), "proposal_anchor:self_map_page_drops_a_name")


class Hygiene(unittest.TestCase):
    def test_page_caps_and_identity(self):  # proposal_page_cap_off proposal_email_allowed
        cases = {
            insert(PAGE, 41, ["x"] * 40): f"proposal_page_cap:{PAGE}",
            insert(PAGE, 41, ["x" * 121]): f"proposal_page_cap:{PAGE}",
            insert(PAGE, 41, ["yaz: someone@example.org"]): "proposal_identity:email",
            insert(PAGE, 41, ["Co-Authored-By: x"]): "proposal_identity:trailer",
            insert(PAGE, 41, ["ghp_" + "a" * 36]): "proposal_identity:secret",
            insert(PAGE, 41, ["x"] * 2001): "proposal_too_large",
        }
        for patch, reason in cases.items():
            with self.subTest(reason=reason):
                self.assertEqual(refused(patch), reason)
        names = target_names((config.Target(id="t", repo="o/r", kind="copy", base_sha="c" * 40,
                                            identifiers=("Zorbalix",), excluded_paths=(), unit_candidates=()),))
        self.assertEqual(refused_with(insert(PAGE, 41, ["ZORBALIX burada"]), names), "proposal_identity:target_name")

    def test_the_evidence_is_a_test_the_patch_adds(self):  # proposal_evidence_unchecked
        patch = good_patch()
        for test_id in ("test_flow.Flow.test_x", "test_mapcheck.Over.test_none", "test_mapcheck.Nope.test_over", "x"):
            with self.subTest(test_id=test_id):
                self.assertEqual(refused(patch, evidence={"tests": [test_id]}), f"proposal_evidence:{test_id}")

    def test_the_base_is_the_delivered_seed(self):  # proposal_base_unchecked
        patch = good_patch()
        self.assertEqual(refused(patch, base=dict(BASE, bootstrap_sha256="4" * 64)), "proposal_base_unknown")
        with self.assertRaises(proposals.Refused):
            proposals.check(record(patch), patch.encode(), None, [], read)


class Runner(unittest.TestCase):
    """What runs, collects or reports the suite is never the Founder's to change (`29w` "Kanıt", E601): the existing
    tests and their helpers, `local/`'s scripts but `MUTANTS` rows, start-up hooks and `unittest`-named modules."""

    def test_what_runs_the_suite_is_refused_by_name(self):  # proposal_runner_open proposal_runner_local_open
        helpers = "seed/bootstrap/tests/helpers.py"
        flow = "seed/bootstrap/tests/test_flow.py"
        shard = "seed/bootstrap/local/unit_shard.py"
        cases = {
            insert(helpers, 1, ["# x"]): helpers,
            insert(flow, 1, ["# x"]): flow,
            insert(shard, 1, ["# x"]): shard,
            new_file("seed/bootstrap/local/run_more.py", ['"""x"""']): "seed/bootstrap/local/run_more.py",
            new_file("seed/bootstrap/tests/helpers2.py", ['"""x"""']): "seed/bootstrap/tests/helpers2.py",
            new_file("seed/bootstrap/tests/__init__.py", ['"""x"""']): "seed/bootstrap/tests/__init__.py",
            new_file("seed/bootstrap/tests/conftest.py", ['"""x"""']): "seed/bootstrap/tests/conftest.py",
            new_file("seed/bootstrap/tests/sub/test_x.py", ['"""x"""']): "seed/bootstrap/tests/sub/test_x.py",
            new_file(f"{proposals.PKG}sitecustomize.py", ['"""x"""']): f"{proposals.PKG}sitecustomize.py",
            new_file(f"{proposals.PKG}usercustomize.py", ['"""x"""']): f"{proposals.PKG}usercustomize.py",
            new_file(f"{proposals.PKG}unittest_extra.py", ['"""x"""']): f"{proposals.PKG}unittest_extra.py",
            new_file("seed/bootstrap/extra.pth", ["import os"]): "seed/bootstrap/extra.pth",
        }
        for patch, path in cases.items():
            with self.subTest(path=path):
                self.assertEqual(refused(patch), f"proposal_runner:{path}")
        self.assertFalse(proposals.runner(MUTATE, False))  # its rows are checked apart; the merge path runs the base's
        self.assertFalse(proposals.runner(NEW_TEST, True))


class TestCaseOwnRun(unittest.TestCase):
    """The verifier's constructions of epoch L round 2: a new test that owns its run or its result, or rebinds a shared
    object through an alias. Each is refused at its line; none could change the existing suite's verdict anyway
    (`MergePath`), because the existing suite never shares a process with a new test (E601)."""

    def refused_test(self, *lines):
        test = TEST_LINES[:7] + list(lines) + ["", "", "class Over(unittest.TestCase):", "    def test_over(self):",
                                               "        self.assertTrue(mapcheck.over(4))"]
        return refused(new_file(NEW_MODULE, MODULE_LINES) + new_file(NEW_TEST, test))

    def test_a_new_test_owns_neither_its_run_nor_its_result(self):  # proposal_testcase_override_allowed
        cases = {
            "run": ["class E(unittest.TestCase):", "    def run(self, result=None):", "        return None"],
            "run_stop": ["class E(unittest.TestCase):", "    def run(self, result=None):",
                         "        result.shouldStop = True"],
            "run_clear": ["class E(unittest.TestCase):", "    def run(self, result):", "        f = result.failures",
                          "        f.clear()"],
            "doCleanups": ["class E(unittest.TestCase):", "    def doCleanups(self):", "        return True"],
            "callTestMethod": ["class E(unittest.TestCase):", "    def _callTestMethod(self, method):",
                               "        return None"],
            "failureException": ["class E(unittest.TestCase):", "    failureException = KeyError"],
            "defaultTestResult": ["class E(unittest.TestCase):", "    def defaultTestResult(self):",
                                  "        return None"],
            "debug": ["class E(unittest.TestCase):", "    def debug(self):", "        return None"],
            "assertEqual": ["class E(unittest.TestCase):", "    def assertEqual(self, a, b, msg=None):",
                            "        return None"],
        }
        for name, lines in cases.items():
            with self.subTest(case=name):
                self.assertRegex(self.refused_test(*lines), rf"^proposal_meaning:{re.escape(NEW_TEST)}:\d+$")

    def test_no_attribute_store_but_on_its_own_instance(self):  # proposal_alias_store_allowed
        body = ["class E(unittest.TestCase):", "    def test_e(self):"]
        cases = {
            "alias_class": body + ["        t = unittest.TestCase", "        t.assertEqual = None"],
            "alias_module": body + ["        m = mapcheck", "        m.LIMIT = 9"],
            "alias_del": body + ["        m = mapcheck", "        del m.LIMIT"],
            "result_flag": ["class E(unittest.TestCase):", "    def test_e(self, result=None):",
                            "        result.shouldStop = True"],
            "own_member": body + ["        self.failureException = KeyError"],
            "plain_self": ["def poke(self):", "    self.LIMIT = 9"],
            "for_target": body + ["        m = mapcheck", "        for m.LIMIT in (1, 2):", "            pass"],
            "skip": body + ["        self.skipTest('green by skipping')"],  # proposal_skip_allowed
        }
        for name, lines in cases.items():
            with self.subTest(case=name):
                self.assertRegex(self.refused_test(*lines), rf"^proposal_meaning:{re.escape(NEW_TEST)}:\d+$")
        self.assertEqual(self.refused_test(*(body + ["        self.seen = {}", "        self.seen['a'] = 1"])),
                         "candidate")


class Bounds(unittest.TestCase):
    """A finding is bounded and no pattern scans a long line (E601)."""

    def test_a_reason_is_bounded_whatever_the_founder_wrote(self):  # proposal_reason_uncapped
        self.assertEqual(len(proposals.Refused("x" * 5000).reason), proposals.MAX_REASON)
        long_id = "test_mapcheck.Over.test_" + "a" * 5000
        self.assertEqual(len(refused(good_patch(), evidence={"tests": [long_id]})), proposals.MAX_REASON)

    def test_a_long_path_is_no_diff(self):  # proposal_path_uncapped
        path = "seed/bootstrap/tests/test_" + "a" * 300 + ".py"
        self.assertEqual(refused(new_file(path, ['"""x"""'])), "proposal_not_a_diff")

    def test_the_width_is_read_before_any_pattern(self):  # proposal_pattern_before_width
        line = "a@" + ".a" * 3000 + " someone@example.org"
        self.assertEqual(refused(insert(PAGE, 41, [line])), f"proposal_page_cap:{PAGE}")
        self.assertEqual(refused(insert(MODULE, len(read(MODULE).split("\n")) - 1, ["# " + "x" * 119])),
                         f"proposal_page_cap:{MODULE}")


class LineEndings(unittest.TestCase):
    """The referee's copy may be a Windows checkout with `core.autocrlf=true` (E601): its base reads as git holds it."""

    def test_committed_text_undoes_only_a_whole_crlf_checkout(self):  # proposal_base_crlf_kept
        self.assertEqual(proposals.committed_text(b"a\r\nb\r\n"), "a\nb\n")
        self.assertEqual(proposals.committed_text(b"a\r\nb\n"), "a\r\nb\n")  # mixed: not a conversion
        self.assertEqual(proposals.committed_text(b"a\rb\r\n"), "a\rb\r\n")  # a lone CR is content
        self.assertEqual(proposals.committed_text(b"a\nb\n"), "a\nb\n")
        self.assertIsNone(proposals.committed_text(b"\xff"))

    def test_a_crlf_copy_judges_like_a_linux_one(self):
        good = good_patch()
        with tempfile.TemporaryDirectory() as tmp:
            boot = Path(tmp) / "bootstrap"
            for rel in (MODULE, MUTATE, "seed/bootstrap/snowball_bootstrap/decide.py",
                        "seed/bootstrap/snowball_bootstrap/__init__.py"):
                target = boot / rel[len(proposals.BOOT_PREFIX):]
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(read(rel).encode("utf-8").replace(b"\n", b"\r\n"))
            files = {PAGE: read(PAGE).encode("utf-8").replace(b"\n", b"\r\n"),
                     "reports/p.json": json.dumps(dict(record(good), id="p")).encode(),
                     "reports/p.patch": good.encode()}
            with mock.patch.object(proposals, "BOOT", boot):
                rows = proposals.judge(tar_of(files), EPOCH, [])
        self.assertEqual((rows[0]["status"], rows[0]["reasons"]), ("candidate", []))


def refused_with(patch: str, names) -> str:
    try:
        check(patch, names=names)
    except proposals.Refused as found:
        return found.reason
    return "candidate"


def tar_of(files: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        for name, content in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))
    return buf.getvalue()


class Judge(unittest.TestCase):
    def tree(self, records: dict[str, tuple[dict, str]]) -> bytes:
        files = {PAGE: read(PAGE).encode()}
        for stem, (rec, patch) in records.items():
            files[f"reports/{stem}.json"] = json.dumps(dict(rec, id=stem)).encode()
            files[f"reports/{stem}.patch"] = patch.encode()
        return tar_of(files)

    def test_statuses(self):  # proposal_unread_rejected proposal_cap_ignored proposal_patch_hash_unchecked
        good = good_patch()
        records = {f"p{i}": (record(good), good) for i in range(4)}
        records["p0"] = (record(good, patch_sha256="0" * 64), good)
        records["p1"] = (record(good, state="withdrawn"), good)
        far = insert(MUTATE, mutants_end(), ['    ("x_far", "seed/founder/launch.py", "import", "x", "w"),'])
        records["p5"] = (record(far), far)
        records["p6"] = (record(good), good)
        rows = proposals.judge(self.tree(records), EPOCH, [])
        got = {r["id"]: (r["status"], r["reasons"]) for r in rows}
        self.assertEqual(got, {"p0": ("rejected", ["proposal_malformed"]), "p1": ("withdrawn", []),
                               "p2": ("candidate", []), "p3": ("candidate", []),
                               "p5": ("incomplete", ["proposal_unread:seed/founder/launch.py"]),
                               "p6": ("deferred", [])})
        self.assertEqual(rows[2]["patch_sha256"], hashlib.sha256(good.encode()).hexdigest())

    def test_a_check_that_breaks_is_incomplete_never_a_candidate(self):  # proposal_unchecked_is_candidate
        good = good_patch()
        orig = proposals.check
        try:
            proposals.check = lambda *a: (_ for _ in ()).throw(KeyError("x"))
            rows = proposals.judge(self.tree({"p": (record(good), good)}), EPOCH, [])
        finally:
            proposals.check = orig
        self.assertEqual((rows[0]["status"], rows[0]["reasons"]), ("incomplete", ["proposal_unchecked:KeyError"]))

    def test_a_proposal_is_never_a_reason(self):  # proposal_is_a_reason proposal_candidate_without_warning
        rows = [{"id": "p", "status": "candidate"}, {"id": "q", "status": "rejected", "reasons": ["proposal_meaning"]}]
        meta = meta_("spec", state0(), proposals=rows)
        res = decide(meta, None, not_refuted(), None, {"cagir": "success"}, 2, 3, now="2026-11-14T00:00:00Z")
        self.assertEqual((res["verdict"], res["reasons"]), ("frozen", []))
        self.assertEqual(res["proposals"], rows)
        self.assertIn("proposal_candidate:p", res["warnings"])
        self.assertNotIn("proposal_candidate:q", res["warnings"])
        code = decide(meta_("code", state0(), proposals=rows), green_run(), not_refuted(), [],
                      {"getir": "success", "kos": "success", "cagir": "success"}, 2, 3, now="2026-11-14T00:00:00Z")
        self.assertEqual(code["verdict"], "accepted")


class NoNameDispatch(unittest.TestCase):
    def test_the_package_reaches_no_function_by_its_name(self):  # proposal_dispatch_guard_off
        """Inert additions stay inert only while nothing in the package finds code by name (H2): no `globals()`,
        `vars()`, `__import__`, `eval`, `exec`, `__subclasses__`, `importlib`, and no `getattr` or `dir` over one of the
        package's own modules."""
        found = []
        for path in sorted((BOOT / "snowball_bootstrap").glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            own = {a.asname or a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.level
                   for a in n.names}
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    if node.func.id in ("globals", "vars", "__import__", "eval", "exec"):
                        found.append(f"{path.name}:{node.lineno}")
                    elif node.func.id in ("getattr", "dir") and node.args and isinstance(node.args[0], ast.Name) \
                            and node.args[0].id in own:
                        found.append(f"{path.name}:{node.lineno}")
                elif isinstance(node, ast.Attribute) and node.attr == "__subclasses__":
                    found.append(f"{path.name}:{node.lineno}")
                elif isinstance(node, (ast.Import, ast.ImportFrom)) and any(
                        a.name.split(".")[0] == "importlib" for a in node.names) | (
                        isinstance(node, ast.ImportFrom) and (node.module or "").startswith("importlib")):
                    found.append(f"{path.name}:{node.lineno}")
        self.assertEqual(found, [])


class PageAndPointers(unittest.TestCase):
    def page(self, prefix: str) -> str:
        return next((ROOT / "spec" / "tohum").glob(f"{prefix}-*.md")).read_text(encoding="utf-8")

    def test_29w_holds_the_closed_list_and_every_finding(self):  # proposals_page_drops_a_name proposal_closed_list_drift
        text = self.page("29w")
        listed = re.findall(r"`([^`]+)`", text[text.index("**Kapalı yüzey.**"):text.index("**Eklemeli**")])
        expected = [p.rsplit("/", 1)[-1] for p in proposals.CLOSED]
        self.assertEqual([x for x in listed if x in expected], expected)
        for name in proposals.NAMES + ("candidate", "incomplete", "deferred", "withdrawn", "proposal_candidate",
                                       "local/proposal_check.py"):
            with self.subTest(name=name):
                self.assertIn(f"`{name}", text)

    def test_the_pointers(self):  # proposals_pointer_00a_dropped proposals_pointer_09a_dropped
        self.assertIn("`29w`", self.page("00a"))
        self.assertIn("`29w`", self.page("09a"))
        self.assertIn("`29w`", self.page("29e"))
        self.assertIn("seed_proposal", self.page("26c"))


def load_proposal_check():
    spec = importlib.util.spec_from_file_location("proposal_check", BOOT / "local" / "proposal_check.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MergePath(unittest.TestCase):
    """`local/proposal_check.py` (`29w` "Kanıt ve inceleme", E600): the Founder's tests never run with the operator's
    environment, the base is HEAD as git holds it, and the evidence is red before and green after."""

    SEED = {
        "seed/bootstrap/snowball_bootstrap/__init__.py": "",
        "seed/bootstrap/snowball_bootstrap/limits.py": '"""Limits."""\n\nLIMIT = 3\n',
        "seed/bootstrap/tests/test_base.py": "import unittest\n\n\nclass B(unittest.TestCase):\n"
                                            "    def test_b(self):\n        self.assertTrue(True)\n",
        "seed/bootstrap/local/mutate.py": '"""Mutants."""\n\nPKG = "seed/bootstrap/snowball_bootstrap"\n'
                                          "MUTANTS = [\n]\n",
        "spec/tohum/a.md": "# A\n",
        "README.md": "readme\n",
    }

    def test_the_operators_environment_never_reaches_a_test(self):  # proposal_check_env_inherited
        pc = load_proposal_check()
        with mock.patch.dict(os.environ, {"PROBE_TOKEN": "secret", "GH_TOKEN": "t", "PATH": os.environ["PATH"]}):
            env = pc.scrubbed_env(Path("h"))
        self.assertNotIn("PROBE_TOKEN", env)
        self.assertNotIn("GH_TOKEN", env)
        self.assertLessEqual(set(env), set(pc.KEPT_ENV) | {"HOME", "USERPROFILE", "TMP", "TEMP", "TMPDIR",
                                                             "PYTHONPATH", "PYTHONDONTWRITEBYTECODE"})

    def test_a_proposal_pr_runs_every_mutant_before_a_merge(self):  # proposal_pr_mutation_off
        ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        plan = re.search(r"(?ms)^  mutation-plan:\n(.*?)(?=^    runs-on)", ci).group(1)
        self.assertIn("(github.event_name == 'pull_request' && startsWith(github.head_ref, 'proposal/'))", plan)
        self.assertIn("proposal/<id>", (ROOT / "spec" / "tohum" / "29w-tohum-teklifi.md").read_text(encoding="utf-8"))

    def test_a_run_needs_a_pinned_container_or_the_word_unsandboxed(self):  # proposal_check_image_unpinned
        pc = load_proposal_check()
        with self.assertRaises(SystemExit), mock.patch("sys.stderr", io.StringIO()):
            pc.main(["--record", "r", "--patch", "p"])
        with mock.patch("sys.stderr", io.StringIO()):
            self.assertEqual(pc.main(["--record", "r", "--patch", "p", "--image", "python:3.12"]), 2)
        argv = []
        fake = pc.docker_runner("img@sha256:" + "a" * 64, Path("e"))
        with mock.patch("subprocess.run", lambda a, **k: argv.append(a) or subprocess.CompletedProcess(a, 0, b"", b"")):
            self.assertEqual(fake(Path("t"), ["-m", "unittest", "x"]), 0)
        self.assertIn("--network", argv[0])
        self.assertEqual(argv[0][argv[0].index("--network") + 1], "none")
        self.assertNotIn("PROBE", " ".join(argv[0]))

    def test_the_evidence_runs_on_heads_files_red_before_green_after(self):  # proposal_check_working_tree
        pc = load_proposal_check()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "seed"
            make_repo(repo, self.SEED)
            (repo / "seed/bootstrap/snowball_bootstrap/limits.py").write_text("LIMIT = 'dirty'\n", encoding="utf-8")
            tar = pc.committed(repo)
            base = pc.Base(tar)
            module = ['"""Over."""', "", "", "def over(n):", "    return n > 3"]
            test = ['"""Evidence."""', "", "import unittest", "", "from snowball_bootstrap import limits, over", "",
                    "", "class Over(unittest.TestCase):", "    def test_over(self):",
                    "        self.assertTrue(over.over(4) and limits.LIMIT == 3)"]
            patch = (new_file("seed/bootstrap/snowball_bootstrap/over.py", module)
                     + new_file("seed/bootstrap/tests/test_over.py", test))
            rec = record(patch, base={"spec_tohum_sha256": base.spec_tohum_sha256,
                                      "bootstrap_sha256": base.bootstrap_sha256},
                         evidence={"tests": ["test_over.Over.test_over"]})
            work = Path(tmp) / "work"
            (work / "home").mkdir(parents=True)
            run = pc.local_runner(work / "home")
            review, found = pc.check(repo, rec, patch.encode(), run, False, work)
            # Green after on HEAD's LIMIT = 3: the dirty working tree's 'dirty' never ran.
            self.assertEqual(found, {"existing": [], "evidence": []})
            self.assertEqual(review, ["new_module:seed/bootstrap/snowball_bootstrap/over.py",
                                      "tests:seed/bootstrap/tests/test_over.py"])
            green = test[:4] + ["from snowball_bootstrap import limits"] + test[5:-1] + [
                "        self.assertTrue(limits.LIMIT == 3)"]
            patch2 = new_file("seed/bootstrap/tests/test_over.py", green)
            rec2 = dict(rec, patch_sha256=hashlib.sha256(patch2.encode()).hexdigest())
            work2 = Path(tmp) / "work2"
            (work2 / "home").mkdir(parents=True)
            self.assertEqual(pc.check(repo, rec2, patch2.encode(), pc.local_runner(work2 / "home"), False, work2)[1],
                             {"existing": [], "evidence": ["proposal_evidence_not_red:test_over.Over.test_over"]})
            # proposal_check_not_red

    # The verifier's constructions (epoch L, round 2), each a new test that would hide a red existing test when it
    # shares the suite's process: they run here past the static check (which refuses each, `TestCaseOwnRun`).
    ATTACKS = {
        "addFailure": ["class Aaa(unittest.TestCase):", "    def run(self, result=None):",
                       "        result.addFailure = lambda *a: None", "        result.addError = lambda *a: None",
                       "        return super().run(result)", "    def test_aaa(self):", "        pass"],
        "failures_clear": ["class Aaa(unittest.TestCase):", "    def run(self, result=None):",
                           "        stop = result.stopTestRun", "        def clear():",
                           "            f = result.failures", "            f.clear()", "            e = result.errors",
                           "            e.clear()", "            stop()", "        result.stopTestRun = clear",
                           "        return super().run(result)",
                           "    def test_aaa(self):", "        pass"],
        "shouldStop": ["class Aaa(unittest.TestCase):", "    def run(self, result=None):",
                       "        result.startTest(self)", "        result.addSuccess(self)",
                       "        result.stopTest(self)",
                       "        result.shouldStop = True", "        return result", "    def test_aaa(self):",
                       "        pass"],
        "alias": ["class Aaa(unittest.TestCase):", "    def test_aaa(self):", "        t = unittest.TestCase",
                  "        t.assertEqual = lambda *a, **k: None"],
    }
    RED = {"seed/bootstrap/tests/test_page.py": "import unittest\nfrom pathlib import Path\n\n\n"
                                                "class Page(unittest.TestCase):\n    def test_one_line(self):\n"
                                                "        page = Path('../../spec/tohum/a.md').read_text()\n"
                                                "        self.assertEqual(len(page.splitlines()), 1)\n"}

    def merge_run(self, tmp: Path, test_lines: list[str]):
        """The merge path's `--full` run of a patch that turns the base's page test red, with a new test beside it,
        past the static check: the two verdicts, and what the old single-process run said of the same tree."""
        pc = load_proposal_check()
        repo = tmp / "seed"
        make_repo(repo, {**self.SEED, **self.RED})
        patch = (insert_text("spec/tohum/a.md", "# A\n", ["ek"])
                 + new_file("seed/bootstrap/tests/test_aaa.py", ["import unittest", "", ""] + test_lines))
        rec = record(patch, evidence={"tests": ["test_aaa.Aaa.test_aaa"]})
        work = tmp / "work"
        (work / "home").mkdir(parents=True)
        run = pc.local_runner(work / "home")
        with mock.patch.object(pc.proposals, "check", lambda *a: []):
            verdicts = pc.check(repo, rec, patch.encode(), run, True, work)[1]
        return verdicts, run(work / "after", pc.SUITE)

    def test_a_new_test_never_shares_the_existing_suites_process(self):  # proposal_check_suite_with_new_tests
        for name, lines in self.ATTACKS.items():
            with self.subTest(attack=name), tempfile.TemporaryDirectory() as tmp:
                verdicts, together = self.merge_run(Path(tmp), lines)
                self.assertEqual(verdicts["existing"], ["proposal_suite_red"])
                self.assertEqual(together, 0)  # in the suite's process each one hides the red page test
        with tempfile.TemporaryDirectory() as tmp:  # the control: nothing to hide, the same red
            verdicts, together = self.merge_run(Path(tmp), ["class Aaa(unittest.TestCase):",
                                                            "    def test_aaa(self):", "        pass"])
            self.assertEqual((verdicts["existing"], together != 0), (["proposal_suite_red"], True))

    def test_the_existing_tree_is_the_bases_suite_or_nothing_runs(self):  # proposal_check_isolation_guard_off
        pc = load_proposal_check()  # proposal_check_overlay_unchecked
        files = {p: t.encode() for p, t in self.SEED.items()}
        with tempfile.TemporaryDirectory() as tmp:
            root = pc.tree(files, {}, Path(tmp) / "t")
            pc.assert_isolated(files, root)
            (root / "seed/bootstrap/tests/test_new.py").write_text("x = 1\n", encoding="utf-8")
            with self.assertRaises(pc.Isolation):
                pc.assert_isolated(files, root)
            (root / "seed/bootstrap/tests/test_new.py").unlink()
            (root / "seed/bootstrap/local/mutate.py").write_text("MUTANTS = [\n]\n", encoding="utf-8")
            with self.assertRaises(pc.Isolation):
                pc.assert_isolated(files, root)
            pc.tree(files, {}, root)
            (root / "seed/bootstrap/sitecustomize.py").write_text("x = 1\n", encoding="utf-8")
            with self.assertRaises(pc.Isolation):
                pc.assert_isolated(files, root)
        with self.assertRaises(pc.Isolation):
            pc.existing_overlay(files, {"seed/bootstrap/tests/helpers.py": ("x", "code")})
        self.assertEqual(pc.existing_overlay(files, {"spec/tohum/a.md": ("x", "code"), NEW_TEST: ("t", "test"),
                                                     MUTATE: ("m", "mutants")}), {"spec/tohum/a.md": "x"})

    def test_the_bases_mutants_of_a_touched_file_run_on_the_existing_tree(self):  # proposal_touched_mutants_skipped
        pc = load_proposal_check()  # proposal_mutant_rows_untouched
        mutate = ('"""Mutants."""\n\nPKG = "seed/bootstrap/snowball_bootstrap"\nMUTANTS = [\n'
                  '    ("a_title", "spec/tohum/a.md", "# A", "# B", "w"),\n'
                  '    ("limit", f"{PKG}/limits.py", "LIMIT = 3", "LIMIT = 4", "w"),\n]\n')
        self.assertEqual(proposals.mutant_names_in(mutate, {"spec/tohum/a.md"}), ["a_title"])
        calls = []

        def run(root, args):
            calls.append(args)
            return 1 if args[0] == "local/mutate.py" else 0
        self.assertEqual(pc.existing_suite(run, Path("t"), mutate, ["spec/tohum/a.md"]), ["proposal_mutant_survived"])
        self.assertEqual(calls, [pc.SUITE, ["local/mutate.py", "--only", "a_title"]])
        calls.clear()
        self.assertEqual(pc.existing_suite(run, Path("t"), mutate, ["spec/tohum/b.md"]), [])
        self.assertEqual(calls, [pc.SUITE])

    def test_ci_puts_the_bases_suite_back_on_a_proposal_pr(self):  # proposal_ci_isolate_keeps_new_tests
        pc = load_proposal_check()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "seed"
            base = make_repo(repo, self.SEED)
            commit(repo, {"seed/bootstrap/tests/test_new.py": "import unittest\n", "spec/tohum/a.md": "# A\nek\n",
                          "seed/bootstrap/local/mutate.py": self.SEED["seed/bootstrap/local/mutate.py"] + "# row\n"},
                   "proposal")
            self.assertEqual(pc.added_tests(repo, base), ["test_new"])
            self.assertEqual(pc.isolate(repo, base), [])
            self.assertFalse((repo / "seed/bootstrap/tests/test_new.py").exists())
            self.assertEqual((repo / "seed/bootstrap/local/mutate.py").read_text(encoding="utf-8"),
                             self.SEED["seed/bootstrap/local/mutate.py"])
            self.assertEqual((repo / "spec/tohum/a.md").read_text(encoding="utf-8"), "# A\nek\n")  # the code stays
            commit(repo, {"seed/bootstrap/tests/test_base.py": "x = 1\n", "seed/bootstrap/conftest.py": "x = 1\n"},
                   "worse")
            self.assertEqual(pc.isolate(repo, base), ["seed/bootstrap/conftest.py",
                                                      "changed:seed/bootstrap/tests/test_base.py"])
        ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")  # proposal_ci_isolate_off
        for job, runs in (("unit-linux", "Referee unit tests"), ("unit-windows", "Referee unit tests"),
                          ("mutation", "Referee mutants")):
            with self.subTest(job=job):
                body = re.search(rf"(?ms)^  {job}:\n(.*?)(?=^  \S|\Z)", ci).group(1)
                step = re.search(r"(?ms)      - name: A proposal PR runs the base's tests.*?run: (python3?) "
                                 r"local/proposal_check\.py --isolate HEAD\^1\n", body)
                self.assertIsNotNone(step)
                self.assertIn("if: github.event_name == 'pull_request' && startsWith(github.head_ref, 'proposal/')",
                              step.group(0))
                self.assertLess(step.start(), body.index(f"- name: {runs}"))
                self.assertIn("fetch-depth: 2", body)
        evidence = re.search(r"(?ms)^  proposal-evidence:\n(.*?)(?=^  \S|\Z)", ci).group(1)
        self.assertIn("python3 local/proposal_check.py --added-tests HEAD^1", evidence)
        self.assertIn('python3 -m unittest "$module"', evidence)


if __name__ == "__main__":
    unittest.main()
