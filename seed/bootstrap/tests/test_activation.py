"""The operator's activation tools (`tohum/25a` 1, 2 and 9; `asama-0/10a` #aktarim, #oyuncak, "Kilidin açılışı"; `26c`):
the import (K1 of `seed/founder/ETKINLESTIRME.md`: E100, E275, E370, E374), `stage-open`, the stage lock the bootstrap
reads on every pull, and Stage 1's batch tables, batch exit and batch transfer (K3: E331, E371-E373, E375-E379, E388).

Nothing here signs or verifies with Sigstore: the seed's one call into it (`importer.verify_signature`) is replaced by a
recorder, as `test_flow` and `test_exit_checks` do. Every git repository is a local one. The trailing comment on a test
names the mutants it kills (`local/mutate.py`).
"""

import base64
import contextlib
import ctypes
import hashlib
import json
import os
import re
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from snowball_bootstrap import canon, cli, config, gitio, importer, manifest as manifest_module, stagelock, stages, wiring
from snowball_bootstrap.canon import canonical, row_hash
from snowball_bootstrap.config import ConfigError
from snowball_bootstrap.container import RunResult
from snowball_bootstrap.decide import decide
from snowball_bootstrap.importer import ImportErrorStop, run_import
from snowball_bootstrap.manifest import check_stage, parse_manifest
from snowball_bootstrap.treehash import tree_hash

import test_exit_checks
from helpers import LOOP_YML, FakeRunner, commit, make_repo, posix_only, sh
from test_exit_checks import tar_of

BOOT = Path(__file__).resolve().parents[1]
ROOT = BOOT.parents[1]
ZERO = "0" * 64
TOY_DIR = "tests/fixtures/toy-repo"
BRAIN_FILES = {
    "referee/ledger/chain.py": "x = 1\n",
    "referee/gate/check.py": "y = 2\n",
    "referee/.github/workflows/loop.yml": LOOP_YML,
    f"{TOY_DIR}/app.py": "import os\n",
    f"{TOY_DIR}/README.md": "toy\n",
    "spec/tohum/00-cekirdek.md": "# core\n",
}
# What `import` must keep exactly as it found it (`25a` 1): the operator's files, the bootstrap referee and its workflow.
OPERATOR_FILES = {
    "policy.json": "{}\n",
    "bootstrap.json": "{}\n",
    "setup/summary.json": "{}\n",
    "seats/29-tohum-koltuklari.md": "seat\n",
    "vectors/vectors.json": "{}\n",
    "bootstrap/snowball_bootstrap/__init__.py": "seed\n",
    "bootstrap/workflow/bootstrap.yml": "name: copy\n",
    ".github/workflows/bootstrap.yml": "name: snowball-bootstrap\n",
}
IMPORT_KEYS = ["ts", "stage", "brain_sha", "referee_tree_sha256", "result_sha256", "toy_tree_sha256", "prev_hash",
               "row_hash"]
BATCH_KEYS = ["ts", "stage", "batch", "brain_sha", "referee_tree_sha256", "result_sha256", "prev_hash", "row_hash"]
DROP = object()  # a field a fixture leaves out


def write(root, files):
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))


def read_all(root, skip=(".git",)):
    """Every file under ``root`` as {posix path: bytes}, ``skip`` top names left out."""
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*"))
            if p.is_file() and p.relative_to(root).parts[0] not in skip}


def chained(rows):
    """``rows`` (dicts without the chain fields) chained with the seed's canonical code, as JSONL bytes (`26`)."""
    out, prev = [], ZERO
    for row in rows:
        row = dict(row, prev_hash=prev)
        row["row_hash"] = row_hash(row)
        prev = row["row_hash"]
        out.append(row)
    return out, b"".join(json.dumps(r, separators=(",", ":")).encode("utf-8") + b"\n" for r in out)


def edited(base, over):
    """``base`` with ``over`` applied; a value ``DROP`` removes its key."""
    out = dict(base)
    for key, value in (over or {}).items():
        if value is DROP:
            out.pop(key, None)
        else:
            out[key] = value
    return out


def lock_of(line, **over):
    """A well-formed lock naming the counter line ``line``."""
    return dict({"stage": 1, "pass_row_sha256": "1" * 64, "toy_state_head": "2" * 40, "copy_state_head": "3" * 40,
                 "import_line_sha256": hashlib.sha256(line).hexdigest()}, **over)


def locked(root, brain_sha="4" * 40, batches=()):
    """Stage 0's transfer, the lock naming it and a transfer row for each of ``batches`` after it, under ``root``;
    the counter's rows."""
    rows, data = chained([{"ts": "2026-10-31T08:00:00Z", "stage": 0, "brain_sha": brain_sha,
                           "referee_tree_sha256": "d" * 64, "result_sha256": "e" * 64, "toy_tree_sha256": "f" * 64}] +
                         [{"ts": "2026-11-02T08:00:00Z", "stage": 1, "batch": b, "brain_sha": "5" * 40,
                           "referee_tree_sha256": "6" * 64, "result_sha256": "7" * 64} for b in batches])
    write(root, {"setup/imports.jsonl": data, "setup/stage.json": json.dumps(lock_of(data.split(b"\n")[0]))})
    return rows


class ImportCase(unittest.TestCase):
    """A brain with a referee tree and a toy, the signed result of its (A) and an operator's referee and toy checkout."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name)
        self.brain = self.work / "brain"
        make_repo(self.brain, {"README.md": "brain\n"})
        write(self.brain, BRAIN_FILES)
        self.sha = commit(self.brain, {}, "referee and toy")
        tar = gitio.archive(self.brain, self.sha)
        self.referee_hash = tree_hash(tar, "referee")
        self.toy_hash = tree_hash(tar, TOY_DIR, forbid_operator_names=False, fold_case=True)
        self.result = self.work / "result.json"
        self.write_result()
        self.bundle = self.work / "result.json.sigstore.json"
        self.bundle.write_text("{}")
        self.referee = self.work / "referee"
        write(self.referee, OPERATOR_FILES)
        write(self.referee, {"control.json": '{"kill_switch": true, "budget_state": "ok"}\n'})
        self.toy = self.work / "toy"
        self.toy.mkdir()
        self.verified = []
        patcher = mock.patch.object(importer, "verify_signature",
                                    side_effect=lambda *a: self.verified.append(a))
        patcher.start()
        self.addCleanup(patcher.stop)

    def write_result(self, **exit_fields):
        exit_block = {"transferable": True, "brain_sha": self.sha, "referee_tree_sha256": self.referee_hash,
                      "toy_tree_sha256": self.toy_hash, "repeat_events": 0}
        exit_block.update(exit_fields)
        self.result.write_bytes(json.dumps({"kind": "exit", "verdict": "accepted", "head": self.sha,
                                            "exit": exit_block}, indent=2).encode("utf-8") + b"\n")

    def use_tree(self, files):
        """The brain's archive replaced by a stand-in holding ``files`` (a patch to enter), with the signed result
        naming its hashes."""
        tar = tar_of(files)
        self.referee_hash, self.toy_hash = tree_hash(tar, "referee"), tree_hash(tar, TOY_DIR, False, True)
        self.write_result()
        return mock.patch.object(importer.gitio, "archive", return_value=tar)

    def run_import(self, toy=True):
        return run_import(self.result, self.bundle, "id", "py", self.brain, self.referee, self.toy if toy else None)

    def imports(self):
        path = self.referee / "setup" / "imports.jsonl"
        return path.read_bytes() if path.exists() else b""


class ImportKeepsTheBootstrapTest(ImportCase):
    def test_the_bootstrap_its_workflow_and_the_operator_files_stay_as_they_were(self):
        """E100, `25a` 1, `asama-0/10a` #aktarim: the push judge stays; `loop.yml` lands beside `bootstrap.yml`."""
        before = read_all(self.referee)
        self.run_import()
        after = read_all(self.referee)
        for rel, content in before.items():
            self.assertEqual(after.get(rel), content, rel)
        self.assertEqual(after[".github/workflows/loop.yml"], LOOP_YML.encode("utf-8"))
        self.assertEqual(after["ledger/chain.py"], b"x = 1\n")
        self.assertEqual(sorted(set(after) - set(before)),
                         [".github/workflows/loop.yml", "gate/check.py", "ledger/chain.py", "setup/imports.jsonl"])
        self.assertEqual(read_all(self.toy), {"README.md": b"toy\n", "app.py": b"import os\n"})

    def test_a_second_import_leaves_no_file_of_the_first_referee_tree(self):
        """`ETKINLESTIRME` 3: every referee file is the signed commit's `referee/` blob; the bootstrap still stays."""
        self.run_import()
        commit(self.brain, {"referee/gate/check.py": None, "referee/gate/other.py": "z = 3\n"}, "next batch")
        self.sha = sh(self.brain, "git", "rev-parse", "HEAD")
        self.referee_hash = tree_hash(gitio.archive(self.brain, self.sha), "referee")
        self.write_result()
        self.run_import()
        after = read_all(self.referee)
        self.assertNotIn("gate/check.py", after)
        self.assertEqual(after["gate/other.py"], b"z = 3\n")
        self.assertEqual(after[".github/workflows/bootstrap.yml"], b"name: snowball-bootstrap\n")
        self.assertEqual(after["bootstrap/snowball_bootstrap/__init__.py"], b"seed\n")

    def test_github_is_cleared_around_the_bootstraps_workflow(self):  # SK_github_not_descended
        """E389: `.github/` holds `bootstrap.yml`, so the clearing goes down into it: an earlier tree's workflow, or any
        other file there, does not survive the import to run beside the push judge."""
        write(self.referee, {".github/workflows/old.yml": "name: stale\n", ".github/CODEOWNERS": "* @x\n"})
        self.run_import()
        after = read_all(self.referee)
        self.assertNotIn(".github/workflows/old.yml", after)
        self.assertNotIn(".github/CODEOWNERS", after)
        self.assertEqual(after[".github/workflows/bootstrap.yml"], b"name: snowball-bootstrap\n")

    def test_a_referee_tree_that_carries_the_bootstraps_workflow_is_refused(self):
        """`25a` 1: the import never touches `bootstrap.yml`, in any spelling (E130, E289: the operator's file system
        folds case): nothing is written. (A)'s wiring check refuses such a tree first (`workflow_extra_file`); the
        import does not lean on it. The brain's archive is a stand-in, so no file system folds it before the check."""
        for name in (".github/workflows/bootstrap.yml", ".GitHub/Workflows/BOOTSTRAP.yml"):  # import_overwrites_bootstrap_yml import_kept_case_sensitive
            with self.subTest(name=name):
                tar = tar_of({"referee/a.py": "x\n", f"referee/{name}": "name: evil\n", f"{TOY_DIR}/app.py": "y\n"})
                self.referee_hash, self.toy_hash = tree_hash(tar, "referee"), tree_hash(tar, TOY_DIR, False, True)
                self.write_result()
                before = read_all(self.referee)
                with mock.patch.object(importer.gitio, "archive", return_value=tar), \
                        self.assertRaises(ImportErrorStop) as caught:
                    self.run_import()
                self.assertIn("would land on what the import keeps", str(caught.exception))
                self.assertEqual(read_all(self.referee), before)
                self.assertEqual(read_all(self.toy), {})

    def test_the_checkout_is_hashed_again_before_the_row_is_written(self):  # import_checkout_not_rehashed
        """`25a` 1: the referee checkout, what the import keeps left out, is the signed tree once the files are in
        place; a checkout that is not (here: a file the clearing left behind) gets no counter row."""
        write(self.referee, {"old/stale.py": "from an earlier tree\n"})
        with mock.patch.object(importer, "_clear"), self.assertRaises(ImportErrorStop) as caught:
            self.run_import()
        self.assertIn("checkout on disk", str(caught.exception))
        self.assertEqual(self.imports(), b"")


class ImportTheToyTest(ImportCase):
    """`25a` 2, `asama-0/10a` #oyuncak: the toy checkout becomes the signed toy subtree, nothing else (E389)."""

    def test_an_earlier_toy_file_is_cleared_and_the_git_directory_kept(self):  # SK_toy_not_cleared
        write(self.toy, {"stale.py": "from an earlier toy\n", "old/x.txt": "x\n", ".git/HEAD": "ref: refs/heads/main\n"})
        self.run_import()
        self.assertEqual(read_all(self.toy), {"README.md": b"toy\n", "app.py": b"import os\n"})
        self.assertEqual((self.toy / ".git" / "HEAD").read_bytes(), b"ref: refs/heads/main\n")

    def test_the_toy_checkout_is_hashed_again_before_the_row_is_written(self):  # SK_toy_final_rehash_off
        """A toy checkout that is not the signed toy tree once the files are in place (here: the clearing of the toy
        left a file behind) gets no counter row."""
        write(self.toy, {"stale.py": "from an earlier toy\n"})
        real = importer._clear

        def referee_only(directory, keep, holds, rel=importer.PurePosixPath()):
            if Path(directory) != self.toy:
                real(directory, keep, holds, rel)
        with mock.patch.object(importer, "_clear", side_effect=referee_only), \
                self.assertRaises(ImportErrorStop) as caught:
            self.run_import()
        self.assertIn("toy checkout on disk", str(caught.exception))
        self.assertEqual(self.imports(), b"")


class ImportRowTest(ImportCase):
    def test_the_row_is_26cs_chained_and_its_line_is_what_genesis_binds(self):
        """E275: `{ts, stage, brain_sha, referee_tree_sha256, result_sha256, toy_tree_sha256}` chained (`26`), one line
        of compact JSON in that order, LF only (`29o` hashes the line without its LF); a second import chains on."""
        first = self.run_import()
        lines = self.imports().split(b"\n")
        self.assertEqual(lines[-1], b"")
        row = json.loads(lines[0])
        self.assertEqual(list(row), IMPORT_KEYS)
        self.assertEqual(lines[0], json.dumps(row, separators=(",", ":")).encode("ascii"))
        self.assertNotIn(b"\r", self.imports())
        self.assertEqual((row["stage"], row["brain_sha"], row["referee_tree_sha256"], row["toy_tree_sha256"]),
                         (0, self.sha, self.referee_hash, self.toy_hash))
        self.assertEqual(row["result_sha256"], hashlib.sha256(self.result.read_bytes()).hexdigest())
        self.assertRegex(row["ts"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z")
        self.assertEqual((row["prev_hash"], row["row_hash"]), (ZERO, row_hash(row)))
        self.assertEqual(first, row)
        second = self.run_import()
        rows = [json.loads(line) for line in self.imports().splitlines()]
        self.assertEqual(rows, [row, second])
        self.assertEqual((second["prev_hash"], second["row_hash"]), (row["row_hash"], row_hash(second)))

    def test_a_counter_whose_chain_is_broken_is_not_appended_to(self):  # import_appends_to_a_broken_counter
        _rows, data = chained([{"ts": "2026-10-30T12:00:00Z", "stage": 0}])
        _rows, other = chained([{"ts": "2026-10-30T13:00:00Z", "stage": 0}])
        for broken in (data.replace(b'"stage":0', b'"stage":1'), data[:-1], b"not json\n", data + b"\n",
                       data.replace(b"\n", b"\r\n"), data + other,  # the second row does not link to the first
                       data.replace(b'"stage":0', b'"stage":0,"stage":0')):  # a key twice hides one value
            # import_counter_hash_unchecked import_counter_link_unchecked import_counter_cr_allowed
            with self.subTest(broken=broken[:40]):
                write(self.referee, {"setup/imports.jsonl": broken})
                with self.assertRaises(ConfigError):
                    self.run_import()
                self.assertEqual(self.imports(), broken)
                self.assertFalse((self.referee / "ledger").exists())

    def test_a_non_transfer_touch_row_of_the_counter_is_chained_on(self):
        """`29n`, E277: the counter holds touches that are no transfer; the next row chains on its hash."""
        rows, data = chained([{"ts": "2026-10-30T12:00:00Z", "stage": 0}])
        write(self.referee, {"setup/imports.jsonl": data})
        row = self.run_import()
        self.assertEqual(row["prev_hash"], rows[0]["row_hash"])


class ImportRefusesTest(ImportCase):
    def assert_nothing_written(self, before):
        self.assertEqual(read_all(self.referee), before)
        self.assertEqual(read_all(self.toy), {})

    def test_the_kill_switch_must_be_on(self):  # import_without_kill_switch
        """`25a` 1, `asama-0/10a` #aktarim: "Kill switch açık değilse çalışmaz". On means exactly true here (spec
        sessiz, E370): the import's most restrictive reading of `26c`'s fail-closed rule is not to run."""
        for control in ('{"kill_switch": false, "budget_state": "ok"}\n', '{"budget_state": "ok"}\n',
                        '{"kill_switch": "true"}\n', '{"kill_switch": 1}\n', "[true]\n", "not json\n", None):
            with self.subTest(control=control):
                path = self.referee / "control.json"
                if control is None:
                    path.unlink(missing_ok=True)
                else:
                    path.write_text(control, encoding="utf-8", newline="\n")
                before = read_all(self.referee)
                with self.assertRaises(ImportErrorStop) as caught:
                    self.run_import()
                self.assertIn("kill switch", str(caught.exception))
                self.assertEqual(self.verified, [])  # checked first, before anything else
                self.assert_nothing_written(before)

    def test_the_cli_stops_with_exit_2_when_the_kill_switch_is_off(self):
        (self.referee / "control.json").write_text('{"kill_switch": false}\n', encoding="utf-8")
        argv = ["import", "--result", str(self.result), "--bundle", str(self.bundle), "--identity", "id",
                "--sigstore-python", "py", "--brain", str(self.brain), "--referee", str(self.referee),
                "--toy", str(self.toy)]
        self.assertEqual(cli.main(argv), 2)
        self.assertEqual(self.imports(), b"")

    def test_the_disk_tree_is_hashed_again_before_anything_is_written(self):  # import_disk_not_rehashed
        """`25a` 1: opened into a sibling temporary directory first, hashed there as it lies on disk; a tree the file
        system changed (here: an extraction that adds a file) stops the import before the checkouts are touched."""
        real = importer.extract

        def extract_and_add(tar_bytes, dest, max_bytes, prefix=""):
            total = real(tar_bytes, dest, max_bytes, prefix)
            if prefix == "referee":
                (dest / "ledger" / "extra.py").write_text("planted\n")
            return total
        before = read_all(self.referee)
        with mock.patch.object(importer, "extract", side_effect=extract_and_add), \
                self.assertRaises(ImportErrorStop) as caught:
            self.run_import()
        self.assertIn("on disk", str(caught.exception))
        self.assert_nothing_written(before)
        self.assertEqual([p.name for p in self.work.iterdir() if p.name.startswith(".snowball-import")], [])

    @posix_only
    def test_a_link_or_a_special_file_on_disk_is_never_hashed_through(self):  # SK_disk_links_allowed
        """E389: what lies on disk is hashed as regular files only; a link (to a file or a directory) or a FIFO the
        extraction left stops the import before the checkouts are touched, whatever it points at."""
        real = importer.extract
        for plant in ("file_link", "dir_link", "fifo"):
            def extract_and_plant(tar_bytes, dest, max_bytes, prefix="", plant=plant):
                total = real(tar_bytes, dest, max_bytes, prefix)
                if prefix == "referee":
                    target = dest / "ledger" / "chain.py"
                    if plant == "file_link":
                        os.symlink(target, dest / "gate" / "linked.py")
                    elif plant == "dir_link":
                        os.symlink(dest / "ledger", dest / "linked")
                    else:
                        os.mkfifo(dest / "gate" / "pipe")
                return total
            with self.subTest(plant=plant):
                before = read_all(self.referee)
                with mock.patch.object(importer, "extract", side_effect=extract_and_plant), \
                        self.assertRaises(ImportErrorStop) as caught:
                    self.run_import()
                self.assertRegex(str(caught.exception), "is a link|not a regular file")
                self.assert_nothing_written(before)

    def test_the_temporary_tree_is_a_sibling_of_the_referee_checkout(self):  # import_temp_not_sibling
        seen = []
        real = importer.extract

        def record(tar_bytes, dest, max_bytes, prefix=""):
            seen.append(Path(dest).parent.resolve())
            return real(tar_bytes, dest, max_bytes, prefix)
        with mock.patch.object(importer, "extract", side_effect=record):
            self.run_import()
        self.assertTrue(seen)
        for parent in seen:
            self.assertEqual(parent, self.referee.parent.resolve())

    def test_the_toy_tree_must_be_the_signed_toy_tree(self):  # import_toy_hash_unchecked
        """`25a` 2, `asama-0/10a` #oyuncak (E131): its hash is the signed result's `toy_tree_sha256`."""
        self.write_result(toy_tree_sha256="1" * 64)
        before = read_all(self.referee)
        with self.assertRaises(ImportErrorStop) as caught:
            self.run_import()
        self.assertIn("toy tree hash", str(caught.exception))  # from the brain's archive, before anything is opened
        self.assert_nothing_written(before)

    def test_the_toy_disk_tree_is_hashed_again(self):  # import_toy_disk_not_rehashed
        real = importer.extract

        def extract_and_add(tar_bytes, dest, max_bytes, prefix=""):
            total = real(tar_bytes, dest, max_bytes, prefix)
            if prefix == TOY_DIR:
                (dest / "planted.py").write_text("x\n")
            return total
        before = read_all(self.referee)
        with mock.patch.object(importer, "extract", side_effect=extract_and_add), self.assertRaises(ImportErrorStop):
            self.run_import()
        self.assert_nothing_written(before)

    def test_a_result_with_a_toy_hash_needs_the_toy_checkout(self):  # import_without_toy
        before = read_all(self.referee)
        with self.assertRaises(ImportErrorStop):
            self.run_import(toy=False)
        self.assert_nothing_written(before)

    def test_the_referee_tree_must_be_the_signed_referee_tree(self):
        self.write_result(referee_tree_sha256="2" * 64)
        before = read_all(self.referee)
        with self.assertRaises(ImportErrorStop):
            self.run_import()
        self.assert_nothing_written(before)

    def test_a_result_that_is_not_accepted_and_transferable_is_refused(self):
        for exit_fields, verdict in (({"transferable": False}, "accepted"), ({}, "rejected")):
            with self.subTest(verdict=verdict, exit=exit_fields):
                self.write_result(**exit_fields)
                if verdict != "accepted":
                    data = json.loads(self.result.read_text())
                    data["verdict"] = verdict
                    self.result.write_text(json.dumps(data))
                before = read_all(self.referee)
                with self.assertRaises(ImportErrorStop):
                    self.run_import()
                self.assert_nothing_written(before)

    def test_an_open_stage_lock_refuses_a_stage_0_import(self):  # import_after_the_lock_opened
        """Spec sessiz (E370): with `setup/stage.json` in place, a result without a batch is Stage 0's, and the lock it
        opened is not undone by importing it again (a batch's result is another matter, `BatchImportTest`)."""
        write(self.referee, {"setup/stage.json": "{}\n"})
        before = read_all(self.referee)
        with self.assertRaises(ImportErrorStop):
            self.run_import()
        self.assert_nothing_written(before)


# ---------------------------------------------------------------- K1's trust root: names the file system resolves

def short_name(path):
    """The 8.3 short name Windows gave ``path`` (its last part), or None (another system, or short names off there)."""
    if os.name != "nt":
        return None
    buf = ctypes.create_unicode_buffer(1024)
    if not ctypes.windll.kernel32.GetShortPathNameW(str(path), buf, len(buf)):
        return None
    name = Path(buf.value).name
    return name if name.upper() != path.name.upper() else None


class ImportAliasTest(ImportCase):
    """E374 (E130's 8.3 rule): on the operator's Windows file system a name can reach an existing entry under another
    name: `BOOTST~1` is `bootstrap/`, `POLICY~1.JSO` `policy.json`, `GIT~1` `.git/`. Such a referee tree has none of
    the reserved names in any case, so `tree_hash`, `_lands_on_kept` and the re-hash of the sibling temporary tree (where
    nothing is there to alias) all pass it; the copy into the checkout would write the Founder's bytes over the trust
    root. The import asks the file system where each path lands before anything is written."""

    @staticmethod
    def aliased(aliases):
        """The file system as the operator's Windows has it (patches to enter): each ``{checkout: {alias: entry}}``
        alias exists and is that entry, though no directory lists the alias."""
        real_lexists, real_samefile = os.path.lexists, os.path.samefile
        names = {str(Path(base) / alias): str(Path(base) / entry) for base, pairs in aliases.items()
                 for alias, entry in pairs.items()}

        def lexists(path):
            return str(Path(path)) in names or real_lexists(path)

        def samefile(a, b):
            a, b = str(Path(a)), str(Path(b))
            if a in names:
                return names[a] == b
            return real_samefile(a, b)
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(importer.os.path, "lexists", side_effect=lexists))
        stack.enter_context(mock.patch.object(importer.os.path, "samefile", side_effect=samefile))
        return stack

    def assert_refused_untouched(self, says="under another name"):
        before, toy_before = read_all(self.referee, skip=()), read_all(self.toy, skip=())
        with self.assertRaises(ImportErrorStop) as caught:
            self.run_import()
        self.assertIn(says, str(caught.exception))
        self.assertEqual(read_all(self.referee, skip=()), before)
        self.assertEqual(read_all(self.toy, skip=()), toy_before)
        self.assertEqual(self.imports(), b"")
        return str(caught.exception)

    def test_a_short_name_of_what_the_referee_checkout_keeps_is_refused(self):  # import_alias_unchecked import_alias_kept_only_exact
        for alias, entry, path in (("BOOTST~1", "bootstrap", "BOOTST~1/snowball_bootstrap/__init__.py"),
                                   ("POLICY~1.JSO", "policy.json", "POLICY~1.JSO"),
                                   ("CONTRO~1.JSO", "control.json", "CONTRO~1.JSO"),
                                   ("GIT~1", ".git", "GIT~1/hooks/post-checkout")):
            with self.subTest(alias=alias):
                write(self.referee, {".git/HEAD": "ref: refs/heads/main\n"})
                with self.use_tree({"referee/ledger/chain.py": "x = 1\n",
                                    "referee/.github/workflows/loop.yml": LOOP_YML, f"referee/{path}": "EVIL\n",
                                    f"{TOY_DIR}/app.py": "y\n"}), self.aliased({self.referee: {alias: entry}}):
                    said = self.assert_refused_untouched()
                self.assertIn(f"would land on {entry}", said)

    def test_a_short_name_on_the_way_to_the_bootstraps_workflow_is_refused(self):  # import_alias_holds_unchecked
        """`GITHUB~1/workflows/` is `.github/workflows/`: an alias of `.github/` is refused, whether the path under it
        would reach `bootstrap.yml` or land beside it."""
        for path in ("GITHUB~1/workflows/bootstrap.yml", "GITHUB~1/workflows/other.yml"):
            with self.subTest(path=path):
                with self.use_tree({"referee/ledger/chain.py": "x = 1\n", f"referee/{path}": "name: evil\n",
                                    f"{TOY_DIR}/app.py": "y\n"}), self.aliased({self.referee: {"GITHUB~1": ".github"}}):
                    self.assertIn("would land on .github", self.assert_refused_untouched())

    def test_a_short_name_below_the_top_is_refused(self):  # A1_alias_top_only alias_walk_top_only
        """E403 (the second skeptic's A1): the file system is asked at every depth, not of the first part alone.
        `.github/` is listed under its own name, but `workflows/` is reached as `WORKFL~1` and `bootstrap.yml` as
        `BOOTST~1.YML`: a check of the first part passes both, and the copy writes the Founder's file over the push
        judge (the skeptic did it on C:). `GIT~1/hooks/...` is the top-level case beside them."""
        github = self.referee / ".github"
        for path, aliases, entry in (
                (".github/workflows/BOOTST~1.YML", {github / "workflows": {"BOOTST~1.YML": "bootstrap.yml"}},
                 ".github/workflows/bootstrap.yml"),
                (".github/WORKFL~1/bootstrap.yml", {github: {"WORKFL~1": "workflows"}}, ".github/workflows"),
                (".github/WORKFL~1/other.yml", {github: {"WORKFL~1": "workflows"}}, ".github/workflows"),
                ("GIT~1/hooks/post-checkout", {self.referee: {"GIT~1": ".git"}}, ".git")):
            with self.subTest(path=path):
                write(self.referee, {".git/HEAD": "ref: refs/heads/main\n"})
                # No `workflows/` beside `WORKFL~1/` in the tree: on a volume with 8.3 names the two would already be one
                # directory in the sibling temporary tree, and its re-hash would stop the import first.
                with self.use_tree({"referee/ledger/chain.py": "x = 1\n", f"referee/{path}": "EVIL\n",
                                    f"{TOY_DIR}/app.py": "y\n"}), self.aliased(aliases):
                    said = self.assert_refused_untouched()
                self.assertIn(f"would land on {entry} ", said)

    def test_a_short_name_of_the_toys_git_directory_is_refused(self):  # import_toy_alias_unchecked
        """The toy checkout keeps `.git/`; `GIT~1/hooks/post-checkout` would plant a hook the operator's next git
        command runs (E04)."""
        write(self.toy, {".git/HEAD": "ref: refs/heads/main\n"})
        with self.use_tree({"referee/ledger/chain.py": "x = 1\n", "referee/.github/workflows/loop.yml": LOOP_YML,
                            f"{TOY_DIR}/app.py": "y\n", f"{TOY_DIR}/GIT~1/hooks/post-checkout": "#!/bin/sh\nevil\n"}), \
                self.aliased({self.toy: {"GIT~1": ".git"}}):
            self.assertIn("would land on .git", self.assert_refused_untouched())

    def test_a_name_no_entry_is_listed_under_is_refused(self):  # import_alias_unlisted_allowed
        """A name the file system finds though its directory lists nothing it could be (on Windows a device name such
        as `NUL`; here a stand-in, `ghost`) is not written into."""
        real = os.path.lexists
        with self.use_tree({"referee/ledger/chain.py": "x = 1\n", "referee/ghost/x.py": "y\n",
                            f"{TOY_DIR}/app.py": "y\n"}), \
                mock.patch.object(importer.os.path, "lexists",
                                  side_effect=lambda p: Path(p) == self.referee / "ghost" or real(p)):
            self.assertIn("would land on ghost", self.assert_refused_untouched())

    def test_an_alias_of_an_earlier_trees_entry_is_cleared_like_it(self):  # import_alias_refuses_any
        """What is not kept is cleared before the copy, so a name that reaches an earlier referee tree's entry (here
        `LEDGER~1` is the old `ledger_v1/`) lands on nothing kept: the import goes on."""
        write(self.referee, {"ledger_v1/old.py": "old\n"})
        with self.use_tree({"referee/LEDGER~1/new.py": "x = 1\n", "referee/.github/workflows/loop.yml": LOOP_YML,
                            f"{TOY_DIR}/app.py": "y\n"}), self.aliased({self.referee: {"LEDGER~1": "ledger_v1"}}):
            self.run_import()
        self.assertEqual(read_all(self.referee)["bootstrap/snowball_bootstrap/__init__.py"], b"seed\n")
        self.assertNotIn("ledger_v1/old.py", read_all(self.referee))

    def test_on_a_volume_with_short_names_the_trust_root_is_not_written(self):
        """The repro on a real file system: where Windows makes 8.3 names (the system volume by default), the alias of
        `bootstrap/`, of `policy.json` and of the toy's `.git/` each stops the import with nothing written."""
        write(self.toy, {".git/HEAD": "ref: refs/heads/main\n"})
        names = {"bootstrap": short_name(self.referee / "bootstrap"),
                 "policy.json": short_name(self.referee / "policy.json"),
                 "toy .git": short_name(self.toy / ".git")}
        if not all(names.values()):
            self.skipTest("this volume makes no 8.3 short names (or this is not Windows)")
        for label, path in (("bootstrap", f"referee/{names['bootstrap']}/snowball_bootstrap/__init__.py"),
                            ("policy.json", f"referee/{names['policy.json']}"),
                            ("toy .git", f"{TOY_DIR}/{names['toy .git']}/hooks/post-checkout")):
            with self.subTest(label=label):
                files = {"referee/ledger/chain.py": "x = 1\n", f"{TOY_DIR}/app.py": "y\n", path: "EVIL = 1\n"}
                with self.use_tree(files):
                    self.assert_refused_untouched()
                self.assertEqual((self.referee / "bootstrap" / "snowball_bootstrap" / "__init__.py").read_bytes(),
                                 b"seed\n")
                self.assertEqual((self.referee / "policy.json").read_bytes(), b"{}\n")

    def short_names_below_the_top(self):
        """The real alias paths of a kept entry below the top, or of the git directory, on this volume (skip if none)."""
        write(self.referee, {".git/HEAD": "ref: refs/heads/main\n", ".git/config": "[core]\n"})
        workflow = self.referee / ".github" / "workflows" / "bootstrap.yml"
        names = {"bootstrap.yml": short_name(workflow), "workflows": short_name(workflow.parent),
                 ".github": short_name(workflow.parent.parent), ".git": short_name(self.referee / ".git")}
        if not all(names.values()):
            self.skipTest("this volume makes no 8.3 short names (or this is not Windows)")
        return {".github/workflows/bootstrap.yml": f".github/workflows/{names['bootstrap.yml']}",
                ".github/workflows": f".github/{names['workflows']}/bootstrap.yml",
                ".github": f"{names['.github']}/workflows/bootstrap.yml",
                ".git": f"{names['.git']}/hooks/post-checkout"}

    def test_on_a_volume_with_short_names_nothing_kept_below_the_top_is_written(self):  # A1_alias_top_only
        """E403, the skeptic's repro: `.github/workflows/BOOTST~1.YML`, `.github/WORKFL~1/bootstrap.yml`,
        `GITHUB~1/workflows/bootstrap.yml` and `GIT~1/hooks/...` on a volume that makes 8.3 names stop the import with
        nothing written: the push judge and the git directory stay as they were."""
        for entry, path in self.short_names_below_the_top().items():
            with self.subTest(entry=entry, path=path):
                files = {"referee/ledger/chain.py": "x = 1\n", f"{TOY_DIR}/app.py": "y\n", f"referee/{path}": "EVIL\n"}
                with self.use_tree(files):
                    self.assertIn(f"would land on {entry} ", self.assert_refused_untouched())
                self.assertEqual(workflow_bytes(self.referee), b"name: snowball-bootstrap\n")

    def test_on_a_volume_with_short_names_the_kept_state_stops_what_the_name_check_misses(self):  # import_kept_state_unchecked
        """E403's defence in depth, on the real file system: with the name check taken away, each alias really
        writes into a kept entry, and the second reading of what the checkout keeps stops the import before the counter
        row; the message names the entry and says to reset the checkout."""
        for entry, path in self.short_names_below_the_top().items():
            with self.subTest(entry=entry, path=path):
                write(self.referee, OPERATOR_FILES)
                files = {"referee/ledger/chain.py": "x = 1\n", f"{TOY_DIR}/app.py": "y\n", f"referee/{path}": "EVIL\n"}
                with self.use_tree(files), mock.patch.object(importer, "_refuse_aliases"), \
                        self.assertRaises(ImportErrorStop) as caught:
                    self.run_import()
                said = str(caught.exception)
                self.assertIn("the copy changed what the referee checkout keeps", said)
                self.assertIn(".git/hooks/post-checkout" if entry == ".git" else ".github/workflows/bootstrap.yml", said)
                self.assertIn("reset the checkout", said)
                self.assertEqual(self.imports(), b"")


def workflow_bytes(referee):
    return (referee / ".github" / "workflows" / "bootstrap.yml").read_bytes()


class ImportKeptStateTest(ImportCase):
    """E403: whatever name the file system resolves, a path of the signed tree that reaches a kept entry changes it.
    What each checkout keeps (`bootstrap/`, `.github/workflows/bootstrap.yml`, the operator's files, the git directory;
    the toy's git directory) is read with its bytes before anything is written and after the copy; a difference stops
    the import before the counter row. Here the copy itself is made to write where a resolved alias would."""

    def copy_and_also(self, target, change):
        """`shutil.copytree` as the import calls it, but the copy into ``target`` also does ``change`` (what a file
        system that resolved some name onto a kept entry would do)."""
        real = shutil.copytree

        def copy(src, dst, *args, **kw):  # copytree calls itself for each directory below
            done = real(src, dst, *args, **kw)
            if Path(dst) == target:
                change()
            return done
        return mock.patch.object(importer.shutil, "copytree", side_effect=copy)

    def test_a_change_to_any_kept_entry_stops_the_import(self):
        write(self.referee, {".git/HEAD": "ref: refs/heads/main\n", ".git/config": "[core]\n"})
        write(self.toy, {".git/HEAD": "ref: refs/heads/main\n", ".git/config": "[core]\n"})
        referee, toy = self.referee, self.toy
        cases = {  # what the copy also does -> the entry the stop names
            "bootstrap/ file": (referee, lambda: write(referee, {"bootstrap/snowball_bootstrap/__init__.py": "EVIL\n"}),
                                "referee", "bootstrap/snowball_bootstrap/__init__.py"),
            "bootstrap/ new file": (referee, lambda: write(referee, {"bootstrap/snowball_bootstrap/x.py": "EVIL\n"}),
                                    "referee", "bootstrap/snowball_bootstrap/x.py"),
            "push judge": (referee, lambda: write(referee, {".github/workflows/bootstrap.yml": "name: evil\n"}),
                           "referee", ".github/workflows/bootstrap.yml"),
            "operator file": (referee, lambda: write(referee, {"policy.json": "{\"x\": 1}\n"}), "referee", "policy.json"),
            "operator file gone": (referee, lambda: (referee / "seats" / "29-tohum-koltuklari.md").unlink(), "referee",
                                   "seats/29-tohum-koltuklari.md"),
            "git config": (referee, lambda: write(referee, {".git/config": "[core]\n\tfsmonitor = evil\n"}), "referee",
                           ".git/config"),
            "git hook": (referee, lambda: write(referee, {".git/hooks/post-checkout": "#!/bin/sh\nevil\n"}), "referee",
                         ".git/hooks/post-checkout"),
            "toy git hook": (toy, lambda: write(toy, {".git/hooks/post-checkout": "#!/bin/sh\nevil\n"}), "toy",
                             ".git/hooks/post-checkout"),
            "toy git config": (toy, lambda: write(toy, {".git/config": "[core]\n\thooksPath = x\n"}), "toy", ".git/config"),
        }
        for label, (target, change, what, entry) in cases.items():
            with self.subTest(label):
                write(self.referee, dict(OPERATOR_FILES, **{".git/config": "[core]\n"}))
                write(self.toy, {".git/config": "[core]\n"})
                for stray in (self.referee / ".git" / "hooks", self.toy / ".git" / "hooks"):
                    shutil.rmtree(stray, ignore_errors=True)
                (self.referee / "bootstrap" / "snowball_bootstrap" / "x.py").unlink(missing_ok=True)
                with self.copy_and_also(target, change), self.assertRaises(ImportErrorStop) as caught:
                    self.run_import()
                said = str(caught.exception)
                self.assertIn(f"the copy changed what the {what} checkout keeps: ", said)
                self.assertIn(entry, said)
                self.assertIn("reset the checkout before anything is pushed", said)
                self.assertEqual(self.imports(), b"")

    def test_an_import_that_reaches_nothing_kept_passes_and_keeps_every_entry(self):
        write(self.referee, {".git/HEAD": "ref: refs/heads/main\n", ".git/hooks/README": "hooks\n"})
        write(self.toy, {".git/HEAD": "ref: refs/heads/main\n"})
        before = (importer.kept_state(self.referee, importer.kept, importer._holds_kept),
                  importer.kept_state(self.toy, importer._git_dir, importer._nothing))
        self.run_import()
        after = importer.kept_state(self.referee, importer.kept, importer._holds_kept)
        self.assertEqual(after.pop("setup/imports.jsonl")[:0], "")  # the counter row, written after the check
        self.assertEqual(after, before[0])
        self.assertEqual(importer.kept_state(self.toy, importer._git_dir, importer._nothing), before[1])
        self.assertIn(".github/workflows/bootstrap.yml", before[0])  # held below the top, read there
        self.assertIn(".git/hooks/README", before[0])  # a kept directory is read whole
        self.assertNotIn(".github/workflows/loop.yml", before[0] | importer.kept_state(self.referee, importer.kept,
                                                                                         importer._holds_kept))

    def test_the_kept_state_names_each_entry_with_what_it_is(self):  # kept_state_files_only kept_state_no_descent
        write(self.referee, {".git/hooks/README": "hooks\n", "ledger/x.py": "not kept\n"})
        state = importer.kept_state(self.referee, importer.kept, importer._holds_kept)
        self.assertEqual(state[".git"], "dir")
        self.assertEqual(state[".git/hooks"], "dir")
        self.assertEqual(state[".git/hooks/README"], hashlib.sha256(b"hooks\n").hexdigest())
        self.assertEqual(state["policy.json"], hashlib.sha256(b"{}\n").hexdigest())
        self.assertNotIn("ledger/x.py", state)
        self.assertNotIn(".github", state)  # on the way, not kept: its other entries are cleared, not compared
        self.assertEqual(sorted(k for k in state if k.startswith(".github")), [".github/workflows/bootstrap.yml"])

    @posix_only
    def test_a_link_or_a_special_entry_in_what_is_kept_is_compared_as_what_it_is(self):  # kept_state_links_ignored
        write(self.referee, {".git/HEAD": "ref: refs/heads/main\n"})
        os.symlink("HEAD", self.referee / ".git" / "link")
        os.mkfifo(self.referee / ".git" / "fifo")
        state = importer.kept_state(self.referee, importer.kept, importer._holds_kept)
        self.assertEqual((state[".git/link"], state[".git/fifo"]), ("link:HEAD", "special"))
        (self.referee / ".git" / "link").unlink()
        os.symlink("config", self.referee / ".git" / "link")
        self.assertEqual(importer.kept_state(self.referee, importer.kept, importer._holds_kept)[".git/link"],
                         "link:config")


# ---------------------------------------------------------------- the batch transfer (`asama-1/13` 3, E378)

class BatchImportTest(ImportCase):
    """Once `setup/stage.json` opened Stage 1, the same command transfers the open batch's signed (A) (`25a` 1:
    "her parti çıkışında aynı komut"; `asama-1/06`: P1's (A), transfer and (B) come first). The toy is left as it is."""

    def setUp(self):
        super().setUp()
        self.stage0_rows, data = chained([{"ts": "2026-10-31T08:00:00Z", "stage": 0, "brain_sha": "c" * 40,
                                           "referee_tree_sha256": "d" * 64, "result_sha256": "e" * 64,
                                           "toy_tree_sha256": "f" * 64}])
        write(self.referee, {"setup/imports.jsonl": data,
                             "setup/stage.json": json.dumps(lock_of(data.split(b"\n")[0]))})
        self.write_result(stage=1, batch="P1")

    def test_the_open_batchs_result_is_transferred_and_its_row_names_the_batch(self):  # import_batch_refused import_batch_row_unnamed
        """`26c:39`: `{ts, stage, batch, brain_sha, referee_tree_sha256, result_sha256}` chained on, no toy hash."""
        row = self.run_import(toy=False)
        self.assertEqual(list(row), BATCH_KEYS)
        self.assertEqual((row["stage"], row["batch"], row["brain_sha"], row["referee_tree_sha256"]),
                         (1, "P1", self.sha, self.referee_hash))
        self.assertEqual(row["result_sha256"], hashlib.sha256(self.result.read_bytes()).hexdigest())
        self.assertEqual(row["prev_hash"], self.stage0_rows[-1]["row_hash"])
        self.assertEqual(read_all(self.toy), {})
        self.assertEqual(read_all(self.referee)["ledger/chain.py"], b"x = 1\n")
        self.assertEqual(stagelock.batches_done(self.referee, stagelock.load(self.referee)), ("P1",))

    def test_a_batch_is_transferred_once_and_only_the_open_one(self):  # import_batch_any
        self.run_import(toy=False)
        before = read_all(self.referee)
        with self.assertRaises(ImportErrorStop) as caught:  # P1 is done; the seed carries no later batch table
            self.run_import(toy=False)
        self.assertIn("open batch is None", str(caught.exception))
        self.assertEqual(read_all(self.referee), before)

    def test_a_batch_result_of_another_batch_or_stage_or_without_the_lock_is_refused(self):  # import_batch_stage_unchecked
        for fields, says in (({"stage": 1, "batch": "P2"}, "open batch is 'P1'"), ({"stage": 2, "batch": "P1"}, "Stage 2"),
                             ({"stage": True, "batch": "P1"}, "Stage True"), ({"batch": "P1"}, "Stage None")):
            with self.subTest(fields=fields):
                self.write_result(**fields)
                before = read_all(self.referee)
                with self.assertRaises(ImportErrorStop) as caught:
                    self.run_import(toy=False)
                self.assertIn(says, str(caught.exception))
                self.assertEqual(read_all(self.referee), before)
        (self.referee / "setup" / "stage.json").unlink()
        self.write_result(stage=1, batch="P1")
        with self.assertRaises(ImportErrorStop) as caught:
            self.run_import(toy=False)
        self.assertIn("only once setup/stage.json opened", str(caught.exception))

    def test_a_batch_transfer_leaves_the_toy_alone(self):  # import_batch_touches_the_toy
        write(self.toy, {"app.py": "the live toy\n"})
        before = read_all(self.referee)
        with self.assertRaises(ImportErrorStop) as caught:
            self.run_import(toy=True)
        self.assertIn("without --toy", str(caught.exception))
        self.assertEqual(read_all(self.referee), before)
        self.assertEqual(read_all(self.toy), {"app.py": b"the live toy\n"})


# ---------------------------------------------------------------- stage-open

TOY_TARGET = {"id": "toy-t", "repo": "owner/toy", "kind": "toy", "base_sha": None, "identifiers": [],
              "excluded_paths": [], "unit_candidates": []}
COPY_BASE = "ab" * 20
COPY_TARGET = {"id": "copy-t", "repo": "owner/copy", "kind": "copy", "base_sha": COPY_BASE, "identifiers": ["acme"],
               "excluded_paths": [], "unit_candidates": ["app"]}
OWNER_EXCEPTION = {"anchor": "durustluk", "stage": 0, "carry_to": 1, "reason": "E287", "carry_commitment": "c" * 64,
                   "measured": False}


class Target:
    """A target repository whose `brain/state` holds a ledger and a root chain, as the loop referee writes them; the
    root's bundle has one `hashedrekord` log entry that records the root as its hash (`29j`)."""

    def __init__(self, path, rows, root_override=None, entry_hash=None, body=None):
        self.path = path
        make_repo(path, {"README.md": "main\n"})
        sh(path, "git", "checkout", "-q", "--orphan", "brain/state")
        sh(path, "git", "rm", "-q", "-rf", ".")
        self.rows, self.ledger = chained(rows)
        tips = {}
        for row in self.rows:
            tips[row["part"]] = row["row_hash"]
        self.root = root_override or hashlib.sha256(canonical(tips)).hexdigest()
        recorded = entry_hash if entry_hash is not None else {"algorithm": "sha256", "value": self.root}
        signature = {"content": base64.b64encode(str(path).encode()).decode(), "publicKey": {"content": "x"}}
        entry = body(self.root, signature) if body else {"apiVersion": "0.0.1", "kind": "hashedrekord", "spec": {
            "data": {"hash": recorded}, "signature": signature}}
        self.body = json.dumps(entry, separators=(",", ":")).encode()
        self.uuid = "24296fb24b8ad77a" + hashlib.sha256(b"\x00" + self.body).hexdigest()
        self.roots, root_bytes = chained([{"row_id": "r1", "ts": "2026-10-31T10:00:00Z", "root": self.root,
                                           "rekor_uuid": self.uuid}])
        write(path, {"ledger.jsonl": self.ledger, "chain/root.jsonl": root_bytes, "status.md": "# status\n"})
        sh(path, "git", "add", "-A")
        sh(path, "git", "commit", "-q", "-m", "state")
        self.head = sh(path, "git", "rev-parse", "HEAD")
        sh(path, "git", "checkout", "-q", "main")
        self.bundle = path.parent / f"{path.name}-root.sigstore.json"
        self.bundle.write_text(json.dumps({"mediaType": "application/vnd.dev.sigstore.bundle.v0.3+json",
                                           "verificationMaterial": {"tlogEntries": [
                                               {"canonicalizedBody": base64.b64encode(self.body).decode()}]}}))

    def line_of(self, index):
        return self.ledger.split(b"\n")[index]


def event(kind, payload, part="events"):
    return {"row_id": f"{part}-{kind}", "ts": "2026-10-31T09:00:00Z", "part": part, "kind": kind, "payload": payload,
            "derivation": "tool", "trust": "verified", "snapshot_id": "0" * 40, "evidence_refs": []}


class StageOpenCase(unittest.TestCase):
    """The referee checkout after Stage 0's transfer, the signed (A) result it imported, and the two targets' state
    clones after (B): genesis rows naming the transfer, a copy merge, the PASS row on the toy carrying the copy's rows."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name)
        self.referee = self.work / "referee"
        write(self.referee, OPERATOR_FILES)
        self.write_summary()
        self.result = self.work / "result.json"
        self.write_signed()
        self.write_counter()
        self.made = 0
        self.copy = self.make_copy()
        self.toy = self.make_toy()
        self.verified = []

        def verify(subject, bundle, identity, sigstore_python):
            self.verified.append((subject, Path(bundle), identity, sigstore_python))
        patcher = mock.patch.object(importer, "verify_signature", side_effect=verify)
        patcher.start()
        self.addCleanup(patcher.stop)

    def write_summary(self, targets=(TOY_TARGET, COPY_TARGET), **over):
        summary = {"seed_commit": "a" * 40, "seed_tree_sha256": "b" * 64, "targets": list(targets)}
        summary.update(over)
        write(self.referee, {"setup/summary.json": json.dumps(summary)})

    def write_signed(self, **exit_fields):
        """The (A) result the import verified; its bytes' hash is the transfer row's `result_sha256`."""
        exit_block = edited({"requested": True, "transferable": True, "brain_sha": "c" * 40,
                             "referee_tree_sha256": "d" * 64, "toy_tree_sha256": "f" * 64}, exit_fields)
        self.result.write_bytes(json.dumps({"kind": "exit", "verdict": "accepted", "exit": exit_block},
                                           indent=2).encode("utf-8") + b"\n")

    def write_counter(self, later=()):
        """Stage 0's transfer of the signed result, a touch that is no transfer (`29n`), then ``later`` rows."""
        self.import_rows, data = chained([
            {"ts": "2026-10-31T08:00:00Z", "stage": 0, "brain_sha": "c" * 40, "referee_tree_sha256": "d" * 64,
             "result_sha256": hashlib.sha256(self.result.read_bytes()).hexdigest(), "toy_tree_sha256": "f" * 64},
            {"ts": "2026-10-31T08:30:00Z", "stage": 0}, *later])
        write(self.referee, {"setup/imports.jsonl": data})
        self.import_line = data.split(b"\n")[0]
        self.line_sha = hashlib.sha256(self.import_line).hexdigest()

    def fresh(self, name):
        """A new directory for a target (a git repository's objects are read-only on Windows: none is removed)."""
        self.made += 1
        return self.work / f"{name}{self.made}"

    def copy_rows(self, genesis=None):
        return [event("genesis", edited({"target": "copy-t", "base_sha": COPY_BASE,
                                         "import_line_sha256": self.line_sha}, genesis)),
                event("merge", {"c": 2}), event("status", {"b": 3})]

    def make_copy(self, rows=None, **kw):
        return Target(self.fresh("copy"), rows if rows is not None else self.copy_rows(), **kw)

    def toy_rows(self, genesis=None, payload=None, row=None):
        passed = event("pass", edited({"stage": 0, "verdict": "PASS", "import_line_sha256": self.line_sha,
                                       "copy_genesis_row_hash": self.copy.rows[0]["row_hash"],
                                       "copy_merge_row_hashes": [self.copy.rows[1]["row_hash"]]}, payload))
        return [event("genesis", edited({"target": "toy-t", "import_line_sha256": self.line_sha}, genesis)),
                event("merge", {"c": 1}), event("cost", {"usd": 1}, part="cost"), edited(passed, row),
                event("status", {"b": 2})]

    def make_toy(self, rows=None, **kw):
        return Target(self.fresh("toy"), rows if rows is not None else self.toy_rows(), **kw)

    def argv(self, **over):
        args = {"--referee": self.referee, "--toy": self.toy.path, "--copy": self.copy.path,
                "--ref": "refs/heads/brain/state", "--identity": "loop-id", "--sigstore-python": "py",
                "--toy-root-bundle": self.toy.bundle, "--copy-root-bundle": self.copy.bundle, "--result": self.result}
        args.update(over)
        return ["stage-open"] + [str(x) for pair in args.items() for x in pair]

    def open(self):
        return stagelock.open_stage(self.referee, self.toy.path, self.copy.path, "refs/heads/brain/state", "loop-id",
                                    "py", self.toy.bundle, self.copy.bundle, self.result)

    def stage_file(self):
        return self.referee / "setup" / "stage.json"

    def refused(self, says):
        with self.assertRaises((ConfigError, ImportErrorStop, gitio.GitError)) as caught:
            self.open()
        self.assertIn(says, str(caught.exception))
        self.assertFalse(self.stage_file().exists())


class StageOpenWritesTest(StageOpenCase):
    def test_the_lock_is_26cs_five_fields_and_nothing_else(self):
        """`asama-0/10a`, `26c:40-41`, `25a` 9: `{stage: 1, pass_row_sha256, toy_state_head, copy_state_head,
        import_line_sha256}`, the hashes of the PASS line and the last transfer line without their LF (`29o`)."""
        self.assertEqual(cli.main(self.argv()), 0)
        lock = json.loads(self.stage_file().read_text(encoding="utf-8"))
        self.assertEqual(lock, {"stage": 1, "pass_row_sha256": hashlib.sha256(self.toy.line_of(3)).hexdigest(),
                                "toy_state_head": self.toy.head, "copy_state_head": self.copy.head,
                                "import_line_sha256": self.line_sha})
        self.assertEqual(self.stage_file().read_bytes(), canon.dump(lock).encode("utf-8"))  # LF, sorted, readable
        self.assertEqual(stagelock.load(self.referee), stagelock.Lock(**lock))  # what the bootstrap then reads

    def test_each_targets_last_root_is_verified_with_sigstore_as_the_root_digest(self):  # stage_open_root_not_signed stage_open_root_signs_another_artifact
        """E375, `29j`, `13`: the Rekor entry's hash is the root, so Sigstore verifies the bundle against the digest
        `sha256:<root>`, not against a file of the root's hex text (whose sha256 is not the root)."""
        self.open()
        self.assertEqual(self.verified, [(f"sha256:{self.toy.root}", self.toy.bundle, "loop-id", "py"),
                                         (f"sha256:{self.copy.root}", self.copy.bundle, "loop-id", "py")])

    def test_stage_open_is_a_command_the_operator_can_ask_for_help(self):
        with self.assertRaises(SystemExit) as caught:
            cli.build_parser().parse_args(["stage-open", "--help"])
        self.assertEqual(caught.exception.code, 0)


class SigstoreCallTest(unittest.TestCase):
    def test_the_seeds_sigstore_call_takes_a_digest_as_its_input(self):  # verify_subject_not_passed
        """sigstore 4.5.0 (`requirements/sign.txt`) reads an input `sha256:<hex>` as a digest, not as a file name."""
        calls = []
        with mock.patch.object(importer.subprocess, "run",
                               side_effect=lambda argv, **k: calls.append(argv) or mock.Mock(returncode=0)):
            importer.verify_signature("sha256:" + "a" * 64, Path("b.json"), "id", "py")
        self.assertEqual(calls[0][-1], "sha256:" + "a" * 64)
        self.assertEqual(calls[0][:5], ["py", "-m", "sigstore", "verify", "identity"])
        self.assertIn("sigstore==4.5.0", (BOOT / "requirements" / "sign.txt").read_text(encoding="utf-8"))


class StageOpenRefusesTest(StageOpenCase):
    def test_without_an_accepted_transferable_import(self):  # stage_open_without_a_transfer
        """Only a transfer (a row with `referee_tree_sha256`, `29o`) of Stage 0 opens Stage 1: a Stage 1 transfer of
        the very result in hand stops at the stage, before anything else is read."""
        signed = hashlib.sha256(self.result.read_bytes()).hexdigest()
        for rows in ([{"ts": "2026-10-31T08:30:00Z", "stage": 0}],
                     [{"ts": "2026-10-31T08:00:00Z", "stage": 1, "brain_sha": "c" * 40, "referee_tree_sha256": "d" * 64,
                       "result_sha256": signed}],
                     [{"ts": "2026-10-31T08:00:00Z", "stage": False, "brain_sha": "c" * 40,
                       "referee_tree_sha256": "d" * 64, "result_sha256": signed}]):
            with self.subTest(rows=rows):
                write(self.referee, {"setup/imports.jsonl": chained(rows)[1]})
                self.refused("the last transfer is not Stage 0's")
        (self.referee / "setup" / "imports.jsonl").unlink()
        self.refused("imports.jsonl")

    def test_with_a_broken_counter(self):  # stage_open_counter_unchained
        data = (self.referee / "setup" / "imports.jsonl").read_bytes()
        write(self.referee, {"setup/imports.jsonl": data.replace(b'"stage":0', b'"stage":3', 1)})
        self.refused("imports.jsonl")

    def test_without_the_pass_row(self):  # stage_open_without_pass stage_open_two_pass_rows stage_open_pass_any_part stage_open_pass_any_verdict stage_open_pass_any_stage
        first = self.toy_rows()[:3]
        for extra, says in (([], "no PASS row"),
                            ([event("pass", {"stage": 0, "verdict": "FAIL"})], "no PASS row"),
                            ([event("pass", {"stage": 1, "verdict": "PASS"})], "no PASS row"),
                            ([event("pass", {"stage": False, "verdict": "PASS"})], "no PASS row"),
                            ([event("pass", {"stage": 0, "verdict": "PASS"}, part="drill")], "no PASS row"),
                            ([self.toy_rows()[3], event("pass2", self.toy_rows()[3]["payload"])], "2 PASS rows")):
            with self.subTest(rows=[r["payload"] for r in extra]):
                self.toy = self.make_toy(first + extra)
                self.refused(says)

    def test_with_a_broken_toy_or_copy_chain(self):  # stage_open_chain_unchecked
        for name in ("toy", "copy"):
            with self.subTest(target=name):
                target = getattr(self, name)
                sh(target.path, "git", "checkout", "-q", "brain/state")
                data = target.ledger.replace(b'"c":', b'"C":', 1)
                write(target.path, {"ledger.jsonl": data})
                sh(target.path, "git", "commit", "-q", "-am", "edit a row")
                sh(target.path, "git", "checkout", "-q", "main")
                self.refused(f"{name} brain/state ledger.jsonl")
                sh(target.path, "git", "branch", "-q", "-f", "brain/state", target.head)

    def test_when_the_ledger_moved_past_its_last_anchored_root(self):  # stage_open_root_not_the_tips
        """`13`, `29j` `verify_tip_moved`: the root anchors the head's tips; a tip past it is not anchored."""
        self.copy = self.make_copy(root_override="9" * 64)
        self.toy = self.make_toy()
        self.refused("copy")

    def test_when_the_root_bundle_is_not_the_root_rows_log_entry(self):  # stage_open_bundle_any_entry
        other = json.loads(self.copy.bundle.read_text())
        self.toy.bundle.write_text(json.dumps(other))
        self.refused("rekor_uuid")

    def test_when_the_log_entry_does_not_record_the_root(self):  # stage_open_entry_hash_unchecked
        """E375, `29j` `entry_root_mismatch`: the entry the root row names must record the root itself as its hash."""
        for recorded in ({"algorithm": "sha256", "value": hashlib.sha256(b"x").hexdigest()},
                         {"algorithm": "sha512", "value": None}, "not a hash"):
            with self.subTest(recorded=recorded):
                self.toy = self.make_toy(entry_hash=recorded)
                self.refused("entry_root_mismatch")
        self.assertEqual(self.verified, [])  # refused before Sigstore is asked

    def test_a_log_entry_of_another_kind_or_body_does_not_open_the_lock(self):  # S2_entry_kind_unchecked
        """E406 (the skeptic's S2): only a `hashedrekord` body whose `spec.data.hash` is the root records it. Another
        kind carrying the same `spec.data.hash` (here `intoto`, and `rekord`) does not; nor does a Rekor v2 body
        (`hashedrekord` 0.0.2, the digest under `spec.hashedRekordV002`): the seed reads v0.0.1 bodies alone and is
        closed to any other until a seed epoch reads it (`26d` 8)."""
        bodies = {
            "intoto": lambda root, sig: {"apiVersion": "0.0.2", "kind": "intoto", "spec": {
                "data": {"hash": {"algorithm": "sha256", "value": root}}, "signature": sig}},
            "rekord": lambda root, sig: {"apiVersion": "0.0.1", "kind": "rekord", "spec": {
                "data": {"hash": {"algorithm": "sha256", "value": root}}, "signature": sig}},
            "hashedrekord v0.0.2": lambda root, sig: {"apiVersion": "0.0.2", "kind": "hashedrekord", "spec": {
                "hashedRekordV002": {"data": {"algorithm": "SHA2_256",
                                              "digest": base64.b64encode(bytes.fromhex(root)).decode()},
                                     "signature": sig}}},
        }
        for label, body in bodies.items():
            with self.subTest(body=label):
                self.toy = self.make_toy(body=body)
                self.refused("entry_root_mismatch")
        self.assertEqual(self.verified, [])
        self.toy = self.make_toy()  # the v0.0.1 hashedrekord body, as the vectors' `root` group has it, opens
        self.open()
        self.assertTrue(self.stage_file().exists())

    def test_when_sigstore_refuses_the_root(self):
        importer.verify_signature.side_effect = ImportErrorStop("signature verification failed: no")
        self.refused("signature verification failed")

    def test_without_the_targets_state_branch(self):
        self.copy = self.make_copy()
        sh(self.copy.path, "git", "branch", "-q", "-D", "brain/state")
        self.refused("brain/state")

    def test_when_the_lock_is_already_open(self):  # stage_open_overwrites
        write(self.referee, {"setup/stage.json": '{"stage": 1}\n'})
        with self.assertRaises(ConfigError):
            self.open()
        self.assertEqual(self.stage_file().read_text(), '{"stage": 1}\n')


class StageOpenBindsTheCopyTest(StageOpenCase):
    """E376, `10a` #pass: the PASS row carries the copy's genesis and merge rows' hashes; `--copy` must be the clone of
    `setup/summary.json`'s copy target that holds them, and `--toy` the toy target's."""

    def test_the_toy_clone_given_as_the_copy_is_refused(self):  # SK_copy_target_any stage_open_copy_target_unchecked
        self.copy = self.toy
        self.refused("copy target 'copy-t'")

    def test_each_clone_is_its_targets(self):  # stage_open_toy_target_unchecked
        for rows, name, says in ((self.toy_rows(genesis={"target": "copy-t"}), "toy", "toy target 'toy-t'"),
                                 (self.copy_rows(genesis={"target": "toy-t"}), "copy", "copy target 'copy-t'"),
                                 (self.copy_rows(genesis={"base_sha": "cd" * 20}), "copy", "base_sha"),
                                 (self.toy_rows()[1:], "toy", "toy target")):  # its first row is no genesis
            with self.subTest(name=name, says=says):
                if name == "copy":
                    self.copy = self.make_copy(rows)
                    self.toy = self.make_toy()
                else:
                    self.toy = self.make_toy(rows)
                self.refused(says)
                self.copy, self.toy = self.make_copy(), None
                self.toy = self.make_toy()

    def test_the_summary_names_one_toy_and_one_copy(self):  # stage_open_targets_unchecked
        for targets in ((TOY_TARGET,), (TOY_TARGET, COPY_TARGET, dict(COPY_TARGET, id="copy-2")), ()):
            with self.subTest(targets=[t["id"] for t in targets]):
                self.write_summary(targets)
                self.refused("one toy and one copy target")

    def test_the_pass_row_names_the_copys_genesis_and_merge_rows(self):  # stage_open_copy_rows_unchecked
        copy_rows = self.copy.rows
        for payload in ({"copy_genesis_row_hash": DROP}, {"copy_genesis_row_hash": "1" * 64},
                        {"copy_genesis_row_hash": copy_rows[1]["row_hash"]}):
            with self.subTest(payload=payload):
                self.toy = self.make_toy(self.toy_rows(payload=payload))
                self.refused("copy_genesis_row_hash")
        for merges in (DROP, [], ["2" * 64], [copy_rows[0]["row_hash"]], [copy_rows[1]["row_hash"]] * 2,
                       copy_rows[1]["row_hash"], [{"h": 1}]):
            with self.subTest(merges=merges):
                self.toy = self.make_toy(self.toy_rows(payload={"copy_merge_row_hashes": merges}))
                self.refused("copy_merge_row_hashes")
        # Two merges on the copy, both named (the status row is no merge, `26d` 6).
        self.copy = self.make_copy(self.copy_rows()[:2] + [event("merge", {"c": 3})] + self.copy_rows()[2:])
        merges = [r["row_hash"] for r in self.copy.rows if r["kind"] == "merge"]
        self.assertEqual(len(merges), 2)
        self.toy = self.make_toy(self.toy_rows(payload={"copy_merge_row_hashes": merges}))
        self.open()
        self.assertTrue(self.stage_file().exists())


class StageOpenBindsTheTransferTest(StageOpenCase):
    """E377, `29o`, `02` 5: the lock binds the referee (B) ran on. Both genesis rows name the counter's last transfer
    line; a transfer imported after it (no lock yet, so the import lets it in, `25a` "Başarısızlık") opens nothing."""

    def test_a_genesis_naming_another_import_line_is_refused(self):  # stage_open_genesis_line_unchecked
        for name in ("toy", "copy"):
            with self.subTest(name=name):
                if name == "toy":
                    self.toy = self.make_toy(self.toy_rows(genesis={"import_line_sha256": "9" * 64}))
                else:
                    self.copy = self.make_copy(self.copy_rows(genesis={"import_line_sha256": "9" * 64}))
                    self.toy = self.make_toy()
                self.refused(f"{name} brain/state: the genesis row names another transfer")
                self.copy = self.make_copy()
                self.toy = self.make_toy()

    def test_a_second_stage_0_transfer_after_the_pass_opens_nothing(self):  # stage_open_import_line_of_the_last_row
        """(B) ran on the first transfer (both genesis rows name it); a second Stage 0 transfer imported after the PASS
        row is the counter's last, and its own signed result in hand does not open the lock either."""
        first = [{k: v for k, v in row.items() if k not in ("prev_hash", "row_hash")} for row in self.import_rows]
        self.write_signed(brain_sha="7" * 40)
        second = {"ts": "2026-10-31T12:00:00Z", "stage": 0, "brain_sha": "7" * 40, "referee_tree_sha256": "8" * 64,
                  "result_sha256": hashlib.sha256(self.result.read_bytes()).hexdigest(), "toy_tree_sha256": "5" * 64}
        write(self.referee, {"setup/imports.jsonl": chained(first + [second])[1]})
        self.refused("toy brain/state: the genesis row names another transfer than the counter's last one")


class StageOpenCarriesTheExceptionTest(StageOpenCase):
    """E379, `02` "Sahip istisnası": the PASS row carries the owner's exception by name, exactly as the signed (A)
    result names it, so the condition carried to Stage 1's (A) is not lost; `--result` is that result (its hash is the
    transfer row's `result_sha256`)."""

    def with_exception(self):
        self.write_signed(owner_exception=OWNER_EXCEPTION)
        self.write_counter()
        self.copy = self.make_copy()

    def test_the_pass_row_carries_the_signed_exception_exactly(self):  # stage_open_owner_exception_unchecked SK_exception_anchor_any
        self.with_exception()
        self.toy = self.make_toy()
        self.refused("owner_exception")
        for change in ({"anchor": "kok"}, {"carry_to": None}, {"carry_commitment": None}, {"measured": True},
                       {"measured": 0}, {"reason": "other"}, {"stage": DROP}, {"extra": 1}):
            with self.subTest(change=change):
                self.toy = self.make_toy(self.toy_rows(payload={"owner_exception": edited(OWNER_EXCEPTION, change)}))
                self.refused("owner_exception")
        self.toy = self.make_toy(self.toy_rows(payload={"owner_exception": dict(OWNER_EXCEPTION)}))
        self.open()
        self.assertTrue(self.stage_file().exists())

    def test_no_exception_is_carried_that_the_signed_result_does_not_name(self):  # stage_open_exception_one_sided
        self.toy = self.make_toy(self.toy_rows(payload={"owner_exception": dict(OWNER_EXCEPTION)}))
        self.refused("owner_exception")

    def test_the_result_must_be_the_one_the_transfer_imported(self):  # stage_open_result_unbound
        self.result.write_bytes(self.result.read_bytes() + b" ")
        self.refused("result_sha256")
        self.result.unlink()
        self.refused("cannot be read")


class StageOpenNeedsTheRefereesRowTest(StageOpenCase):
    """E388, E404, `26`, `13`, `26d`: rows the player proposes carry `proposed_by` and `trust: inferred`; only the
    referee's own PASS row opens the lock: no `proposed_by`, `trust` one of `26`'s other two, a merge-evidence
    derivation."""

    def test_a_player_proposed_or_inferred_pass_row_is_refused(self):  # stage_open_pass_any_trust
        for row in ({"trust": "inferred"}, {"trust": DROP}, {"trust": "VERIFIED"}, {"derivation": "player"},
                    {"derivation": "llm_inference"}, {"derivation": DROP}):
            with self.subTest(row=row):
                self.toy = self.make_toy(self.toy_rows(row=row))
                self.refused("not the referee's own row")
        for row in ({"proposed_by": "founder"}, {"proposed_by": "founder", "trust": "inferred", "derivation": "player"}):
            with self.subTest(row=row):  # a proposal is no PASS row at all: it is left out before the count
                self.toy = self.make_toy(self.toy_rows(row=row))
                self.refused("no PASS row")
        self.toy = self.make_toy(self.toy_rows(row={"derivation": "test_verified"}))
        self.open()
        self.assertTrue(self.stage_file().exists())

    def test_26s_observed_trust_is_the_referees_too(self):  # stage_open_observed_refused
        """E404: `26` has three trust values and only `inferred` marks a player's proposal; an `observed` PASS row (the
        second skeptic's N3) is the referee's own and opens the lock."""
        self.toy = self.make_toy(self.toy_rows(row={"trust": "observed", "derivation": "tool"}))
        self.open()
        self.assertTrue(self.stage_file().exists())

    def test_a_proposed_copy_of_the_pass_row_is_left_out(self):  # stage_open_proposals_counted
        """E405 (the second skeptic): a player's proposed copy of the PASS row beside the referee's own made "2 PASS
        rows" and blocked the lock for good; rows with `proposed_by` are left out before the count (`26d` 3)."""
        rows = self.toy_rows()
        proposed = edited(rows[3], {"row_id": "events-proposed", "proposed_by": "founder", "trust": "inferred",
                                    "derivation": "llm_inference"})
        for at in (len(rows), 2):  # after the PASS row, and before it
            with self.subTest(at=at):
                self.toy = self.make_toy(rows[:at] + [proposed] + rows[at:])
                lock = self.open()
                self.assertEqual(lock["pass_row_sha256"], hashlib.sha256(self.toy.line_of(3 + (at == 2))).hexdigest())
                self.stage_file().unlink()


class StageOpenNeedsTheMergesTest(StageOpenCase):
    """E405, `26d` 4 and 6, `asama-0/08` rounds 2 and 9: the PASS row comes after the toy's merge, and every copy row it
    names as a merge is one: an `events` row of `kind: merge`, the referee's own."""

    def test_the_pass_row_may_not_come_before_the_toys_merge(self):  # stage_open_pass_before_merge
        rows = self.toy_rows()
        for order, label in (([rows[0], rows[3], rows[1], rows[2], rows[4]], "PASS right after genesis"),
                             ([rows[0], rows[2], rows[3], rows[4]], "no merge at all"),
                             ([rows[0], edited(rows[1], {"proposed_by": "founder", "trust": "inferred",
                                                         "derivation": "llm_inference"}), rows[3]], "a proposed merge"),
                             ([rows[0], edited(rows[1], {"part": "cost"}), rows[3]], "a merge outside events"),
                             ([rows[0], edited(rows[1], {"kind": "decision"}), rows[3]], "another kind")):
            with self.subTest(label):
                self.toy = self.make_toy(order)
                self.refused("comes before the toy's merge")
        self.toy = self.make_toy([rows[0], rows[1], rows[3]])
        self.open()

    def test_each_named_copy_merge_is_a_merge_row(self):  # stage_open_copy_merge_any_row
        """The second skeptic: the copy's status row named as a merge passed (any later copy row did)."""
        status = self.copy.rows[2]
        self.assertEqual(status["kind"], "status")
        self.toy = self.make_toy(self.toy_rows(payload={"copy_merge_row_hashes": [status["row_hash"]]}))
        self.refused("each a merge row of the copy's ledger")
        self.toy = self.make_toy(self.toy_rows(payload={"copy_merge_row_hashes": [self.copy.rows[1]["row_hash"],
                                                                                status["row_hash"]]}))
        self.refused("each a merge row of the copy's ledger")
        proposed = edited(self.copy.rows[1], {"row_id": "events-merge-2", "proposed_by": "founder",
                                              "trust": "inferred", "derivation": "llm_inference"})
        proposed.pop("prev_hash"), proposed.pop("row_hash")
        self.copy = self.make_copy(self.copy_rows() + [proposed])
        self.toy = self.make_toy(self.toy_rows(payload={"copy_merge_row_hashes": [self.copy.rows[3]["row_hash"]]}))
        self.refused("each a merge row of the copy's ledger")
        # A proposal stays one with trust and derivation a referee row would have; and the copy's genesis, even of
        # kind merge, is no merge after the genesis (S6, the first skeptic's).
        merge = edited(self.copy_rows()[1], {"proposed_by": "founder"})
        self.copy = self.make_copy(self.copy_rows()[:1] + [merge])
        self.toy = self.make_toy(self.toy_rows(payload={"copy_merge_row_hashes": [self.copy.rows[1]["row_hash"]]}))
        self.refused("each a merge row of the copy's ledger")
        genesis = edited(self.copy_rows()[0], {"kind": "merge"})
        self.copy = self.make_copy([genesis] + self.copy_rows()[1:])
        self.toy = self.make_toy(self.toy_rows(payload={"copy_merge_row_hashes": [self.copy.rows[0]["row_hash"]]}))
        self.refused("each a merge row of the copy's ledger")
        self.toy = self.make_toy(self.toy_rows(payload={"copy_merge_row_hashes": [self.copy.rows[1]["row_hash"]]}))
        self.open()


class StageOpenNamesTheTransferTest(StageOpenCase):
    """E405, `26d` 5, `10a` #pass (the trust root includes the operator transfer): the PASS row names the counter's
    last transfer line, as the genesis rows do."""

    def test_a_pass_row_naming_another_transfer_or_none_is_refused(self):  # stage_open_pass_line_unchecked
        for value in ("9" * 64, DROP, self.line_sha.upper(), None):
            with self.subTest(value=value):
                self.toy = self.make_toy(self.toy_rows(payload={"import_line_sha256": value}))
                self.refused("the PASS row names another transfer")

    def test_a_reverted_later_transfer_that_wrote_the_pass_row_opens_nothing(self):
        """The second skeptic's residual: transfer 1 is in place and the genesis rows name it; a later transfer 2's
        referee wrote the PASS row, then transfer 2 was reverted, so the counter's last line is transfer 1's again.
        Its PASS row names transfer 2's line: the lock does not open on transfer 1."""
        second = self.import_rows[0] | {"ts": "2026-10-31T12:00:00Z", "brain_sha": "7" * 40}
        second.pop("prev_hash"), second.pop("row_hash")
        _rows, data = chained([edited(r, {"prev_hash": DROP, "row_hash": DROP}) for r in self.import_rows] + [second])
        reverted_line = hashlib.sha256(data.split(b"\n")[2]).hexdigest()  # transfer 2's line, now gone
        self.toy = self.make_toy(self.toy_rows(payload={"import_line_sha256": reverted_line}))
        self.refused("the PASS row names another transfer")


class PassRowPageTest(unittest.TestCase):
    """E404 (the second skeptic's N3): the PASS row is written by the Founder's code and read by `stage-open`, so its
    format is an interface fact the seed owes on a page the Founder reads (it never sees seed code). `tohum/26d` names
    every field, value and rule `stagelock` applies, and the pages that point at the PASS row point there."""

    @staticmethod
    def flat(name):
        return " ".join((ROOT / "spec" / name).read_text(encoding="utf-8").split())

    def test_26d_names_what_stage_open_reads(self):  # stage_open_observed_refused stage_open_merge_any_kind
        from snowball_bootstrap import decide as decide_module
        page = self.flat("tohum/26d-semalar-pass-satiri.md")
        source = Path(stagelock.__file__).read_text(encoding="utf-8")
        for field in ("import_line_sha256", "copy_genesis_row_hash", "copy_merge_row_hashes", "owner_exception"):
            self.assertIn(f"`{field}`", page)
            self.assertIn(f'"{field}"', source)
        for value in stagelock.REFEREE_TRUST + stagelock.REFEREE_DERIVATIONS:
            self.assertIn(f"`{value}`", page)
        self.assertEqual(stagelock.REFEREE_TRUST, ("verified", "observed"))  # `26`'s three but a proposal's `inferred`
        for words in ("`part: events`", "`stage`: tamsayı `0`", '`verdict`: dizgi `"PASS"`', "`proposed_by` taşımaz",
                      "`kind: merge`", "`proposed_by` taşıyan satırlar ayrıldıktan sonra", "ondan önce en az bir merge "
                      "satırı", "PASS satırı başka bir aktarımı adlandırıyorsa kilit açılmaz", "`hashedrekord`",
                      "`{algorithm: sha256, value: <kök>}`", "`sha256:<kök>`", "`pass_row_sha256`",
                      "`{anchor, stage, carry_to, reason, carry_commitment, measured}`",
                      f"`{decide_module.OWNER_EXCEPTABLE}`"):
            self.assertIn(words, page)
        lines = (ROOT / "spec" / "tohum" / "26d-semalar-pass-satiri.md").read_text(encoding="utf-8").splitlines()
        self.assertRegex(lines[2], r"^Tarih: \d{4}-\d\d-\d\d · Sürüm: [\d.]+ · Durum: \w+ · Sahibi: operatör$")
        index = (ROOT / "spec" / "INDEX.md").read_text(encoding="utf-8")
        self.assertIn(f"| `tohum/26d-semalar-pass-satiri.md` | {lines[0].removeprefix('# ')} | "
                      f"{lines[3].removeprefix('Okunma: ')} |", index)
        self.assertIn("PASS satırı ve kilidin açılışı `26d`'de", self.flat("tohum/26-semalar.md"))
        self.assertIn("`26b`, `26c`, `26d`", self.flat("tohum/26-semalar.md"))  # the sources of field names
        self.assertIn("PASS satırının alanları ve komutun kuralı `26d`", self.flat("tohum/25a-kurulum-etkinlestirme.md"))


# ---------------------------------------------------------------- the lock the bootstrap reads on every pull

class LockReadTest(StageOpenCase):
    def lock(self, **over):
        return lock_of(self.import_line, **over)

    def test_no_file_is_stage_0(self):
        self.assertIsNone(stagelock.load(self.referee))

    def test_the_file_is_read_strictly(self):  # lock_keys_unchecked lock_stage_unchecked lock_hex_unchecked
        """`26c`: a missing or unknown field fails closed; test 29: a transition that does not match is refused."""
        good = self.lock()
        cases = [dict(good, extra=1), {k: v for k, v in good.items() if k != "copy_state_head"},
                 dict(good, stage=2), dict(good, stage=True), dict(good, stage="1"), dict(good, stage=0),
                 dict(good, pass_row_sha256="X" * 64), dict(good, toy_state_head="2" * 39),
                 dict(good, import_line_sha256="4" * 64)]
        for case in cases:
            with self.subTest(case=case):
                write(self.referee, {"setup/stage.json": json.dumps(case)})
                with self.assertRaises(ConfigError):
                    stagelock.load(self.referee)
        write(self.referee, {"setup/stage.json": json.dumps(good)})
        self.assertEqual(stagelock.load(self.referee).stage, 1)

    def test_the_import_line_must_be_a_stage_0_transfer_of_a_sound_counter(self):  # lock_line_any_row lock_transfer_of_any_stage
        rows, data = chained([{"ts": "2026-10-31T08:30:00Z", "stage": 0}])
        write(self.referee, {"setup/imports.jsonl": data,
                             "setup/stage.json": json.dumps(lock_of(data.split(b"\n")[0]))})
        with self.assertRaises(ConfigError):  # names the touch row, not a transfer
            stagelock.load(self.referee)
        write(self.referee, {"setup/imports.jsonl": data.replace(b"08:30", b"08:31")})
        with self.assertRaises(ConfigError):  # the chain no longer holds
            stagelock.load(self.referee)
        _rows, batch = chained([{"ts": "2026-11-02T08:00:00Z", "stage": 1, "batch": "P1", "brain_sha": "5" * 40,
                                 "referee_tree_sha256": "6" * 64, "result_sha256": "7" * 64}])
        write(self.referee, {"setup/imports.jsonl": batch,  # Stage 1's own transfer
                             "setup/stage.json": json.dumps(lock_of(batch.split(b"\n")[0]))})
        with self.assertRaises(ConfigError):
            stagelock.load(self.referee)

    def test_a_later_batch_transfer_keeps_the_lock_and_is_read_as_done(self):  # lock_batches_unread
        """`asama-1/13`: the batches' transfers come after the lock; it still names its own line."""
        self.write_counter(later=[{"ts": "2026-11-02T08:00:00Z", "stage": 1, "batch": "P1", "brain_sha": "5" * 40,
                                   "referee_tree_sha256": "6" * 64, "result_sha256": "7" * 64}])
        write(self.referee, {"setup/stage.json": json.dumps(self.lock())})
        lock = stagelock.load(self.referee)
        self.assertEqual(lock.stage, 1)
        self.assertEqual(stagelock.batches_done(self.referee, lock), ("P1",))
        self.write_counter()
        self.assertEqual(stagelock.batches_done(self.referee, stagelock.load(self.referee)), ())

    def test_past_the_lock_only_the_stages_batch_transfers(self):  # lock_later_transfers_unchecked
        """A Stage 0 transfer after the lock's line, or a row of another stage or without its batch, stops the run."""
        for later in ({"stage": 0}, {"stage": 2, "batch": "P1"}, {"stage": 1}, {"stage": 1, "batch": "P 1"},
                      {"stage": True, "batch": "P1"}):
            with self.subTest(later=later):
                self.write_counter(later=[dict({"ts": "2026-11-02T08:00:00Z", "brain_sha": "5" * 40,
                                                "referee_tree_sha256": "6" * 64, "result_sha256": "7" * 64}, **later)])
                write(self.referee, {"setup/stage.json": json.dumps(self.lock())})
                with self.assertRaises(ConfigError) as caught:
                    stagelock.load(self.referee)
                self.assertIn("batch", str(caught.exception))

    def test_control_checks_the_lock_with_the_other_operator_files(self):  # lock_not_read_by_control
        referee = self.work / "ctl"
        shutil.copytree(self.referee, referee)
        write(referee, {
            "control.json": '{"kill_switch": false, "budget_state": "ok"}',
            "bootstrap.json": json.dumps({
                "brain_repo": "owner/brain", "brain_branch": "main",
                "image": "docker.io/library/python:3.12-slim@sha256:" + "a" * 64,
                "rival": {"model": "claude-sonnet-5-5", "effort": "medium", "max_turns": 30,
                          "per_run_cap_usd_micros": 3_000_000},
                "limits": {"test_timeout_s": 600, "reproducer_timeout_s": 120, "max_prompt_chars": 600_000,
                           "max_tree_bytes": 50_000_000}}),
            "policy.json": json.dumps({"constitutional": {
                "monthly_cap_usd": 300, "stage_params": {"rival_min_attempts": 2, "repeat_reject_limit": 3},
                "stage_budgets": {"asama_0": {"rival_usd": 30}},
                "license_allowlist": ["MIT"], "license_exceptions": {}}}),
            "setup/stage.json": json.dumps(self.lock(stage=2))})
        self.assertEqual(cli.main(["control", "--root", str(referee)]), 2)
        write(referee, {"setup/stage.json": json.dumps(self.lock())})
        self.assertEqual(cli.main(["control", "--root", str(referee)]), 0)


# ---------------------------------------------------------------- Stage 1's batch tables (E372, E378)

def batch_rows(name):
    """`asama-1/13`'s rows of batch ``name``: {MF: (tests, groups)}."""
    page = next((ROOT / "spec" / "asama-1").glob("13-*.md")).read_text(encoding="utf-8")
    rows = {}
    for line in page.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 5 and cells[0] == name and cells[1].isdigit():
            tests = [int(n) for n in cells[3].split(", ")] if re.fullmatch(r"[\d, ]+", cells[3]) else None
            groups = re.findall(r"`([a-z_]+)`", cells[4])
            rows[int(cells[1])] = (tests, groups)
    return rows


def page_batches():
    """The batches of `asama-1/13`'s micro-feature table, in the page's order."""
    page = next((ROOT / "spec" / "asama-1").glob("13-*.md")).read_text(encoding="utf-8")
    found = []
    for line in page.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 5 and cells[1].isdigit() and cells[0] not in found:
            found.append(cells[0])
    return found


class StageOneTableTest(unittest.TestCase):
    TABLE = stages.load(1)

    def test_the_table_is_the_p1_batchs_rows_of_asama_1_13(self):  # stage1_table_drifts
        """`asama-1/13` 1: the batch's table is in the seed and holds once `setup/stage.json` opened it. P1's comes
        first (`asama-1/06`: P1 ends before Stage 1's MF1 runs live). Tests and groups are the page's; module and calls
        are spec sessiz (E372)."""
        rows = batch_rows("P1")
        self.assertEqual(sorted(rows), list(range(1, 9)))
        self.assertEqual((self.TABLE.stage, self.TABLE.batch, self.TABLE.label), (1, "P1", "stage1-P1"))
        self.assertEqual({f.mf: (list(f.tests), list(f.groups)) for f in self.TABLE.mfs}, rows)

    def test_each_batch_is_a_table_of_its_own_in_the_pages_order(self):  # stage1_table_is_the_stages
        """E378, `26c:23` "Partilerin tabloları aynı dizindedir", `asama-1/06` "Partiler numarasızdır": a batch's table
        is named for its batch and numbers its own micro-features, so a later batch joins without renumbering; the
        batches the seed carries are the page's first ones, in its order, and no other table lies beside them."""
        order = page_batches()
        self.assertEqual(order[:2], ["P1", "P2"])
        self.assertEqual(list(stages.BATCHES[1]), order[:len(stages.BATCHES[1])])
        files = sorted(p.name for p in stages.STAGES_DIR.glob("*.json"))
        self.assertEqual(files, ["stage0.json"] + [stages.table_name(1, b) for b in stages.BATCHES[1]])
        data = json.loads((stages.STAGES_DIR / "stage1-P1.json").read_text(encoding="utf-8"))
        self.assertEqual((data["stage"], data["batch"]), (1, "P1"))
        with self.assertRaises(ConfigError):  # a batch table read as another batch's
            stages.parse_table(json.dumps(data), 1, "P2")
        with self.assertRaises(ConfigError):  # or as a stage table
            stages.parse_table(json.dumps(data), 1)

    def test_its_tests_are_section_09s_p1_tests_and_its_groups_the_seeds_p1_vectors(self):
        page = (ROOT / "spec" / "asama-0" / "09-harness-in-kendi-testleri.md").read_text(encoding="utf-8")
        p1 = {int(m.group(1)) for m in re.finditer(r"^\| (\d+) \| .* \| P1 \|$", page, re.M)}
        self.assertEqual({n for f in self.TABLE.mfs for n in f.tests}, p1)
        seed = json.loads((BOOT / "vectors" / "vectors.json").read_text(encoding="utf-8"))
        owned = {name for name, group in seed.items() if isinstance(group, dict) and group.get("owner") == "P1"}
        self.assertEqual({g for f in self.TABLE.mfs for g in f.groups}, owned)

    def test_stage_1_carries_stage_0_as_finished(self):  # stage0_groups_dropped_in_stage1 stage1_wiring_not_due
        """`asama-0/14`: a finished micro-feature's group runs on every later push; Stage 0's 18 are all finished once
        the lock opens, so every Stage 0 group runs with Stage 1's own, and the wiring check on every code push."""
        stage0 = stages.load(0)
        every0 = stage0.groups_of(range(1, stage0.count + 1))
        self.assertEqual(self.TABLE.groups_of(()), every0)
        self.assertEqual(self.TABLE.groups_of([4]), every0 + ("match", "cp_lower", "mcnemar"))
        self.assertEqual(stage0.groups_of(()), ())
        self.assertEqual([t.stage for t in self.TABLE.before], [0])
        self.assertTrue(wiring.due(self.TABLE, set()))
        self.assertFalse(wiring.due(stage0, set()))

    def test_a_transferred_batch_is_finished_and_the_next_one_holds(self):  # stage1_batches_done_ignored
        """E378: once the counter has P1's transfer, P1's micro-features are finished (its groups run, its tests stay
        declared) and the next batch's table holds; this seed carries none after P1, so none is open: `done_mf` is
        empty and Stage 1's own micro-features are the transferred referee's to judge (`asama-1/06`)."""
        after = stages.load(1, done=("P1",))
        self.assertEqual((after.stage, after.batch, after.count), (1, None, 0))
        self.assertEqual([t.label for t in after.before], ["stage0", "stage1-P1"])
        self.assertEqual(after.groups_of(()), self.TABLE.groups_of(range(1, 9)))
        for done in (("P2",), ("P1", "P1"), ("P1", "P2")):
            with self.subTest(done=done), self.assertRaises(ConfigError):
                stages.load(1, done=done)
        with self.assertRaises(ConfigError):
            stages.load(0, done=("P1",))

    def test_there_is_no_table_past_the_root(self):
        """`03`: Stage 1 is the ladder's fixed root; what follows is the Founder's stage spec, not a seed table."""
        with self.assertRaises(ConfigError):
            stages.load(2)


class StageOneManifestTest(unittest.TestCase):
    def manifest(self, stage0_mfs=range(1, 19), stage1_done=(), stage1_tests=None, drop=(), done=None):
        t0 = stages.load(0)
        tests = [{"id": f"T{n}", "cmd": f"t{n}", "stage": 0} for mf in stage0_mfs for n in t0.feature(mf).tests
                 if n not in drop]
        t1 = stages.load(1)
        numbers = stage1_tests if stage1_tests is not None else [n for mf in stage1_done for n in t1.feature(mf).tests]
        tests += [{"id": f"T{n}", "cmd": f"t{n}", "stage": 1} for n in numbers]
        return parse_manifest(json.dumps({"tests": tests, "done_mf": list(stage1_done if done is None else done),
                                          "lockfiles": []}))

    def test_done_mf_is_the_open_batchs_and_its_tests_are_stage_1_tests(self):  # stage1_tests_at_stage0
        table = stages.load(1)
        self.assertEqual(check_stage(self.manifest(), table), [])
        self.assertEqual(check_stage(self.manifest(stage1_done=[1, 2]), table), [])
        self.assertEqual(check_stage(self.manifest(stage1_done=[1, 2], stage1_tests=[51]), table),
                         ["missing_test:MF2:T8"])
        self.assertEqual(check_stage(self.manifest(stage1_done=range(1, 19), stage1_tests=[]), table),
                         ["done_mf_not_in_order"])  # Stage 0's done_mf kept: P1 has 8
        stage0_numbered = parse_manifest(json.dumps({"tests": [{"id": "T51", "cmd": "x", "stage": 0}] + [
            {"id": f"T{n}", "cmd": "x", "stage": 0} for f in stages.load(0).mfs for n in f.tests],
            "done_mf": [1], "lockfiles": []}))
        self.assertEqual(check_stage(stage0_numbered, table), ["missing_test:MF1:T51"])

    def test_stage_0s_tests_stay_declared(self):  # stage0_tests_dropped_in_stage1
        """E292's rule across the lock: Stage 0's micro-features stay finished, so their tests stay in the manifest."""
        self.assertEqual(check_stage(self.manifest(drop=(13,)), stages.load(1)), ["missing_test:stage0:MF1:T13"])

    def test_a_transferred_batchs_tests_stay_declared_and_done_mf_starts_again(self):  # stage1_batches_done_ignored
        """E378: under the table after P1's transfer, P1's tests stay declared at stage 1 (named by their table) and
        `done_mf` is the next table's, empty here."""
        after = stages.load(1, done=("P1",))
        self.assertEqual(check_stage(self.manifest(stage1_done=range(1, 9), done=[]), after), [])
        self.assertEqual(check_stage(self.manifest(stage1_done=range(1, 9)), after), ["done_mf_not_in_order"])
        self.assertEqual(check_stage(self.manifest(stage1_done=range(1, 9), stage1_tests=[51, 8], done=[]), after),
                         ["missing_test:stage1-P1:MF3:T2", "missing_test:stage1-P1:MF3:T4",
                          "missing_test:stage1-P1:MF4:T1", "missing_test:stage1-P1:MF4:T6",
                          "missing_test:stage1-P1:MF4:T7", "missing_test:stage1-P1:MF4:T12",
                          "missing_test:stage1-P1:MF4:T28", "missing_test:stage1-P1:MF5:T9",
                          "missing_test:stage1-P1:MF5:T11", "missing_test:stage1-P1:MF6:T24",
                          "missing_test:stage1-P1:MF7:T41", "missing_test:stage1-P1:MF8:T52"])

    def test_stage_0_is_judged_as_before(self):
        table = stages.load(0)
        m = parse_manifest(json.dumps({"tests": [{"id": "T13", "cmd": "x", "stage": 0}, {"id": "T51", "cmd": "y",
                                                                                         "stage": 1}],
                                       "done_mf": [1], "lockfiles": []}))
        self.assertEqual(check_stage(m, table), manifest_module.check_stage0(m))
        self.assertEqual(check_stage(m, table), [])
        only_later = parse_manifest(json.dumps({"tests": [{"id": "T51", "cmd": "y", "stage": 1}], "done_mf": [],
                                                "lockfiles": []}))
        self.assertEqual(check_stage(only_later, table), ["zero_tests"])  # a stage 1 test is not one yet


# ---------------------------------------------------------------- pull with the lock open

class StageOnePullTest(unittest.TestCase):
    """The bootstrap with `setup/stage.json` in place (`asama-0/10a` "Kilidin açılışı"): the Stage 1 tables and the
    `stage: 1` tests hold from then on."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.brain = base / "brain"
        self.seed_files = {"spec/tohum/00-cekirdek.md": "# core\n", "spec/asama-0/00-ozet.md": "# stage 0\n",
                           "spec/asama-1/00-ozet.md": "# stage 1\n",
                           "referee/.github/workflows/loop.yml": LOOP_YML,
                           "snowball-tests.json": self.manifest_text(stage1_done=())}
        make_repo(self.brain, {"README.md": "brain\n"})
        write(self.brain, self.seed_files)
        self.seed_sha = commit(self.brain, {}, "stage 0 exit")
        tar = gitio.archive(self.brain, self.seed_sha)
        self.referee = base / "referee"
        seed_hash = tree_hash(tar, "spec/tohum", forbid_operator_names=False)
        write(self.referee, {"setup/summary.json": json.dumps({"seed_commit": self.seed_sha,
                                                              "seed_tree_sha256": seed_hash})})
        write(self.referee, {
            "control.json": '{"kill_switch": false, "budget_state": "ok"}',
            "bootstrap.json": json.dumps({
                "brain_repo": "owner/brain", "brain_branch": "main",
                "image": "docker.io/library/python:3.12-slim@sha256:" + "a" * 64,
                "rival": {"model": "claude-sonnet-5-5", "effort": "medium", "max_turns": 30,
                          "per_run_cap_usd_micros": 3_000_000},
                "limits": {"test_timeout_s": 600, "reproducer_timeout_s": 120, "max_prompt_chars": 600_000,
                           "max_tree_bytes": 50_000_000}}),
            "policy.json": json.dumps({"constitutional": {
                "monthly_cap_usd": 300, "stage_params": {"rival_min_attempts": 2, "repeat_reject_limit": 3},
                "stage_budgets": {"asama_0": {"rival_usd": 30}},
                "license_allowlist": ["MIT", "Apache-2.0"], "license_exceptions": {}}})})
        self.write_counter()
        frozen = {d: tree_hash(tar, d, forbid_operator_names=False) for d in ("spec/asama-0", "spec/asama-1")}
        self.state = {"schema": "snowball-bootstrap-state/3", "origin": "artifact",
                      "last_accepted_sha": self.seed_sha, "last_evaluated_sha": None, "frozen_specs": frozen,
                      "rival_artifacts": [], "month": "2026-10", "month_spend_usd_micros": 0,
                      "stage_spend_usd_micros": 0, "runs": 9, "reject_streaks": {}, "repeat_events": 0,
                      "outage_sha": None, "outage_count": 0, "outage_since": None, "outage_stop": None,
                      "rival_side_streak": 0, "open_refutations": [], "open_claims": [], "pending_rival": None,
                      "rejected_exit_request": None}
        self.n = 0

    def write_counter(self, batches=()):
        """Stage 0's transfer, the lock naming it, and a transfer row for each of ``batches`` after it."""
        self.imports = locked(self.referee, self.seed_sha, batches)

    @staticmethod
    def manifest_text(stage1_done=(), p1_finished=False):
        """Every Stage 0 test at stage 0, and ``stage1_done``'s tests at stage 1 with it as `done_mf`; None: the
        manifest of Stage 0's exit, its 18 micro-features done. ``p1_finished``: every P1 test, `done_mf` empty."""
        t0, t1 = stages.load(0), stages.load(1)
        tests = [{"id": f"T{n}", "cmd": f"t{n}", "stage": 0} for f in t0.mfs for n in f.tests]
        if stage1_done is None:
            return json.dumps({"tests": tests, "done_mf": list(range(1, t0.count + 1)), "lockfiles": []})
        if p1_finished:
            tests += [{"id": f"T{n}", "cmd": f"t{n}", "stage": 1} for f in t1.mfs for n in f.tests]
            return json.dumps({"tests": tests, "done_mf": [], "lockfiles": []})
        tests += [{"id": f"T{n}", "cmd": f"t{n}", "stage": 1} for mf in stage1_done for n in t1.feature(mf).tests]
        return json.dumps({"tests": tests, "done_mf": list(stage1_done), "lockfiles": []})

    def pull(self, rc=0):
        self.n += 1
        state_path = Path(self.tmp.name) / f"state{self.n}.json"
        state_path.write_text(json.dumps(self.state))
        out = Path(self.tmp.name) / f"pulled{self.n}"
        got = cli.main(["pull", "--root", str(self.referee), "--state", str(state_path),
                        "--work", str(Path(self.tmp.name) / "work"), "--out", str(out), "--remote", str(self.brain)])
        self.assertEqual(got, rc)
        return json.loads((out / "meta.json").read_text(encoding="utf-8")) if rc == 0 else None

    def stage0_base(self):
        """The last accepted commit is still Stage 0's: its manifest declares Stage 0's 18 micro-features."""
        self.state["last_accepted_sha"] = commit(self.brain, {"snowball-tests.json": self.manifest_text(None)},
                                                 "stage 0's manifest")

    def ask(self, **request):
        """An exit request alone, naming the last accepted commit and the frozen spec ``request`` says."""
        req = dict({"stage": 1, "sha": self.state["last_accepted_sha"],
                    "spec_sha256": self.state["frozen_specs"]["spec/asama-1"], "batch": "P1"}, **request)
        commit(self.brain, {"exit-request.json": json.dumps({k: v for k, v in req.items() if v is not DROP})}, "exit")
        meta = self.pull()
        self.assertEqual(meta["kind"], "exit")
        return meta

    def test_the_first_stage_1_push_after_a_stage_0_base(self):  # stage_lock_never_read stage0_base_read_as_stage1
        """The base's `done_mf` is Stage 0's: nothing of Stage 1 is withdrawn, MF1's module-less red runs, and the
        stage reaches run-tests."""
        self.stage0_base()
        commit(self.brain, {"referee/runner/organs.py": "x = 1\n", "snowball-tests.json": self.manifest_text([1])},
               "P1 MF1")
        meta = self.pull()
        self.assertEqual((meta["kind"], meta["pre_reasons"], stagelock.open_table(self.referee).label),
                         ("code", [], "stage1-P1"))
        self.assertEqual((meta["module_less"], meta["run_tests"]), ([1], True))
        self.assertEqual({"stage", "batch", "batches_done"} & set(meta), set())  # the jobs read the lock themselves

    def test_a_stage_1_micro_feature_cannot_be_undeclared(self):
        self.state["last_accepted_sha"] = commit(self.brain, {"snowball-tests.json": self.manifest_text([1])}, "MF1")
        commit(self.brain, {"snowball-tests.json": self.manifest_text([])}, "undeclare")
        self.assertIn("done_mf_withdrawn:MF1", self.pull()["pre_reasons"])

    def test_stage_1s_tests_and_stage_0s_are_both_required(self):
        commit(self.brain, {"snowball-tests.json": json.dumps({"tests": [{"id": "T13", "cmd": "t", "stage": 0}],
                                                               "done_mf": [1], "lockfiles": []})}, "no T51")
        reasons = self.pull()["pre_reasons"]
        self.assertIn("missing_test:MF1:T51", reasons)
        self.assertIn("missing_test:stage0:MF2:T38", reasons)

    def test_stage_1s_spec_must_be_frozen(self):  # stage1_spec_not_required
        """`29b`, `02` 2-3: code is accepted under a frozen spec; in Stage 1 that is `spec/asama-1`'s, Stage 0's too."""
        for missing in ("spec/asama-1", "spec/asama-0"):
            with self.subTest(missing=missing):
                frozen = dict(self.state["frozen_specs"])
                del self.state["frozen_specs"][missing]
                commit(self.brain, {"referee/x.py": f"x = '{missing}'\n"}, "code")
                self.assertIn("spec_not_frozen", self.pull()["pre_reasons"])
                self.state["frozen_specs"] = frozen

    def test_a_stage_exit_request_is_the_wrong_stage(self):  # stage1_exit_judged_as_stage0
        """`02`: this seed judges only the Stage 0 exit; with the lock open that exit is behind, Stage 1's not yet
        judged here (E373)."""
        self.stage0_base()
        frozen = self.state["frozen_specs"]["spec/asama-0"]
        for stage in (0, 1):
            with self.subTest(stage=stage):
                meta = self.ask(stage=stage, spec_sha256=frozen, batch=DROP)
                self.assertIn("exit_request_wrong_stage", meta["pre_reasons"])

    def test_the_open_batchs_exit_request_is_judged(self):  # batch_exit_request_malformed batch_exit_wrong_stage_always
        """E378, `02` 6, `asama-1/13` 2, `26c:17`: the batch's request is the exit request's form with `batch`; for the
        open batch, on the last accepted commit and the frozen `spec/asama-1`, nothing in the request is refused."""
        meta = self.ask()
        self.assertEqual([r for r in meta["pre_reasons"] if r.startswith("exit_request")], [])
        self.assertEqual(meta["exit_request"]["batch"], "P1")
        self.assertIsNotNone(meta["referee_tree_sha256"])

    def test_a_batch_request_for_another_batch_stage_or_spec_is_refused(self):  # batch_exit_batch_unchecked batch_exit_spec_of_stage0
        for request, reason in (({"batch": "P2"}, "exit_request_wrong_batch"),
                                ({"stage": 0}, "exit_request_wrong_stage"),
                                ({"stage": 2}, "exit_request_wrong_stage"),
                                ({"spec_sha256": self.state["frozen_specs"]["spec/asama-0"]},
                                 "exit_request_spec_hash_mismatch"),
                                ({"batch": "P 1"}, "exit_request_malformed"), ({"batch": 1}, "exit_request_malformed"),
                                ({"batches": "P1"}, "exit_request_malformed")):
            with self.subTest(request=request):
                self.assertIn(reason, self.ask(**request)["pre_reasons"])
                self.state["last_evaluated_sha"] = None

    def test_without_the_lock_a_batch_request_is_malformed_as_it_always_was(self):  # stage0_batch_key_allowed
        """E402: before the lock the form is Stage 0's table's, which has no batch: a `batch` key is malformed, the
        request is not read (no pinned SHA), exactly as before the Stage 1 tooling (`test_stage0_unchanged`)."""
        (self.referee / "setup" / "stage.json").unlink()
        stage0 = self.state["frozen_specs"]["spec/asama-0"]  # batch_exit_stage0_batch: Stage 0 has no batches
        for request in ({}, {"stage": 0, "spec_sha256": stage0}):
            with self.subTest(request=request):
                meta = self.ask(**request)
                self.assertEqual((meta["pre_reasons"][:1], meta["exit_request"]), (["exit_request_malformed"], None))
                self.state["last_evaluated_sha"] = None

    def test_after_p1s_transfer_its_micro_features_are_finished(self):  # stage1_batches_done_ignored
        """E378: the counter's P1 transfer finishes P1: its tests stay declared, `done_mf` is the next table's (none in
        this seed), and a P1 request is the wrong batch."""
        self.write_counter(batches=("P1",))
        self.state["last_accepted_sha"] = commit(self.brain, {"snowball-tests.json": self.manifest_text(range(1, 9))},
                                                 "P1 done")
        commit(self.brain, {"referee/y.py": "y = 1\n", "snowball-tests.json": self.manifest_text(p1_finished=True)},
               "after P1")
        meta = self.pull()
        table = stagelock.open_table(self.referee)
        self.assertEqual((table.stage, table.batch, [b.label for b in table.before]), (1, None, ["stage0", "stage1-P1"]))
        self.assertEqual(meta["pre_reasons"], [])
        commit(self.brain, {"snowball-tests.json": self.manifest_text([])}, "P1's tests dropped")
        self.assertIn("missing_test:stage1-P1:MF1:T51", self.pull()["pre_reasons"])
        self.state["last_accepted_sha"] = sh(self.brain, "git", "rev-parse", "HEAD")
        self.assertIn("exit_request_wrong_batch", self.ask()["pre_reasons"])

    def test_the_wiring_is_checked_on_every_stage_1_code_push(self):
        commit(self.brain, {"referee/.github/workflows/loop.yml": "name: loop\n"}, "break the loop workflow")
        reasons = self.pull()["pre_reasons"]
        self.assertTrue(any(r.startswith("workflow_") for r in reasons), reasons)

    def test_a_lock_that_does_not_match_stops_the_run(self):  # lock_not_read_by_pull
        """Test 29 (`asama-0/09`): the transition is refused, the run stops for the operator (exit 2)."""
        lock = json.loads((self.referee / "setup" / "stage.json").read_text())
        write(self.referee, {"setup/stage.json": json.dumps(dict(lock, import_line_sha256="0" * 64))})
        commit(self.brain, {"referee/x.py": "x = 1\n"}, "code")
        self.pull(rc=2)

    def test_without_the_lock_the_stage_is_0(self):
        (self.referee / "setup" / "stage.json").unlink()
        self.stage0_base()
        commit(self.brain, {"referee/x.py": "x = 1\n"}, "code")
        meta = self.pull()
        self.assertEqual((stagelock.open_table(self.referee).label, "stage" in meta), ("stage0", False))
        self.assertNotIn("spec_not_frozen", meta["pre_reasons"])


# ---------------------------------------------------------------- the batch's (A) (`02` 6, `asama-1/13` 2, E378)

class BatchExitDecisionTest(unittest.TestCase):
    state = test_exit_checks.ExitDecision.state
    ok = staticmethod(test_exit_checks.ExitDecision.ok)

    def meta(self, done=range(1, 9), **request):
        meta = test_exit_checks.ExitDecision.meta(self, self.state(), self.ok())
        meta.update(manifest={"tests": [], "done_mf": list(done), "lockfiles": []},
                    exit_request=dict({"stage": 1, "sha": meta["base"], "spec_sha256": "e" * 64, "batch": "P1"},
                                      **request),
                    honesty_exception={"stage": 0, "carry_to": 1, "reason": "E287", "carry_commitment": "c" * 64})
        return meta

    def run_(self, meta, table=None):
        return decide(meta, {"controls": [], "tests": [{"id": "T51", "cmd_sha256": "c", "ok": True}], "vectors": [],
                             "licenses": [], "green": True}, None, None, {"getir": "success", "kos": "success"}, 2, 3,
                      table=table or stages.load(1))

    def test_the_open_batchs_request_is_transferable_and_names_its_batch(self):  # batch_exit_takes_the_stage_conditions batch_exit_unnamed
        """The narrow form: the batch's own micro-features, the tests, vectors and rival, the archive's checks of the
        tree; the stage's own conditions (#spec, #durustluk) and the owner's exception are the stage exit's."""
        res = self.run_(self.meta())
        self.assertEqual((res["verdict"], res["exit"]["transferable"], res["exit"]["missing"]), ("accepted", True, []))
        self.assertEqual((res["exit"]["stage"], res["exit"]["batch"]), (1, "P1"))
        self.assertNotIn("owner_exception", res["exit"])

    def test_every_micro_feature_of_the_batch_must_be_done(self):
        res = self.run_(self.meta(done=range(1, 8)))
        self.assertEqual(res["exit"]["missing"], ["not_all_micro_features_done"])
        self.assertNotIn("batch", res["exit"])
        res = self.run_(self.meta(), table=stages.load(0))  # judged under Stage 0's 18: not done
        self.assertIn("not_all_micro_features_done", res["exit"]["missing"])

    def test_the_archives_checks_still_hold(self):
        meta = self.meta()
        meta["exit_checks"]["agac"] = {"status": "failed", "reasons": ["agent_config_in_referee:referee/CLAUDE.md"],
                                       "why": ""}
        res = self.run_(meta)
        self.assertEqual(res["exit"]["missing"], ["agent_config_in_referee:referee/CLAUDE.md"])

    def test_the_exits_form_is_the_open_tables_not_the_requests(self):  # batch_form_from_the_request
        """E402: under Stage 0's table every request is Stage 0's exit, one that carries `batch` too: the stage's own
        conditions and the owner's exception stay, nothing names a batch. Under the lock the open batch's form holds
        whatever the request says (`pull` refuses a request that is not the open batch's)."""
        for request in ({}, {"batch": DROP}, {"stage": 0, "batch": "P1"}):
            with self.subTest(table="stage0", request=request):
                meta = self.meta()
                meta["exit_request"] = edited(meta["exit_request"], request)
                res = self.run_(meta, table=stages.load(0))
                self.assertIn("not_checked:spec", res["exit"]["missing"])
                self.assertEqual(res["exit"]["owner_exception"]["anchor"], "durustluk")
                self.assertEqual({"stage", "batch"} & set(res["exit"]), set())
            with self.subTest(table="stage1-P1", request=request):
                res = self.run_(meta, table=stages.load(1))
                self.assertEqual((res["verdict"], res["exit"]["batch"]), ("accepted", "P1"))
                self.assertNotIn("owner_exception", res["exit"])

    def test_the_decide_command_judges_under_the_table_pull_named(self):  # decide_reads_stage0_table
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        work = Path(tmp.name)
        write(work / "root", {"policy.json": json.dumps({"constitutional": {
            "monthly_cap_usd": 300, "stage_params": {"rival_min_attempts": 2, "repeat_reject_limit": 3},
            "stage_budgets": {"asama_0": {"rival_usd": 30}}, "license_allowlist": ["MIT"], "license_exceptions": {}}})})
        write(work / "pulled", {"meta.json": json.dumps(self.meta())})
        write(work / "run", {"run.json": json.dumps({"controls": [], "tests": [{"id": "T51", "cmd_sha256": "c",
                                                                                "ok": True}],
                                                     "vectors": [], "licenses": [], "green": True})})
        argv = ["decide", "--root", str(work / "root"), "--pulled", str(work / "pulled"), "--run", str(work / "run"),
                "--out", str(work / "out"), "--job", "getir=success", "--job", "kos=success"]
        # No lock in the snapshot: Stage 0's table, whatever the meta says of a stage (E402).
        write(work / "pulled", {"meta.json": json.dumps(dict(self.meta(), stage=1, batch="P1", batches_done=[]))})
        self.assertEqual(cli.main(argv), 0)
        result = json.loads((work / "out" / "result.json").read_text(encoding="utf-8"))
        self.assertEqual(result["exit"]["transferable"], False)
        self.assertIn("not_all_micro_features_done", result["exit"]["missing"])
        locked(work / "root")  # the lock the snapshot carries: P1 is the open batch
        self.assertEqual(cli.main(argv), 0)
        result = json.loads((work / "out" / "result.json").read_text(encoding="utf-8"))
        self.assertEqual((result["exit"]["transferable"], result["exit"]["batch"]), (True, "P1"))
        locked(work / "root", batches=("P1",))  # P1 transferred: none of this seed's batches is open
        self.assertEqual(cli.main(argv), 0)
        result = json.loads((work / "out" / "result.json").read_text(encoding="utf-8"))
        self.assertEqual((result["exit"]["transferable"], "batch" in result["exit"]), (False, False))


class StageOneRunTestsTest(unittest.TestCase):
    def test_stage_0_and_stage_1_tests_run_and_module_less_red_reads_stage_1s(self):  # stage1_tests_not_run run_tests_stage_ignored
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        work = Path(tmp.name)
        referee = work / "referee"
        shutil.copytree(BOOT / "vectors", referee / "vectors")
        write(referee, {"bootstrap.json": json.dumps({
            "brain_repo": "owner/brain", "brain_branch": "main",
            "image": "docker.io/library/python:3.12-slim@sha256:" + "a" * 64,
            "rival": {"model": "claude-sonnet-5-5", "effort": "medium", "max_turns": 30, "per_run_cap_usd_micros": 1},
            "limits": {"test_timeout_s": 60, "reproducer_timeout_s": 60, "max_prompt_chars": 1000,
                       "max_tree_bytes": 50_000_000}}),
            "policy.json": json.dumps({"constitutional": {
                "monthly_cap_usd": 300, "stage_params": {"rival_min_attempts": 2, "repeat_reject_limit": 3},
                "stage_budgets": {"asama_0": {"rival_usd": 30}}, "license_allowlist": ["MIT"],
                "license_exceptions": {}}})})
        src = work / "tree"
        write(src, {"referee/runner/organs.py": "x\n", "referee/other.py": "y\n"})
        pulled = work / "pulled"
        pulled.mkdir()
        cli.pack_dir(src, pulled / "brain.tar")
        manifest = {"tests": [{"id": "T13", "cmd": "t13", "stage": 0}, {"id": "T51", "cmd": "t51", "stage": 1},
                              {"id": "T60", "cmd": "t60", "stage": 2}], "done_mf": [1], "lockfiles": []}
        (pulled / "meta.json").write_text(json.dumps({"manifest": manifest, "module_less": [1]}))
        locked(referee)  # the snapshot's lock opened Stage 1: P1's table, its `stage: 1` tests
        deps = work / "deps"
        deps.mkdir()
        calls, trees = [], []

        class Runner(FakeRunner):
            def run(self, cmd, **kw):
                if cmd in ("t13", "t51", "t60"):
                    calls.append((cmd, self.src))
                    present = (self.src / "referee" / "runner" / "organs.py").exists()
                    return RunResult(0 if present else 1, b"", b"", 1)
                return super().run(cmd, **kw)

        def make(boot, tree, *a, **k):
            runner = Runner(referee / "vectors")
            runner.src = Path(tree)
            trees.append(Path(tree))
            return runner
        with mock.patch.object(cli, "_runner", side_effect=make):
            rc = cli.main(["run-tests", "--root", str(referee), "--pulled", str(pulled), "--deps", str(deps),
                           "--work", str(work / "work"), "--out", str(work / "run")])
        self.assertEqual(rc, 0)
        run = json.loads((work / "run" / "run.json").read_text())
        self.assertEqual([t["id"] for t in run["tests"]], ["T13", "T51"])  # a stage 2 test is not one yet
        self.assertEqual([(m["mf"], m["test_id"], m["module"], m["stayed_green"]) for m in run["module_less"]],
                         [(1, "T51", "referee/runner/organs.py", False)])


class WorkflowReadsTheLockTest(unittest.TestCase):
    def test_the_snapshot_carries_the_lock_and_the_counter_when_they_exist(self):  # workflow_drops_the_lock
        """`asama-0/10a`: the bootstrap reads `setup/stage.json` on every pull, so the snapshot the jobs read holds it
        and the counter it is bound to; before the import neither exists and the snapshot is as before."""
        workflow = (BOOT / "workflow" / "bootstrap.yml").read_text(encoding="utf-8")
        step = workflow[workflow.index("name: Snapshot operator files"):workflow.index("name: Kill switch and operator")]
        for name in ("stage.json", "imports.jsonl"):
            self.assertIn(f"if [ -e referee/setup/{name} ]; then cp referee/setup/{name} snap/setup/; fi", step)

    @posix_only
    def test_the_snapshot_step_run_copies_the_lock_and_the_counter(self):  # workflow_drops_the_lock
        """E389: the step itself, run as the job runs it, over a referee checkout with and without the two files."""
        workflow = (BOOT / "workflow" / "bootstrap.yml").read_text(encoding="utf-8")
        block = workflow[workflow.index("name: Snapshot operator files"):workflow.index("name: Kill switch and operator")]
        lines = block.splitlines()[2:]  # past the name and `run: |`
        script = "\n".join(line[10:] for line in lines if line.startswith(" " * 10)) + "\n"
        operator = {"bootstrap/x.py": "x\n", "vectors/v.json": "{}\n", "seats/s.md": "s\n", "bootstrap.json": "{}\n",
                    "control.json": "{}\n", "policy.json": "{}\n", "setup/summary.json": "{}\n"}
        for present in (False, True):
            with self.subTest(present=present), tempfile.TemporaryDirectory() as tmp:
                work = Path(tmp)
                write(work / "referee", operator)
                if present:
                    write(work / "referee", {"setup/stage.json": "{\"stage\": 1}\n", "setup/imports.jsonl": "{}\n"})
                (work / "step.sh").write_text("set -e\n" + script, encoding="utf-8")
                self.assertEqual(sh(work, "sh", "step.sh"), "")
                snapped = sorted(p.name for p in (work / "snap" / "setup").iterdir())
                self.assertEqual(snapped, ["imports.jsonl", "stage.json", "summary.json"] if present else ["summary.json"])


if __name__ == "__main__":
    unittest.main()
