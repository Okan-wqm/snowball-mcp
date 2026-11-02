"""The Founder's capsule and launcher (`seed/founder`, register E90, E91, E112): the isolation the pilot relies on
is pinned here, so a later edit that loosens it fails a test instead of passing unnoticed."""

from __future__ import annotations

import argparse
import base64
import contextlib
import dataclasses
import hashlib
import http.server
import importlib.util
import io
import ipaddress
import json
import os
import re
import socket
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from snowball_bootstrap import rival, vectors

from helpers import (commit, definition, ledger_bytes, ledger_rows, load_brain_defs, make_repo, quiet_pilot, sh,
                     tree_repo)

FOUNDER = Path(__file__).resolve().parents[2] / "founder"
VECTORS = Path(__file__).resolve().parents[1] / "vectors"


def load_launch():
    spec = importlib.util.spec_from_file_location("founder_launch", FOUNDER / "launch.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CapsuleArgvTest(unittest.TestCase):
    def setUp(self):
        self.launch = load_launch()
        self.work = Path(tempfile.mkdtemp())
        pilot = self.launch.Pilot(self.work, "owner/brain", "owner/referee", "target")
        pilot.seed = "a" * 40
        self.argv = pilot.capsule_argv("20261029T000000Z", "claude-opus-5-5", 200, 50)
        self.joined = " ".join(self.argv)

    def mounts(self) -> dict[str, str]:
        out = {}
        for i, arg in enumerate(self.argv):
            if arg == "--mount":
                spec = dict(part.split("=", 1) if "=" in part else (part, "") for part in self.argv[i + 1].split(","))
                out[spec["dst"]] = "readonly" if "readonly" in spec else "rw"
        return out

    def test_the_capsule_is_locked_down(self):
        for flag in ("--read-only", "--rm"):
            self.assertIn(flag, self.argv)
        self.assertEqual(self.argv[self.argv.index("--cap-drop") + 1], "ALL")
        self.assertEqual(self.argv[self.argv.index("--security-opt") + 1], "no-new-privileges")
        for flag in ("--privileged", "--cap-add", "--pid", "--userns", "--ipc", "--device", "-v", "--volume",
                     "--network", "--net"):  # the default bridge only: never the host's network or namespaces
            self.assertFalse(any(a == flag or a.startswith(flag + "=") for a in self.argv), flag)
        self.assertNotIn("docker.sock", self.joined)
        self.assertEqual(self.argv[-1], self.launch.IMAGE)

    def test_secrets_referee_result_and_target_are_read_only_and_the_brain_lives_in_memory(self):
        self.assertEqual(self.mounts(), {"/run/secrets/founder.env": "readonly", "/work/referee": "readonly",
                                         "/work/target": "readonly", "/work/logs": "rw", "/vec": "readonly"})
        self.assertIn("/work/brain:rw,exec,size=2g,mode=1777", self.argv)  # a fresh clone every session, never on disk
        for i, arg in enumerate(self.argv):
            if arg == "-e":
                self.assertNotRegex(self.argv[i + 1], r"TOKEN|KEY|SECRET", "a secret passed as an environment flag")

    def test_a_session_sees_only_its_own_transcript_folder_and_gets_the_seed(self):  # E155, E154
        logs = [self.argv[i + 1] for i, a in enumerate(self.argv) if a == "--mount" and "dst=/work/logs" in self.argv[i + 1]]
        self.assertEqual(len(logs), 1)
        src = Path(re.search(r"src=([^,]+)", logs[0]).group(1))
        self.assertEqual(src, self.work / "logs" / "20261029T000000Z" / "capsule")  # E508: not the record's folder
        self.assertIn("BRAIN_SEED=" + "a" * 40, self.argv)

    def test_the_vector_inputs_are_mounted_read_only_where_the_commands_read_them(self):  # E244
        vec = [self.argv[i + 1] for i, a in enumerate(self.argv)
               if a == "--mount" and "dst=/vec," in self.argv[i + 1] + ","]
        self.assertEqual(len(vec), 1)
        self.assertEqual(self.mounts()["/vec"], "readonly")  # the Founder reads the inputs, never rewrites them
        self.assertEqual(Path(re.search(r"src=([^,]+)", vec[0]).group(1)), self.work / "vec")

    def test_every_mount_stays_inside_the_one_work_folder(self):
        for i, arg in enumerate(self.argv):
            if arg == "--mount":
                src = re.search(r"src=([^,]+)", self.argv[i + 1]).group(1)
                self.assertTrue(Path(src).is_relative_to(self.work), src)


class ResultShadowTest(unittest.TestCase):  # E344: a noop on the launcher's own commit never hides the Founder's verdict
    def setUp(self):
        self.launch = load_launch()
        self.work = Path(tempfile.mkdtemp())
        self.pilot = self.launch.Pilot(self.work, "o/brain", "o/referee", "target")
        self.pilot.result_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def zipped(result: dict) -> bytes:
        import zipfile
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("result.json", json.dumps(result))
        return buf.getvalue()

    def mounted(self, newest: dict, older: dict, committers: list[tuple[str, str]], status: str = "ahead"):
        listing = {"artifacts": [
            {"id": 2, "expired": False, "created_at": "2026-11-01T02:00:00Z", "workflow_run": {"head_branch": "main"}},
            {"id": 1, "expired": False, "created_at": "2026-11-01T01:00:00Z", "workflow_run": {"head_branch": "main"}}]}
        compare = {"status": status, "commits": [{"commit": {"committer": {"name": n, "email": e}}} for n, e in committers]}
        zips = {"2": self.zipped(newest), "1": self.zipped(older)}

        def gh_json(*args):
            return listing if "artifacts?" in args[1] else compare

        def gh_read(*args, timeout=120):
            return zips[args[1].split("/")[-2]]

        with mock.patch.object(self.launch, "gh_json", side_effect=gh_json), \
                mock.patch.object(self.launch, "gh_read", side_effect=gh_read):
            got = self.pilot.fetch_result()
        on_disk = json.loads((self.pilot.result_dir / "result.json").read_text(encoding="utf-8"))
        self.assertEqual(got, on_disk)
        return got

    def test_a_noop_on_the_launchers_cost_commit_mounts_the_founders_verdict(self):
        launcher = (self.launch.LAUNCHER_NAME, self.launch.LAUNCHER_EMAIL)
        got = self.mounted({"head": "c" * 40, "kind": "none", "verdict": "noop"},
                           {"head": "f" * 40, "kind": "code", "verdict": "accepted"}, [launcher])
        self.assertEqual(got["head"], "f" * 40)

    def test_a_noop_over_any_other_commit_is_mounted_as_it_is(self):
        launcher = (self.launch.LAUNCHER_NAME, self.launch.LAUNCHER_EMAIL)
        for committers in ([launcher, ("Founder", "founder@example.invalid")],
                           [(self.launch.LAUNCHER_NAME, "someone@example.invalid")],
                           [("Founder", self.launch.LAUNCHER_EMAIL)], []):
            got = self.mounted({"head": "c" * 40, "kind": "none", "verdict": "noop"},
                               {"head": "f" * 40, "kind": "code", "verdict": "accepted"}, committers)
            self.assertEqual(got["head"], "c" * 40, committers)
        got = self.mounted({"head": "c" * 40, "kind": "none", "verdict": "noop"},
                           {"head": "f" * 40, "kind": "code", "verdict": "accepted"}, [launcher], status="diverged")
        self.assertEqual(got["head"], "c" * 40)

    def test_a_real_verdict_is_mounted_as_it_is(self):
        launcher = (self.launch.LAUNCHER_NAME, self.launch.LAUNCHER_EMAIL)
        for kind in ("code", "spec", "seed_update", "exit"):
            got = self.mounted({"head": "c" * 40, "kind": kind, "verdict": "accepted"},
                               {"head": "f" * 40, "kind": "code", "verdict": "accepted"}, [launcher])
            self.assertEqual(got["head"], "c" * 40, kind)

    def test_broken_record_lines_never_stop_the_launcher(self):
        self.pilot.metrics.write_text('{"stamp": "s1", "session_exit": 0, "minutes": 3, "pushed": true}\n\n{"stamp": "s2"',
                                      encoding="utf-8")
        self.pilot.previous_session_note("20261101T000000Z", 10800)
        note = json.loads((self.work / "logs" / "20261101T000000Z" / "capsule" / "previous-session.json")
                          .read_text(encoding="utf-8"))
        self.assertEqual(note["stamp"], "s1")


class PreviousSessionTest(unittest.TestCase):  # E360: how the last session ended is an observation, never its transcript
    def setUp(self):
        self.launch = load_launch()
        self.work = Path(tempfile.mkdtemp())
        self.pilot = self.launch.Pilot(self.work, "owner/brain", "owner/referee", "target")
        self.pilot.verdict_on = lambda head: None  # the look-up has its own tests below; no test here reaches GitHub

    def note(self, stamp="20261031T210000Z"):
        path = self.work / "logs" / stamp / "capsule" / "previous-session.json"  # the capsule's /work/logs (E508)
        return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None

    def test_a_seed_epoch_between_does_not_hide_the_heads_verdict(self):  # E420: the live 20261101T045525Z case
        head, epoch = "b" * 40, "d" * 40
        row = {"stamp": "20261101T012022Z", "brain_before": "a" * 40, "brain_after": head, "pushed": True,
               "session_exit": 0, "minutes": 51.9, "ledger_new": {"decision": 4}, "verdict": None,
               "session_timeout_s": 10800}
        self.pilot.metrics.write_text(json.dumps(row) + "\n", encoding="utf-8")
        noop = {"head": epoch, "kind": "seed_update", "verdict": "noop", "state": {"last_evaluated_sha": epoch}}
        on_head = {"head": head, "kind": "code", "verdict": "accepted", "state": {"last_evaluated_sha": head}}
        self.pilot.verdict_on = lambda h: on_head if h == head else None
        self.pilot.previous_session_note("20261101T045525Z", 10800, noop)
        self.assertEqual(self.note("20261101T045525Z")["verdict"], "accepted")
        self.pilot.verdict_on = lambda h: None  # not among the recent results: unknown, never another head's
        self.pilot.previous_session_note("20261101T045525Z", 10800, noop)
        self.assertIsNone(self.note("20261101T045525Z")["verdict"])

    def test_the_look_up_finds_the_newest_result_that_evaluated_the_head(self):  # E420
        pilot = self.launch.Pilot(self.work, "owner/brain", "owner/referee", "target")
        head = "b" * 40
        results = [{"head": "d" * 40, "verdict": "noop", "state": {"last_evaluated_sha": "d" * 40}},
                   {"head": head, "verdict": "accepted", "state": {"last_evaluated_sha": None}},  # did not evaluate it
                   {"head": head, "verdict": "rejected", "state": {"last_evaluated_sha": head}},
                   {"head": head, "verdict": "accepted", "state": {"last_evaluated_sha": head}}]
        pilot.state_artifacts = lambda: [{"id": i} for i in range(len(results))]
        pilot.artifact_files = lambda art: {"result.json": json.dumps(results[art["id"]]).encode()}
        self.assertEqual(pilot.verdict_on(head)["verdict"], "rejected")
        self.assertIsNone(pilot.verdict_on("e" * 40))
        pilot.state_artifacts = lambda: [{"id": 0}] * self.launch.VERDICT_LOOKBACK + [{"id": 3}]
        self.assertIsNone(pilot.verdict_on(head))  # bounded: an old head is not searched for without end

        def down():
            raise self.launch.GitHubUnavailable("down")
        pilot.state_artifacts = down
        self.assertIsNone(pilot.verdict_on(head))

    def test_a_timed_out_session_is_named_for_the_next_one(self):
        rows = [{"stamp": "20261031T170731Z", "session_exit": 0, "minutes": 18.5, "pushed": True,
                 "ledger_new": {"decision": 3, "build": 1}, "verdict": "accepted", "session_timeout_s": 10800},
                {"stamp": "20261031T174316Z", "session_exit": -1, "minutes": 180.2, "pushed": False,
                 "ledger_new": {}, "verdict": None, "session_timeout_s": 10800}]
        self.pilot.metrics.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
        self.pilot.previous_session_note("20261031T210000Z", 10800)
        self.assertEqual(self.note(), {"stamp": "20261031T174316Z", "ended": "timeout", "exit": -1, "minutes": 180.2,
                                       "limit_minutes": 180.0, "pushed": False, "ledger_rows_added": 0, "verdict": None})

    def test_a_normal_end_and_the_limit_it_ran_under(self):
        row = {"stamp": "20261031T170731Z", "session_exit": 0, "minutes": 18.5, "pushed": True,
               "ledger_new": {"decision": 3, "build": 1}, "verdict": "accepted", "session_timeout_s": 7200}
        self.pilot.metrics.write_text(json.dumps(row) + "\n", encoding="utf-8")
        self.pilot.previous_session_note("20261031T210000Z", 10800)
        note = self.note()
        self.assertEqual((note["ended"], note["limit_minutes"], note["ledger_rows_added"], note["pushed"]),
                         ("exit", 120.0, 4, True))

    def test_the_restart_after_a_timeout_still_names_the_timeout(self):
        """A timed-out session stops the launcher, and every start appends its intervention row before cycle 1 (E313):
        the note reads the last cycle's row, never that start row (E360)."""
        row = {"stamp": "20261031T174316Z", "session_exit": -1, "minutes": 180.2, "pushed": False,
               "ledger_new": {}, "verdict": None, "session_timeout_s": 10800}
        self.pilot.metrics.write_text(json.dumps(row) + "\n", encoding="utf-8")
        args = argparse.Namespace(work=self.work, cycles=1, no_build=True)
        with mock.patch.object(self.pilot, "image_prompt", return_value="p" * 64), \
                mock.patch.object(self.pilot, "image", return_value=None), mock.patch.object(self.launch, "say"):
            self.pilot.intervention(args)
            self.pilot.intervention(args)  # two starts in a row (a preflight failure, then a start that ran)
        self.pilot.previous_session_note("20261031T210000Z", 10800)
        self.assertEqual(self.note(), {"stamp": "20261031T174316Z", "ended": "timeout", "exit": -1, "minutes": 180.2,
                                       "limit_minutes": 180.0, "pushed": False, "ledger_rows_added": 0, "verdict": None})

    def test_no_earlier_cycle_writes_nothing(self):
        self.pilot.previous_session_note("20261031T210000Z", 10800)
        self.assertIsNone(self.note())
        self.pilot.record_metrics({"kind": "intervention", "ts": "2026-10-31T21:01:35Z", "args": {}})
        self.pilot.previous_session_note("20261031T210000Z", 10800)  # a first start's own row is not a session
        self.assertIsNone(self.note())

    def test_a_verdict_caught_up_after_the_cycle_is_the_one_named(self):  # E381: the live 20261031T223452Z case
        head, other = "b" * 40, "c" * 40
        row = {"stamp": "20261031T215701Z", "brain_before": "a" * 40, "brain_after": head, "pushed": True,
               "session_exit": 0, "minutes": 37.0, "ledger_new": {"decision": 4}, "verdict": None,
               "session_timeout_s": 10800}
        self.pilot.metrics.write_text(json.dumps(row) + "\n", encoding="utf-8")

        def signed(on, evaluated=True, verdict="accepted"):
            return {"head": on, "verdict": verdict, "state": {"last_evaluated_sha": on if evaluated else None}}

        for prior, expected in ((signed(head), "accepted"), (signed(head, verdict="rejected"), "rejected"),
                                (signed(other), None),  # another head's verdict is never lent (E241)
                                (signed(head, evaluated=False), None),  # a run that did not evaluate it
                                (None, None)):
            self.pilot.previous_session_note("20261031T210000Z", 10800, prior)
            self.assertEqual(self.note()["verdict"], expected, prior)
        self.pilot.metrics.write_text(json.dumps(dict(row, brain_after="a" * 40, pushed=False)) + "\n",
                                      encoding="utf-8")
        self.pilot.previous_session_note("20261031T210000Z", 10800, signed("a" * 40))
        self.assertIsNone(self.note()["verdict"])  # no push: the verdict on its head is an earlier session's
        self.assertEqual(self.pilot.metrics.read_text(encoding="utf-8").count("\n"), 1)  # the row is never rewritten

    def test_the_cycle_hands_the_caught_up_verdict_to_the_note(self):  # E381
        launch = load_launch()
        head = "b" * 40
        notes = []

        class Fake(quiet_pilot(launch)):  # the cycle's reads after the session never reach GitHub
            dispatched = False

            def fetch_result(self):  # the newest result is an older head's until the catch-up run
                on = head if self.dispatched else "a" * 40
                return {"head": on, "verdict": "accepted", "state": {"last_evaluated_sha": on}}

            def dispatch_referee(self, timeout_s):
                self.dispatched = True
                return {"id": "1", "conclusion": "success", "url": "u"}

            def brain_head(self):
                return head

            def ledger_rows(self, sha):
                return []

            def refresh_inputs(self):
                pass

            def previous_session_note(self, stamp, timeout_s, prior=None):
                notes.append(prior)

            def session(self, *a):
                return {"exit": 0, "minutes": 1}

            def write(self, text):
                pass

        pilot = Fake(self.work, "o/brain", "o/referee", "target")
        pilot.idle, pilot.seed = 0, "s" * 40
        args = type("Args", (), dict(model="m", max_turns=1, budget_usd=1, session_timeout=1, referee_timeout=1))
        with mock.patch.object(launch, "say"):
            pilot.cycle(1, args)
        self.assertEqual([(n or {}).get("head") for n in notes], [head])

    def test_the_prompt_says_where_it_is(self):
        self.assertIn("/work/logs/previous-session.json", (FOUNDER / "prompt.md").read_text(encoding="utf-8"))


class BuildContextTest(unittest.TestCase):
    def test_a_windows_checkout_reaches_the_image_with_lf_and_nothing_else(self):  # E152
        launch = load_launch()
        seed = Path(tempfile.mkdtemp())
        for rel in launch.BUILD_FILES:
            (seed / rel).parent.mkdir(parents=True, exist_ok=True)
            (seed / rel).write_bytes(b"#!/bin/sh\r\nset -eu\r\n" if rel.endswith(".sh") else b"line\r\nline\r\n")
        (seed / "founder" / "secret-notes.txt").write_bytes(b"not for the image\n")
        launch.SEED = seed
        ctx = Path(tempfile.mkdtemp())
        launch.write_build_context(ctx)
        files = sorted(p.relative_to(ctx).as_posix() for p in ctx.rglob("*") if p.is_file())
        self.assertEqual(files, sorted(launch.BUILD_FILES))
        for rel in files:
            self.assertNotIn(b"\r", (ctx / rel).read_bytes(), rel)
        self.assertEqual((ctx / "founder/entrypoint.sh").read_bytes(), b"#!/bin/sh\nset -eu\n")


def tarball(files: dict[str, bytes]) -> bytes:
    """A repository tarball as GitHub serves it: every path under one `<owner>-<repo>-<sha>/` folder."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name, data in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def files_under(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


class VectorInputsTest(unittest.TestCase):
    """E244, Founder report f97: the capsule holds the vectors' inputs at `/vec` (each case's command, stdin and
    fixtures, as the referee runs them) and never their expected values: inputs yes, answers never."""

    SEED = json.loads((VECTORS / "vectors.json").read_text(encoding="utf-8"))
    DATA = [case for group in SEED.values() if isinstance(group, dict) and group.get("runner") == vectors.DATA_RUNNER
            for case in group["cases"]]
    TOP = "o-referee-1a2b3c4/"

    def test_the_inputs_are_every_data_case_with_no_expected_value_at_any_depth(self):
        def keys(value):
            if isinstance(value, dict):
                return set(value) | {k for v in value.values() for k in keys(v)}
            return {k for v in value for k in keys(v)} if isinstance(value, list) else set()

        with tempfile.TemporaryDirectory() as tmp:
            vec = vectors.founder_inputs(VECTORS, Path(tmp) / "vec")  # the real seed: no fixture carries an answer
            given = files_under(vec)
            referee = files_under(vectors.fixtures(VECTORS, Path(tmp) / "referee"))
        cases = json.loads(given.pop("cases.json").decode("utf-8"))
        self.assertEqual(given, referee)  # the files the referee's containers read, nothing more
        self.assertNotIn("vectors.json", given)
        self.assertEqual(len(cases), len(self.DATA))
        self.assertFalse(keys(cases) & {"expect", "expect_not"})
        for got, case in zip(cases, self.DATA):
            changed = case["changed"]
            self.assertEqual(got, {"id": case["id"], "purpose": case["purpose"], "cmd": case["cmd"],
                                   "stdin": case.get("stdin", ""), "fixture": case["fixture"],
                                   "changed": {"description": changed["description"], "cmd": changed["cmd"],
                                               "stdin": changed.get("stdin", ""), "fixture": changed["fixture"]}})

    @staticmethod
    def probe_seed(root: Path, files: dict[str, str]) -> Path:
        answer = "ab" * 32  # what the command must compute from its input
        case = {"id": "probe.one", "purpose": "a made-up case", "cmd": "python -m probe.x root /vec/probe/a.txt",
                "fixture": ["probe/a.txt"], "expect": {"root": answer},
                "changed": {"description": "another row", "cmd": "python -m probe.x root /vec/probe/b.txt",
                            "fixture": ["probe/b.txt"], "expect_not": {"root": answer}}}
        (root / "probe").mkdir(parents=True)
        (root / "vectors.json").write_text(json.dumps({"probe": {"owner": "asama-0", "runner": "data",
                                                                 "cases": [case]}}), encoding="utf-8")
        for rel, text in {"probe/a.txt": "row 1\n", "probe/b.txt": "row 2\n", **files}.items():
            (root / rel).write_text(text.replace("ANSWER", answer), encoding="utf-8")
        return root

    def test_a_fixture_that_carries_a_computed_answer_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            echo = self.probe_seed(Path(tmp, "echo"), {"probe/a.txt": "row 1 ANSWER\n"})  # its own input: an echo
            self.assertTrue((vectors.founder_inputs(echo, Path(tmp, "vec")) / "cases.json").is_file())
            lookup = self.probe_seed(Path(tmp, "lookup"), {"probe/answers.json": '{"probe.one": "ANSWER"}'})
            with self.assertRaisesRegex(ValueError, r"probe\.one: probe/answers\.json"):
                vectors.founder_inputs(lookup, Path(tmp, "vec2"))
            self.assertFalse(Path(tmp, "vec2").exists())  # refused before anything reaches the capsule's folder

    def test_the_launcher_builds_them_with_the_referees_own_function(self):  # one source: no copy of the rule
        self.assertIs(load_launch().founder_inputs, vectors.founder_inputs)

    def test_only_the_referee_repos_vectors_are_unpacked(self):
        launch = load_launch()
        blob = tarball({self.TOP + "bootstrap/snowball_bootstrap/decide.py": b"the referee's code",
                        self.TOP + "bootstrap/vectors/old.json": b"{}", self.TOP + "setup/summary.json": b"{}",
                        self.TOP + "vectors/vectors.json": b"{}", self.TOP + "vectors/g/a.txt": b"input"})
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(launch.referee_vectors(blob, Path(tmp)), Path(tmp, self.TOP, "vectors"))
            self.assertEqual(sorted(files_under(Path(tmp))), [self.TOP + "vectors/g/a.txt",
                                                              self.TOP + "vectors/vectors.json"])
            with self.assertRaises(tarfile.FilterError):  # filter="data": nothing lands outside the folder
                launch.referee_vectors(tarball({self.TOP + "vectors/../../../out.txt": b"x"}), Path(tmp, "x"))
            self.assertFalse(Path(tmp, "out.txt").exists())

    def test_the_inputs_are_rebuilt_from_the_referee_repos_main(self):
        launch = load_launch()
        repo = {self.TOP + "vectors/" + rel: data for rel, data in files_under(VECTORS).items()}
        repo[self.TOP + "bootstrap/snowball_bootstrap/decide.py"] = b"the referee's code"
        calls = []

        def gh(*args, **kw):
            calls.append(args)
            return subprocess.CompletedProcess(args, 0, tarball(repo), b"")

        work = Path(tempfile.mkdtemp())
        (work / "vec").mkdir()
        (work / "vec" / "stale.json").write_text("{}")  # an earlier session's copy
        with mock.patch.object(launch, "run", gh):
            launch.Pilot(work, "o/brain", "o/referee", "target").refresh_inputs()
        self.assertEqual(calls, [("gh", "api", "repos/o/referee/tarball/main")])
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(files_under(work / "vec"), files_under(vectors.founder_inputs(VECTORS, Path(tmp))))

    def run_cycle(self, gh):
        launch = load_launch()
        head, calls, report = "a" * 40, [], []

        class Fake(quiet_pilot(launch)):
            def fetch_result(self):
                return {"head": head, "verdict": "accepted", "state": {"last_evaluated_sha": head}}

            def brain_head(self):
                return head

            def ledger_rows(self, sha):
                return []

            def refresh_inputs(self):
                calls.append("refresh")
                super().refresh_inputs()

            def session(self, *a):
                calls.append("session")
                return {"exit": 0, "minutes": 1}

            def write(self, text):
                report.append(text)

        pilot = Fake(Path(tempfile.mkdtemp()), "o/brain", "o/referee", "target")
        pilot.idle, pilot.seed = 0, "s" * 40
        args = type("Args", (), dict(model="m", max_turns=1, budget_usd=1, session_timeout=1, referee_timeout=1))
        with mock.patch.object(launch, "say"), mock.patch.object(launch, "run", gh), \
                mock.patch.object(launch.time, "sleep"):
            try:
                go_on = pilot.cycle(1, args)
            except launch.GitHubUnavailable:
                go_on = "outage"  # run_cycles waits it out (E245)
        return calls, go_on, "".join(report), pilot.work / "vec"

    def test_the_inputs_are_rebuilt_before_each_session_and_a_failed_fetch_stops_the_cycle(self):
        seed = tarball({self.TOP + "vectors/vectors.json": b'{"schema": "x"}'})
        calls, go_on, _, vec = self.run_cycle(lambda *a, **kw: subprocess.CompletedProcess(a, 0, seed, b""))
        self.assertEqual((calls, go_on), (["refresh", "session"], True))
        self.assertEqual(json.loads((vec / "cases.json").read_text(encoding="utf-8")), [])
        calls, go_on, report, vec = self.run_cycle(lambda *a, **kw: subprocess.CompletedProcess(a, 1, b"", b"HTTP 502"))
        self.assertEqual((calls, go_on), (["refresh"], "outage"))  # no session on stale inputs; the outage is waited out
        self.assertIn("HTTP 502", report)
        broken = lambda *a, **kw: subprocess.CompletedProcess(a, 0, b"not a tarball", b"")  # noqa: E731
        calls, go_on, report, vec = self.run_cycle(broken)
        self.assertEqual((calls, go_on), (["refresh"], False))  # a broken tarball is a defect: stop


class RefereeRetryTest(unittest.TestCase):  # E166: the loop never waits on the Founder for the rival's own failure
    def run_cycle(self, evaluated_on):
        launch = load_launch()
        before, after = "a" * 40, "b" * 40
        report = []

        class Fake(quiet_pilot(launch)):
            dispatches = 0
            heads = [before, after]

            def fetch_result(self):
                if not self.dispatches:
                    return None
                done = self.dispatches >= evaluated_on
                return {"head": after, "verdict": "accepted" if done else "rejected",
                        "warnings": [] if done else [f"rival_side_retry:{self.dispatches}"],
                        "state": {"last_evaluated_sha": after if done else None}}

            def dispatch_referee(self, timeout_s):
                self.dispatches += 1
                return {"id": str(self.dispatches), "conclusion": "success", "url": "u"}

            def brain_head(self):
                return self.heads.pop(0)

            def ledger_rows(self, sha):
                return []

            def refresh_inputs(self):  # VectorInputsTest's subject
                pass

            def session(self, *a):
                return {"exit": 0, "minutes": 1}

            def write(self, text):
                report.append(text)

        pilot = Fake(Path(tempfile.mkdtemp()), "o/brain", "o/referee", "target")
        pilot.idle = 0
        pilot.seed = before  # a fresh pilot: nothing to judge before the first session
        args = type("Args", (), dict(model="m", max_turns=1, budget_usd=1, session_timeout=1, referee_timeout=1))
        with mock.patch.object(launch, "say"):
            pilot.cycle(1, args)
        self.metrics = [json.loads(line) for line in pilot.metrics.read_text(encoding="utf-8").splitlines()]
        return pilot.dispatches, "".join(report), launch.MAX_REFEREE_RETRIES

    def test_every_cycle_leaves_one_measurable_line(self):  # what docs/pilot-gunlugu.md counts
        self.run_cycle(evaluated_on=2)
        self.assertEqual(len(self.metrics), 1)
        m = self.metrics[0]
        self.assertEqual((m["pushed"], m["verdict"], m["referee_retries"], m["brain_after"]), (True, "accepted", 1, "b" * 40))
        for key in ("reasons", "warnings", "rival_attempts", "reproduced", "old_refutations_still_reproducing",
                    "ledger_new", "reports_new", "minutes", "cost_usd"):
            self.assertIn(key, m)

    def catch_up(self, prior_head):
        launch = load_launch()
        head, calls = "b" * 40, []

        class Fake(quiet_pilot(launch)):
            dispatches = 0

            def fetch_result(self):
                judged = head if self.dispatches else prior_head
                return {"head": judged, "verdict": "rejected", "state": {"last_evaluated_sha": judged},
                        "warnings": [], "reasons": []}

            def dispatch_referee(self, timeout_s):
                self.dispatches += 1
                calls.append("referee")
                return {"id": "1", "conclusion": "success", "url": "u"}

            def brain_head(self):
                return head  # the session pushes nothing

            def ledger_rows(self, sha):
                return []

            def refresh_inputs(self):  # VectorInputsTest's subject
                pass

            def session(self, *a):
                calls.append("session")
                return {"exit": 0, "minutes": 1}

            def write(self, text):
                pass

        pilot = Fake(Path(tempfile.mkdtemp()), "o/brain", "o/referee", "target")
        pilot.idle, pilot.seed = 0, "s" * 40
        args = type("Args", (), dict(model="m", max_turns=1, budget_usd=1, session_timeout=1, referee_timeout=1))
        with mock.patch.object(launch, "say"):
            pilot.cycle(1, args)
        return calls

    def test_an_unfinished_run_never_lends_an_older_heads_verdict(self):  # E241
        launch = load_launch()
        before, after = "a" * 40, "b" * 40
        report = []

        class Fake(quiet_pilot(launch)):
            heads = [before, after]

            def fetch_result(self):  # the newest signed result is still the previous head's
                return {"head": before, "verdict": "accepted", "reasons": [], "warnings": [],
                        "state": {"last_evaluated_sha": before}}

            def dispatch_referee(self, timeout_s):  # STOP arrived while waiting: the run is still going
                return {"id": "1", "conclusion": "still_running", "url": ""}

            def brain_head(self):
                return self.heads.pop(0)

            def ledger_rows(self, sha):
                return []

            def refresh_inputs(self):  # VectorInputsTest's subject
                pass

            def session(self, *a):
                return {"exit": 0, "minutes": 1}

            def write(self, text):
                report.append(text)

        pilot = Fake(Path(tempfile.mkdtemp()), "o/brain", "o/referee", "target")
        pilot.idle, pilot.seed = 0, before
        args = type("Args", (), dict(model="m", max_turns=1, budget_usd=1, session_timeout=1, referee_timeout=1))
        with mock.patch.object(launch, "say"):
            pilot.cycle(1, args)
        row = json.loads(pilot.metrics.read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual((row["brain_after"], row["verdict"], row["reasons"]), (after, None, []))
        self.assertNotIn("Hakemin kararı", "".join(report))
        self.assertIn("still_running", "".join(report))

    def test_a_github_read_is_retried_and_a_lasting_failure_is_an_outage(self):  # E245
        launch = load_launch()
        ok = mock.Mock(returncode=0, stdout=b'{"sha": "x"}', stderr=b"")
        down = mock.Mock(returncode=1, stdout=b"", stderr=b"error connecting to api.github.com")
        with mock.patch.object(launch, "run", side_effect=[down, down, ok]) as run, \
                mock.patch.object(launch.time, "sleep") as sleep:
            self.assertEqual(launch.gh_json("api", "repos/o/b/commits/main"), {"sha": "x"})
        self.assertEqual(run.call_count, 3)
        self.assertEqual(sleep.call_count, 2)
        with mock.patch.object(launch, "run", return_value=down) as run, mock.patch.object(launch.time, "sleep"):
            with self.assertRaises(launch.GitHubUnavailable):
                launch.gh_read("run", "view", "1")
        self.assertEqual(run.call_count, len(launch.GH_RETRY_DELAYS_S) + 1)

    def test_an_outage_is_waited_out_and_the_unjudged_push_judged_next(self):  # E245
        launch = load_launch()
        calls, waits = [], []

        class Fake:
            def stopped(self):
                return False

            def cycle(self, n, args):
                calls.append(n)
                if n == 1:
                    raise launch.GitHubUnavailable("gh api: error connecting to api.github.com")
                return False

            def wait(self, seconds):
                waits.append(seconds)

        args = type("Args", (), dict(cycles=5))
        with mock.patch.object(launch, "say"):
            launch.run_cycles(Fake(), args)
        self.assertEqual((calls, waits), ([1, 2], [launch.GH_OUTAGE_WAIT_S]))

        class Unreadable(launch.Pilot):
            def dispatch_referee(self, timeout_s):
                return {"id": "1", "conclusion": "success", "url": "u"}

            def fetch_result(self):
                raise launch.GitHubUnavailable("gh api: timed out")

        pilot = Unreadable(Path(tempfile.mkdtemp()), "o/brain", "o/referee", "target")
        with mock.patch.object(launch, "say"):
            self.assertEqual(pilot.judge(1, "b" * 40, 1)[1], None)

    def test_no_session_works_blind_on_an_unjudged_push(self):  # E168, E248: the live f07f215 -> d0dc433 case
        launch = load_launch()
        calls = []

        class Fake(quiet_pilot(launch)):
            def fetch_result(self):  # GitHub cannot be read: the newest result stays an older head's
                return {"head": "a" * 40, "verdict": "accepted", "state": {"last_evaluated_sha": "a" * 40}}

            def dispatch_referee(self, timeout_s):
                calls.append("referee")
                return {"id": "1", "conclusion": "github_unavailable", "url": ""}

            def brain_head(self):
                return "b" * 40

            def ledger_rows(self, sha):
                return []

            def refresh_inputs(self):
                calls.append("refresh")

            def session(self, *a):
                calls.append("session")
                return {"exit": 0, "minutes": 1}

            def write(self, text):
                pass

        pilot = Fake(Path(tempfile.mkdtemp()), "o/brain", "o/referee", "target")
        pilot.idle, pilot.seed = 0, "s" * 40
        args = type("Args", (), dict(model="m", max_turns=1, budget_usd=1, session_timeout=1, referee_timeout=1))
        with mock.patch.object(launch, "say"), self.assertRaises(launch.NoVerdict):
            pilot.cycle(1, args)
        self.assertEqual(calls, ["referee"])

    def test_a_dispatch_that_cannot_reach_github_is_an_outage(self):  # E248
        launch = load_launch()
        down = mock.Mock(returncode=1, stdout=b"", stderr=b"error connecting to api.github.com")
        pilot = launch.Pilot(Path(tempfile.mkdtemp()), "o/brain", "o/referee", "target")
        with mock.patch.object(launch, "run", return_value=down), mock.patch.object(launch.time, "sleep"):
            with self.assertRaisesRegex(launch.GitHubUnavailable, "workflow run"):
                pilot.dispatch_referee(1)
        self.assertTrue(issubclass(launch.NoVerdict, launch.Outage) and issubclass(launch.GitHubUnavailable, launch.Outage))

    def test_the_dispatched_run_is_mains_never_a_branch_trial_of_the_same_minute(self):  # E461
        launch = load_launch()
        pilot = launch.Pilot(Path(tempfile.mkdtemp()), "o/brain", "o/referee", "target")
        ok = mock.Mock(returncode=0, stdout=b"", stderr=b"")
        later = (datetime.now(timezone.utc) + timedelta(seconds=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
        latest = (datetime.now(timezone.utc) + timedelta(seconds=40)).strftime("%Y-%m-%dT%H:%M:%SZ")
        listed = [{"databaseId": 7, "createdAt": later, "headBranch": "ops/trial"},
                  {"databaseId": 8, "createdAt": latest, "headBranch": "main"}]
        asked = []

        def gh(*args):
            asked.append(args)
            if args[:2] == ("run", "list"):
                return listed
            return {"status": "completed", "conclusion": "success", "url": "u"}

        with mock.patch.object(launch, "run", return_value=ok), mock.patch.object(launch, "gh_json", side_effect=gh), \
                mock.patch.object(launch.time, "sleep"):
            got = pilot.dispatch_referee(60)
        self.assertEqual(got["id"], "8")  # the earlier run was a branch's, not this dispatch's
        listing = next(a for a in asked if a[:2] == ("run", "list"))
        self.assertIn("--branch", listing)
        self.assertEqual(listing[listing.index("--branch") + 1], "main")

    def test_the_usage_limit_reset_is_read_from_the_cli(self):  # E243
        wait = load_launch().usage_limit_wait
        at = datetime(2026, 10, 30, 2, 1, 20, tzinfo=timezone.utc)
        hit = {"api_error": "usage_limit_reached", "api_error_status": 429}
        self.assertEqual(wait(dict(hit, final="You've hit your session limit · resets 3:50am (UTC)"), at),
                         (3600 + 48 * 60 + 40) + 120)
        self.assertEqual(wait(dict(hit, final="resets 1pm (UTC)"), at), 6 * 3600)  # capped
        self.assertEqual(wait(dict(hit, final="resets 1:00am (UTC)"), at), 6 * 3600)  # tomorrow, capped
        self.assertEqual(wait(dict(hit, final="limit reached"), at), 30 * 60)  # no reset named: the fallback
        self.assertIsNone(wait({"api_error": None, "api_error_status": None, "final": "pushed MF1"}, at))

    def test_a_session_stopped_by_the_usage_limit_is_an_outage_not_idle(self):  # E243
        launch = load_launch()
        head, waits = "a" * 40, []

        class Fake(quiet_pilot(launch)):
            def fetch_result(self):
                return {"head": head, "verdict": "accepted", "state": {"last_evaluated_sha": head}}

            def brain_head(self):
                return head  # nothing pushed: the session could not work

            def ledger_rows(self, sha):
                return []

            def refresh_inputs(self):  # VectorInputsTest's subject
                pass

            def session(self, *a):
                return {"exit": 0, "minutes": 0.1, "api_error": "usage_limit_reached", "api_error_status": 429,
                        "final": "You've hit your session limit · resets 3:50am (UTC)"}

            def write(self, text):
                pass

            def wait(self, seconds):
                waits.append(seconds)

        pilot = Fake(Path(tempfile.mkdtemp()), "o/brain", "o/referee", "target")
        pilot.idle, pilot.seed = 0, "s" * 40
        args = type("Args", (), dict(model="m", max_turns=1, budget_usd=1, session_timeout=1, referee_timeout=1))
        with mock.patch.object(launch, "say"):
            self.assertTrue(pilot.cycle(1, args))
            self.assertTrue(pilot.cycle(2, args))  # two limited sessions in a row do not stop the pilot
        self.assertEqual(pilot.idle, 0)
        self.assertEqual(len(waits), 2)
        self.assertTrue(all(w > 0 for w in waits))
        rows = [json.loads(line) for line in pilot.metrics.read_text(encoding="utf-8").splitlines()]
        self.assertEqual([r["api_error"] for r in rows], ["usage_limit_reached"] * 2)

    def test_a_push_the_referee_never_judged_is_judged_before_the_next_session(self):  # E168
        self.assertEqual(self.catch_up(prior_head="a" * 40), ["referee", "session"])
        self.assertEqual(self.catch_up(prior_head="b" * 40), ["session"])  # already judged: straight to work

    def test_a_reasons_owner_is_the_referees_own_rule(self):
        owner = load_launch().reason_owner
        self.assertEqual(owner({"kind": "refutation_reproduced", "ref": "repro:x"}), "founder")
        self.assertEqual(owner({"kind": "rival_unresolved", "ref": "secret_in_prompt:generic_assignment"}), "founder")
        self.assertEqual(owner({"kind": "rival_unresolved", "ref": "secret_in_verdict:generic_assignment_bare"}), "rival")
        self.assertEqual(owner({"kind": "rival_missing", "ref": ""}), "rival")
        self.assertEqual(owner({"kind": "infra", "ref": "kos"}), "referee")
        self.assertEqual(owner({"kind": "budget", "ref": ""}), "referee")

    def test_an_unevaluated_commit_goes_back_to_the_referee_before_the_next_session(self):
        dispatches, report, _ = self.run_cycle(evaluated_on=2)
        self.assertEqual(dispatches, 2)
        self.assertIn("1 kez yeniden incelendi", report)
        self.assertIn("**accepted**", report)

    def test_an_evaluated_commit_is_not_sent_again_and_retries_are_capped(self):
        self.assertEqual(self.run_cycle(evaluated_on=1)[0], 1)
        dispatches, report, cap = self.run_cycle(evaluated_on=99)
        self.assertEqual(dispatches, 1 + cap)
        self.assertIn(f"{cap} kez yeniden incelendi", report)


class CycleRecordTest(unittest.TestCase):
    """E313 and the debate's N4: every cycle's line names what its outcome is attributed to, every launcher start is a
    row of its own, and the open brain reports with their age reach the report (N1: a report with no reader)."""

    def cycle(self, verdict_rival=None, sess=None):
        launch = load_launch()
        before, after = "a" * 40, "b" * 40
        report = []

        class Fake(quiet_pilot(launch)):
            heads = [before, after]
            dispatches = 0

            def fetch_result(self):
                if not self.dispatches:
                    return None
                return {"head": after, "verdict": "accepted", "warnings": [], "rival": verdict_rival,
                        "state": {"last_evaluated_sha": after, "last_accepted_sha": after}}

            def dispatch_referee(self, timeout_s):
                self.dispatches += 1
                return {"id": "1", "conclusion": "success", "url": "u"}

            def brain_head(self):
                return self.heads.pop(0)

            def ledger_rows(self, sha):
                return []

            def refresh_inputs(self):
                pass

            def session(self, *a):
                return sess or {"exit": 0, "minutes": 1, "cli_version": "2.1.293", "model_served": "claude-opus-5-5",
                                "timed_out": False}

            def write(self, text):
                report.append(text)

        pilot = Fake(Path(tempfile.mkdtemp()), "o/brain", "o/referee", "target")
        pilot.idle, pilot.seed = 0, before
        pilot.prompt_sha256, pilot.image_id = "p" * 64, "sha256:" + "i" * 64
        args = type("Args", (), dict(model="claude-opus-5-5", max_turns=1, budget_usd=1, session_timeout=1,
                                     referee_timeout=1))
        with mock.patch.object(launch, "say"):
            pilot.cycle(1, args)
        return pilot, json.loads(pilot.metrics.read_text(encoding="utf-8").splitlines()[-1]), "".join(report)

    def test_every_attribution_field_is_on_the_cycles_line(self):
        rival_block = {"prompt_sha256": "r" * 64, "model_served": "claude-sonnet-5-5", "effort": "medium",
                       "cli_version": "2.1.290", "attempts": [], "cost_usd_micros": 320527}
        pilot, m, _ = self.cycle(verdict_rival=rival_block)
        self.assertEqual({k: m[k] for k in ("prompt_sha256", "image_id", "model", "cli_version", "model_served",
                                            "seed_commit", "spec_tohum_tree", "target_sha", "timed_out")},
                         {"prompt_sha256": "p" * 64, "image_id": "sha256:" + "i" * 64, "model": "claude-opus-5-5",
                          "cli_version": "2.1.293", "model_served": "claude-opus-5-5", "seed_commit": "a" * 40,
                          "spec_tohum_tree": "t" * 40, "target_sha": "c" * 40, "timed_out": False})
        self.assertEqual(m["rival_config"], {"prompt_sha256": "r" * 64, "model_served": "claude-sonnet-5-5",
                                             "effort": "medium", "cli_version": "2.1.290"})
        self.assertEqual((m["cost_row"], m["reports_open"]), ("stub", 0))
        self.assertEqual(pilot.cost_calls, [(pilot.cost_calls[0][0], "b" * 40, "b" * 40)])  # after the referee's verdict

    def test_no_rival_block_is_no_rival_configuration_and_a_timeout_is_named(self):
        _, m, _ = self.cycle(sess={"exit": -1, "minutes": 180.2, "timed_out": True})
        self.assertEqual((m["rival_config"], m["timed_out"], m["cli_version"]), (None, True, None))

    def test_a_launcher_start_writes_one_intervention_row(self):
        launch = load_launch()
        pilot = launch.Pilot(Path(tempfile.mkdtemp()), "o/brain", "o/referee", "target")
        pilot.seed = "s" * 40
        args = argparse.Namespace(cycles=3, model="claude-opus-5-5", no_build=True)
        with mock.patch.object(launch.Pilot, "image", return_value="sha256:" + "i" * 64), \
                mock.patch.object(launch.Pilot, "image_prompt", return_value="q" * 64), \
                mock.patch.object(launch, "say") as said:
            pilot.intervention(args)
        self.assertIn("the sessions run the image's", said.call_args[0][0])  # the difference is said
        rows = [json.loads(line) for line in pilot.metrics.read_text(encoding="utf-8").splitlines()]
        # --no-build: the sessions run the image's prompt, so that is the one attributed; the checkout's is beside it.
        self.assertEqual(rows, [{"kind": "intervention", "ts": rows[0]["ts"], "image_id": "sha256:" + "i" * 64,
                                 "prompt_sha256": "q" * 64, "checkout_prompt_sha256": launch.prompt_sha256(),
                                 "seed_commit": "s" * 40, "egress": "open",
                                 "args": {"cycles": "3", "model": "claude-opus-5-5", "no_build": "True"}}])
        self.assertEqual(pilot.prompt_sha256, "q" * 64)  # what every cycle row of this start names
        built = (FOUNDER / "prompt.md").read_bytes().replace(b"\r\n", b"\n")  # the bytes a build now would copy
        self.assertEqual(launch.prompt_sha256(), hashlib.sha256(built).hexdigest())
        self.assertIn("pilot.intervention(args)", (FOUNDER / "launch.py").read_text(encoding="utf-8"))

    def test_the_build_labels_the_image_with_its_prompt_and_a_start_reads_the_label(self):  # E313
        launch = load_launch()
        pilot = launch.Pilot(Path(tempfile.mkdtemp()), "o/brain", "o/referee", "target")
        calls = []

        def fake_run(*argv, **kw):
            calls.append(argv)
            return subprocess.CompletedProcess(argv, 0, b"sha256:x\n", b"")
        with mock.patch.object(launch, "run", side_effect=fake_run), mock.patch.object(launch, "say"):
            pilot.build()
        built = calls[0]
        label = built[built.index("--label") + 1]
        self.assertEqual(label, launch.PROMPT_LABEL + "=" + launch.prompt_sha256())  # the context's LF bytes
        for stdout, rc, expected in ((json.dumps({launch.PROMPT_LABEL: "a" * 64, "other": "x"}).encode(), 0, "a" * 64),
                                     (b"null\n", 0, None),  # an image built before the label: unknown
                                     (json.dumps({launch.PROMPT_LABEL: "not a hash"}).encode(), 0, None),
                                     (b"", 1, None), (b"{broken", 0, None)):
            with mock.patch.object(launch, "run", return_value=subprocess.CompletedProcess([], rc, stdout, b"")):
                self.assertEqual(pilot.image_prompt(), expected, stdout)

    def test_the_transcripts_init_event_gives_the_cli_and_the_served_model(self):
        launch = load_launch()
        path = Path(tempfile.mkdtemp()) / "s.jsonl"
        path.write_text("not json\n" + json.dumps({"type": "system", "subtype": "init", "model": "claude-opus-5-5",
                                                   "claude_code_version": "2.1.293"}) + "\n", encoding="utf-8")
        self.assertEqual(launch.Pilot.transcript_init(path), {"cli_version": "2.1.293", "model_served": "claude-opus-5-5"})
        self.assertEqual(launch.Pilot.transcript_init(path.with_name("none.jsonl")),
                         {"cli_version": None, "model_served": None})

    def test_the_open_reports_and_their_age_reach_the_report(self):
        launch = load_launch()
        seen = {}
        reports = [{"file": "seed-040.json", "id": "seed-040", "state": "open"},
                   {"file": "spec-004.json", "id": "spec-004", "state": "confirmed"}]
        self.assertEqual(launch.report_ages(reports, seen, "2026-10-31T20:00:00Z"), [("seed-040", 0)])
        reports.append({"file": "seed-041.json", "id": "seed-041", "state": "open"})
        self.assertEqual(launch.report_ages(reports, seen, "2026-11-01T01:30:00Z"), [("seed-040", 5), ("seed-041", 0)])
        self.assertEqual(seen["seed-040"], "2026-10-31T20:00:00Z")  # the first sighting is kept
        pilot = launch.Pilot(Path(tempfile.mkdtemp()), "o/brain", "o/referee", "target")
        with mock.patch.object(launch.Pilot, "open_reports", return_value=reports[:1]), \
                mock.patch.object(launch.Pilot, "spec_tohum_tree", return_value="t" * 40), \
                mock.patch.object(launch.Pilot, "target_head", return_value="c" * 40):
            seen_now = pilot.observe("b" * 40)
        self.assertEqual(seen_now, {"spec_tohum_tree": "t" * 40, "target_sha": "c" * 40, "reports_open": [("seed-040", 0)]})
        self.assertIn("seed-040", json.loads((pilot.work / launch.REPORTS_SEEN).read_text(encoding="utf-8")))
        _, _, text = self.cycle()
        self.assertIn("- Açık raporlar (0, beyin `bbbbbbb`", text)
        self.assertIn("- Maliyet satırı (`kind: cost`): stub", text)

    def test_the_reads_are_get_only(self):
        source = (FOUNDER / "launch.py").read_text(encoding="utf-8")
        for name in ("spec_tohum_tree", "open_reports"):
            body = source.split(f"def {name}(", 1)[1].split("\n    def ", 1)[0]
            self.assertNotIn("--method", body)
            self.assertNotIn("-X", body)


class CostRowTest(unittest.TestCase):
    """The seed's launcher contract (`tohum/24a` 4, the debate's N3): after each session the launcher writes the CLI's
    cost as a `kind: cost` founder row, chained by `26`'s rule, as its own identity, and only as a commit the referee
    reads as memory alone. Before delivery it was tried on a mirror (docs/eksik-kaydi.md, E344)."""

    FACT = {"stamp": "20261031T174316Z", "head": "9" * 40, "exit": -1, "minutes": 180.2, "turns": None,
            "cost_usd": None, "subtype": None}

    def test_the_row_is_bare_facts_chained_to_the_last_row_and_passes_the_referees_check(self):
        from snowball_bootstrap import canon, ledgercheck
        launch = load_launch()
        ledger = ledger_bytes(ledger_rows(3))
        line = launch.cost_line(ledger, self.FACT, "2026-10-31T21:00:00Z")
        row = json.loads(line)
        self.assertEqual(row["prev_hash"], ledger_rows(3)[-1]["row_hash"])
        self.assertEqual(row["row_hash"], canon.row_hash(row))
        self.assertEqual({k: row[k] for k in ("row_id", "part", "kind", "derivation", "trust", "snapshot_id")},
                         {"row_id": "f4", "part": "founder", "kind": "cost", "derivation": "tool", "trust": "observed",
                          "snapshot_id": "9" * 40})
        self.assertEqual(row["payload"], {
            "summary": "session 20261031T174316Z: exit -1, 180.2 min, turns unknown, cost_usd_micros unknown, "
                       "CLI result none",
            "refs": ["logs/20261031T174316Z/session-20261031T174316Z.jsonl"]})
        self.assertEqual(ledgercheck.check(ledger + line, ledger, whole=False), [])
        paid = launch.cost_summary(dict(self.FACT, exit=0, minutes=14.5, turns=88, cost_usd=2.3456789, subtype="success"))
        self.assertEqual(paid, "session 20261031T174316Z: exit 0, 14.5 min, turns 88, cost_usd_micros 2345679, "
                               "CLI result success")
        first = json.loads(launch.cost_line(b"", self.FACT, "2026-10-31T21:00:00Z"))
        self.assertEqual((first["row_id"], first["prev_hash"]), ("f1", "0" * 64))

    def test_a_ledger_that_cannot_take_an_appended_row_gets_none(self):
        launch = load_launch()
        ledger = ledger_bytes(ledger_rows(2))
        for broken in (ledger[:-1], ledger + b'{"kind": "x"}\n', ledger + b"not json\n"):
            with self.assertRaises(ValueError):
                launch.cost_line(broken, self.FACT, "2026-10-31T21:00:00Z")

    def mirror(self, extra=None):
        tmp = Path(tempfile.mkdtemp())
        work = tmp / "work"
        make_repo(work, {"referee/a.py": "x = 1\n"})
        accepted = commit(work, {"founder-ledger.jsonl": ledger_bytes(ledger_rows(2))}, "accepted")  # bytes as given
        if extra:
            commit(work, extra, "the Founder's next push")
        bare = tmp / "brain.git"
        subprocess.run(["git", "clone", "--quiet", "--bare", str(work), str(bare)], check=True, capture_output=True)
        return bare, accepted

    def test_on_an_accepted_head_the_row_is_pushed_as_the_launcher(self):
        from snowball_bootstrap import gitio, ledgercheck
        launch = load_launch()
        bare, accepted = self.mirror()
        head = launch.push_cost_rows(str(bare), [self.FACT, dict(self.FACT, stamp="20261031T210135Z")], accepted,
                                     "2026-10-31T22:00:00Z", credential=False)
        self.assertRegex(head, r"^[0-9a-f]{40}$")
        self.assertEqual(gitio.git(bare, "rev-parse", "main").decode().strip(), head)
        self.assertEqual(gitio.git(bare, "log", "-1", "--format=%an <%ae>|%cn", head).decode().strip(),
                         f"{launch.LAUNCHER_NAME} <{launch.LAUNCHER_EMAIL}>|{launch.LAUNCHER_NAME}")
        self.assertEqual(gitio.git(bare, "diff", "--name-only", accepted, head).decode().split(), ["founder-ledger.jsonl"])
        old = gitio.git(bare, "show", f"{accepted}:founder-ledger.jsonl")
        new = gitio.git(bare, "show", f"{head}:founder-ledger.jsonl")
        self.assertEqual(ledgercheck.check(new, old, whole=True), [])
        self.assertEqual([json.loads(x)["kind"] for x in new.splitlines()], ["decision", "decision", "cost", "cost"])

    def test_a_head_with_work_the_referee_has_not_accepted_gets_no_commit(self):
        from snowball_bootstrap import gitio
        launch = load_launch()
        bare, accepted = self.mirror(extra={"referee/a.py": "x = 2\n"})  # rejected or unjudged: judged again otherwise
        before = gitio.git(bare, "rev-parse", "main").decode().strip()
        outcome = launch.push_cost_rows(str(bare), [self.FACT], accepted, "2026-10-31T22:00:00Z", credential=False)
        self.assertTrue(outcome.startswith("deferred: 1 path(s) changed since the last accepted"), outcome)
        self.assertEqual(gitio.git(bare, "rev-parse", "main").decode().strip(), before)
        self.assertTrue(launch.push_cost_rows(str(bare), [self.FACT], None, "t", credential=False).startswith("deferred"))
        bare2, accepted2 = self.mirror(extra={"reports/r.json": "{}\n"})  # memory above the accepted head is fine
        self.assertRegex(launch.push_cost_rows(str(bare2), [self.FACT], accepted2, "2026-10-31T22:00:00Z",
                                               credential=False), r"^[0-9a-f]{40}$")

    def test_a_seed_delivery_above_the_accepted_head_is_the_operators_not_work(self):
        """As the referee reads it (`cli._pull_classify`, E88): while the head's seed is the last epoch commit's, the
        seed paths since the last accepted commit are the delivery; any other seed is work, and waits."""
        from snowball_bootstrap import gitio
        launch = load_launch()
        bare, accepted = self.mirror(extra={"spec/tohum/00-cekirdek.md": "# core, epoch 2\n"})
        epoch = gitio.git(bare, "rev-parse", "main").decode().strip()
        self.assertRegex(launch.push_cost_rows(str(bare), [self.FACT], accepted, "2026-10-31T22:00:00Z", epoch,
                                               credential=False), r"^[0-9a-f]{40}$")
        bare2, accepted2 = self.mirror(extra={"spec/tohum/00-cekirdek.md": "# core, epoch 2\n"})
        for named in (None, accepted2):  # no epoch named, or one whose seed is not the head's
            self.assertTrue(launch.push_cost_rows(str(bare2), [self.FACT], accepted2, "t", named,
                                                  credential=False).startswith("deferred"), named)

    def test_a_deferred_row_waits_in_the_work_folder_and_goes_out_first_next_time(self):
        launch = load_launch()
        pilot = launch.Pilot(Path(tempfile.mkdtemp()), "o/brain", "o/referee", "target")
        calls = []

        def fake_push(remote, facts, last_accepted, ts, epoch=None, credential=True):
            calls.append([f["stamp"] for f in facts])
            return "deferred: 1 path(s)" if len(calls) == 1 else "f" * 40
        with mock.patch.object(launch, "push_cost_rows", side_effect=fake_push):
            self.assertIn("1 satır bekliyor", pilot.record_cost("S1", {"exit": 0}, "b" * 40, "a" * 40))
            self.assertTrue((pilot.work / launch.COST_PENDING).is_file())
            self.assertIn("2 satır yazıldı", pilot.record_cost("S2", {"exit": 0}, "b" * 40, "b" * 40))
        self.assertEqual(calls, [["S1"], ["S1", "S2"]])
        self.assertFalse((pilot.work / launch.COST_PENDING).exists())

    def test_a_session_already_written_is_not_written_again_and_every_git_call_has_a_limit(self):
        """A push that timed out after it reached GitHub leaves its facts pending; the next attempt finds their rows
        and writes only the new ones. A stalled clone or push ends in GitError, which defers the rows (E344)."""
        from snowball_bootstrap import gitio
        launch = load_launch()
        bare, accepted = self.mirror()
        first = launch.push_cost_rows(str(bare), [self.FACT], accepted, "2026-10-31T22:00:00Z", credential=False)
        self.assertEqual(launch.push_cost_rows(str(bare), [self.FACT], first, "t", credential=False), first)  # no commit
        later = dict(self.FACT, stamp="20261101T010000Z")
        limits = []
        real = gitio.git

        def bounded(repo, *args, **kw):
            rest = list(args)
            while rest[0] == "-c":  # `-c name=value` pairs before the command
                rest = rest[2:]
            limits.append((rest[0], kw.get("timeout")))
            return real(repo, *args, **kw)
        with mock.patch.object(launch.gitio, "git", side_effect=bounded):
            second = launch.push_cost_rows(str(bare), [self.FACT, later], first, "2026-11-01T02:00:00Z",
                                           credential=False)
        self.assertEqual([c for c, _ in limits], ["clone", "rev-parse", "add", "commit", "push", "rev-parse"])
        self.assertTrue(all(t for _, t in limits), limits)
        ledger = gitio.git(bare, "show", f"{second}:founder-ledger.jsonl")
        self.assertEqual(sorted(launch.cost_stamps(ledger)), [self.FACT["stamp"], later["stamp"]])
        self.assertEqual(sum(1 for x in ledger.splitlines() if json.loads(x)["kind"] == "cost"), 2)
        with mock.patch.object(gitio.subprocess, "run", side_effect=subprocess.TimeoutExpired(["git"], 1)):
            with self.assertRaisesRegex(gitio.GitError, "timed out"):
                gitio.git(bare, "fetch", timeout=1)
            with self.assertRaisesRegex(gitio.GitError, "timed out"):
                gitio.same_under(bare, first, second, ("seed",), timeout=1)
        pilot = launch.Pilot(Path(tempfile.mkdtemp()), "o/brain", "o/referee", "target")
        with mock.patch.object(launch.gitio, "git", side_effect=gitio.GitError("git push timed out after 300 s")):
            self.assertIn("1 satır bekliyor (deferred: GitError: git push timed out", pilot.record_cost(
                "S1", {"exit": 0}, "b" * 40, "a" * 40))

    def test_the_launchers_cost_commit_is_not_judged_before_the_next_session(self):
        """The cost commit above the Founder's accepted push is memory alone: the referee would read it as a `noop`,
        and judging it first would put that `noop` where the Founder reads the verdict on its own push, cost a referee
        run and, in an outage, hold the Founder on the launcher's commit. Any work above the last accepted commit is
        still judged first (E168)."""
        from snowball_bootstrap import gitio
        launch = load_launch()
        bare, accepted = self.mirror()
        cost = launch.push_cost_rows(str(bare), [self.FACT], accepted, "2026-10-31T22:00:00Z", credential=False)
        alone = lambda remote, last, evaluated, head, epoch=None: launch.memory_alone(  # noqa: E731
            str(remote), last, evaluated, head, epoch, credential=False)
        self.assertTrue(alone(bare, accepted, accepted, cost))
        self.assertFalse(alone(bare, accepted, accepted, accepted))  # main moved on past the head the cycle read
        self.assertFalse(alone(bare, None, accepted, cost))
        self.assertFalse(alone(bare, accepted, None, cost))  # the newest result did not evaluate its own head
        self.assertFalse(alone(bare, "0" * 40, accepted, cost))  # not in the clone
        self.assertFalse(alone(bare, accepted, "0" * 40, cost))
        work, work_accepted = self.mirror(extra={"referee/a.py": "x = 2\n"})
        head = gitio.git(work, "rev-parse", "main").decode().strip()
        self.assertFalse(alone(work, work_accepted, work_accepted, head))  # work above the accepted commit
        # A memory-only push above a rejected one: the referee judges the rejected work again there (E168).
        rejected, last_ok = self.mirror(extra={"referee/a.py": "x = 2\n"})
        bad = gitio.git(rejected, "rev-parse", "main").decode().strip()
        above = launch.push_cost_rows(str(rejected), [self.FACT], bad, "t", credential=False)  # as if bad were accepted
        self.assertFalse(alone(rejected, last_ok, bad, above))
        # A seed epoch above the accepted head is judged first (its `seed_update` result opens a scorecard segment);
        # a cost commit above the judged epoch is memory alone.
        delivered, ok = self.mirror(extra={"spec/tohum/00-cekirdek.md": "# core, epoch 2\n"})
        epoch = gitio.git(delivered, "rev-parse", "main").decode().strip()
        self.assertFalse(alone(delivered, ok, ok, epoch, epoch))
        after_epoch = launch.push_cost_rows(str(delivered), [self.FACT], ok, "t", epoch, credential=False)
        self.assertTrue(alone(delivered, ok, epoch, after_epoch, epoch))
        self.assertFalse(alone(delivered, ok, epoch, after_epoch, None))  # the seed is no delivery without the epoch
        verdict = {"head": accepted, "verdict": "accepted", "rival": {"attempts": [{"claim": "c"}]},
                   "state": {"last_evaluated_sha": accepted, "last_accepted_sha": accepted}}

        class Fake(quiet_pilot(launch)):
            dispatches = 0

            def fetch_result(self):
                return verdict

            def dispatch_referee(self, timeout_s):
                self.dispatches += 1
                return {"id": "1", "conclusion": "success", "url": "u"}

            def memory_alone(self, prior, head_):
                self.brain_remote = str(bare)
                with mock.patch.object(launch, "GH_CREDENTIAL", "credential.helper="):  # a local mirror: none
                    return launch.Pilot.memory_alone(self, prior, head_)

            def brain_head(self):
                return cost

            def ledger_rows(self, sha):
                return []

            def refresh_inputs(self):
                pass

            def session(self, *a):
                return {"exit": 0, "minutes": 1}

            def write(self, text):
                report.append(text)

        report = []
        pilot = Fake(Path(tempfile.mkdtemp()), "o/brain", "o/referee", "target")
        pilot.idle, pilot.seed = 0, "a" * 40
        args = type("Args", (), dict(model="m", max_turns=1, budget_usd=1, session_timeout=1, referee_timeout=1))
        with mock.patch.object(launch, "say"):
            pilot.cycle(1, args)
        self.assertEqual(pilot.dispatches, 0)  # no referee run before the session, so no `noop` artifact
        self.assertIn("- Hakemin önceki kararı (Kurucu'nun okuduğu): accepted", "".join(report))

    def test_the_launchers_own_commit_is_not_a_founder_push(self):
        """The two-sessions-without-a-push stop counts the Founder's pushes: the cost commit lands after the head is
        read, so a session that pushed nothing is idle even when the launcher wrote a row (N3 (d))."""
        launch = load_launch()
        head = "a" * 40

        class Fake(quiet_pilot(launch)):
            def fetch_result(self):
                return {"head": head, "verdict": "accepted", "state": {"last_evaluated_sha": head,
                                                                       "last_accepted_sha": head}}

            def brain_head(self):
                return head

            def ledger_rows(self, sha):
                return []

            def refresh_inputs(self):
                pass

            def session(self, *a):
                return {"exit": 0, "minutes": 1}

            def write(self, text):
                pass

            def record_cost(self, stamp, sess, head_, last_accepted):
                return "1 satır yazıldı, beyin `ccccccc`"

        pilot = Fake(Path(tempfile.mkdtemp()), "o/brain", "o/referee", "target")
        pilot.idle, pilot.seed = 0, head
        args = type("Args", (), dict(model="m", max_turns=1, budget_usd=1, session_timeout=1, referee_timeout=1))
        with mock.patch.object(launch, "say"):
            self.assertTrue(pilot.cycle(1, args))
            self.assertFalse(pilot.cycle(2, args))  # two sessions without a Founder push stop the pilot
        m = json.loads(pilot.metrics.read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual((m["pushed"], pilot.idle), (False, 2))


class TranscriptTest(unittest.TestCase):
    def test_the_closing_result_event_is_what_the_report_reads(self):
        launch = load_launch()
        path = Path(tempfile.mkdtemp()) / "s.jsonl"
        events = [{"type": "system", "subtype": "init"}, {"type": "result", "num_turns": 1, "total_cost_usd": 0.1},
                  "not json", {"type": "result", "subtype": "success", "num_turns": 7, "total_cost_usd": 1.5,
                               "result": "pushed MF1"}]
        path.write_text("\n".join(e if isinstance(e, str) else json.dumps(e) for e in events), encoding="utf-8")
        self.assertEqual(launch.Pilot.transcript_summary(path),
                         {"turns": 7, "cost_usd": 1.5, "subtype": "success", "final": "pushed MF1",
                          "api_error": None, "api_error_status": None})
        self.assertEqual(launch.Pilot.transcript_summary(path.with_name("missing.jsonl")), {"transcript": "missing"})


class ImageAndEntrypointTest(unittest.TestCase):
    def setUp(self):
        self.dockerfile = (FOUNDER / "Dockerfile").read_text(encoding="utf-8")
        self.entry = (FOUNDER / "entrypoint.sh").read_text(encoding="utf-8")

    def test_base_images_are_pinned_by_digest_and_the_founder_is_not_root(self):
        froms = re.findall(r"(?m)^FROM (\S+)", self.dockerfile)
        self.assertEqual(len(froms), 2)
        for image in froms:
            self.assertRegex(image, r"@sha256:[0-9a-f]{64}$")
        self.assertRegex(self.dockerfile, r"(?m)^USER founder$")
        self.assertIn("COPY bootstrap/requirements/claude-cli/", self.dockerfile)  # the referee's own CLI pin
        self.assertIn("npm ci", self.dockerfile)

    def test_the_capsule_pins_the_cli_like_the_referee_does(self):
        env_block = self.dockerfile[self.dockerfile.index("ENV "):self.dockerfile.index("USER ")]
        for key, value in rival.PINNED_ENV.items():
            self.assertRegex(env_block, rf"\b{key}={value}\b", f"{key} differs from the referee's rival pin")

    def test_the_founder_is_asked_for_its_own_ideas_and_given_none(self):  # E207, owner 2026-10-29
        """The owner: the system must come up with ideas such as using what it learned in a later repository in an
        earlier one, or finding similarities between repositories. Those ideas are kept off the prompt, in the
        operator's private idea benchmark; the prompt only asks for the Founder's own ideas."""
        prompt = " ".join((FOUNDER / "prompt.md").read_text(encoding="utf-8").split())
        self.assertIn("kimsenin sana söylemediği, sistemi daha iyi yapacak kendi fikrini çıkar", prompt)
        for idea in ("her iki yönde", "başka repolarda", "benzediğini", "kütüphane", "geriye dönük"):
            self.assertNotIn(idea, prompt)

    def test_disagreements_between_its_agents_are_settled_by_evidence(self):  # E208, owner 2026-10-29
        prompt = " ".join((FOUNDER / "prompt.md").read_text(encoding="utf-8").split())
        for phrase in ("Anlaşmazlık kanıtla çözülür", "oyla, otoriteyle, ilk ya da son gelenle karar verilmez",
                       "kanıtı tutan sonuç alınır", "ikisini ayıran deney tasarlanır"):
            self.assertIn(phrase, prompt)

    def test_documents_are_hints_and_the_founders_own_docs_are_generated(self):  # E206, owner 2026-10-29
        prompt = " ".join((FOUNDER / "prompt.md").read_text(encoding="utf-8").split())
        for phrase in ("Belge ipucudur, gerçek koddur", "her iddiayı kodla, yapılandırmayla ve testle doğrula",
                       "bayat belge", "doğrulanmış haritandan üretilir", "kod değişince yeniden üretilir",
                       "hem hedefin hem kendi kodunun (beynin)", "bir insanın okuyup anlayacağı bir harita",
                       "bayat çizim bayat belgedir",  # E301, owner 2026-10-30
                       "Defterin de belgedir", "Eski bir satıra dayanmadan önce onu bugünkü kodla, testle ve hakemin son "
                       "kararıyla doğrula",  # E302, owner 2026-10-30
                       "Hedef, sahibin ürünüdür", "AI kredisi kısıt değildir, zaman değerlidir",
                       "Yol, yöntem ve sıra senindir",  # E305, owner 2026-10-30
                       "Değer hedefte ölçülür", "bugün değmiyorsa değecek hâle getir",  # E337, owner 2026-10-31
                       "duvar saati sınırı 3 saattir",  # E340, the session limit as an observation
                       "Hedefin iyi yazıldığını varsayma", "yürütmedir, görüş değil",  # E361, owner 2026-10-31
                       "Açığı mimariyle kapat, yamayla değil", "çelik gibi çalışan, hatasız, her yoldan sınanmış",
                       "yama ve tekrar",  # E362, owner 2026-10-31
                       "Bir kez sağlam yaz, tekrar kullan", "daha iyi bir mimari ya da yol var mı"):  # E363, owner 2026-10-31
            self.assertIn(phrase, prompt)

    def test_the_founder_keeps_one_source_and_chooses_its_own_architecture(self):  # E205, owner 2026-10-29
        prompt = " ".join((FOUNDER / "prompt.md").read_text(encoding="utf-8").split())
        for phrase in ("Yazmadan önce aynı ya da benzer işi yapan kodu ara", "tek bir yetkili kaynağı olsun",
                       "duruma bakarak sen karar verirsin", "danışma içindir, reçete değil", "`decision` satırı"):
            self.assertIn(phrase, prompt)

    def test_the_founder_fixes_root_causes_and_never_hides_them(self):  # E204, owner 2026-10-29
        prompt = " ".join((FOUNDER / "prompt.md").read_text(encoding="utf-8").split())
        for phrase in ("kök nedeninden ve mimari olarak onar", "`except: pass`", "susturmak",
                       "özel durum olarak kodlamak", "düzeltilmiş gibi yapma"):
            self.assertIn(phrase, prompt)

    def test_the_founder_measures_its_own_coverage_on_the_real_target(self):  # E203: the muscle, not a per-repo patch
        prompt = " ".join((FOUNDER / "prompt.md").read_text(encoding="utf-8").split())
        for phrase in ("`/work/target` üzerinde salt okunur çalıştır", "kapsamını ölç", "`missing_capability:`",
                       "tek bir repoya özel yama değil", "hedefte yeniden ölçüp farkı yaz", "herkese açıktır"):
            self.assertIn(phrase, prompt)
        self.assertNotIn("project.json", prompt)  # the duty is general; what is missing is the Founder's to find
        self.assertNotIn("Nx", prompt)

    def test_every_kind_the_prompt_asks_for_and_the_launcher_surfaces_is_in_the_closed_sets(self):
        """The Founder's report seed-006 (E158): the ledger's and the reports' kind sets are closed (`26`, `26c`), and
        the prompt said "write it as `missing_capability`", a kind no valid row can carry. A missing capability is a
        `seed_issue` row whose text starts `missing_capability:`; the launcher surfaces only kinds a row can have."""
        from snowball_bootstrap import ledgercheck
        prompt = " ".join((FOUNDER / "prompt.md").read_text(encoding="utf-8").split())
        page = (Path(__file__).resolve().parents[3] / "spec" / "tohum" / "26c-semalar-asama-0.md").read_text(encoding="utf-8")
        notices = set(re.search(r"kind: ([a-z_|]+)", page.split("**reports/*.json**", 1)[1]).group(1).split("|"))
        asked = re.findall(r"`([a-z_]+)` (?:olarak yaz|satırı)", prompt)
        asked += re.findall(r"`[a-z_]+:` diye başlayan bir `([a-z_]+)`", prompt)
        asked += [k for pair in re.findall(r"`([a-z_]+)` ya da `([a-z_]+)` satırı", prompt) for k in pair]
        self.assertIn("seed_issue", asked)
        for kind in asked:
            self.assertIn(kind, set(ledgercheck.FOUNDER_KINDS) | notices, kind)
        self.assertNotIn("`missing_capability` olarak yaz", prompt)
        launch = load_launch()
        self.assertTrue(launch.REPORT_KINDS)
        self.assertLessEqual(set(launch.REPORT_KINDS), set(ledgercheck.FOUNDER_KINDS))
        source = (FOUNDER / "launch.py").read_text(encoding="utf-8")
        self.assertNotIn('"missing_capability"', source)  # no tuple or comparison names it as a kind
        self.assertEqual(source.count('row.get("kind") in REPORT_KINDS') + source.count('r.get("kind") in REPORT_KINDS'), 2)

    OWNER_AIM = "**Sahibin amacı (sahip, 2026-10-30 – 2026-11-01).**"  # E463: the owner's directions, one section

    @classmethod
    def owner_aim(cls, prompt: str) -> str:
        """The owner's section in the whitespace-joined prompt: from its title to the next bold title."""
        start = prompt.index(cls.OWNER_AIM)
        return prompt[start:prompt.index("**", start + len(cls.OWNER_AIM))]

    def test_the_owners_aim_is_one_section_right_after_the_real_target_duty(self):  # E463, owner 2026-11-01
        """The owner's eight directions (E305, E337, E361-E364, E460, E462) are one section, merged by three experts
        and a judge and approved by the owner. The eight old headings are gone; the section stands once, right after
        the coverage duty that E364's "Kapsamını ölçtüğünde" leans on; it keeps the prompt's wrapping; and it names
        no domain, tool, seed page or practice the operator holds back to measure what the Founder finds itself."""
        raw = (FOUNDER / "prompt.md").read_text(encoding="utf-8").replace("\r\n", "\n")
        prompt = " ".join(raw.split())
        self.assertEqual(prompt.count(self.OWNER_AIM), 1)
        self.assertEqual(prompt.count("Sahibin amacı"), 1)
        self.assertNotIn("Sahibin hedefi", prompt)  # 'hedef' is the target repository in this prompt
        for heading in ("**Sahibin önceliği (sahip, 2026-10-30).**", "**Değer hedefte ölçülür (sahip, 2026-10-31).**",
                        "**Hedefin iyi yazıldığını varsayma (sahip, 2026-10-31).**",
                        "**Açığı mimariyle kapat, yamayla değil (sahip, 2026-10-31).**",
                        "**Bir kez sağlam yaz, tekrar kullan; her zaman daha iyi yolu sor (sahip, 2026-10-31).**",
                        "**Bilmediğin alan (sahip, 2026-10-31).**",
                        "**Her repo için, en ileri düzeyde (sahip, 2026-11-01).**",
                        "**Sıra muhakemesi (sahip, 2026-11-01).**"):
            self.assertNotIn(heading, prompt)
        section = self.owner_aim(prompt)
        blocks = raw.split("\n\n")
        first = next(i for i, block in enumerate(blocks) if block.startswith(self.OWNER_AIM))
        end = next(i for i in range(first + 1, len(blocks)) if blocks[i].startswith("**"))
        self.assertTrue(blocks[first - 1].startswith("**Gerçek hedefte sına ve eksiğini kendin bul.**"))
        self.assertTrue(blocks[end].startswith("**Anlaşmazlık kanıtla çözülür"))
        self.assertEqual(" ".join(" ".join(blocks[first:end]).split()), section.strip())  # its paragraphs, no more
        for line in "\n".join(blocks[first:end]).split("\n"):
            self.assertLessEqual(len(line), 120, line)
        for phrase in (self.OWNER_AIM, "bir çıtadır, iddia değil", "ürünün iş akışını da anla",
                       "refactor davranışı korur, bir düzeltme yalnız düzelttiği davranışı bilerek değiştirir",
                       "o işe dokunan derslerin de görevle gider", "sonuç dersi sınar, ders sonucu değil",
                       "Neyi önce yapacağını değer ve risk belirler",
                       "bekleyemeyecek bir risk bu sırayı bozmayı gerektiriyorsa riski önce kapat",
                       "neyi neden sonraya bıraktığınla birlikte",
                       "bu hedefe özgü bir varsayıma dayandığın her yeri açıkça yaz"):
            self.assertIn(phrase, section)
        self.assertIsNone(re.search(r"\byem", section, re.IGNORECASE))  # at a word start: 'işleyemediği' is pinned
        for hint in ("besle", "balık", "akuakült", "alarm", "oksijen", "tank", "sensör", "müdahale",  # no domain
                     "planlayıcı", "dispatcher", "görünüm", "enjeksiyon", "withheld", "lessons_injected",  # no seed
                     "düzeltici", "`22`", "`05`", "Aşama 2",  # mechanism, page or stage timing
                     "etki kümesi", "karakterizasyon", "golden", "mutant", "mutasyon", "sözleşme testi", "canary",
                     "FMEA", "HAZOP", "uçtan",  # held-back practices
                     "adaptör", "Nx", "Rust", "Zig", "cargo", "depmap", "profile.fit", "mermaid",  # no tool, no format
                     "kütüphane", "arayüz", "lint", "K0", "K2", "önce ortak"):  # no layer, no concrete order
            self.assertNotIn(hint.casefold(), section.casefold(), hint)
        self.assertNotIn("mimari", section[section.index("Neyi önce yapacağını"):])  # E362/E363 use it before

    def test_the_order_of_work_is_chosen_so_nothing_is_done_twice(self):  # E462, owner 2026-11-01; in E463's section
        """The owner, in their own analogy: sweep the counter before the floor, or the crumbs make you sweep the floor
        twice. The duty is general: choose an order in which a later step does not undo an earlier one, write why,
        and write when a place had to be reopened. It names no layer, tool, class or concrete order. Since E463 it is
        the order half of the priority paragraph of the owner's section, and its closing is the section's one."""
        prompt = " ".join((FOUNDER / "prompt.md").read_text(encoding="utf-8").split())
        section = self.owner_aim(prompt)
        paragraph = section[section.index("Neyi önce yapacağını"):]
        for phrase in ("önce tezgâhı yaparsan",
                       "birinin sonucu bir öncekini bozmayacak ve aynı işi yeniden yaptırmayacak",
                       "aynı yeri yeniden açmak zorunda kaldığında bunu ve nedenini de yaz",
                       "Yol, yöntem ve sıra senindir"):
            self.assertIn(phrase, paragraph)
        for hint in ("mimari", "arayüz", "kütüphane", "lint", "K0", "K2", "Nx", "önce ortak"):
            self.assertNotIn(hint, paragraph)

    FINISH_WORK = "**İşi bitirerek ilerle (sahip, 2026-11-01).**"  # E500

    def test_a_problem_is_closed_at_its_root_before_the_next_and_no_pr_is_left_open(self):  # E500, owner 2026-11-01
        """The owner: on the target, never move to the next problem before this one is solved at its root; when the
        tokens run out, go on from where it stopped; never leave a PR open; work in commits. One section, its own
        title, after the Founder's duties and before what it may not do, in the prompt's wrapping. Unfinished work
        lives on a work branch (never the brain's main nor the target's brain/integration), a cut session leaves the
        next step in its last commit, and the session after a cut first resumes and closes what was left open; a
        rejection still comes first, and the one-job-per-session rule stands."""
        raw = (FOUNDER / "prompt.md").read_text(encoding="utf-8").replace("\r\n", "\n")
        prompt = " ".join(raw.split())
        self.assertEqual(prompt.count(self.FINISH_WORK), 1)
        blocks = raw.split("\n\n")
        at = next(i for i, block in enumerate(blocks) if block.startswith(self.FINISH_WORK))
        self.assertTrue(blocks[at - 1].startswith("**Görevlerin (operatör, 2026-10-29).**"))
        self.assertTrue(blocks[at + 1].startswith("**Yapamazsın:**"))
        for line in blocks[at].split("\n"):
            self.assertLessEqual(len(line), 120, line)
        section = " ".join(blocks[at].split())
        for phrase in ("bir problemi kökten çözmeden diğerine geçmesin",
                       "kanıtı hakemden geçtiğinde biter; bitmeden sıradakine geçmezsin",
                       "her oturumda yine tek iş yaparsın",
                       "beyinde `wip/<konu>`, hedefte `brain/` altındaki dalın",
                       "yarım iş beynin `main`'ine ve hedefin `brain/integration`'ına girmez",
                       "çalışma dalının son commit mesajına sıradaki adımı yaz",
                       "hakemin bir reddi varsa onu giderdikten sonra",
                       "açtığın her PR oturum bitmeden ya birleşir ya kapanır",
                       "yeni bir işe başlamadan kapanır",
                       "Biten işin çalışma dalını sil"):
            self.assertIn(phrase, section)
        self.assertIn("Ret varsa bu oturumun ilk işi o nedeni düzeltmektir", prompt)  # the rejection rule is unchanged
        self.assertNotIn("force", section.casefold())  # a work branch is pushed forward, never rewritten

    def test_the_system_is_for_every_repository_and_its_lessons_are_claims(self):  # E460, owner 2026-11-01; E463
        """The owner: Snowball is a general application for every kind of repository, not tailored to this target; it
        knows and closes its own gaps, understands the given repository fully, gives its agents the repository's map
        with their task, and tests whether what it learned is right. The duty is general: it names no tool, adaptor,
        ecosystem or format, and how stays the Founder's. Since E463 it is part of the owner's section."""
        prompt = " ".join((FOUNDER / "prompt.md").read_text(encoding="utf-8").split())
        section = self.owner_aim(prompt)
        for phrase in ("her çeşit repoya göre tasarlanmış kapsayıcı bir uygulama olmalı",
                       "Bu hedef senin ilk sınavındır, son değil",
                       "hiç görmediğin bir repoda da doğru çalışacak kadar genel olmalı",
                       "hedefin koddan üretilmiş güncel haritasını ve işin ilgili kısmını görevle birlikte ver",
                       "Öğrendiğin her şey bir iddiadır"):
            self.assertIn(phrase, section)
        for hint in ("Nx", "Rust", "Zig", "cargo", "depmap", "profile.fit", "mermaid", "adaptör"):
            self.assertNotIn(hint, section)

    def test_the_founder_owns_the_whole_target_even_a_domain_it_does_not_know(self):  # E364, owner 2026-10-31; E463
        """The owner: in a domain it does not know at all, with no muscles for it, the system must understand it,
        learn and apply it, solve what it meets and become expert in it, by itself. The duty is general: it names no
        language, tool, mechanism, curriculum or timing, it does not answer the Founder's own earlier closure, and
        it does not point at the seed pages that are held (E304: the owner's decision, never a hint). Since E463 its
        body stands word for word in the owner's section, after the coverage duty it leans on; the sealed generality
        exam (sha256 e901b772...) measures that body."""
        prompt = " ".join((FOUNDER / "prompt.md").read_text(encoding="utf-8").split())
        section = self.owner_aim(prompt)
        body = ("Hedefin bütün kodu, içerdiği her dil, ekosistem ve yapıyla senin alanındır; sıradaki aşamanın "
                "ihtiyacıyla sınırlı değildir. Kapsamını ölçtüğünde işleyemediğin her parça, hiç bilmediğin ve hiçbir "
                "aletinin işleyemediği bir alan olsa da, senin işindir: onu kendin anla, öğren ve uygula, "
                "karşılaştığın problemleri anlayıp çöz, o alanda uzmanlaş.")
        for phrase in (body, "sıradaki aşamanın ihtiyacıyla sınırlı değildir",
                       "hiçbir aletinin işleyemediği bir alan olsa da", "o alanda uzmanlaş",
                       "neyi, ne zaman, hangi sırayla ve nasıl öğreneceğine ve yapacağına sen karar verirsin"):
            self.assertIn(phrase, section)
        self.assertLess(prompt.index("**kapsamını ölç**"), prompt.index(body))
        for hint in ("Rust", "Zig", "cargo", "Cargo", "clippy", "rustfmt", "build.rs",  # no domain, no tool
                     "kas büyüt", "kasın", "müfredat",  # no mechanism, no curriculum
                     "f284", "f360", "kapalı sayılmaz",  # not the answer to its own closure
                     "tohum/17", "tohum/21", "`17`", "`21`"):  # no routing to the held pages
            self.assertNotIn(hint, prompt)

    def test_the_founder_gets_the_vector_inputs_and_reports_a_vector_that_contradicts_its_page(self):  # E244, f97
        prompt = " ".join((FOUNDER / "prompt.md").read_text(encoding="utf-8").split())
        for phrase in ("`/vec`'te salt okunurdur", "`/vec/cases.json`", "Beklenen değerler orada yoktur",
                       "`stdin`'iyle, olduğu gibi", "sayfasıyla çelişiyorsa kırmızı kalır",
                       "operatör bir tohum dönemiyle yanıt verene kadar kabulü engeller",
                       "kanıtıyla (vaka, sayfanın satırı, çıktı) `seed_issue` yaz, etrafından dolaşma",
                       "Bir girdiyi (bir fikstürü, bir yolu, bir vaka adını) özel durum olarak kodlamak gizlemedir",
                       "rakip taze girdilerle çürütür", "Hakem reposunu ve `snowball-mcp`'yi okuma yasağı sürer"):
            self.assertIn(phrase, prompt)
        for claim in ("tartışmalı", "askıya", "disputed"):  # a seed_issue sets no vector aside: nothing implements that
            self.assertNotIn(claim, prompt)

    def test_the_session_has_no_inherited_configuration_and_no_mcp(self):
        self.assertIn('--setting-sources ""', self.entry)
        self.assertIn("--strict-mcp-config", self.entry)
        self.assertIn("--no-session-persistence", self.entry)
        self.assertIn('CLAUDE_CONFIG_DIR="$(mktemp -d)"', self.entry)
        self.assertNotIn("ANTHROPIC_API_KEY", self.entry + self.dockerfile)

    def test_six_tools_are_denied_and_no_other_is_narrowed(self):  # E380, E508  # webfetch_not_disallowed
        """RemoteTrigger is the one default tool whose effect can outlive the capsule; the Cron tools die with the
        session and were never used; WebFetch and WebSearch reach the web around the capsule's network (E508: a search
        is served from outside, its snippets can quote any public repository). Every other default tool stays: the
        session's tool set is the Founder's."""
        call = self.entry[self.entry.index("claude -p"):self.entry.index('2> "/work/logs/session-')]
        denied = re.findall(r'--disallowedTools "([^"]*)"', self.entry)
        self.assertEqual(len(denied), 1)
        self.assertIn(f'--disallowedTools "{denied[0]}"', call)
        self.assertEqual(denied[0].split(","),
                         ["RemoteTrigger", "CronCreate", "CronDelete", "CronList", "WebFetch", "WebSearch"])
        for narrowing in ("--tools", "--allowedTools", "--allowed-tools", "--disallowed-tools"):
            self.assertNotRegex(self.entry, rf"(?m){re.escape(narrowing)}(\s|=|$)", narrowing)

    def test_git_trusts_the_brain_clone_on_its_root_owned_tmpfs(self):  # E152: without it no commit, no push
        self.assertIn("safe.directory /work/brain", self.entry)

    def test_the_clone_holds_no_history_before_the_seed(self):  # E154: earlier rehearsal code is not the Founder's
        cut = self.entry[self.entry.index('if [ -n "${BRAIN_SEED:-}" ]'):]
        self.assertIn('merge-base --is-ancestor "$BRAIN_SEED" HEAD', cut)
        self.assertIn("> /work/brain/.git/shallow", cut)
        self.assertIn("reflog expire --expire=now --all", cut)
        self.assertIn("gc --quiet --prune=now", cut)
        self.assertLess(self.entry.index("git clone"), self.entry.index('if [ -n "${BRAIN_SEED:-}" ]'))
        self.assertLess(self.entry.index("gc --quiet --prune=now"), self.entry.index("claude -p"))

    def test_the_github_token_never_reaches_a_url_a_command_line_or_the_log(self):
        self.assertIn("http.https://github.com/.extraheader", self.entry)
        self.assertIn("unset GITHUB_TOKEN basic", self.entry)
        self.assertNotRegex(self.entry, r"https://[^\"\s]*\$\{?GITHUB_TOKEN")
        self.assertNotRegex(self.entry, r"echo[^\n]*\$\{?(GITHUB_TOKEN|CLAUDE_CODE_OAUTH_TOKEN|basic)")
        self.assertNotIn("set -x", self.entry)


class BrainDefinitionsTest(unittest.TestCase):  # E450, owner 2026-11-01: the brain's agents/ and skills/ load, checked
    """The capsule loads the agent and skill definitions the Founder keeps in its brain, at the start of every session,
    and nothing else of the brain. Each guardrail is held here; the real CLI reading the result is in test_live_cli."""

    def setUp(self):
        self.defs = load_brain_defs()
        self.tmp = Path(tempfile.mkdtemp())

    def brain(self, entries: dict) -> Path:
        path = self.tmp / f"brain{sum(1 for _ in self.tmp.iterdir())}"
        tree_repo(path, entries)
        return path

    def load(self, entries: dict, limits=None) -> tuple[dict, Path]:
        brain = self.brain(entries)
        plugin = brain.with_name(brain.name + "-plugin")
        with mock.patch.object(self.defs, "LIMITS", limits or self.defs.LIMITS):
            record = self.defs.build(brain, plugin).record()
        return record, plugin

    @staticmethod
    def files(plugin: Path) -> list[str]:
        return sorted(p.relative_to(plugin).as_posix() for p in plugin.rglob("*") if p.is_file())

    @staticmethod
    def skipped(record: dict) -> dict[str, list[str]]:
        return {row["path"]: row["reasons"] for row in record["skipped"]}

    def test_only_agents_and_skills_become_the_plugin(self):
        brain = self.brain({
            "agents/reviewer.md": definition("reviewer"), "skills/probe/SKILL.md": definition("probe"),
            "CLAUDE.md": b"# instructions\n", "AGENTS.md": b"x\n", ".mcp.json": b'{"mcpServers": {"x": {}}}\n',
            ".claude/settings.json": b'{"hooks": {}}\n', ".claude/agents/inner.md": definition("inner"),
            ".claude/skills/inner/SKILL.md": definition("inner"), "hooks/hooks.json": b'{"hooks": {}}\n',
            "commands/c.md": b"c\n", "output-styles/s.md": b"s\n", "settings.json": b"{}\n",
            ".claude-plugin/plugin.json": b'{"name": "other", "hooks": "./h.json"}\n', "monitors/monitors.json": b"{}\n",
            "bin/tool": ("100755", b"#!/bin/sh\n"), "referee/agents/x.md": definition("x"),
            "docs/skills/y/SKILL.md": definition("y")})
        (brain / "agents").mkdir()  # in the working tree, not committed: git's objects are what is read
        (brain / "agents" / "extra.md").write_bytes(definition("extra"))
        plugin = self.tmp / "plugin"
        record = self.defs.build(brain, plugin).record()
        self.assertEqual(self.files(plugin), [".claude-plugin/plugin.json", "agents/reviewer.md", "skills/probe/SKILL.md"])
        self.assertEqual(json.loads((plugin / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")),
                         {"name": "brain"})
        self.assertEqual([a["loaded_as"] for a in record["agents"]], ["brain:reviewer"])
        self.assertEqual([s["loaded_as"] for s in record["skills"]], ["brain:probe"])
        self.assertEqual(record["skipped"], [])  # nothing outside the two folders is even looked at
        self.assertIsNone(record["error"])

    def test_every_definition_is_written_anew_from_its_checked_fields(self):
        agent = ('---\r\nname: reviewer\r\ndescription: "Reviews: \\"quoted\\" code, ç # text"\r\n\r\n'
                 'tools: Read,  Grep ,Read\r\nmodel: sonnet\r\n---\r\nYou review.\r\n---\r\nstill the body\r\n')
        script = b"#!/bin/sh\r\necho run\r\n"
        record, plugin = self.load({
            "agents/reviewer.md": agent.encode("utf-8"),
            "skills/probe/SKILL.md": b"---\nname: probe\ndescription: 'It''s a probe: run it'\n---\nRun it.",
            "skills/probe/scripts/run.sh": ("100755", script), "skills/probe/notes.md": b"notes\n"})
        self.assertEqual((plugin / "agents" / "reviewer.md").read_text(encoding="utf-8"),
                         '---\nname: reviewer\ndescription: "Reviews: \\"quoted\\" code, ç # text"\ntools: Read, Grep\n'
                         "model: sonnet\n---\nYou review.\n---\nstill the body\n")
        self.assertEqual((plugin / "skills" / "probe" / "SKILL.md").read_text(encoding="utf-8"),
                         '---\nname: probe\ndescription: "It\'s a probe: run it"\n---\nRun it.\n')
        self.assertEqual((plugin / "skills" / "probe" / "scripts" / "run.sh").read_bytes(), script)  # as it is
        if os.name != "nt":
            self.assertEqual((plugin / "skills" / "probe" / "scripts" / "run.sh").stat().st_mode & 0o777, 0o755)
            self.assertEqual((plugin / "skills" / "probe" / "notes.md").stat().st_mode & 0o777, 0o644)
        self.assertEqual(record["agents"][0]["tools"], ["Read", "Grep"])
        self.assertEqual(record["agents"][0]["model"], "sonnet")

    def test_a_key_outside_the_format_drops_the_definition(self):
        keys = ("hooks", "mcpServers", "permissionMode", "skills", "isolation", "disallowedTools", "color")
        entries = {f"agents/a{i}.md": definition(f"a{i}", extra={key: "x"}) for i, key in enumerate(keys)}
        skill_keys = ("allowed-tools", "hooks", "model", "context", "tools")  # a skill takes name and description only
        entries.update({f"skills/s{i}/SKILL.md": definition(f"s{i}", extra={key: "x"}) for i, key in enumerate(skill_keys)})
        record, plugin = self.load(entries)
        self.assertEqual(record["agents"] + record["skills"], [])
        self.assertEqual(self.skipped(record), {**{f"agents/a{i}.md": [f"key_not_allowed:{k}"] for i, k in enumerate(keys)},
                                                **{f"skills/s{i}/": [f"key_not_allowed:{k}"] for i, k in enumerate(skill_keys)}})
        self.assertEqual(self.files(plugin), [".claude-plugin/plugin.json"])

    def test_an_agent_whose_tools_leave_the_capsules_is_dropped_and_named(self):
        entries = {"agents/ok.md": definition("ok",
                                              extra={"tools": "Read, Grep, Bash, Agent, Task, NotebookEdit, Skill"})}
        for tool in self.defs.DENIED_TOOLS:
            entries[f"agents/deny-{tool.lower()}.md"] = definition(f"deny-{tool.lower()}", extra={"tools": f"Read, {tool}"})
        unknown = ("Foo", "Bash(git *)", "mcp__x__y", "read", "PowerShell")
        for i, tool in enumerate(unknown):
            entries[f"agents/unknown-{i}.md"] = definition(f"unknown-{i}", extra={"tools": f"Read, {tool}"})
        entries["agents/empty.md"] = definition("empty", extra={"tools": ""})
        entries["agents/hole.md"] = definition("hole", extra={"tools": "Read,,Grep"})
        record, plugin = self.load(entries)
        self.assertEqual([(a["name"], a["tools"]) for a in record["agents"]],
                         [("ok", ["Read", "Grep", "Bash", "Agent", "Task", "NotebookEdit", "Skill"])])
        skipped = self.skipped(record)
        for tool in self.defs.DENIED_TOOLS:
            self.assertEqual(skipped[f"agents/deny-{tool.lower()}.md"], [f"tool_denied:{tool}"])
        for i, tool in enumerate(unknown):
            self.assertEqual(skipped[f"agents/unknown-{i}.md"], [f"tool_not_allowed:{tool}"])
        self.assertEqual(skipped["agents/empty.md"], ["bad_tools"])
        self.assertEqual(skipped["agents/hole.md"], ["bad_tools"])
        self.assertEqual(self.files(plugin), [".claude-plugin/plugin.json", "agents/ok.md"])

    def test_the_tool_sets_are_the_capsules(self):  # E380, E508: the six the entrypoint denies, none of them allowed
        entry = (FOUNDER / "entrypoint.sh").read_text(encoding="utf-8")
        self.assertEqual(re.findall(r'--disallowedTools "([^"]*)"', entry), [",".join(self.defs.DENIED_TOOLS)])
        self.assertEqual(self.defs.ALLOWED_TOOLS & set(self.defs.DENIED_TOOLS), set())
        self.assertTrue(all(self.defs.TOOL_RE.fullmatch(tool) for tool in self.defs.ALLOWED_TOOLS))

    def test_the_limits_are_one_named_constant_and_each_is_enforced(self):
        Limits = self.defs.Limits
        self.assertIsInstance(self.defs.LIMITS, Limits)
        big = definition("big", body="x" * 300 + "\n")
        cases = [  # (limits, brain, skipped, loaded)
            (Limits(agents=2), {f"agents/{n}.md": definition(n) for n in "abc"}, {"agents/c.md": ["over_limit:agents"]},
             ["a", "b"]),
            (Limits(skills=1), {f"skills/{n}/SKILL.md": definition(n) for n in "ab"}, {"skills/b/": ["over_limit:skills"]},
             ["a"]),
            (Limits(definition_bytes=200), {"agents/big.md": big, "skills/big/SKILL.md": big, "agents/a.md": definition("a")},
             {"agents/big.md": ["over_limit:definition_bytes"], "skills/big/": ["over_limit:definition_bytes"]}, ["a"]),
            (Limits(skill_files=2), {"skills/s/SKILL.md": definition("s"), "skills/s/a": b"a", "skills/s/b": b"b",
                                     "skills/t/SKILL.md": definition("t"), "skills/t/a": b"a"},
             {"skills/s/": ["over_limit:skill_files"]}, ["t"]),
            (Limits(skill_bytes=100), {"skills/s/SKILL.md": definition("s"), "skills/s/a": b"a" * 60,
                                       "skills/t/SKILL.md": definition("t")},
             {"skills/s/": ["over_limit:skill_bytes"]}, ["t"]),
            (Limits(skill_depth=1), {"skills/s/SKILL.md": definition("s"), "skills/s/a/c/d.txt": b"d",
                                     "skills/t/SKILL.md": definition("t"), "skills/t/a/b.txt": b"b"},
             {"skills/s/": ["over_limit:skill_depth:skills/s/a/c/d.txt"]}, ["t"]),
            (Limits(total_bytes=100), {f"agents/{n}.md": definition(n) for n in "ab"},  # 64 bytes each
             {"agents/b.md": ["over_limit:total_bytes"]}, ["a"]),
            (Limits(entries=3), {**{f"agents/{n}.md": definition(n) for n in "abcd"}, "skills/s/SKILL.md": definition("s")},
             {"agents/": ["over_limit:entries"]}, ["s"]),
        ]
        for limits, entries, skipped, loaded in cases:
            with self.subTest(limits=limits):
                record, _ = self.load(entries, limits)
                self.assertEqual(self.skipped(record), skipped)
                self.assertEqual([d["name"] for d in record["agents"] + record["skills"]], loaded)
                self.assertEqual(record["limits"], dataclasses.asdict(limits))
        record, _ = self.load({f"agents/{n}.md": b"broken\n" for n in "abc"}, Limits(skipped_listed=2))
        self.assertEqual((len(record["skipped"]), record["skipped_total"]), (2, 3))  # the rest are counted

    def test_names_are_checked_and_nothing_leads_out_of_the_brain(self):
        record, plugin = self.load({
            "agents/Upper.md": definition("Upper"), "agents/under_score.md": definition("under_score"),
            "agents/-dash.md": definition("-dash"), f"agents/{'a' * 65}.md": definition("a" * 65),
            "agents/mismatch.md": definition("other"), "agents/claude.md": definition("claude"),
            "agents/agents.md": definition("agents"), "agents/link.md": ("120000", b"../../../run/secrets/founder.env"),
            "agents/sub.md": ("160000", b"a" * 40), "agents/readme.txt": b"x\n", "agents/nested/x.md": definition("x"),
            "skills/linked/SKILL.md": ("120000", b"../../CLAUDE.md"),
            "skills/inner-link/SKILL.md": definition("inner-link"), "skills/inner-link/data": ("120000", b"/etc/passwd"),
            "skills/sub/SKILL.md": definition("sub"), "skills/sub/vendor": ("160000", b"b" * 40),
            "skills/conf/SKILL.md": definition("conf"), "skills/conf/.claude/settings.json": b"{}\n",
            "skills/conf2/SKILL.md": definition("conf2"), "skills/conf2/docs/CLAUDE.md": b"x\n",
            "skills/odd/SKILL.md": definition("odd"), "skills/odd/a b.txt": b"x\n",
            "skills/uni/SKILL.md": definition("uni"), "skills/uni/\u00f6.txt": b"x\n",
            "skills/Bad_Name/SKILL.md": definition("Bad_Name"), "skills/README.md": b"x\n",
            "skills/ok/SKILL.md": definition("ok"), "skills/ok/.gitkeep": b""})
        self.assertEqual(record["agents"], [])
        self.assertEqual([s["name"] for s in record["skills"]], ["ok"])
        self.assertEqual(self.skipped(record), {
            "agents/Upper.md": ["bad_name"], "agents/under_score.md": ["bad_name"], "agents/-dash.md": ["bad_name"],
            f"agents/{'a' * 65}.md": ["bad_name"], "agents/mismatch.md": ["name_mismatch"],
            "agents/claude.md": ["agent_config"], "agents/agents.md": ["agent_config"], "agents/link.md": ["symlink"],
            "agents/sub.md": ["submodule"], "agents/readme.txt": ["not_a_definition"],
            "agents/nested/": ["not_a_definition"], "skills/README.md": ["not_a_definition"],
            "skills/linked/": ["symlink:skills/linked/SKILL.md"], "skills/inner-link/": ["symlink:skills/inner-link/data"],
            "skills/sub/": ["submodule:skills/sub/vendor"],
            "skills/conf/": ["agent_config:skills/conf/.claude/settings.json"],
            "skills/conf2/": ["agent_config:skills/conf2/docs/CLAUDE.md"], "skills/odd/": ["bad_path:skills/odd/a b.txt"],
            "skills/uni/": ["bad_path:skills/uni/\u00f6.txt"], "skills/Bad_Name/": ["bad_name"]})
        self.assertEqual(self.files(plugin), [".claude-plugin/plugin.json", "skills/ok/.gitkeep", "skills/ok/SKILL.md"])

    def test_the_record_names_what_loaded_with_the_sha256_of_its_source(self):
        agent, skill, notes = definition("reviewer", extra={"model": "inherit"}), definition("probe"), b"notes\n"
        brain = self.brain({"agents/reviewer.md": agent, "skills/probe/SKILL.md": skill, "skills/probe/notes.md": notes,
                            "agents/bad.md": b"no front matter\n"})
        logs = self.tmp / "logs"
        logs.mkdir()
        rc = self.defs.main([str(brain), str(self.tmp / "plugin"), str(logs / "brain-definitions.json")])
        self.assertEqual(rc, 0)
        record = json.loads((logs / "brain-definitions.json").read_text(encoding="utf-8"))
        sha = lambda data: hashlib.sha256(data).hexdigest()  # noqa: E731  the blob's bytes: `git cat-file blob | sha256sum`
        self.assertEqual(record["schema"], "snowball-brain-definitions/1")
        self.assertEqual(record["brain"], sh(brain, "git", "rev-parse", "HEAD"))
        self.assertIsNone(record["error"])
        self.assertEqual(record["agents"], [{"name": "reviewer", "loaded_as": "brain:reviewer", "path": "agents/reviewer.md",
                                             "sha256": sha(agent), "tools": None, "model": "inherit"}])
        self.assertEqual(record["skills"], [{"name": "probe", "loaded_as": "brain:probe", "path": "skills/probe/SKILL.md",
                                             "sha256": sha(skill), "files": {"skills/probe/SKILL.md": sha(skill),
                                                                             "skills/probe/notes.md": sha(notes)}}])
        self.assertEqual(record["skipped"], [{"path": "agents/bad.md", "reasons": ["no_frontmatter"]}])
        self.assertEqual(record["limits"], dataclasses.asdict(self.defs.LIMITS))
        self.assertEqual(record["denied_tools"], list(self.defs.DENIED_TOOLS))
        self.assertEqual(record["allowed_tools"], sorted(self.defs.ALLOWED_TOOLS))
        self.assertEqual(sorted(p.name for p in logs.iterdir()), ["brain-definitions.json"])  # no temporary left

    def test_a_broken_definition_is_skipped_and_the_rest_load(self):
        record, plugin = self.load({
            "agents/good.md": definition("good"),
            "agents/latin.md": "---\nname: latin\ndescription: café\n---\nx\n".encode("latin-1"),
            "agents/bare.md": b"You review.\n", "agents/open.md": b"---\nname: open\ndescription: d\nno end\n",
            "agents/line.md": b"---\nname: line\n  indented: x\ndescription: d\n---\nx\n",
            "agents/twice.md": b"---\nname: twice\nname: twice\ndescription: d\n---\nx\n",
            "agents/nodesc.md": b"---\nname: nodesc\n---\nx\n", "agents/empty.md": b"---\nname: empty\ndescription: d\n---\n\n \n",
            "agents/quote.md": b'---\nname: quote\ndescription: "open\n---\nx\n',
            "agents/ctrl.md": b'---\nname: ctrl\ndescription: "a\\u0007b"\n---\nx\n',
            "agents/sep.md": "---\nname: sep\ndescription: a\u2028b\n---\nx\n".encode("utf-8"),
            "agents/long.md": definition("long", description="d" * 1025),
            "agents/model.md": definition("model", extra={"model": "sonnet; rm -rf /"}),
            "skills/good/SKILL.md": definition("good"),
            "skills/nobody/SKILL.md": b"---\nname: nobody\ndescription: d\n---\n"})
        self.assertEqual([a["name"] for a in record["agents"]], ["good"])
        self.assertEqual([s["name"] for s in record["skills"]], ["good"])
        self.assertEqual(self.skipped(record), {
            "agents/latin.md": ["not_utf8"], "agents/bare.md": ["no_frontmatter"], "agents/open.md": ["no_frontmatter"],
            "agents/line.md": ["bad_frontmatter_line"], "agents/twice.md": ["duplicate_key:name"],
            "agents/nodesc.md": ["missing:description"], "agents/empty.md": ["empty_body"],
            "agents/quote.md": ["bad_quotes:description", "missing:description"], "agents/ctrl.md": ["bad_description"],
            "agents/sep.md": ["bad_description"], "agents/long.md": ["bad_description"], "agents/model.md": ["bad_model"],
            "skills/nobody/": ["empty_body"]})
        self.assertIsNone(record["error"])

    def test_an_unforeseen_failure_in_one_definition_names_it_and_the_rest_load(self):
        real = self.defs.check_fields

        def failing(fields, name):
            if name == "boom":
                raise RuntimeError("unforeseen")
            return real(fields, name)

        with mock.patch.object(self.defs, "check_fields", failing):
            record, plugin = self.load({"agents/boom.md": definition("boom"), "agents/good.md": definition("good"),
                                        "skills/boom/SKILL.md": definition("boom"), "skills/boom/a.txt": b"a",
                                        "skills/good/SKILL.md": definition("good")})
        self.assertEqual(self.skipped(record), {"agents/boom.md": ["error:RuntimeError"],
                                                "skills/boom/": ["error:RuntimeError"]})
        self.assertEqual(self.files(plugin), [".claude-plugin/plugin.json", "agents/good.md", "skills/good/SKILL.md"])

    def test_a_loader_that_cannot_read_the_brain_leaves_no_plugin_and_says_why(self):
        plugin, record_file = self.tmp / "plugin", self.tmp / "brain-definitions.json"
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(self.defs.main([str(self.tmp / "no-brain"), str(plugin), str(record_file)]), 0)
        self.assertIn("brain definitions not loaded: CalledProcessError", err.getvalue())  # the container's log
        record = json.loads(record_file.read_text(encoding="utf-8"))
        self.assertTrue(record["error"].startswith("CalledProcessError"), record["error"])
        self.assertEqual((record["agents"], record["skills"]), ([], []))
        self.assertFalse(plugin.exists())  # the CLI starts without a plugin it cannot find (test_live_cli)
        self.assertFalse(plugin.with_name("plugin.partial").exists())

    def test_the_capsule_loads_them_after_the_clone_and_before_claude_and_never_stops_on_them(self):
        entry = (FOUNDER / "entrypoint.sh").read_text(encoding="utf-8")
        loader = ('python3 /opt/founder/brain_defs.py /work/brain "$CLAUDE_CONFIG_DIR/brain-plugin" '
                  '/work/logs/brain-definitions.json \\\n  || echo ')
        self.assertEqual(entry.count("/opt/founder/brain_defs.py"), 1)
        self.assertIn(loader, entry)  # `||`: under `set -e` a failed loader never stops the session
        self.assertLess(entry.index("gc --quiet --prune=now"), entry.index(loader))
        self.assertLess(entry.index(loader), entry.index("claude -p"))
        call = entry[entry.index("claude -p"):entry.index('> "/work/logs/session-')]
        self.assertEqual(re.findall(r"--plugin-dir \S+", entry), ['--plugin-dir "$CLAUDE_CONFIG_DIR/brain-plugin"'])
        self.assertIn('--plugin-dir "$CLAUDE_CONFIG_DIR/brain-plugin"', call)
        self.assertIn('--setting-sources ""', call)
        for other in ("--agents", "--agent ", "--add-dir", "--settings", "--plugin-url", "--bare", "--safe-mode"):
            self.assertNotIn(other, call)  # the plugin is the one way in
        self.assertIn('CLAUDE_CONFIG_DIR="$(mktemp -d)"', entry)  # the plugin's folder is this session's own
        self.assertIn("COPY founder/brain_defs.py /opt/founder/brain_defs.py", (FOUNDER / "Dockerfile").read_text(
            encoding="utf-8"))
        self.assertIn("founder/brain_defs.py", load_launch().BUILD_FILES)
        self.assertEqual(self.defs.PLUGIN, "brain")

    def test_the_prompt_states_which_brain_folders_load_and_where_their_record_is(self):  # E450, owner 2026-11-01
        prompt = " ".join((FOUNDER / "prompt.md").read_text(encoding="utf-8").split())
        title = "**Beynin tanımları (gözlem).**"
        paragraph = prompt[prompt.index(title):]
        paragraph = paragraph[:paragraph.index("**", len(title))]
        for phrase in ("her oturumun başında", "`agents/` ve `skills/`", "`brain:<ad>`", "`spec/tohum/24a`",
                       "başka hiçbir dosyasını yapılandırma olarak yüklemez", "`/work/logs/brain-definitions.json`"):
            self.assertIn(phrase, paragraph)
        for nudge in ("yaz", "kullan", "öner", "oluştur", "faydal", "yararl", "gerekirse", "istersen", "senindir", "meli",
                      "malı"):
            self.assertNotIn(nudge, paragraph.casefold())  # a fact: whether, when and why is the Founder's own choice
        self.assertEqual(prompt.count("brain-definitions.json"), 1)
        self.assertIn("`.claude/`", prompt[prompt.index("**Yapamazsın:**"):])  # its own .claude/ still loads nothing

    def test_the_referee_judges_a_push_of_them_as_the_founders_code(self):  # E450: not out of scope, not a record
        from snowball_bootstrap import classify
        paths = ["agents/reviewer.md", "skills/probe/SKILL.md", "skills/probe/scripts/run.sh"]
        self.assertEqual(classify.classify(paths), ("code", []))
        self.assertEqual(classify.classify(paths + [classify.LEDGER_FILE]), ("code", []))
        self.assertEqual(classify.classify(["spec/asama-0/a.md", "agents/reviewer.md"]),
                         ("rejected", [classify.MIXED]))  # like any code beside a spec request
        for path in paths:
            self.assertFalse(classify.is_agent_config(path), path)
            self.assertFalse(classify.is_founder_record(path), path)
            self.assertFalse(classify.is_seed_path(path), path)
            self.assertFalse(rival.hidden(path), path)  # the rival reads them like the rest of the push
        self.assertEqual(self.defs.AGENT_CONFIG_DIRS, classify.AGENT_DIRS)  # one rule for both
        self.assertEqual(self.defs.AGENT_CONFIG_FILES, classify.AGENT_FILES)


class LauncherResumeTest(unittest.TestCase):
    """E505 (owner-approved gap C): the launcher survives a crash or a reboot and resumes by itself, and never
    overrides a deliberate stop. One launcher per work folder (an OS lock the OS frees with its process); <work>/RUNNING
    holds the run in progress; `--resume`, which the Scheduled Task runs, continues it. No task is registered here."""

    def setUp(self):
        self.launch = load_launch()
        self.work = Path(tempfile.mkdtemp())

    def running(self):
        path = self.work / "RUNNING"
        return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None

    def store(self, **fields):
        state = {"argv": [], "cycles_left": 3, "idle": 0, "started": "2026-11-02T01:00:00Z",
                 "updated": "2026-11-02T02:00:00Z", **fields}
        (self.work / "RUNNING").write_text(json.dumps(state), encoding="utf-8")
        return state

    def pilot_class(self, outcomes, seen):
        test = self

        class FakePilot:  # the launcher's Pilot as start() and run_cycles() see it; the cycle has its own tests
            idle = 0

            def __init__(self, work, brain, referee, target, egress="open"):
                self.work, self.report = work, work / "pilot-log.md"
                seen["target"], seen["egress"] = target, egress

            def image_entrypoint(self):  # E508: what the build labelled; a start holds it to the checkout's
                return seen.get("image_entrypoint", test.launch.entrypoint_sha256())

            def preflight(self):
                seen["calls"].append("preflight")
                if seen.get("preflight_fails"):
                    sys.exit("preflight failed")

            def build(self):
                seen["calls"].append("build")

            def intervention(self, args):
                seen["args"] = args

            def write(self, text):
                with self.report.open("a", encoding="utf-8") as fh:
                    fh.write(text)

            def stopped(self):
                return (self.work / "STOP").exists()

            def wait(self, seconds):
                if seen.get("stop_while_waiting"):
                    (self.work / "STOP").touch()

            def cycle(self, n, args):
                seen["running"].append(test.running())
                seen["idle"].append(self.idle)
                outcome = outcomes.pop(0)
                if isinstance(outcome, BaseException):
                    raise outcome
                self.idle += 1  # no push
                return outcome
        return FakePilot

    def main(self, argv, outcomes=(), ready=True, **flags):
        seen = {"calls": [], "running": [], "idle": [], **flags}
        with mock.patch.object(self.launch, "Pilot", self.pilot_class(list(outcomes), seen)), \
                mock.patch.object(self.launch.shutil, "which", return_value="/usr/bin/tool"), \
                mock.patch.object(self.launch, "wait_ready", side_effect=ready if callable(ready) else None,
                                  return_value=ready) as wait, \
                mock.patch.object(self.launch, "say"):
            seen["code"] = self.launch.main([*argv, "--work", str(self.work)])
        seen["waited"] = wait.called
        return seen

    def test_one_launcher_holds_the_work_folder_and_the_os_frees_a_dead_ones_lock(self):  # launcher_lock_shared
        path = self.work / "launcher.lock"
        first, second = self.launch.LauncherLock(path), self.launch.LauncherLock(path)
        self.assertTrue(first.acquire())
        self.assertFalse(second.acquire())
        first.release()
        self.assertTrue(second.acquire())
        second.release()
        # Another process holds it, then dies without releasing (a crash, a kill): the lock goes with it.
        code = ("import importlib.util, sys, time; from pathlib import Path; "
                "spec = importlib.util.spec_from_file_location('launch', sys.argv[1]); "
                "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); "
                "lock = m.LauncherLock(Path(sys.argv[2])); print(lock.acquire(), flush=True); time.sleep(600)")
        proc = subprocess.Popen([sys.executable, "-c", code, str(FOUNDER / "launch.py"), str(path)],
                                stdout=subprocess.PIPE, text=True)
        try:
            self.assertEqual(proc.stdout.readline().strip(), "True")
            self.assertFalse(first.acquire())
        finally:
            proc.kill()
            proc.wait(timeout=60)
            proc.stdout.close()
        for _ in range(100):  # the OS frees it as the process ends; give it a moment
            if first.acquire():
                break
            time.sleep(0.1)
        else:
            self.fail("the dead process's lock was never freed")
        first.release()

    def test_a_second_launcher_does_nothing_while_one_lives(self):  # launcher_runs_beside_a_live_one
        holder = self.launch.LauncherLock(self.work / "launcher.lock")
        self.assertTrue(holder.acquire())
        try:
            stored = self.store(argv=["--model", "m"])
            for argv in (["--cycles", "3"], ["--resume"]):
                seen = self.main(argv, outcomes=[True] * 3)
                self.assertEqual((seen["code"], seen["calls"], seen["running"], seen["waited"]), (0, [], [], False))
            self.assertEqual(self.running(), stored)  # the live launcher's run is not touched
        finally:
            holder.release()

    def fresh_run(self):
        """A fresh start of four cycles whose third says stop (two idle sessions, a timeout, no inputs)."""
        self.env_line = "zq-x9-env-line-never-copied"
        (self.work / "snowball-founder.env").write_text(f"GITHUB_TOKEN={self.env_line}\n", encoding="utf-8")
        seen = self.main(["--cycles", "4", "--model", "m1", "--no-build", "--target", "target-x"],
                         outcomes=[True, True, False])
        self.assertEqual((seen["code"], seen["calls"]), (0, ["preflight"]))
        self.assertIsNone(self.running())  # the cycle said stop
        return seen

    def test_running_counts_down(self):  # running_not_counted_down running_forgets_the_idle_count
        first, _, third = running = self.fresh_run()["running"]
        self.assertEqual(set(first), {"argv", "cycles_left", "idle", "started", "updated"})
        self.assertEqual([r["cycles_left"] for r in running], [4, 3, 2])  # after each cycle, what is left
        self.assertEqual([r["idle"] for r in running], [0, 1, 2])  # two sessions without a push stay two
        self.assertEqual(third["started"], first["started"])

    def test_running_holds_the_options_and_no_secret(self):  # running_drops_a_flag
        seen = self.fresh_run()
        argv = seen["running"][0]["argv"]
        self.assertIn("--no-build", argv)
        for option in ("--resume", "--cycles", "--work", "--install-service", "--uninstall-service"):
            self.assertNotIn(option, argv)
        self.assertNotIn(self.env_line, json.dumps(seen["running"]))
        again = self.launch.build_parser().parse_args([*argv, "--cycles", "4", "--work", str(self.work)])
        self.assertEqual(vars(again), vars(seen["args"]))  # the stored options run the same launcher

    def test_a_start_by_hand_replaces_a_cut_run(self):  # fresh_start_keeps_a_cut_run
        self.store(argv=["--model", "old"])
        with self.assertRaises(SystemExit):  # the operator sees the failure; the old run is not resumed behind it
            self.main(["--cycles", "2"], outcomes=[True, True], preflight_fails=True)
        self.assertIsNone(self.running())
        self.store(argv=["--model", "old"], cycles_left=9)
        seen = self.main(["--cycles", "2", "--model", "new"], outcomes=[True, True])
        self.assertEqual([(r["cycles_left"], r["argv"][r["argv"].index("--model") + 1]) for r in seen["running"]],
                         [(2, "new"), (1, "new")])

    def test_each_deliberate_end_removes_running(self):  # running_kept_after_a_deliberate_stop
        ends = {"STOP before a cycle": ([], {}, True), "the cycle says stop": ([False], {}, False),
                "STOP while an outage is waited out": ([self.launch.GitHubUnavailable("down")],
                                                       {"stop_while_waiting": True}, False),
                "every cycle ran": ([True, True], {}, False)}
        for end, (outcomes, flags, stop) in ends.items():
            with self.subTest(end=end):
                (self.work / "STOP").unlink(missing_ok=True)
                intent = self.launch.Intent(self.work)
                intent.write(["--model", "m"], 2)
                if stop:
                    (self.work / "STOP").touch()
                seen = {"calls": [], "running": [], "idle": [], **flags}
                pilot = self.pilot_class(list(outcomes), seen)(self.work, "b", "r", "t")
                with mock.patch.object(self.launch, "say"):
                    self.launch.run_cycles(pilot, argparse.Namespace(cycles=2), intent)
                self.assertIsNone(self.running())

    def test_a_crash_leaves_running_and_ctrl_c_does_not(self):  # running_cleared_on_a_crash running_kept_after_ctrl_c
        with self.assertRaises(RuntimeError):
            self.main(["--cycles", "4", "--no-build"], outcomes=[True, RuntimeError("a bug escapes")])
        left = self.running()
        self.assertEqual((left["cycles_left"], left["idle"]), (3, 1))  # what --resume continues
        with self.assertRaises(KeyboardInterrupt):  # the operator's own stop, in the console
            self.main(["--cycles", "4", "--no-build"], outcomes=[True, KeyboardInterrupt()])
        self.assertIsNone(self.running())

    def test_resume_never_overrides_a_stop(self):  # resume_overrides_a_stop
        seen = self.main(["--resume"], outcomes=[True])  # nothing was running
        self.assertEqual((seen["code"], seen["calls"], seen["waited"]), (0, [], False))
        self.store()
        (self.work / "STOP").touch()  # stopped on purpose, then the machine went down: the stop stands
        seen = self.main(["--resume"], outcomes=[True] * 3)
        self.assertEqual((seen["code"], seen["calls"], seen["waited"], self.running()), (0, [], False, None))
        (self.work / "STOP").unlink()
        self.store(cycles_left=0)
        seen = self.main(["--resume"], outcomes=[True])
        self.assertEqual((seen["calls"], self.running()), ([], None))
        (self.work / "RUNNING").write_text('{"argv": ["--model"', encoding="utf-8")  # not a run
        seen = self.main(["--resume"], outcomes=[True])
        self.assertEqual(seen["calls"], [])
        self.assertTrue((self.work / "RUNNING").exists())  # left for the operator to read

    def resume_cut_run(self):
        """A run cut after one session without a push, three cycles left, resumed by the task."""
        self.stored = self.store(argv=["--model", "m9", "--no-build", "--target", "target-z"], cycles_left=3, idle=1)
        return self.main(["--resume", "--cycles", "50"], outcomes=[True, True, True])  # the stored run, not these

    def test_resume_keeps_the_idle_count(self):  # resume_restarts_the_idle_count
        self.assertEqual(self.resume_cut_run()["idle"][0], 1)  # one session without a push before the crash counts

    def test_resume_runs_the_stored_run(self):  # resume_forgets_the_cycles_left resume_drops_the_stored_options
        seen, stored = self.resume_cut_run(), self.stored
        args = seen["args"]
        self.assertEqual((seen["code"], seen["calls"], seen["waited"]), (0, ["preflight"], True))
        self.assertEqual((args.model, args.target, args.no_build, args.cycles, args.resume, args.work),
                         ("m9", "target-z", True, 3, True, self.work))
        self.assertEqual(len(seen["running"]), 3)
        self.assertEqual(seen["running"][0]["started"], stored["started"])
        self.assertIsNone(self.running())
        log = (self.work / "pilot-log.md").read_text(encoding="utf-8")
        self.assertIn("başlatıcı yeniden başladı (çökme/yeniden açılış sonrası): kalan 3 döngü", log)
        self.assertIn(stored["started"], log)

    def test_resume_waits_for_docker_and_github_and_a_stop_still_stands(self):
        stored = self.store(argv=["--no-build"])
        with self.assertRaises(SystemExit):  # docker never answered: the task's next trigger tries again
            self.main(["--resume"], outcomes=[True], ready=False)
        self.assertEqual(self.running(), stored)

        def stop_while_waiting(work):
            (work / "STOP").touch()
            return False
        seen = self.main(["--resume"], outcomes=[True], ready=stop_while_waiting)
        self.assertEqual((seen["code"], seen["calls"], self.running()), (0, [], None))

    def test_the_ready_wait_is_bounded(self):  # resume_wait_ignores_stop resume_wait_unbounded
        launch, clock, asked = self.launch, [0.0], []

        def sleep(seconds):
            clock[0] += seconds
            if clock[0] > 100 * launch.READY_WAIT_S:
                raise AssertionError("the wait has no end")

        def check(answers):
            def fake(*cmd, **kw):
                asked.append(cmd[:2])
                if isinstance(answers.get(cmd[0]), BaseException):
                    raise answers[cmd[0]]
                return subprocess.CompletedProcess(cmd, 0 if answers.get(cmd[0], 0) <= clock[0] else 1, b"", b"")
            return fake

        def wait(answers):
            clock[0], asked[:] = 0.0, []
            with mock.patch.object(launch, "run", check(answers)), mock.patch.object(launch.time, "sleep", sleep), \
                    mock.patch.object(launch.time, "monotonic", lambda: clock[0]):
                return launch.wait_ready(self.work)

        self.assertTrue(wait({"docker": 0, "gh": 0}))
        self.assertEqual(asked, [("docker", "info"), ("gh", "auth")])
        self.assertTrue(wait({"docker": 120, "gh": 0}))  # docker came up two minutes after the logon
        self.assertGreaterEqual(clock[0], 120)
        self.assertFalse(wait({"docker": 10 ** 9, "gh": 0}))  # it never does
        self.assertLessEqual(clock[0], launch.READY_WAIT_S + launch.READY_RETRY_S)
        self.assertFalse(wait({"docker": FileNotFoundError("docker"), "gh": 0}))  # not on PATH yet is not ready
        (self.work / "STOP").touch()
        self.assertFalse(wait({"docker": 0, "gh": 0}))
        self.assertEqual(asked, [])

    TASK_NS = {"t": "http://schemas.microsoft.com/windows/2004/02/mit/task"}

    def task(self):
        """The Scheduled Task's XML, read as schtasks reads the file (UTF-16)."""
        import xml.etree.ElementTree as ET
        text = self.launch.task_xml(r"C:\Python312\python.exe", r"J:\İCLOUD\a b\seed\founder\launch.py",
                                    r"F:\snowball-work", r"J:\İCLOUD\a b", r"PC\op & co", "2026-11-02T10:00:00")
        return ET.fromstring(text.encode("utf-16"))

    def test_the_task_runs_the_resume(self):  # service_task_without_resume service_task_only_at_logon
        launch, task, ns = self.launch, self.task(), self.TASK_NS
        get = lambda path: task.find(path, ns).text  # noqa: E731
        self.assertEqual(get("t:Actions/t:Exec/t:Command"), r"C:\Python312\python.exe")
        self.assertEqual(get("t:Actions/t:Exec/t:Arguments"),
                         r'-u "J:\İCLOUD\a b\seed\founder\launch.py" --resume --work F:\snowball-work')
        self.assertEqual(get("t:Actions/t:Exec/t:WorkingDirectory"), r"J:\İCLOUD\a b")
        triggers = task.find("t:Triggers", ns)
        self.assertEqual(sorted(t.tag.split("}")[1] for t in triggers), ["LogonTrigger", "TimeTrigger"])
        for trigger in triggers:
            self.assertEqual(trigger.find("t:Repetition/t:Interval", ns).text, "PT15M")
            self.assertIsNone(trigger.find("t:Repetition/t:Duration", ns))  # indefinitely
        self.assertEqual(get("t:Triggers/t:LogonTrigger/t:UserId"), r"PC\op & co")
        self.assertEqual(get("t:Triggers/t:TimeTrigger/t:StartBoundary"), "2026-11-02T10:00:00")
        self.assertEqual((get("t:Principals/t:Principal/t:LogonType"), get("t:Principals/t:Principal/t:RunLevel")),
                         ("InteractiveToken", "LeastPrivilege"))  # the user's own session: no admin, no password
        self.assertEqual(launch.schtasks_argv(r"C:\t\task.xml"),
                         ["schtasks", "/Create", "/TN", launch.TASK_NAME, "/XML", r"C:\t\task.xml", "/F"])
        self.assertEqual(launch.schtasks_argv(None), ["schtasks", "/Delete", "/TN", launch.TASK_NAME, "/F"])

    def test_the_task_never_times_out_or_doubles(self):  # service_task_time_limited service_task_parallel_instances
        settings = {s.tag.split("}")[1]: s.text for s in self.task().find("t:Settings", self.TASK_NS)}
        self.assertEqual(settings["ExecutionTimeLimit"], "PT0S")  # the scheduler's 72 h default would kill a long run
        self.assertEqual(settings["MultipleInstancesPolicy"], "IgnoreNew")  # a trigger while it runs starts nothing
        self.assertEqual((settings["DisallowStartIfOnBatteries"], settings["StopIfGoingOnBatteries"]),
                         ("false", "false"))

    def test_install_and_uninstall_call_schtasks_and_nothing_else(self):
        launch, calls = self.launch, []

        def fake_run(*argv, **kw):
            sent = Path(argv[argv.index("/XML") + 1]).read_bytes() if "/XML" in argv else b""
            calls.append((list(argv), sent))
            return subprocess.CompletedProcess(argv, 0, b"SUCCESS", b"")
        with mock.patch.object(launch, "run", fake_run), mock.patch.object(launch, "say"), \
                mock.patch.object(launch.shutil, "which", return_value=r"C:\Windows\System32\schtasks.exe"):
            self.assertEqual(launch.main(["--install-service", "--work", str(self.work)]), 0)
            self.assertEqual(launch.main(["--uninstall-service"]), 0)
        (install, sent), (uninstall, _) = calls
        self.assertEqual(install[:5], ["schtasks", "/Create", "/TN", launch.TASK_NAME, "/XML"])
        self.assertTrue(sent.startswith(b"\xff\xfe"))  # UTF-16, as its declaration says
        task = sent.decode("utf-16")
        self.assertIn(f"<Command>{sys.executable}</Command>", task)
        self.assertIn("--resume --work", task)
        self.assertEqual(uninstall, launch.schtasks_argv(None))
        self.assertFalse((self.work / "launcher.lock").exists())  # no launcher ran
        with mock.patch.object(launch, "run", fake_run), mock.patch.object(launch.shutil, "which", return_value=None):
            with self.assertRaises(SystemExit):  # not Windows: no task, nothing run
                launch.main(["--install-service"])
        self.assertEqual(len(calls), 2)



# ---- E508: capsule containment --------------------------------------------------------------------------------------
def load_egress():
    """The capsule's relay (`seed/founder/egress.py`, E508): the operator's code, run beside the capsule."""
    if "founder_egress" not in sys.modules:  # its dataclasses look their module up there
        spec = importlib.util.spec_from_file_location("founder_egress", FOUNDER / "egress.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
    return sys.modules["founder_egress"]


ALLOWED_REPO = "o/brain"
# What a contained capsule must never reach through the relay (E508): the referee and the seed by path and by name
# case, a longer name that starts with the brain's, the raw, codeload and objects hosts, the REST API outside the
# brain, an IP literal, the cloud metadata address, the relay itself, encoded and dotted escapes. Each with the reason
# the relay records.
FORBIDDEN = (
    ("CONNECT", "github.com:443", "connect_not_allowed"),
    ("CONNECT", "raw.githubusercontent.com:443", "connect_not_allowed"),
    ("CONNECT", "codeload.github.com:443", "connect_not_allowed"),
    ("CONNECT", "objects.githubusercontent.com:443", "connect_not_allowed"),
    ("CONNECT", "api.github.com:443", "connect_not_allowed"),
    ("CONNECT", "140.82.121.3:443", "connect_not_allowed"),
    ("CONNECT", "[2606:50c0:8000::153]:443", "connect_not_allowed"),
    ("CONNECT", "api.anthropic.com:80", "connect_not_allowed"),
    ("CONNECT", "api.anthropic.com.evil.example:443", "connect_not_allowed"),
    ("CONNECT", "api.anthropic.com.:443", "connect_not_allowed"),
    ("CONNECT", "statsig.anthropic.com:443", "connect_not_allowed"),
    ("CONNECT", "claude.ai:443", "connect_not_allowed"),
    ("CONNECT", "registry.npmjs.org:443", "connect_not_allowed"),
    ("CONNECT", "169.254.169.254:80", "connect_not_allowed"),
    ("CONNECT", "relay:3128", "connect_not_allowed"),
    ("CONNECT", "api.anthropic.com", "connect_target"),
    ("GET", "http://github.com/o/referee", "absolute_form"),
    ("GET", "http://raw.githubusercontent.com/o/referee/main/vectors/vectors.json", "absolute_form"),
    ("GET", "/git/o/referee.git/info/refs?service=git-upload-pack", "repo_not_allowed"),
    ("GET", "/git/o/snowball-mcp.git/info/refs?service=git-upload-pack", "repo_not_allowed"),
    ("POST", "/git/o/referee.git/git-upload-pack", "repo_not_allowed"),
    ("GET", "/git/O/Referee/info/refs?service=git-upload-pack", "repo_not_allowed"),
    ("GET", "/git/o/brain-referee.git/info/refs?service=git-upload-pack", "repo_not_allowed"),
    ("GET", "/git/o/brain.git/archive/main.zip", "git_endpoint"),
    ("GET", "/git/o/brain.git/info/lfs/objects/batch", "git_endpoint"),
    ("GET", "/git/o/brain.git/info/refs", "git_endpoint"),
    ("GET", "/git/o/brain.git/info/refs?service=git-upload-archive", "git_endpoint"),
    ("POST", "/git/o/brain.git/info/refs?service=git-upload-pack", "git_endpoint"),
    ("GET", "/git/o/brain.git/../referee.git/info/refs?service=git-upload-pack", "unsafe_path"),
    ("GET", "/api/repos/o/referee/contents/vectors/vectors.json", "repo_not_allowed"),
    ("GET", "/api/repos/O/REFEREE/contents/vectors", "repo_not_allowed"),
    ("GET", "/api/repos/o/snowball-mcp/tarball/main", "repo_not_allowed"),
    ("GET", "/api/repos/o/brain-referee/contents/vectors", "repo_not_allowed"),
    ("GET", "/api/repos/o/brainx", "repo_not_allowed"),
    ("GET", "/api/repos/o/brain/../referee/contents", "unsafe_path"),
    ("GET", "/api/repos/o/brain/%2e%2e/referee/contents", "unsafe_path"),
    ("GET", "/api/repos/o/brain%2F..%2Freferee", "unsafe_path"),
    ("GET", "/api/repos/o/brain/contents/%00", "unsafe_path"),
    ("GET", "/api/repos/o/brain/contents/%zz", "unsafe_path"),
    ("GET", "/api/repos/o/brain\\..\\referee", "unsafe_path"),
    ("GET", "/api/repos/o/brain/contents//x", "unsafe_path"),
    ("GET", "/api/repositories/1/contents", "no_route"),
    ("GET", "/api/user", "no_route"),
    ("GET", "/api/search/code?q=repo:o/referee", "no_route"),
    ("GET", "/o/referee/raw/main/vectors/vectors.json", "no_route"),
    ("TRACE", "/api/repos/o/brain", "method"),
    ("OPTIONS", "/api/repos/o/brain/contents", "method"),
)


class EgressDecisionTest(unittest.TestCase):
    """E508: the relay's whole rule is `decide`, before any byte goes upstream."""

    def setUp(self):
        self.egress = load_egress()
        self.policy = self.egress.policy([ALLOWED_REPO])

    def test_every_forbidden_target_is_denied_with_its_reason(self):  # relay_allows_any_repo relay_prefix_match_loose
        self.assertGreaterEqual(len(FORBIDDEN), 30)
        for method, target, reason in FORBIDDEN:
            decision = self.egress.decide(self.policy, method, target)
            self.assertEqual((decision.allow, decision.reason), (False, reason), f"{method} {target}")

    def test_the_brain_alone_passes_and_the_upstream_comes_from_the_route(self):
        decide = self.egress.decide
        cases = {
            ("GET", "/git/o/brain.git/info/refs?service=git-upload-pack"):
                ("https://github.com", "/o/brain.git/info/refs?service=git-upload-pack", "basic"),
            ("GET", "/git/O/Brain/info/refs?service=git-receive-pack"):  # GitHub's names have no case
                ("https://github.com", "/o/brain.git/info/refs?service=git-receive-pack", "basic"),
            ("POST", "/git/o/brain.git/git-upload-pack"):
                ("https://github.com", "/o/brain.git/git-upload-pack", "basic"),
            ("POST", "/git/o/brain.git/git-receive-pack"):
                ("https://github.com", "/o/brain.git/git-receive-pack", "basic"),
            ("GET", "/api/repos/o/brain"): ("https://api.github.com", "/repos/o/brain", "bearer"),
            ("PATCH", "/api/repos/o/brain/issues/1?x=a%2Fb"):
                ("https://api.github.com", "/repos/o/brain/issues/1?x=a%2Fb", "bearer"),
        }
        for (method, target), (upstream, path, auth) in cases.items():
            decision = decide(self.policy, method, target)
            self.assertEqual((decision.allow, decision.upstream, decision.path, decision.auth),
                             (True, upstream, path, auth), target)
        model = decide(self.policy, "CONNECT", "API.Anthropic.com:443")
        self.assertEqual((model.allow, model.upstream), (True, "api.anthropic.com:443"))
        self.assertEqual(self.egress.MODEL_HOSTS, (("api.anthropic.com", 443),))  # the model's API and nothing else

    def test_a_policy_names_real_repositories(self):
        self.assertEqual(self.egress.policy(["O/Brain", "o/brain"]).repos, ("o/brain",))
        for bad in ([], ["brain"], ["o/brain/x"], ["o/.."], ["-o/brain"], ["o/br ain"]):
            with self.assertRaises(ValueError, msg=bad):
                self.egress.policy(bad)

    def test_the_token_is_read_from_its_line_and_never_elsewhere(self):
        path = Path(tempfile.mkdtemp()) / "relay.env"
        path.write_text("OTHER=1\nGITHUB_TOKEN=gh-tok\r\nGITHUB_TOKEN=second\n", encoding="utf-8")
        self.assertEqual(self.egress.read_token(path), "gh-tok")
        path.write_text("GITHUB_TOKEN=\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.egress.read_token(path)
        self.assertEqual(self.egress.auth_header("basic", "t"), "Basic eC1hY2Nlc3MtdG9rZW46dA==")
        self.assertEqual(self.egress.auth_header("bearer", "t"), "Bearer t")


class FakeGitHub:
    """github.com and api.github.com on 127.0.0.1 for the relay's tests: git smart-HTTP served by `git http-backend`
    over bare repositories in root, any other path answered 200 with what was asked. Every request it gets is recorded
    with the Authorization header it came with, so a test sees what reached "GitHub" and with which credentials."""

    def __init__(self, root: Path):
        self.root, self.seen = root, []
        fake = self
        egress = load_egress()

        class Handler(http.server.BaseHTTPRequestHandler):
            def _serve(self):
                body = b"".join(egress.read_body(self.rfile, self.headers) or [])
                path, _, query = self.path.partition("?")
                fake.seen.append({"method": self.command, "path": self.path,
                                  "authorization": self.headers.get("Authorization"),
                                  "cookie": self.headers.get("Cookie")})
                if not path.endswith(("/info/refs", "/git-upload-pack", "/git-receive-pack")):
                    self._reply(200, {"Content-Type": "application/json"}, json.dumps({"path": self.path}).encode())
                    return
                env = {**os.environ, "GIT_PROJECT_ROOT": str(fake.root), "GIT_HTTP_EXPORT_ALL": "1",
                       "PATH_INFO": path, "QUERY_STRING": query, "REQUEST_METHOD": self.command,
                       "CONTENT_TYPE": self.headers.get("Content-Type") or "", "CONTENT_LENGTH": str(len(body)),
                       "REMOTE_USER": "relay", "REMOTE_ADDR": "127.0.0.1",
                       "HTTP_CONTENT_ENCODING": self.headers.get("Content-Encoding") or "",
                       "GIT_PROTOCOL": self.headers.get("Git-Protocol") or ""}
                out = subprocess.run(["git", "http-backend"], input=body, env=env, capture_output=True,
                                     check=True).stdout
                ends = [(out.find(sep), sep) for sep in (b"\r\n\r\n", b"\n\n") if sep in out]
                head, _, payload = out.partition(min(ends)[1])  # the CGI header block ends at the first blank line
                headers, status = {}, 200
                for line in head.decode("latin-1").splitlines():
                    key, _, value = line.partition(":")
                    if key.lower() == "status":
                        status = int(value.split()[0])
                    elif key:
                        headers[key] = value.strip()
                self._reply(status, headers, payload)

            def _reply(self, status, headers, payload):
                self.send_response(status)
                for key, value in headers.items():
                    self.send_header(key, value)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            do_GET = do_POST = do_PATCH = do_PUT = do_DELETE = do_HEAD = _serve

            def log_message(self, *args):
                pass

        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()


class RelayLiveTest(unittest.TestCase):
    """E508: the relay itself, over real sockets on 127.0.0.1, in front of a fake GitHub and an echo server standing in
    for the model's API. Forbidden requests never reach either, each is in the log as denied; the brain is cloned and
    pushed through it with the relay's token alone."""

    TOKEN = "relay-only-" + "t" * 20  # made up; built so the repository's own secret scan sees no literal

    def setUp(self):
        self.egress = load_egress()
        self.tmp = Path(tempfile.mkdtemp())
        self.github = FakeGitHub(self.tmp / "repos")
        self.echo = socket.create_server(("127.0.0.1", 0))
        threading.Thread(target=self._echo, daemon=True).start()
        policy = self.egress.policy([ALLOWED_REPO], git_upstream=self.github.url, api_upstream=self.github.url,
                                    connect=(("127.0.0.1", self.echo.getsockname()[1]),))
        self.log = self.tmp / "log" / "egress.jsonl"
        self.relay = self.egress.Relay(("127.0.0.1", 0), policy, self.TOKEN, self.log)
        self.port = self.relay.server_address[1]
        threading.Thread(target=self.relay.serve_forever, daemon=True).start()

    def tearDown(self):
        self.relay.shutdown()
        self.relay.server_close()
        self.github.close()
        self.echo.close()

    def _echo(self):
        while True:
            try:
                conn, _ = self.echo.accept()
            except OSError:
                return
            with conn:
                while data := conn.recv(4096):
                    conn.sendall(data)

    def ask(self, method: str, target: str, extra: str = "") -> bytes:
        """The relay's whole answer to one raw request."""
        with socket.create_connection(("127.0.0.1", self.port), timeout=30) as conn:
            conn.sendall(f"{method} {target} HTTP/1.1\r\nHost: relay\r\n{extra}Content-Length: 0\r\n\r\n".encode())
            chunks = []
            while data := conn.recv(65536):
                chunks.append(data)
        return b"".join(chunks)

    def rows(self) -> list[dict]:
        return [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]

    def test_nothing_forbidden_goes_out_each_logged(self):
        # relay_deny_not_logged relay_allows_any_repo relay_denied_still_forwarded relay_git_endpoints_any
        for method, target, _ in FORBIDDEN:
            self.assertTrue(self.ask(method, target).startswith(b"HTTP/1.1 403 "), f"{method} {target}")
        self.assertEqual(self.github.seen, [])  # not one byte went upstream
        rows = self.rows()
        self.assertEqual([(r["method"], r["target"], r["decision"], r["reason"]) for r in rows],
                         [(m, t, "deny", reason) for m, t, reason in FORBIDDEN])
        self.assertTrue(all(set(r) == {"ts", "peer", "method", "target", "decision", "reason"} for r in rows))
        self.assertTrue(self.ask("GET", "/api/repos/o/brain").startswith(b"HTTP/1.1 200 "))  # the control
        self.assertEqual(self.rows()[-1]["decision"], "allow")

    def test_a_malformed_request_is_logged_and_refused(self):
        with socket.create_connection(("127.0.0.1", self.port), timeout=30) as conn:
            conn.sendall(b"NONSENSE\r\n\r\n")
            answer = b""
            while data := conn.recv(65536):  # to the close: the row is written before the relay closes
                answer += data
        self.assertIn(b"Error code: 400", answer)  # read as HTTP/0.9: the error page without a status line
        self.assertEqual([(r["decision"], r["reason"]) for r in self.rows()], [("deny", "malformed")])

    def test_the_relays_token_replaces_the_clients_and_no_cookie_passes(self):  # relay_forwards_client_auth
        answer = self.ask("GET", "/api/repos/O/brain/contents/a.md?ref=main",
                          "Authorization: Bearer capsule-made-up\r\nCookie: s=1\r\n")
        self.assertTrue(answer.startswith(b"HTTP/1.1 200 "), answer[:60])
        self.assertEqual(self.github.seen, [{"method": "GET", "path": "/repos/o/brain/contents/a.md?ref=main",
                                             "authorization": f"Bearer {self.TOKEN}", "cookie": None}])

    def test_the_model_tunnel_carries_bytes_both_ways(self):
        with socket.create_connection(("127.0.0.1", self.port), timeout=30) as conn:
            conn.sendall(f"CONNECT 127.0.0.1:{self.echo.getsockname()[1]} HTTP/1.1\r\nHost: x\r\n\r\n".encode())
            head = b""
            while b"\r\n\r\n" not in head:
                head += conn.recv(1)
            self.assertTrue(head.startswith(b"HTTP/1.1 200 "), head)
            conn.sendall(b"tls bytes the relay cannot read")
            self.assertEqual(conn.recv(4096), b"tls bytes the relay cannot read")
        self.assertEqual([r["decision"] for r in self.rows()], ["allow"])

    def test_the_brain_is_cloned_and_pushed_through_the_relay_alone(self):
        bare = self.tmp / "repos" / "o" / "brain.git"
        bare.parent.mkdir(parents=True)
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(bare)], check=True)
        seed = self.tmp / "seed"
        make_repo(seed, {"a.txt": "one\n"})
        sh(seed, "git", "push", "-q", str(bare), "main")
        home = self.tmp / "home"
        home.mkdir()
        env = {**os.environ, "HOME": str(home), "GIT_CONFIG_NOSYSTEM": "1", "GIT_TERMINAL_PROMPT": "0",
               "GIT_CONFIG_GLOBAL": str(home / ".gitconfig")}
        relay = f"http://127.0.0.1:{self.port}"
        # As the contained entrypoint does it: https://github.com/ URLs are rewritten to the relay.
        subprocess.run(["git", "config", "--global", f"url.{relay}/git/.insteadOf", "https://github.com/"],
                       env=env, check=True)
        clone = self.tmp / "clone"
        git = lambda *a: subprocess.run(["git", *a], env=env, check=True, capture_output=True)  # noqa: E731
        git("clone", "-q", "https://github.com/o/brain.git", str(clone))
        self.assertEqual((clone / "a.txt").read_text(encoding="utf-8"), "one\n")
        git("-C", str(clone), "config", "user.email", "f@example.invalid")
        git("-C", str(clone), "config", "user.name", "f")
        (clone / "b.bin").write_bytes(os.urandom(3 << 20))  # past git's 1 MiB post buffer: a chunked push body
        git("-C", str(clone), "add", "-A")
        git("-C", str(clone), "commit", "-q", "-m", "work")
        git("-C", str(clone), "-c", "http.extraHeader=Authorization: Basic Y2Fwc3VsZTpub3Bl", "push", "-q",
            "origin", "main")
        head = git("-C", str(clone), "rev-parse", "HEAD").stdout.strip()
        self.assertEqual(sh(bare, "git", "rev-parse", "main"), head.decode())
        basic = "Basic " + base64.b64encode(f"x-access-token:{self.TOKEN}".encode()).decode()
        self.assertTrue(self.github.seen)
        self.assertEqual({s["authorization"] for s in self.github.seen}, {basic})  # never the capsule's header
        self.assertIn(("POST", "/o/brain.git/git-receive-pack"), {(s["method"], s["path"]) for s in self.github.seen})
        self.assertEqual({r["decision"] for r in self.rows()}, {"allow"})
        with self.assertRaises(subprocess.CalledProcessError):  # and nothing else: the control
            git("clone", "-q", "https://github.com/o/referee.git", str(self.tmp / "other"))
        self.assertEqual(self.rows()[-1]["decision"], "deny")


class ContainedCapsuleTest(unittest.TestCase):
    """E508: the launcher's contained egress. The capsule sits on an internal network with the relay's address, holds
    the model's token alone, and the transcript is written on the host from its stdout. Open egress stays as it was."""

    STAMP = "20261102T000000Z"

    def setUp(self):
        self.launch = load_launch()
        self.work = Path(tempfile.mkdtemp())
        self.pilot = self.launch.Pilot(self.work, "o/brain", "o/referee", "target", "contained")
        self.pilot.seed = "a" * 40
        self.argv = self.pilot.capsule_argv(self.STAMP, "claude-opus-5-5", 200, 50)

    def mounts(self, argv) -> dict[str, tuple[Path, str]]:
        out = {}
        for i, arg in enumerate(argv):
            if arg == "--mount":
                spec = dict(part.split("=", 1) if "=" in part else (part, "") for part in argv[i + 1].split(","))
                out[spec["dst"]] = (Path(spec["src"]), "readonly" if "readonly" in spec else "rw")
        return out

    def env(self, argv) -> dict[str, str]:
        return dict(argv[i + 1].split("=", 1) for i, a in enumerate(argv) if a == "-e")

    def test_the_capsule_is_on_the_internal_network_behind_the_relay(self):  # capsule_default_network
        self.assertEqual(self.argv[self.argv.index("--network") + 1], self.launch.CAPSULE_NETWORK)
        self.assertEqual([a for a in self.argv if a.startswith("--net")], ["--network"])
        env = self.env(self.argv)
        self.assertEqual((env["RELAY"], env["HTTPS_PROXY"], env["NO_PROXY"]),
                         ("http://relay:3128", "http://relay:3128", "relay"))
        relay = self.pilot.relay_argv(self.STAMP)
        self.assertEqual([relay[i + 1] for i, a in enumerate(relay) if a == "--network"],
                         [f"name={self.launch.CAPSULE_NETWORK},alias=relay", "bridge"])  # its one route out
        opened = self.launch.Pilot(self.work, "o/brain", "o/referee", "target")
        opened.seed = "a" * 40
        self.assertFalse(any(a.startswith("--net") or a.startswith("RELAY") or "PROXY" in a
                             for a in opened.capsule_argv(self.STAMP, "m", 1, 1)))  # open egress: as before
        with self.assertRaises(ValueError):
            self.launch.Pilot(self.work, "o/brain", "o/referee", "target", "half")

    def test_the_github_token_is_the_relays_alone(self):  # token_in_capsule_env relay_token_check_removed
        capsule, relay = self.mounts(self.argv), self.mounts(self.pilot.relay_argv(self.STAMP))
        self.assertEqual(capsule["/run/secrets/founder.env"], (self.work / "snowball-capsule.env", "readonly"))
        self.assertEqual(relay["/run/secrets/relay.env"], (self.work / "snowball-relay.env", "readonly"))
        secrets = {self.work / "snowball-founder.env", self.work / "snowball-relay.env"}
        self.assertEqual({src for src, _ in capsule.values()} & secrets, set())
        self.assertFalse(any(re.search(r"TOKEN|KEY|SECRET", k) for k in self.env(self.argv)))
        # The relay sees its code, its token and its log: none of the capsule's inputs.
        self.assertEqual(set(relay), {"/opt/relay/egress.py", "/run/secrets/relay.env", "/log"})
        self.assertEqual(relay["/opt/relay/egress.py"][1], "readonly")
        # The entrypoint refuses a GitHub token in a contained capsule, and git goes through the relay's address.
        entry = (FOUNDER / "entrypoint.sh").read_text(encoding="utf-8")
        branch = entry[entry.index('if [ -n "${RELAY:-}" ]; then'):entry.index("\nelse\n")]
        self.assertIn('if [ -n "$(secret GITHUB_TOKEN)" ]; then', branch)
        self.assertIn("exit 64", branch)
        self.assertIn('url."$RELAY/git/".insteadOf "https://github.com/"', branch)
        self.assertNotIn("extraheader", branch)

    def test_the_relay_runs_the_capsules_pinned_python_locked_down(self):
        relay = self.pilot.relay_argv(self.STAMP)
        dockerfile = (FOUNDER / "Dockerfile").read_text(encoding="utf-8")
        self.assertEqual(self.launch.relay_image(), re.findall(r"(?m)^FROM (\S+)", dockerfile)[-1])
        self.assertRegex(self.launch.relay_image(), r"^docker\.io/library/python:3\.12-slim@sha256:[0-9a-f]{64}$")
        self.assertIn(self.launch.relay_image(), relay)
        for flag in ("--read-only", "--rm", "--detach"):
            self.assertIn(flag, relay)
        self.assertEqual(relay[relay.index("--cap-drop") + 1], "ALL")
        self.assertEqual(relay[relay.index("--security-opt") + 1], "no-new-privileges")
        self.assertNotIn("--privileged", relay)
        self.assertEqual(relay[relay.index("--repo") + 1], "o/brain")  # the brain alone
        self.assertEqual(relay.count("--repo"), 1)
        self.assertEqual(relay[relay.index("--listen") + 1], "relay:3128")  # its capsule-network address, not 0.0.0.0
        for argv in (relay, self.argv):
            for i, arg in enumerate(argv):
                if arg == "--mount":
                    src = re.search(r"src=([^,]+)", argv[i + 1]).group(1)
                    self.assertTrue(Path(src).is_relative_to(self.work), src)

    @staticmethod
    def network(internal=True, ipv6=False, **options) -> bytes:
        """What `docker network inspect --format {{json .}}` prints for the capsule network (docker 28.4's fields, as
        the launcher's own create made it: `--ipv6=false` leaves no enable_ipv6 option, EnableIPv6 says it)."""
        opts = {"com.docker.network.bridge.gateway_mode_ipv4": "isolated", "com.docker.network.enable_ipv4": "true"}
        opts.update(options)
        state = {"Name": "snowball_capsule", "Driver": "bridge", "Internal": internal, "EnableIPv6": ipv6,
                 "Options": {k: v for k, v in opts.items() if v is not None}}
        return json.dumps({k: v for k, v in state.items() if v is not None}).encode() + b"\n"

    def network_problems(self, states):
        """network_problems against a fake docker whose `network inspect` prints states in turn (None: missing)."""
        calls = []

        def run(*argv, **kw):
            calls.append(argv)
            out = states.pop(0) if argv[:3] == ("docker", "network", "inspect") else b""
            return subprocess.CompletedProcess(argv, 0 if out is not None else 1, out or b"", b"")
        with mock.patch.object(self.launch, "run", run):
            found = self.pilot.network_problems()
        return found, [c for c in calls if c[:3] == ("docker", "network", "create")]

    def test_a_network_with_a_route_out_is_refused_never_used(self):  # capsule_network_not_internal
        made_one = [("docker", "network", "create", "--internal", "--ipv6=false", "-o",
                     "com.docker.network.bridge.gateway_mode_ipv4=isolated", "snowball_capsule")]
        for states, problems, made in (([self.network()], 0, []), ([None, self.network()], 0, made_one),
                                       ([self.network(internal=False)], 1, []), ([None, None], 1, made_one),
                                       ([b"not json\n", b"not json\n"], 1, made_one)):  # create fails: it exists
            found, created = self.network_problems(list(states))
            self.assertEqual(len(found), problems, (states, found))
            self.assertEqual(created, made, states)

    def test_an_internal_network_whose_gateway_reaches_the_host_is_refused(self):
        # capsule_gateway_not_isolated capsule_ipv6_allowed
        """E508, measured on docker 28.4 (2026-11-02): from a plain `--internal` network a container connected to a
        service listening on 0.0.0.0 in the docker host's own namespace, through the network's gateway address; with
        `gateway_mode_ipv4=isolated` the bridge has no host address and the same connect was refused. An internal
        network without it, or with IPv6 (or not saying), is refused like one with a route out, and never changed."""
        for kw in ({"com.docker.network.bridge.gateway_mode_ipv4": None},
                   {"com.docker.network.bridge.gateway_mode_ipv4": "nat"},
                   {"com.docker.network.bridge.gateway_mode_ipv4": "routed"}, {"ipv6": True}, {"ipv6": None}):
            found, created = self.network_problems([self.network(**kw)])
            self.assertEqual(len(found), 1, kw)
            self.assertIn("isolated gateway and no IPv6", found[0])
            self.assertEqual(created, [], kw)

    def test_contained_preflight_wants_both_secret_files_and_not_the_open_one(self):
        def problems(pilot):
            with mock.patch.object(self.launch, "run",
                                   return_value=subprocess.CompletedProcess([], 1, b"", b"")), \
                    self.assertRaises(SystemExit) as stop:
                pilot.preflight()
            return str(stop.exception)
        text = problems(self.pilot)
        self.assertIn("snowball-capsule.env is missing", text)
        self.assertIn("snowball-relay.env is missing", text)
        self.assertNotIn("snowball-founder.env", text)
        opened = self.launch.Pilot(self.work, "o/brain", "o/referee", "target")
        self.assertIn("snowball-founder.env is missing", problems(opened))

    def fake_capsule(self, stdout: bytes, tamper: bytes, rc: int = 0, timeout: bool = False):
        """subprocess.run as docker would run the capsule: stdout into the launcher's file, and the capsule writing
        into everything it has mounted read-write (its /work/logs), the Founder's copy of the stream included."""
        seen = {}
        stream, timed_out = stdout, timeout

        def run(cmd, stdout=None, stderr=None, timeout=None, check=False):
            seen["cmd"] = cmd
            stdout.write(stream)
            stdout.flush()
            for src, mode in self.mounts(cmd).values():  # then the Founder edits what it can reach
                if mode == "rw":
                    src.mkdir(parents=True, exist_ok=True)
                    (src / f"session-{self.STAMP}.jsonl").write_bytes(tamper)
            if timed_out:
                raise subprocess.TimeoutExpired(cmd, timeout)
            return subprocess.CompletedProcess(cmd, rc, None, b"git noise\nfounder_session stamp=x claude_exit=0\n")
        return run, seen

    STREAM = (json.dumps({"type": "system", "subtype": "init", "claude_code_version": "2.1.293", "model": "m"}) + "\n"
              + json.dumps({"type": "result", "subtype": "success", "num_turns": 3, "total_cost_usd": 0.5,
                            "result": "done"}) + "\n").encode()

    def test_the_transcript_is_the_capsules_stdout_on_the_host_and_its_hash_holds(self):
        # transcript_in_logs_mount transcript_hash_not_recorded
        pilot = self.launch.Pilot(self.work, "o/brain", "o/referee", "target")  # open egress: the record is the same
        pilot.seed = "a" * 40
        forged = json.dumps({"type": "result", "num_turns": 99, "total_cost_usd": 0.0, "subtype": "success"}).encode()
        fake, seen = self.fake_capsule(self.STREAM, forged + b"\n")
        with mock.patch.object(self.launch.subprocess, "run", fake):
            out = pilot.session(self.STAMP, "m", 1, 1, 60)
        record = pilot.transcript(self.STAMP)
        self.assertEqual(record.read_bytes(), self.STREAM)  # what the capsule wrote into its mounts changed nothing
        for src, _ in self.mounts(seen["cmd"]).values():
            self.assertFalse(record.is_relative_to(src), src)  # no mount of the capsule reaches the record
        digest = hashlib.sha256(self.STREAM).hexdigest()
        self.assertEqual(out["transcript_sha256"], digest)
        self.assertEqual(record.with_name(record.name + ".sha256").read_text(encoding="utf-8"),
                         f"{digest}  session-{self.STAMP}.jsonl\n")
        self.assertEqual((out["turns"], out["cost_usd"], out["cli_version"]), (3, 0.5, "2.1.293"))  # read from it
        self.assertEqual((out["line"], out["egress"]), ("founder_session stamp=x claude_exit=0", "open"))
        self.assertNotIn("egress_denied", out)  # open egress: nothing counts refusals
        self.assertEqual(out["transcript_results"], 1)
        # What the capsule can do (measured: a process of its user writes to /proc/1/fd/N, the container's stdout):
        # append a line. The record keeps every line the CLI wrote; the second `result` is counted for the report.
        fake, _ = self.fake_capsule(self.STREAM + forged + b"\n", b"")
        with mock.patch.object(self.launch.subprocess, "run", fake):
            out = pilot.session(self.STAMP, "m", 1, 1, 60)
        self.assertTrue(record.read_bytes().startswith(self.STREAM))
        self.assertEqual(out["transcript_results"], 2)

    def test_a_contained_session_runs_between_its_relays_start_and_stop(self):  # relay_left_running
        order = []
        log = self.pilot.session_logs(self.STAMP) / "relay" / "log" / "egress.jsonl"

        def run(*argv, **kw):
            order.append(argv[:2] if argv[1] not in ("run", "stop") else
                         ("docker", "run", argv[argv.index("--name") + 1]) if argv[1] == "run" else
                         ("docker", "stop", argv[-1]))
            if argv[:2] == ("docker", "logs"):
                return subprocess.CompletedProcess(argv, 0, b"relay listening on 0.0.0.0:3128 for o/brain\n", b"")
            return subprocess.CompletedProcess(argv, 0, b"id\n", b"")
        for timeout in (False, True):
            order.clear()
            fake, _ = self.fake_capsule(self.STREAM, b"", timeout=timeout)

            def capsule(cmd, **kw):
                order.append(("capsule",))
                log.write_text("\n".join(json.dumps(r) for r in (
                    {"decision": "allow", "method": "CONNECT", "target": "api.anthropic.com:443", "reason": "ok"},
                    {"decision": "deny", "method": "GET", "target": "/api/repos/o/referee",
                     "reason": "repo_not_allowed"},
                )) + "\nnot json\n", encoding="utf-8")
                return fake(cmd, **kw)
            with mock.patch.object(self.launch, "run", run), \
                    mock.patch.object(self.launch.subprocess, "run", capsule), \
                    mock.patch.object(self.launch.time, "sleep"):
                out = self.pilot.session(self.STAMP, "m", 1, 1, 60)
            relay = "snowball_relay_" + self.STAMP.lower()
            self.assertEqual(order[0], ("docker", "run", relay))
            self.assertEqual(order[-1], ("docker", "stop", relay))  # after the capsule, a timeout too
            self.assertLess(order.index(("capsule",)), len(order) - 1)
            self.assertEqual((out["egress"], out["egress_allowed"], out["egress_denied"], out["egress_unreadable"]),
                             ("contained", 1, 1, 1))
            self.assertEqual(out["egress_denied_first"],
                             [{"method": "GET", "target": "/api/repos/o/referee", "reason": "repo_not_allowed"}])
            self.assertEqual(out["timed_out"], timeout)
        code = (self.pilot.session_logs(self.STAMP) / "relay" / "egress.py").read_bytes()
        self.assertEqual(code, (FOUNDER / "egress.py").read_bytes().replace(b"\r\n", b"\n"))  # what decided them

    def test_a_relay_that_never_listens_is_an_outage_and_is_stopped(self):
        calls = []

        def run(*argv, **kw):
            calls.append(argv[:2])
            return subprocess.CompletedProcess(argv, 0, b"", b"")
        clock = iter(range(0, 1000, 10))
        with mock.patch.object(self.launch, "run", run), mock.patch.object(self.launch.time, "sleep"), \
                mock.patch.object(self.launch.time, "monotonic", lambda: next(clock)), \
                mock.patch.object(self.launch.subprocess, "run") as capsule:
            with self.assertRaises(self.launch.RelayDown):
                self.pilot.session(self.STAMP, "m", 1, 1, 60)
        capsule.assert_not_called()  # no session without its relay
        self.assertEqual(calls[-1], ("docker", "stop"))
        self.assertTrue(issubclass(self.launch.RelayDown, self.launch.Outage))

    def test_the_cycle_line_names_the_egress_the_hash_and_the_refusals(self):
        report = []
        launch = self.launch

        class Fake(quiet_pilot(launch)):
            heads = ["a" * 40, "a" * 40]

            def fetch_result(self):
                return None

            def brain_head(self):
                return self.heads.pop(0)

            def ledger_rows(self, sha):
                return []

            def refresh_inputs(self):
                pass

            def session(self, *a):
                return {"exit": 0, "minutes": 1, "egress": "contained", "transcript_sha256": "f" * 64,
                        "transcript_results": 2, "egress_allowed": 4, "egress_denied": 2,
                        "egress_denied_first": [{"method": "GET", "target": "/x", "reason": "no_route"}]}

            def write(self, text):
                report.append(text)

        pilot = Fake(self.work, "o/brain", "o/referee", "target", "contained")
        pilot.idle, pilot.seed = 0, "a" * 40
        args = type("Args", (), dict(model="m", max_turns=1, budget_usd=1, session_timeout=1, referee_timeout=1))
        with mock.patch.object(launch, "say"):
            pilot.cycle(1, args)
        row = json.loads(pilot.metrics.read_text(encoding="utf-8").splitlines()[-1])
        keys = ("egress", "transcript_sha256", "transcript_results", "egress_allowed", "egress_denied")
        self.assertEqual({k: row[k] for k in keys},
                         {"egress": "contained", "transcript_sha256": "f" * 64, "transcript_results": 2,
                          "egress_allowed": 4, "egress_denied": 2})
        self.assertIn("- Dökümde 2 `result` olayı var", "".join(report))
        self.assertIn("- Kapsülün reddedilen ağ istekleri: 2", "".join(report))
        self.assertIn("/relay/log/egress.jsonl", "".join(report))

    def test_the_entrypoint_writes_the_stream_to_stdout_and_nothing_else_there(self):
        entry = (FOUNDER / "entrypoint.sh").read_text(encoding="utf-8")
        self.assertLess(entry.index("exec 3>&1 1>&2"), entry.index("secret()"))  # before anything can print
        self.assertNotIn('> "/work/logs/session-$stamp.jsonl"', entry)  # the record is no file of the capsule's
        call = entry[entry.index("rc=$( { { code=0"):entry.index("rc=${rc:-1}")]
        self.assertIn('2> "/work/logs/session-$stamp.err" 3>&- 4>&- || code=$?', call)
        self.assertIn('| tee "/work/logs/session-$stamp.jsonl" >&3 4>&-; } 4>&1 ) || true', call)
        self.assertIn('echo "$code" >&4', call)

    def test_a_start_refuses_an_image_whose_entrypoint_is_not_the_checkouts(self):  # image_entrypoint_unchecked
        work = Path(tempfile.mkdtemp())
        seen = {"calls": []}
        launch = self.launch

        class FakePilot:
            idle = 0

            def __init__(self, work, brain, referee, target, egress="open"):
                self.work, self.report = work, work / "pilot-log.md"
                seen["egress"] = egress

            def write(self, text):
                pass

            def preflight(self):
                seen["calls"].append("preflight")

            def build(self):
                seen["calls"].append("build")

            def image_entrypoint(self):
                return seen.get("label")

            def intervention(self, args):
                seen["calls"].append("intervention")

        def start(*argv):
            with mock.patch.object(launch, "Pilot", FakePilot), mock.patch.object(launch, "say"), \
                    mock.patch.object(launch, "run_cycles", lambda *a: seen["calls"].append("cycles")), \
                    mock.patch.object(launch.shutil, "which", return_value="/usr/bin/tool"):
                return launch.main([*argv, "--work", str(work)])
        with self.assertRaises(SystemExit) as stop:
            start("--no-build", "--egress", "contained")
        self.assertIn("another entrypoint", str(stop.exception))
        self.assertEqual((seen["calls"], seen["egress"]), (["preflight"], "contained"))
        self.assertFalse((work / "RUNNING").exists())  # a resume would fail the same way
        seen.update(calls=[], label=launch.entrypoint_sha256())
        self.assertEqual(start("--no-build"), 0)
        self.assertEqual(seen["calls"], ["preflight", "intervention", "cycles"])
        self.assertEqual(launch.build_parser().parse_args([]).egress, "open")  # opt-in: a restart changes nothing

    def test_the_build_labels_the_image_with_its_entrypoint(self):  # E508
        calls = []

        def fake_run(*argv, **kw):
            calls.append(argv)
            return subprocess.CompletedProcess(argv, 0, b"", b"")
        with mock.patch.object(self.launch, "run", side_effect=fake_run), mock.patch.object(self.launch, "say"):
            self.pilot.build()
        labels = [calls[0][i + 1] for i, a in enumerate(calls[0]) if a == "--label"]
        self.assertIn(f"{self.launch.ENTRYPOINT_LABEL}={self.launch.entrypoint_sha256()}", labels)
        built = (FOUNDER / "entrypoint.sh").read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(self.launch.entrypoint_sha256(), hashlib.sha256(built).hexdigest())
        self.assertIn("founder/entrypoint.sh", self.launch.BUILD_FILES)
        self.assertNotIn("founder/egress.py", self.launch.BUILD_FILES)  # the relay's code never enters the capsule


PROBE = r'''
import json, socket, ssl, sys
RELAY = ("relay", 3128)
out = []

def note(kind, target, ok, detail):
    out.append({"kind": kind, "target": target, "reached": ok, "detail": str(detail)[:200]})

for host in ("github.com", "raw.githubusercontent.com", "codeload.github.com", "objects.githubusercontent.com",
             "api.github.com", "api.anthropic.com", "pypi.org"):
    try:
        note("dns", host, True, socket.getaddrinfo(host, 443)[0][4])
    except OSError as exc:
        note("dns", host, False, exc)
# The capsule subnet's first address, where a plain internal network puts the docker host (its gateway); isolated, it is
# a container's or no one's. And a port a service of the docker host's own listens on.
first, listener = sys.argv[3], int(sys.argv[4])
for host, port in (("140.82.121.3", 443), ("1.1.1.1", 443), ("8.8.8.8", 53), ("172.17.0.1", 80),
                   ("169.254.169.254", 80), ("host.docker.internal", 80), ("host.docker.internal", 2375),
                   (first, listener), ("172.17.0.1", listener), (first, 22), (first, 2375)):
    try:
        socket.create_connection((host, port), timeout=5).close()
        note("tcp", f"{host}:{port}", True, "connected")
    except OSError as exc:
        note("tcp", f"{host}:{port}", False, exc)
udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp.settimeout(5)
try:
    udp.sendto(bytes.fromhex("12340100000100000000000006676974687562036e65740000010001"), ("8.8.8.8", 53))
    note("udp", "8.8.8.8:53", True, udp.recvfrom(512)[0][:8].hex())
except OSError as exc:
    note("udp", "8.8.8.8:53", False, exc)

def ask(method, target):
    with socket.create_connection(RELAY, timeout=30) as conn:
        conn.sendall(f"{method} {target} HTTP/1.1\r\nHost: relay\r\nContent-Length: 0\r\n\r\n".encode())
        head = b""
        while b"\r\n" not in head:
            data = conn.recv(1)
            if not data:
                break
            head += data
        return head.split(b"\r\n")[0].decode(errors="replace")

for method, target in json.loads(sys.argv[1]):
    status = ask(method, target)
    note("relay", f"{method} {target}", " 403 " not in status, status)
with socket.create_connection(RELAY, timeout=30) as conn:
    conn.sendall(b"CONNECT api.anthropic.com:443 HTTP/1.1\r\nHost: api.anthropic.com:443\r\n\r\n")
    head = b""
    while b"\r\n\r\n" not in head:
        head += conn.recv(1)
    tls = ssl.create_default_context().wrap_socket(conn, server_hostname="api.anthropic.com")
    note("model", "api.anthropic.com:443", True, f"{head.split(b' ')[1].decode()} {tls.version()}")
note("brain", "info/refs", True, ask("GET", "/git/" + sys.argv[2] + ".git/info/refs?service=git-upload-pack"))
print(json.dumps(out))
'''


@unittest.skipUnless(os.environ.get("SNOWBALL_EGRESS_PROBE"),
                     "set SNOWBALL_EGRESS_PROBE to a name prefix to probe the real docker (network, relay, capsule)")
class ContainmentProbeTest(unittest.TestCase):
    """E508, opt-in: the launcher's own argv against the real docker. An internal network, the session's relay, and a
    probe in the capsule's place (its argv, the pinned Python base as the founder user) that tries to get out every way
    it can: DNS, TCP and UDP to addresses, and through the relay every forbidden target. It reaches the model's API
    (a TLS handshake, no request) and the brain's git endpoint (GitHub answers the made-up token 401). Containers and
    the network carry the prefix and are removed. Nothing secret is used."""

    BRAIN = "Okan-wqm/snowball-rehearsal-brain"

    def test_nothing_gets_out_but_the_model_and_the_brain_and_every_refusal_is_logged(self):
        launch, prefix = load_launch(), os.environ["SNOWBALL_EGRESS_PROBE"].rstrip("_")
        work = Path(tempfile.mkdtemp())
        for folder in ("target", "referee", "vec"):
            (work / folder).mkdir()
        (work / launch.CAPSULE_ENV).write_text("CLAUDE_CODE_OAUTH_TOKEN=made-up-" + "0" * 40 + "\n", encoding="utf-8")
        (work / launch.RELAY_ENV).write_text("GITHUB_TOKEN=made-up-" + "0" * 40 + "\n", encoding="utf-8")
        pilot = launch.Pilot(work, self.BRAIN, "o/referee", "target", "contained")
        pilot.network, pilot.container_prefix, pilot.seed = f"{prefix}_net", prefix, "a" * 40
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        relay_targets = [(m, t) for m, t, _ in FORBIDDEN] + [
            ("GET", "/git/Okan-wqm/snowball-rehearsal-referee.git/info/refs?service=git-upload-pack"),
            ("GET", "/api/repos/Okan-wqm/snowball-rehearsal-referee/contents/vectors"),
            ("GET", "/api/repos/Okan-wqm/snowball-mcp/contents/seed")]
        # A service of the docker host's own (its network namespace, 0.0.0.0): a plain internal network reaches it
        # through its gateway address (measured 2026-11-02); the capsule's must not. Both are removed whatever happens.
        listener, hostsvc = 18508, f"{prefix}_hostsvc_{stamp.lower()}"
        self.addCleanup(subprocess.run, ["docker", "network", "rm", pilot.network], capture_output=True)
        self.addCleanup(subprocess.run, ["docker", "stop", "--time", "1", hostsvc], capture_output=True)
        self.assertEqual(pilot.network_problems(), [])
        subprocess.run(["docker", "run", "--detach", "--rm", "--name", hostsvc, "--network", "host", "--entrypoint",
                        "python3", launch.relay_image(), "-m", "http.server", str(listener), "--bind", "0.0.0.0"],
                       capture_output=True, check=True, timeout=120)
        relay = pilot.start_relay(stamp)
        try:
            pilot.capsule_logs(stamp).mkdir(parents=True, exist_ok=True)
            argv = pilot.capsule_argv(stamp, "m", 1, 1)
            subnet = subprocess.run(["docker", "network", "inspect", "--format",
                                     "{{range .IPAM.Config}}{{.Subnet}}{{end}}", pilot.network],
                                    capture_output=True, check=True, text=True).stdout.strip()
            first = str(next(ipaddress.ip_network(subnet).hosts()))  # where a plain internal network's gateway is
            argv = [*argv[:-1], "--user", "10001:10001", "--entrypoint", "python3", launch.relay_image(),
                    "-c", PROBE, json.dumps(relay_targets), self.BRAIN, first, str(listener)]
            proc = subprocess.run(argv, capture_output=True, timeout=600)
            self.assertEqual(proc.returncode, 0, proc.stderr.decode(errors="replace")[-2000:])
            results = json.loads(proc.stdout)
            # From the default bridge, where the relay has its route out, neither of its addresses answers; the
            # host's service does (the control: the probe above is not blind to it).
            nets = json.loads(subprocess.run(["docker", "inspect", "--format", "{{json .NetworkSettings.Networks}}",
                                              relay], capture_output=True, check=True).stdout)
            code = ("import socket, sys\nfor ip, port in (a.split(',') for a in sys.argv[1:]):\n    try:\n"
                    "        socket.create_connection((ip, int(port)), timeout=5).close(); print('reached', ip)\n"
                    "    except OSError as exc:\n        print('blocked', ip, exc)\n")
            bridge = subprocess.run(["docker", "run", "--rm", "--name", f"{prefix}_bridge_{stamp.lower()}",
                                     "--network", "bridge", "--entrypoint", "python3", launch.relay_image(), "-c",
                                     code, *[f"{n['IPAddress']},3128" for n in nets.values()]],
                                    capture_output=True, timeout=120, text=True)
            control = subprocess.run(["docker", "run", "--rm", "--name", f"{prefix}_control_{stamp.lower()}",
                                      "--network", "bridge", "--entrypoint", "python3", launch.relay_image(), "-c",
                                      code, f"172.17.0.1,{listener}"], capture_output=True, timeout=120, text=True)
            print(bridge.stdout, control.stdout)
            self.assertNotIn("reached", bridge.stdout)
            self.assertEqual(bridge.stdout.count("blocked"), 2)
            self.assertIn("reached", control.stdout)
        finally:
            pilot.stop_relay(relay)
        print("\n" + json.dumps(results, indent=1))
        reached = [r for r in results if r["reached"] and r["kind"] not in ("model", "brain")]
        self.assertEqual(reached, [])
        self.assertEqual(len([r for r in results if not r["reached"]]), len(results) - 2)
        self.assertTrue(next(r for r in results if r["kind"] == "model")["detail"].startswith("200 TLS"))
        self.assertRegex(next(r for r in results if r["kind"] == "brain")["detail"], r" (200|401) ")
        log = pilot.session_logs(stamp) / "relay" / "log" / "egress.jsonl"
        rows = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
        denied = {(r["method"], r["target"]) for r in rows if r["decision"] == "deny"}
        self.assertEqual(set(relay_targets) - denied, set())  # every refusal through the relay is in its log
        self.assertEqual({r["decision"] for r in rows if r["method"] == "CONNECT"
                          and r["target"] == "api.anthropic.com:443"}, {"allow"})


if __name__ == "__main__":
    unittest.main()
