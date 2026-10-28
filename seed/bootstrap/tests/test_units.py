import json
import unittest
from pathlib import Path

from snowball_bootstrap import canon, secretscan
from snowball_bootstrap.classify import classify, spec_stage_dirs
from snowball_bootstrap.controls import run_controls
from snowball_bootstrap.manifest import ManifestError, check_stage0, parse_lockfile, parse_manifest
from snowball_bootstrap.vectors import run_vectors

from helpers import FakeRunner

VECTORS = Path(__file__).resolve().parents[1] / "vectors"
Z = "0" * 64


class CanonTest(unittest.TestCase):
    def test_seed_vectors_v1_v2(self):
        v1 = {"row_id": "r1", "ts": "2026-10-28T00:00:00Z", "part": "events", "kind": "genesis", "payload": {},
              "derivation": "tool", "trust": "verified", "snapshot_id": "s0", "evidence_refs": [], "prev_hash": Z}
        h1 = canon.row_hash(v1)
        self.assertEqual(h1, "3bae91580aca99362572e9f5f41b3e46c2bc0c29236f72e867faa5cd46ca603a")
        v2 = {"row_id": "r2", "ts": "2026-10-28T00:00:01Z", "part": "cost", "kind": "run",
              "payload": {"usd_micros": 0}, "derivation": "tool", "trust": "observed", "snapshot_id": "s0",
              "evidence_refs": [], "prev_hash": h1}
        self.assertEqual(canon.row_hash(v2), "3b10a5bb06351b0933c0e30f7dd55d3a57245743b97fb1faba348351a554a45c")

    def test_row_hash_ignores_own_hash_field(self):
        row = {"a": 1, "prev_hash": Z}
        self.assertEqual(canon.row_hash(row), canon.row_hash(dict(row, row_hash="x" * 64)))

    def test_floats_and_surrogates_rejected(self):
        with self.assertRaises(canon.CanonicalError):
            canon.canonical({"x": 0.5})
        with self.assertRaises(canon.CanonicalError):
            canon.canonical({"x": "\ud800"})
        with self.assertRaises(canon.CanonicalError):
            canon.canonical({"x": 2**60})

    def test_keys_sorted_by_utf16(self):
        self.assertEqual(canon.canonical({"b": 1, "a": 2, "é": 3}), '{"a":2,"b":1,"é":3}'.encode())


class ClassifyTest(unittest.TestCase):
    def test_kinds(self):
        self.assertEqual(classify([]), ("none", []))
        self.assertEqual(classify(["spec/asama-0/01-amac.md", "spec/INDEX.md"]), ("spec", []))
        self.assertEqual(classify(["referee/ledger/chain.py", "snowball-tests.json"]), ("code", []))
        self.assertEqual(classify(["spec/asama-0/x.md", "referee/a.py"]), ("rejected", ["mixed_spec_and_code"]))
        self.assertEqual(classify(["spec/tohum/00-cekirdek.md"]), ("rejected", ["seed_modified"]))
        self.assertEqual(classify(["seed/bootstrap/x.py"]), ("rejected", ["seed_modified"]))
        self.assertEqual(classify([".github/workflows/x.yml"]), ("rejected", ["root_workflow_modified"]))
        self.assertEqual(classify(["referee/.github/workflows/x.yml"]), ("code", []))

    def test_spec_dirs(self):
        self.assertEqual(spec_stage_dirs(["spec/asama-0/a.md", "spec/asama-1/b.md", "spec/INDEX.md"]),
                         ["spec/asama-0", "spec/asama-1"])


class ManifestTest(unittest.TestCase):
    def manifest(self, tests, done, locks=()):
        return json.dumps({"tests": tests, "done_mf": list(done), "lockfiles": list(locks)})

    def test_valid_and_complete(self):
        m = parse_manifest(self.manifest([{"id": "T13", "cmd": "python -m unittest", "stage": 0},
                                          {"id": "T30", "cmd": "python -m unittest t30", "stage": 0}], [1, 2]))
        self.assertEqual(check_stage0(m), [])

    def test_missing_test_and_zero_tests_and_order(self):
        m = parse_manifest(self.manifest([{"id": "T13", "cmd": "x", "stage": 0}], [1, 2]))
        self.assertEqual(check_stage0(m), ["missing_test:MF2:T30"])
        m = parse_manifest(self.manifest([], []))
        self.assertEqual(check_stage0(m), ["zero_tests"])
        m = parse_manifest(self.manifest([{"id": "T13", "cmd": "x", "stage": 0}], [2]))
        self.assertEqual(check_stage0(m), ["done_mf_not_in_order"])

    def test_malformed(self):
        for bad in ['{"tests": []}', self.manifest([{"id": "13", "cmd": "x", "stage": 0}], []),
                    self.manifest([{"id": "T1", "cmd": "", "stage": 0}], []),
                    self.manifest([], [], ["../x.txt"]),
                    self.manifest([{"id": "T1", "cmd": "x", "stage": 0, "extra": 1}], [])]:
            with self.assertRaises(ManifestError):
                parse_manifest(bad)

    def test_lockfile(self):
        h = "a" * 64
        self.assertEqual(len(parse_lockfile(f"x==1 \\\n    --hash=sha256:{h}\ny==2 --hash=sha256:{h}\n")), 2)
        for bad in [f"x>=1 --hash=sha256:{h}", "x==1", f"--index-url https://evil\nx==1 --hash=sha256:{h}",
                    f"x==1 --hash=sha256:{h} --trusted-host evil", "git+https://x/y"]:
            with self.assertRaises(ManifestError):
                parse_lockfile(bad)


class VectorsTest(unittest.TestCase):
    def test_correct_implementation_passes_every_vector(self):
        results = run_vectors(FakeRunner(VECTORS), VECTORS, (1, 9))
        self.assertTrue(results)
        self.assertEqual([r for r in results if not r["ok"]], [])

    def test_groups_wait_for_their_micro_feature(self):
        self.assertEqual(run_vectors(FakeRunner(VECTORS), VECTORS, (2,)), [])
        ids = {r["id"].split(".")[0] for r in run_vectors(FakeRunner(VECTORS), VECTORS, (1,))}
        self.assertEqual(ids, {"chain"})

    def test_wrong_implementations_fail(self):
        for wrong, prefix in [("chain_ignores_input", "chain.V1.hash_changed_input"),
                              ("verify_always_valid", "chain.V3"), ("cp_wilson", "cp_lower.60/60"),
                              ("score_counts_twice", "match.3")]:
            failed = {r["id"] for r in run_vectors(FakeRunner(VECTORS, wrong={wrong}), VECTORS, (1, 9))
                      if not r["ok"]}
            self.assertIn(prefix, failed, wrong)


class ControlsTest(unittest.TestCase):
    def test_honest_runner_passes(self):
        runner = FakeRunner(VECTORS, commands={"exit 1": (1, b"")})
        self.assertTrue(all(c["ok"] for c in run_controls(runner)))

    def test_always_green_runner_fails(self):
        class Green(FakeRunner):
            def run(self, cmd, **kw):
                from snowball_bootstrap.container import RunResult
                return RunResult(0, b"", b"", 1)
        results = {c["id"]: c["ok"] for c in run_controls(Green(VECTORS))}
        self.assertFalse(results["exit_one"])
        self.assertFalse(results["network_blocked"])
        self.assertFalse(results["source_read_only"])


class SecretScanTest(unittest.TestCase):
    def test_patterns(self):
        fake = "gh" + "p_" + "A" * 36
        self.assertEqual(secretscan.scan(f"token: {fake}"), ["github_token"])
        self.assertEqual(secretscan.scan("-----BEGIN " + "RSA PRIVATE KEY-----"), ["private_key"])
        self.assertEqual(secretscan.scan("nothing here"), [])


if __name__ == "__main__":
    unittest.main()
