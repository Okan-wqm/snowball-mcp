"""The exam's answers apart from its inputs, and the pin that binds them (E509, plan D3/D4).

What is published holds the inputs alone: the projection of the seed's vectors, round trip exact, refusing a field it
cannot tell from an answer. The answers come from a private store only as the epoch pins them: one flipped byte in the
manifest or a file, a file the manifest does not list, a missing store or a missing answer is `answers_unavailable`,
an outage, never an empty exam and never green. `kos`'s parts plan and run their calls on the inputs alone and the join
judges them with the store's answers: the very run the seed's own vectors give. No record shows an expected value, the
published vectors and a packed snapshot of them hold no `expect`, and the canary is found wherever it lands, nested
archives too. The operator's migration writes the store and the projection outside the repository and admits them.
"""

from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import json
import shutil
import tarfile
import tempfile
import unittest
from pathlib import Path

from snowball_bootstrap import answers, cli, parts, stages, vectors
from snowball_bootstrap.answers import AnswersError
from snowball_bootstrap.container import RunResult

from helpers import EVERY_GROUP, FakeRunner
from test_parts import Sandbox

BOOT = Path(__file__).resolve().parents[1]
VECTORS = BOOT / "vectors"
SEED = json.loads((VECTORS / vectors.SEED_FILE).read_text(encoding="utf-8"))
TABLE = stages.load(0)
PROBE_TABLE = stages.parse_table(json.dumps({"stage": 0, "mfs": [
    {"mf": 1, "tests": [13], "groups": ["probe"], "module": "probe/x.py", "calls": []}]}), 0)
TOKEN_A, TOKEN_B = answers.CANARY_PREFIX + "a" * 32, answers.CANARY_PREFIX + "b" * 32


def _admit_module():
    spec = importlib.util.spec_from_file_location("exam_admit", BOOT / "local" / "exam_admit.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _keys(value):
    if isinstance(value, dict):
        return set(value) | {k for v in value.values() for k in _keys(v)}
    if isinstance(value, list):
        return {k for v in value for k in _keys(v)}
    return set()


class StoreTestCase(unittest.TestCase):
    """A temporary store holding the seed's answers as one exam version, and the public projection beside it."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="e509-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.inputs, self.own = answers.split(SEED)
        self.store, self.public = self.tmp / "store", self.tmp / "public"
        self.pin, self.canary = answers.write_exam(self.store, self.inputs, self.own, burned=True)
        vectors.public_vectors(VECTORS, self.public)
        self.base = self.store / answers.EXAMS / self.pin

    def flip(self, rel: str) -> None:
        path = self.base / rel
        data = bytearray(path.read_bytes())
        data[len(data) // 2] ^= 0x01
        path.write_bytes(bytes(data))


class ProjectionTest(unittest.TestCase):
    def test_the_seed_splits_into_its_inputs_and_its_answers_and_back(self):
        """E509: the projection is the seed's vectors without a single answer slot (every `expect`, `expect_not`,
        chain hash, statistic, hit count and drill verdict), and the answers put back give the seed exactly."""
        inputs, own = answers.split(SEED)
        self.assertEqual(answers.fill(inputs, own), SEED)
        self.assertEqual(set(own), set(answers.slot_pointers(inputs)))
        self.assertEqual(len(own), 371)  # the seed's answer slots today: every one moves
        self.assertEqual(_keys(inputs) & {"expect", "expect_not", "row_hash", "v3_broken_row", "hits", "verdicts"},
                         set())
        self.assertTrue(all(len(case) == 2 for g in ("cp_lower", "mcnemar") for case in inputs[g]["cases"]))
        self.assertEqual(answers.split(inputs), (inputs, {}))

    def test_a_field_the_projection_cannot_tell_from_an_answer_is_refused(self):
        """E509: a case field no judge reads might be an answer under a new name; the projection refuses it rather
        than publish it. An entry no judge knows is refused where the seed is published and left unjudged where the
        referee reads it (`29d`: a group without a judge runs nothing)."""
        spec = copy.deepcopy(SEED)
        spec["secrets"]["cases"][0]["expected"] = {"verdict": "x"}
        with self.assertRaisesRegex(ValueError, "expected"):
            answers.split(spec)
        spec = copy.deepcopy(SEED)
        spec["secrets"]["cases"][0]["changed"]["answer"] = "x"
        with self.assertRaisesRegex(ValueError, "answer"):
            answers.split(spec)
        spec = dict(copy.deepcopy(SEED), probe={"owner": "asama-0", "runner": "other", "cases": []})
        with self.assertRaisesRegex(ValueError, "probe"):
            answers.split(spec)
        inputs, own = answers.split(spec, strict=False)
        self.assertEqual(inputs["probe"], spec["probe"])
        self.assertEqual(len(own), 371)

    def test_a_seed_holding_some_answers_and_not_others_is_refused(self):
        """E509: half a projection is neither the seed nor its inputs; it would judge some cases on nothing."""
        spec = copy.deepcopy(SEED)
        del spec["secrets"]["cases"][0]["expect"]
        with self.assertRaisesRegex(ValueError, "some answers and not others"):
            answers.split(spec)


class StoreTest(StoreTestCase):
    def test_the_store_opens_on_its_pin_and_on_nothing_else(self):  # pin_compare_skipped
        """E509 (D3): the pin is the manifest's sha256 and the manifest lists every file's sha256 under a 256-bit salt.
        The pinned store opens; another pin, no pin, one flipped byte in the manifest or in the answers do not."""
        exam = answers.open_store(self.store, self.pin)
        self.assertEqual((exam.pin, exam.canary, exam.burned, len(exam.answers)), (self.pin, self.canary, True, 371))
        manifest = json.loads((self.base / answers.MANIFEST).read_bytes())
        self.assertEqual(len(manifest["salt"]), 64)
        for pin in ("0" * 64, None, "", self.pin.upper()):
            with self.subTest(pin=pin), self.assertRaises(AnswersError):
                answers.load(*answers.read_store(self.store, self.pin), pin)
        original = {rel: (self.base / rel).read_bytes() for rel in (answers.MANIFEST, answers.VISIBLE)}
        for rel in original:
            with self.subTest(flipped=rel):
                self.flip(rel)
                with self.assertRaises(AnswersError):
                    answers.open_store(self.store, self.pin)
                (self.base / rel).write_bytes(original[rel])
        self.assertEqual(answers.open_store(self.store, self.pin).answers, exam.answers)

    def test_a_file_the_manifest_does_not_list_is_refused(self):
        """E509: a job holds only the files it needs, each as the manifest lists it; a file the manifest does not name
        (another version's, or one added after the pin) is not part of the pinned exam."""
        manifest, files = answers.read_store(self.store, self.pin)
        answers.verify(manifest, files, self.pin)
        with self.assertRaisesRegex(AnswersError, "not a file the manifest lists"):
            answers.verify(manifest, dict(files, **{"held/extra.json": b"{}"}), self.pin)
        with self.assertRaises(AnswersError):
            answers.verify(manifest, {"../manifest.json": manifest}, self.pin)

    def test_a_store_that_cannot_be_read_is_an_outage_not_an_empty_exam(self):  # fetch_fail_is_exam_fault
        """E509 (D3, critique A-4): a failed fetch is `answers_unavailable`, an outage the Founder did not cause, never
        an `exam_fault` an operator could waive and never an empty set of answers."""
        for store in (self.tmp / "nothing", self.store):
            for pin in (self.pin, "f" * 64):
                if store == self.store and pin == self.pin:
                    continue
                with self.subTest(store=store.name, pin=pin[:4]):
                    with self.assertRaises(AnswersError) as caught:
                        answers.open_store(store, pin)
                    self.assertEqual(caught.exception.reason, "answers_unavailable")
                    self.assertFalse(caught.exception.reason.startswith("exam_fault"))
        (self.base / answers.VISIBLE).unlink()
        with self.assertRaises(AnswersError) as caught:
            answers.open_store(self.store, self.pin)
        self.assertEqual(caught.exception.reason, answers.REASON)


class JoinTest(StoreTestCase):
    def test_answers_fill_only_the_inputs_they_were_written_for(self):  # join_ignores_changed_inputs
        """E509: the answers are bound to the canonical inputs they answer. Two cases swapped in the public file, or
        one input edited, would put every later answer in the wrong slot; the join refuses them instead."""
        exam = answers.open_store(self.store, self.pin)
        self.assertEqual(answers.join(self.inputs, exam), SEED)
        swapped = copy.deepcopy(self.inputs)
        cases = swapped["secrets"]["cases"]
        cases[0], cases[1] = cases[1], cases[0]
        edited = copy.deepcopy(self.inputs)
        edited["chain"]["rows"][0]["row"]["row_id"] += "x"
        for changed in (swapped, edited):
            with self.assertRaisesRegex(AnswersError, "not the inputs"):
                answers.join(changed, exam)

    def test_every_slot_takes_exactly_one_answer(self):
        """E509: a store short of one answer, or answering a slot these inputs do not have, judges nothing."""
        short = dict(self.own)
        short.pop("/secrets/cases/0/expect")
        with self.assertRaisesRegex(AnswersError, "no answer in the store"):
            answers.fill(self.inputs, short)
        with self.assertRaisesRegex(AnswersError, "do not have"):
            answers.fill(self.inputs, dict(self.own, **{"/secrets/cases/99/expect": {}}))
        with self.assertRaisesRegex(AnswersError, "hold an answer"):
            answers.fill(SEED, self.own)

    def test_nothing_is_judged_on_the_inputs_alone(self):  # missing_answers_empty_green
        """E509: the public vectors give the judges a plan of their calls and nothing to judge on. Judging them without
        the exam, in one job or in the join, is the store's outage passed off as a verdict: refused, never green."""
        done = tuple(range(1, TABLE.count + 1))
        plan = vectors.applied(self.public, done, table=TABLE)
        self.assertFalse(plan.answered)
        self.assertEqual(vectors.call_inputs(plan), vectors.call_inputs(vectors.applied(VECTORS, done, table=TABLE)))
        with self.assertRaises(AnswersError):
            vectors.replay([], plan)
        with self.assertRaises(AnswersError):
            vectors.run_vectors(FakeRunner(self.public), self.public, done, table=TABLE)
        exam = answers.open_store(self.store, self.pin)
        self.assertTrue(vectors.applied(self.public, done, table=TABLE, exam=exam).answered)
        with self.assertRaisesRegex(AnswersError, "public vectors hold answers"):
            vectors.applied(VECTORS, done, table=TABLE, exam=exam)
        self.assertTrue(vectors.applied(VECTORS, done, table=TABLE).answered)  # the seed's own, before a pin


class PartsWithTheStoreTest(StoreTestCase):
    """`kos` as the workflow will run it: parts on the public inputs, the join with the store's answers."""

    def run_of(self, scenario, groups_plan, groups_judge, vec, count):
        done_tests = [{"id": "T1", "cmd": "python -m unittest t1", "stage": 0}]

        def push(groups):
            return parts.Push(head="b" * 40, tests=done_tests, groups=groups, asked=vectors.call_inputs(groups),
                              units=[], lic=[], missing=[])
        records = [parts.run_part(push(groups_plan), k, count, Sandbox(vec, self.tmp / f"src{k}", scenario), 600,
                                  lambda own: []) for k in range(count)]
        return parts.join(push(groups_judge), records)

    def test_parts_on_the_inputs_alone_joined_with_the_store_give_the_seed_run(self):
        """E509 with E440: the parts hold no answer, so they know no verdict and run their module-less share; the join
        judges their tapes with the pinned answers. The run is the one the seed's own vectors give, honest or not."""
        done = tuple(range(1, TABLE.count + 1))
        exam = answers.open_store(self.store, self.pin)
        seed_groups = vectors.applied(VECTORS, done, table=TABLE)
        plan = vectors.applied(self.public, done, table=TABLE)
        judged = vectors.applied(self.public, done, table=TABLE, exam=exam)
        for scenario in ({"vectors": "honest"}, {"vectors": "mixed"}):
            with self.subTest(scenario=scenario["vectors"]):
                seed_run = self.run_of(scenario, seed_groups, seed_groups, VECTORS, 1)
                store_run = self.run_of(scenario, plan, judged, self.public, 2)
                self.assertEqual(store_run, seed_run)
                self.assertEqual(seed_run["green"], scenario["vectors"] == "honest")


class DetailTest(unittest.TestCase):
    """What a record shows: never an expected value (plan D4; the signed result is public)."""

    CASE = {"id": "probe.one", "purpose": "a made-up case", "cmd": "python -m probe.x one", "fixture": [],
            "expect": {"a": TOKEN_A, "b": "x"},
            "changed": {"description": "another", "cmd": "python -m probe.x two", "fixture": [],
                        "expect_not": {"a": TOKEN_B}}}

    def run_probe(self, one, two):
        class Scripted:
            def run(self, cmd, *, cwd=".", stdin=b"", timeout_s):
                out = one if cmd.endswith("one") else two
                return RunResult(0, (json.dumps(out) + "\n").encode(), b"", 1)
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, vectors.SEED_FILE).write_text(json.dumps({"probe": {"owner": "asama-0", "runner": "data",
                                                                          "cases": [self.CASE]}}), encoding="utf-8")
            return {r["id"]: r for r in vectors.run_vectors(Scripted(), Path(tmp), (1,), table=PROBE_TABLE)}

    def test_no_record_shows_an_expected_value(self):  # expect_in_detail
        """E509: a pass shows nothing; a fail shows the Founder's values that differ and names the fields it left out;
        an answer that is the one a changed input must not give is named, not shown. The expected values never appear,
        and a wrong answer's detail still begins with "got "."""
        for one, two, oks in (({"a": TOKEN_A, "b": "x"}, {"a": "other"}, (True, True)),
                              ({"a": TOKEN_A, "b": "y"}, {"a": TOKEN_B}, (False, False)),
                              ({"a": TOKEN_A}, {"b": 1}, (False, False)),
                              ({"a": TOKEN_A, "b": "x"}, {"a": TOKEN_B, "c": TOKEN_A}, (True, False))):
            with self.subTest(one=one, two=two):
                results = self.run_probe(one, two)
                self.assertEqual((results["probe.one"]["ok"], results["probe.one.changed_input"]["ok"]), oks)
                for record in results.values():
                    self.assertNotIn(TOKEN_A, record["detail"])
                    self.assertNotIn(TOKEN_B, record["detail"])
                    self.assertEqual(record["detail"] == "", record["ok"])
                    self.assertTrue(record["ok"] or record["detail"].startswith("got "), record)
        results = self.run_probe({"a": TOKEN_A, "b": "y"}, {"a": TOKEN_B})
        self.assertEqual(results["probe.one"]["detail"], 'got {"b": "y"}')
        self.assertEqual(results["probe.one.changed_input"]["detail"], vectors.GAVE_THE_ORIGINAL)
        self.assertEqual(self.run_probe({"a": TOKEN_A}, {})["probe.one"]["detail"], "got {}, without b")

    def test_the_own_judges_show_no_expected_value(self):  # pass_detail_shows_answer
        """E509: chain hashes, statistics, hit counts and drill verdicts are answers too. On the reference they all
        pass with nothing shown; a chain that ignores its input fails its changed inputs without showing the hash."""
        done = (1, 2, 3)
        honest = vectors.run_vectors(FakeRunner(VECTORS), VECTORS, done, table=EVERY_GROUP)
        self.assertEqual([(r["id"], r["detail"]) for r in honest if not r["ok"] or r["detail"]], [])
        counted = (2 * len(SEED["chain"]["rows"]) + 2 + 2 * len(SEED["cp_lower"]["cases"])
                   + 2 * len(SEED["mcnemar"]["cases"]) + len(SEED["match"]["cases"]) + len(SEED["drill"]["cases"]))
        self.assertEqual(len(honest), counted)
        broken = {r["id"]: r for r in vectors.run_vectors(
            FakeRunner(VECTORS, wrong={"chain_ignores_input", "drill_lenient"}), VECTORS, done, table=EVERY_GROUP)}
        own = {f"chain.V{i}.": row["row_hash"] for i, row in enumerate(SEED["chain"]["rows"], start=1)}
        own.update({f"drill.{c['name']}": json.dumps(c["verdicts"]) for c in SEED["drill"]["cases"]})
        failed = [i for i, r in broken.items() if not r["ok"]]
        self.assertTrue(any(i.startswith("chain.") for i in failed) and any(i.startswith("drill.") for i in failed))
        for record_id in failed:
            for prefix, value in own.items():
                if record_id.startswith(prefix):
                    self.assertNotIn(value, broken[record_id]["detail"], record_id)
        changed = [broken[i]["detail"] for i in failed if i.startswith("chain.") and i.endswith("changed_input")]
        self.assertIn(vectors.GAVE_THE_ORIGINAL, changed)


class SnapshotTest(StoreTestCase):
    def test_the_published_vectors_and_their_snapshot_hold_no_answer(self):  # snap_full_vectors
        """E509 (D4, critique fact 1: the snapshot artifact held 150 `expect` keys). The vectors the referee publishes,
        packed as `cek` packs its snapshot, hold no `expect`, no `expect_not` and no answer slot; the seed's own
        vectors packed the same way are named by the same check, so `cek` can refuse to upload them."""
        snap = self.tmp / "snap"
        shutil.copytree(self.public, snap / "vectors")
        tar = self.tmp / "snapshot.tar"
        cli.pack_dir(snap, tar)
        self.assertEqual(answers.carrying([tar]), [])
        with tarfile.open(tar) as archive:
            names = archive.getnames()
            seed = json.loads(archive.extractfile("vectors/vectors.json").read())
        self.assertEqual(_keys(seed) & {"expect", "expect_not"}, set())
        self.assertEqual(answers.split(seed), (self.inputs, {}))
        self.assertEqual(sorted(n for n in names if n != "vectors/vectors.json"),
                         sorted("vectors/" + p.relative_to(VECTORS).as_posix() for p in VECTORS.rglob("*")
                                if p.is_file() and p.name != vectors.SEED_FILE))
        shutil.copytree(VECTORS, snap / "bootstrap" / "vectors")
        cli.pack_dir(snap, tar)
        self.assertEqual(answers.carrying([tar]), [f"{tar.as_posix()}!bootstrap/vectors/vectors.json"])

    def test_the_founders_inputs_are_the_same_from_the_projection(self):
        """E509 with E244: the launcher builds `/vec` from the referee's `vectors/`; from the projection it is byte for
        byte what the seed gave, the answer-in-fixture check having run at admission."""
        a, b = vectors.founder_inputs(VECTORS, self.tmp / "a"), vectors.founder_inputs(self.public, self.tmp / "b")
        files = sorted(p.relative_to(a).as_posix() for p in a.rglob("*") if p.is_file())
        self.assertEqual(files, sorted(p.relative_to(b).as_posix() for p in b.rglob("*") if p.is_file()))
        self.assertTrue(all((a / f).read_bytes() == (b / f).read_bytes() for f in files))


class CanaryTest(StoreTestCase):
    def test_the_canary_is_found_in_files_trees_and_nested_archives(self):  # canary_tar_members_unscanned
        """E509 (red team A2): the store's canary in a file, a tree, a tar member or a tar inside a tar is found; a
        tree without it is clean, and so is a `.git` folder's packed content, which the check does not read."""
        tree = self.tmp / "tree"
        (tree / "deep" / ".git").mkdir(parents=True)
        (tree / "deep" / "clean.txt").write_text("nothing here", encoding="utf-8")
        (tree / "deep" / ".git" / "packed").write_text(self.canary, encoding="utf-8")
        self.assertTrue(answers.canary_absent([tree], self.canary))
        inner, outer = io.BytesIO(), self.tmp / "outer.tar"
        with tarfile.open(fileobj=inner, mode="w:") as tar:
            data = f"log line {self.canary}\n".encode()
            info = tarfile.TarInfo("run/log.txt")
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
        with tarfile.open(outer, mode="w:gz") as tar:
            info = tarfile.TarInfo("part-0.tar")
            info.size = len(inner.getvalue())
            tar.addfile(info, io.BytesIO(inner.getvalue()))
        self.assertEqual(answers.canary_hits([outer], self.canary),  # the inner archive's bytes, then its member
                         [f"{outer.as_posix()}!part-0.tar", f"{outer.as_posix()}!part-0.tar!run/log.txt"])
        self.assertEqual(answers.canary_hits([self.base], self.canary),
                         [(self.base / answers.VISIBLE).as_posix()])
        with self.assertRaises(ValueError):
            answers.canary_hits([tree], "")

    def test_a_judged_run_carries_no_canary_and_no_expected_value(self):
        """E509: the join's records, judged with the store's answers on an honest push, hold neither the canary nor an
        `expect`: what `kos` packs into its artifact."""
        exam = answers.open_store(self.store, self.pin)
        done = tuple(range(1, TABLE.count + 1))
        records = vectors.run_vectors(FakeRunner(self.public), self.public, done, table=TABLE, exam=exam)
        out = self.tmp / "run"
        out.mkdir()
        (out / "run.json").write_text(json.dumps({"vectors": records}), encoding="utf-8")
        self.assertTrue(answers.canary_absent([out, self.public], exam.canary))
        self.assertEqual(answers.carrying([out]), [])


class AdmitTest(unittest.TestCase):
    """`local/exam_admit.py`: the operator's migration and admission (no repository, key or network)."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="e509-admit-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.tool = _admit_module()

    def migrate(self, **kw):
        out = io.StringIO()
        argv = ["migrate", "--vectors", str(VECTORS), "--store", str(self.tmp / "store"),
                "--public-out", str(self.tmp / "public"), "--public", str(VECTORS)]
        with contextlib.redirect_stdout(out):
            rc = self.tool.main(argv)
        return rc, out.getvalue()

    def test_migration_writes_the_store_and_the_projection_outside_the_repo_and_admits_them(self):
        """E509: the seed's answers become a burned exam version in the store and the referee's projection beside it;
        the report names the pin and counts, never an answer or the canary. Nothing is written inside the repo."""
        rc, printed = self.migrate()
        self.assertEqual(rc, 0, printed)
        report = json.loads(printed)
        self.assertTrue(report["admitted"])
        self.assertEqual((report["slots"], report["burned"], report["canary_hits"]), (371, True, []))
        self.assertGreater(report["public_answer_atoms"], 0)  # burned: the seed holds them, and the report says so
        exam = answers.open_store(self.tmp / "store", report["pin"])
        self.assertNotIn(exam.canary, printed)
        self.assertTrue(all(json.dumps(v) not in printed for v in exam.answers.values() if len(json.dumps(v)) > 6))
        self.assertEqual(answers.carrying([self.tmp / "public"]), [])
        with self.assertRaisesRegex(self.tool.AdmitError, "inside"):
            self.tool.migrate(VECTORS, BOOT / "exam-store", self.tmp / "p2")
        with self.assertRaisesRegex(self.tool.AdmitError, "not empty"):
            self.tool.migrate(VECTORS, self.tmp / "s2", self.tmp / "public")

    def test_admission_refuses_what_would_publish_or_misplace_an_answer(self):
        """E509: an exam version is refused when its canary is in a public path, when the public vectors hold
        answers, when a fixture carries an answer its case must compute, or when an unburned version's answer is
        already public."""
        store, public = self.tmp / "store", self.tmp / "public"
        inputs, own = answers.split(SEED)
        vectors.public_vectors(VECTORS, public)
        pin, canary = answers.write_exam(store, inputs, own, burned=True)
        self.assertTrue(self.tool.admit(store, pin, public, [VECTORS])["admitted"])
        leak = self.tmp / "leak"
        leak.mkdir()
        (leak / "notes.md").write_text(f"see {canary}", encoding="utf-8")
        self.assertEqual(self.tool.admit(store, pin, public, [leak])["canary_hits"], [(leak / "notes.md").as_posix()])
        self.assertFalse(self.tool.admit(store, pin, public, [leak])["admitted"])
        self.assertIn("refused", self.tool.admit(store, pin, VECTORS))
        fresh_pin, _ = answers.write_exam(store, inputs, own, burned=False)
        report = self.tool.admit(store, fresh_pin, public, [VECTORS])
        self.assertGreater(report["public_answer_atoms"], 0)
        self.assertFalse(report["admitted"])  # unburned answers that are public already give no secrecy
        flagged = [f for f in self.tool.admit(store, pin, public).get("fixture_lookups", ["refused"])]
        self.assertEqual(flagged, [])
        atom = next(a for p, v in own.items() if p.endswith("/expect") for a in vectors.answer_atoms(v)
                    if not any(a.encode() in f.read_bytes() for f in public.rglob("*") if f.is_file()))
        (public / "planted.txt").write_text(atom, encoding="utf-8")
        report = self.tool.admit(store, pin, public)
        self.assertNotEqual(report["fixture_lookups"], [])
        self.assertFalse(report["admitted"])

if __name__ == "__main__":
    unittest.main()
