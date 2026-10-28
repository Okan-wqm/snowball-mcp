"""End to end over local git repositories: pull -> decide, across spec, code and exit requests."""

import io
import json
import os
import stat
import tarfile
import tempfile
import unittest
from pathlib import Path

from snowball_bootstrap import cli, gitio
from snowball_bootstrap.container import DockerRunner
from snowball_bootstrap.decide import decide
from snowball_bootstrap.importer import ImportErrorStop, run_import
from snowball_bootstrap.manifest import STAGE0_MF_TESTS
from snowball_bootstrap.treehash import TreeError, tree_hash

from helpers import commit, make_repo, sh

SEED_FILES = {"spec/tohum/00-cekirdek.md": "# core\n", "spec/asama-0/00-ozet.md": "# stage 0\n"}


def all_tests_manifest(done):
    tests = [{"id": f"T{n}", "cmd": f"python -m unittest t{n}", "stage": 0}
             for mf in done for n in STAGE0_MF_TESTS[mf]]
    return json.dumps({"tests": tests, "done_mf": list(done), "lockfiles": []})


class Flow(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.brain = base / "brain"
        self.seed_sha = make_repo(self.brain, SEED_FILES)
        self.referee = base / "referee"
        (self.referee / "setup").mkdir(parents=True)
        seed_hash = tree_hash(gitio.archive(self.brain, self.seed_sha), "spec/tohum", forbid_operator_names=False)
        (self.referee / "setup" / "summary.json").write_text(
            json.dumps({"seed_commit": self.seed_sha, "seed_tree_sha256": seed_hash}))
        (self.referee / "bootstrap.json").write_text(json.dumps({
            "brain_repo": "owner/brain", "brain_branch": "main",
            "image": "docker.io/library/python:3.12-slim@sha256:" + "a" * 64,
            "rival": {"model": "claude-sonnet-5-5", "effort": "medium", "max_turns": 30, "max_tokens": 16000,
                      "per_run_cap_usd_micros": 3_000_000,
                      "price_micros_per_mtok": {"input": 2_000_000, "output": 10_000_000,
                                                "cache_write": 2_500_000, "cache_read": 200_000}},
            "limits": {"test_timeout_s": 600, "reproducer_timeout_s": 120, "max_prompt_chars": 600_000,
                       "max_tree_bytes": 50_000_000}}))
        (self.referee / "policy.json").write_text(json.dumps({"constitutional": {
            "monthly_cap_usd": 300, "stage_params": {"rival_min_attempts": 2, "repeat_reject_limit": 3},
            "stage_budgets": {"asama_0": {"rival_usd": 30}},
            "license_allowlist": ["MIT", "Apache-2.0"], "license_exceptions": {}}}))
        (self.referee / "control.json").write_text(json.dumps({"kill_switch": False, "budget_state": "ok"}))
        self.state = {"schema": "snowball-bootstrap-state/1", "origin": "initial",
                      "last_accepted_sha": self.seed_sha, "last_evaluated_sha": None, "frozen_specs": {},
                      "rival_artifacts": [], "month": "2026-10", "month_spend_usd_micros": 0,
                      "stage_spend_usd_micros": 0, "runs": 0, "reject_streaks": {}, "repeat_events": 0}
        self.n = 0

    def tearDown(self):
        self.tmp.cleanup()

    def pull(self):
        self.n += 1
        state_path = Path(self.tmp.name) / f"state{self.n}.json"
        state_path.write_text(json.dumps(self.state))
        out = Path(self.tmp.name) / f"pulled{self.n}"
        rc = cli.main(["pull", "--root", str(self.referee), "--state", str(state_path),
                       "--work", str(Path(self.tmp.name) / "work"), "--out", str(out), "--remote", str(self.brain)])
        self.assertEqual(rc, 0)
        return json.loads((out / "meta.json").read_text())

    def finish(self, meta, run=None, rival=None, repro=None, jobs=None):
        result = decide(meta, run, rival, repro, jobs or {}, rival_min_attempts=2, repeat_reject_limit=3)
        self.state = result["state"]
        return result

    def rival_ok(self, cost=1000):
        return {"verdict": "not_refuted", "attempts": [], "reasons": [], "cost_usd_micros": cost,
                "reproducer_count": 0}

    def green_run(self, meta):
        tests = [{"id": t["id"], "cmd_sha256": "c", "ok": True, "output_tail": ""}
                 for t in meta["manifest"]["tests"]]
        return {"controls": [{"id": "exit_one", "ok": True}], "tests": tests, "vectors": [], "green": True}

    def test_full_stage0_path(self):
        meta = self.pull()
        self.assertEqual(meta["kind"], "none")

        # Code before the spec is frozen is refused.
        commit(self.brain, {"referee/ledger/chain.py": "x = 1\n", "snowball-tests.json": all_tests_manifest([1])},
               "mf1")
        meta = self.pull()
        self.assertEqual(meta["kind"], "code")
        self.assertIn("spec_not_frozen", meta["pre_reasons"])
        self.assertFalse(meta["run_tests"])
        result = self.finish(meta)
        self.assertEqual(result["verdict"], "rejected")
        self.assertEqual(result["state"]["last_accepted_sha"], self.seed_sha)

        # Same head again is not re-evaluated.
        self.assertEqual(self.pull()["kind"], "none")

        # A spec request: mixing with code from the rejected commit is refused ...
        commit(self.brain, {"spec/asama-0/00-ozet.md": "# stage 0, fixed\n"}, "spec fix")
        meta = self.pull()
        self.assertIn("mixed_spec_and_code", meta["pre_reasons"])
        self.finish(meta)

        # ... so the founder reverts the code and pushes the spec alone.
        commit(self.brain, {"referee/ledger/chain.py": None, "snowball-tests.json": None}, "spec only")
        meta = self.pull()
        self.assertEqual((meta["kind"], meta["pre_reasons"], meta["run_rival"]), ("spec", [], True))
        result = self.finish(meta, rival=self.rival_ok(), jobs={"cagir": "success"})
        self.assertEqual(result["verdict"], "frozen")
        self.assertIn("spec/asama-0", result["state"]["frozen_specs"])
        self.assertEqual(result["state"]["rival_artifacts"], [meta["head"]])

        # MF1 as a code request.
        commit(self.brain, {"referee/ledger/chain.py": "x = 1\n", "snowball-tests.json": all_tests_manifest([1])},
               "mf1")
        meta = self.pull()
        self.assertEqual((meta["kind"], meta["pre_reasons"], meta["run_tests"]), ("code", [], True))
        jobs = {"getir": "success", "kos": "success", "cagir": "success", "yeniden": "skipped"}
        run = self.green_run(meta)
        result = self.finish(meta, run=run, rival=self.rival_ok(), jobs=jobs)
        self.assertEqual(result["verdict"], "accepted", result["reasons"])
        accepted = meta["head"]

        # Red tests: rival skipped on purpose, not an infra failure, and the SHA is consumed.
        commit(self.brain, {"referee/ledger/chain.py": "x = 2\n"}, "break")
        meta = self.pull()
        run = self.green_run(meta)
        run["tests"][0]["ok"], run["green"] = False, False
        result = self.finish(meta, run=run, jobs={"getir": "success", "kos": "success", "cagir": "skipped"})
        self.assertEqual(result["verdict"], "rejected")
        self.assertEqual([r["kind"] for r in result["reasons"]], ["test_failed"])
        self.assertEqual(result["state"]["last_evaluated_sha"], meta["head"])
        self.assertEqual(result["state"]["last_accepted_sha"], accepted)

        # A reproduced refutation blocks; one without a reproducer does not.
        commit(self.brain, {"referee/ledger/chain.py": "x = 3\n"}, "fix")
        meta = self.pull()
        refuted = {"verdict": "refuted", "attempts": [{"claim": "wrong", "evidence_refs": [],
                                                        "reproducer": {"cmd": "x"}}], "reasons": [],
                   "cost_usd_micros": 1, "reproducer_count": 1}
        result = self.finish(meta, run=self.green_run(meta), rival=refuted,
                             repro=[{"attempt_index": 0, "reproduced": True}],
                             jobs={"getir": "success", "kos": "success", "cagir": "success", "yeniden": "success"})
        self.assertEqual(result["reasons"][0]["kind"], "refutation_reproduced")

    def test_exit_request_and_import(self):
        # Freeze the spec, then accept a complete stage 0.
        commit(self.brain, {"spec/asama-0/00-ozet.md": "# stage 0 v2\n"}, "spec")
        meta = self.pull()
        self.finish(meta, rival=self.rival_ok(), jobs={"cagir": "success"})
        files = {"referee/ledger/chain.py": "x = 1\n", "referee/.github/workflows/ref.yml": "on: push\n",
                 "tests/fixtures/toy-repo/app.py": "import os\n",
                 "snowball-tests.json": all_tests_manifest(range(1, 31))}
        commit(self.brain, files, "all of stage 0")
        meta = self.pull()
        jobs = {"getir": "success", "kos": "success", "cagir": "success", "yeniden": "skipped"}
        result = self.finish(meta, run=self.green_run(meta), rival=self.rival_ok(), jobs=jobs)
        self.assertEqual(result["verdict"], "accepted", result["reasons"])
        exit_sha = meta["head"]

        frozen = self.state["frozen_specs"]["spec/asama-0"]
        commit(self.brain, {"exit-request.json": json.dumps({"stage": 0, "sha": exit_sha, "spec_sha256": frozen})},
               "exit request")
        meta = self.pull()
        self.assertEqual((meta["kind"], meta["pre_reasons"], meta["run_rival"]), ("exit", [], False))
        result = self.finish(meta, run=self.green_run(meta), jobs={"getir": "success", "kos": "success"})
        self.assertEqual(result["verdict"], "rejected")
        self.assertIn("rival_attempts:1<2", [r["ref"] for r in result["reasons"]])

        # An exit request must name the last accepted commit, and that commit needs its own review.
        self.state["last_evaluated_sha"] = None
        saved = json.loads(json.dumps(self.state))
        self.state["rival_artifacts"] = [a for a in self.state["rival_artifacts"] if a != exit_sha] + ["e" * 40]
        meta = self.pull()
        result = self.finish(meta, run=self.green_run(meta), jobs={"getir": "success", "kos": "success"})
        self.assertIn("no_rival_attempt_on_exit_sha", [r["ref"] for r in result["reasons"]])
        self.state = saved
        commit(self.brain, {"exit-request.json": json.dumps({"stage": 0, "sha": self.seed_sha,
                                                              "spec_sha256": frozen})}, "wrong sha")
        meta = self.pull()
        self.assertIn("exit_request_sha_is_not_last_accepted", meta["pre_reasons"])
        commit(self.brain, {"exit-request.json": json.dumps({"stage": 0, "sha": exit_sha, "spec_sha256": frozen})},
               "exit request again")

        # One more independently reviewed artefact, then the exit request passes.
        self.state["rival_artifacts"].append("f" * 40)
        self.state["last_accepted_sha"] = exit_sha
        self.state["last_evaluated_sha"] = None
        meta = self.pull()
        result = self.finish(meta, run=self.green_run(meta), jobs={"getir": "success", "kos": "success"})
        self.assertEqual(result["verdict"], "accepted", result["reasons"])
        self.assertTrue(result["exit"]["transferable"])
        self.assertEqual(result["exit"]["repeat_events"], 0)

        # Operator import: signature check stubbed, tree hash real.
        work = Path(self.tmp.name)
        (work / "result.json").write_text(json.dumps(result))
        (work / "bundle.json").write_text("{}")
        fake_sigstore = work / "fake-python"
        fake_sigstore.write_text("#!/bin/sh\nexit 0\n")
        fake_sigstore.chmod(fake_sigstore.stat().st_mode | stat.S_IEXEC)
        referee = work / "referee-checkout"
        (referee / "setup").mkdir(parents=True)
        (referee / "policy.json").write_text("{}")
        (referee / "bootstrap").mkdir()
        (referee / ".github" / "workflows").mkdir(parents=True)
        (referee / ".github" / "workflows" / "bootstrap.yml").write_text("old")
        toy = work / "toy"
        toy.mkdir()
        log = run_import(work / "result.json", work / "bundle.json", "id", str(fake_sigstore), self.brain,
                         referee, toy)
        self.assertEqual(log["referee_tree_sha256"], result["exit"]["referee_tree_sha256"])
        self.assertTrue((referee / "ledger" / "chain.py").exists())
        self.assertTrue((referee / ".github" / "workflows" / "ref.yml").exists())
        self.assertFalse((referee / ".github" / "workflows" / "bootstrap.yml").exists())
        self.assertFalse((referee / "bootstrap").exists())
        self.assertEqual((referee / "policy.json").read_text(), "{}")
        self.assertTrue((toy / "app.py").exists())

        # A signed hash that does not match the commit's referee tree stops the import.
        tampered = json.loads(json.dumps(result))
        tampered["exit"]["referee_tree_sha256"] = "0" * 64
        (work / "tampered.json").write_text(json.dumps(tampered))
        with self.assertRaises(ImportErrorStop):
            run_import(work / "tampered.json", work / "bundle.json", "id", str(fake_sigstore), self.brain,
                       referee, toy)

        # A failing signature check stops the import.
        fake_sigstore.write_text("#!/bin/sh\necho bad >&2\nexit 1\n")
        with self.assertRaises(ImportErrorStop):
            run_import(work / "result.json", work / "bundle.json", "id", str(fake_sigstore), self.brain, referee, toy)

    def test_rejection_memory_shows_whether_the_founder_uses_what_it_was_told(self):
        commit(self.brain, {"spec/asama-0/00-ozet.md": "# stage 0 v4\n"}, "spec")
        self.finish(self.pull(), rival=self.rival_ok(), jobs={"cagir": "success"})
        red_jobs = {"getir": "success", "kos": "success", "cagir": "skipped"}
        same = f"test_failed:T{STAGE0_MF_TESTS[1][0]}"

        def red_push(n, licenses=None):
            commit(self.brain, {"referee/ledger/chain.py": f"x = {n}\n",
                                "snowball-tests.json": all_tests_manifest([1])}, f"try {n}")
            meta = self.pull()
            run = self.green_run(meta)
            if licenses is None:
                run["tests"][0]["ok"] = False
            else:
                run["licenses"] = licenses
            run["green"] = False
            return self.finish(meta, run=run, jobs=red_jobs)

        first = red_push(1)
        self.assertEqual(first["learning"], {"repeated": [], "not_learning": [], "repeat_events": 0})
        self.assertEqual(red_push(2)["learning"]["repeated"], [same])
        third = red_push(3)
        self.assertEqual(third["learning"]["not_learning"], [same])
        self.assertEqual(third["state"]["repeat_events"], 2)

        # An infrastructure failure judges nothing, so it neither extends nor clears a streak.
        commit(self.brain, {"referee/ledger/chain.py": "x = 4\n"}, "infra")
        result = self.finish(self.pull(), jobs={"getir": "failure", "kos": "skipped", "cagir": "skipped"})
        self.assertEqual(result["state"]["reject_streaks"], {same: 3})

        # A different failure ends the old streak; a license violation is a rejection like any other.
        gpl = [{"name": "gplpkg", "version": "1.0", "expression": "GPL-3.0-only", "allowed": False}]
        result = red_push(5, licenses=gpl)
        self.assertEqual([r["kind"] for r in result["reasons"]], ["license_not_allowed"])
        self.assertEqual(result["state"]["reject_streaks"], {"license_not_allowed:gplpkg==1.0:GPL-3.0-only": 1})

        # Acceptance clears the streaks; the count of repeats stays as the founder's record.
        commit(self.brain, {"referee/ledger/chain.py": "x = 6\n"}, "fixed")
        meta = self.pull()
        result = self.finish(meta, run=self.green_run(meta), rival=self.rival_ok(),
                             jobs={"getir": "success", "kos": "success", "cagir": "success", "yeniden": "skipped"})
        self.assertEqual(result["verdict"], "accepted", result["reasons"])
        self.assertEqual((result["state"]["reject_streaks"], result["state"]["repeat_events"]), ({}, 2))

    def test_exhausted_budget_is_recorded_once_without_calling_the_rival(self):
        self.state["stage_spend_usd_micros"] = 30_000_000
        commit(self.brain, {"spec/asama-0/00-ozet.md": "# stage 0 v3\n"}, "spec")
        meta = self.pull()
        self.assertEqual(meta["pre_reasons"], ["budget"])
        self.assertFalse(meta["run_rival"])
        result = self.finish(meta, jobs={"cagir": "skipped"})
        self.assertEqual(result["verdict"], "rejected")
        self.assertEqual(result["state"]["last_evaluated_sha"], meta["head"])
        self.assertEqual(self.pull()["kind"], "none")

    def test_history_rewrite_and_seed_edit_are_rejected(self):
        commit(self.brain, {"spec/tohum/00-cekirdek.md": "# changed core\n"}, "edit seed")
        meta = self.pull()
        self.assertEqual(meta["kind"], "rejected")
        self.assertIn("seed_modified", meta["pre_reasons"])
        self.assertIn("seed_tree_mismatch", meta["pre_reasons"])
        sh(self.brain, "git", "reset", "-q", "--hard", self.seed_sha)
        sh(self.brain, "git", "commit", "-q", "--allow-empty", "-m", "rewritten")
        self.state["last_accepted_sha"] = meta["head"]
        meta = self.pull()
        self.assertIn("history_rewritten", meta["pre_reasons"])
        self.assertEqual(meta["kind"], "rejected")

    def test_symlink_and_export_ignore(self):
        (self.brain / "referee").mkdir()
        os.symlink("/etc/passwd", self.brain / "referee" / "link")
        commit(self.brain, {".gitattributes": "hidden.py export-ignore\n", "hidden.py": "x\n"}, "tricks")
        meta = self.pull()
        self.assertIn("not_regular_file:symlink:referee/link", meta["pre_reasons"])
        tar_bytes = (Path(self.tmp.name) / f"pulled{self.n}" / "brain.tar").read_bytes()
        names = tarfile.open(fileobj=io.BytesIO(tar_bytes)).getnames()
        self.assertIn("hidden.py", names)
        self.assertNotIn("referee/link", names)


class TreeHashTest(unittest.TestCase):
    def test_operator_names_are_refused_under_referee(self):
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:") as tar:
            for name in ("referee/a.py", "referee/policy.json"):
                info = tarfile.TarInfo(name)
                info.size = 1
                tar.addfile(info, io.BytesIO(b"x"))
        with self.assertRaises(TreeError):
            tree_hash(buf.getvalue(), "referee")
        self.assertEqual(len(tree_hash(buf.getvalue(), "referee", forbid_operator_names=False)), 64)


class DockerRunnerTest(unittest.TestCase):
    def test_flags_and_no_host_environment(self):
        runner = DockerRunner(image="img@sha256:" + "a" * 64, src_dir="/s", deps_dir="/d", vectors_dir="/v",
                              lockfiles=("req.lock",))
        argv = runner.argv("n", "python -m unittest", "referee")
        joined = " ".join(argv)
        for flag in ("--network none", "--cap-drop ALL", "--read-only", "--user 65534:65534",
                     "--security-opt no-new-privileges", "type=bind,src=/s,dst=/src,readonly"):
            self.assertIn(flag, joined)
        envs = [argv[i + 1] for i, a in enumerate(argv) if a == "--env"]
        self.assertFalse([e for e in envs if e.startswith(("ACTIONS_", "GITHUB_", "ANTHROPIC"))])
        self.assertIn("SNOWBALL_CMD=python -m unittest", envs)

    def test_exit_code_and_timeout_through_a_fake_docker(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "docker"
            fake.write_text('#!/bin/sh\nfor a in "$@"; do case "$a" in SNOWBALL_CMD=*) cmd="${a#SNOWBALL_CMD=}";; '
                            'esac; done\n[ "$1" = rm ] && exit 0\nexec sh -c "$cmd"\n')
            fake.chmod(0o755)
            runner = DockerRunner(image="i", src_dir=tmp, deps_dir=tmp, vectors_dir=tmp, docker=str(fake))
            self.assertEqual(runner.run("exit 7", timeout_s=10).exit_code, 7)
            self.assertEqual(runner.run("echo hi", timeout_s=10).stdout, b"hi\n")
            slow = runner.run("sleep 5", timeout_s=1)
            self.assertTrue(slow.timed_out)
            self.assertFalse(slow.ok)
            with self.assertRaises(ValueError):
                runner.run("true", cwd="../x", timeout_s=1)


if __name__ == "__main__":
    unittest.main()
