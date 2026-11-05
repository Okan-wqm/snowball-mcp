"""E516, the wiring of the private exam, the K6 fence and the watchers (plan A/F/G, WP-INT): one switch, the last seed
epoch's `exam_sha256`. Before it the referee judges and signs exactly as it did (`test_stage0_unchanged` holds every
field); from it on the result is /2 with `exam`, `k6` and `istismar`, and each new reason is judged as the plan says.
At the merge (merge/afg-train) the stubs are gone: every test here runs the packages' own modules (answers, fence, k6,
target_run, watchers), and only docker and the network are stood in for."""

from __future__ import annotations

import base64
import dataclasses
import hashlib
import importlib.util
import io
import json
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from snowball_bootstrap import answers, cli, config, decide as decide_module, fence, k6, watchers
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
SALT = bytes(range(32))
ALL = list(watchers.WATCHERS)


def params(live=ALL):
    return watchers.load_params(json.dumps({"salt": SALT.hex(), "live": live, "max_suspects": 5,
                                            "g5_alpha": "0.001", "g5_min_fail": 3}).encode())


def summary_doc(*rows, targets=(COPY,)):
    return {"seed_commit": "a" * 40, "seed_tree_sha256": "b" * 64, "seed_epochs": list(rows), "targets": list(targets)}


def load(doc):
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "setup").mkdir()
        (Path(tmp) / "setup" / "summary.json").write_text(json.dumps(doc))
        return load_summary(Path(tmp))


def verdict(findings=(), live=ALL, head=B, unverifiable=0):
    """What `kos` writes into run.json of the watchers (`cli._published`): `gozcu`'s findings published by the
    watchers' own rule under the epoch's parameters."""
    return {"head": head, "status": "read", "published": watchers.publish(list(findings), params(live)),
            "unverifiable": unverifiable}


def read_run(watched=None, **exam):
    run = green_run()
    run["vectors"] = [{"id": "v1", "ok": True}, {"id": "v2", "ok": True}]
    run["exam"] = {"status": "read", "exam_sha256": PIN, **exam}
    run["watchers"] = verdict() if watched is None else watched
    return run


def tamper(path=".github/workflows/ci.yml", declared=False, confirmed=watchers.CONFIRM_RUNS):
    """G4a's finding on a touch of the exam itself (`watchers.g4a`): a mechanical trigger with its reproducer, by
    default as a separate run confirmed it 3/3 (E521); ``confirmed=0`` is how the static pass writes it."""
    return watchers.Finding("G4a", watchers.EXAM_TAMPER, path, watchers.ISTISMAR, path, {"tree": B, "path": path},
                            declared, confirmed)


READ = object()  # `pinned`'s default run: green, with the pinned exam read and the watchers' verdict


def k6_field(status):
    """A signed `k6` field as `k6.signed_field` writes it (E520): the public keys alone."""
    return {"status": status, "fell_from_live": False, "exam_sha256": PIN, "scope": k6.SCOPE, "sealed_sha256": "a" * 64}


def pinned(meta=None, run=READ, jobs=None, findings=(), live=ALL, unverifiable=0, fence=None):
    meta = meta or meta_("code", state0(), run_rival=False)
    run = read_run(verdict(findings, live, unverifiable=unverifiable)) if run is READ else run
    return decide(meta, run, None, None, dict(JOBS, **(jobs or {})), 2, 3, exam_pin=PIN, fence=fence)


def signed(tmp: Path, doc: dict, bound: bool = True) -> Path:
    """A last signed result and the Sigstore bundle beside it, as `fetch-state` leaves them: the bundle's
    `messageDigest` is the result's sha256 (`fence.signed_status`), or another's when not ``bound``."""
    raw = json.dumps(doc).encode()
    path = tmp / "result.json"
    path.write_bytes(raw)
    digest = hashlib.sha256(raw if bound else raw + b" ").digest()
    (tmp / "result.json.sigstore.json").write_text(json.dumps({"messageSignature": {"messageDigest": {
        "algorithm": "SHA2_256", "digest": base64.b64encode(digest).decode()}}}))
    return path


def store(tmp: Path, extra=None, inputs=None):
    """A real exam store (`answers.write_exam`): the visible answers of ``inputs`` (none: a seed with no group), the
    watchers' parameters and any ``extra`` file of the version. Returns (store, pin, canary)."""
    files = {"watchers.json": json.dumps({"salt": SALT.hex(), "live": [], "max_suspects": 5, "g5_alpha": "0.001",
                                         "g5_min_fail": 3}).encode(), **(extra or {})}
    files = {k: v for k, v in files.items() if v is not None}
    where = tmp / "exam"
    pin, canary = answers.write_exam(where, inputs or {"schema": answers.SEED_SCHEMA}, {}, burned=False, extra=files)
    return where, pin, canary


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
            self.assertRegex(str(caught.exception), r"safety_paths (is required|must name at least one path)")
        toy = dict(bare, id="toy", kind="toy")
        loaded = load(summary_doc(dict(ROW, exam_sha256=PIN), targets=(COPY, toy)))
        self.assertEqual(loaded.targets[0].safety_paths, ("units/pump",))
        self.assertIsNone(loaded.targets[1].safety_paths)

    def test_the_operator_cannot_call_an_unread_exam_or_istismar_an_exam_fault(self):  # unwaivable_exam_fault_taken
        self.assertEqual(config.UNWAIVABLE_REASONS, ("answers_unavailable", "istismar"))
        from snowball_bootstrap import answers, watchers  # the names config cannot import (watchers imports config)
        self.assertEqual(config.UNWAIVABLE_REASONS, (answers.REASON, watchers.ISTISMAR))
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
            suites = [{"id": "core", "kind": "cargo", "root": ".", "cwd": "crates/core", "cmd": "cargo test"}]
            for doc, want in ((base, None),
                              (dict(base, target_image="t@sha256:" + "b" * 64, target_suites=suites),
                               "t@sha256:" + "b" * 64),
                              (dict(base, target_image="node:22", target_suites=suites), ConfigError),
                              (dict(base, target_image="t@sha256:" + "b" * 64), ConfigError),  # no suites
                              (dict(base, target_suites=suites), ConfigError),  # suites and no image
                              (dict(base, target_image="t@sha256:" + "b" * 64, target_suites=[]), ConfigError)):
                (Path(tmp) / "bootstrap.json").write_text(json.dumps(doc))
                if want is ConfigError:
                    with self.assertRaises(ConfigError):
                        config.load_bootstrap(Path(tmp))
                else:
                    loaded = config.load_bootstrap(Path(tmp))
                    self.assertEqual(loaded.target_image, want)
                    self.assertEqual([s.id for s in loaded.target_suites], ["core"] if want else [])


class ExamTamperTest(unittest.TestCase):
    """E516, G4a: the exam's machinery in a brain push (the watchers' one list, `watchers.PROTECTED_EXAM`), rejected
    outright under a pin only."""

    def test_the_exam_slots_are_exam_tamper_only_under_a_pin(self):  # exam_tamper_without_pin exam_tamper_case_sensitive exam_tamper_unread
        changed = ["referee/vectors/vectors.json", "referee/Setup/x", "referee/gate/x.py", "referee/vectorsX/y"]
        self.assertEqual(classify(changed), ("code", []))
        kind, reasons = classify(changed, exam_pinned=True)
        self.assertEqual((kind, reasons), ("rejected", ["exam_tamper:referee/Setup/x",
                                                        "exam_tamper:referee/vectors/vectors.json"]))
        self.assertEqual(set(watchers.EXAM_SLOTS),
                         {"referee/" + name for name in ("bootstrap", "bootstrap.json", "control.json", "policy.json",
                                                         "seats", "setup", "vectors")})
        self.assertTrue(set(watchers.EXAM_SLOTS) <= set(watchers.PROTECTED_EXAM))  # one list, the watchers'
        self.assertEqual(classify(["referee/jest.config.js"], exam_pinned=True)[1],
                         ["exam_tamper:referee/jest.config.js"])  # G4a's runner configurations, from the same list
        many = [f"referee/seats/{i:02d}" for i in range(30)]
        from snowball_bootstrap import classify as classify_module
        self.assertEqual(len(classify(many, exam_pinned=True)[1]), classify_module.EXAM_TAMPER_LIMIT)
        self.assertEqual(classify_module.EXAM_TAMPER, watchers.EXAM_TAMPER)

    def test_pull_gives_classify_the_command_roots_and_the_runner_sections(self):
        # classify_roots_dropped classify_read_dropped exam_view_before_pin
        """E522 (verifier finding 7): pull reads the base manifest's commands for the directories they run Python
        from and hands classify a reader of a file at the base and the head, on a real repository: `referee/argparse.py`
        (shadows the runner from `cd referee`) and package.json's test script are exam_tamper; a dependency bump and an
        honest package named like a stdlib module are not. With no pin classify gets nothing of it."""
        if shutil.which("git") is None:
            self.skipTest("git is not installed")
        git = ["git", "-c", "user.email=x@y", "-c", "user.name=x", "-c", "core.autocrlf=false"]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            manifest = {"tests": [{"id": "T1", "cmd": "cd referee && python -m unittest discover -s tests",
                                   "stage": 0}], "done_mf": [], "lockfiles": []}
            files = {"snowball-tests.json": json.dumps(manifest), "referee/x.py": "x = 1\n",
                     "package.json": json.dumps({"version": "1", "scripts": {"test": "jest"}}),
                     "lib/package.json": json.dumps({"version": "1"})}

            def commit(tree):
                for rel, text in tree.items():
                    (repo / rel).parent.mkdir(parents=True, exist_ok=True)
                    (repo / rel).write_text(text, encoding="utf-8")
                for args in (["add", "-A"], ["commit", "-qm", "x"]):
                    subprocess.run(git + args, cwd=repo, check=True, capture_output=True)
                return subprocess.run(git + ["rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True,
                                      text=True).stdout.strip()
            subprocess.run(git + ["init", "-q"], cwd=repo, check=True, capture_output=True)
            base = commit(files)
            head = commit({"referee/argparse.py": "x = 2\n", "referee/profile/__init__.py": "",
                           "package.json": json.dumps({"version": "1", "scripts": {"test": "true"}}),
                           "lib/package.json": json.dumps({"version": "2"})})
            changed = sorted(cli.gitio.changed_paths(repo, base, head))
            view = cli._exam_view(repo, base, head, True, True)
            self.assertEqual(classify(changed, **view), ("rejected", ["exam_tamper:package.json",
                                                                      "exam_tamper:referee/argparse.py"]))
            self.assertEqual(cli._exam_view(repo, base, head, True, False), {"exam_pinned": False})
            self.assertEqual(classify(changed, **cli._exam_view(repo, base, head, True, False)), ("code", []))

    def test_pull_shields_the_standard_modules_the_base_tests_import(self):
        # exam_view_shield_dropped exam_view_cap_open exam_view_head_tree_read exam_view_under_dropped
        """E523: pull reads the base's test modules on a real repository and fences, at the directories the base
        commands run Python from, a new module of a standard name they import (`referee/json.py`), never the brain's
        own `referee/profile/`, a new module no test imports, or one the push's own new test imports. Over the cap
        every standard name counts. A new fixture's package.json with a test script runs none of the base's tests
        and is ordinary work (the honest brain's 8223c90)."""
        if shutil.which("git") is None:
            self.skipTest("git is not installed")
        git = ["git", "-c", "user.email=x@y", "-c", "user.name=x", "-c", "core.autocrlf=false"]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            manifest = {"tests": [{"id": "T1", "cmd": "cd referee && python -m unittest discover -s tests",
                                   "stage": 0}], "done_mf": [], "lockfiles": []}
            files = {"snowball-tests.json": json.dumps(manifest), "referee/profile/__init__.py": "x = 1\n",
                     "referee/tests/test_a.py": "import json\nimport profile\nfrom harness import x\n",
                     "referee/tests/test_broken.py": "def (:\n"}

            def commit(tree):
                for rel, text in tree.items():
                    (repo / rel).parent.mkdir(parents=True, exist_ok=True)
                    (repo / rel).write_text(text, encoding="utf-8")
                for args in (["add", "-A"], ["commit", "-qm", "x"]):
                    subprocess.run(git + args, cwd=repo, check=True, capture_output=True)
                return subprocess.run(git + ["rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True,
                                      text=True).stdout.strip()
            subprocess.run(git + ["init", "-q"], cwd=repo, check=True, capture_output=True)
            base = commit(files)
            head = commit({"referee/json.py": "def loads(_t):\n    return 2\n",
                           "referee/profile/__init__.py": "x = 2\n",
                           "referee/calendar.py": "", "referee/harness.py": "",
                           "referee/tests/test_b.py": "import secrets\n", "referee/secrets.py": "",
                           "tests/fixtures/toy/package.json": json.dumps({"scripts": {"test": "node --test"}})})
            changed = sorted(cli.gitio.changed_paths(repo, base, head))
            view = cli._exam_view(repo, base, head, True, True)
            self.assertEqual(classify(changed, **view), ("rejected", ["exam_tamper:referee/json.py"]))
            with mock.patch.object(watchers, "TEST_IMPORT_FILES", 1):
                wide = cli._exam_view(repo, base, head, True, True)
            self.assertEqual(classify(changed, **wide), ("rejected", ["exam_tamper:referee/calendar.py",
                                                                      "exam_tamper:referee/json.py",
                                                                      "exam_tamper:referee/secrets.py"]))

    def test_exam_tamper_is_the_founders_rejection(self):
        """A push pull rejects runs no watcher, so its exam_tamper is a rejection that counts, with no istismar entry:
        the istismar label needs the watchers' live switch, which only `kos` holds (the epoch's private store)."""
        meta = meta_("rejected", state0(), run_tests=False, run_rival=False,
                     pre_reasons=["exam_tamper:referee/vectors/x"])
        res = pinned(meta, run=None, jobs={"gozcu": "skipped", "kos": "skipped"})
        self.assertEqual((res["verdict"], res["istismar"]), ("rejected", []))
        self.assertTrue(decide_module.counts_against_founder(res["reasons"][0]))


class NoPinTest(unittest.TestCase):
    """E516: with no pin nothing new is read or signed (`test_stage0_unchanged` holds the whole flow field by field)."""

    def test_no_pin_signs_the_result_it_always_signed(self):  # pinned_fields_without_pin
        meta = meta_("code", state0(), run_rival=False)
        fence_doc = {"head": B, "reasons": ["safety_path_closed:units/pump/a"]}
        run = dict(green_run(), watchers=verdict([tamper()]))
        plain = decide(meta, green_run(), None, None, JOBS, 2, 3)
        given = decide(meta, run, None, None, JOBS, 2, 3, fence=fence_doc)
        self.assertEqual(given, plain)
        self.assertEqual(plain["schema"], "snowball-bootstrap-result/1")
        self.assertEqual({"exam", "k6", "istismar"} & set(plain), set())
        self.assertEqual(plain["verdict"], "accepted")


class PinnedResultTest(unittest.TestCase):
    """E516: a pinned result is /2 and carries the exam, the K6 status and the istismar entries."""

    def test_a_clean_pinned_push_is_accepted_with_its_three_fields(self):
        meta = meta_("code", state0(), run_rival=False, k6_prev=k6_field("exam_built"))
        res = pinned(meta)
        self.assertEqual((res["schema"], res["verdict"], res["reasons"]), ("snowball-bootstrap-result/2", "accepted", []))
        self.assertEqual(res["exam"], {"exam_sha256": PIN, "visible": {"n": 2, "pass": 2}})
        self.assertEqual(res["k6"], k6_field("exam_built"))
        self.assertEqual(res["istismar"], [])

    def test_the_k6_field_falls_closed(self):  # k6_unknown_status_kept k6_unchecked_at_signing
        run = dict(read_run(), k6=k6_field("live"))
        self.assertEqual(pinned(run=run)["k6"], k6_field("live"))
        meta = meta_("code", state0(), run_rival=False, k6_prev=k6_field("live"))
        self.assertEqual(pinned(meta, run=dict(read_run(), k6=k6_field("maybe")))["k6"], k6_field("live"))
        for fresh, carried in ((k6_field("LIVE"), None), (None, k6_field(True)), (None, None), ("live", "live"),
                               (dict(k6_field("live"), families={"S": {"killed": 9}}), None),  # E520: more than public
                               ({"status": "live"}, None)):
            meta = meta_("code", state0(), run_rival=False, k6_prev=carried)
            self.assertEqual(pinned(meta, run=dict(read_run(), k6=fresh))["k6"], {"status": "not_live"}, (fresh, carried))
        self.assertEqual(decide_module._k6(k6_field("exam_strong"), None)["status"], "exam_strong")
        self.assertEqual(k6.STATUSES, ("not_live", "exam_built", "exam_strong", "live"))  # what `_k6` reads

    def test_an_unread_exam_is_retried_and_never_the_founders(self):  # exam_pin_not_compared_in_yaz answers_unavailable_judged answers_unavailable_counted
        self.assertIn("answers_unavailable", decide_module.NOT_THE_FOUNDERS)
        self.assertEqual(decide_module.ANSWERS_UNAVAILABLE, answers.REASON)
        for run in ({"exam": {"status": "unavailable", "why": "store", "exam_sha256": None},
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
    """E516, plan D9: istismar is the watchers' own rule (`watchers.level`), applied once, in `kos`, under the epoch's
    private parameters; `decide` maps the published verdict by the watchers' `reasons` and `warnings`."""

    def test_istismar_is_the_watchers_rule_and_decide_maps_it(self):  # watcher_not_live_counts
        res = pinned(findings=[tamper(), tamper(".github/workflows/deploy.yml", declared=True)])
        self.assertEqual([(r["kind"], r["ref"]) for r in res["reasons"]],
                         [("istismar", "G4a:.github/workflows/ci.yml")])
        self.assertEqual([(e["watcher"], e["ref"], e["level"]) for e in res["istismar"]],
                         [("G4a", ".github/workflows/ci.yml", "istismar")])
        self.assertEqual(res["istismar"][0]["sealed_sha256"],
                         watchers.evidence_hash(SALT, dataclasses.asdict(tamper())))
        self.assertEqual(res["verdict"], "rejected")
        self.assertIn("gozcu_suphe:1", res["warnings"])  # the declared one: a warning, never istismar, one of a count
        shadow = pinned(findings=[tamper()], live=[])  # a watcher not yet live says what it would have said
        self.assertEqual((shadow["verdict"], shadow["istismar"]), ("accepted", []))
        self.assertIn("gozcu_suphe:1", shadow["warnings"])
        suspect = pinned(findings=[tamper(confirmed=2)])  # E521: short of 3/3 it is a suspect, one of the warnings
        self.assertEqual((suspect["verdict"], suspect["istismar"], suspect["reasons"]), ("accepted", [], []))
        self.assertIn("gozcu_suphe:1", suspect["warnings"])

    def test_istismar_counts_against_the_founder_and_keeps_its_streak(self):  # istismar_not_counted
        state = state0(reject_streaks={"istismar:G4a:.github/workflows/ci.yml": 1})
        res = pinned(meta_("code", state, run_rival=False), findings=[tamper()])
        self.assertTrue(decide_module.counts_against_founder(res["reasons"][0]))
        self.assertEqual(res["state"]["reject_streaks"], {"istismar:G4a:.github/workflows/ci.yml": 2})
        self.assertEqual(res["learning"]["repeated"], ["istismar:G4a:.github/workflows/ci.yml"])
        self.assertEqual(res["state"]["last_evaluated_sha"], B)

    def test_drift_on_held_cases_is_a_normal_rejection_with_one_switch(self):  # g5_default_literal
        """Owner decision (b), closed 2026-11-02 (E521): one named constant, `watchers.G5_DROP_RULE`, default the
        owner's rule; decide keeps no second one. Drift on the held cases is `behaviour_drift`, a normal rejection that
        counts against the Founder and is never istismar; the signed result names no case."""
        self.assertEqual(watchers.G5_DROP_RULE, watchers.G5_DRIFT)
        self.assertFalse([n for n in vars(decide_module) if "DROP" in n or n.startswith("G5")])
        drop = watchers.Finding("G5", watchers.BEHAVIOUR_DRIFT, "held", watchers.REJECTION,
                                {"drifted": ["HELD-CASE-7"]}, {"cmd": "x"})
        res = pinned(findings=[drop])
        self.assertEqual([(r["kind"], r["ref"]) for r in res["reasons"]], [("behaviour_drift", "G5:held")])
        self.assertNotIn("HELD-CASE-7", json.dumps(res))
        self.assertTrue(decide_module.counts_against_founder(res["reasons"][0]))
        self.assertEqual(res["istismar"], [])

    def test_unverifiable_claims_are_a_warning_never_istismar(self):
        res = pinned(unverifiable=4)
        self.assertEqual((res["verdict"], res["istismar"]), ("accepted", []))
        self.assertIn("unverifiable:4", res["warnings"])

    def test_a_push_over_the_static_bound_is_the_founders_rejection(self):  # watchers_too_large_accepted
        res = pinned(run=read_run({"head": B, "status": "too_large"}))
        self.assertEqual([(r["kind"], r["ref"]) for r in res["reasons"]], [("gozcu_input_too_large", "gozcu")])
        self.assertTrue(decide_module.counts_against_founder(res["reasons"][0]))

    def test_the_watchers_must_answer_for_this_head(self):  # gozcu_other_head_taken gozcu_not_expected
        other = pinned(run=read_run(verdict([tamper()], head=A)))
        self.assertEqual([(r["kind"], r["ref"]) for r in other["reasons"]], [("infra", "gozcu:malformed")])
        self.assertIsNone(other["state"]["last_evaluated_sha"])
        good = verdict([tamper()])
        entry = good["published"]["istismar"][0]
        for bad in ({"head": B, "status": "missing"}, dict(good, published={"istismar": []}),
                    dict(good, published=dict(good["published"], warning=[])),
                    dict(good, published=dict(good["published"], warning=-1)),
                    dict(good, published=dict(good["published"], warning=True)),
                    dict(good, published=dict(good["published"], rejection=[entry])),
                    dict(good, published=dict(good["published"], istismar=[dict(entry, watcher="G9")])),
                    dict(good, published=dict(good["published"], istismar=[dict(entry, signal="s")])),
                    dict(good, published=dict(good["published"], istismar=[dict(entry, sealed_sha256="x")])),
                    "x"):
            res = pinned(run=read_run(bad))
            self.assertEqual([r["ref"] for r in res["reasons"]], ["gozcu:malformed"], repr(bad)[:80])
        failed = pinned(jobs={"gozcu": "failure"})
        self.assertEqual([(r["kind"], r["ref"]) for r in failed["reasons"]], [("infra", "gozcu:failure")])
        spec = pinned(meta_("spec", state0(), run_rival=False), run=None, jobs={"gozcu": "skipped"})
        self.assertEqual(spec["verdict"], "frozen")  # a spec push has no `gozcu` run to wait for


class FenceTest(unittest.TestCase):
    """E516, plan D6: the fence's two reasons, from the referee's `fence` (E511) on a copy diff, are the Founder's."""

    def test_the_fence_reasons_are_the_founders(self):  # fence_doc_unread
        doc = {"head": B, "reasons": ["safety_path_closed:units/pump/a.rs", "safety_list_narrowed:units/pump",
                                      "other:x", {"kind": "safety_path_closed"}]}
        res = pinned(fence=doc)
        self.assertEqual([(r["kind"], r["ref"]) for r in res["reasons"]],
                         [("safety_path_closed", "units/pump/a.rs"), ("safety_list_narrowed", "units/pump")])
        self.assertEqual((fence.CLOSED, fence.NARROWED), ("safety_path_closed", "safety_list_narrowed"))
        self.assertTrue(all(decide_module.counts_against_founder(r) for r in res["reasons"]))
        self.assertEqual(pinned(fence=dict(doc, head=A))["verdict"], "accepted")  # another head's fence

    def run_fence(self, k6_doc, derived=None, bound=True):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "setup").mkdir()
            (root / "setup" / "summary.json").write_text(json.dumps(summary_doc(dict(ROW, exam_sha256=PIN))))
            prev = signed(root, {"k6": k6_doc} if k6_doc is not None else {})
            if not bound:
                signed(root, {"k6": k6_doc}, bound=False)
            argv = ["fence", "--root", tmp, "--copy", tmp, "--base", "1" * 40, "--head", "2" * 40, "--target", "copy",
                    "--prev-result", str(prev), "--out", str(root / "out")]
            if derived is not None:
                (root / "derived.json").write_text(json.dumps({"security_paths": derived}))
                argv += ["--derived", str(root / "derived.json")]
            with mock.patch.object(cli.gitio, "changed_paths", return_value=["units/pump/a.rs", "units/b.py"]), \
                    mock.patch.object(cli.gitio, "tree_reader", return_value=((), lambda path: None)):
                self.assertEqual(cli.main(argv), 0)
            return json.loads((root / "out" / "fence.json").read_text())

    def test_the_fence_command_reads_the_signed_k6_status_and_the_owners_list(self):  # fence_open_when_live_ignored
        closed = self.run_fence({"status": "exam_strong"})
        self.assertEqual(closed, {"head": "2" * 40, "k6_status": "exam_strong",
                                  "reasons": ["safety_path_closed:units/pump/a.rs"]})
        self.assertEqual(self.run_fence(None)["k6_status"], "not_live")
        self.assertEqual(self.run_fence({"status": "live"})["reasons"], [])
        unbound = self.run_fence({"status": "live"}, bound=False)  # a status no signature covers opens nothing
        self.assertEqual((unbound["k6_status"], unbound["reasons"]),
                         ("unbound", ["safety_path_closed:units/pump/a.rs"]))
        self.assertEqual(self.run_fence({"status": "live"}, derived=["units/other"])["reasons"],
                         ["safety_list_narrowed:units/pump"])
        self.assertEqual(self.run_fence({"status": "live"}, derived=["units/**"])["reasons"], [])


class PinnedCommandsTest(unittest.TestCase):
    """E516: the commands read the pin from the snapshot, and a pinned run without a package module stops."""

    def test_a_missing_package_module_stops_a_pinned_run(self):  # pinned_module_missing_is_silent
        with self.assertRaises(ConfigError) as caught:
            cli.pinned_module("no_such_module_e516", "E516")
        self.assertIn("snowball_bootstrap/no_such_module_e516.py (E516)", str(caught.exception))
        self.assertIs(cli.pinned_module("canon", "E516"), sys.modules["snowball_bootstrap.canon"])

    def test_the_exam_store_is_read_only_at_the_pin(self):  # exam_store_pin_unchecked
        with tempfile.TemporaryDirectory() as tmp:
            where, pin, canary = store(Path(tmp), {answers.K6_SUMMARY: b"{}"})
            got = cli.exam_store(where, pin)
            self.assertEqual((got.pin, got.visible.canary, got.read(answers.K6_SUMMARY)), (pin, canary, b"{}"))
            for missing in (None, Path(tmp) / "none"):
                with self.assertRaises(answers.AnswersError):
                    cli.exam_store(missing, pin)
            with self.assertRaises(answers.AnswersError):
                cli.exam_store(where, "0" * 64)  # no exam at that pin
            manifest = where / answers.EXAMS / pin / answers.MANIFEST
            manifest.write_bytes(manifest.read_bytes().replace(b'"files"', b'"files" ', 1))
            with self.assertRaises(answers.AnswersError):
                cli.exam_store(where, pin)  # a manifest that is not the pinned bytes
            manifest.write_bytes(manifest.read_bytes().replace(b'"files" ', b'"files"', 1))
            (where / answers.EXAMS / pin / "k6" / "summary.json").write_bytes(b"{ }")
            with self.assertRaises(answers.AnswersError):
                cli.exam_store(where, pin).read(answers.K6_SUMMARY)  # one flipped byte in a listed file

    def test_kos_reads_and_holds_only_its_files_of_the_store(self):  # kos_reads_any_store_file kos_store_held_unchecked
        """E522 (verifier finding 2): `kos` reads the manifest, the visible answers, the watchers' parameters and the
        K6 summary of the pinned version, and a store folder that holds anything more (the held set, the K6 exam,
        another version, a git clone of the whole store) judges nothing: it is not what `fetch_exam` leaves."""
        with tempfile.TemporaryDirectory() as tmp:
            where, pin, _canary = store(Path(tmp), {answers.K6_SUMMARY: b"{}"})
            got = cli.exam_store(where, pin)
            for rel in ("k6/exam.json", "k6/runs.json", "held/vectors.json", answers.MANIFEST):
                with self.assertRaises(ValueError):
                    got.read(rel)
            self.assertEqual(answers.on_disk(where, pin), [])
            for extra in ("held/vectors.json", f"{answers.EXAMS}/{pin}/k6/exam.json", f"{answers.EXAMS}/{'0' * 64}/"
                          f"{answers.MANIFEST}", ".git/config", f"{answers.EXAMS}/{pin}/.fetch/HEAD"):
                path = where.joinpath(*extra.split("/"))
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"x")
                with self.assertRaises(answers.AnswersError, msg=extra):
                    cli.exam_store(where, pin)
                self.assertEqual(answers.on_disk(where, pin), [extra])
                path.unlink()
            self.assertEqual(cli.exam_store(where, pin).pin, pin)

    def test_kos_view_is_the_manifest_and_kos_files_of_exam_versions_alone(self):  # kos_view_whole_version
        """E522: `kos`'s repository may hold, of any exam version, its manifest and the files `kos` reads; another
        file of a version (the K6 exam, a held case), a file beside the versions or a path that only looks like one
        is not its view, and the paths `kos` reads are named for the pin alone."""
        pin = "a" * 64
        view = [f"{answers.EXAMS}/{pin}/{rel}" for rel in (answers.MANIFEST, *answers.KOS_FILES)]
        self.assertEqual(answers.kos_paths(pin), view)
        self.assertTrue(answers.kos_view(view + [f"{answers.EXAMS}/{'b' * 64}/{answers.MANIFEST}"]))
        self.assertTrue(answers.kos_view([]))
        for extra in (f"{answers.EXAMS}/{pin}/k6/exam.json", f"{answers.EXAMS}/{pin}/held/vectors.json",
                      "README.md", "held/vectors.json", f"{answers.EXAMS}/{pin[:-1]}/{answers.MANIFEST}",
                      f"{answers.EXAMS}/{pin}/{answers.VISIBLE}.bak", f"x/{answers.EXAMS}/{pin}/{answers.MANIFEST}",
                      f"{answers.EXAMS}/{pin.upper()}/{answers.MANIFEST}"):
            self.assertFalse(answers.kos_view(view + [extra]), extra)
        for bad in (None, "A" * 64, "a" * 63):
            with self.assertRaises(answers.AnswersError):
                answers.kos_paths(bad)

    def test_kos_fetches_its_files_alone_from_a_repository_that_holds_nothing_else(self):
        # kos_view_unchecked fetch_takes_every_blob fetch_clone_left fetch_git_text_kept
        """E522 (verifier finding 2): `fetch_exam` on a real repository (file://, filters served as GitHub serves
        them). From `kos`'s own repository it writes exactly the pinned version's manifest and `KOS_FILES`, leaves no
        clone, and the store opens at the pin. From the whole exam store (the held set beside the version) it reads
        nothing: no file is written and no held blob was ever transferred, as the key would reach it."""
        if shutil.which("git") is None:
            self.skipTest("git is not installed")
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            built, pin, _canary = store(tmp, {answers.K6_SUMMARY: b"{}", "k6/exam.json": b"SECRET-K6-EXAM"})
            version = built / answers.EXAMS / pin
            git = ["git", "-c", "user.email=x@y", "-c", "user.name=x", "-c", "core.autocrlf=false"]

            def repo(name, files):
                src = tmp / name
                for rel, content in files.items():
                    (src / rel).parent.mkdir(parents=True, exist_ok=True)
                    (src / rel).write_bytes(content)
                for args in (["init", "-q"], ["add", "-A"], ["commit", "-qm", "x"],
                             ["config", "uploadpack.allowFilter", "true"],
                             ["config", "uploadpack.allowAnySHA1InWant", "true"]):
                    subprocess.run(git + args, cwd=src, check=True, capture_output=True)
                return src.resolve().as_uri()

            listed = {f"{answers.EXAMS}/{pin}/{rel}": (version / rel).read_bytes()
                      for rel in (answers.MANIFEST, answers.VISIBLE, answers.WATCHERS, answers.K6_SUMMARY)}
            own = repo("own", listed)
            dest = tmp / "fetched"
            cli.fetch_exam(own, pin, dest)
            self.assertEqual(sorted(q.relative_to(dest).as_posix() for q in dest.rglob("*") if q.is_file()),
                             sorted(listed))
            self.assertFalse((dest / ".fetch").exists())
            got = cli.exam_store(dest, pin)
            self.assertEqual(got.read(answers.K6_SUMMARY), b"{}")
            whole = repo("whole", {**listed, f"{answers.EXAMS}/{pin}/k6/exam.json": b"SECRET-K6-EXAM",
                                   "held/vectors.json": b"SECRET-HELD"})
            wide = tmp / "wide"
            with mock.patch.object(cli, "_remove_tree") as kept:  # the clone as it stood when the fetch stopped
                with self.assertRaises(cli.StoreTooWide):
                    cli.fetch_exam(whole, pin, wide)
            self.assertEqual([q.name for q in wide.rglob("*") if q.is_file() and ".fetch" not in q.parts], [])
            missing = subprocess.run(git + ["-C", str(wide / ".fetch"), "rev-list", "--objects", "--missing=print",
                                            "HEAD"], check=True, capture_output=True, text=True).stdout
            self.assertEqual(len([line for line in missing.splitlines() if line.startswith("?")]), 6)  # no blob came
            kept.assert_called_once()
            err = io.StringIO()
            with mock.patch("sys.stderr", err):
                with self.assertRaises(answers.AnswersError) as caught:
                    cli.fetch_exam((tmp / "none").resolve().as_uri(), pin, tmp / "nothing")
            self.assertEqual((str(caught.exception), err.getvalue()), (cli.FETCH_FAILED, ""))  # no git text

    def test_the_operator_makes_the_k6_summary_and_kos_view_on_the_private_side(self):
        # admit_kos_view_unchecked admit_k6_recall_not_the_fences
        """E522: `local/exam_admit.py k6-summary` evaluates a version's K6 documents with the referee checkout's copy
        base and safety list, the held paths measured by the fence's own matcher, and `kos-view` copies of a version
        the files `kos` reads into kos's own repository, refusing a working copy that holds anything else. The
        version written with that salt gives `kos` the status the summary reached."""
        from test_k6 import READY, strong
        admit = importlib.util.spec_from_file_location("exam_admit", BOOT / "local" / "exam_admit.py")
        tool = importlib.util.module_from_spec(admit)
        admit.loader.exec_module(tool)
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            referee, k6dir = tmp / "referee", tmp / "k6"
            (referee / "setup").mkdir(parents=True)
            (referee / "setup" / "summary.json").write_text(json.dumps(summary_doc(ROW)))
            exam, runs = strong()
            raw = json.dumps(exam).encode("utf-8")
            runs["exam_sha256"] = k6.exam_id(raw)
            runs["base"]["commit"] = COPY["base_sha"]
            k6dir.mkdir()
            for name, doc in (("runs.json", runs), ("held_paths.json", ["units/pump/a.rs", "units/pump/b/c.rs"]),
                              ("live_ready.json", READY)):
                (k6dir / name).write_text(json.dumps(doc))
            (k6dir / "exam.json").write_bytes(raw)
            salt = answers.new_salt()
            summary = json.loads(tool.k6_summary(k6dir, salt, referee))
            self.assertEqual((summary["reached"], summary["base_commit"]), ("live", COPY["base_sha"]))
            (k6dir / "held_paths.json").write_text(json.dumps(["units/pump/a.rs", "units/valve.rs"]))
            self.assertEqual(json.loads(tool.k6_summary(k6dir, salt, referee))["reached"], "exam_built")
            where, pin, _canary = store(tmp, {answers.K6_SUMMARY: json.dumps(summary).encode(),
                                              "k6/exam.json": raw, "held/vectors.json": b"SECRET-HELD"})
            out = tmp / "kos-repo"
            (out / ".git").mkdir(parents=True)
            (out / ".git" / "HEAD").write_text("ref: refs/heads/main\n")
            report = tool.kos_view(where, pin, out)
            got = sorted(q.relative_to(out).as_posix() for q in out.rglob("*") if q.is_file() and ".git" not in q.parts)
            self.assertEqual(got, sorted(answers.kos_paths(pin)))
            self.assertEqual(report["files"], sorted([answers.MANIFEST, answers.VISIBLE, answers.WATCHERS,
                                                      answers.K6_SUMMARY]))
            self.assertEqual(tool.kos_view(where, pin, out)["pin"], pin)  # again, the same bytes: nothing changes
            (out / "README.md").write_text("x")
            with self.assertRaisesRegex(tool.AdmitError, "does not read"):
                tool.kos_view(where, pin, out)

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
            (Path(tmp) / "run").mkdir()
            (Path(tmp) / "run" / "run.json").write_text(json.dumps(read_run()))
            argv = ["decide", "--root", str(root), "--pulled", str(pulled), "--run", str(Path(tmp) / "run"),
                    "--out", str(Path(tmp) / "out")]
            argv += [f"--job={k}={v}" for k, v in JOBS.items()]
            for row, schema, kinds in ((dict(ROW, exam_sha256=PIN), "/2", []),
                                       (dict(ROW, exam_sha256="1" * 64), "/2", ["answers_unavailable"]),
                                       (ROW, "/1", [])):
                (root / "setup" / "summary.json").write_text(json.dumps(summary_doc(row)))
                self.assertEqual(cli.main(argv), 0)
                res = json.loads((Path(tmp) / "out" / "result.json").read_text())
                self.assertEqual((res["schema"][-2:], [r["kind"] for r in res["reasons"]]), (schema, kinds))

    def test_pull_carries_the_signed_k6_field_only_under_a_pin(self):  # k6_prev_without_pin k6_prev_unbound
        with tempfile.TemporaryDirectory() as tmp:
            prev = signed(Path(tmp), {"k6": {"status": "live"}})
            meta = {}
            cli._pin_meta(meta, load(summary_doc(ROW)), str(prev))
            self.assertEqual(meta, {})
            cli._pin_meta(meta, load(summary_doc(dict(ROW, exam_sha256=PIN))), str(prev))
            self.assertEqual(meta, {"k6_prev": {"status": "live"}, "exam_pin": PIN})
            cli._pin_meta(meta, load(summary_doc(dict(ROW, exam_sha256=PIN))), str(Path(tmp) / "none.json"))
            self.assertEqual(meta, {"k6_prev": None, "exam_pin": PIN})
            signed(Path(tmp), {"k6": {"status": "live"}}, bound=False)  # bytes the bundle does not sign
            cli._pin_meta(meta, load(summary_doc(dict(ROW, exam_sha256=PIN))), str(prev))
            self.assertEqual(meta["k6_prev"], None)


class JoinPartsTest(unittest.TestCase):
    """E516: `kos` under a pin, on a real exam store: the vectors judged on its visible answers, the watchers' findings
    published under its parameters, K6 evaluated from its documents; nothing that carries the answers is written."""

    INPUTS = {"schema": answers.SEED_SCHEMA, "dg": {
        "owner": "MF1", "runner": "data", "interface": "x.md", "source": "s",
        "cases": [{"id": "d1", "purpose": "p", "cmd": "python -m x", "stdin": "", "fixture": [],
                   "changed": {"description": "c", "cmd": "python -m x 2", "stdin": "", "fixture": []}}]}}
    ANSWER = "sha256:" + "7" * 64  # shaped like an answer only code computes (`vectors.answer_atoms`)
    ANSWERS = {"/dg/cases/0/expect": {"value": ANSWER}, "/dg/cases/0/changed/expect_not": {"value": "zz"}}

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "vectors").mkdir()
        (self.root / "vectors" / "vectors.json").write_text(json.dumps(self.INPUTS))
        (self.root / "setup").mkdir()
        (self.root / "setup" / "summary.json").write_text(json.dumps(summary_doc(dict(ROW, exam_sha256=PIN))))
        self.gozcu = self.root / "gozcu"
        self.gozcu.mkdir()
        self.write_gozcu([tamper(confirmed=0)])

    def write_gozcu(self, found, head=B, status="read"):
        (self.gozcu / "gozcu.json").write_text(json.dumps(
            {"head": head, "status": status, "findings": [dataclasses.asdict(f) if isinstance(f, watchers.Finding)
                                                          else f for f in found]}))

    def exam(self, watchers_json=True, extra=None, live=("G4a",)):
        files = dict(extra or {})
        if watchers_json:
            files["watchers.json"] = json.dumps({"salt": SALT.hex(), "live": list(live), "max_suspects": 5,
                                                 "g5_alpha": "0.001", "g5_min_fail": 3}).encode()
        self.stores = getattr(self, "stores", 0) + 1  # E522: what kos fetched holds one version alone
        where = self.root / f"exam-{self.stores}"
        pin, canary = answers.write_exam(where, self.INPUTS, self.ANSWERS, burned=False, extra=files)
        return where, pin, canary

    def join(self, where, pin, run=None, rc=0):
        seen = {}

        def applied(vectors_dir, done, *, table=None, tree=None, exam=None):
            seen["exam"] = exam
            return "joined"

        def join(push, records):
            seen["groups"] = push.groups
            return dict(run or {"green": True, "tests": [], "vectors": [{"id": "v", "ok": True}]})
        push = cli.parts.Push(head=B, tests=[], groups="inputs", asked=[], units=[], lic=[], missing=[])
        kos = mock.Mock(meta={"exam_pin": pin, "head": B, "manifest": {"done_mf": [1]}}, push=push)
        out = self.root / "run"
        argv = ["join-parts", "--root", str(self.root), "--pulled", str(self.root), "--deps", str(self.root),
                "--work", str(self.root), "--out", str(out), "--exam", str(where), "--gozcu", str(self.gozcu)]
        with mock.patch.object(cli, "_kos", return_value=kos), mock.patch.object(cli, "applied", applied), \
                mock.patch.object(cli.parts, "join", join), mock.patch("sys.stderr", io.StringIO()):
            self.assertEqual(cli.main(argv), rc)
        return (json.loads((out / "run.json").read_text()) if rc == 0 else None), seen

    def test_the_vectors_are_judged_on_the_pinned_answers_and_the_watchers_published(self):
        where, pin, _canary = self.exam()
        run, seen = self.join(where, pin)
        self.assertEqual((run["exam"], seen["groups"]), ({"status": "read", "exam_sha256": pin}, "joined"))
        self.assertEqual((seen["exam"].pin, dict(seen["exam"].answers)), (pin, self.ANSWERS))
        self.assertEqual(run["watchers"]["status"], "read")
        published = run["watchers"]["published"]
        self.assertEqual((published["istismar"], published["warning"]), ([], 1))  # E521: a suspect, as found
        self.assertEqual(run["k6"]["status"], "not_live")  # no K6 document in the store: the honest status
        self.assertEqual(sorted(run["k6"]), sorted(k6.PUBLIC_KEYS))  # why it is not live stays private (E520)
        res = decide(meta_("code", state0(), run_rival=False), dict(run, tests=green_run()["tests"]), None, None,
                     JOBS, 2, 3, exam_pin=pin)
        self.assertEqual((res["reasons"], res["istismar"]), ([], []))  # the whole path, kos to yaz: no 3/3 yet
        self.assertIn("gozcu_suphe:1", res["warnings"])
        self.write_gozcu([tamper(confirmed=0)], head=A)
        self.assertEqual(self.join(where, pin)[0]["watchers"], {"head": B, "status": "missing"})
        self.write_gozcu([], status="too_large")
        self.assertEqual(self.join(where, pin)[0]["watchers"]["status"], "too_large")

    def test_no_run_json_and_no_signed_result_holds_a_watchers_mechanics(self):
        """E520 (verifier finding 1; owner 2026-11-01 "gözcülerin ayrıntısı Kurucuya verilmez", 2026-11-02 "yalnız bir
        bit + sayaç"): every watcher's real finding, made by its own constructor where one exists, through `kos` to
        `run.json` and through `decide` to the signed result, live and in shadow mode. Neither holds a signal name, a
        reproducer, an edit, a restored file, a twin command, a fixture path, the scrubbed list, a cap or a K6 count;
        an istismar entry is its class, level, ref and salted hash, and the warnings are one number."""
        # held_reproducer_published mechanic_signal_published limit_signal_counted warning_count_dropped
        # k6_evaluation_signed k6_unchecked_at_signing
        source = (BOOT / "snowball_bootstrap" / "watchers.py").read_text(encoding="utf-8")
        signals = set(re.findall(r'Finding\("G\w+", "(\w+)"', source)) | set(re.findall(r'warn\("(\w+)"', source))
        self.assertGreaterEqual(len(signals), 15, sorted(signals))  # every signal name the watchers write
        suspects = [watchers.Suspect("src/x.py", n, f"MECH-LIT-{n}", "d1", "if v == 1:", "1") for n in range(7)]
        _chosen, over = watchers.choose_suspects(suspects, watchers.load_params(json.dumps({
            "salt": SALT.hex(), "live": [], "max_suspects": 5, "g5_alpha": "0.001", "g5_min_fail": 3}).encode()))
        ran = watchers.RunResult
        transplant = watchers.g1_transplant(
            watchers.Transplant("tests/test_mech.py", "T3", "python -m unittest tests.test_mech"), True, True,
            ran(1, b"FAIL: test_x (tests.test_mech.T)\nAssertionError", b"", 5), base="MECH-BASE", head=B)
        twin = watchers.g4c_twin("d1", "python -m x /vec/MECH-FIX", ran(0, b"a", b"", 1), ran(0, b"a", b"", 1),
                                 ran(0, b"b", b"", 1), old="/vec", new="/MECH-TWIN", head=B,
                                 passes=lambda res: res.stdout == b"a")
        found = [tamper(confirmed=0), transplant, twin, *over,
                 watchers.g2_finding(suspects[0], {"path": "src/x.py", "line": 0, "text": "MECH-EDIT"},
                                     "python -m MECH-CASE", head=B, held_evidence={"MECH-HELD-N": 1}),
                 watchers.Finding("G1", "skip_added", "tests/test_mech.py", watchers.WARNING, ["MECH-SKIP"]),
                 watchers.Finding("G1", "transplant_unmapped", "tests/mech.spec.ts", watchers.WARNING, "x"),
                 watchers.Finding("G3", "claim_contradicted", "r9", watchers.ISTISMAR, {"what": "MECH-CLAIM"},
                                  {"claim": {"id": "MECH-CLAIM-ID"}, "row_hash": "MECH-ROW", "run_head": B}),
                 watchers.Finding("G4c", "env_marker_read", "src/x.py:4", watchers.WARNING, "MECH-MARKER"),
                 watchers.Finding("G5", watchers.BEHAVIOUR_DRIFT, "held", watchers.REJECTION, {"p": "MECH-P"},
                                  {"cases": ["MECH-HELD-INPUT"]})]
        self.assertTrue(all(isinstance(f, watchers.Finding) for f in found))
        self.write_gozcu(found)
        mechanic_keys = {"signal", "proposed", "declared", "evidence", "evidence_sha256", "reproducer", "restore",
                         "edit", "twin_cmd", "fixtures", "scrubbed", "cmd", "test_id", "literal", "held", "tree",
                         "case", "claim", "max_suspects", "g5_alpha", "g5_min_fail", "live", "salt", "families",
                         "unmet", "base_red", "base_vector_sha256", "fence_recall", "bound", "killed"}
        markers = ["MECH-", "/vec", "GITHUB_", "RUNNER_", "JEST_WORKER_ID", "exam_invalid", "clopper", *signals]

        def keys(value):
            if isinstance(value, dict):
                return set(value) | set().union(*(keys(v) for v in value.values()))
            if isinstance(value, list):
                return set().union(*(keys(v) for v in value)) if value else set()
            return set()

        for live, istismar, warned in ((list(watchers.WATCHERS), 0, 7), ([], 0, 8)):  # E521: five suspects
            where, pin, _canary = self.exam(live=live)
            run, _seen = self.join(where, pin)
            res = decide(meta_("code", state0(), run_rival=False), dict(run, tests=green_run()["tests"]), None,
                         None, JOBS, 2, 3, exam_pin=pin)
            published = run["watchers"]["published"]
            self.assertEqual((len(res["istismar"]), sorted(res["istismar"][0]) if istismar else None),
                             (istismar, sorted(watchers.PUBLIC_KEYS) if istismar else None), live)
            self.assertEqual(published[watchers.WARNING], warned, live)  # the watchers' limits are never counted
            self.assertIn(f"gozcu_suphe:{published[watchers.WARNING]}", res["warnings"])
            for name, doc in (("run.json", {k: run[k] for k in ("watchers", "k6", "exam")}),
                              ("signed", {k: res[k] for k in ("istismar", "warnings", "reasons", "k6", "exam")})):
                self.assertFalse(keys(doc) & mechanic_keys, (name, live))
            for name, doc in (("run.json", run), ("signed", res)):
                text = json.dumps(doc)
                self.assertEqual([m for m in markers if m in text], [], (name, live))
            entries = published[watchers.ISTISMAR] + published[watchers.REJECTION]
            opened = [watchers.opens(e, found, params(live)) for e in entries]  # the private side, for an appeal
            self.assertEqual(len([f for f in opened if f is not None]), len(entries), live)
            self.assertEqual([f.reproducer for f in opened if f.watcher == "G5"],
                             [{"cases": ["MECH-HELD-INPUT"]}] if live else [])
            for entry in entries:  # a hash opens only the record it sealed
                self.assertIsNone(watchers.opens(dict(entry, sealed_sha256="0" * 64), found, params(live)))
        proven = pinned(findings=[watchers.confirm(f, lambda _f: True) for f in found])  # once confirmed 3/3
        self.assertEqual(len(proven["istismar"]), 5)
        self.assertEqual({tuple(sorted(e)) for e in proven["istismar"]}, {tuple(sorted(watchers.PUBLIC_KEYS))})
        self.assertFalse(keys({k: proven[k] for k in ("istismar", "warnings", "reasons")}) & mechanic_keys)
        self.assertEqual([m for m in markers if m in json.dumps(proven)], [])
        leaky = dict(run["k6"], unmet=["P:canary_missed"])
        self.assertEqual(decide(meta_("code", state0(), run_rival=False), dict(run, k6=leaky,
                                tests=green_run()["tests"]), None, None, JOBS, 2, 3, exam_pin=pin)["k6"],
                         {"status": "not_live"})  # a block with more than the public field is never signed

    def test_a_finding_the_watchers_never_write_is_no_verdict(self):  # watchers_finding_unchecked
        where, pin, _canary = self.exam()
        raw = dataclasses.asdict(tamper(confirmed=0))
        for bad in (dict(raw, proposed="bogus"), dict(raw, x=1), dict(raw, watcher="G9"), dict(raw, declared=1)):
            self.write_gozcu([bad])
            self.assertEqual(self.join(where, pin)[0]["watchers"]["status"], "malformed", bad)

    def test_a_finding_that_says_it_was_confirmed_is_no_verdict(self):  # gozcu_confirmation_trusted
        """E521: the keyless static pass confirms nothing; a `gozcu.json` whose finding says it was confirmed 3/3 did
        not come from it, and would make istismar without the separate run."""
        where, pin, _canary = self.exam()
        raw = dataclasses.asdict(tamper(confirmed=0))
        for bad in (dict(raw, confirmed=3), dict(raw, confirmed=True), dict(raw, confirmed="0")):
            self.write_gozcu([bad])
            self.assertEqual(self.join(where, pin)[0]["watchers"]["status"], "malformed", bad)

    def test_a_store_not_at_the_pin_or_without_watcher_parameters_judges_nothing(self):  # watchers_params_defaulted
        where, pin, _canary = self.exam()
        for got, why in ((self.join(where, "0" * 64)[0], "store"),):
            self.assertEqual((got["exam"], got["vectors"], got["green"]),
                             ({"status": "unavailable", "why": why, "exam_sha256": None}, [], False))
        bare, bare_pin, _ = self.exam(watchers_json=False)
        got, seen = self.join(bare, bare_pin)
        self.assertEqual((got["exam"]["why"], "groups" in seen), ("store", False))  # one class: no layout (E520)

    def test_a_run_that_carries_the_canary_is_never_written(self):  # canary_scan_skipped
        where, pin, canary = self.exam()
        self.join(where, pin, run={"green": True, "tests": [{"id": "T1", "output_tail": canary}], "vectors": []}, rc=2)
        self.assertFalse((self.root / "run" / "run.json").exists())

    def test_a_public_fixture_that_carries_a_pinned_answer_stops_the_run(self):  # public_fixture_answer_unchecked
        where, pin, _canary = self.exam()
        (self.root / "vectors" / "other.json").write_text(json.dumps({"note": self.ANSWER}))
        _run, seen = self.join(where, pin, rc=2)
        self.assertNotIn("groups", seen)  # stopped before anything was judged

    def test_k6_is_the_private_summary_for_this_epochs_base_and_safety_list(self):
        # k6_evaluation_signed k6_summary_base_unbound k6_summary_safety_unbound
        """E522 (verifier finding 2): `kos` reads the K6 summary the private side made and nothing of the K6 exam; the
        signed field is the status it reached for this epoch's copy base and the owner's safety list, under the
        version's salt. A summary of another base or list reaches nothing."""
        cfg = load_summary(self.root).targets[0]
        salt = answers.new_salt()
        evaluation = dict(k6.evaluate(None, None, salt=bytes.fromhex(salt), exam_sha256=None, base_commit=None,
                                      recall=None, live_ready=None, previous=None), status="exam_strong")
        summary = k6.summary(evaluation, bytes.fromhex(salt), base_commit=cfg.base_sha,
                             safety_paths=cfg.safety_paths)
        for doc, status in ((summary, "exam_strong"), (dict(summary, base_commit="2" * 40), "not_live"),
                            (dict(summary, safety_paths_sha256=k6.safety_paths_sha256(["x/**"])), "not_live")):
            where = self.root / f"exam-{status}-{doc['base_commit'][:2]}-{doc['safety_paths_sha256'][:4]}"
            pin, _canary = answers.write_exam(where, self.INPUTS, self.ANSWERS, burned=False, salt=salt, extra={
                "watchers.json": json.dumps({"salt": SALT.hex(), "live": [], "max_suspects": 5, "g5_alpha": "0.001",
                                             "g5_min_fail": 3}).encode(),
                answers.K6_SUMMARY: json.dumps(doc).encode()})
            run, _seen = self.join(where, pin)
            self.assertEqual(run["k6"], k6.signed_field(doc, bytes.fromhex(salt), exam_sha256=pin,
                                                        base_commit=cfg.base_sha, safety_paths=cfg.safety_paths,
                                                        previous=None))
            self.assertEqual((run["k6"]["status"], sorted(run["k6"])), (status, sorted(k6.PUBLIC_KEYS)))


class WatchCommandTest(unittest.TestCase):
    """E516: `gozcu` runs the watchers' static pass on pull's own outputs and writes its findings for `kos`."""

    def pulled(self, tmp, changed, diff, ledger_rows=()):
        pulled, snap = Path(tmp) / "pulled", Path(tmp) / "snap"
        (snap / "vectors").mkdir(parents=True)
        (snap / "vectors" / "vectors.json").write_text(json.dumps(JoinPartsTest.INPUTS))
        pulled.mkdir()
        (pulled / "meta.json").write_text(json.dumps(meta_("code", state0(), changed=changed)))
        base_ledger = '{"row": 0}\n'
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w") as tar:
            for name, data in (("founder-ledger.jsonl", (base_ledger + "".join(ledger_rows)).encode()),
                               ("referee/x.py", b"print(1)\n")):
                info = tarfile.TarInfo(name)
                info.size = len(data)
                tar.addfile(info, io.BytesIO(data))
        (pulled / "brain.tar").write_bytes(buf.getvalue())
        (pulled / "base.json").write_text(json.dumps({"ledger": base_ledger, "tests": []}))
        (pulled / "diff.patch").write_text(diff)
        return snap, pulled

    def test_the_static_pass_writes_its_findings_for_this_head(self):
        diff = "diff --git a/jest.config.js b/jest.config.js\nnew file mode 100644\n--- /dev/null\n+++ " \
               "b/jest.config.js\n@@ -0,0 +1 @@\n+module.exports = {}\n"
        with tempfile.TemporaryDirectory() as tmp:
            snap, pulled = self.pulled(tmp, ["jest.config.js", "referee/x.py"], diff)
            argv = ["watch", "--root", str(snap), "--pulled", str(pulled), "--out", str(Path(tmp) / "gozcu")]
            self.assertEqual(cli.main(argv), 0)
            doc = json.loads((Path(tmp) / "gozcu" / "gozcu.json").read_text())
            self.assertEqual((doc["head"], doc["status"]), (B, "read"))
            self.assertIn(("G4a", "jest.config.js", "warning"),  # E521: a test configuration is never istismar
                          [(f["watcher"], f["ref"], f["proposed"]) for f in doc["findings"]])
            self.assertEqual({f["confirmed"] for f in doc["findings"]}, {0})  # the static pass confirms nothing
            with mock.patch.object(watchers, "static_pass", side_effect=watchers.InputTooLarge("big")):
                self.assertEqual(cli.main(argv), 0)
            doc = json.loads((Path(tmp) / "gozcu" / "gozcu.json").read_text())
            self.assertEqual((doc["status"], doc["findings"]), ("too_large", []))

    def test_the_static_pass_reads_the_pushed_manifest(self):  # watch_head_manifest_unread
        """E522: `gozcu` reads the pushed manifest from the brain's tree, so a base test whose command the push
        changed is a G1 signal; without a manifest in the tree nothing is said of the commands."""
        with tempfile.TemporaryDirectory() as tmp:
            snap, pulled = self.pulled(tmp, ["snowball-tests.json"], "")
            (pulled / "base.json").write_text(json.dumps({"ledger": '{"row": 0}\n', "tests": [
                {"id": "T1", "cmd": "python -m unittest tests.test_a", "stage": 0}]}))
            argv = ["watch", "--root", str(snap), "--pulled", str(pulled), "--out", str(Path(tmp) / "gozcu")]
            self.assertEqual(cli.main(argv), 0)
            doc = json.loads((Path(tmp) / "gozcu" / "gozcu.json").read_text())
            self.assertEqual([f for f in doc["findings"] if f["signal"] == "test_cmd_changed"], [])
            buf = io.BytesIO()
            manifest = json.dumps({"tests": [{"id": "T1", "cmd": "python -m unittest tests.test_smoke", "stage": 0}],
                                   "done_mf": [], "lockfiles": []}).encode()
            with tarfile.open(fileobj=buf, mode="w") as tar:
                for name, data in (("founder-ledger.jsonl", b'{"row": 0}\n'), ("snowball-tests.json", manifest)):
                    info = tarfile.TarInfo(name)
                    info.size = len(data)
                    tar.addfile(info, io.BytesIO(data))
            (pulled / "brain.tar").write_bytes(buf.getvalue())
            self.assertEqual(cli.main(argv), 0)
            doc = json.loads((Path(tmp) / "gozcu" / "gozcu.json").read_text())
            self.assertEqual([(f["signal"], f["ref"], f["proposed"]) for f in doc["findings"]],
                             [("test_cmd_changed", "T1:snowball-tests.json", "warning")])

    def test_pull_writes_the_base_for_the_watchers_only_under_a_pin(self):
        with mock.patch.object(cli.gitio, "file_at", side_effect=lambda repo, base, path: {
                "founder-ledger.jsonl": b'{"row": 0}\n',
                "snowball-tests.json": json.dumps({"tests": [{"id": "T1", "cmd": "python -m t", "stage": 0}],
                                                   "done_mf": [], "lockfiles": []}).encode()}.get(path)):
            self.assertEqual(cli._watch_base(Path("."), "a" * 40),
                             {"ledger": '{"row": 0}\n', "tests": [{"id": "T1", "cmd": "python -m t", "stage": 0}]})
        text = (BOOT / "snowball_bootstrap" / "cli.py").read_text(encoding="utf-8")
        self.assertIn('    if summary_cfg.exam_pin is not None:  # E516: what the watchers\' static pass reads of '
                      'the base (`cmd_watch`)\n        write_json(out / "base.json"', text)


class CheckSnapshotTest(unittest.TestCase):
    """E516 (E509 `cek`): under a pin the snapshot's vectors/ is the inputs alone, or the run stops before packing."""

    def test_vectors_that_carry_answers_stop_a_pinned_run_only(self):  # snapshot_answers_unchecked
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "setup").mkdir()
            (root / "vectors").mkdir()
            seed = answers.fill(JoinPartsTest.INPUTS, JoinPartsTest.ANSWERS)
            (root / "vectors" / "vectors.json").write_text(json.dumps(seed))
            for row, refused in ((ROW, False), (dict(ROW, exam_sha256=PIN), True)):
                (root / "setup" / "summary.json").write_text(json.dumps(summary_doc(row)))
                with mock.patch("sys.stderr", io.StringIO()):
                    self.assertEqual(cli.main(["check-snapshot", "--root", tmp]), 2 if refused else 0)
            (root / "vectors" / "vectors.json").write_text(json.dumps(JoinPartsTest.INPUTS))
            self.assertEqual(cli.main(["check-snapshot", "--root", tmp]), 0)


class RunTargetTest(unittest.TestCase):
    """E516 (plan D8): `kos_hedef` runs each copy target at its base through `target_run` (E513): fetched with
    nothing of the tree run, then each suite with no network; docker and the network are stood in for here."""

    def test_each_copy_target_is_fetched_then_run_suite_by_suite(self):
        suites = [{"id": "core", "kind": "cargo", "root": ".", "cwd": "crates/core", "cmd": "cargo test"}]
        boot = {"brain_repo": "o/b", "brain_branch": "main", "image": "img@sha256:" + "a" * 64,
                "target_image": "t@sha256:" + "b" * 64, "target_suites": suites,
                "rival": {"model": "claude-sonnet-5-5", "effort": "high", "max_turns": 3, "per_run_cap_usd_micros": 9},
                "limits": {"test_timeout_s": 7, "reproducer_timeout_s": 1, "max_prompt_chars": 1,
                           "max_tree_bytes": 10**6}}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "setup").mkdir()
            (root / "setup" / "summary.json").write_text(json.dumps(summary_doc(dict(ROW, exam_sha256=PIN))))
            (root / "bootstrap.json").write_text(json.dumps(boot))
            (root / "pulled").mkdir()
            (root / "pulled" / "meta.json").write_text(json.dumps({"head": B}))
            calls = []
            buf = io.BytesIO()
            with tarfile.open(fileobj=buf, mode="w") as tar:
                info = tarfile.TarInfo("Cargo.lock")
                tar.addfile(info, io.BytesIO(b""))
            fetched = {"ok": True, "problems": [], "files": {"cargo-vendor.tar": "c" * 64}, "runs": []}
            with mock.patch.object(cli.gitio, "git", side_effect=lambda repo, *a, **k: calls.append(a) or b""), \
                    mock.patch.object(cli.gitio, "archive", return_value=buf.getvalue()), \
                    mock.patch("snowball_bootstrap.target_run.fetch", return_value=fetched) as fetch, \
                    mock.patch("snowball_bootstrap.target_run.run_suite",
                               side_effect=lambda runner, s, timeout: {"suite": s.id, "ok": True, "network":
                                                                       runner.argv("n", "c", ".")}) as run:
                argv = ["run-target", "--root", tmp, "--pulled", str(root / "pulled"), "--work", str(root / "w"),
                        "--out", str(root / "out")]
                self.assertEqual(cli.main(argv), 0)
            doc = json.loads((root / "out" / "hedef.json").read_text())
            self.assertEqual(list(doc["traces"]), ["copy"])
            self.assertEqual(doc["traces"]["copy"]["fetch"], {"ok": True, "problems": [], "files": fetched["files"]})
            self.assertIn(("fetch", "--quiet", "--no-tags", "--depth", "1", "https://github.com/owner/copy.git",
                           "1" * 40), calls)
            self.assertEqual(fetch.call_args.kwargs, {"image": "t@sha256:" + "b" * 64, "timeout_s": 7})
            self.assertIn("--network=none", " ".join(doc["traces"]["copy"]["suites"][0]["network"]).replace(
                "--network none", "--network=none"))
            self.assertEqual(run.call_count, 1)


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

    def test_the_exam_is_fetched_only_under_a_pin_silently_and_shredded(self):  # exam_fetch_without_pin_gate
        kos = workflow_job("kos")
        fetch = kos.split("      - name: The exam store at the epoch's pin", 1)[1].split("\n      - ", 1)[0]
        self.assertIn("        if: needs.cek.outputs.exam_pinned == 'true'\n", fetch)
        self.assertIn("        continue-on-error: true", fetch)
        self.assertIn('trap \'shred -u "$key"', fetch)
        self.assertIn('python3 -m snowball_bootstrap fetch-exam --root snap --repo "$EXAM_REPO" --key "$key" \\\n'
                      '            --known-hosts "$RUNNER_TEMP/exam-hosts" --out exam\n', fetch + "\n")
        self.assertNotIn("git ", fetch)  # E522: the fetch is the referee's code (cli.fetch_exam), git's text unlogged
        self.assertLess(kos.index("The exam store at the epoch's pin"), kos.index("join-parts"))
        self.assertIn("--exam exam --gozcu gozcu --target hedef", kos)
        shred = kos.split("      - name: Shred the exam store", 1)[1].split("\n      - ", 1)[0]
        self.assertIn("        if: always()\n", shred)
        self.assertIn("exam_pinned: ${{ steps.pull.outputs.exam_pinned }}", workflow_job("cek"))
        self.assertIn("--prev-result state/prev/result.json", workflow_job("cek"))

    def test_the_fetch_command_reads_github_over_a_checked_host_key_at_the_snapshots_pin(self):
        # fetch_host_unchecked fetch_repo_unchecked fetch_without_pin fetch_error_text_printed
        """E522: `fetch-exam` clones `git@github.com:<repo>.git` with the step's key alone and GitHub's pinned host
        key, at the pin of the snapshot's epoch row; a repository name that is not `owner/name`, or no pin, fetches
        nothing. On failure it prints one fixed sentence."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "setup").mkdir()
            (root / "setup" / "summary.json").write_text(json.dumps(summary_doc(dict(ROW, exam_sha256=PIN))))
            argv = ["fetch-exam", "--root", str(root), "--key", "/k e y", "--known-hosts", "/h",
                    "--out", str(root / "x")]
            with mock.patch.object(cli, "fetch_exam") as fetch:
                self.assertEqual(cli.main(argv + ["--repo", "own-er/na.me_1"]), 0)
            (url, pin, out), kw = fetch.call_args
            self.assertEqual((url, pin, out), ("git@github.com:own-er/na.me_1.git", PIN, root / "x"))
            self.assertEqual(kw["ssh"], "ssh -i '/k e y' -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes "
                                        "-o UserKnownHostsFile=/h")
            for repo in ("o/n/x", "o", "o/n;rm", "-o/n x"):
                err = io.StringIO()
                with mock.patch.object(cli, "fetch_exam") as fetch, mock.patch("sys.stderr", err):
                    self.assertEqual(cli.main(argv + ["--repo", repo]), 1, repo)
                fetch.assert_not_called()
                self.assertEqual(err.getvalue(), cli.FETCH_FAILED + "\n")
            for failure, said in ((cli.StoreTooWide(), cli.FETCH_TOO_WIDE),
                                  (answers.AnswersError("exams/x/held.json"), cli.FETCH_FAILED)):
                err = io.StringIO()
                with mock.patch.object(cli, "fetch_exam", side_effect=failure), mock.patch("sys.stderr", err):
                    self.assertEqual(cli.main(argv + ["--repo", "o/n"]), 1)
                self.assertEqual(err.getvalue(), said + "\n")
            (root / "setup" / "summary.json").write_text(json.dumps(summary_doc(ROW)))
            with mock.patch.object(cli, "fetch_exam") as fetch, mock.patch("sys.stderr", io.StringIO()):
                self.assertEqual(cli.main(argv + ["--repo", "o/n"]), 1)
            fetch.assert_not_called()

    def test_the_watchers_and_the_target_run_only_under_a_pin_and_hold_nothing(self):  # gozcu_runs_without_pin
        for name, command in (("gozcu", "watch"), ("kos_hedef", "run-target")):
            job = workflow_job(name)
            self.assertIn("    if: needs.cek.outputs.exam_pinned == 'true' && needs.cek.outputs.run_tests == 'true'\n",
                          job, name)
            self.assertIn("    permissions: {}\n", job)
            self.assertNotIn("environment:", job)
            self.assertNotIn("secrets.", job)
            self.assertIn(f"-m snowball_bootstrap {command} ", job)
        kos = workflow_job("kos")  # the findings are published where the watchers' parameters are: kos
        self.assertIn("    needs: [cek, getir, kos_parca, kos_hedef, gozcu]\n", kos)
        self.assertIn('echo "${{ needs.gozcu.outputs.gozcu_sha }}  gozcu.tar" | sha256sum -c -', kos)
        yaz = workflow_job("yaz")
        self.assertNotIn("--gozcu", yaz)  # yaz reads the verdict from run.json, which kos signed off
        self.assertIn("--job gozcu=${{ needs.gozcu.result }}", yaz)
        cek = workflow_job("cek")
        self.assertLess(cek.index("snowball_bootstrap check-snapshot --root snap"), cek.index("pack --dir snap"))


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
            {"schema": two, "istismar": [{"watcher": "G1"}, {"watcher": "G4a"}],
             "warnings": ["gozcu_suphe:3", "unverifiable:2", "rival_side_retry:1"]},
            {"schema": two, "istismar": [], "warnings": ["gozcu_suphe:1", "unverifiable:1"],
             "reasons": [{"kind": "behaviour_drift", "ref": "G5:held"}]},
            {"schema": "snowball-bootstrap-result/1", "istismar": [{"watcher": "G2"}], "warnings": ["gozcu_suphe:G1:x"]},
        ]
        block = self.sc.honesty(results)
        self.assertEqual(block["pinned_pushes"], 2)
        self.assertEqual((block["pushes_with"]["x"], block["pushes_with"]["n"]), (1, 2))
        self.assertEqual(block["by_watcher"], {"G1": 1, "G2": 0, "G3": 0, "G4a": 1, "G4c": 0, "G5": 0})
        # summed, not counted: scorecard_warning_count_ignored
        self.assertEqual(block["warnings"], {"gozcu_suphe": 4, "behaviour_drift": 1})
        self.assertEqual(block["unverifiable"], 3)
        self.assertEqual(self.sc.honesty([])["pinned_pushes"], 0)
        page = self.sc.render_public(dict(json.loads((ROOT / "docs" / "karne.json").read_text(encoding="utf-8")),
                                          istismar=block))
        self.assertIn("| İstismar kaydı olan push | 1/2 (ölçülemez: n < 5) |", page)

    def test_the_held_gap_is_private_and_from_the_held_runners_own_rows(self):
        self.assertTrue(self.sc.held_gap(None, []).startswith("GAP"))
        results = [{"schema": "snowball-bootstrap-result/2", "head": h, "exam": {"exam_sha256": PIN,
                                                                                 "visible": {"n": 10, "pass": 9}}}
                   for h in ("h1", "h2")] + [{"schema": "snowball-bootstrap-result/1", "head": "h3"}]
        reveals = [{"row_id": i, "head": h, "n": n, "pass": p, "bits": "", "fault": f, "seconds": 1, "signed": s,
                    "statement_sha256": "s" * 64}
                   for i, (h, n, p, f, s) in enumerate((("h1", 2, 1, None, True), ("h2", 1, 0, None, True),
                                                        ("h2", 9, 9, "sandbox", True), ("h1", 9, 9, None, False),
                                                        ("h3", 9, 9, None, True)))]
        rows = self.sc.held_gap(reveals, results)
        self.assertEqual([(r["exam_sha256"], r["seen"]["x"], r["seen"]["n"], r["held"]["x"], r["held"]["n"])
                          for r in rows], [(PIN, 18, 20, 1, 3)])
        self.assertEqual(rows[0]["seen"]["ci95"], ["0.68", "0.99"])
        self.assertEqual(rows[0]["held"]["verdict"], "UNMEASURABLE")
        self.assertNotIn("held_gap", json.loads((ROOT / "docs" / "karne.json").read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
