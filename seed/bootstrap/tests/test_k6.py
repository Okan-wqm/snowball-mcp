"""K6's state and strength (E512): `k6.evaluate` turns an exam, its runs and the live prerequisites into the private
evaluation, `k6.summary` into the store's K6 document (E522) and `k6.signed_field` into the signed `k6`
field (E520), and the fence opens only on `live`.

The exam here is synthetic and says nothing of a real one: abstract modes, clauses and cases in four families, each
with twenty mutants (ten of them fail-safe inversions), fifty canaries and two cases, every mutant and canary caught.
From that strong exam each test removes one piece of evidence and checks the status, the reason and the numbers that
are kept. The real exam, its answers, mutants, canaries and held path list are private and never come here.
"""

import copy
import hashlib
import hmac
import json
import math
import unittest

from snowball_bootstrap import canon, k6

SALT = bytes(range(32))
OTHER_SALT = bytes(range(1, 33))
BASE = "b" * 40
PIN = "e" * 64
READY = {"hunter_seat": True, "hunter_model": "claude-opus-5-5", "oracle_model": "claude-sonnet-5-5"}
RECALL = {"held_paths": 10, "classified_safety": 10}
FAMILIES = ("P", "S", "A", "X")


def strong():
    """A synthetic exam that meets every number, and its runs."""
    exam = {"format": 1, "required_modes": [], "clauses": [], "exclusions": [], "cases": [], "mutants": [],
            "canaries": []}
    runs = {"exam_sha256": PIN, "base": {"commit": BASE, "failed_cases": []}, "mutants": [], "canaries": []}
    for f in FAMILIES:
        exam["required_modes"].append(f"mode-{f}")
        exam["clauses"].append({"id": f"cl-{f}", "family": f, "mode": f"mode-{f}", "kind": "behaviour",
                                "text": "a synthetic general requirement", "sources": []})
        for n in (1, 2):
            exam["cases"].append({"id": f"case-{f}-{n}", "clause": f"cl-{f}", "family": f, "unit": "unit-a",
                                  "input": {"x": n}, "expected": {"y": n},
                                  "visibility": "held" if n == 2 else "visible",
                                  "evidence": [{"kind": "automaton", "source": "ref-a"},
                                               {"kind": "standard", "source": "std-b"}]})
        for n in range(20):
            mutant = {"id": f"m-{f}-{n}", "family": f, "class": "fail_safe_inversion" if n < 10 else "ordinary"}
            if f == "P":
                mutant["output_shift_ppm"] = 8000
            exam["mutants"].append(mutant)
            runs["mutants"].append({"mutant": f"m-{f}-{n}", "subject": "ref", "failed_cases": [f"case-{f}-1"]})
        for n in range(50):
            exam["canaries"].append({"id": f"k-{f}-{n}", "family": f, "clauses": [f"cl-{f}"]})
            runs["canaries"].append({"canary": f"k-{f}-{n}", "failed_cases": [f"case-{f}-2"]})
    return exam, runs


def judge(exam, runs, previous=None, recall=RECALL, ready=READY, pin=PIN, base=BASE):
    return k6.evaluate(exam, runs, salt=SALT, exam_sha256=pin, base_commit=base, recall=recall, live_ready=ready,
                       previous=previous)


def run_of(runs, mutant, subject="ref"):
    return next(r for r in runs["mutants"] if r["mutant"] == mutant and r["subject"] == subject)


class StatusTest(unittest.TestCase):

    def test_a_strong_exam_with_its_prerequisites_is_live_and_the_field_is_canonical(self):
        """E512: the whole field is signed, so it holds no float (`canon`), and it states its scope."""
        exam, runs = strong()
        field = judge(exam, runs, previous="exam_strong")
        self.assertEqual(field["status"], "live")
        self.assertEqual(field["unmet"], [])
        self.assertFalse(field["fell_from_live"])
        self.assertEqual(field["exam_sha256"], PIN)
        self.assertEqual(field["base_commit"], BASE)
        self.assertEqual(field["base_red"], 0)
        self.assertEqual(sorted(field["families"]), sorted(FAMILIES))  # E has no clause: not judged, not blocking
        self.assertEqual(field["families"]["S"], {
            "cases": 2, "mutants_total": 20, "killed": 20, "fail_safe_inversion_total": 10,
            "fail_safe_inversion_survived": 0, "canaries_held": 50, "canaries_missed": 0, "miss_bound_ppm": 58156})
        self.assertEqual(field["scope"], "software logic only: no field I/O, no hardware in the loop")
        self.assertEqual(field["bound"], "clopper_pearson_one_sided_95")
        canon.canonical(field)

    def test_live_needs_strong_in_the_same_evaluation(self):  # live_without_strong
        """E512: the prerequisites of `live` (the hunter seat, a different oracle model) never stand in for the exam's
        strength, not even after a signed `live`."""
        exam, runs = strong()
        exam["canaries"] = [k for k in exam["canaries"] if not k["id"].startswith("k-A-") or k["id"] < "k-A-5"]
        runs["canaries"] = [r for r in runs["canaries"] if r["canary"] in {k["id"] for k in exam["canaries"]}]
        field = judge(exam, runs, previous="exam_strong")
        self.assertEqual(field["status"], "exam_built")
        self.assertIn("A:canaries_held", field["unmet"])
        self.assertEqual(judge(exam, runs, previous="live")["status"], "not_live")

    def test_each_step_names_what_it_lacks(self):
        """E512: no pin, an invalid exam or a required family without a clause is `not_live`; no base run on the named
        commit is `exam_built`; strength without the prerequisites of `live` is `exam_strong`."""
        exam, runs = strong()
        self.assertEqual(judge(exam, runs, pin=None)["unmet"], ["exam_unpinned"])
        self.assertEqual(judge(exam, runs, pin="E" * 64)["status"], "not_live")
        broken = copy.deepcopy(exam)
        broken["cases"][0]["visibility"] = "secret"
        self.assertEqual(judge(broken, runs)["unmet"], ["exam_invalid"])
        no_x = copy.deepcopy(exam)
        no_x["clauses"] = [c for c in no_x["clauses"] if c["family"] != "X"]
        no_x["cases"] = [c for c in no_x["cases"] if c["family"] != "X"]
        no_x["required_modes"].remove("mode-X")
        no_x["canaries"] = [k for k in no_x["canaries"] if k["family"] != "X"]
        self.assertEqual(judge(no_x, runs)["unmet"], ["X:no_clause"])
        field = judge(exam, runs, base="c" * 40)
        self.assertEqual((field["status"], field["unmet"], field["base_commit"]),
                         ("exam_built", ["base_run_missing"], None))
        self.assertEqual(judge(exam, runs, base=None)["status"], "exam_built")
        self.assertEqual(judge(exam, {"base": runs["base"]})["unmet"], ["runs_invalid"])
        self.assertEqual(judge(exam, {**runs, "exam_sha256": "f" * 64})["unmet"], ["runs_of_another_exam"])
        for ready, why in (({**READY, "hunter_seat": False}, "live:hunter_seat"),
                           ({**READY, "oracle_model": "claude-opus-5-0"}, "live:oracle_same_model_as_hunter"),
                           ({**READY, "oracle_model": "gpt"}, "live:model_unknown"),
                           (None, "live:prerequisites_unknown")):
            field = judge(exam, runs, ready=ready)
            self.assertEqual((field["status"], field["unmet"]), ("exam_strong", [why]))

    def test_the_store_holds_a_summary_and_the_signed_field_is_the_status_and_a_sealed_hash(self):
        # k6_counts_published
        """E520 (verifier finding 10, plan D6/D7, owner "yalnız bir bit + sayaç"), E522 (finding 2): the private side
        evaluates and the store gets ``summary``: the status reached, what it was reached for and an HMAC of the whole
        evaluation under the epoch's salt. No family, count, base-red number or unmet name is in it, so none is on
        `kos`'s disk; the signed field built from it carries the status, the fall from live, the pin and the scope."""
        exam, runs = strong()
        runs["canaries"][60]["failed_cases"] = []
        evaluation = judge(exam, runs)
        doc = k6.summary(evaluation, SALT, base_commit=BASE, safety_paths=["units/**", "alarm/*"])
        self.assertEqual(doc, {"schema": k6.SUMMARY_SCHEMA, "reached": "exam_built", "base_commit": BASE,
                               "safety_paths_sha256": k6.safety_paths_sha256(["alarm/*", "units/**", "alarm/*"]),
                               "sealed_sha256": hmac.new(SALT, k6.SEAL_TAG + canon.canonical(evaluation),
                                                         hashlib.sha256).hexdigest()})
        field = k6.signed_field(doc, SALT, exam_sha256=PIN, base_commit=BASE, safety_paths=["units/**", "alarm/*"],
                                previous="live")
        self.assertEqual(tuple(field), k6.PUBLIC_KEYS)
        self.assertEqual({k: v for k, v in field.items() if k != "sealed_sha256"},
                         {"status": "not_live", "fell_from_live": True, "exam_sha256": PIN, "scope": k6.SCOPE})
        for text in (json.dumps(doc), json.dumps(field)):
            for private in ("canary", "families", "unmet", "killed", "base_red", "S:", "58156"):
                self.assertNotIn(private, text)
        self.assertNotEqual(k6.summary(judge(*strong()), SALT, base_commit=BASE, safety_paths=["units/**"])
                            ["sealed_sha256"], doc["sealed_sha256"])
        self.assertNotEqual(k6.summary(evaluation, OTHER_SALT, base_commit=BASE, safety_paths=["units/**"])
                            ["sealed_sha256"], doc["sealed_sha256"])
        with self.assertRaises(k6.K6Error):
            k6.summary(evaluation, b"short", base_commit=BASE, safety_paths=["units/**"])
        with self.assertRaises(k6.K6Error):  # a summary is made with no previous status: the fall is the referee's
            k6.summary(judge(exam, runs, previous="live"), SALT, base_commit=BASE, safety_paths=["units/**"])
        with self.assertRaises(k6.K6Error):
            k6.signed_field(doc, b"short", exam_sha256=PIN, base_commit=BASE, safety_paths=["x"], previous=None)

    def test_the_signed_field_holds_only_for_this_epochs_base_and_safety_list(self):
        # k6_summary_base_unbound k6_summary_safety_unbound k6_fall_ignored k6_seal_unbound
        """E522: the status a summary reached is signed only for the copy base and the owner's safety list it was
        reached for; anything else, a summary of another base or list, or no summary, reaches nothing (`not_live`).
        After a signed `live` a summary that no longer reaches it falls (``fell_from_live``). The seal binds the
        summary and the previous status, so two runs that sign the same status for different reasons differ."""
        paths = ["units/**"]
        live = k6.summary(judge(*strong(), previous=None), SALT, base_commit=BASE, safety_paths=paths)
        self.assertEqual(live["reached"], "live")

        def signed(doc, previous=None, base=BASE, safety=paths):
            return k6.signed_field(doc, SALT, exam_sha256=PIN, base_commit=base, safety_paths=safety,
                                   previous=previous)
        self.assertEqual((signed(live)["status"], signed(live)["fell_from_live"]), ("live", False))
        self.assertEqual((signed(live, "live")["status"], signed(live, "live")["fell_from_live"]), ("live", False))
        for doc, base, safety in ((live, "c" * 40, paths), (live, BASE, ["units/**", "extra/**"]), (live, None, paths),
                                  (live, BASE, None), (None, BASE, paths), ({**live, "reached": "open"}, BASE, paths),
                                  ({**live, "families": {}}, BASE, paths), ({**live, "schema": "x"}, BASE, paths)):
            self.assertEqual(signed(doc, None, base, safety)["status"], "not_live", (doc, base, safety))
            self.assertEqual((signed(doc, "live", base, safety)["status"],
                              signed(doc, "live", base, safety)["fell_from_live"]), ("not_live", True))
        built = {**live, "reached": "exam_built"}
        self.assertEqual((signed(built, "live")["status"], signed(built, "live")["fell_from_live"]),
                         ("not_live", True))
        self.assertEqual(signed(built, "exam_strong")["status"], "exam_built")
        self.assertNotEqual(signed(built, "live")["sealed_sha256"], signed(None, "live")["sealed_sha256"])
        self.assertNotEqual(signed(live, None)["sealed_sha256"], signed(live, "exam_strong")["sealed_sha256"])
        self.assertEqual(signed(live, None, safety=["units/**", "units/**"])["status"], "live")  # order, repeats aside
        self.assertIsNone(k6.signed_field(live, SALT, exam_sha256="x", base_commit=BASE, safety_paths=paths,
                                          previous=None)["exam_sha256"])
        with self.assertRaises(k6.K6Error):
            signed(live, "open")

    def test_the_runs_name_the_exam_by_its_document_and_summarize_reads_bytes(self):  # k6_exam_id_not_bytes
        """E522: the store's pin hashes a manifest that lists the summary, so the runs name the exam they ran by the
        exam document's sha256 (``exam_id``); ``summarize`` reads the documents as the store holds them and measures
        the held paths with the matcher it is given. Unreadable bytes are missing evidence, never an error."""
        exam, runs = strong()
        raw = json.dumps(exam).encode("utf-8")
        runs["exam_sha256"] = k6.exam_id(raw)
        self.assertEqual(k6.exam_id(raw), hashlib.sha256(raw).hexdigest())
        held = ["units/a.rs", "units/b.rs"]

        def reached(raw=raw, runs=runs, is_safety=lambda path: path.startswith("units/")):
            return k6.summarize(raw, runs, held, READY, salt=SALT, base_commit=BASE, safety_paths=["units/**"],
                                is_safety=is_safety)["reached"]
        self.assertEqual(reached(), "live")
        self.assertEqual(reached(runs={**runs, "exam_sha256": PIN}), "exam_built")  # runs named by the store's pin
        self.assertEqual(reached(is_safety=lambda path: path.endswith("a.rs")), "exam_built")  # recall 1 of 2
        for bad in (b"\xff", b"{", None):
            self.assertEqual(reached(raw=bad), "not_live")

    def test_a_missed_canary_after_live_falls_back_to_not_live(self):  # missed_canary_keeps_live
        """E512: one missed canary ends `exam_strong`; after a signed `live` the status is `not_live`, never a middle
        state, and `fell_from_live` says why the merged safety commits must now be listed for the owner."""
        exam, runs = strong()
        runs["canaries"][60]["failed_cases"] = []  # a canary of family S that no case catches
        field = judge(exam, runs, previous="live")
        self.assertEqual((field["status"], field["fell_from_live"]), ("not_live", True))
        self.assertEqual(field["unmet"], ["S:canary_missed"])
        self.assertEqual(field["families"]["S"]["canaries_missed"], 1)
        self.assertEqual(judge(exam, runs, previous="exam_strong")["status"], "exam_built")

    def test_any_lost_evidence_after_live_falls_back_to_not_live(self):
        """E512: the status is computed afresh; a run that cannot be read is no reason to stay open."""
        exam, runs = strong()
        for bad in ({**runs, "canaries": "x"}, None, {**runs, "exam_sha256": "f" * 64}):
            field = judge(exam, bad, previous="live")
            self.assertEqual((field["status"], field["fell_from_live"]), ("not_live", True))
        field = judge(exam, runs, previous="live", recall=None)
        self.assertEqual((field["status"], field["unmet"], field["fence_recall"]), ("not_live", ["fence_recall"], None))
        with self.assertRaises(k6.K6Error):
            judge(exam, runs, previous="open")

    def test_the_signed_field_names_no_case(self):
        """E512: case, clause, mutant and canary ids stay private; the base run is signed as a hash over tokens."""
        exam, runs = strong()
        runs["base"]["failed_cases"] = ["case-S-2"]
        field = judge(exam, runs)
        text = canon.canonical(field).decode("utf-8")
        for word in ("case-", "cl-", "m-P", "k-S", "mode-"):
            self.assertNotIn(word, text)
        self.assertEqual(field["base_red"], 1)
        vector = k6.base_vector(exam, runs, SALT)
        self.assertEqual(field["base_vector_sha256"], canon.sha256_hex(canon.canonical(vector)))
        self.assertIn([k6.case_token(SALT, "case-S-2"), False], vector)
        self.assertEqual(len(vector), 8)


class StrengthTest(unittest.TestCase):

    def test_kill_rate_is_measured_against_the_reference(self):  # kill_vs_base_not_ref
        """E512 (critique §5): a case red on the base makes "killed" there mean nothing, so the base runs of mutants
        are never counted; a mutant with a base run alone is unmeasured, and unmeasured is not killed."""
        exam, runs = strong()
        for n in range(3):
            run_of(runs, f"m-A-{n}")["failed_cases"] = []
            runs["mutants"].append({"mutant": f"m-A-{n}", "subject": "base", "failed_cases": ["case-A-1"]})
        field = judge(exam, runs)
        self.assertEqual(field["families"]["A"]["killed"], 17)
        self.assertIn("A:kill_rate", field["unmet"])
        runs["mutants"] = [r for r in runs["mutants"] if r["mutant"] != "m-A-0" or r["subject"] == "base"]
        self.assertEqual(judge(exam, runs)["families"]["A"]["killed"], 17)

    def test_the_kill_floor_is_nine_in_ten(self):
        """E512: 18 of 20 is the floor and passes; 17 of 20 does not; a family without mutants does not."""
        exam, runs = strong()
        for n in (10, 11):
            run_of(runs, f"m-X-{n}")["failed_cases"] = []
        self.assertNotIn("X:kill_rate", judge(exam, runs)["unmet"])
        run_of(runs, "m-X-12")["failed_cases"] = []
        self.assertIn("X:kill_rate", judge(exam, runs)["unmet"])
        exam, runs = strong()
        exam["mutants"] = [m for m in exam["mutants"] if m["family"] != "P"]
        runs["mutants"] = [r for r in runs["mutants"] if not r["mutant"].startswith("m-P-")]
        self.assertEqual(judge(exam, runs)["unmet"], ["P:kill_rate"])

    def test_a_surviving_fail_safe_inversion_blocks_strong(self):  # fail_safe_survivor_tolerated
        """E512: one fail-safe inversion of ten survives; the kill rate (19/20) passes, the exam is still not strong."""
        exam, runs = strong()
        run_of(runs, "m-S-3")["failed_cases"] = []
        field = judge(exam, runs)
        self.assertEqual(field["unmet"], ["S:fail_safe_inversion_survived"])
        self.assertEqual((field["families"]["S"]["killed"], field["families"]["S"]["fail_safe_inversion_survived"]),
                         (19, 1))

    def test_each_family_is_judged_by_its_own_cases(self):  # family_kills_pooled
        """E512: a family's mutant that only another family's case fails is not killed for it; a weak family is not
        hidden by the strong ones."""
        exam, runs = strong()
        for n in (10, 11, 12):
            run_of(runs, f"m-S-{n}")["failed_cases"] = ["case-P-1"]
        field = judge(exam, runs)
        self.assertEqual(field["families"]["S"]["killed"], 17)
        self.assertEqual(field["unmet"], ["S:kill_rate"])

    def test_canaries_need_fifty_and_none_missed(self):  # bound_wrong_n
        """E512: 49 held canaries are too few; the bound signed next to the counts is computed from the held count, not
        from the caught one."""
        exam, runs = strong()
        exam["canaries"] = [k for k in exam["canaries"] if k["id"] != "k-X-0"]
        runs["canaries"] = [r for r in runs["canaries"] if r["canary"] != "k-X-0"]
        field = judge(exam, runs)
        self.assertEqual(field["unmet"], ["X:canaries_held"])
        self.assertEqual(field["families"]["X"]["miss_bound_ppm"], 59307)
        exam, runs = strong()
        runs["canaries"][0]["failed_cases"] = []
        field = judge(exam, runs)
        self.assertEqual(field["families"]["P"]["canaries_missed"], 1)
        self.assertEqual(field["families"]["P"]["miss_bound_ppm"], k6.miss_bound_ppm(1, 50))
        self.assertEqual(field["families"]["P"]["miss_bound_ppm"], 91399)

    def test_a_case_red_on_the_base_catches_only_the_fix_it_is_about(self):
        """E512: a base-red case of another clause would "catch" every canary; it catches only the canary whose clauses
        hold it (a bad fix that leaves its own case red is caught)."""
        exam, runs = strong()
        exam["clauses"].append({"id": "cl-S2", "family": "S", "mode": "mode-S2", "kind": "behaviour",
                                "text": "a second synthetic requirement", "sources": []})
        exam["required_modes"].append("mode-S2")
        exam["cases"].append({**copy.deepcopy(exam["cases"][2]), "id": "case-S-3", "clause": "cl-S2"})
        runs["base"]["failed_cases"] = ["case-S-3"]
        runs["canaries"][50]["failed_cases"] = ["case-S-3"]  # k-S-0 names cl-S only
        runs["canaries"][51]["failed_cases"] = ["case-S-3"]
        exam["canaries"][51]["clauses"] = ["cl-S2"]
        field = judge(exam, runs)
        self.assertEqual(field["families"]["S"]["canaries_missed"], 1)
        self.assertEqual(field["unmet"], ["S:canary_missed"])
        self.assertEqual(field["base_red"], 1)

    def test_fence_recall_must_be_complete(self):  # recall_partial_accepted
        """E512: every held, labelled safety path is classified by the fence's own matcher, or the exam is not strong;
        an empty list measures nothing."""
        exam, runs = strong()
        for recall in ({"held_paths": 10, "classified_safety": 9}, {"held_paths": 0, "classified_safety": 0},
                       {"held_paths": 10}):
            self.assertEqual(judge(exam, runs, recall=recall)["unmet"], ["fence_recall"], recall)
        held = ["a/safe_x.rs", "b/alarm.ts", "a/safe_x.rs", "c/pump.rs"]
        self.assertEqual(k6.fence_recall(held, lambda p: "safe" in p or "alarm" in p),
                         {"held_paths": 3, "classified_safety": 2})

    def test_an_empty_site_data_family_waits_and_a_filled_one_is_judged(self):
        """E512, owner decision (e) open: family E may stay empty until site data exists; a clause in it is judged
        like any other, and an equipment case needs a datasheet."""
        exam, runs = strong()
        exam["clauses"].append({"id": "cl-E", "family": "E", "mode": "mode-E", "kind": "limit", "text": "a limit",
                                "sources": [{"kind": "datasheet", "source": "sheet-1"}]})
        exam["required_modes"].append("mode-E")
        exam["cases"].append({"id": "case-E-1", "clause": "cl-E", "family": "E", "unit": "unit-e", "input": {},
                              "expected": {}, "visibility": "held",
                              "evidence": [{"kind": "datasheet", "source": "sheet-1"},
                                           {"kind": "standard", "source": "std-b"}]})
        field = judge(exam, runs)
        self.assertEqual(field["unmet"], ["E:canaries_held", "E:kill_rate"])
        self.assertEqual(field["families"]["E"]["cases"], 1)
        self.assertEqual(sorted(k6.SITE_DATA_FAMILIES), ["E"])


class CaseTokenTest(unittest.TestCase):

    def test_case_ids_are_hmac_tokens_of_the_epoch_salt(self):  # case_id_unsalted
        """E512 (F-5): an id such as `<family>.<mode>.<n>` is guessable, so outside the private side a case is named
        by HMAC-SHA256 under the epoch's salt: another salt names it differently and nobody without the salt can
        compute it; a salt under 256 bits is refused."""
        token = k6.case_token(SALT, "S.mode.0031")
        self.assertRegex(token, r"^[0-9a-f]{64}\Z")
        self.assertEqual(token, k6.case_token(SALT, "S.mode.0031"))
        self.assertNotEqual(token, k6.case_token(OTHER_SALT, "S.mode.0031"))
        self.assertNotEqual(token, k6.case_token(SALT, "S.mode.0032"))
        import hashlib
        import hmac
        self.assertEqual(token, hmac.new(SALT, b"snowball-k6-case\x00S.mode.0031", hashlib.sha256).hexdigest())
        for salt in (SALT[:31], "x" * 32, None):
            with self.assertRaises(k6.K6Error):
                k6.case_token(salt, "S.mode.0031")
        exam, runs = strong()
        with self.assertRaises(k6.K6Error):
            k6.evaluate(exam, runs, salt=b"short", exam_sha256=PIN, base_commit=BASE, recall=RECALL,
                        live_ready=READY, previous=None)


class BoundTest(unittest.TestCase):

    def test_the_bound_is_the_exact_one_sided_clopper_pearson(self):
        """E512: with no miss the bound is 1 - 0.05^(1/n): 13.9 % at 20 and 5.8 % at 50, rounded up to a whole ppm;
        with misses it matches an independent float bisection of the binomial tail to the ppm; it falls with n,
        rises with misses, and no canary or all missed bounds nothing."""
        self.assertEqual(k6.miss_bound_ppm(0, 20), 139109)
        self.assertEqual(k6.miss_bound_ppm(0, 50), 58156)
        for n in (1, 7, 20, 49, 50, 51, 200):
            self.assertEqual(k6.miss_bound_ppm(0, n), math.ceil((1 - 0.05 ** (1 / n)) * 10**6), n)

        def tail(k, n, p):
            return sum(math.comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(k + 1))

        for k, n in ((1, 50), (2, 100), (5, 60)):
            lo, hi = 0.0, 1.0
            for _ in range(100):
                mid = (lo + hi) / 2
                lo, hi = (lo, mid) if tail(k, n, mid) <= 0.05 else (mid, hi)
            self.assertLessEqual(abs(k6.miss_bound_ppm(k, n) - hi * 10**6), 1, (k, n))
        self.assertEqual(k6.miss_bound_ppm(1, 50), 91399)
        self.assertLess(k6.miss_bound_ppm(0, 60), k6.miss_bound_ppm(0, 50))
        self.assertGreater(k6.miss_bound_ppm(1, 50), k6.miss_bound_ppm(0, 50))
        self.assertEqual((k6.miss_bound_ppm(0, 0), k6.miss_bound_ppm(4, 4)), (10**6, 10**6))
        for bad in ((-1, 5), (0, -1), (0.0, 5), (0, "50")):
            with self.assertRaises(k6.K6Error):
                k6.miss_bound_ppm(*bad)


class ToleranceTest(unittest.TestCase):

    def test_the_oxygen_tolerance_widens_with_salinity_past_the_anchors_disagreement(self):
        """E512 (critique §2): the two formulations disagree by 0.259 % at S = 0, 0.445 % at S = 35 and 0.527 % at
        S = 40 (re-measured by the judge); the tolerance 0.35 % + 0.007 %/ppt covers each, and a physics mutant's
        smallest shift lies past the widest tolerance, so a mutant is never inside it."""
        for s, gap_ppm in ((0, 2590), (35, 4450), (40, 5270)):
            self.assertGreater(k6.do_saturation_tolerance_ppm(s), gap_ppm, s)
        self.assertEqual((k6.do_saturation_tolerance_ppm(0), k6.do_saturation_tolerance_ppm(40)), (3500, 6300))
        self.assertEqual(k6.do_saturation_tolerance_ppm("35.5"), 5985)
        self.assertGreater(k6.PHYSICS_SHIFT_PPM[0], k6.do_saturation_tolerance_ppm(k6.SALINITY_PPT[1]))
        for s in (-1, 41, "40.01"):
            with self.assertRaises(k6.K6Error):
                k6.do_saturation_tolerance_ppm(s)
        self.assertTrue(k6.do_saturation_within(9.0 * 1.0034, 9.0, 0))
        self.assertFalse(k6.do_saturation_within(9.0 * 1.0036, 9.0, 0))
        self.assertTrue(k6.do_saturation_within(7.0 * 0.994, 7.0, 40))
        for got in (float("nan"), float("inf"), None, True, "9.0"):
            self.assertFalse(k6.do_saturation_within(got, 9.0, 0), got)
        self.assertFalse(k6.do_saturation_within(0.0, 0.0, 0))


class AuthoringFormatTest(unittest.TestCase):
    """E512: the validator of the authoring format; one broken rule per check, each named."""

    def problems(self, change):
        exam, _runs = strong()
        change(exam)
        return k6.validate_exam(exam)

    def test_the_synthetic_exam_is_valid_and_strict_about_its_keys(self):
        self.assertEqual(self.problems(lambda e: None), [])
        self.assertEqual(self.problems(lambda e: e.update(extra=1)), ["unknown key extra"])
        self.assertEqual(self.problems(lambda e: e.update(format=2)), ["format is not 1"])
        self.assertEqual(self.problems(lambda e: e.pop("canaries")), ["canaries is not a list"])
        self.assertEqual(self.problems(lambda e: e["cases"][0].update(kills=[])), ["cases[0]: unknown key kills"])
        self.assertEqual(self.problems(lambda e: e["mutants"][0].pop("class")), ["mutants[0]: missing class"])
        self.assertEqual(self.problems(lambda e: e["clauses"][0].update(family="Q")),
                         ["clauses[0]: unknown family 'Q'"])
        self.assertEqual(k6.validate_exam([]), ["the exam is not an object"])
        self.assertIn("cases[1]: duplicate id case-P-1",
                      self.problems(lambda e: e["cases"][1].update(id="case-P-1")))

    def test_any_json_value_in_any_field_is_a_problem_never_a_crash(self):
        """E512: the judge reads the exam and its runs whatever their shape: each field of each record and each run,
        replaced by a list, an object, null or a number, gives a named problem and no exception, and such an exam
        or such runs keep K6 shut."""
        exam, runs = strong()
        for section in ("clauses", "exclusions", "cases", "mutants", "canaries"):
            if section == "exclusions":
                exam["exclusions"].append({"mode": "mode-x", "family": "S", "reason": "r"})
                exam["required_modes"].append("mode-x")
            for key in list(exam[section][0]):
                if key in ("input", "expected"):
                    continue  # any JSON value is an input or an answer
                for value in ([], {}, None, 7) if key != "sources" else ({}, None, 7, [7]):
                    broken = copy.deepcopy(exam)
                    broken[section][0][key] = value
                    self.assertTrue(k6.validate_exam(broken), (section, key, value))
                    self.assertEqual(judge(broken, runs)["status"], "not_live")
        exam, runs = strong()
        for path in (("exam_sha256",), ("base", "commit"), ("base", "failed_cases"), ("mutants", 0, "mutant"),
                     ("mutants", 0, "subject"), ("mutants", 0, "failed_cases"), ("canaries", 0, "canary"),
                     ("canaries", 0, "failed_cases")):
            for value in ([[]], {}, None, 7):
                broken = copy.deepcopy(runs)
                holder = broken
                for step in path[:-1]:
                    holder = holder[step]
                holder[path[-1]] = value
                self.assertTrue(k6.validate_runs(exam, broken), (path, value))
                self.assertEqual(judge(exam, broken)["unmet"], ["runs_invalid"])

    def test_every_clause_has_a_case_and_every_case_a_clause(self):
        """Owner rule: each case is bound to a clause, a case without one is discarded; each clause has a case."""
        def orphan(e):
            e["cases"][0]["clause"] = "cl-none"
        self.assertEqual(self.problems(orphan),
                         ["case case-P-1: no clause 'cl-none' (a case without a clause is discarded)"])
        def uncovered(e):
            e["cases"] = [c for c in e["cases"] if c["family"] != "A"]
        self.assertEqual(self.problems(uncovered), ["clause cl-A: no case"])
        def other_family(e):
            e["cases"][0]["family"] = "S"
        self.assertEqual(self.problems(other_family), ["case case-P-1: family S is not its clause's P"])

    def test_every_fault_mode_is_answered_once(self):
        """D7: every mode of the required list gets a clause or an exclusion with a reason, never both."""
        self.assertEqual(self.problems(lambda e: e["required_modes"].append("mode-new")),
                         ["mode mode-new has neither a clause nor an exclusion"])
        def excluded(e):
            e["required_modes"].append("mode-new")
            e["exclusions"].append({"mode": "mode-new", "family": "S", "reason": "needs a second probe"})
        self.assertEqual(self.problems(excluded), [])
        def no_reason(e):
            e["exclusions"].append({"mode": "mode-P", "family": "P", "reason": " "})
        self.assertEqual(self.problems(no_reason),
                         ["exclusion of mode-P: no reason", "mode mode-P is both answered and excluded"])

    def test_a_case_rests_on_two_independent_evidences(self):
        def one(e):
            e["cases"][0]["evidence"] = [{"kind": "formula", "source": "f-1"}, {"kind": "table", "source": "f-1 "}]
        self.assertEqual(self.problems(one), ["case case-P-1: fewer than two independent evidences"])
        def kind(e):
            e["cases"][0]["evidence"][0]["kind"] = "opinion"
        self.assertEqual(self.problems(kind), ["case case-P-1 evidence[0]: unknown evidence kind 'opinion'",
                                               "case case-P-1: fewer than two independent evidences"])
        def two_formulations(e):
            e["cases"][0]["evidence"] = [{"kind": "formula", "source": "f-1"}, {"kind": "formula", "source": "f-2"}]
        self.assertEqual(self.problems(two_formulations), [])

    def test_limits_budgets_and_equipment_rest_on_cited_data(self):
        """D7 and owner decision (e): a limit cites a source; a time budget rests on owner-supplied site data; an
        equipment case carries a datasheet."""
        def limit(e):
            e["clauses"][0]["kind"] = "limit"
        self.assertEqual(self.problems(limit), ["clause cl-P: a limit without a cited source"])
        def budget(e):
            e["clauses"][1].update(kind="time_budget", sources=[{"kind": "formula", "source": "assumed"}])
        self.assertEqual(self.problems(budget), ["clause cl-S: a time budget without owner-supplied site data"])
        def budget_with_data(e):
            e["clauses"][1].update(kind="time_budget", sources=[{"kind": "site_data", "source": "site-1"}])
        self.assertEqual(self.problems(budget_with_data), [])
        def equipment(e):
            e["clauses"].append({"id": "cl-E", "family": "E", "mode": "mode-E", "kind": "behaviour", "text": "t",
                                 "sources": []})
            e["cases"].append({**copy.deepcopy(e["cases"][0]), "id": "case-E-1", "clause": "cl-E", "family": "E"})
        self.assertEqual(self.problems(equipment), ["case case-E-1: an equipment case without a datasheet"])

    def test_physics_mutants_are_sized_to_the_tolerance(self):
        """D7 (critique §2): a physics mutant moves the output 0.7-1 %; a blunt one (a 1 % coefficient change moves
        it about 5.6 times) or one inside the tolerance is not admitted, nor one whose shift was not measured."""
        for shift in (6999, 10001, 56000, None, 8000.0, True):
            def change(e, shift=shift):
                if shift is None:
                    e["mutants"][0].pop("output_shift_ppm")
                else:
                    e["mutants"][0]["output_shift_ppm"] = shift
            self.assertEqual(len(self.problems(change)), 1, shift)
        for shift in (7000, 10000):
            self.assertEqual(self.problems(lambda e, s=shift: e["mutants"][0].update(output_shift_ppm=s)), [])
        self.assertEqual(self.problems(lambda e: e["mutants"][0].update(**{"class": "boundary"})),
                         ["mutant m-P-0: unknown class 'boundary'"])

    def test_a_canary_names_clauses_of_its_own_family(self):
        self.assertEqual(self.problems(lambda e: e["canaries"][0].update(clauses=["cl-S"])),
                         ["canary k-P-0: names a clause that is not one of its family's"])
        self.assertEqual(self.problems(lambda e: e["canaries"][0].update(clauses=[])),
                         ["canary k-P-0: clauses is not a non-empty list of ids"])

    def test_runs_fit_the_exam(self):
        exam, runs = strong()
        self.assertEqual(k6.validate_runs(exam, runs), [])
        bad = copy.deepcopy(runs)
        bad["mutants"].append({"mutant": "m-P-0", "subject": "ref", "failed_cases": []})
        bad["canaries"][0]["failed_cases"] = ["case-none"]
        bad["base"]["commit"] = "b" * 39
        self.assertEqual(k6.validate_runs(exam, bad), [
            "base: not a commit and its failed cases", "mutants[80]: a second run of m-P-0 on ref",
            "canaries[0]: failed_cases is not a list of distinct case ids"])
        self.assertEqual(k6.validate_runs(exam, json.loads(json.dumps(runs)) | {"extra": 1}),
                         ["the runs are not an object of exam_sha256, base, mutants and canaries"])


if __name__ == "__main__":
    unittest.main()
