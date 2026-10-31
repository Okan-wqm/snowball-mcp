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
from snowball_drill.judge import QUESTIONS, commitment, judge, mcnemar_p, newcombe_lower, scope_matches, withheld
from snowball_drill.power import calibration, effect_power, power_table, ready_chance, unmeasurable_risk
from snowball_drill.vectors import EDITED, drill_docs, write_vectors

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "local"))
import mutate_drill  # noqa: E402

SEEDS = range(1, 101)

# Each defective brain and the question that must catch it in every drill.
CAUGHT_BY = {
    "wrong_cause": ("birth", "FAIL"),
    "unbound_lesson": ("birth", "FAIL"),
    "unscoped": ("birth", "FAIL"),
    "label_peeker": ("birth", "FAIL"),          # the scope names the answer key's family label (E64)
    "overbroad_scope": ("birth", "FAIL"),       # the scope covers another family too (E64)
    "no_injection": ("use", "FAIL"),
    "leaky": ("use", "FAIL"),
    "ignores_lessons": ("effect", None),       # FAIL, except a lucky drill; never a passing drill
    "shortcut": ("effect", "UNMEASURABLE"),    # knows the trap without a lesson: effect cannot be shown
    "unequal_effect_arms": ("effect", "FAIL"),  # adds text outside an effect pair's lesson block (E321)
    "stubborn": ("wrong_lesson", "FAIL"),
    "unrecorded_withdrawal": ("wrong_lesson", "FAIL"),
    "stale_dispatcher": ("wrong_lesson", "FAIL"),
    "llm_prior_discarder": ("right_lesson", "FAIL"),  # drops any imported lesson at the first red (E318)
    "cherry_picking_dispatcher": ("placebo", "FAIL"),  # serves its own lesson against the referee's draw (E65)
    "unequal_arms": ("placebo", "FAIL"),  # runs the lesson's arm with more effort, turns, budget; effect too (E65)
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
                arm["ok"] = arm["lesson_id"] in arm["lessons_injected"]
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


class BlindScope(unittest.TestCase):
    """E64: the brain never sees a family's name, so a scope is judged by what it covers, with one public matcher."""

    def setUp(self):
        self.doc = sim.run_drill(sim.LEARNER, 7)
        key = self.doc["answer_key"]
        self.birth_path = key["instances"][self.doc["transcript"]["birth"]["instance_id"]]["observables"]["paths"][0]
        self.family = [i for i, v in key["instances"].items() if v["family"] == key["family"]]

    def birth(self, scope, coverage=None):
        doc = copy.deepcopy(self.doc)
        doc["transcript"]["birth"]["lesson"]["scope"] = scope
        if coverage is not None:
            doc["params"]["scope_coverage"] = coverage
        result = judge(doc)
        return result["verdicts"]["birth"], result["details"]["birth"]

    def test_the_matcher_reads_only_the_public_vocabulary(self):
        job = {"paths": ["src/api/m1.py", "README.md"], "class_level": "K2", "property": "field_rename"}
        self.assertTrue(scope_matches({"path_glob": "src/api/*", "property": "field_rename"}, job))
        self.assertTrue(scope_matches({"path_glob": "*.md"}, job))  # one of the job's paths is enough
        self.assertTrue(scope_matches({"conditions": ["x"]}, job))  # conditions are the dispatcher's, not coverage
        self.assertTrue(scope_matches({}, job))  # an empty scope covers every job
        self.assertFalse(scope_matches({"path_glob": "src/ui/*"}, job))
        self.assertFalse(scope_matches({"class_level": "K1"}, job))
        self.assertFalse(scope_matches({"property": "docstring"}, job))
        self.assertFalse(scope_matches({"family": sim.TRAP}, job))  # a label is no observable
        self.assertFalse(scope_matches({"property": "field_rename", "family": sim.TRAP}, job))
        self.assertFalse(scope_matches(["src/api/*"], job))

    def test_a_blind_scope_passes_birth(self):
        verdict, checks = self.birth({"path_glob": "src/api/*", "class_level": "K2", "conditions": []})
        self.assertEqual(verdict, "PASS", checks)

    def test_a_scope_naming_the_family_fails_birth(self):
        verdict, checks = self.birth({"family": sim.TRAP})
        self.assertEqual(verdict, "FAIL")
        self.assertEqual([k for k, ok in checks.items() if not ok],
                         ["scope_public", "scope_covers_birth", "scope_covers_family"])

    def test_a_scope_covering_another_family_fails_birth(self):
        for scope in ({"property": "field_rename"}, {}, {"path_glob": "src/*"}):
            verdict, checks = self.birth(scope)
            self.assertEqual(verdict, "FAIL", scope)
            self.assertEqual([k for k, ok in checks.items() if not ok], ["scope_excludes_other_families"], scope)

    def test_coverage_of_the_family_is_counted_against_the_policy(self):
        # A scope that names the birth instance's own file covers it and one instance of its family, no more.
        verdict, checks = self.birth({"path_glob": self.birth_path})
        self.assertEqual(verdict, "FAIL")
        self.assertEqual([k for k, ok in checks.items() if not ok], ["scope_covers_family"])
        exact = f"1/{len(self.family)}"
        self.assertEqual(self.birth({"path_glob": self.birth_path}, coverage=exact)[0], "PASS")
        self.assertEqual(self.birth({"path_glob": self.birth_path}, coverage=f"2/{2 * len(self.family) - 1}")[0],
                         "FAIL")

    def test_a_scope_that_misses_the_birth_instance_fails_birth(self):
        verdict, checks = self.birth({"path_glob": "src/api/*", "property": "field_rename"}, coverage="0")
        self.assertEqual(verdict, "PASS")
        doc = copy.deepcopy(self.doc)
        key = doc["answer_key"]
        key["instances"][doc["transcript"]["birth"]["instance_id"]]["observables"]["paths"] = ["src/other/x.py"]
        doc["commitment_sha256"] = commitment(key)
        result = judge(doc)
        self.assertFalse(result["details"]["birth"]["scope_covers_birth"])
        self.assertEqual(result["verdicts"]["birth"], "FAIL")

    def test_use_follows_the_scope_not_the_label(self):
        # The dispatcher gives the lesson exactly where its scope covers the job; a narrower scope the dispatcher
        # follows is consistent, a dispatcher that also serves an uncovered job of the family leaks.
        doc = copy.deepcopy(self.doc)
        key = doc["answer_key"]
        fixer = next(r for r in doc["transcript"]["use"] if r["role"] == "fixer"
                     and key["instances"][r["instance_id"]]["family"] == key["family"])
        path = key["instances"][fixer["instance_id"]]["observables"]["paths"][0]
        doc["transcript"]["birth"]["lesson"]["scope"] = {"path_glob": path}
        result = judge(doc)
        self.assertEqual(result["verdicts"]["use"], "FAIL")
        self.assertTrue(all(w.endswith(":leaked") for w in result["details"]["use"]["wrong"]), result["details"]["use"])


class RefereeArms(unittest.TestCase):
    """E65: who gets a lesson in the placebo arms is the referee's draw from the committed seed, and both arms of a
    lesson run alike, in the effect's pairs as in the placebo's arms; neither is read from the transcript's say-so."""

    def setUp(self):
        self.doc = sim.run_drill(sim.LEARNER, 7)
        self.assertEqual(judge(self.doc)["verdicts"]["placebo"], "PASS")
        self.assertEqual(judge(self.doc)["verdicts"]["effect"], "PASS")

    def test_the_unequal_arms_brain_fails_effect_and_placebo(self):
        for seed in range(1, 21):
            verdicts = judge(sim.run_drill(sim.BRAINS["unequal_arms"], seed))["verdicts"]
            self.assertEqual((verdicts["effect"], verdicts["placebo"]), ("FAIL", "FAIL"), seed)

    def test_the_draw_is_an_hmac_of_the_seed(self):
        seed = "00" * 32
        draws = [withheld(seed, f"i{n}") for n in range(400)]
        self.assertTrue(160 < sum(draws) < 240)  # about half withheld
        self.assertEqual(draws, [withheld(seed, f"i{n}") for n in range(400)])
        self.assertNotEqual(draws, [withheld("11" * 32, f"i{n}") for n in range(400)])

    def test_an_arm_served_against_the_draw_fails_placebo(self):
        for lesson in ("L1", "Lp"):
            doc = copy.deepcopy(self.doc)
            arm = next(a for a in doc["transcript"]["placebo"]["arms"] if a["lesson_id"] == lesson)
            arm["lessons_injected"] = [] if lesson in arm["lessons_injected"] else [lesson]
            result = judge(doc)
            self.assertEqual(result["verdicts"]["placebo"], "FAIL", lesson)
            self.assertEqual(result["details"]["placebo"], {"arms_off_the_draw": [arm["instance_id"]]})

    def test_another_seed_makes_the_same_arms_off_the_draw(self):
        doc = copy.deepcopy(self.doc)
        doc["answer_key"]["withhold_seed"] = "ab" * 32
        doc["commitment_sha256"] = commitment(doc["answer_key"])
        result = judge(doc)
        self.assertEqual(result["verdicts"]["placebo"], "FAIL")
        self.assertGreater(len(result["details"]["placebo"]["arms_off_the_draw"]), 5)

    def test_arms_of_one_lesson_run_alike(self):
        for field, value in (("max_turns", 21), ("effort", "high"), ("model", "claude-opus-5-5"),
                             ("max_budget_usd", "1.000000")):
            doc = copy.deepcopy(self.doc)
            arm = next(a for a in doc["transcript"]["placebo"]["arms"] if a["lesson_id"] == "Lp")
            arm["run"][field] = value
            result = judge(doc)
            self.assertEqual(result["verdicts"]["placebo"], "FAIL", field)
            self.assertEqual(result["details"]["placebo"], {"unequal_arms": ["Lp"]}, field)

    def test_two_lessons_may_run_with_different_settings(self):
        # Equal arms are within one lesson: the trap family may need another budget than the placebo's.
        doc = copy.deepcopy(self.doc)
        for arm in doc["transcript"]["placebo"]["arms"]:
            if arm["lesson_id"] == "L1":
                arm["run"]["max_turns"] = 40
        self.assertEqual(judge(doc)["verdicts"]["placebo"], "PASS")

    def test_an_arm_of_fewer_than_eight_is_unmeasurable(self):
        # The draw splits every lesson's arms; a drill that ran too few of one arm cannot give that lesson a credit.
        doc = copy.deepcopy(self.doc)
        seed, arms = doc["answer_key"]["withhold_seed"], doc["transcript"]["placebo"]["arms"]
        given = [a for a in arms if a["lesson_id"] == "Lp" and not withheld(seed, a["instance_id"])]
        held = [a for a in arms if a["lesson_id"] == "Lp" and withheld(seed, a["instance_id"])]
        trap = [a for a in arms if a["lesson_id"] == "L1"]
        doc["transcript"]["placebo"]["arms"] = trap + given[:7] + held[:9]
        result = judge(doc)
        self.assertEqual((result["verdicts"]["placebo"], result["details"]["placebo"]),
                         ("UNMEASURABLE", {"arm_too_small": "Lp"}))
        doc["transcript"]["placebo"]["arms"] = trap + given[:8] + held[:9]
        self.assertIn("lower_bounds", judge(doc)["details"]["placebo"])  # eight are enough

    def test_settings_outside_the_compared_fields_are_ignored(self):
        doc = copy.deepcopy(self.doc)
        doc["transcript"]["placebo"]["arms"][0]["run"]["started_at"] = "2026-10-30T00:00:00Z"
        self.assertEqual(judge(doc)["verdicts"]["placebo"], "PASS")


class EffectArms(unittest.TestCase):
    """E65, E321: the effect question is the MVP's central claim. A pair is one job run twice; both runs have the same
    model, effort, turns and budget, every pair the same settings, and both the same prompt once the lesson block is
    taken out (E65's plan). The referee records both runs; a pair it cannot show alike fails the question. Before
    E321 the budget and the prompt were not compared, and a setting missing from every run counted as equal."""

    PROMPT = "prompt_sha256_without_lessons"

    def setUp(self):
        self.doc = sim.run_drill(sim.LEARNER, 7)
        self.assertEqual(judge(self.doc)["verdicts"]["effect"], "PASS")

    def unequal(self, edit, index=3):
        doc = copy.deepcopy(self.doc)
        pair = doc["transcript"]["effect"][index]
        edit(pair)
        result = judge(doc)
        return result["verdicts"]["effect"], result["details"]["effect"], pair["instance_id"]

    def test_the_referee_records_both_runs_of_every_pair(self):
        for pair in self.doc["transcript"]["effect"]:
            run = pair["run"]
            self.assertEqual(run["with"], run["without"])
            self.assertEqual(set(run["with"]), {*judge_module.RUN_FIELDS, self.PROMPT})
            self.assertEqual(len(run["with"][self.PROMPT]), 64)
        self.assertIn("max_budget_usd", judge_module.RUN_FIELDS)
        # One prompt per job: pairs differ from each other, the two runs of a pair do not.
        hashes = {pair["run"]["with"][self.PROMPT] for pair in self.doc["transcript"]["effect"]}
        self.assertEqual(len(hashes), len(self.doc["transcript"]["effect"]))

    def test_both_runs_of_every_pair_run_alike(self):
        # More effort, turns or budget for one run, or text outside its lesson block, inflates the McNemar effect.
        for arm in ("with", "without"):
            for field, value in (("model", "claude-opus-5-5"), ("effort", "high"), ("max_turns", 21),
                                 ("max_budget_usd", "1.000000"), (self.PROMPT, "ab" * 32)):
                verdict, detail, iid = self.unequal(lambda pair: pair["run"][arm].update({field: value}))
                self.assertEqual((verdict, detail), ("FAIL", {"unequal_arms": [iid]}), (arm, field))

    def test_every_pair_runs_with_the_same_settings(self):
        verdict, detail, _iid = self.unequal(lambda pair: [pair["run"][arm].update(max_turns=40)
                                                           for arm in ("with", "without")])
        self.assertEqual((verdict, detail), ("FAIL", {"unequal_pairs": True}))
        doc = copy.deepcopy(self.doc)
        for pair in doc["transcript"]["effect"]:
            for arm in ("with", "without"):
                pair["run"][arm].update(max_turns=40, started_at=pair["instance_id"])  # outside RUN_FIELDS: ignored
        self.assertEqual(judge(doc)["verdicts"]["effect"], "PASS")

    def test_a_pair_without_a_full_record_of_both_runs_fails_effect(self):
        def no_budget(pair):
            del pair["run"]["with"]["max_budget_usd"], pair["run"]["without"]["max_budget_usd"]

        def empty_prompt_hash(pair):  # equal, and no evidence: as in persistence, an empty hash shows nothing
            pair["run"]["with"][self.PROMPT] = pair["run"]["without"][self.PROMPT] = ""

        for name, edit in (("no_run", lambda pair: pair.pop("run")),
                           ("no_lessonless_run", lambda pair: pair["run"].pop("without")),
                           ("no_budget", no_budget), ("empty_prompt_hash", empty_prompt_hash)):
            verdict, detail, iid = self.unequal(edit, index=5)
            self.assertEqual((verdict, detail), ("FAIL", {"unequal_arms": [iid]}), name)

    def test_unequal_arms_fail_before_the_family_is_measured(self):
        # Fewer than k pairs is UNMEASURABLE (another family next time); runs that are not alike are a FAIL whatever
        # the counts, as in the placebo question.
        doc = copy.deepcopy(self.doc)
        del doc["transcript"]["effect"][doc["params"]["k"] - 1:]
        self.assertEqual(judge(doc)["verdicts"]["effect"], "UNMEASURABLE")
        doc["transcript"]["effect"][0]["run"]["with"]["effort"] = "high"
        self.assertEqual(judge(doc)["verdicts"]["effect"], "FAIL")

    def test_settings_outside_the_compared_fields_are_ignored(self):
        verdict, _detail, _iid = self.unequal(lambda pair: pair["run"]["with"].update(started_at="2026-10-31T00:00Z"))
        self.assertEqual(verdict, "PASS")

    def test_the_simulated_dispatcher_that_adds_text_to_the_lesson_run_never_passes(self):
        # Its settings are equal and its placebo arms are fair: only the prompt hash shows the extra text (E321).
        for seed in range(1, 21):
            doc = sim.run_drill(sim.BRAINS["unequal_effect_arms"], seed)
            result = judge(doc)
            self.assertEqual((result["verdicts"]["effect"], result["verdicts"]["placebo"]), ("FAIL", "PASS"), seed)
            self.assertEqual(len(result["details"]["effect"]["unequal_arms"]), 20)  # every pair, the first twenty named
            run = doc["transcript"]["effect"][0]["run"]
            self.assertEqual({f: run["with"][f] for f in judge_module.RUN_FIELDS},
                             {f: run["without"][f] for f in judge_module.RUN_FIELDS})
            self.assertNotEqual(run["with"][self.PROMPT], run["without"][self.PROMPT])


class Attempts(unittest.TestCase):
    """E323: every opened drill is an attempt, and a retry at the same α inflates a false PASS (on a calibrated family
    a lesson with no effect passes the effect question in 2.5% of 4,000 drills at α = 0.10; three tries, about 7%).
    Attempt i passes only at p < α · 2^-i, so all attempts together spend at most α. The attempt is in the answer
    key, committed before the run."""

    def setUp(self):
        self.doc = sim.run_drill(sim.LEARNER, 7)

    def effect(self, attempt, b, c):
        """The learner's drill as attempt ``attempt``, b pairs broken only with the lesson, c only without it."""
        doc = copy.deepcopy(self.doc)
        doc["answer_key"]["attempt"] = attempt
        doc["commitment_sha256"] = commitment(doc["answer_key"])
        for i, pair in enumerate(doc["transcript"]["effect"]):
            pair["without"], pair["with"] = (True, False) if i < b else (False, True) if i < b + c else (False, False)
        result = judge(doc)
        return result["verdicts"]["effect"], result["details"]["effect"]

    def test_the_simulation_commits_the_attempt(self):
        self.assertEqual(self.doc["answer_key"]["attempt"], 1)
        self.assertEqual(sim.run_drill(sim.LEARNER, 7, attempt=3)["answer_key"]["attempt"], 3)

    def test_attempt_i_is_judged_at_alpha_over_two_to_the_i(self):
        # p(2, 8) = 56/1024 passed at a fixed 0.10 and fails the first attempt (α_1 = 0.05); p(1, 7) = 9/256 passes the
        # first, not the second (α_2 = 0.025); p(0, 8) = 1/256 passes the fourth (α_4 = 0.00625), not the fifth.
        cases = {(1, 2, 8): "FAIL", (1, 1, 7): "PASS", (2, 1, 7): "FAIL", (4, 0, 8): "PASS", (5, 0, 8): "FAIL"}
        for (attempt, b, c), verdict in cases.items():
            got, detail = self.effect(attempt, b, c)
            self.assertEqual(got, verdict, (attempt, b, c, detail))
            self.assertEqual(detail["alpha"], f"{0.10 / 2 ** attempt:.6f}", attempt)

    def test_an_attempt_that_is_not_a_committed_count_fails_effect(self):
        for attempt in (None, 0, -1, "1", True, 1.0):
            doc = copy.deepcopy(self.doc)
            if attempt is None:
                del doc["answer_key"]["attempt"]
            else:
                doc["answer_key"]["attempt"] = attempt
            doc["commitment_sha256"] = commitment(doc["answer_key"])
            result = judge(doc)
            self.assertEqual((result["verdicts"]["effect"], result["details"]["effect"]),
                             ("FAIL", {"attempt_not_committed": True}), attempt)

    def test_an_attempt_changed_after_the_run_fails_everything(self):
        doc = copy.deepcopy(self.doc)
        doc["answer_key"]["attempt"] = 0  # the first attempt's α would be the whole 0.10
        self.assertEqual(set(judge(doc)["verdicts"].values()), {"FAIL"})

    def test_all_attempts_together_spend_at_most_alpha(self):
        alpha = Fraction(1, 10)
        self.assertEqual([judge_module.attempt_alpha(alpha, i) for i in (1, 2, 3)],
                         [Fraction(1, 20), Fraction(1, 40), Fraction(1, 80)])
        self.assertLess(sum(judge_module.attempt_alpha(alpha, i) for i in range(1, 100)), alpha)

    def test_a_later_attempt_has_less_power(self):
        powers = [effect_power(0.6, 0.2, 300, attempt=i)["PASS"] for i in (1, 2, 3)]
        self.assertEqual(powers, sorted(powers, reverse=True))
        self.assertGreater(powers[0], powers[2])


class RightLesson(unittest.TestCase):
    """E318: every imported lesson in a drill is planted, so withdrawing any of them at the first red would pass the
    wrong-lesson question; the positive control is a useful imported lesson that must survive a red not its own."""

    def setUp(self):
        self.doc = sim.run_drill(sim.LEARNER, 7)
        self.assertEqual(judge(self.doc)["verdicts"]["right_lesson"], "PASS")

    def first(self, doc):
        return judge(doc)["details"]["right_lesson"]["unrelated_seq"]

    def test_no_unrelated_red_while_given_is_unmeasurable(self):
        for change in ("no_red", "not_given", "own_trap"):
            doc = copy.deepcopy(self.doc)
            key = doc["answer_key"]
            for rec in doc["transcript"]["control"]:
                if rec["failed_test"] is not None:
                    if change == "no_red":
                        rec["failed_test"] = None
                    elif change == "not_given":
                        rec["injected"] = False
                    else:
                        rec["failed_test"] = key["instances"][rec["instance_id"]]["trap_test"]
            result = judge(doc)
            self.assertEqual((result["verdicts"]["right_lesson"], result["details"]["right_lesson"]),
                             ("UNMEASURABLE", {"unrelated_red": None}), change)

    def test_nothing_after_the_unrelated_red_is_unmeasurable(self):
        doc = copy.deepcopy(self.doc)
        first = self.first(doc)
        doc["transcript"]["control"] = [r for r in doc["transcript"]["control"] if r["seq"] <= first]
        self.assertEqual(judge(doc)["verdicts"]["right_lesson"], "UNMEASURABLE")

    def test_a_useful_lesson_superseded_or_narrowed_after_an_unrelated_red_fails(self):
        for state in ({"superseded": True, "excluded_conditions": []},
                      {"superseded": False, "excluded_conditions": [sim.SHARED]}):
            doc = copy.deepcopy(self.doc)
            first = self.first(doc)
            next(r for r in doc["transcript"]["control"] if r["seq"] == first)["lesson_state"] = state
            result = judge(doc)
            self.assertEqual(result["verdicts"]["right_lesson"], "FAIL", state)
            self.assertTrue(result["details"]["right_lesson"]["withdrawn"], state)

    def test_narrowing_by_a_condition_the_instance_lacks_is_no_withdrawal(self):
        doc = copy.deepcopy(self.doc)
        first = self.first(doc)
        next(r for r in doc["transcript"]["control"] if r["seq"] == first)["lesson_state"] = {
            "superseded": False, "excluded_conditions": ["another_condition"]}
        self.assertEqual(judge(doc)["verdicts"]["right_lesson"], "PASS")

    def test_a_useful_lesson_no_longer_given_after_an_unrelated_red_fails(self):
        doc = copy.deepcopy(self.doc)
        first = self.first(doc)
        later = [r for r in doc["transcript"]["control"] if r["seq"] > first]
        later[-1]["injected"] = False
        result = judge(doc)
        self.assertEqual(result["verdicts"]["right_lesson"], "FAIL")
        self.assertEqual(result["details"]["right_lesson"]["dropped_after"], [later[-1]["instance_id"]])

    def test_records_of_another_family_are_not_the_control(self):
        doc = copy.deepcopy(self.doc)
        doc["transcript"]["control"] = [dict(r, instance_id=w["instance_id"]) for r, w in
                                        zip(doc["transcript"]["control"], doc["transcript"]["wrong"])]
        self.assertEqual(judge(doc)["verdicts"]["right_lesson"], "UNMEASURABLE")

    def test_the_order_of_the_control_records_does_not_change_the_verdict(self):
        discarder = sim.run_drill(sim.BRAINS["llm_prior_discarder"], 7)
        for doc, verdict in ((self.doc, "PASS"), (discarder, "FAIL")):
            expected = judge(doc)
            self.assertEqual(expected["verdicts"]["right_lesson"], verdict)
            shuffled = copy.deepcopy(doc)
            shuffled["transcript"]["control"].reverse()
            self.assertEqual(judge(shuffled), expected, verdict)


class Calibration(unittest.TestCase):
    """E319: a family the lessonless arm breaks only 70% of the time makes 41% of drills UNMEASURABLE at k = 30 and
    21 broken; every such drill spends a family, so the operator calibrates before a family enters the pool."""

    def test_the_risk_of_an_unmeasurable_drill(self):
        k, need = sim.DEFAULT_PARAMS["k"], sim.DEFAULT_PARAMS["min_broken_without"]
        self.assertEqual((k, need), (30, 21))
        self.assertEqual(f"{float(unmeasurable_risk(Fraction(7, 10), k, need)):.3f}", "0.411")
        self.assertEqual(f"{float(unmeasurable_risk(Fraction(85, 100), k, need)):.3f}", "0.010")
        self.assertEqual(unmeasurable_risk(Fraction(1), k, need), 0)

    def test_a_family_is_ready_at_85_percent_over_20_runs(self):
        self.assertTrue(calibration(17, 20)["ready"])
        self.assertFalse(calibration(16, 20)["ready"])
        self.assertFalse(calibration(19, 19)["ready"])  # too few runs, however strong
        self.assertEqual(calibration(14, 20)["unmeasurable_risk"], "0.4112")
        with self.assertRaises(ValueError):
            calibration(21, 20)

    def test_the_gate_reads_a_point_estimate_so_the_risk_is_also_given_at_its_lower_bound(self):
        # 17 of 20 is ready, yet with 95% confidence the family breaks only at least 66% of the time (E319).
        ready = calibration(17, 20)
        self.assertEqual((ready["unmeasurable_risk"], ready["rate_lower_95"], ready["unmeasurable_risk_at_lower_95"]),
                         ("0.0097", "0.6563", "0.6148"))
        self.assertEqual(calibration(20, 20)["rate_lower_95"], "0.8609")  # 1 - 0.05 ** (1 / 20)
        self.assertEqual(calibration(0, 20)["rate_lower_95"], "0.0000")
        # What the gate lets through: a family truly breaking 70% or 75%, and turns away a true 85% one.
        chances = {p: f"{float(ready_chance(Fraction(p, 100))):.3f}" for p in (70, 75, 85)}
        self.assertEqual(chances, {70: "0.107", 75: "0.225", 85: "0.648"})

    def test_effect_power_is_the_reference_question(self):
        strong = effect_power(0.9, 0.1, 200)
        self.assertEqual(sum(strong.values()), 200)
        self.assertGreaterEqual(strong["PASS"], 195)
        weak = effect_power(0.5, 0.3, 200)
        self.assertGreater(weak["UNMEASURABLE"], 40)  # the lessonless arm breaks 70%: often below 21 of 30
        self.assertEqual(effect_power(0.9, 0.1, 50, seed=3), effect_power(0.9, 0.1, 50, seed=3))


class Vectors(unittest.TestCase):
    """The drill vectors the bootstrap applies are this judge's verdicts on these brains, unchanged."""

    def test_vector_files_reproduce_from_the_simulation(self):
        root = Path(__file__).resolve().parents[2] / "bootstrap" / "vectors"
        group = json.loads((root / "vectors.json").read_text())["drill"]
        names = [c["name"] for c in group["cases"]]
        self.assertEqual(names, [*sim.BRAINS, "tampered_key", "reused_instances", "missing_evidence",
                                 "stubborn_reversed", "second_attempt"])
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
                   "missing_evidence": {"use": "UNMEASURABLE", "effect": "FAIL", "persistence": "FAIL"},
                   "stubborn_reversed": {},  # reversed, the stubborn brain's records still fail wrong_lesson
                   "second_attempt": {"effect": "FAIL"}}  # p = 9/256 passes α_1, not α_2 (E323)
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

    def test_calibrate_and_effect_print_one_json_line(self):
        for argv, field, value in ((["calibrate", "17", "20"], "ready", True),
                                   (["effect", "0.9", "0.1", "20"], "PASS", effect_power(0.9, 0.1, 20)["PASS"]),
                                   (["effect", "0.6", "0.2", "200", "3"], "PASS",
                                    effect_power(0.6, 0.2, 200, attempt=3)["PASS"])):
            buf = io.StringIO()
            with redirect_stdout(buf):
                self.assertEqual(main(argv), 0)
            self.assertEqual(json.loads(buf.getvalue())[field], value, argv)


if __name__ == "__main__":
    unittest.main()
