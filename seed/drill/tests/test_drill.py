"""The drill judge passes a brain that learns and uses what it learned, and fails each one that does not."""

import copy
import io
import json
import os
import random
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from fractions import Fraction
from pathlib import Path

import snowball_drill.judge as judge_module
from snowball_drill import sim
from snowball_drill.__main__ import main
from snowball_drill.judge import QUESTIONS, judge, mcnemar_p, newcombe_lower
from snowball_drill.power import power_table
from snowball_drill.vectors import EDITED, drill_docs, write_vectors

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "local"))
import mutate_drill  # noqa: E402

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
        # The second is five units off in the fourth decimal: not the referee's credit rounded, a different one.
        for credit in ("0.9999", f"{float(self.doc['transcript']['placebo']['credit']['L1']) + 0.0005:.4f}"):
            doc = copy.deepcopy(self.doc)
            doc["transcript"]["placebo"]["credit"]["L1"] = credit
            self.assertEqual(judge(doc)["verdicts"]["placebo"], "FAIL", credit)

    def test_a_lesson_given_to_the_oracle_fails_use(self):
        doc = copy.deepcopy(self.doc)
        oracle = next(r for r in doc["transcript"]["use"] if r["role"] == "oracle")
        oracle["lessons_injected"] = ["L1"]
        self.assertEqual(judge(doc)["verdicts"]["use"], "FAIL")

    # The rules below are ones no simulated brain reaches (gap E48): each test is a drill edited so that a judge
    # skipping the rule gives a different verdict. `local/mutate_drill.py` checks that each one is needed.

    def contradiction_seq(self, doc):
        return judge(doc)["details"]["wrong_lesson"]["contradiction_seq"]

    def harmful(self, doc, record):
        key = doc["answer_key"]
        return key["wrong"]["harmful_condition"] in key["instances"][record["instance_id"]]["conditions"]

    def test_a_birth_from_an_instance_outside_the_family_is_no_birth(self):
        easy = next(i for i, v in self.doc["answer_key"]["instances"].items() if v["family"] == sim.EASY)
        for instance_id in (easy, "i_not_in_the_key"):
            doc = copy.deepcopy(self.doc)
            doc["transcript"]["birth"]["instance_id"] = instance_id
            result = judge(doc)
            self.assertEqual(result["verdicts"]["birth"], "FAIL", instance_id)
            self.assertFalse(result["details"]["birth"]["instance_in_family"], instance_id)

    def test_use_with_no_record_of_another_family_is_unmeasurable(self):
        # Nothing shows that the lesson is withheld where it does not belong.
        doc = copy.deepcopy(self.doc)
        key = doc["answer_key"]
        doc["transcript"]["use"] = [r for r in doc["transcript"]["use"]
                                    if key["instances"][r["instance_id"]]["family"] == key["family"]]
        result = judge(doc)
        self.assertEqual((result["verdicts"]["use"], result["details"]["use"]["negatives"]), ("UNMEASURABLE", 0))

    def test_use_with_no_planner_or_fixer_of_the_family_is_unmeasurable(self):
        # Nothing shows that the lesson is given where it belongs.
        doc = copy.deepcopy(self.doc)
        key = doc["answer_key"]
        doc["transcript"]["use"] = [r for r in doc["transcript"]["use"]
                                    if key["instances"][r["instance_id"]]["family"] != key["family"]
                                    or r["role"] not in ("planner", "fixer")]
        result = judge(doc)
        self.assertEqual((result["verdicts"]["use"], result["details"]["use"]["positives"]), ("UNMEASURABLE", 0))

    def test_a_use_record_of_an_instance_the_key_does_not_hold_fails_use(self):
        doc = copy.deepcopy(self.doc)
        doc["transcript"]["use"].append({"instance_id": "i_not_in_the_key", "role": "fixer", "lessons_injected": []})
        result = judge(doc)
        self.assertEqual(result["verdicts"]["use"], "FAIL")
        self.assertEqual(result["details"]["use"]["wrong"], ["i_not_in_the_key:not_in_key"])

    def test_an_instance_recorded_twice_in_the_effect_fails_it(self):
        doc = copy.deepcopy(self.doc)
        effect = doc["transcript"]["effect"]
        effect.append(dict(effect[0]))
        result = judge(doc)
        self.assertEqual(result["verdicts"]["effect"], "FAIL")
        self.assertEqual(result["details"]["effect"], {"duplicate_instances": True})

    def test_fewer_than_k_pairs_are_unmeasurable(self):
        doc = copy.deepcopy(self.doc)
        del doc["transcript"]["effect"][doc["params"]["k"] - 1:]
        self.assertEqual(judge(doc)["verdicts"]["effect"], "UNMEASURABLE")

    def test_an_effect_needs_eight_discordant_pairs_and_a_small_p_value(self):
        # b pairs break only with the lesson, c only without it, the rest both ways: the lessonless arm always breaks
        # often enough. p(0, 7) = 1/128 is small but seven pairs are too few; p(3, 5) = 93/256 is too large.
        cases = {(0, 8): "PASS", (1, 7): "PASS", (0, 7): "FAIL", (3, 5): "FAIL", (4, 4): "FAIL"}
        for (b, c), verdict in cases.items():
            doc = copy.deepcopy(self.doc)
            for i, pair in enumerate(doc["transcript"]["effect"]):
                ok = (True, False) if i < b else (False, True) if i < b + c else (False, False)
                pair["without"], pair["with"] = ok
            result = judge(doc)
            self.assertEqual((result["details"]["effect"]["b"], result["details"]["effect"]["c"]), (b, c))
            self.assertEqual(result["verdicts"]["effect"], verdict, (b, c))

    def test_the_order_of_the_wrong_records_does_not_change_the_verdict(self):
        # "After the contradiction" is by seq. Read in file order, the stubborn brain's last contradiction would
        # come first, nothing harmful would follow it, and its FAIL would become UNMEASURABLE.
        stubborn = sim.run_drill(sim.BRAINS["stubborn"], 7)
        for doc, verdict in ((self.doc, "PASS"), (stubborn, "FAIL")):
            expected = judge(doc)
            self.assertEqual(expected["verdicts"]["wrong_lesson"], verdict)
            for order in range(4):
                shuffled = copy.deepcopy(doc)
                records = shuffled["transcript"]["wrong"]
                if order == 0:
                    records.reverse()
                else:
                    random.Random(order).shuffle(records)
                self.assertEqual(judge(shuffled), expected, (verdict, order))

    def test_a_trap_test_broken_without_the_lesson_is_no_contradiction(self):
        doc = copy.deepcopy(self.doc)
        first = self.contradiction_seq(doc)
        next(r for r in doc["transcript"]["wrong"] if r["seq"] == first)["injected"] = False
        self.assertEqual(judge(doc)["verdicts"]["wrong_lesson"], "UNMEASURABLE")

    def test_a_superseded_lesson_is_withdrawn(self):
        # The learner narrows the lesson by excluding the condition; `tohum/22a` allows superseding it instead.
        doc = copy.deepcopy(self.doc)
        first = self.contradiction_seq(doc)
        for rec in doc["transcript"]["wrong"]:
            if rec["seq"] >= first:
                rec["lesson_state"] = {"superseded": True, "excluded_conditions": []}
                rec["injected"] = rec["seq"] == first
        result = judge(doc)
        self.assertTrue(result["details"]["wrong_lesson"]["withdrawn"])
        self.assertEqual(result["verdicts"]["wrong_lesson"], "PASS")

    def test_a_contradiction_with_nothing_harmful_after_it_is_unmeasurable(self):
        doc = copy.deepcopy(self.doc)
        first = self.contradiction_seq(doc)
        doc["transcript"]["wrong"] = [r for r in doc["transcript"]["wrong"]
                                      if r["seq"] <= first or not self.harmful(doc, r)]
        self.assertEqual(judge(doc)["verdicts"]["wrong_lesson"], "UNMEASURABLE")

    def test_a_placebo_that_earns_credit_fails_placebo(self):
        # The referee's arms say the irrelevant lesson helps. The brain reports the referee's credit and ranks by it,
        # so only the placebo's own credit can fail the drill.
        doc = copy.deepcopy(self.doc)
        placebo = doc["transcript"]["placebo"]
        for arm in placebo["arms"]:
            if arm["lesson_id"] == doc["answer_key"]["placebo"]:
                arm["ok"] = arm["given"]
        placebo["credit"] = judge(doc)["details"]["placebo"]["lower_bounds"]
        placebo["ranking"] = sorted(placebo["credit"], key=lambda lid: -float(placebo["credit"][lid]))
        result = judge(doc)
        details = result["details"]["placebo"]
        self.assertTrue(details["credit_matches"] and details["ranked_first"] == details["expected_first"], details)
        self.assertFalse(details["placebo_no_credit"])
        self.assertEqual(result["verdicts"]["placebo"], "FAIL")

    def test_a_ranking_or_a_credit_report_without_the_placebo_fails_placebo(self):
        placebo = self.doc["answer_key"]["placebo"]
        ranking = copy.deepcopy(self.doc)
        ranking["transcript"]["placebo"]["ranking"].remove(placebo)
        credit = copy.deepcopy(self.doc)
        del credit["transcript"]["placebo"]["credit"][placebo]
        for doc in (ranking, credit):
            self.assertEqual(judge(doc)["verdicts"]["placebo"], "FAIL")

    def test_empty_persistence_hashes_are_no_evidence(self):
        for before, after, check in (("view_sha256_before", "view_sha256_rebuilt", "view_rebuilt_identical"),
                                     ("injected_sha256_before", "injected_sha256_after_restart",
                                      "same_lesson_after_restart")):
            doc = copy.deepcopy(self.doc)
            persistence = doc["transcript"]["persistence"]
            persistence[before] = persistence[after] = ""
            result = judge(doc)
            self.assertEqual(result["verdicts"]["persistence"], "FAIL", before)
            self.assertEqual([k for k, ok in result["details"]["persistence"].items() if not ok], [check])

    def test_a_different_lesson_after_the_restart_fails_persistence(self):
        doc = copy.deepcopy(self.doc)
        doc["transcript"]["persistence"]["injected_sha256_after_restart"] = "0" * 64
        result = judge(doc)
        self.assertEqual(result["verdicts"]["persistence"], "FAIL")
        self.assertEqual([k for k, ok in result["details"]["persistence"].items() if not ok],
                         ["same_lesson_after_restart"])


class Vectors(unittest.TestCase):
    """The drill vectors the bootstrap applies are this judge's verdicts on these brains, unchanged."""

    def test_vector_files_reproduce_from_the_simulation(self):
        root = Path(__file__).resolve().parents[2] / "bootstrap" / "vectors"
        group = json.loads((root / "vectors.json").read_text())["drill"]
        names = [c["name"] for c in group["cases"]]
        self.assertEqual(names, [*sim.BRAINS, "tampered_key", "reused_instances", "missing_evidence",
                                 "stubborn_reversed"])
        for case in group["cases"]:
            doc = json.loads((root / case["file"]).read_text())
            if case["name"] in sim.BRAINS:
                self.assertEqual(doc, sim.run_drill(sim.BRAINS[case["name"]], 7), case["name"])
            result = judge(doc)
            self.assertEqual((result["drill"], result["verdicts"]), (case["drill"], case["verdicts"]), case["name"])
        self.assertEqual([c["drill"] for c in group["cases"]].count("PASS"), 1)

    def test_each_edited_drill_changes_only_the_verdicts_its_edit_is_about(self):
        """The edited drills carry to the Founder's judge the rules no simulated brain reaches (gap E48)."""
        docs = drill_docs()
        changed = {"tampered_key": dict.fromkeys(QUESTIONS, "FAIL"),
                   "reused_instances": {"birth": "FAIL", "effect": "FAIL"},
                   "missing_evidence": {"use": "UNMEASURABLE", "persistence": "FAIL"},
                   "stubborn_reversed": {}}  # reversed, the stubborn brain's records still fail wrong_lesson
        self.assertEqual(list(changed), list(EDITED))
        for name, verdicts in changed.items():
            base = judge(docs[EDITED[name][0]])["verdicts"]
            self.assertEqual(judge(docs[name])["verdicts"], {**base, **verdicts}, name)
        self.assertEqual(judge(docs["stubborn"])["verdicts"]["wrong_lesson"], "FAIL")

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


class MutationList(unittest.TestCase):
    """`local/mutate_drill.py` breaks the judge on purpose; its anchors must keep matching the judge they break."""

    @unittest.skipIf(os.environ.get(mutate_drill.SKIP_ENV), "a mutant run has broken the judge on purpose")
    def test_every_judge_mutant_still_applies(self):
        text = Path(judge_module.__file__).read_text(encoding="utf-8")
        names = [m[0] for m in mutate_drill.MUTANTS]
        self.assertEqual(len(set(names)), len(names))
        for name, old, _new, _why in mutate_drill.MUTANTS:
            self.assertEqual(text.count(old), 1, f"{name}: its anchor must occur exactly once in the judge")


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
