import json
import re
import tempfile
import unittest
import zipfile
from pathlib import Path

from snowball_bootstrap import canon, licenses, secretscan
from snowball_bootstrap.classify import classify, spec_stage_dirs
from snowball_bootstrap.controls import run_controls
from snowball_bootstrap.manifest import ManifestError, check_stage0, parse_lockfile, parse_manifest
from snowball_bootstrap.vectors import run_vectors

from helpers import FakeRunner

BOOTSTRAP = Path(__file__).resolve().parents[1]
VECTORS = BOOTSTRAP / "vectors"
POLICY_DEFAULTS = BOOTSTRAP.parents[1] / "spec" / "tohum" / "18a-politika-baslangic-degerleri.md"
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


def spec_allowlist() -> frozenset[str]:
    """The recommended allowlist as `tohum/18a` writes it: the backticked ids before the first ';'."""
    row = next(line for line in POLICY_DEFAULTS.read_text(encoding="utf-8").splitlines()
               if line.startswith("| `license_allowlist` |"))
    return frozenset(re.findall(r"`([^`]+)`", row.split("|")[2].split(";")[0]))


def make_wheel(directory: Path, name: str, headers: list[str], files: dict[str, str] | None = None) -> Path:
    path = directory / f"{name}-1.0-py3-none-any.whl"
    with zipfile.ZipFile(path, "w") as zf:
        meta = "Metadata-Version: 2.4\nName: " + name + "\nVersion: 1.0\n" + "".join(h + "\n" for h in headers)
        zf.writestr(f"{name}-1.0.dist-info/METADATA", meta)
        for rel, text in (files or {}).items():
            zf.writestr(f"{name}-1.0.dist-info/{rel}", text)
    return path


GPL3 = "GNU GENERAL PUBLIC LICENSE\n   Version 3, 29 June 2007\n Everyone is permitted to copy..."
MIT_TEXT = ("Permission is hereby granted, free of charge, to any person obtaining a copy of this software... "
            "The above copyright notice and this permission notice shall be included in all copies.")
PSF_TEXT = ("PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2\n... material that was previously distributed under "
            "the GNU General Public License (GPL), the law of the Commonwealth of Virginia shall govern ...")


class LicenseTest(unittest.TestCase):
    ALLOW = frozenset({"MIT", "Apache-2.0", "BSD-3-Clause", "PSF-2.0"})

    def judge(self, headers, files=None, exceptions=None):
        with tempfile.TemporaryDirectory() as tmp:
            make_wheel(Path(tmp), "pkg", headers, files)
            report = licenses.check_dir(Path(tmp), self.ALLOW, exceptions or {})
        self.assertEqual(len(report), 1)
        return report[0]

    def test_expressions(self):
        for expr, ok in (("MIT", True), ("mit", True), ("MIT OR GPL-3.0-only", True),
                         ("MIT AND GPL-3.0-only", False), ("(MIT OR GPL-3.0-only) AND Apache-2.0", True),
                         ("GPL-3.0-only OR (MIT AND AGPL-3.0-only)", False),
                         ("Apache-2.0 WITH LLVM-exception", True), ("Apache-2.0+", True)):
            self.assertEqual(licenses.allowed(expr, self.ALLOW), ok, expr)
        for bad in ("", "MIT OR", "(MIT", "MIT)", "AND MIT", "MIT GPL-3.0-only"):
            with self.assertRaises(licenses.ExpressionError, msg=bad):
                licenses.allowed(bad, self.ALLOW)

    def test_every_place_that_names_a_license_must_allow(self):
        r = self.judge(["License-Expression: MIT"], {"licenses/LICENSE": MIT_TEXT})
        self.assertEqual((r["expression"], r["allowed"]), ("MIT", True))
        r = self.judge(["License-Expression: MIT",
                        "Classifier: License :: OSI Approved :: GNU General Public License v3 (GPLv3)"])
        self.assertFalse(r["allowed"])
        r = self.judge(["License: MIT"], {"licenses/COPYING": GPL3})
        self.assertFalse(r["allowed"])
        r = self.judge(["Classifier: License :: Other/Proprietary License"])
        self.assertFalse(r["allowed"])

    def test_license_found_only_in_a_file_and_unknown_is_refused(self):
        r = self.judge([], {"licenses/LICENSE": MIT_TEXT})
        self.assertEqual((r["expression"], r["allowed"]), ("MIT", True))
        r = self.judge(["Classifier: License :: OSI Approved :: BSD License"], {"licenses/AUTHORS": "someone"})
        self.assertEqual((r["expression"], r["allowed"]), ("unknown", False))
        r = self.judge(["License: see the website"])
        self.assertEqual((r["expression"], r["allowed"]), ("unknown", False))

    def test_a_mention_is_not_a_license(self):
        r = self.judge(["License-Expression: PSF-2.0"], {"licenses/LICENSE": PSF_TEXT})
        self.assertEqual((r["expression"], r["allowed"]), ("PSF-2.0", True))
        self.assertEqual([s["expression"] for s in r["sources"]], ["PSF-2.0", "PSF-2.0"])

    def test_operator_exception_must_itself_be_allowed(self):
        r = self.judge([], exceptions={"pkg==1.0": "MIT"})
        self.assertEqual((r["basis"], r["allowed"]), ("exception", True))
        r = self.judge([], exceptions={"pkg==1.0": "GPL-3.0-only"})
        self.assertFalse(r["allowed"])
        r = self.judge([], exceptions={"pkg==2.0": "MIT"})
        self.assertEqual((r["expression"], r["allowed"]), ("unknown", False))

    def test_oversized_license_file_is_not_read(self):
        r = self.judge([], {"licenses/LICENSE": MIT_TEXT + " " * licenses.MAX_READ})
        self.assertEqual(r["expression"], "unknown")

    def test_cli_stops_on_a_violation(self):
        from snowball_bootstrap import cli
        with tempfile.TemporaryDirectory() as tmp:
            root, wheels = Path(tmp), Path(tmp) / "w"
            wheels.mkdir()
            (root / "policy.json").write_text(json.dumps({"constitutional": {
                "monthly_cap_usd": 1, "stage_params": {"rival_min_attempts": 1, "repeat_reject_limit": 3},
                "stage_budgets": {"asama_0": {"rival_usd": 1}}, "license_allowlist": ["MIT"],
                "license_exceptions": {}}}))
            argv = ["licenses", "--root", str(root), "--wheels", str(wheels), "--out", str(root / "r.json")]
            self.assertEqual(cli.main(argv), 2)  # no wheels at all is not a pass
            make_wheel(wheels, "good", ["License-Expression: MIT"])
            self.assertEqual(cli.main(argv), 0)
            make_wheel(wheels, "bad", [], {"licenses/LICENSE": GPL3})
            self.assertEqual(cli.main(argv), 2)
            report = json.loads((root / "r.json").read_text())
            self.assertEqual([(r["name"], r["allowed"]) for r in report], [("bad", False), ("good", True)])


class LicensePolicyTest(unittest.TestCase):
    def policy(self, **const):
        from snowball_bootstrap.config import load_policy
        base = {"monthly_cap_usd": 1, "stage_params": {"rival_min_attempts": 1, "repeat_reject_limit": 3},
                "stage_budgets": {"asama_0": {"rival_usd": 1}}, "license_allowlist": ["MIT"],
                "license_exceptions": {}}
        base.update(const)
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "policy.json").write_text(json.dumps({"constitutional": base}))
            return load_policy(Path(tmp))

    def test_allowlist_and_exceptions_are_strict(self):
        from snowball_bootstrap.config import ConfigError
        good = self.policy(license_exceptions={"pkg==1.0": {"expression": "MIT", "evidence": "LICENSE in sdist"}})
        self.assertEqual((good.license_allowlist, good.license_exceptions), (frozenset({"MIT"}), {"pkg==1.0": "MIT"}))
        for bad in ({"license_allowlist": []}, {"license_allowlist": ["MIT OR GPL-3.0-only"]},
                    {"license_exceptions": {"pkg==1.0": {"expression": "MIT"}}},
                    {"license_exceptions": {"Pkg_X==1.0": {"expression": "MIT", "evidence": "x"}}}):
            with self.assertRaises(ConfigError, msg=bad):
                self.policy(**bad)

    def test_a_wheel_that_is_not_allowed_makes_the_run_red(self):
        from snowball_bootstrap.cli import is_green
        ok = [{"ok": True}]
        self.assertTrue(is_green(ok, ok, ok, [{"allowed": True}]))
        self.assertFalse(is_green(ok, ok, ok, [{"allowed": True}, {"allowed": False}]))
        self.assertFalse(is_green(ok, [], ok, []))


class PinnedRequirementLicenseTest(unittest.TestCase):
    """The bootstrap's own pinned wheels: every one has a recorded, allowed license."""

    def test_record_matches_the_lock_files_and_the_spec_allowlist(self):
        allow = spec_allowlist()
        self.assertIn("MIT", allow)
        self.assertNotIn("GPL-3.0-only", allow)
        record = json.loads((BOOTSTRAP / "requirements" / "licenses.json").read_text())["packages"]
        pins = set()
        for lock in ("call.txt", "sign.txt"):
            for req in parse_lockfile((BOOTSTRAP / "requirements" / lock).read_text()):
                pins.add(f"{re.sub(r'[-_.]+', '-', req.name).lower()}=={req.version}")
        self.assertEqual(pins, set(record))
        for pin, expr in record.items():
            self.assertTrue(licenses.allowed(expr, allow), f"{pin}: {expr}")
