"""Open claims: age, answer, closure (`tohum/29x`; the owner's decision of 2026-11-14, E596). The trailing comment on a
test names the mutants it kills (`local/mutate.py`)."""

import hashlib
import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path

from snowball_bootstrap import claims, cli, config, stages, state as st
from snowball_bootstrap.config import ConfigError
from snowball_bootstrap.decide import decide

from helpers import commit, make_repo, sh
from test_decision import A, B, C, CODE_JOBS, green_run, meta_, not_refuted, refuted, state0, survived
from test_flow import Flow

D, E = "d" * 40, "e" * 40
CID = "0123456789ab"
OTHER = "ba9876543210"
NOW = "2026-11-14T12:00:00Z"
STAGE1 = stages.load(1)


def tar_of(files: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        for name, content in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))
    return buf.getvalue()


def claim(cid=CID, first=A, reproducer=None, paths=("referee/x.py",)):
    refs = [{"path": p, "line_start": 1, "line_end": 1} for p in paths]
    return {"id": cid, "claim": f"claim {cid}", "evidence_refs": refs,
            "reproducer": reproducer, "observed": None, "first_head": first, "rewritten": False}


def row(heads=0, opened="2026-11-10T12:00:00Z", basis="run", challenged=()):
    return {"accepted_heads": heads, "opened_at": opened, "basis": basis, "challenged": list(challenged)}


def book(rows, **kw):
    b = claims.empty_book()
    b["claims"] = rows
    b.update(kw)
    return b


def answer_doc(cid=CID, kind="fix", path="referee/x.py", start=1, end=2, **extra):
    doc = {"id": f"claim-{cid}", "kind": "claim_answer", "ref": cid, "state": "answer", "answer": kind,
           "evidence_refs": [{"path": path, "line_start": start, "line_end": end}]}
    doc.update(extra)
    return json.dumps(doc).encode()


def answers(cid=CID, sha="a" * 64, problem=None, kind="fix"):
    return {"answers": [{"ref": cid, "sha256": sha, "answer": kind, "problem": problem}], "dates": {}, "waived": [],
            "refused": []}


def judge(state, kind="spec", table=None, meta_claims=None, min_attempts=2, rival=None, run=None, repro=None,
          jobs=None, **meta_kw):
    meta = meta_(kind, state, claims=meta_claims or {}, **meta_kw)
    if kind == "spec":
        rival, jobs = rival or not_refuted(), jobs or {"cagir": "success"}
    else:
        rival, run, jobs = rival or not_refuted(), run or green_run(), jobs or CODE_JOBS
    return decide(meta, run, rival, None, jobs, min_attempts, 3, state_repro=repro, now=NOW, table=table)


class AnswerRecords(unittest.TestCase):
    TREE = {"referee/x.py": b"a\nb\nc\n", "reports/claim-0123456789ab.json": answer_doc()}

    def read(self, **files):
        tree = dict(self.TREE)
        tree.update({k.replace("__", "/").replace("_dot_", "."): v for k, v in files.items()})
        return claims.read_answers(tar_of(tree))

    def test_a_well_formed_answer_is_read_with_its_hash(self):  # claim_answer_hash_dropped
        rows = self.read()
        self.assertEqual(rows, [{"ref": CID, "sha256": hashlib.sha256(answer_doc()).hexdigest(), "answer": "fix",
                                 "paths": ["referee/x.py"], "problem": None}])

    def test_every_shape_fault_is_named_never_read_as_an_answer(self):  # claim_answer_shape_unchecked
        cases = {
            "malformed": [answer_doc(kind="maybe"), answer_doc(state="open"), answer_doc(extra_key=1), b"[1]", b"{",
                          answer_doc(note=5), answer_doc(note="x" * 2001), answer_doc(kind_="x")],
            "id_mismatch": [answer_doc(id="claim-ffffffffffff"), answer_doc(ref=OTHER)],
            "evidence_refs": [answer_doc(start=0), answer_doc(start=3, end=2), answer_doc(start="1")],
            "ref_missing:referee/y.py": [answer_doc(path="referee/y.py")],
            "ref_lines:referee/x.py": [answer_doc(end=4)],
        }
        for problem, docs in cases.items():
            for doc in docs:
                with self.subTest(problem=problem, doc=doc[:60]):
                    tree = dict(self.TREE, **{"reports/claim-0123456789ab.json": doc})
                    self.assertEqual(claims.read_answers(tar_of(tree))[0]["problem"], problem)
        # The record's own fields beside a forged kind (`answer_doc(kind_="x")` adds a key): still malformed.
        self.assertIsNone(self.read()[0]["problem"])

    def test_only_records_directly_under_reports_are_answers(self):  # claim_answer_depth_open
        tree = {"referee/x.py": b"a\n", "reports/sub/claim-0123456789ab.json": answer_doc(end=1),
                "claim-0123456789ab.json": answer_doc(end=1), "reports/claim-XYZ.json": answer_doc(end=1)}
        self.assertEqual(claims.read_answers(tar_of(tree)), [])

    def test_a_fix_cites_a_changed_file_and_a_refutation_the_claims_own_evidence(self):  # claim_fix_change_unchecked
        rows = [{"ref": CID, "sha256": "s", "answer": "fix", "paths": ["referee/x.py"], "problem": None}]
        open_claims = [claim()]
        self.assertIsNone(claims.engage(rows, open_claims, {CID: {"referee/x.py"}})[0]["problem"])
        self.assertEqual(claims.engage(rows, open_claims, {CID: {"referee/z.py"}})[0]["problem"], "fix_cites_no_change")
        self.assertEqual(claims.engage(rows, open_claims, {CID: None})[0]["problem"], "first_head_unknown")
        self.assertEqual(claims.engage(rows, open_claims, {})[0]["problem"], "first_head_unknown")
        refute = [dict(rows[0], answer="refute", paths=["spec/a.md"])]  # claim_refute_unanchored
        self.assertEqual(claims.engage(refute, open_claims, {})[0]["problem"], "refute_cites_no_claim_path")
        self.assertIsNone(claims.engage([dict(refute[0], paths=["referee/x.py"])], open_claims, {})[0]["problem"])
        self.assertIsNone(claims.engage(refute, [claim(paths=())], {})[0]["problem"])  # a claim citing nothing
        self.assertEqual(claims.engage(rows, [claim(OTHER)], {}), [])  # not open: no answer

    def test_a_fix_cites_a_changed_file_of_the_claims_own_evidence(self):  # claim_fix_any_changed_file
        """A fix that cites only some other changed file answers nothing (the verifier of epoch L: with 100 heads
        since the first head, every file is a changed file); a claim citing nothing takes any changed file."""
        rows = [{"ref": CID, "sha256": "s", "answer": "fix", "paths": ["referee/z.py"], "problem": None}]
        changed = {CID: {"referee/z.py", "referee/x.py"}}
        self.assertEqual(claims.engage(rows, [claim()], changed)[0]["problem"], "fix_cites_no_claim_change")
        both = [dict(rows[0], paths=["referee/x.py", "referee/z.py"])]
        self.assertIsNone(claims.engage(both, [claim()], changed)[0]["problem"])
        unchanged = {CID: {"referee/z.py"}}  # the claim's own file is cited but did not change
        self.assertEqual(claims.engage(both, [claim()], unchanged)[0]["problem"], "fix_cites_no_claim_change")
        self.assertIsNone(claims.engage(rows, [claim(paths=())], changed)[0]["problem"])


class BookShape(unittest.TestCase):
    def test_a_state_without_the_book_validates_as_it_always_did(self):  # claim_book_required
        st.validate(state0())
        st.validate(state0(open_claims=[claim()]))

    def test_the_book_is_validated_and_holds_only_open_claims(self):  # claim_book_unvalidated
        good = state0(open_claims=[claim()], claim_book=book({CID: row()}))
        self.assertIs(st.validate(good), good)
        bad = [book({OTHER: row()}), book({CID: row(heads=-1)}), book({CID: dict(row(), extra=1)}),
               book({CID: row(basis="guess")}), book({CID: row(opened="yesterday")}),
               book({CID: row(challenged=["x"])}), dict(book({}), closed={"observed": 0}),
               dict(book({}), recent=[{"id": CID, "how": "magic", "accepted_heads": 1, "days": 1}]),
               dict(book({}), evicted=True), "book"]
        for b in bad:
            with self.subTest(book=b):
                with self.assertRaises(ConfigError):
                    st.validate(state0(open_claims=[claim()], claim_book=b))

    def test_seeded_age_counts_the_survivors_after_the_first_head(self):  # claim_seeded_age_zero
        arts = survived(A) + [{"sha": B, "outcome": "refuted"}] + survived(C, D)
        state = state0(open_claims=[claim(first=A)], rival_artifacts=arts)
        seen = claims.Claims(state, {"dates": {CID: "2026-11-01T12:00:00Z"}}, NOW)
        self.assertEqual(seen.book["claims"][CID], {"accepted_heads": 2, "opened_at": "2026-11-01T12:00:00Z",
                                                    "basis": "seeded", "challenged": []})
        unknown = claims.Claims(state0(open_claims=[claim(first=E)], rival_artifacts=arts), {}, NOW)
        self.assertEqual(unknown.book["claims"][CID]["accepted_heads"], 3)  # every survivor: not held, so not younger


class AgeAndOverdue(unittest.TestCase):
    def test_an_accepted_head_ages_every_open_claim_a_rejected_one_none(self):  # claim_age_counts_rejected_head
        state = state0(open_claims=[claim()], claim_book=book({CID: row(heads=0)}))
        accepted = judge(state)
        self.assertEqual(accepted["verdict"], "frozen")
        self.assertEqual(accepted["state"]["claim_book"]["claims"][CID]["accepted_heads"], 1)
        rejected = judge(state, pre_reasons=["seed_modified"])
        self.assertEqual(rejected["verdict"], "rejected")
        self.assertEqual(rejected["state"]["claim_book"]["claims"][CID]["accepted_heads"], 0)

    def test_a_noop_head_ages_nothing(self):  # claim_age_counts_noop
        state = state0(open_claims=[claim()], claim_book=book({CID: row(heads=1)}))
        res = decide(meta_("none", state, claims={}), None, None, None, {}, 2, 3, now=NOW)
        self.assertEqual(res["verdict"], "noop")
        self.assertEqual(res["state"]["claim_book"]["claims"][CID]["accepted_heads"], 1)
        self.assertEqual(res["claims"]["items"][0]["accepted_heads"], 1)  # claims_block_missing_on_noop

    def test_a_new_claim_starts_at_zero_on_the_run_that_opened_it(self):  # claim_age_counts_the_first_head
        res = decide(meta_("code", state0(), claims={}), green_run(), refuted("c"),
                     [{"attempt_index": 0, "reproduced": False}], dict(CODE_JOBS, yeniden="success"), 2, 3, now=NOW)
        self.assertEqual(res["verdict"], "accepted")
        cid = res["state"]["open_claims"][0]["id"]
        self.assertEqual(res["state"]["claim_book"]["claims"][cid],
                         {"accepted_heads": 0, "opened_at": NOW, "basis": "run", "challenged": []})

    def test_overdue_warns_in_stage_0_and_changes_no_verdict(self):  # claim_overdue_in_stage0_rejects
        state = state0(open_claims=[claim()], claim_book=book({CID: row(heads=2)}))
        res = judge(state)
        self.assertEqual((res["verdict"], res["reasons"]), ("frozen", []))
        self.assertIn(f"claim_overdue:{CID}", res["warnings"])
        self.assertEqual(res["claims"]["items"][0]["status"], "overdue")

    def test_overdue_is_a_reason_from_stage_1_that_counts_against_the_founder(self):  # claim_overdue_stage1_only_warns
        state = state0(open_claims=[claim()], claim_book=book({CID: row(heads=2, opened="2026-11-10T12:00:00Z")}))
        res = judge(state, table=STAGE1)
        self.assertEqual(res["verdict"], "rejected")
        self.assertEqual([(r["kind"], r["ref"], r.get("detail")) for r in res["reasons"]],
                         [("claim_overdue", f"claim:{CID}", "accepted_heads=2 days=4")])
        self.assertEqual(res["learning"]["repeated"], [])
        # claim_overdue_not_the_founders
        self.assertEqual(res["state"]["reject_streaks"], {f"claim_overdue:claim:{CID}": 1})
        self.assertNotIn(f"claim_overdue:{CID}", res["warnings"])

    def test_the_line_is_the_exits_window_reached_not_passed(self):  # claim_threshold_off_by_one claim_threshold_hardcoded
        for heads, window, overdue in ((1, 2, False), (2, 2, True), (4, 5, False), (5, 5, True)):
            state = state0(open_claims=[claim()], claim_book=book({CID: row(heads=heads)}))
            with self.subTest(heads=heads, window=window):
                res = judge(state, min_attempts=window)
                self.assertEqual(f"claim_overdue:{CID}" in res["warnings"], overdue)
                self.assertEqual(res["claims"]["window"], window)

    def test_an_answered_claim_is_not_overdue_a_refused_or_challenged_answer_is(self):  # claim_answer_ignored
        state = state0(open_claims=[claim()], claim_book=book({CID: row(heads=3)}))
        res = judge(state, table=STAGE1, meta_claims=answers())
        self.assertEqual((res["verdict"], res["claims"]["items"][0]["status"]), ("frozen", "answered"))
        self.assertIn("claims_answered:1", res["warnings"])
        # claim_refused_answer_kept
        refused = judge(state, table=STAGE1, meta_claims=dict(answers(), refused=["a" * 64]))
        self.assertEqual(refused["verdict"], "rejected")
        self.assertEqual(refused["claims"]["items"][0]["answer"]["status"], "refused")
        spent = state0(open_claims=[claim()], claim_book=book({CID: row(heads=3, challenged=["a" * 64])}))
        again = judge(spent, table=STAGE1, meta_claims=answers())  # claim_challenged_answer_counts
        self.assertEqual((again["verdict"], again["claims"]["items"][0]["answer"]["status"]),
                         ("rejected", "challenged"))
        new_bytes = judge(spent, table=STAGE1, meta_claims=answers(sha="b" * 64))
        self.assertEqual(new_bytes["verdict"], "frozen")

    def test_an_invalid_answer_warns_and_answers_nothing(self):  # claim_invalid_answer_counts
        state = state0(open_claims=[claim()], claim_book=book({CID: row(heads=3)}))
        res = judge(state, table=STAGE1, meta_claims=answers(problem="fix_cites_no_change"))
        self.assertEqual(res["verdict"], "rejected")
        self.assertIn(f"claim_answer_invalid:{CID}", res["warnings"])
        self.assertNotIn("claims_answered:1", res["warnings"])

    def test_the_rival_sending_an_answered_claim_again_challenges_the_answer(self):  # claim_window_ignores_resend
        state = state0(open_claims=[claim()], claim_book=book({CID: row(heads=3)}))
        resend = refuted("again")
        resend["attempts"][0]["open_claim"] = CID
        del resend["attempts"][0]["reproducer"]
        res = judge(state, kind="spec", table=STAGE1, meta_claims=answers(), rival=resend)
        self.assertEqual(res["verdict"], "rejected")
        self.assertIn("claim_overdue", [r["kind"] for r in res["reasons"]])
        self.assertEqual(res["state"]["claim_book"]["claims"][CID]["challenged"], ["a" * 64])
        self.assertEqual((res["claims"]["challenged"], res["state"]["claim_book"]["claims"][CID]["accepted_heads"]),
                         (1, 3))  # claim_challenge_resets_age: the age never stopped and is not reset


class Closures(unittest.TestCase):
    REP = {"cmd": "check", "expect_exit": 1, "correct_exit": 0}

    def observed_run(self, state, kind="code", shown=False, contradicted=True, timed_out=False, pre=()):
        result = {"key": CID, "source": "claim", "reproduced": False, "shown": shown, "contradicted": contradicted,
                  "timed_out": timed_out, "runner_fault": False, "tautological": None, "exit": 0}
        return decide(meta_(kind, state, claims={}, state_repro=[CID], pre_reasons=list(pre)), green_run(),
                      not_refuted(), [], dict(CODE_JOBS, yeniden="success"), 2, 3, state_repro=[result], now=NOW)

    def test_observed_closes_on_an_accepted_head_only(self):  # claim_observed_on_rejected_head
        state = state0(open_claims=[claim(reproducer=self.REP)], claim_book=book({CID: row(heads=4)}))
        res = self.observed_run(state)
        self.assertEqual((res["verdict"], res["state"]["open_claims"]), ("accepted", []))
        self.assertEqual(res["claims"]["closed"], {"observed": 1, "operator": 0, "proven": 0, "total": 1})
        self.assertEqual(res["claims"]["closed_now"], [{"id": CID, "how": "observed"}])
        self.assertEqual(res["state"]["claim_book"]["recent"],
                         [{"id": CID, "how": "observed", "accepted_heads": 5, "days": 4}])
        self.assertNotIn(f"claim_overdue:{CID}", res["warnings"])  # claim_overdue_before_closure
        rejected = self.observed_run(state, pre=["seed_modified"])
        self.assertEqual([c["id"] for c in rejected["state"]["open_claims"]], [CID])

    def test_observed_needs_the_correct_side_not_the_symptom_and_a_finished_run(self):  # claim_observed_when_symptom_shows
        state = state0(open_claims=[claim(reproducer=self.REP)], claim_book=book({CID: row(heads=0)}))
        for kw in ({"shown": True}, {"contradicted": False}, {"timed_out": True}):  # claim_observed_with_timeout
            with self.subTest(**kw):
                res = self.observed_run(state, **kw)
                self.assertEqual([c["id"] for c in res["state"]["open_claims"]], [CID])
                self.assertEqual(res["claims"]["closed"]["total"], 0)

    def test_the_operator_closes_by_id(self):  # waived_claims_ignored
        state = state0(open_claims=[claim(), claim(OTHER)], claim_book=book({CID: row(heads=9), OTHER: row(heads=9)}))
        res = judge(state, meta_claims={"waived": [CID]})
        self.assertEqual([c["id"] for c in res["state"]["open_claims"]], [OTHER])
        self.assertEqual(res["claims"]["closed_now"], [{"id": CID, "how": "operator"}])
        self.assertNotIn(f"claim_overdue:{CID}", res["warnings"])
        self.assertIn(f"claim_overdue:{OTHER}", res["warnings"])

    def test_a_proven_claim_is_counted_proven(self):  # claim_proven_uncounted
        rep = {"cmd": "check c", "expect_exit": 1}
        state = state0(open_claims=[claim(reproducer=rep)], claim_book=book({CID: row(heads=1)}))
        rival = refuted("c")
        rival["attempts"][0]["open_claim"] = CID
        res = decide(meta_("code", state, claims={}), green_run(), rival,
                     [{"attempt_index": 0, "reproduced": True, "contradicted": False}],
                     dict(CODE_JOBS, yeniden="success"), 2, 3, now=NOW)
        self.assertEqual(res["claims"]["closed_now"], [{"id": CID, "how": "proven"}])
        self.assertEqual(res["state"]["open_claims"], [])

    def test_evicted_claims_are_counted_apart_and_never_closed(self):  # claim_evicted_counted_closed
        many = [claim(f"{i:012x}") for i in range(10)]
        state = state0(open_claims=many, claim_book=book({c["id"]: row() for c in many}))
        res = decide(meta_("code", state, claims={}), green_run(), refuted("new one"),
                     [{"attempt_index": 0, "reproduced": False}], dict(CODE_JOBS, yeniden="success"), 2, 3, now=NOW)
        self.assertEqual((res["claims"]["evicted"], res["claims"]["closed"]["total"]), (1, 0))
        self.assertNotIn(f"{0:012x}", res["state"]["claim_book"]["claims"])

    def test_a_closed_claim_coming_back_counts_reopened(self):  # claim_reopened_uncounted
        cid = hashlib.sha256(b"c").hexdigest()[:12]
        recent = [{"id": cid, "how": "observed", "accepted_heads": 3, "days": 1}]
        state = state0(claim_book=book({}, recent=recent, closed={"observed": 1, "operator": 0, "proven": 0}))
        res = decide(meta_("code", state, claims={}), green_run(), refuted("c"),
                     [{"attempt_index": 0, "reproduced": False}], dict(CODE_JOBS, yeniden="success"), 2, 3, now=NOW)
        self.assertEqual(res["claims"]["reopened"], 1)

    def test_time_to_close_is_the_median_of_the_recent_closures(self):  # claim_median_is_mean
        recent = [{"id": f"{i:012x}", "how": "operator", "accepted_heads": h, "days": d}
                  for i, (h, d) in enumerate(((1, 1), (2, 1), (30, 9)))]
        res = judge(state0(claim_book=book({}, recent=recent)))
        self.assertEqual(res["claims"]["time_to_close"], {"n": 3, "median_accepted_heads": 2, "median_days": 1})

    def test_the_recent_closures_are_bounded(self):  # claim_recent_unbounded
        recent = [{"id": f"{i:012x}", "how": "operator", "accepted_heads": 1, "days": 1} for i in range(50)]
        state = state0(open_claims=[claim()], claim_book=book({CID: row()}, recent=recent))
        res = judge(state, meta_claims={"waived": [CID]})
        self.assertEqual(len(res["state"]["claim_book"]["recent"]), 50)
        self.assertEqual(res["state"]["claim_book"]["recent"][-1]["id"], CID)
        st.validate(res["state"])

    def test_an_empty_book_is_not_written(self):  # claim_book_always_written
        res = judge(state0())
        self.assertNotIn("claim_book", res["state"])
        self.assertEqual(res["claims"]["open"], 0)


class PullInputs(unittest.TestCase):
    def test_pull_reads_answers_held_to_the_claims_and_the_first_heads_time(self):  # claim_inputs_not_read
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "brain"
            first = make_repo(repo, {"referee/x.py": "a\n"})
            head = commit(repo, {"referee/x.py": "a\nb\n", "reports/claim-0123456789ab.json": answer_doc().decode()},
                          "fix")
            prev = state0(open_claims=[claim(first=first)])
            got = cli.claim_inputs(repo, head, prev, cli.gitio.archive(repo, head))
            self.assertEqual([(a["ref"], a["answer"], a["problem"]) for a in got["answers"]], [(CID, "fix", None)])
            seconds = int(sh(repo, "git", "show", "-s", "--format=%ct", first))
            self.assertEqual(got["dates"], {CID: claims.datetime.datetime.fromtimestamp(
                seconds, claims.datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")})
            booked = dict(prev, claim_book=book({CID: row()}))
            self.assertEqual(cli.claim_inputs(repo, head, booked, cli.gitio.archive(repo, head))["dates"], {})
            stale = cli.claim_inputs(repo, first, prev, cli.gitio.archive(repo, head))  # nothing changed since first
            self.assertEqual(stale["answers"][0]["problem"], "fix_cites_no_change")

    def test_the_operators_lists_are_read_strictly(self):  # claim_controls_unchecked
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "control.json").write_text(json.dumps({}), encoding="utf-8")
            self.assertEqual(config.load_claim_controls(root), ([], []))
            (root / "control.json").write_text(json.dumps({"waived_claims": [CID, CID], "refused_answers": ["a" * 64]}),
                                               encoding="utf-8")
            self.assertEqual(config.load_claim_controls(root), ([CID], ["a" * 64]))
            for bad in ({"waived_claims": ["xyz"]}, {"waived_claims": CID}, {"refused_answers": ["A" * 64]}):
                (root / "control.json").write_text(json.dumps(bad), encoding="utf-8")
                with self.subTest(bad=bad), self.assertRaises(ConfigError):
                    config.load_claim_controls(root)


class StageZeroSetAside(unittest.TestCase):
    def test_the_golden_test_sets_aside_only_these_names(self):  # stage0_set_aside_widened stage0_result_widened
        """`test_stage0_unchanged` compares Stage 0's signed documents with the base's recordings and sets aside, by
        name, only what E585, E594 and E596 add (the verifier of epoch L: a wider list let Stage 0 drift unseen)."""
        import test_stage0_unchanged as golden
        self.assertEqual(golden.SET_ASIDE_META, ("self_map", "claims", "proposals"))
        self.assertEqual(golden.SET_ASIDE_RESULT, ("claims", "proposals"))
        self.assertEqual(golden.SET_ASIDE_WARNINGS, ("self_map_", "claim_", "claims_", "proposal_"))
        self.assertEqual(golden.CLAIM_BOOK, claims.BOOK)


class PageAndPointers(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[3]

    def page(self, prefix: str) -> str:
        return next((self.ROOT / "spec" / "tohum").glob(f"{prefix}-*.md")).read_text(encoding="utf-8")

    def test_29x_names_each_finding_and_the_closures(self):  # claims_page_drops_a_name
        text = self.page("29x")
        for name in claims.NAMES + claims.HOWS + ("waived_claims", "refused_answers", "claim_book", "accepted_heads",
                                                  "rival_min_attempts", "reports/claim-<id>.json"):
            with self.subTest(name=name):
                self.assertIn(f"`{name}", text)

    def test_the_duty_is_on_00a_and_the_record_on_29e(self):  # claims_pointer_00a_dropped claims_pointer_29e_dropped
        self.assertIn("`29x`", self.page("00a"))
        self.assertIn("`29x`", self.page("29e"))
        self.assertIn("`29x`", self.page("26c"))



class PullWiring(Flow):
    """`pull` hands `decide` the answers, the operator's lists and the checked proposals, on a records-only push too."""

    def test_pull_reads_the_answers_the_operators_lists_and_the_proposals(self):  # claim_inputs_not_read
        first = sh(self.brain, "git", "rev-parse", "HEAD")
        self.state["open_claims"] = [claim(first=first, paths=("spec/tohum/00-cekirdek.md",))]
        (self.referee / "control.json").write_text(json.dumps({
            "kill_switch": False, "budget_state": "ok", "waived_claims": [OTHER], "refused_answers": ["c" * 64]}))
        answer = answer_doc(kind="refute", path="spec/tohum/00-cekirdek.md", start=1, end=1).decode()
        proposal = json.dumps({"id": "p1", "kind": "seed_proposal", "ref": "x", "state": "open",
                               "base": {"spec_tohum_sha256": "2" * 64, "bootstrap_sha256": "3" * 64},
                               "patch_sha256": hashlib.sha256(b"diff --git a/x b/x\n").hexdigest(),
                               "evidence": {"tests": ["test_x.T.test_x"]}})
        commit(self.brain, {"reports/claim-0123456789ab.json": answer, "reports/p1.json": proposal,
                            "reports/p1.patch": "diff --git a/x b/x\n"}, "records")
        meta = self.pull()
        self.assertEqual(meta["kind"], "none")
        self.assertEqual([(a["ref"], a["answer"], a["problem"]) for a in meta["claims"]["answers"]],
                         [(CID, "refute", None)])
        # claim_controls_not_passed
        self.assertEqual((meta["claims"]["waived"], meta["claims"]["refused"]), ([OTHER], ["c" * 64]))
        self.assertEqual(sorted(meta["claims"]["dates"]), [CID])
        self.assertEqual([(p["id"], p["status"], p["reasons"]) for p in meta["proposals"]],  # proposals_not_read
                         [("p1", "rejected", ["proposal_base_unknown"])])
        result = self.finish(meta)
        self.assertEqual(result["verdict"], "noop")
        self.assertEqual(result["claims"]["items"][0]["status"], "answered")


def load_tests(loader, tests, pattern):
    """This module's own tests: `PullWiring` is a `test_flow.Flow`, whose tests run in their own module."""
    suite = unittest.TestSuite()
    cases = [v for v in globals().values() if isinstance(v, type) and issubclass(v, unittest.TestCase)
             and v.__module__ == __name__]  # every class of this module, none forgotten in a list
    for case in cases:
        names = [n for n in vars(case) if n.startswith("test")]
        suite.addTests(case(n) for n in names)
    return suite


if __name__ == "__main__":
    unittest.main()
