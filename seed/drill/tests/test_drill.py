"""The drill judge passes a brain that learns and uses what it learned, and fails each one that does not."""

import copy
import io
import json
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from fractions import Fraction
from pathlib import Path

from snowball_drill import sim
from snowball_drill.__main__ import main
from snowball_drill.judge import QUESTIONS, judge, mcnemar_p, newcombe_lower
from snowball_drill.power import power_table
from snowball_drill.vectors import write_vectors

SEEDS = range(1, 101)

# Each defective brain and the question that must catch it in every drill.
CAUGHT_BY = {
    "wrong_cause": ("birth", "FAIL"),
    "unbound_lesson": ("birth", "FAIL"),
    "unscoped": ("birth", "FAIL"),
    "no_injection": ("use", "FAIL"),
    "leaky": ("use", "FAIL"),
    "ignores_lessons": ("effect", None),       # FAIL, except a lucky drill; never a passing drill
    "shortcut": ("effect", "UNMEASURABLE"),    # knows the trap without a lesson: effect cannot be shown
    "stubborn": ("wrong_lesson", "FAIL"),
    "unrecorded_withdrawal": ("wrong_lesson", "FAIL"),
    "stale_dispatcher": ("wrong_lesson", "FAIL"),
    "raw_rate_ranker": ("placebo", "FAIL"),
    "rank_ignores_credit": ("placebo", "FAIL"),
    "amnesic": ("persistence", "FAIL"),
    "lossy_ledger": ("persistence", "FAIL"),
}


class Statistics(unittest.TestCase):
    def test_mcnemar_matches_the_seed_vectors(self):
        for (b, c), p in {(0, 3): "0.1250", (0, 4): "0.0625", (1, 7): "0.0352", (0, 8): "0.0039",
                          (2, 8): "0.0547"}.items():
            self.assertEqual(f"{float(mcnemar_p(b, c)):.4f}", p)
        self.assertEqual(mcnemar_p(0, 8), Fraction(1, 256))

    def test_newcombe_matches_the_published_example(self):
        # Newcombe (1998), method 10: 56/70 vs 48/80, 95% interval lower bound 0.0524.
        self.assertEqual(f"{newcombe_lower(56, 70, 48, 80, 1.959963984540054):.4f}", "0.0524")


class Discrimination(unittest.TestCase):
    def test_the_learner_is_never_failed(self):
        # A drill whose family happened not to break the lessonless arm often enough is UNMEASURABLE
        # and is re-run with another family; it is never a FAIL for a brain that learns.
        results = [judge(sim.run_drill(sim.LEARNER, seed)) for seed in SEEDS]
        self.assertEqual([r["details"] for r in results if r["drill"] == "FAIL"], [])
        self.assertGreaterEqual(sum(r["drill"] == "PASS" for r in results), 98)

    def test_each_defect_is_caught_and_never_passes(self):
        for name, (question, verdict) in CAUGHT_BY.items():
            for seed in SEEDS:
                result = judge(sim.run_drill(sim.BRAINS[name], seed))
                self.assertNotEqual(result["drill"], "PASS", (name, seed))
                if verdict is not None:
                    self.assertEqual(result["verdicts"][question], verdict, (name, seed, result["details"]))

    def test_power_table_over_independent_drills(self):
        table = power_table(200)
        self.assertNotIn("FAIL", table["learner"]["drill"])
        self.assertGreaterEqual(table["learner"]["drill_pass"], 196)
        for name in CAUGHT_BY:
            self.assertEqual(table[name]["drill_pass"], 0, name)


class Tamper(unittest.TestCase):
    def setUp(self):
        self.doc = sim.run_drill(sim.LEARNER, 7)
        self.assertEqual(judge(self.doc)["drill"], "PASS")

    def test_an_answer_key_changed_after_the_run_fails_everything(self):
        doc = copy.deepcopy(self.doc)
        doc["answer_key"]["cause"] = "test_failure"
        doc["transcript"]["birth"]["cause"] = "test_failure"
        self.assertEqual(set(judge(doc)["verdicts"].values()), {"FAIL"})

    def test_families_come_from_the_answer_key_not_from_the_transcript(self):
        doc = copy.deepcopy(self.doc)
        other = [i for i, v in doc["answer_key"]["instances"].items() if v["family"] == sim.EASY]
        for pair, iid in zip(doc["transcript"]["effect"], other):
            pair["instance_id"] = iid  # claim the effect on instances that are not in the trap family
        self.assertNotEqual(judge(doc)["verdicts"]["effect"], "PASS")

    def test_an_unrelated_failure_is_not_a_contradiction(self):
        doc = copy.deepcopy(self.doc)
        for rec in doc["transcript"]["wrong"]:
            if rec["failed_test"] not in (None, "unrelated"):
                rec["failed_test"] = "unrelated"
        self.assertEqual(judge(doc)["verdicts"]["wrong_lesson"], "UNMEASURABLE")

    def test_a_merge_that_was_not_reverted_gives_no_birth(self):
        doc = copy.deepcopy(self.doc)
        doc["transcript"]["birth"]["reverted"] = False
        self.assertEqual(judge(doc)["verdicts"]["birth"], "FAIL")

    def test_reported_credit_must_be_the_referees(self):
        doc = copy.deepcopy(self.doc)
        doc["transcript"]["placebo"]["credit"]["L1"] = "0.9999"
        self.assertEqual(judge(doc)["verdicts"]["placebo"], "FAIL")

    def test_a_lesson_given_to_the_oracle_fails_use(self):
        doc = copy.deepcopy(self.doc)
        oracle = next(r for r in doc["transcript"]["use"] if r["role"] == "oracle")
        oracle["lessons_injected"] = ["L1"]
        self.assertEqual(judge(doc)["verdicts"]["use"], "FAIL")


class Vectors(unittest.TestCase):
    """The drill vectors the bootstrap applies are this judge's verdicts on these brains, unchanged."""

    def test_vector_files_reproduce_from_the_simulation(self):
        root = Path(__file__).resolve().parents[2] / "bootstrap" / "vectors"
        group = json.loads((root / "vectors.json").read_text())["drill"]
        names = [c["name"] for c in group["cases"]]
        self.assertEqual(names, [*sim.BRAINS, "tampered_key"])
        for case in group["cases"]:
            doc = json.loads((root / case["file"]).read_text())
            if case["name"] in sim.BRAINS:
                self.assertEqual(doc, sim.run_drill(sim.BRAINS[case["name"]], 7), case["name"])
            result = judge(doc)
            self.assertEqual((result["drill"], result["verdicts"]), (case["drill"], case["verdicts"]), case["name"])
        self.assertEqual([c["drill"] for c in group["cases"]].count("PASS"), 1)


    def test_regenerating_the_vectors_gives_the_committed_bytes_on_every_platform(self):
        """V4: a Windows run without an explicit LF newline wrote CRLF into 17 files. A checkout may translate the
        committed ones, so they are compared line-ending-insensitively; what is written must never contain a CR."""
        root = Path(__file__).resolve().parents[2] / "bootstrap" / "vectors"
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copy(root / "vectors.json", tmp)
            write_vectors(Path(tmp))
            written = sorted(Path(tmp).rglob("*.json"))
            self.assertGreater(len(written), 5)
            for path in written:
                data = path.read_bytes()
                committed = (root / path.relative_to(tmp)).read_bytes().replace(b"\r\n", b"\n")
                self.assertEqual(data.count(b"\r"), 0, f"{path.name}: CR written")  # assertEqual on the bytes would
                self.assertTrue(data == committed, f"{path.name}: differs from the committed file")  # print whole files


class Cli(unittest.TestCase):
    def test_judge_prints_one_json_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "d.json"
            path.write_text(json.dumps(sim.run_drill(sim.BRAINS["stubborn"], 3)))
            buf = io.StringIO()
            with redirect_stdout(buf):
                self.assertEqual(main(["judge", str(path)]), 0)
            out = json.loads(buf.getvalue().strip().splitlines()[-1])
            self.assertEqual(out["verdicts"]["wrong_lesson"], "FAIL")
            self.assertEqual(sorted(out["verdicts"]), sorted(QUESTIONS))


if __name__ == "__main__":
    unittest.main()
