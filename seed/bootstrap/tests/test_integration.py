"""E516, the wiring of the private exam, the K6 fence and the watchers (plan A/F/G, WP-INT): one switch, the last seed
epoch's `exam_sha256`. Before it the referee judges and signs exactly as it did (`test_stage0_unchanged` holds every
field); from it on the result is /2 with `exam`, `k6` and `istismar`, and each new reason is judged as the plan says.
The package modules other work packages deliver (answers, fence, k6, target_run, watchers) are stubs here: what is
tested is what this referee does with what they answer, never what they compute."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

from snowball_bootstrap import classify as classify_module, cli, config, decide as decide_module
from snowball_bootstrap.classify import classify
from snowball_bootstrap.config import ConfigError, load_summary
from snowball_bootstrap.decide import decide

from helpers import workflow_job
from test_decision import A, B, green_run, meta_, state0

BOOT = Path(__file__).resolve().parents[1]
ROOT = BOOT.parents[1]
WORKFLOW = (BOOT / "workflow" / "bootstrap.yml").read_text(encoding="utf-8")
PIN = "e" * 64
ROW = {"commit": "c" * 40, "spec_tohum_sha256": "d" * 64, "seed_sha256": None, "bootstrap_sha256": "f" * 64}
COPY = {"id": "copy", "repo": "owner/copy", "kind": "copy", "base_sha": "1" * 40, "identifiers": ["X"],
        "excluded_paths": [], "unit_candidates": ["units/a"], "safety_paths": ["units/pump"]}
JOBS = {"getir": "success", "kos": "success", "cagir": "success", "yeniden": "skipped", "gozcu": "success"}


def summary_doc(*rows, targets=(COPY,)):
    return {"seed_commit": "a" * 40, "seed_tree_sha256": "b" * 64, "seed_epochs": list(rows), "targets": list(targets)}


def load(doc):
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "setup").mkdir()
        (Path(tmp) / "setup" / "summary.json").write_text(json.dumps(doc))
        return load_summary(Path(tmp))


def read_run(**exam):
    run = green_run()
    run["vectors"] = [{"id": "v1", "ok": True}, {"id": "v2", "ok": True}]
    run["exam"] = {"status": "read", "exam_sha256": PIN, **exam}
    return run


def finding(watcher, ref="t1", reproducer=True, declared=False, subject=None):
    out = {"watcher": watcher, "ref": ref, "evidence_sha256": "a" * 64,
           "reproducer": {"cmd": "python3 -m x", "expect_exit": 1} if reproducer else None, "declared": declared}
    if subject is not None:
        out["subject"] = subject
    return out


READ = object()  # `pinned`'s default run: green, with the pinned exam read


def pinned(meta=None, run=READ, jobs=None, findings=(), unverifiable=0, fence=None, gozcu=True):
    meta = meta or meta_("code", state0(), run_rival=False)
    doc = {"head": meta["head"], "findings": list(findings), "unverifiable": unverifiable} if gozcu else None
    return decide(meta, read_run() if run is READ else run, None, None, dict(JOBS, **(jobs or {})), 2, 3,
                  exam_pin=PIN, gozcu=doc, fence=fence)


class EpochPinTest(unittest.TestCase):
    """E516: `exam_sha256` in `EPOCH_KEYS`; the rows before it read as null, and the pin, once set, stays."""

    def test_rows_without_the_key_read_as_unpinned_and_a_pinned_row_sets_the_pin(self):  # exam_pin_format_unchecked
        self.assertEqual(config.EPOCH_KEYS - config.EPOCH_LEGACY_KEYS, {"exam_sha256"})
        self.assertIsNone(load(summary_doc(ROW)).exam_pin)
        self.assertIsNone(load(summary_doc(dict(ROW, exam_sha256=None))).exam_pin)
        self.assertIsNone(load({"seed_commit": "a" * 40, "seed_tree_sha256": "b" * 64}).exam_pin)
        self.assertEqual(load(summary_doc(ROW, dict(ROW, exam_sha256=PIN))).exam_pin, PIN)
        for bad in ("E" * 64, "e" * 63, 7, ""):
            with self.assertRaises(ConfigError, msg=repr(bad)):
                load(summary_doc(dict(ROW, exam_sha256=bad)))

    def test_a_later_epoch_cannot_drop_the_pin(self):  # exam_pin_may_be_dropped
        with self.assertRaises(ConfigError) as caught:
            load(summary_doc(dict(ROW, exam_sha256=PIN), ROW))
        self.assertIn("drops the exam pin", str(caught.exception))
        with self.assertRaises(ConfigError):
            load(summary_doc(dict(ROW, exam_sha256=PIN), dict(ROW, exam_sha256=None)))
        self.assertEqual(load(summary_doc(dict(ROW, exam_sha256="1" * 64), dict(ROW, exam_sha256=PIN))).exam_pin, PIN)

    def test_under_a_pin_every_copy_target_names_the_owners_safety_paths(self):  # pinned_copy_without_safety_paths
        bare = {k: v for k, v in COPY.items() if k != "safety_paths"}
        self.assertEqual(len(load(summary_doc(ROW, targets=(bare,))).targets), 1)  # no pin: optional, as E421 had it
        for target in (bare, dict(COPY, safety_paths=[])):
            with self.assertRaises(ConfigError) as caught:
                load(summary_doc(dict(ROW, exam_sha256=PIN), targets=(target,)))
            self.assertIn("without safety_paths", str(caught.exception))
        toy = dict(bare, id="toy", kind="toy")
        loaded = load(summary_doc(dict(ROW, exam_sha256=PIN), targets=(COPY, toy)))
        self.assertEqual(loaded.targets[0].safety_paths, ("units/pump",))
        self.assertIsNone(loaded.targets[1].safety_paths)

    def test_the_operator_cannot_call_an_unread_exam_or_istismar_an_exam_fault(self):  # unwaivable_exam_fault_taken
        self.assertEqual(config.UNWAIVABLE_REASONS, ("answers_unavailable", "istismar"))
        with tempfile.TemporaryDirectory() as tmp:
            for signature, refused in (("istismar:G1:t1", True), ("answers_unavailable:missing", True),
                                       ("test_failed:T13", False)):
                (Path(tmp) / "control.json").write_text(json.dumps(
                    {"kill_switch": False, "budget_state": "ok",
                     "exam_faults": [{"head": "a" * 40, "signature": signature}]}))
                if refused:
                    with self.assertRaises(ConfigError, msg=signature):
                        config.load_exam_faults(Path(tmp))
                else:
                    self.assertEqual(config.load_exam_faults(Path(tmp))[0].signature, signature)

    def test_the_target_image_is_pinned_by_digest(self):
        base = {"brain_repo": "o/b", "brain_branch": "main", "image": "img@sha256:" + "a" * 64,
                "rival": {"model": "claude-sonnet-5-5", "effort": "high", "max_turns": 3, "per_run_cap_usd_micros": 9},
                "limits": {"test_timeout_s": 1, "reproducer_timeout_s": 1, "max_prompt_chars": 1, "max_tree_bytes": 1}}
        with tempfile.TemporaryDirectory() as tmp:
            for doc, want in ((base, None), (dict(base, target_image="t@sha256:" + "b" * 64), "t@sha256:" + "b" * 64),
                              (dict(base, target_image="node:22"), ConfigError)):
                (Path(tmp) / "bootstrap.json").write_text(json.dumps(doc))
                if want is ConfigError:
                    with self.assertRaises(ConfigError):
                        config.load_bootstrap(Path(tmp))
                else:
                    self.assertEqual(config.load_bootstrap(Path(tmp)).target_image, want)


class ExamTamperTest(unittest.TestCase):
    """E516, G4a: the exam's own slots in the tree that becomes the referee, rejected outright under a pin only."""

    def test_the_exam_slots_are_exam_tamper_only_under_a_pin(self):  # exam_tamper_without_pin exam_tamper_case_sensitive exam_tamper_unread
        changed = ["referee/vectors/vectors.json", "referee/Setup/x", "referee/gate/x.py", "referee/vectorsX/y"]
        self.assertEqual(classify(changed), ("code", []))
        kind, reasons = classify(changed, exam_pinned=True)
        self.assertEqual((kind, reasons), ("rejected", ["exam_tamper:referee/Setup/x",
                                                        "exam_tamper:referee/vectors/vectors.json"]))
        self.assertEqual(set(classify_module.PROTECTED_EXAM),
                         {"referee/" + name for name in ("bootstrap", "bootstrap.json", "control.json", "policy.json",
                                                         "seats", "setup", "vectors")})
        many = [f"referee/seats/{i:02d}" for i in range(30)]
        self.assertEqual(len(classify(many, exam_pinned=True)[1]), classify_module.EXAM_TAMPER_LIMIT)

    def test_exam_tamper_is_named_as_g4_istismar_and_counted(self):  # exam_tamper_not_istismar
        meta = meta_("rejected", state0(), run_tests=False, run_rival=False,
                     pre_reasons=["exam_tamper:referee/vectors/x"])
        res = pinned(meta, run=None)
        self.assertEqual(res["verdict"], "rejected")
        self.assertEqual([e["watcher"] for e in res["istismar"]], ["G4"])
        self.assertEqual(res["istismar"][0]["reproducer"], {"changed_path": "referee/vectors/x"})
        self.assertEqual(res["istismar"][0]["evidence_sha256"], hashlib.sha256(b"referee/vectors/x").hexdigest())


class NoPinTest(unittest.TestCase):
    """E516: with no pin nothing new is read or signed (`test_stage0_unchanged` holds the whole flow field by field)."""

    def test_no_pin_signs_the_result_it_always_signed(self):  # pinned_fields_without_pin
        meta = meta_("code", state0(), run_rival=False)
        doc = {"head": B, "findings": [finding("G1")], "unverifiable": 3}
        fence = {"head": B, "reasons": [{"kind": "safety_path_closed", "ref": "units/pump/a"}]}
        plain = decide(meta, green_run(), None, None, JOBS, 2, 3)
        given = decide(meta, green_run(), None, None, JOBS, 2, 3, gozcu=doc, fence=fence)
        self.assertEqual(given, plain)
        self.assertEqual(plain["schema"], "snowball-bootstrap-result/1")
        self.assertEqual({"exam", "k6", "istismar"} & set(plain), set())
        self.assertEqual(plain["verdict"], "accepted")


class PinnedResultTest(unittest.TestCase):
    """E516: a pinned result is /2 and carries the exam, the K6 status and the istismar entries."""

    def test_a_clean_pinned_push_is_accepted_with_its_three_fields(self):
        meta = meta_("code", state0(), run_rival=False, k6_prev={"status": "exam_built", "exam_sha256": PIN})
        res = pinned(meta)
        self.assertEqual((res["schema"], res["verdict"], res["reasons"]), ("snowball-bootstrap-result/2", "accepted", []))
        self.assertEqual(res["exam"], {"exam_sha256": PIN, "visible": {"n": 2, "pass": 2}})
        self.assertEqual(res["k6"], {"status": "exam_built", "exam_sha256": PIN})
        self.assertEqual(res["istismar"], [])

    def test_the_k6_field_falls_closed(self):  # k6_unknown_status_kept
        run = dict(read_run(), k6={"status": "live", "strength": {"killed": 9}})
        self.assertEqual(pinned(run=run)["k6"], {"status": "live", "strength": {"killed": 9}})
        meta = meta_("code", state0(), run_rival=False, k6_prev={"status": "live"})
        self.assertEqual(pinned(meta, run=dict(read_run(), k6={"status": "maybe"}))["k6"], {"status": "live"})
        for fresh, carried in (({"status": "LIVE"}, None), (None, {"status": True}), (None, None), ("live", "live")):
            meta = meta_("code", state0(), run_rival=False, k6_prev=carried)
            self.assertEqual(pinned(meta, run=dict(read_run(), k6=fresh))["k6"], {"status": "not_live"}, (fresh, carried))

    def test_an_unread_exam_is_retried_and_never_the_founders(self):  # exam_pin_not_compared_in_yaz answers_unavailable_judged answers_unavailable_counted
        self.assertIn("answers_unavailable", decide_module.NOT_THE_FOUNDERS)
        for run in ({"exam": {"status": "unavailable", "why": "pin_mismatch", "exam_sha256": "1" * 64},
                     "green": False, "tests": [], "vectors": [], "controls": [], "module_less": [], "licenses": []},
                    read_run(exam_sha256="1" * 64), dict(green_run(), vectors=[{"id": "v", "ok": False}])):
            res = pinned(meta_("code", state0(reject_streaks={"x:y": 1}), run_rival=False), run=run)
            self.assertEqual([r["kind"] for r in res["reasons"]], ["answers_unavailable"])
            self.assertEqual(res["verdict"], "rejected")
            self.assertIsNone(res["state"]["last_evaluated_sha"])  # retried, as an outage is
            self.assertEqual(res["state"]["reject_streaks"], {"x:y": 1})
            self.assertEqual((res["state"]["outage_sha"], res["state"]["outage_count"]), (B, 1))
            self.assertEqual(res["exam"]["visible"], None)
        res = pinned(run=read_run(exam_sha256="1" * 64))
        self.assertFalse(decide_module.counts_against_founder(res["reasons"][0]))
        state = state0(reject_streaks={"x:y": 1})
        decide_module._learning(state, res["reasons"], 3)  # even judged, it would leave every streak as it was
        self.assertEqual(state["reject_streaks"], {"x:y": 1})


class IstismarTest(unittest.TestCase):
    """E516, plan D9: istismar is a watcher's mechanical finding with its reproducer on an undeclared change."""

    def test_istismar_needs_a_reproducer_and_an_undeclared_change(self):  # istismar_from_declared istismar_without_reproducer
        res = pinned(findings=[finding("G1"), finding("G2", declared=True), finding("G3", reproducer=False)])
        self.assertEqual([(r["kind"], r["ref"]) for r in res["reasons"]], [("istismar", "G1:t1")])
        self.assertEqual(res["istismar"], [{k: finding("G1")[k] for k in ("watcher", "ref", "evidence_sha256",
                                                                          "reproducer", "declared")}])
        self.assertEqual(res["verdict"], "rejected")
        self.assertIn("gozcu_declared:G2", res["warnings"])
        self.assertIn("gozcu_suphe:G3", res["warnings"])

    def test_istismar_counts_against_the_founder_and_keeps_its_streak(self):  # istismar_not_counted
        state = state0(reject_streaks={"istismar:G1:t1": 1})
        res = pinned(meta_("code", state, run_rival=False), findings=[finding("G1")])
        self.assertTrue(decide_module.counts_against_founder(res["reasons"][0]))
        self.assertEqual(res["state"]["reject_streaks"], {"istismar:G1:t1": 2})
        self.assertEqual(res["learning"]["repeated"], ["istismar:G1:t1"])
        self.assertEqual(res["state"]["last_evaluated_sha"], B)

    def test_a_drop_on_held_cases_alone_follows_the_one_switch(self):  # held_drop_rule_default_judge g5_ignores_branch_evidence
        """Owner's open decision (b): the default is the owner's literal rule, "düşüş = ezber"."""
        self.assertEqual(decide_module.HELD_DROP_RULE, decide_module.HELD_DROP_OWNER)
        alone = [finding("G5", ref="held", subject="f")]
        res = pinned(findings=alone)
        self.assertEqual([(r["kind"], r["ref"]) for r in res["reasons"]], [("istismar", "G5:held")])
        with mock.patch.object(decide_module, "HELD_DROP_RULE", decide_module.HELD_DROP_JUDGE):  # the other side
            res = pinned(findings=alone)
            self.assertEqual((res["istismar"], [(r["kind"], r["ref"]) for r in res["reasons"]]),
                             ([], [("held_drop", "G5:held")]))
            self.assertIn("ezber_suphe:G5", res["warnings"])
            self.assertTrue(decide_module.counts_against_founder(res["reasons"][0]))  # a normal rejection
            both = pinned(findings=alone + [finding("G2", ref="branch", subject="f")])
            self.assertEqual([e["watcher"] for e in both["istismar"]], ["G5", "G2"])
            other = pinned(findings=alone + [finding("G2", ref="branch", subject="g")])
            self.assertEqual([e["watcher"] for e in other["istismar"]], ["G2"])
            self.assertIn(("held_drop", "G5:held"), [(r["kind"], r["ref"]) for r in other["reasons"]])
        res = pinned(findings=alone)  # the switch is read at each call: the owner's rule again
        self.assertEqual([r["kind"] for r in res["reasons"]], ["istismar"])

    def test_unverifiable_claims_are_a_warning_never_istismar(self):
        res = pinned(unverifiable=4)
        self.assertEqual((res["verdict"], res["istismar"]), ("accepted", []))
        self.assertIn("unverifiable:4", res["warnings"])

    def test_the_watchers_must_answer_for_this_head(self):  # gozcu_other_head_taken gozcu_not_expected
        meta = meta_("code", state0(), run_rival=False)
        other = decide(meta, read_run(), None, None, JOBS, 2, 3, exam_pin=PIN,
                       gozcu={"head": A, "findings": [], "unverifiable": 0})
        self.assertEqual([(r["kind"], r["ref"]) for r in other["reasons"]], [("infra", "gozcu:malformed")])
        self.assertIsNone(other["state"]["last_evaluated_sha"])
        for bad in ([{"watcher": "G9", "ref": "x", "evidence_sha256": "a" * 64, "reproducer": None,
                      "declared": False}], [dict(finding("G1"), declared="no")], "x"):
            res = decide(meta, read_run(), None, None, JOBS, 2, 3, exam_pin=PIN, gozcu={"head": B, "findings": bad})
            self.assertEqual([r["ref"] for r in res["reasons"]], ["gozcu:malformed"], repr(bad))
        failed = pinned(jobs={"gozcu": "failure"}, gozcu=False)
        self.assertEqual([(r["kind"], r["ref"]) for r in failed["reasons"]], [("infra", "gozcu:failure")])
        spec = pinned(meta_("spec", state0(), run_rival=False), run=None, jobs={"gozcu": "skipped"}, gozcu=False)
        self.assertEqual(spec["verdict"], "frozen")  # a spec push has no `gozcu` run to wait for


class FenceTest(unittest.TestCase):
    """E516, plan D6: the fence's two reasons, from the referee's `fence` on a copy diff, are the Founder's."""

    def test_the_fence_reasons_are_the_founders(self):  # fence_doc_unread
        fence = {"head": B, "reasons": [{"kind": "safety_path_closed", "ref": "units/pump/a.rs"},
                                        {"kind": "safety_list_narrowed", "ref": "copy"}, {"kind": "other", "ref": "x"}]}
        res = pinned(fence=fence)
        self.assertEqual([(r["kind"], r["ref"]) for r in res["reasons"]],
                         [("safety_path_closed", "units/pump/a.rs"), ("safety_list_narrowed", "copy")])
        self.assertTrue(all(decide_module.counts_against_founder(r) for r in res["reasons"]))
        self.assertEqual(pinned(fence=dict(fence, head=A))["verdict"], "accepted")  # another head's fence

    def run_fence(self, k6, derived, superset=True):
        stub = types.ModuleType("snowball_bootstrap.fence")
        stub.touches_safety = lambda changed, paths: [p for p in changed if p.startswith(tuple(paths))]
        stub.superset_ok = lambda got, owner: superset
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "setup").mkdir()
            (root / "setup" / "summary.json").write_text(json.dumps(summary_doc(dict(ROW, exam_sha256=PIN))))
            (root / "prev.json").write_text(json.dumps({"k6": k6}))
            (root / "derived.json").write_text(json.dumps({"security_paths": ["units/pump"]}))
            argv = ["fence", "--root", tmp, "--copy", tmp, "--base", "1" * 40, "--head", "2" * 40, "--target", "copy",
                    "--prev-result", str(root / "prev.json"), "--out", str(root / "out")]
            with mock.patch.dict(sys.modules, {"snowball_bootstrap.fence": stub}), \
                    mock.patch.object(cli.gitio, "changed_paths", return_value=["units/pump/a.rs", "units/b.py"]):
                self.assertEqual(cli.main(argv + (["--derived", str(root / "derived.json")] if derived else [])), 0)
            return json.loads((root / "out" / "fence.json").read_text())

    def test_the_fence_command_reads_the_signed_k6_status_and_the_owners_list(self):  # fence_open_when_live_ignored
        closed = self.run_fence({"status": "exam_strong"}, derived=False)
        self.assertEqual(closed, {"head": "2" * 40, "k6_status": "exam_strong",
                                  "reasons": [{"kind": "safety_path_closed", "ref": "units/pump/a.rs"}]})
        self.assertEqual(self.run_fence(None, derived=False)["k6_status"], "not_live")
        self.assertEqual(self.run_fence({"status": "live"}, derived=False)["reasons"], [])
        self.assertEqual(self.run_fence({"status": "live"}, derived=True, superset=False)["reasons"],
                         [{"kind": "safety_list_narrowed", "ref": "copy"}])


class PinnedCommandsTest(unittest.TestCase):
    """E516: the commands read the pin from the snapshot, and a pinned run without a package module stops."""

    def test_a_missing_package_module_stops_a_pinned_run(self):  # pinned_module_missing_is_silent
        with self.assertRaises(ConfigError) as caught:
            cli.pinned_module("no_such_module_e516", "E516")
        self.assertIn("snowball_bootstrap/no_such_module_e516.py (E516)", str(caught.exception))
        self.assertIs(cli.pinned_module("canon", "E516"), sys.modules["snowball_bootstrap.canon"])

    def store(self, tmp, manifest=b'{"files": {}}'):
        where = Path(tmp) / "exam"
        (where / ".git").mkdir(parents=True)
        (where / ".git" / "config").write_bytes(b"x")
        (where / "manifest.json").write_bytes(manifest)
        (where / "a").mkdir()
        (where / "a" / "b.json").write_bytes(b"{}")
        return where, hashlib.sha256(manifest).hexdigest()

    def test_the_exam_store_is_read_only_at_the_pin(self):  # exam_store_pin_unchecked
        stub = types.ModuleType("snowball_bootstrap.answers")
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(sys.modules, {"snowball_bootstrap.answers": stub}):
            where, pin = self.store(tmp)
            self.assertEqual(cli.exam_store(None, pin), ({}, None, "missing"))
            self.assertEqual(cli.exam_store(Path(tmp) / "none", pin)[2], "missing")
            self.assertEqual(cli.exam_store(where, "0" * 64)[1:], (pin, "pin_mismatch"))
            (where / "manifest.json").rename(where / "m")
            self.assertEqual(cli.exam_store(where, pin)[1:], (None, "no_manifest"))
            (where / "m").rename(where / "manifest.json")
            seen = []
            stub.verify = lambda manifest, files, got: seen.append((manifest, sorted(files), got))
            files, measured, why = cli.exam_store(where, pin)
            self.assertEqual((measured, why), (pin, None))
            self.assertEqual(seen, [({"files": {}}, ["a/b.json", "manifest.json"], pin)])  # never git's own files
            stub.verify = lambda manifest, files, got: False
            self.assertEqual(cli.exam_store(where, pin)[2], "verify_failed")
            stub.verify = lambda manifest, files, got: (_ for _ in ()).throw(ValueError("tampered"))
            self.assertEqual(cli.exam_store(where, pin)[2], "verify:ValueError")

    def test_decide_reads_the_pin_from_the_snapshot_and_compares_it_again(self):  # exam_pin_not_compared_in_yaz
        with tempfile.TemporaryDirectory() as tmp:
            root, pulled = Path(tmp) / "snap", Path(tmp) / "pulled"
            (root / "setup").mkdir(parents=True)
            pulled.mkdir()
            (root / "policy.json").write_text(json.dumps({"constitutional": {
                "monthly_cap_usd": 300, "stage_params": {"rival_min_attempts": 2, "repeat_reject_limit": 3},
                "stage_budgets": {"asama_0": {"rival_usd": 30}}, "license_allowlist": ["MIT"],
                "license_exceptions": {}}}))
            (pulled / "meta.json").write_text(json.dumps(meta_("code", state0(), run_rival=False)))
            for name, doc in (("run", read_run()), ("gozcu", {"head": B, "findings": [], "unverifiable": 0})):
                (Path(tmp) / name).mkdir()
                (Path(tmp) / name / f"{name}.json").write_text(json.dumps(doc))
            argv = ["decide", "--root", str(root), "--pulled", str(pulled), "--run", str(Path(tmp) / "run"),
                    "--gozcu", str(Path(tmp) / "gozcu"), "--out", str(Path(tmp) / "out")]
            argv += [f"--job={k}={v}" for k, v in JOBS.items()]
            for row, schema, kinds in ((dict(ROW, exam_sha256=PIN), "/2", []),
                                       (dict(ROW, exam_sha256="1" * 64), "/2", ["answers_unavailable"]),
                                       (ROW, "/1", [])):
                (root / "setup" / "summary.json").write_text(json.dumps(summary_doc(row)))
                self.assertEqual(cli.main(argv), 0)
                res = json.loads((Path(tmp) / "out" / "result.json").read_text())
                self.assertEqual((res["schema"][-2:], [r["kind"] for r in res["reasons"]]), (schema, kinds))

    def test_pull_carries_the_signed_k6_field_only_under_a_pin(self):  # k6_prev_without_pin
        with tempfile.TemporaryDirectory() as tmp:
            prev = Path(tmp) / "result.json"
            prev.write_text(json.dumps({"k6": {"status": "live"}}))
            meta = {}
            cli._pin_meta(meta, load(summary_doc(ROW)), str(prev))
            self.assertEqual(meta, {})
            cli._pin_meta(meta, load(summary_doc(dict(ROW, exam_sha256=PIN))), str(prev))
            self.assertEqual(meta, {"k6_prev": {"status": "live"}, "exam_pin": PIN})
            cli._pin_meta(meta, load(summary_doc(dict(ROW, exam_sha256=PIN))), str(Path(tmp) / "none.json"))
            self.assertEqual(meta, {"k6_prev": None, "exam_pin": PIN})

    def test_join_parts_judges_on_the_answers_only_when_the_store_is_the_pinned_one(self):
        """The parts' records are joined on the groups `answers.join` gave back; an unread store judges nothing."""
        stub = types.ModuleType("snowball_bootstrap.answers")
        stub.verify = lambda manifest, files, pin: True
        stub.join = lambda groups, files: ("joined", groups)
        seen = []

        def join(push, records):
            seen.append(push.groups)
            return {"green": True, "tests": [], "vectors": [{"id": "v", "ok": True}]}
        with tempfile.TemporaryDirectory() as tmp:
            where, pin = self.store(tmp)
            push = cli.parts.Push(head=B, tests=[], groups="inputs", asked=[], units=[], lic=[], missing=[])
            kos = types.SimpleNamespace(meta={"exam_pin": pin}, push=push)
            out = Path(tmp) / "run"
            argv = ["join-parts", "--root", tmp, "--pulled", tmp, "--deps", tmp, "--work", tmp, "--out", str(out)]
            with mock.patch.dict(sys.modules, {"snowball_bootstrap.answers": stub}), \
                    mock.patch.object(cli, "_kos", return_value=kos), mock.patch.object(cli.parts, "join", join):
                self.assertEqual(cli.main(argv + ["--exam", str(where)]), 0)
                run = json.loads((out / "run.json").read_text())
                self.assertEqual((run["exam"], seen), ({"status": "read", "exam_sha256": pin}, [("joined", "inputs")]))
                self.assertEqual(cli.main(argv + ["--exam", str(Path(tmp) / "none")]), 0)
                run = json.loads((out / "run.json").read_text())
                self.assertEqual((run["exam"]["status"], run["vectors"], run["green"]), ("unavailable", [], False))
                self.assertEqual(len(seen), 1)  # nothing joined without the pinned store


class WorkflowEnvironmentsTest(unittest.TestCase):
    """E516, plan A's T8 changed by the critique: no `docker` in any Environment job; each secret in its own
    Environment's job and in one step's env only; the new jobs run only under a pin and hold nothing."""

    def jobs(self):
        names = re.findall(r"(?m)^  ([a-z_]+):\n", WORKFLOW.split("\njobs:\n", 1)[1])
        return {name: workflow_job(name) for name in names}

    def test_no_environment_job_runs_docker_and_each_secret_stays_in_its_step(self):  # kos_parca_gets_environment answers_key_job_level
        jobs = self.jobs()
        environments = {name: re.findall(r"(?m)^    environment: (\S+)$", text) for name, text in jobs.items()}
        self.assertEqual({k: v for k, v in environments.items() if v}, {"kos": ["answers"], "cagir": ["rival"]})
        for name, text in jobs.items():
            if environments[name]:
                self.assertNotIn("docker", text, f"{name} holds an Environment and runs docker")
            secrets = re.findall(r"(?m)^( *)[A-Z_]+: \$\{\{ secrets\.([A-Z_]+) \}\}$", text)
            if not environments[name]:
                self.assertEqual(secrets, [], f"{name} reads a secret without an Environment")
            for indent, secret in secrets:
                self.assertEqual(len(indent), 10, f"{secret} in {name} is not in a step's env")
        fetch = jobs["kos"].split("      - name: The exam store at the epoch's pin", 1)[1].split("\n      - ", 1)[0]
        self.assertEqual(re.findall(r"secrets\.([A-Z_]+)", fetch), ["ANSWERS_KEY", "EXAM_REPO"])

    def test_the_exam_is_fetched_only_under_a_pin_silently_and_shredded(self):  # exam_fetch_without_pin_gate exam_clone_logged
        kos = workflow_job("kos")
        fetch = kos.split("      - name: The exam store at the epoch's pin", 1)[1].split("\n      - ", 1)[0]
        self.assertIn("        if: needs.cek.outputs.exam_pinned == 'true'\n", fetch)
        self.assertIn("        continue-on-error: true", fetch)
        self.assertIn('trap \'shred -u "$key"', fetch)
        self.assertTrue(re.search(r'(?m)^ *git clone [^\n]* exam > /dev/null 2>&1$', fetch), fetch)
        self.assertIn("StrictHostKeyChecking=yes", fetch)
        self.assertLess(kos.index("The exam store at the epoch's pin"), kos.index("join-parts"))
        self.assertIn("--exam exam --target hedef", kos)
        shred = kos.split("      - name: Shred the exam store", 1)[1].split("\n      - ", 1)[0]
        self.assertIn("        if: always()\n", shred)
        self.assertIn("exam_pinned: ${{ steps.pull.outputs.exam_pinned }}", workflow_job("cek"))
        self.assertIn("--prev-result state/prev/result.json", workflow_job("cek"))

    def test_the_watchers_and_the_target_run_only_under_a_pin_and_hold_nothing(self):  # gozcu_runs_without_pin
        for name, command in (("gozcu", "watch"), ("kos_hedef", "run-target")):
            job = workflow_job(name)
            self.assertIn("    if: needs.cek.outputs.exam_pinned == 'true' && needs.cek.outputs.run_tests == 'true'\n",
                          job, name)
            self.assertIn("    permissions: {}\n", job)
            self.assertNotIn("environment:", job)
            self.assertNotIn("secrets.", job)
            self.assertIn(f"-m snowball_bootstrap {command} ", job)
        yaz = workflow_job("yaz")
        self.assertIn("--gozcu gozcu", yaz)
        self.assertIn("--job gozcu=${{ needs.gozcu.result }}", yaz)
        self.assertIn('check gozcu.tar "${{ needs.gozcu.outputs.gozcu_sha }}"', yaz)


class ScorecardIstismarTest(unittest.TestCase):
    """E516: the card's istismar block counts only a pinned exam's signed results."""

    def setUp(self):
        spec = importlib.util.spec_from_file_location("founder_scorecard_e516", ROOT / "seed" / "founder" /
                                                      "scorecard.py")
        self.sc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.sc)

    def test_istismar_by_watcher_warnings_and_unverifiable_from_pinned_results_only(self):  # scorecard_counts_unpinned
        two = "snowball-bootstrap-result/2"
        results = [
            {"schema": two, "istismar": [{"watcher": "G1"}, {"watcher": "G4"}],
             "warnings": ["gozcu_suphe:G3", "unverifiable:2", "rival_side_retry:1"]},
            {"schema": two, "istismar": [], "warnings": ["gozcu_declared:G2", "ezber_suphe:G5", "unverifiable:1"]},
            {"schema": "snowball-bootstrap-result/1", "istismar": [{"watcher": "G2"}], "warnings": ["gozcu_suphe:G1"]},
        ]
        block = self.sc.honesty(results)
        self.assertEqual(block["pinned_pushes"], 2)
        self.assertEqual((block["pushes_with"]["x"], block["pushes_with"]["n"]), (1, 2))
        self.assertEqual(block["by_watcher"], {"G1": 1, "G2": 0, "G3": 0, "G4": 1, "G5": 0})
        self.assertEqual(block["warnings"], {"gozcu_suphe": 1, "gozcu_declared": 1, "ezber_suphe": 1})
        self.assertEqual(block["unverifiable"], 3)
        self.assertEqual(self.sc.honesty([])["pinned_pushes"], 0)
        page = self.sc.render_public(dict(json.loads((ROOT / "docs" / "karne.json").read_text(encoding="utf-8")),
                                          istismar=block))
        self.assertIn("| İstismar kaydı olan push | 1/2 (ölçülemez: n < 5) |", page)

    def test_the_held_gap_is_private_and_per_epoch(self):
        self.assertTrue(self.sc.held_gap(None).startswith("GAP"))
        rows = self.sc.held_gap([{"epoch": 10, "seen": {"n": 20, "pass": 18}, "held": {"n": 3, "pass": 1}}])
        self.assertEqual(rows[0]["seen"]["ci95"], ["0.68", "0.99"])
        self.assertEqual(rows[0]["held"]["verdict"], "UNMEASURABLE")
        self.assertNotIn("held_gap", json.loads((ROOT / "docs" / "karne.json").read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
