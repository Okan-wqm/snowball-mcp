"""E513 (plan D8): the target's toolchain in the referee. The fetch step executes nothing the tree holds and installs
exactly the locks; the run step has no network; a suite is green only when it showed tests that passed; the rival can
send a reproducer for the target image, and a reproducer the referee cannot run never proves or clears a defect.

The unit tests here need no docker. `LiveTargetImageTest` runs the real image and is skipped unless
``SNOWBALL_TARGET_IMAGE`` names a built `images/target/Dockerfile` (the operator's acceptance run)."""

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from snowball_bootstrap import canon, decide, reproduce, rival, rival_mcp, state, target_run
from snowball_bootstrap.config import ConfigError, RivalConfig
from snowball_bootstrap.container import RunResult, sandbox_flags
from snowball_bootstrap.rival import TARGET_IMAGE, ToolBox, validate_verdict
from snowball_bootstrap.target_run import Suite, TargetRunner

from helpers import posix_only

CARGO_SUITE = {"id": "core", "kind": "cargo", "root": ".", "cwd": ".", "cmd": "cargo test --offline -p demo 2>&1"}
NODE_SUITE = {"id": "engines", "kind": "node", "root": ".", "cwd": "libs/engines",
              "workspaces": ["libs/engines", "libs/testing"],
              "cmd": "../../node_modules/.bin/vitest run --reporter=json"}
INTEGRITY = "sha512-" + "A" * 86 + "=="
CFG_IF = "9330f8b2ff13f34540b44e946ef35111825727b38d33286ef986142615121801"  # crates.io's cfg-if 1.0.4
CHECKSUM = "ab" * 32


def npm_lock(**packages):
    base = {"": {"name": "root", "workspaces": ["libs/*"]}, "libs/engines": {"name": "engines"},
            "node_modules/engines": {"resolved": "libs/engines", "link": True},
            "node_modules/vitest": {"version": "4.1.12", "resolved": "https://registry.npmjs.org/vitest/-/v.tgz",
                                    "integrity": INTEGRITY}}
    base.update(packages)
    return json.dumps({"name": "root", "lockfileVersion": 3, "packages": base})


def cargo_lock(*extra):
    rows = ['version = 4', '', '[[package]]', 'name = "demo"', 'version = "0.1.0"', 'dependencies = ["serde"]', '',
            '[[package]]', 'name = "serde"', 'version = "1.0.0"', f'source = "{target_run.CRATES_IO}"',
            f'checksum = "{CHECKSUM}"', ''] + list(extra)
    return "\n".join(rows) + "\n"


# A synthetic `cargo test ... 2>&1`: two test binaries, an ignored test, a should-panic test, a failure and doc-tests.
LIBTEST = """   Compiling demo v0.1.0 (/tmp/work)
    Finished `test` profile [unoptimized + debuginfo] target(s) in 1.00s
     Running unittests src/lib.rs (/tmp/target/debug/deps/demo-0123456789abcdef)

running 3 tests
test tests::adds ... ok
test tests::slow ... ignored, needs hardware
test tests::rejects - should panic ... ok

test result: ok. 2 passed; 0 failed; 1 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running tests/api.rs (/tmp/target/debug/deps/api-fedcba9876543210)

running 1 test
test round_trip ... FAILED

failures:

---- round_trip stdout ----
thread 'round_trip' panicked at tests/api.rs:3:5

failures:
    round_trip

test result: FAILED. 0 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

   Doc-tests demo

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
"""


def jest_report(asserts, *, load_failed=(), **totals):
    results = [{"name": "/tmp/work/libs/engines/src/a.spec.ts", "status": "passed",
                "assertionResults": [{"fullName": n, "status": s} for n, s in asserts]}]
    results += [{"name": f"/tmp/work/{n}", "status": "failed", "assertionResults": []} for n in load_failed]
    counts = {"numPassedTests": sum(s == "passed" for _, s in asserts),
              "numFailedTests": sum(s == "failed" for _, s in asserts),
              "numPendingTests": sum(s in ("pending", "skipped") for _, s in asserts),
              "numTodoTests": sum(s == "todo" for _, s in asserts)}
    counts.update(totals)
    return json.dumps(dict(counts, testResults=results))


class FakeRunner:
    """A `container.Runner` that answers every command with one result and remembers what it was asked."""

    def __init__(self, result):
        self.result, self.calls = result, []

    def run(self, cmd, *, cwd=".", stdin=b"", timeout_s):
        self.calls.append((cmd, cwd))
        return self.result


class SuiteConfigTest(unittest.TestCase):
    """E513: the operator's suites are read strictly; a path that leaves the tree never reaches a container."""

    def test_a_cargo_and_a_node_suite_load_as_written(self):
        core, engines = target_run.load_suites([CARGO_SUITE, NODE_SUITE], "target.suites")
        self.assertEqual((core.kind, core.root, core.cwd, core.workspaces), ("cargo", ".", ".", ()))
        self.assertEqual((engines.cwd, engines.workspaces), ("libs/engines", ("libs/engines", "libs/testing")))

    def test_what_is_refused(self):
        for bad in ([], [dict(CARGO_SUITE, kind="go")], [dict(CARGO_SUITE, root="../up")],
                    [dict(CARGO_SUITE, cwd="/abs")], [dict(NODE_SUITE, workspaces=["libs/../x"])],
                    [dict(CARGO_SUITE, workspaces=["a"])], [dict(CARGO_SUITE, cmd="true\nfalse")],
                    [dict(CARGO_SUITE, extra=1)], [CARGO_SUITE, dict(NODE_SUITE, id="core")],
                    [dict(CARGO_SUITE, id="Core!")]):
            with self.subTest(bad=bad), self.assertRaises(ConfigError):
                target_run.load_suites(bad, "target.suites")


class LockRulesTest(unittest.TestCase):
    """E513: fetch installs a lock only when every package comes from the public registry with its integrity hash, or
    from the tree itself, so what runs offline is exactly what the lock names."""

    def test_a_registry_lock_with_links_and_bundles_passes(self):
        self.assertEqual(target_run.npm_lock_problems(npm_lock(**{
            "node_modules/a/node_modules/b": {"inBundle": True}})), [])
        self.assertEqual(target_run.cargo_lock_problems(cargo_lock()), [])

    def test_a_package_from_elsewhere_is_named(self):
        for resolved in ("https://evil.example/vitest.tgz", "git+ssh://git@github.com/x/y.git#abc", "file:../x.tgz",
                         "https://registry.npmjs.org.evil.example/v.tgz"):
            with self.subTest(resolved=resolved):
                found = target_run.npm_lock_problems(npm_lock(**{
                    "node_modules/x": {"resolved": resolved, "integrity": INTEGRITY}}))
                self.assertEqual(found, ["node_modules/x: resolved outside https://registry.npmjs.org/"])

    def test_a_package_without_a_sha512_hash_is_named(self):
        for integrity in (None, "sha1-abc"):
            pkg = {"resolved": "https://registry.npmjs.org/x/-/x.tgz"}
            if integrity:
                pkg["integrity"] = integrity
            with self.subTest(integrity=integrity):
                self.assertEqual(target_run.npm_lock_problems(npm_lock(**{"node_modules/x": pkg})),
                                 ["node_modules/x: no sha512 integrity"])

    def test_links_and_workspaces_stay_in_the_tree(self):
        self.assertEqual(target_run.npm_lock_problems(npm_lock(**{
            "node_modules/out": {"resolved": "../../etc", "link": True}, "../outside": {"name": "o"}})),
            ["../outside: a workspace outside the tree", "node_modules/out: a link outside the tree"])

    def test_an_old_or_broken_npm_lock_is_refused(self):
        self.assertTrue(target_run.npm_lock_problems(json.dumps({"lockfileVersion": 1, "dependencies": {}})))
        self.assertEqual(target_run.npm_lock_problems("{"), ["package-lock.json is not JSON"])

    def test_a_crate_from_git_or_without_checksum_is_named(self):
        git = ['[[package]]', 'name = "g"', 'version = "0.1.0"', 'source = "git+https://github.com/x/g#abc"', '']
        bare = ['[[package]]', 'name = "c"', 'version = "1.0.0"', f'source = "{target_run.CRATES_IO}"', '']
        self.assertEqual(target_run.cargo_lock_problems(cargo_lock(*git, *bare)),
                         ["g 0.1.0: source git+https://github.com/x/g#abc is not crates.io", "c 1.0.0: no checksum"])
        self.assertTrue(target_run.cargo_lock_problems('[[package]]\nname = "a"\n'))  # a lock with no version

    def test_lock_problems_reads_each_named_lock_and_only_plain_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp)
            suites = target_run.load_suites([CARGO_SUITE, NODE_SUITE], "s")
            self.assertEqual(sorted(p.split(":")[0] for p in target_run.lock_problems(tree, suites)),
                             ["Cargo.lock", "package-lock.json"])
            (tree / "Cargo.lock").write_text(cargo_lock())
            (tree / "package-lock.json").write_text(npm_lock())
            self.assertEqual(target_run.lock_problems(tree, suites), [])


class SkeletonTest(unittest.TestCase):
    """E513: npm sees only the manifests the lock names: no `.npmrc`, no script file, no source."""

    def test_only_the_lock_and_package_files_are_copied_without_scripts(self):  # skeleton_keeps_scripts
        """npm 10.9 runs a linked workspace's `prepare` even under --ignore-scripts (measured on the image): the
        scripts must not reach npm at all."""
        manifest = json.dumps({"name": "w", "workspaces": ["libs/*"], "dependencies": {"vitest": "^4"},
                               "scripts": {"prepare": "node evil.js", "postinstall": "node evil.js"}})
        with tempfile.TemporaryDirectory() as tmp:
            tree, out = Path(tmp) / "tree", Path(tmp) / "out"
            for rel, text in {"package.json": manifest, "package-lock.json": npm_lock(), ".npmrc": "x",
                              "libs/engines/package.json": manifest, "libs/engines/src/a.ts": "x",
                              "libs/engines/.npmrc": "x", "scripts/postinstall.js": "x"}.items():
                (tree / rel).parent.mkdir(parents=True, exist_ok=True)
                (tree / rel).write_text(text)
            out.mkdir()
            copied = target_run.npm_skeleton(tree, ".", out)
            self.assertEqual(copied, ["package.json", "package-lock.json", "libs/engines/package.json"])
            self.assertEqual(sorted(p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()),
                             sorted(copied))
            for rel in ("package.json", "libs/engines/package.json"):
                self.assertEqual(json.loads((out / rel).read_text()),
                                 {"name": "w", "workspaces": ["libs/*"], "dependencies": {"vitest": "^4"}})
            self.assertEqual((out / "package-lock.json").read_text(), npm_lock())
            (tree / "package.json").write_text("[1]")
            with self.assertRaises(target_run.TargetError):
                target_run.npm_skeleton(tree, ".", out)

    @posix_only
    def test_a_linked_manifest_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp) / "tree"
            tree.mkdir()
            (tree / "package-lock.json").write_text(npm_lock())
            (tree / "package.json").symlink_to("/etc/hostname")
            with self.assertRaises(target_run.TargetError):
                target_run.npm_skeleton(tree, ".", Path(tmp))


def _script_line(script, word):
    return next(line for line in script.splitlines() if line.lstrip().startswith(word))


class FetchArgvTest(unittest.TestCase):
    """E513 (critique F-4): the fetch container has the network, so it must execute nothing the tree holds."""

    def setUp(self):
        self.suite = target_run.load_suites([NODE_SUITE], "s")[0]

    def test_npm_runs_no_lifecycle_script_and_reads_only_the_skeleton(self):  # npm_scripts_enabled
        argv = target_run.fetch_npm_argv("docker", "img", "n", Path("/sk"), Path("/o"), self.suite)
        script = argv[argv.index("-c") + 1]
        npm = _script_line(script, "npm ")
        self.assertTrue(npm.startswith("npm ci --ignore-scripts "), npm)
        self.assertIn("--registry=https://registry.npmjs.org/", npm)
        self.assertIn(f"type=bind,src={Path('/sk')},dst=/skel,readonly", argv)
        self.assertEqual(argv[-4:], [".", "npm-engines.tar", "--workspace=libs/engines", "--workspace=libs/testing"])

    def test_cargo_vendors_exactly_the_lock_from_outside_the_tree(self):  # cargo_unlocked fetch_reads_tree_config
        argv = target_run.fetch_cargo_argv("docker", "img", "n", Path("/t"), Path("/o"), [".", "gateway"])
        script = argv[argv.index("-c") + 1]
        cargo = _script_line(script, "cargo ")
        self.assertTrue(cargo.startswith("cargo vendor --locked "), cargo)
        cds = [line.split()[1] for line in script.splitlines()[:script.splitlines().index(cargo)]
               if line.startswith("cd ")]
        self.assertEqual(cds, ["/tmp"])  # cargo reads configuration from its working directory up, never the tree's
        self.assertEqual(argv[-2:], ["/src/Cargo.toml", "/src/gateway/Cargo.toml"])
        self.assertIn(f"type=bind,src={Path('/t')},dst=/src,readonly", argv)

    @posix_only
    def test_the_cargo_script_syncs_every_later_manifest_into_one_vendor_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            bin_dir = Path(tmp)
            for tool, body in (("cargo", 'printf "%s\\n" "$@" > "$LOG"'), ("tar", "true")):
                (bin_dir / tool).write_text(f"#!/bin/sh\n{body}\n")
                (bin_dir / tool).chmod(0o755)
            env = dict(os.environ, PATH=f"{bin_dir}:{os.environ['PATH']}", LOG=str(bin_dir / "log"))
            subprocess.run(["sh", "-c", target_run.FETCH_CARGO, "fetch", "/src/Cargo.toml", "/src/a/Cargo.toml",
                            "/src/b/Cargo.toml"], env=env, check=True)
            self.assertEqual((bin_dir / "log").read_text().split(),
                             ["vendor", "--locked", "--manifest-path", "/src/Cargo.toml", "--sync",
                              "/src/a/Cargo.toml", "--sync", "/src/b/Cargo.toml", "/tmp/vendor"])

    def test_fetch_stops_at_a_lock_problem_and_runs_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree, out = Path(tmp) / "tree", Path(tmp) / "out"
            tree.mkdir()
            (tree / "package-lock.json").write_text(npm_lock(**{"node_modules/x": {"resolved": "https://e.x/x.tgz"}}))
            doc = target_run.fetch(tree, (self.suite,), out, image="img", timeout_s=1, docker="/nonexistent/docker")
            self.assertEqual((doc["ok"], doc["runs"], doc["files"]), (False, [], {}))
            self.assertEqual(json.loads((out / "deps.json").read_text())["problems"], doc["problems"])


class RunArgvTest(unittest.TestCase):
    """E513: the tree's code runs with no network, confined as every untrusted run is (`container.sandbox_flags`)."""

    def test_the_run_has_no_network_and_mounts_read_only(self):  # run_with_network
        runner = TargetRunner("img@sha256:" + "a" * 64, "/s", "/d", ("npm-engines.tar",), True)
        argv = runner.argv("n", "cargo test", "libs/engines")
        self.assertEqual([argv[i + 1] for i, a in enumerate(argv) if a == "--network"], ["none"])
        self.assertEqual(argv[argv.index("--network"):argv.index("--network") + len(sandbox_flags(network="none"))],
                         sandbox_flags(network="none", tmpfs=runner.tmpfs, memory=runner.memory))
        mounts = [argv[i + 1] for i, a in enumerate(argv) if a == "--mount"]
        self.assertEqual(mounts, ["type=bind,src=/s,dst=/src,readonly", "type=bind,src=/d,dst=/deps,readonly"])
        envs = [argv[i + 1] for i, a in enumerate(argv) if a == "--env"]
        self.assertEqual(envs, ["SNOWBALL_NPM=npm-engines.tar", "SNOWBALL_VENDOR=1", "SNOWBALL_CWD=libs/engines",
                                "SNOWBALL_CMD=cargo test"])

    def test_the_control_tree_gets_the_image_and_nothing_fetched(self):
        argv = TargetRunner("img", "/empty", None, ("npm-engines.tar",), True).argv("n", "true", ".")
        self.assertEqual([argv[i + 1] for i, a in enumerate(argv) if a == "--mount"],
                         ["type=bind,src=/empty,dst=/src,readonly"])
        self.assertIn("SNOWBALL_NPM=", argv)
        self.assertIn("SNOWBALL_VENDOR=", argv)

    def test_for_suites_names_the_tars_fetch_makes(self):
        runner = TargetRunner.for_suites("img", "/s", "/d", target_run.load_suites([CARGO_SUITE, NODE_SUITE], "s"))
        self.assertEqual((runner.npm, runner.vendor), (("npm-engines.tar",), True))

    def test_the_prelude_ends_in_the_shared_exit_code_rule(self):
        self.assertTrue(target_run.PRELUDE.endswith(target_run.RUN))
        with self.assertRaises(ValueError):
            TargetRunner("img", "/s").run("true", cwd="../up", timeout_s=1)

    @posix_only
    def test_exit_code_and_timeout_through_a_fake_docker(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "docker"
            fake.write_text('#!/bin/sh\nfor a in "$@"; do case "$a" in SNOWBALL_CMD=*) cmd="${a#SNOWBALL_CMD=}";; '
                            'esac; done\n[ "$1" = rm ] && exit 0\nexec sh -c "$cmd"\n')
            fake.chmod(0o755)
            runner = TargetRunner("img", tmp, tmp, docker=str(fake))
            self.assertEqual(runner.run("exit 7", timeout_s=10).exit_code, 7)
            self.assertTrue(runner.run("sleep 5", timeout_s=1).timed_out)
            self.assertEqual(len(runner.executed), 2)


class DepsPinTest(unittest.TestCase):
    """E513: the run mounts exactly the bytes fetch made."""

    def test_a_changed_missing_or_extra_tar_is_named(self):
        with tempfile.TemporaryDirectory() as tmp:
            deps = Path(tmp)
            (deps / "cargo-vendor.tar").write_bytes(b"vendor")
            pinned = {"cargo-vendor.tar": hashlib.sha256(b"vendor").hexdigest()}
            self.assertEqual(target_run.deps_problems(deps, pinned), [])
            (deps / "cargo-vendor.tar").write_bytes(b"vendor!")
            (deps / "npm-x.tar").write_bytes(b"x")
            self.assertEqual(target_run.deps_problems(deps, dict(pinned, **{"npm-y.tar": "0" * 64})),
                             ["cargo-vendor.tar: not the fetched bytes", "npm-y.tar: missing",
                              "npm-x.tar: not fetched"])


class ReportParsingTest(unittest.TestCase):
    """E513 (red team T4): a suite counts as run only by what its runner printed, case by case."""

    def test_libtest_cases_are_named_by_binary_and_add_up(self):
        cases, consistent = target_run.parse_libtest(LIBTEST)
        self.assertEqual(cases, [("demo::tests::adds", "passed"), ("demo::tests::slow", "skipped"),
                                 ("demo::tests::rejects - should panic", "passed"), ("api::round_trip", "failed")])
        self.assertTrue(consistent)

    def test_a_case_line_the_summary_does_not_count_is_inconsistent(self):
        forged = LIBTEST.replace("test round_trip ... FAILED", "test round_trip ... FAILED\ntest extra ... ok")
        self.assertFalse(target_run.parse_libtest(forged)[1])

    def test_a_jest_shaped_report_is_read_after_any_noise(self):
        text = "vitest noise {\n" + jest_report([("adds", "passed"), ("later", "todo"), ("off", "skipped")])
        cases, consistent = target_run.parse_jest_json(text)
        self.assertEqual(cases, [("libs/engines/src/a.spec.ts::adds", "passed"),
                                 ("libs/engines/src/a.spec.ts::later", "skipped"),
                                 ("libs/engines/src/a.spec.ts::off", "skipped")])
        self.assertTrue(consistent)

    def test_a_spec_file_that_failed_to_load_is_a_failed_case(self):
        cases, consistent = target_run.parse_jest_json(jest_report([("adds", "passed")], load_failed=["b.spec.ts"]))
        self.assertIn(("b.spec.ts::(spec file failed to load)", "failed"), cases)
        self.assertTrue(consistent)

    def test_totals_that_disagree_or_no_report_are_inconsistent(self):
        self.assertFalse(target_run.parse_jest_json(jest_report([("adds", "passed")], numPassedTests=5))[1])
        self.assertEqual(target_run.parse_jest_json("no report here"), ([], False))


class RunSuiteTest(unittest.TestCase):
    """E513: green means the command exited 0 on its own, showed at least one test, none failed, and its lines add
    up to its own summary."""

    SUITE = Suite("core", "cargo", ".", ".", "cargo test")
    PASSING = LIBTEST.replace("test round_trip ... FAILED", "test round_trip ... ok").replace(
        "FAILED. 0 passed; 1 failed", "ok. 1 passed; 0 failed")

    def run_with(self, stdout, exit_code=0, timed_out=False):
        runner = FakeRunner(RunResult(exit_code, stdout.encode(), b"", 5, timed_out))
        return target_run.run_suite(runner, self.SUITE, 60), runner

    def test_a_passing_suite_is_green_with_its_cases(self):
        res, runner = self.run_with(self.PASSING)
        self.assertEqual((res["ok"], res["counts"]), (True, {"passed": 3, "failed": 0, "skipped": 1, "total": 4}))
        self.assertEqual(runner.calls, [("cargo test", ".")])

    def test_exit_0_with_no_test_is_not_green(self):  # suite_without_tests_green
        res, _ = self.run_with("    Finished `test` profile\n")
        self.assertEqual((res["ok"], res["counts"]["total"], res["consistent"]), (False, 0, True))

    def test_lines_that_disagree_with_the_summary_are_not_green(self):
        res, _ = self.run_with(self.PASSING.replace("test tests::adds ... ok", "test tests::adds ... ok\n"
                                                    "test tests::invented ... ok"))
        self.assertEqual((res["ok"], res["consistent"]), (False, False))

    def test_a_failure_a_timeout_or_a_docker_fault_is_not_green(self):
        self.assertFalse(self.run_with(LIBTEST, exit_code=101)[0]["ok"])
        self.assertFalse(self.run_with(self.PASSING, timed_out=True)[0]["ok"])
        fault = self.run_with("", exit_code=125)[0]
        self.assertEqual((fault["ok"], fault["runner_fault"]), (False, True))


class ToolchainDriftTest(unittest.TestCase):
    """E513: a tree naming another Rust toolchain is reported, never followed."""

    def test_drift_is_said_and_agreement_or_absence_is_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp)
            self.assertIsNone(target_run.toolchain_drift(tree, "1.88.0"))
            (tree / "rust-toolchain.toml").write_text('[toolchain]\nchannel = "1.88.0"\n')
            self.assertIsNone(target_run.toolchain_drift(tree, "1.88.0"))
            (tree / "rust-toolchain.toml").write_text('[toolchain]\nchannel = "nightly"\n')
            self.assertEqual(target_run.toolchain_drift(tree, "1.88.0"),
                             "rust-toolchain.toml names nightly; the referee ran 1.88.0")


def _rep(**kw):
    return dict({"cmd": "cargo test 2>&1", "expect_stdout_contains": "FAILED", "correct_stdout_contains": "ok."}, **kw)


class RivalTargetImageTest(unittest.TestCase):
    """E513 (red team T5): the rival can send a reproducer for the target image; only a review that offers it says
    so; a target reproducer is told apart from the same command in Python, and one the referee cannot run never
    proves a defect nor clears a kept one."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.box = ToolBox(Path(self.tmp.name))
        (Path(self.tmp.name) / "a.rs").write_text("fn a() {}\n")

    def tearDown(self):
        self.tmp.cleanup()

    def verdict(self, rep, box=None):
        return validate_verdict({"verdict": "refuted", "attempts": [
            {"claim": "c", "evidence_refs": [{"path": "a.rs", "line_start": 1, "line_end": 1}], "reproducer": rep}]},
            box or ToolBox(Path(self.tmp.name), target=True))["attempts"][0]["reproducer"]

    @staticmethod
    def reproducer_schema(tools):
        tool = next(t for t in tools if t["name"] == "submit_verdict")
        return tool["input_schema"]["properties"]["attempts"]["items"]["properties"]["reproducer"]

    def test_the_image_is_kept_only_when_it_is_the_target(self):
        self.assertEqual(self.verdict(_rep(image="target"))["image"], TARGET_IMAGE)
        self.assertNotIn("image", self.verdict(_rep()))
        with self.assertRaises(ValueError):
            self.verdict(_rep(image="python:3.12"))
        self.assertEqual(self.reproducer_schema(rival.tools(True))["properties"]["image"]["enum"], [TARGET_IMAGE])

    def test_no_offer_no_field(self):  # target_field_always_offered target_image_accepted_unoffered
        """E516 at the merge: the field exists only where the review offers the image; elsewhere the rival's tools
        are what they were before E513 and an `image` it sends is dropped like any other field it may not send,
        so its reproducer runs in Python as before. The flag reaches the rival's MCP server through its argv."""
        self.assertIs(rival.tools(False), rival.TOOLS)
        self.assertNotIn("image", self.reproducer_schema(rival.TOOLS)["properties"])
        self.assertNotIn("image", self.verdict(_rep(image="target"), self.box))
        self.assertNotIn("image", self.verdict(_rep(image="python:3.12"), self.box))
        offered = rival.tools(True)
        self.assertEqual([t for t in offered if t["name"] != "submit_verdict"],
                         [t for t in rival.TOOLS if t["name"] != "submit_verdict"])  # the read tools either way
        self.assertNotIn("image", self.reproducer_schema(rival.TOOLS)["properties"])  # tools(True) copied, never wrote
        with tempfile.TemporaryDirectory() as tmp:
            for target, flag in ((False, []), (True, ["--target"])):
                argv = rival._cli_argv("claude", RivalConfig(model="claude-sonnet-5-5", effort="low", max_turns=1,
                                                             per_run_cap_usd_micros=1),
                                       Path(tmp), Path(tmp), 1, target=target)
                self.assertTrue(argv)
                server = json.loads((Path(tmp) / "mcp.json").read_text())["mcpServers"][rival.MCP_SERVER]
                self.assertEqual(server["args"][8:], flag)
                with mock.patch.object(rival_mcp, "serve") as serve, mock.patch.object(rival_mcp, "sys"):
                    rival_mcp.main(server["args"][2:])
                listed = serve.call_args.args[0].handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
                schema = self.reproducer_schema([dict(t, input_schema=t["inputSchema"])
                                                 for t in listed["result"]["tools"]])
                self.assertEqual("image" in schema["properties"], target)

    def test_a_python_reproducer_is_signed_as_before(self):  # python_reproducer_signed_with_image
        """E516 at the merge: the signed state keeps `image` only on a reproducer that names it."""
        self.assertEqual(decide._reproducer(_rep()), {k: _rep().get(k) for k in rival.REPRODUCER_FIELDS
                                                      if k != "image"})
        self.assertEqual(decide._reproducer(_rep(image="target"))["image"], TARGET_IMAGE)

    def test_target_protocol_only_when_offered(self):
        cfg = RivalConfig(model="claude-sonnet-5-5", effort="low", max_turns=1, per_run_cap_usd_micros=1)
        for target, text in ((False, "s" + rival.PROTOCOL), (True, "s" + rival.PROTOCOL + rival.TARGET_PROTOCOL)):
            out = rival.run_rival(cfg, claude_bin=None, seat_prompt="s", context="c", tree_root=Path(self.tmp.name),
                                  budget_usd_micros=1, max_prompt_chars=10 ** 6, pinned_version="x", target=target)
            self.assertEqual(out.prompt_sha256, hashlib.sha256((text + "\nc").encode()).hexdigest())
        self.assertIn('image "target"', rival.TARGET_PROTOCOL)

    def test_a_python_reproducers_key_is_unchanged_and_a_target_one_differs(self):
        rep = _rep()
        old = hashlib.sha256(canon.canonical({"cmd": rep["cmd"], **{k: rep.get(k) for k in rival.SYMPTOM}}))
        self.assertEqual(reproduce.reproducer_key(rep), old.hexdigest()[:16])
        self.assertEqual(reproduce.reproducer_key(dict(rep, image=None)), old.hexdigest()[:16])
        self.assertNotEqual(reproduce.reproducer_key(_rep(image="target")), old.hexdigest()[:16])

    def test_a_target_reproducer_runs_on_the_target_runners(self):  # target_repro_runs_in_python
        shown = RunResult(1, b"test x ... FAILED\n", b"", 1)
        python, target, control = FakeRunner(shown), FakeRunner(shown), FakeRunner(RunResult(1, b"", b"", 1))
        res = reproduce.run_one(python, python, _rep(image="target"), 9, target=(target, control))
        self.assertEqual((res["reproduced"], len(python.calls), len(target.calls), len(control.calls)),
                         (True, 0, 1, 1))
        res = reproduce.run_one(python, control, _rep(), 9, target=(target, control))
        self.assertEqual((res["reproduced"], len(python.calls), len(target.calls)), (True, 1, 1))

    def test_without_a_target_image_the_rivals_reproducer_proves_nothing(self):
        python = FakeRunner(RunResult(1, b"FAILED", b"", 1))
        res = reproduce.run_reproducers(python, [{"reproducer": _rep(image="target")}], 9, control=python)
        self.assertEqual((res[0]["reproduced"], res[0]["runner_fault"], python.calls), (False, False, []))
        self.assertIn("no target image", res[0]["stderr_tail"])

    def test_without_a_target_image_a_kept_reproducer_is_a_runner_fault(self):  # missing_target_kept_not_fault
        python = FakeRunner(RunResult(0, b"ok.", b"", 1))
        res = reproduce.run_state_reproducers(python, [{"key": "k", "source": "refutation",
                                                        "reproducer": _rep(image="target")}], 9, control=python)
        self.assertEqual((res[0]["runner_fault"], res[0]["shown"], python.calls), (True, False, []))

    def test_the_signed_state_keeps_the_image(self):
        self.assertIn("image", rival.REPRODUCER_FIELDS)
        self.assertTrue(state._reproducer(_rep(image="target")))


@unittest.skipUnless(os.environ.get("SNOWBALL_TARGET_IMAGE") and shutil.which("docker"),
                     "the operator's acceptance run: set SNOWBALL_TARGET_IMAGE to a built images/target image")
class LiveTargetImageTest(unittest.TestCase):
    """E513 acceptance on the real image, with synthetic trees: a planted lifecycle script and a planted cargo
    configuration never run in fetch, the run has no network, and a seeded Rust defect is reproduced on its head
    and not on the empty control tree."""

    IMAGE = os.environ.get("SNOWBALL_TARGET_IMAGE", "")

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, tree, files):
        for rel, text in files.items():
            (tree / rel).parent.mkdir(parents=True, exist_ok=True)
            (tree / rel).write_text(text, newline="\n")

    def test_a_planted_postinstall_and_npmrc_never_run_in_fetch(self):
        tree, out = self.base / "tree", self.base / "out"
        hook = "node -e \"require('fs').writeFileSync('/out/PWNED-' + process.env.npm_lifecycle_event, '')\""
        scripts = {k: hook for k in ("preinstall", "install", "postinstall", "prepare")}
        self.write(tree, {
            "package.json": json.dumps({"name": "root", "version": "1.0.0", "workspaces": ["pkg"], "scripts": scripts}),
            "pkg/package.json": json.dumps({"name": "pkg", "version": "1.0.0", "scripts": scripts}),
            ".npmrc": "ignore-scripts=false\n",
            "package-lock.json": json.dumps({"name": "root", "version": "1.0.0", "lockfileVersion": 3, "packages": {
                "": {"name": "root", "version": "1.0.0", "workspaces": ["pkg"]},
                "pkg": {"name": "pkg", "version": "1.0.0"},
                "node_modules/pkg": {"resolved": "pkg", "link": True}}})})
        suites = target_run.load_suites([{"id": "web", "kind": "node", "root": ".", "cwd": ".", "cmd": "true"}], "s")
        doc = target_run.fetch(tree, suites, out, image=self.IMAGE, timeout_s=600)
        self.assertTrue(doc["ok"], doc)
        self.assertEqual(sorted(p.name for p in out.iterdir()), ["deps.json", "npm-web.tar"])

    def test_a_planted_cargo_config_is_not_read_and_a_seeded_rust_defect_is_reproduced(self):
        tree, deps, empty = self.base / "tree", self.base / "deps", self.base / "empty"
        empty.mkdir()
        self.write(tree, {
            "Cargo.toml": '[package]\nname = "demo"\nversion = "0.1.0"\nedition = "2021"\n\n'
                          '[dependencies]\ncfg-if = "=1.0.4"\n',
            "Cargo.lock": 'version = 4\n\n[[package]]\nname = "cfg-if"\nversion = "1.0.4"\n'
                          f'source = "{target_run.CRATES_IO}"\nchecksum = "{CFG_IF}"\n\n'
                          '[[package]]\nname = "demo"\nversion = "0.1.0"\ndependencies = ["cfg-if"]\n',
            "rust-toolchain.toml": '[toolchain]\nchannel = "nightly-2020-01-01"\n',
            ".cargo/config.toml": '[build]\nrustc-wrapper = "/src/evil.sh"\n[net]\noffline = true\n'
                                  '[source.crates-io]\nreplace-with = "evil"\n[source.evil]\ndirectory = "/none"\n',
            "evil.sh": "#!/bin/sh\ntouch /out/PWNED-cargo\nexec \"$@\"\n",
            "src/lib.rs": "pub fn double(x: i32) -> i32 { x + x + 1 }\n"
                          "#[cfg(test)]\nmod tests {\n    #[test]\n"
                          "    fn doubles() { assert_eq!(super::double(2), 4); }\n}\n"})
        (tree / "evil.sh").chmod(0o755)
        suites = target_run.load_suites([{"id": "demo", "kind": "cargo", "root": ".", "cwd": ".",
                                          "cmd": "cargo test --locked --offline 2>&1"}], "s")
        doc = target_run.fetch(tree, suites, deps, image=self.IMAGE, timeout_s=600)
        self.assertTrue(doc["ok"], doc)
        self.assertEqual(sorted(p.name for p in deps.iterdir()), ["cargo-vendor.tar", "deps.json"])
        self.assertEqual(target_run.deps_problems(deps, doc["files"]), [])
        shutil.rmtree(tree / ".cargo")  # the run reads it (the tree's own code runs there) and it breaks its own build
        head = TargetRunner.for_suites(self.IMAGE, str(tree), str(deps), suites)
        control = TargetRunner(self.IMAGE, str(empty))
        res = target_run.run_suite(head, suites[0], 900)
        self.assertEqual((res["ok"], res["counts"]["failed"], res["consistent"]), (False, 1, True), res)
        offline = head.run("node -e \"fetch('https://registry.npmjs.org').then(() => console.log('NET'), "
                           "() => console.log('NONET'))\"", timeout_s=120)
        self.assertEqual(offline.stdout.strip(), b"NONET")
        rep = {"cmd": "cargo test --locked --offline doubles 2>&1", "expect_stdout_contains": "left: 5",
               "correct_stdout_contains": "test result: ok. 1 passed", "image": "target"}
        python = FakeRunner(RunResult(0, b"", b"", 1))
        result = reproduce.run_one(python, python, rep, 900, target=(head, control))
        self.assertEqual((result["reproduced"], result["tautological"], python.calls), (True, False, []), result)


if __name__ == "__main__":
    unittest.main()
