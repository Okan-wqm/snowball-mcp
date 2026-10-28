"""Mutation check of the bootstrap's own tests: break the code on purpose, expect a test to notice.

Every mutant is one textual change to the referee's code that a careless edit could plausibly make.
The check copies the repository layout to a temporary directory, applies the change, runs the unit
tests there and demands a failure. A mutant that survives names behaviour no test measures. An
anchor that no longer matches fails loudly, so the list cannot rot while the code moves on.

    cd seed/bootstrap && python3 local/mutate.py [--only NAME] [--list]

Run it on Linux (several tests need a POSIX shell). Exit 0 means every mutant was killed.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

BOOT = Path(__file__).resolve().parents[1]
ROOT = BOOT.parents[1]
PKG = "seed/bootstrap/snowball_bootstrap"

# (name, file, old text found exactly once, new text, what the mutant stands for)
MUTANTS = [
    ("outage_judged_by_served_model", f"{PKG}/rival.py",
     'if result.get("is_error") or subtype.startswith("error"):',
     'if served and (result.get("is_error") or subtype.startswith("error")):',
     "the bug found in review: a signed-out CLI (no model) became model_mismatch and counted against the push"),
    ("outage_check_removed", f"{PKG}/rival.py",
     'if result.get("is_error") or subtype.startswith("error"):', "if False:",
     "failed calls read as verdicts"),
    ("model_check_removed", f"{PKG}/rival.py", "if served != [cfg.model]:", "if False:",
     "any served model is accepted"),
    ("model_from_modelusage_only", f"{PKG}/rival.py", "served = sorted(api_models | set(usage))",
     "served = sorted(set(usage))", "the CLI names the requested model; the API's reply is ignored"),
    ("refusal_read_as_outage", f"{PKG}/rival.py", 'if result.get("stop_reason") == "refusal":', "if False:",
     "a refusal is retried forever"),
    ("isolation_not_attested", f"{PKG}/rival.py", "fault = _isolation_fault(init, usage)", "fault = None",
     "a run with extra tools or an API key is accepted"),
    ("verdict_not_validated", f"{PKG}/rival.py", "verdict = validate_verdict(raw, ToolBox(tree_root))",
     'verdict = {"verdict": raw.get("verdict"), "attempts": raw.get("attempts", [])}',
     "whatever the model wrote becomes the verdict"),
    ("negative_cost_accepted", f"{PKG}/rival.py", "if not math.isfinite(cost) or cost < 0:", "if False:",
     "a bad cost lowers the month's spend"),
    ("prompt_secret_scan_off", f"{PKG}/rival.py", "leaked = secretscan.scan(system_text",
     "leaked = [] and secretscan.scan(system_text", "a secret in the request is sent to the model"),
    ("verdict_secret_scan_off", f"{PKG}/rival.py", 'leaked = secretscan.scan(json.dumps(verdict["attempts"]))',
     "leaked = []", "a secret in the verdict text reaches the signed artifacts"),
    ("api_key_reaches_the_cli", f"{PKG}/rival.py",
     'DROPPED_ENV_PREFIXES = ("ANTHROPIC_", "CLAUDE_CODE_USE_", "CLAUDE_CODE_GATEWAY_")',
     "DROPPED_ENV_PREFIXES = ()", "the credential decision leaks: a key overrides the login"),
    ("model_fallback_allowed", f"{PKG}/rival.py", '"CLAUDE_CODE_NO_MODEL_FALLBACK": "1"', '"X_UNUSED": "1"',
     "a refused request is silently re-sent on another model"),
    ("timeout_is_free", f"{PKG}/rival.py", "out.cost_usd_micros = budget  # the spend is unknown",
     "pass  # the spend is unknown", "a hanging run costs nothing, so retrying it is free"),
    ("timeout_leaves_children", f"{PKG}/rival.py", "os.killpg(proc.pid, signal.SIGKILL)", "proc.kill()",
     "the MCP server outlives a timed-out CLI"),
    ("toolbox_escapes_the_tree", f"{PKG}/rival.py", "if not target.is_relative_to(self.root):", "if False:",
     "the model reads files outside the extracted tree"),
    ("mcp_result_secret_scan_off", f"{PKG}/rival_mcp.py", "if secretscan.scan(text):", "if False:",
     "a tool result with a secret reaches the model"),
    ("mcp_accepts_invalid_verdicts", f"{PKG}/rival_mcp.py", "validate_verdict(args, self.box)", "None",
     "the model is never told its verdict is malformed (the real e2e failure)"),
    ("mcp_second_verdict_wins", f"{PKG}/rival_mcp.py", "if self.submitted:", "if False:",
     "a later submission replaces the first valid one"),
    ("outage_counted_against_the_push", f"{PKG}/decide.py", '.startswith("api_error")', '.startswith("api_errorX")',
     "an outage is recorded as a rejection and feeds not_learning"),
    ("missing_rival_ignored", f"{PKG}/decide.py", 'reasons.append(_reason("rival_missing"))', "pass",
     "a push is accepted without any rival result"),
    ("unsafe_archive_names_pass", f"{PKG}/treehash.py", '":" in name', "False",
     "a Windows-shaped member name reaches the filesystem"),
    ("unknown_config_keys_pass", f"{PKG}/config.py", "unknown = sorted(set(obj) - known)", "unknown = []",
     "removed or misspelled operator settings are silently ignored"),
]


def run_mutant(index: int, mutant: tuple[str, str, str, str, str]) -> tuple[bool, str, float]:
    name, rel, old, new, _why = mutant
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix=f"mutant-{index}-") as tmp:
        work = Path(tmp)
        ignore = shutil.ignore_patterns("__pycache__", "node_modules", ".git")
        shutil.copytree(ROOT / "seed", work / "seed", ignore=ignore)
        shutil.copytree(ROOT / "spec" / "tohum", work / "spec" / "tohum", ignore=ignore)
        target = work / rel
        text = target.read_text(encoding="utf-8")
        if text.count(old) != 1:
            return False, f"ANCHOR MISSING in {rel} (found {text.count(old)}x): update the mutant", 0.0
        target.write_text(text.replace(old, new), encoding="utf-8", newline="")
        boot = work / "seed" / "bootstrap"
        env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": ".:tests",
               "HOME": str(work)}
        proc = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-f"], cwd=boot, env=env,
                              capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    output = proc.stdout + proc.stderr
    killers = [line.split(" ")[1] for line in output.splitlines() if line.startswith(("FAIL: ", "ERROR: "))]
    return proc.returncode != 0, (killers[0] if killers else "(no test named)"), time.monotonic() - started


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", help="run only the mutant with this name")
    parser.add_argument("--list", action="store_true", help="list the mutants and what each stands for")
    args = parser.parse_args()
    chosen = [(i, m) for i, m in enumerate(MUTANTS) if not args.only or m[0] == args.only]
    if not chosen:
        print("no such mutant", file=sys.stderr)
        return 2
    if args.list:
        for _i, m in chosen:
            print(f"{m[0]:34} {m[4]}")
        return 0
    survivors = []
    for i, m in chosen:
        killed, detail, seconds = run_mutant(i, m)
        print(f"{'killed  ' if killed else 'SURVIVED'} {m[0]:34} {seconds:5.1f}s  {detail}", flush=True)
        if not killed:
            survivors.append(m[0])
    print(f"\n{len(chosen) - len(survivors)}/{len(chosen)} mutants killed")
    if survivors:
        print("not measured by any test:", ", ".join(survivors))
    return 1 if survivors else 0


if __name__ == "__main__":
    sys.exit(main())
