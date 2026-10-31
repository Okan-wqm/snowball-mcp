"""The operator's activation tools (`tohum/25a` 1, 2 and 9; `asama-0/10a` #aktarim, #oyuncak, "Kilidin açılışı"; `26c`):
the import (K1 of `seed/founder/ETKINLESTIRME.md`: E100, E275, E370), `stage-open`, the stage lock the bootstrap reads on
every pull and the Stage 1 table (K3: E331, E371-E373).

Nothing here signs or verifies with Sigstore: the seed's one call into it (`importer.verify_signature`) is replaced by a
recorder, as `test_flow` and `test_exit_checks` do. Every git repository is a local one.
"""

import base64
import hashlib
import json
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
from snowball_bootstrap.importer import ImportErrorStop, run_import
from snowball_bootstrap.manifest import check_stage, parse_manifest
from snowball_bootstrap.treehash import TreeError, tree_hash

from helpers import LOOP_YML, FakeRunner, commit, make_repo, sh
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
        """Spec sessiz (E370): this seed signs no transferable result after Stage 0, so with `setup/stage.json` in
        place the result in hand is Stage 0's, and the lock it opened is not undone by importing it again."""
        write(self.referee, {"setup/stage.json": "{}\n"})
        before = read_all(self.referee)
        with self.assertRaises(ImportErrorStop):
            self.run_import()
        self.assert_nothing_written(before)


# ---------------------------------------------------------------- stage-open

class Target:
    """A target repository whose `brain/state` holds a ledger and a root chain, as the loop referee writes them."""

    def __init__(self, path, rows, root_override=None):
        self.path = path
        make_repo(path, {"README.md": "main\n"})
        sh(path, "git", "checkout", "-q", "--orphan", "brain/state")
        sh(path, "git", "rm", "-q", "-rf", ".")
        self.rows, self.ledger = chained(rows)
        tips = {}
        for row in self.rows:
            tips[row["part"]] = row["row_hash"]
        self.root = root_override or hashlib.sha256(canonical(tips)).hexdigest()
        self.body = json.dumps({"kind": "hashedrekord", "spec": {"root": self.root, "at": str(path)}}).encode()
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


TOY_ROWS = [event("genesis", {"target": "toy"}), event("merge", {"c": 1}), event("cost", {"usd": 1}, part="cost"),
            event("pass", {"stage": 0, "verdict": "PASS", "copy_rows": ["x"]}), event("status", {"b": 2})]
COPY_ROWS = [event("genesis", {"target": "copy"}), event("merge", {"c": 2})]


class StageOpenCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name)
        self.referee = self.work / "referee"
        write(self.referee, OPERATOR_FILES)
        write(self.referee, {"setup/summary.json": json.dumps({"seed_commit": "a" * 40, "seed_tree_sha256": "b" * 64})})
        self.import_rows, data = chained([
            {"ts": "2026-10-31T08:00:00Z", "stage": 0, "brain_sha": "c" * 40, "referee_tree_sha256": "d" * 64,
             "result_sha256": "e" * 64, "toy_tree_sha256": "f" * 64},
            {"ts": "2026-10-31T08:30:00Z", "stage": 0}])  # a touch that is no transfer (`29n`) comes after it
        write(self.referee, {"setup/imports.jsonl": data})
        self.import_line = data.split(b"\n")[0]
        self.made = 0
        self.toy = Target(self.fresh("toy"), TOY_ROWS)
        self.copy = Target(self.fresh("copy"), COPY_ROWS)
        self.verified = []

        def verify(artifact, bundle, identity, sigstore_python):
            self.verified.append((Path(artifact).read_bytes(), Path(bundle), identity, sigstore_python))
        patcher = mock.patch.object(importer, "verify_signature", side_effect=verify)
        patcher.start()
        self.addCleanup(patcher.stop)

    def fresh(self, name):
        """A new directory for a target (a git repository's objects are read-only on Windows: none is removed)."""
        self.made += 1
        return self.work / f"{name}{self.made}"

    def argv(self, **over):
        args = {"--referee": self.referee, "--toy": self.toy.path, "--copy": self.copy.path,
                "--ref": "refs/heads/brain/state", "--identity": "loop-id", "--sigstore-python": "py",
                "--toy-root-bundle": self.toy.bundle, "--copy-root-bundle": self.copy.bundle}
        args.update(over)
        return ["stage-open"] + [str(x) for pair in args.items() for x in pair]

    def open(self):
        return stagelock.open_stage(self.referee, self.toy.path, self.copy.path, "refs/heads/brain/state", "loop-id",
                                    "py", self.toy.bundle, self.copy.bundle)

    def stage_file(self):
        return self.referee / "setup" / "stage.json"


class StageOpenWritesTest(StageOpenCase):
    def test_the_lock_is_26cs_five_fields_and_nothing_else(self):
        """`asama-0/10a`, `26c:40-41`, `25a` 9: `{stage: 1, pass_row_sha256, toy_state_head, copy_state_head,
        import_line_sha256}`, the hashes of the PASS line and the last transfer line without their LF (`29o`)."""
        self.assertEqual(cli.main(self.argv()), 0)
        lock = json.loads(self.stage_file().read_text(encoding="utf-8"))
        self.assertEqual(lock, {"stage": 1, "pass_row_sha256": hashlib.sha256(self.toy.line_of(3)).hexdigest(),
                                "toy_state_head": self.toy.head, "copy_state_head": self.copy.head,
                                "import_line_sha256": hashlib.sha256(self.import_line).hexdigest()})
        self.assertEqual(self.stage_file().read_bytes(), canon.dump(lock).encode("utf-8"))  # LF, sorted, readable
        self.assertEqual(stagelock.load(self.referee), stagelock.Lock(**lock))  # what the bootstrap then reads

    def test_each_targets_last_root_is_verified_with_sigstore_as_the_root_itself(self):  # stage_open_root_not_signed
        self.open()
        self.assertEqual(self.verified, [(self.toy.root.encode("ascii"), self.toy.bundle, "loop-id", "py"),
                                         (self.copy.root.encode("ascii"), self.copy.bundle, "loop-id", "py")])

    def test_stage_open_is_a_command_the_operator_can_ask_for_help(self):
        with self.assertRaises(SystemExit) as caught:
            cli.build_parser().parse_args(["stage-open", "--help"])
        self.assertEqual(caught.exception.code, 0)


class StageOpenRefusesTest(StageOpenCase):
    def refused(self, says):
        with self.assertRaises((ConfigError, ImportErrorStop, gitio.GitError)) as caught:
            self.open()
        self.assertIn(says, str(caught.exception))
        self.assertFalse(self.stage_file().exists())

    def test_without_an_accepted_transferable_import(self):  # stage_open_without_a_transfer
        """Only a transfer (a row with `referee_tree_sha256`, `29o`) of Stage 0 opens Stage 1."""
        for rows in ([{"ts": "2026-10-31T08:30:00Z", "stage": 0}],
                     [{"ts": "2026-10-31T08:00:00Z", "stage": 1, "brain_sha": "c" * 40, "referee_tree_sha256": "d" * 64,
                       "result_sha256": "e" * 64}]):
            with self.subTest(rows=rows):
                write(self.referee, {"setup/imports.jsonl": chained(rows)[1]})
                self.refused("transfer")
        (self.referee / "setup" / "imports.jsonl").unlink()
        self.refused("imports.jsonl")

    def test_with_a_broken_counter(self):  # stage_open_counter_unchained
        data = (self.referee / "setup" / "imports.jsonl").read_bytes()
        write(self.referee, {"setup/imports.jsonl": data.replace(b'"stage":0', b'"stage":3', 1)})
        self.refused("imports.jsonl")

    def test_without_the_pass_row(self):  # stage_open_without_pass
        for rows, says in ((TOY_ROWS[:3], "no PASS row"),
                           ([event("pass", {"stage": 0, "verdict": "FAIL"})], "no PASS row"),
                           ([event("pass", {"stage": 1, "verdict": "PASS"})], "no PASS row"),
                           ([event("pass", {"stage": False, "verdict": "PASS"})], "no PASS row"),
                           ([event("pass", {"stage": 0, "verdict": "PASS"}, part="drill")], "no PASS row"),
                           ([event("pass", {"stage": 0, "verdict": "PASS"}), event("pass2", {"stage": 0, "verdict": "PASS"})],
                            "2 PASS rows")):
            with self.subTest(rows=[r["payload"] for r in rows]):
                self.toy = Target(self.fresh("toy"), rows)
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
        self.copy = Target(self.fresh("copy"), COPY_ROWS, root_override="9" * 64)
        self.refused("copy")

    def test_when_the_root_bundle_is_not_the_root_rows_log_entry(self):  # stage_open_bundle_any_entry
        other = json.loads(self.copy.bundle.read_text())
        self.toy.bundle.write_text(json.dumps(other))
        self.refused("rekor_uuid")

    def test_when_sigstore_refuses_the_root(self):
        importer.verify_signature.side_effect = ImportErrorStop("signature verification failed: no")
        self.refused("signature verification failed")

    def test_without_the_targets_state_branch(self):
        self.copy = Target(self.fresh("copy"), COPY_ROWS)
        sh(self.copy.path, "git", "branch", "-q", "-D", "brain/state")
        self.refused("brain/state")

    def test_when_the_lock_is_already_open(self):  # stage_open_overwrites
        write(self.referee, {"setup/stage.json": '{"stage": 1}\n'})
        with self.assertRaises(ConfigError):
            self.open()
        self.assertEqual(self.stage_file().read_text(), '{"stage": 1}\n')

    def test_an_owner_exception_must_ride_on_the_pass_row(self):  # stage_open_owner_exception_unchecked
        """`02` "Sahip istisnası", E294, E331: the PASS row carries the exception by its name."""
        summary = {"seed_commit": "a" * 40, "seed_tree_sha256": "b" * 64,
                   "honesty_exception": {"stage": 0, "carry_to": 1, "reason": "E287"}, "honesty_commitment": "c" * 64}
        write(self.referee, {"setup/summary.json": json.dumps(summary)})
        self.refused("owner_exception")
        rows = TOY_ROWS[:3] + [event("pass", {"stage": 0, "verdict": "PASS",
                                              "owner_exception": {"anchor": "durustluk"}})]
        self.toy = Target(self.fresh("toy"), rows)
        self.open()
        self.assertTrue(self.stage_file().exists())

    def test_the_excepted_anchor_is_the_one_the_signed_result_names(self):
        from snowball_bootstrap import decide
        self.assertEqual(stagelock.EXCEPTED_ANCHOR, decide.OWNER_EXCEPTABLE)


# ---------------------------------------------------------------- the lock the bootstrap reads on every pull

class LockReadTest(StageOpenCase):
    def lock(self, **over):
        lock = {"stage": 1, "pass_row_sha256": "1" * 64, "toy_state_head": "2" * 40, "copy_state_head": "3" * 40,
                "import_line_sha256": hashlib.sha256(self.import_line).hexdigest()}
        lock.update(over)
        return lock

    def test_no_file_is_stage_0(self):
        self.assertIsNone(stagelock.load(self.referee))

    def test_the_file_is_read_strictly(self):  # lock_keys_unchecked lock_stage_unchecked
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

    def test_the_import_line_must_be_a_stage_0_transfer_of_a_sound_counter(self):  # lock_line_any_row
        rows, data = chained([{"ts": "2026-10-31T08:30:00Z", "stage": 0}])
        write(self.referee, {"setup/imports.jsonl": data,
                             "setup/stage.json": json.dumps(self.lock(import_line_sha256=hashlib.sha256(
                                 data.split(b"\n")[0]).hexdigest()))})
        with self.assertRaises(ConfigError):  # names the touch row, not a transfer
            stagelock.load(self.referee)
        write(self.referee, {"setup/imports.jsonl": data.replace(b"08:30", b"08:31")})
        with self.assertRaises(ConfigError):  # the chain no longer holds
            stagelock.load(self.referee)
        _rows, batch = chained([{"ts": "2026-11-02T08:00:00Z", "stage": 1, "batch": "P1", "brain_sha": "5" * 40,
                                 "referee_tree_sha256": "6" * 64, "result_sha256": "7" * 64}])
        write(self.referee, {"setup/imports.jsonl": batch,  # lock_transfer_of_any_stage: Stage 1's own transfer
                             "setup/stage.json": json.dumps(self.lock(import_line_sha256=hashlib.sha256(
                                 batch.split(b"\n")[0]).hexdigest()))})
        with self.assertRaises(ConfigError):
            stagelock.load(self.referee)

    def test_a_later_batch_transfer_keeps_the_lock(self):
        """`asama-1/13`: the batches' transfers come after the lock; it still names its own line."""
        later = dict(self.import_rows[-1])
        rows = self.import_rows + [{"ts": "2026-11-02T08:00:00Z", "stage": 1, "batch": "P1", "brain_sha": "5" * 40,
                                    "referee_tree_sha256": "6" * 64, "result_sha256": "7" * 64,
                                    "prev_hash": later["row_hash"]}]
        rows[-1]["row_hash"] = row_hash(rows[-1])
        data = b"".join(json.dumps(r, separators=(",", ":")).encode() + b"\n" for r in rows)
        write(self.referee, {"setup/imports.jsonl": data, "setup/stage.json": json.dumps(self.lock())})
        self.assertEqual(stagelock.load(self.referee).stage, 1)

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


# ---------------------------------------------------------------- the Stage 1 table

def p1_rows():
    """`asama-1/13`'s P1 rows: {MF: (tests, groups)}."""
    page = next((ROOT / "spec" / "asama-1").glob("13-*.md")).read_text(encoding="utf-8")
    rows = {}
    for line in page.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 5 and cells[0] == "P1" and cells[1].isdigit():
            tests = [int(n) for n in cells[3].split(", ")]
            groups = re.findall(r"`([a-z_]+)`", cells[4])
            rows[int(cells[1])] = (tests, groups)
    return rows


class StageOneTableTest(unittest.TestCase):
    TABLE = stages.load(1)

    def test_the_table_is_the_p1_batchs_rows_of_asama_1_13(self):  # stage1_table_drifts
        """`asama-1/13` 1: the batch's table is in the seed and holds once `setup/stage.json` opened it. P1's rows come
        first (`asama-1/06`: P1 ends before Stage 1's MF1 runs live); P2's and the exit batch's join in later seed
        epochs (E373). Tests and groups are the page's; module and calls are spec sessiz (E372)."""
        rows = p1_rows()
        self.assertEqual(sorted(rows), list(range(1, 9)))
        self.assertEqual(self.TABLE.stage, 1)
        self.assertEqual({f.mf: (list(f.tests), list(f.groups)) for f in self.TABLE.mfs}, rows)

    def test_its_tests_are_section_09s_p1_tests_and_its_groups_the_seeds_p1_vectors(self):
        page = (ROOT / "spec" / "asama-0" / "09-harness-in-kendi-testleri.md").read_text(encoding="utf-8")
        p1 = {int(m.group(1)) for m in re.finditer(r"^\| (\d+) \| .* \| P1 \|$", page, re.M)}
        self.assertEqual({n for f in self.TABLE.mfs for n in f.tests}, p1)
        seed = json.loads((BOOT / "vectors" / "vectors.json").read_text(encoding="utf-8"))
        owned = {name for name, group in seed.items() if isinstance(group, dict) and group.get("owner") == "P1"}
        self.assertEqual({g for f in self.TABLE.mfs for g in f.groups}, owned)

    def test_stage_1_carries_stage_0_as_finished(self):  # stage0_groups_dropped_in_stage1
        """`asama-0/14`: a finished MF's group runs on every later push; Stage 0's 18 are all finished once the lock
        opens, so every Stage 0 group runs with Stage 1's own, and the wiring check on every code push."""
        stage0 = stages.load(0)
        every0 = stage0.groups_of(range(1, stage0.count + 1))
        self.assertEqual(self.TABLE.groups_of(()), every0)
        self.assertEqual(self.TABLE.groups_of([4]), every0 + ("match", "cp_lower", "mcnemar"))
        self.assertEqual(stage0.groups_of(()), ())
        self.assertEqual([t.stage for t in self.TABLE.before], [0])
        self.assertTrue(wiring.due(self.TABLE, set()))
        self.assertFalse(wiring.due(stage0, set()))

    def test_there_is_no_table_past_the_root(self):
        """`03`: Stage 1 is the ladder's fixed root; what follows is the Founder's stage spec, not a seed table."""
        with self.assertRaises(ConfigError):
            stages.load(2)


class StageOneManifestTest(unittest.TestCase):
    def manifest(self, stage0_mfs=range(1, 19), stage1_done=(), stage1_tests=None, drop=()):
        t0 = stages.load(0)
        tests = [{"id": f"T{n}", "cmd": f"t{n}", "stage": 0} for mf in stage0_mfs for n in t0.feature(mf).tests
                 if n not in drop]
        t1 = stages.load(1)
        numbers = stage1_tests if stage1_tests is not None else [n for mf in stage1_done for n in t1.feature(mf).tests]
        tests += [{"id": f"T{n}", "cmd": f"t{n}", "stage": 1} for n in numbers]
        return parse_manifest(json.dumps({"tests": tests, "done_mf": list(stage1_done), "lockfiles": []}))

    def test_done_mf_is_stage_1s_and_its_tests_are_stage_1_tests(self):  # stage1_tests_at_stage0
        table = stages.load(1)
        self.assertEqual(check_stage(self.manifest(), table), [])
        self.assertEqual(check_stage(self.manifest(stage1_done=[1, 2]), table), [])
        self.assertEqual(check_stage(self.manifest(stage1_done=[1, 2], stage1_tests=[51]), table),
                         ["missing_test:MF2:T8"])
        self.assertEqual(check_stage(self.manifest(stage1_done=range(1, 19), stage1_tests=[]), table),
                         ["done_mf_not_in_order"])  # Stage 0's done_mf kept: Stage 1 has 8
        stage0_numbered = parse_manifest(json.dumps({"tests": [{"id": "T51", "cmd": "x", "stage": 0}] + [
            {"id": f"T{n}", "cmd": "x", "stage": 0} for f in stages.load(0).mfs for n in f.tests],
            "done_mf": [1], "lockfiles": []}))
        self.assertEqual(check_stage(stage0_numbered, table), ["missing_test:MF1:T51"])

    def test_stage_0s_tests_stay_declared(self):  # stage0_tests_dropped_in_stage1
        """E292's rule across the lock: Stage 0's micro-features stay finished, so their tests stay in the manifest."""
        self.assertEqual(check_stage(self.manifest(drop=(13,)), stages.load(1)), ["missing_test:stage0:MF1:T13"])

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
    """The bootstrap with `setup/stage.json` in place (`asama-0/10a` "Kilidin açılışı"): the Stage 1 table and the
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
        self.imports, data = chained([{"ts": "2026-10-31T08:00:00Z", "stage": 0, "brain_sha": self.seed_sha,
                                       "referee_tree_sha256": "d" * 64, "result_sha256": "e" * 64,
                                       "toy_tree_sha256": "f" * 64}])
        write(self.referee, {"setup/imports.jsonl": data, "setup/stage.json": json.dumps({
            "stage": 1, "pass_row_sha256": "1" * 64, "toy_state_head": "2" * 40, "copy_state_head": "3" * 40,
            "import_line_sha256": hashlib.sha256(data.split(b"\n")[0]).hexdigest()})})
        frozen = {d: tree_hash(tar, d, forbid_operator_names=False) for d in ("spec/asama-0", "spec/asama-1")}
        self.state = {"schema": "snowball-bootstrap-state/3", "origin": "artifact",
                      "last_accepted_sha": self.seed_sha, "last_evaluated_sha": None, "frozen_specs": frozen,
                      "rival_artifacts": [], "month": "2026-10", "month_spend_usd_micros": 0,
                      "stage_spend_usd_micros": 0, "runs": 9, "reject_streaks": {}, "repeat_events": 0,
                      "outage_sha": None, "outage_count": 0, "outage_since": None, "outage_stop": None,
                      "rival_side_streak": 0, "open_refutations": [], "open_claims": [], "pending_rival": None,
                      "rejected_exit_request": None}
        self.n = 0

    @staticmethod
    def manifest_text(stage1_done=()):
        """Every Stage 0 test at stage 0, and ``stage1_done``'s tests at stage 1 with it as `done_mf`; None: the
        manifest of Stage 0's exit, its 18 micro-features done."""
        t0, t1 = stages.load(0), stages.load(1)
        tests = [{"id": f"T{n}", "cmd": f"t{n}", "stage": 0} for f in t0.mfs for n in f.tests]
        if stage1_done is None:
            return json.dumps({"tests": tests, "done_mf": list(range(1, t0.count + 1)), "lockfiles": []})
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

    def test_the_first_stage_1_push_after_a_stage_0_base(self):  # stage_lock_never_read stage0_base_read_as_stage1
        """The base's `done_mf` is Stage 0's: nothing of Stage 1 is withdrawn, MF1's module-less red runs, and the
        stage reaches run-tests."""
        self.stage0_base()
        commit(self.brain, {"referee/runner/organs.py": "x = 1\n", "snowball-tests.json": self.manifest_text([1])},
               "P1 MF1")
        meta = self.pull()
        self.assertEqual((meta["kind"], meta["pre_reasons"], meta["stage"]), ("code", [], 1))
        self.assertEqual((meta["module_less"], meta["run_tests"]), ([1], True))

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

    def test_every_exit_request_is_the_wrong_stage(self):  # stage1_exit_judged_as_stage0
        """`02`: this seed judges only the Stage 0 exit; with the lock open that exit is behind, Stage 1's not yet
        judged here (E373)."""
        self.stage0_base()
        frozen = self.state["frozen_specs"]["spec/asama-0"]
        for stage in (0, 1):
            with self.subTest(stage=stage):
                commit(self.brain, {"exit-request.json": json.dumps({
                    "stage": stage, "sha": self.state["last_accepted_sha"], "spec_sha256": frozen})}, "exit")
                meta = self.pull()
                self.assertEqual(meta["kind"], "exit")
                self.assertIn("exit_request_wrong_stage", meta["pre_reasons"])

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
        self.assertEqual(meta["stage"], 0)
        self.assertNotIn("spec_not_frozen", meta["pre_reasons"])


class StageOneRunTestsTest(unittest.TestCase):
    def test_stage_0_and_stage_1_tests_run_and_module_less_red_reads_stage_1s(self):  # stage1_tests_not_run
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
        (pulled / "meta.json").write_text(json.dumps({"manifest": manifest, "module_less": [1], "stage": 1}))
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


if __name__ == "__main__":
    unittest.main()
