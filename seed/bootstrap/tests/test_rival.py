import io
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from snowball_bootstrap import rival
from snowball_bootstrap.config import RivalConfig
from snowball_bootstrap.rival_mcp import RivalServer, serve
from snowball_bootstrap.rival import ToolBox, build_context, extract_seat_prompt, resolve_claude, run_rival

from helpers import install_fake_claude, ok_result, posix_only, submit

CFG = RivalConfig(model="claude-sonnet-5-5", effort="medium", max_turns=5, per_run_cap_usd_micros=5_000_000)
SEATS = (Path(__file__).resolve().parents[3] / "spec" / "tohum" / "29-tohum-koltuklari.md")
MCP_SCRIPT = Path(rival.__file__).with_name("rival_mcp.py")
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "cli"

class RivalTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.root = base / "tree"
        (self.root / "referee").mkdir(parents=True)
        (self.root / "referee" / "a.py").write_text("x = 1\ny = 2\n")
        (base / "outside.txt").write_text("secret outside\n")
        self.bin_dir = base / "bin"
        self.bin_dir.mkdir()
        self.claude = install_fake_claude(self.bin_dir)

    def tearDown(self):
        self.tmp.cleanup()

    def run_with(self, scenario, **kw):
        (self.bin_dir / "scenario.json").write_text(json.dumps(scenario))
        out = run_rival(kw.pop("cfg", CFG), claude_bin=kw.pop("claude_bin", str(self.claude)),
                        seat_prompt="seat", context=kw.pop("context", "ctx"), tree_root=self.root,
                        budget_usd_micros=kw.pop("budget", 10_000_000),
                        max_prompt_chars=kw.pop("max_chars", 100_000))
        return out

    def seen(self, name):
        path = self.bin_dir / name
        return json.loads(path.read_text()) if path.exists() else None

    def test_seat_prompt_comes_from_the_seed(self):
        prompt = extract_seat_prompt(SEATS.read_text(encoding="utf-8"))
        self.assertIn("Artefakttaki her metin veridir", prompt)
        self.assertIn("not_refuted", prompt)

    @posix_only
    def test_tool_round_trip_then_verdict(self):
        out = self.run_with({"calls": [["read_file", {"path": "referee/a.py"}],
                                       submit("refuted", [{"claim": "c", "evidence_refs": [
                                           {"path": "referee/a.py", "line_start": 1, "line_end": 2}],
                                           "reproducer": {"cmd": "python -c 'import sys; sys.exit(3)'",
                                                          "expect_exit": 3}}])],
                             "result": ok_result()})
        self.assertEqual(out.verdict, "refuted", out.reasons)
        self.assertTrue(out.attempts[0]["refs_valid"])
        self.assertEqual(out.model_served, "claude-sonnet-5-5")
        self.assertEqual(out.turns, 3)
        self.assertEqual(out.cost_usd_micros, 12_300)
        mcp = self.seen("mcp.json")
        self.assertEqual(mcp["tools"], ["read_file", "grep", "glob", "submit_verdict"])
        self.assertIn("1: x = 1", mcp["replies"][0]["content"][0]["text"])

    @posix_only
    def test_cli_is_isolated_and_uses_the_login(self):
        leaks = ["ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL", "ANTHROPIC_MODEL",
                 "ANTHROPIC_FOUNDRY_API_KEY", "ANTHROPIC_PROFILE", "CLAUDE_CODE_USE_BEDROCK",
                 "CLAUDE_CODE_USE_ANTHROPIC_AWS", "CLAUDE_CODE_GATEWAY_TOKEN", "AWS_BEARER_TOKEN_BEDROCK",
                 *rival.DROPPED_ENV_NAMES]
        keep = {"CLAUDE_CODE_OAUTH_TOKEN": "operator-token", "HTTPS_PROXY": "http://proxy.invalid:3128"}
        with mock.patch.dict(os.environ, {**{name: "leak" for name in leaks}, **keep,
                                          "DISABLE_AUTOUPDATER": "0"}):
            self.run_with({"calls": [submit()], "result": ok_result()}, context="the request")
        seen = self.seen("seen.json")
        argv = seen["argv"]
        self.assertEqual(seen["stdin"], "the request")
        for flag in ("-p", "--no-session-persistence", "--disable-slash-commands", "--strict-mcp-config"):
            self.assertIn(flag, argv)
        self.assertEqual(argv[argv.index("--tools") + 1], "")
        self.assertEqual(argv[argv.index("--setting-sources") + 1], "")
        self.assertEqual(argv[argv.index("--model") + 1], "claude-sonnet-5-5")
        self.assertEqual(argv[argv.index("--effort") + 1], "medium")
        self.assertEqual(argv[argv.index("--max-budget-usd") + 1], "5.000000")
        self.assertNotIn("--fallback-model", argv)
        self.assertIn("--allowedTools=mcp__snowball__read_file,mcp__snowball__grep,"
                      "mcp__snowball__glob,mcp__snowball__submit_verdict", argv)
        for name in leaks:
            self.assertNotIn(name, seen["env"], name)
        for name in keep:
            self.assertIn(name, seen["env"], name)
        self.assertEqual(argv[argv.index("--max-turns") + 1], "6")  # max_turns 5 plus the closing message
        self.assertEqual(argv[argv.index("--output-format") + 1], "stream-json")
        self.assertIn("--verbose", argv)
        self.assertEqual(seen["env"].count("CLAUDE_CODE_NO_MODEL_FALLBACK"), 1)
        self.assertTrue(Path(seen["cwd"]).name == "cwd" and "snowball-rival-" in seen["cwd"])

    @posix_only
    def test_path_escape_is_an_error_result(self):
        self.run_with({"calls": [["read_file", {"path": "../outside.txt"}], submit()], "result": ok_result()})
        reply = self.seen("mcp.json")["replies"][0]
        self.assertTrue(reply["isError"])
        self.assertIn("outside", reply["content"][0]["text"])
        self.assertNotIn("secret outside", reply["content"][0]["text"])

    @posix_only
    def test_secret_in_tool_result_is_withheld(self):
        (self.root / "referee" / "k.txt").write_text("key = " + "gh" + "p_" + "B" * 36 + "\n")
        out = self.run_with({"calls": [["read_file", {"path": "referee/k.txt"}], submit()],
                             "result": ok_result()})
        self.assertEqual(out.withheld_tool_results, 1)
        reply = self.seen("mcp.json")["replies"][0]
        self.assertTrue(reply["isError"])
        self.assertIn("withheld", reply["content"][0]["text"])

    @posix_only
    def test_only_the_first_verdict_counts(self):
        out = self.run_with({"calls": [submit("not_refuted"), submit("refuted")], "result": ok_result()})
        self.assertEqual(out.verdict, "not_refuted")
        self.assertTrue(self.seen("mcp.json")["replies"][1]["isError"])

    @posix_only
    def test_fail_closed_outcomes(self):
        cases = [
            ({"calls": [submit()], "result": ok_result(model="claude-opus-5-5")}, "model_mismatch"),
            ({"calls": [submit()], "result": ok_result(modelUsage={"claude-sonnet-5-5": {}, "claude-haiku-5-5": {}})},
             "model_mismatch"),
            ({"calls": [submit()], "result": ok_result(modelUsage={})}, "model_mismatch"),
            ({"calls": [], "result": ok_result()}, "no_verdict:end_turn"),
            ({"calls": [["submit_verdict", {"verdict": "maybe", "attempts": []}]], "result": ok_result()},
             "malformed_verdict"),
            ({"calls": [submit("refuted", [])], "result": ok_result()}, "malformed_verdict"),
            ({"calls": [submit()], "result": ok_result(is_error=True, subtype="error_during_execution")},
             "api_error:error_during_execution"),
            ({"calls": [submit()], "result": ok_result(is_error=True, subtype="error_max_budget_usd")}, "budget"),
            ({"garbage": True, "exit": 1}, "api_error:cli_exit_1"),
            ({"calls": [submit()], "result": ok_result(is_error=True, api_error_status=429, modelUsage={})},
             "api_error:http_429"),
            ({"calls": [submit()], "result": ok_result(modelUsage=["claude-sonnet-5-5"])}, "api_error:bad_cli_result"),
            ({"calls": [submit()], "result": ok_result(num_turns="x")}, "api_error:bad_cli_result"),
            ({"calls": [submit()], "result": ok_result(total_cost_usd=-1)}, "api_error:bad_cli_result"),
            ({"calls": [submit()], "result": ok_result(total_cost_usd="nan")}, "api_error:bad_cli_result"),
            ({"calls": [submit()], "result": ok_result(total_cost_usd="inf")}, "api_error:bad_cli_result"),
            ({"calls": [submit()], "result": {k: v for k, v in ok_result().items() if k != "total_cost_usd"}},
             "api_error:bad_cli_result"),
        ]
        for scenario, reason in cases:
            out = self.run_with(scenario)
            self.assertEqual(out.verdict, "unresolved", reason)
            self.assertTrue(any(r.startswith(reason) for r in out.reasons), (reason, out.reasons))

    @posix_only
    def test_invalid_submission_is_returned_to_the_model_and_the_corrected_one_counts(self):
        """The real run that ended `unresolved`: the model sent expect_stdout_contains as an empty string."""
        broken = json.loads((FIXTURES.parent / "rival" / "empty_expect_stdout.json").read_text())
        fixed = json.loads(json.dumps(broken))
        del fixed["attempts"][1]["reproducer"]["expect_stdout_contains"]
        out = self.run_with({"calls": [["submit_verdict", broken], ["submit_verdict", fixed]], "result": ok_result()})
        self.assertEqual((out.verdict, out.reasons), ("refuted", []))
        self.assertEqual(out.as_dict()["reproducer_count"], 1)
        first, second = self.seen("mcp.json")["replies"]
        self.assertTrue(first["isError"])
        self.assertIn("expect_stdout_contains must be 1-500 characters", first["content"][0]["text"])
        self.assertFalse(second["isError"])

    @posix_only
    def test_only_invalid_submissions_end_unresolved_and_are_bounded(self):
        broken = json.loads((FIXTURES.parent / "rival" / "empty_expect_stdout.json").read_text())
        out = self.run_with({"calls": [["submit_verdict", broken]], "result": ok_result()})
        self.assertEqual(out.verdict, "unresolved")
        self.assertEqual(out.reasons, ["malformed_verdict:expect_stdout_contains must be 1-500 characters"])
        fixed = json.loads(json.dumps(broken))
        del fixed["attempts"][1]["reproducer"]["expect_stdout_contains"]
        out = self.run_with({"calls": [["submit_verdict", broken]] * 3 + [["submit_verdict", fixed]],
                             "result": ok_result()})
        self.assertEqual(out.verdict, "unresolved")
        self.assertIn("too many invalid submissions", self.seen("mcp.json")["replies"][3]["content"][0]["text"])

    def test_tool_schema_tells_the_model_the_limits_the_validator_enforces(self):
        submit_tool = next(t for t in rival.TOOLS if t["name"] == "submit_verdict")
        attempt = submit_tool["input_schema"]["properties"]["attempts"]["items"]["properties"]
        expect = attempt["reproducer"]["properties"]["expect_stdout_contains"]
        self.assertEqual((expect["minLength"], expect["maxLength"]), (1, rival.MAX_EXPECT_CHARS))
        self.assertEqual(attempt["reproducer"]["properties"]["cmd"]["maxLength"], rival.MAX_CMD_CHARS)
        self.assertEqual(attempt["claim"]["maxLength"], rival.MAX_CLAIM_CHARS)
        self.assertEqual(submit_tool["input_schema"]["properties"]["attempts"]["maxItems"], rival.MAX_ATTEMPTS)

    @posix_only
    def test_a_secret_in_the_verdict_text_is_not_written_to_the_artifacts(self):
        leak = "AKIA" + "ABCDEFGHIJKLMNOP"
        refs = [{"path": "referee/a.py", "line_start": 1, "line_end": 1}]
        out = self.run_with({"calls": [submit("refuted", [{"claim": f"the key {leak} is committed",
                                                           "evidence_refs": refs}])], "result": ok_result()})
        self.assertEqual((out.verdict, out.reasons, out.attempts),
                         ("unresolved", ["secret_in_verdict:aws_access_key"], []))

    @posix_only
    def test_the_model_the_api_named_is_what_counts_not_the_one_the_cli_asked_for(self):
        """modelUsage is keyed by the requested model: an auditor's fake API answered as claude-haiku-9-9."""
        out = self.run_with({"calls": [submit()], "result": ok_result(), "api_models": ["claude-haiku-9-9"]})
        self.assertEqual((out.verdict, out.reasons), ("unresolved", ["model_mismatch"]))
        self.assertEqual(out.model_served, "claude-haiku-9-9,claude-sonnet-5-5")

    @posix_only
    def test_a_refusal_is_the_models_answer_not_an_outage(self):
        """Shape seen from the real CLI against a refusing API: is_error true, stop_reason refusal."""
        refused = ok_result(is_error=True, stop_reason="refusal", terminal_reason="api_error", subtype="success")
        out = self.run_with({"calls": [], "result": refused})
        self.assertEqual((out.verdict, out.reasons), ("unresolved", ["refusal"]))

    @posix_only
    def test_a_run_that_was_not_isolated_as_asked_is_refused(self):
        good = {"type": "system", "subtype": "init", "model": "x", "apiKeySource": "none", "skills": [],
                "slash_commands": [], "tools": list(rival.TOOL_NAMES),
                "mcp_servers": [{"name": "snowball", "status": "connected"}]}
        cases = {
            "tools": dict(good, tools=[*rival.TOOL_NAMES, "Bash"]),
            "mcp_servers": dict(good, mcp_servers=[{"name": "snowball", "status": "failed"}]),
            "skills": dict(good, skills=["frontend-design"]),
            "api_key": dict(good, apiKeySource="user"),
            "init_missing": None,
        }
        for fault, init in cases.items():
            out = self.run_with({"calls": [submit()], "result": ok_result(), "init": init})
            self.assertEqual((out.verdict, out.reasons), ("unresolved", [f"api_error:isolation_{fault}"]), fault)
        out = self.run_with({"calls": [submit()], "init": good,
                             "result": ok_result(modelUsage={"claude-sonnet-5-5": {"provider": "bedrock"}})})
        self.assertEqual(out.reasons, ["api_error:isolation_provider"])
        out = self.run_with({"calls": [submit()], "init": good,
                             "result": ok_result(modelUsage={"claude-sonnet-5-5": {"provider": "firstParty"}})})
        self.assertEqual((out.verdict, out.reasons), ("not_refuted", []))

    @posix_only
    def test_stray_lines_in_the_stream_do_not_hide_the_result(self):
        (self.bin_dir / "scenario.json").write_text(json.dumps({"calls": [submit()], "result": ok_result()}))
        original = rival._run_cli
        with mock.patch.object(rival, "_run_cli",
                               lambda *a, **k: (lambda rc, out: (rc, "warning: something" + chr(10) + out))(*original(*a, **k))):
            out = run_rival(CFG, claude_bin=str(self.claude), seat_prompt="s", context="c", tree_root=self.root,
                            budget_usd_micros=1_000_000, max_prompt_chars=100_000)
        self.assertEqual((out.verdict, out.reasons), ("not_refuted", []))

    @posix_only
    def test_real_cli_outputs_are_classified_by_what_went_wrong(self):
        """Recorded outputs of the real CLI (tests/fixtures/cli): a signed-out or rate-limited CLI is an
        infrastructure fault (retried, never counted against the push), never a verdict or a model swap."""
        expected = {"unauthenticated_bad_token": "api_error:http_401", "unauthenticated_no_token": "api_error:unknown",
                    "budget_exhausted": "budget", "max_turns_exhausted": "max_turns"}
        for name, reason in expected.items():
            doc = json.loads((FIXTURES / f"{name}.json").read_text())
            out = self.run_with({"calls": [submit()], "events": doc["events"], "exit": doc["exit_code"]})
            self.assertEqual((out.verdict, out.reasons), ("unresolved", [reason]), name)
        doc = json.loads((FIXTURES / "success_one_model.json").read_text())
        out = self.run_with({"calls": [submit()], "events": doc["events"]})
        self.assertEqual((out.verdict, out.reasons, out.model_served), ("not_refuted", [], "claude-sonnet-5-5"))

    @posix_only
    def test_timeout_and_missing_binary_fail_closed(self):
        with mock.patch.object(rival, "CLI_TIMEOUT_S", 1):
            out = self.run_with({"sleep": 5, "calls": [submit()], "result": ok_result()})
        self.assertEqual((out.verdict, out.reasons), ("unresolved", ["api_error:TimeoutExpired"]))
        out = self.run_with({}, claude_bin=None)
        self.assertEqual(out.reasons, ["api_error:ClaudeCliNotFound"])
        out = self.run_with({}, claude_bin=str(self.bin_dir / "missing"))
        self.assertEqual(out.reasons, ["api_error:FileNotFoundError"])

    @posix_only
    def test_timeout_kills_the_whole_process_tree(self):
        started = time.monotonic()
        with mock.patch.object(rival, "CLI_TIMEOUT_S", 3):
            out = self.run_with({"grandchild": True, "sleep": 30, "calls": [submit()], "result": ok_result()})
        # Killing only the CLI leaves its child holding the output pipe: the run would block until it ends (60 s).
        self.assertLess(time.monotonic() - started, 20)
        self.assertEqual(out.reasons, ["api_error:TimeoutExpired"])
        self.assertEqual(out.cost_usd_micros, 5_000_000)  # unknown spend: the per-run cap is charged
        pid = int((self.bin_dir / "grandchild.pid").read_text())
        for _ in range(50):
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                break
            time.sleep(0.1)
        else:
            os.kill(pid, 9)
            self.fail("the CLI's child process survived the timeout")

    @posix_only
    def test_budget_is_the_smaller_of_remaining_and_cap(self):
        self.run_with({"calls": [submit()], "result": ok_result()}, budget=123_456)
        argv = self.seen("seen.json")["argv"]
        self.assertEqual(argv[argv.index("--max-budget-usd") + 1], "0.123456")
        out = self.run_with({"calls": [submit()], "result": ok_result()}, budget=0)
        self.assertEqual(out.reasons, ["budget"])

    @posix_only
    def test_prompt_guards(self):
        (self.bin_dir / "seen.json").unlink(missing_ok=True)
        out = self.run_with({}, context="x" * 200_000)
        self.assertEqual(out.reasons, ["prompt_too_large"])
        out = self.run_with({}, context="AKIA" + "ABCDEFGHIJKLMNOP")
        self.assertEqual(out.reasons, ["secret_in_prompt:aws_access_key"])
        self.assertIsNone(self.seen("seen.json"))

    def test_toolbox_grep_and_glob(self):
        box = ToolBox(self.root)
        self.assertIn("referee/a.py:2: y = 2", box.grep(r"y = \d"))
        self.assertEqual(box.glob("**/*.py"), "referee/a.py")
        with self.assertRaises(ValueError):
            box.glob("../*")
        for bad in ("\\\\10.0.0.1\\share\\x", "C:/x", "//host/share", "a\\b", "x:y"):
            with self.assertRaises(ValueError, msg=bad):
                box.read_file(bad)
        for bad in ("C:/*", "*:*", "\\\\?\\C:\\*"):
            with self.assertRaises(ValueError, msg=bad):
                box.glob(bad)

    def test_context_contains_diff_and_pages(self):
        ctx = build_context("code", "a" * 40, "b" * 40, ["x.py"], "diff --git", {"spec/tohum/00.md": "core"})
        self.assertIn("diff --git", ctx)
        self.assertIn("=== Seed page spec/tohum/00.md ===", ctx)


class ResolveClaudeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name).resolve() / "bin"
        self.dir.mkdir()
        self.name = "claude.cmd" if os.name == "nt" else "claude"
        self.binary = self.dir / self.name
        self.binary.write_text("echo")
        self.binary.chmod(0o755)

    def test_a_relative_path_becomes_absolute_because_the_run_changes_directory(self):
        before = os.getcwd()
        self.addCleanup(os.chdir, before)
        os.chdir(self.dir.parent)
        found = resolve_claude(os.path.join("bin", "claude"))
        self.assertTrue(os.path.isabs(found))
        self.assertEqual(Path(found).resolve(), self.binary.resolve())

    def test_the_default_name_is_looked_up_on_path(self):
        with mock.patch.dict(os.environ, {"PATH": str(self.dir)}):
            self.assertEqual(Path(resolve_claude()).resolve(), self.binary.resolve())

    def test_nothing_found_is_none_not_a_guess(self):
        self.assertIsNone(resolve_claude(str(self.dir / "missing")))
        self.assertIsNone(resolve_claude(str(self.dir)))  # a directory is not a binary
        with mock.patch.dict(os.environ, {"PATH": str(self.dir.parent)}):
            self.assertIsNone(resolve_claude())


@unittest.skipUnless(hasattr(signal, "setitimer"), "the per-call deadline uses the POSIX interval timer")
class McpServerResilienceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.tree = Path(self.tmp.name) / "tree"
        (self.tree / "referee").mkdir(parents=True)
        (self.tree / "referee" / "x.txt").write_text("a" * 31 + "b" + chr(10))
        self.server = RivalServer(ToolBox(self.tree), Path(self.tmp.name) / "v.json", Path(self.tmp.name) / "s.json",
                                  tool_timeout_s=1)

    def test_a_runaway_regex_is_stopped_by_the_deadline(self):
        started = time.monotonic()
        text, is_error = self.server.call("grep", {"pattern": "(a+)+$"})  # minutes of work without a deadline
        self.assertTrue(is_error)
        self.assertIn("took longer", text)
        self.assertLess(time.monotonic() - started, 5)
        self.assertEqual(self.server.call("glob", {"pattern": "**/*.txt"}), ("referee/x.txt", False))

    def test_odd_arguments_are_error_results_not_crashes(self):
        for name, args in (("read_file", {"path": "referee/x.txt", "start_line": 1e999}),
                           ("read_file", {"path": "referee/x.txt", "start_line": "a"}),
                           ("grep", {"pattern": "("}), ("grep", {"pattern": 5}), ("glob", {"pattern": "C:/*"})):
            text, is_error = self.server.call(name, args)
            self.assertTrue(is_error, (name, args))

    def test_a_failing_request_does_not_end_the_session(self):
        class Flaky(RivalServer):
            def handle(self, msg):
                if msg.get("method") == "boom":
                    raise RuntimeError("bug")
                return super().handle(msg)

        flaky = Flaky(self.server.box, self.server.verdict_path, self.server.stats_path)
        lines = [json.dumps({"jsonrpc": "2.0", "id": 1, "method": "boom"}),
                 json.dumps({"jsonrpc": "2.0", "id": 2, "method": "ping"})]
        out = io.StringIO()
        serve(flaky, io.StringIO(chr(10).join(lines) + chr(10)), out)
        first, second = [json.loads(line) for line in out.getvalue().splitlines()]
        self.assertEqual(first["error"]["code"], -32603)
        self.assertEqual(second["result"], {})


class McpServerTest(unittest.TestCase):
    """The real server process over real pipes, as the CLI would drive it."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.tree = base / "tree"
        (self.tree / "referee").mkdir(parents=True)
        (self.tree / "referee" / "a.py").write_text("x = 1\n")
        self.verdict, self.stats = base / "verdict.json", base / "stats.json"

    def tearDown(self):
        self.tmp.cleanup()

    @staticmethod
    def _reap(proc):
        if proc.poll() is None:
            proc.kill()
        proc.wait(timeout=10)
        for stream in (proc.stdin, proc.stdout):
            if stream and not stream.closed:
                stream.close()

    def test_protocol_over_stdio(self):
        proc = subprocess.Popen(
            [sys.executable, "-I", str(MCP_SCRIPT), "--tree", str(self.tree), "--verdict-out", str(self.verdict),
             "--stats-out", str(self.stats)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, encoding="utf-8")
        self.addCleanup(self._reap, proc)

        def rpc(i, method, params=None):
            proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": i, "method": method, "params": params or {}}) + "\n")
            proc.stdin.flush()
            return json.loads(proc.stdout.readline())

        init = rpc(1, "initialize", {"protocolVersion": "2025-06-18"})["result"]
        self.assertEqual(init["protocolVersion"], "2025-06-18")
        proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
        names = [t["name"] for t in rpc(2, "tools/list")["result"]["tools"]]
        self.assertEqual(names, ["read_file", "grep", "glob", "submit_verdict"])
        self.assertIn("error", rpc(3, "resources/list"))
        call = lambda n, name, args: rpc(n, "tools/call", {"name": name, "arguments": args})["result"]  # noqa: E731
        self.assertIn("1: x = 1", call(4, "read_file", {"path": "referee/a.py"})["content"][0]["text"])
        self.assertTrue(call(5, "read_file", {"path": "missing.py"})["isError"])
        self.assertEqual(call(6, "glob", {"pattern": "**/*.py"})["content"][0]["text"], "referee/a.py")
        self.assertTrue(call(7, "nope", {})["isError"])
        self.assertIn("result", rpc(70, "tools/call", [1, 2]))  # non-object params: an error result, not a crash
        self.assertIn("result", rpc(71, "initialize", "text"))
        self.assertFalse(call(8, "submit_verdict", {"verdict": "not_refuted", "attempts": []})["isError"])
        self.assertTrue(call(9, "submit_verdict", {"verdict": "refuted", "attempts": []})["isError"])
        proc.stdin.close()
        self.assertEqual(proc.wait(timeout=10), 0)
        self.assertEqual(json.loads(self.verdict.read_text())["verdict"], "not_refuted")
        self.assertEqual(json.loads(self.stats.read_text()), {"withheld": 0, "invalid": 0, "last_invalid": ""})


if __name__ == "__main__":
    unittest.main()
