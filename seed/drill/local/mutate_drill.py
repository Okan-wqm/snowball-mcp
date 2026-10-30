"""Mutation check of the lesson drill's reference judge: break it on purpose, expect its tests to notice.

The reference judge (``snowball_drill/judge.py``, `tohum/29c`) is what the Founder's ``harness.drill`` must agree
with: the seed vectors are its verdicts. A branch no test pins can be broken without anyone noticing, and the
vectors written from the broken judge then teach the Founder the broken rule (gap E48 named five such branches).
Every mutant here is one change a careless edit of ``judge.py`` could plausibly make; the drill tests, the vector
tests among them, must fail on it. An anchor that no longer matches fails loudly, so the list cannot rot while the
code moves on.

    cd seed/drill && python3 local/mutate_drill.py [--only NAME] [--list]

Exit 0 means every mutant was killed.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

DRILL = Path(__file__).resolve().parents[1]
VECTORS = DRILL.parent / "bootstrap" / "vectors"  # the vector tests read them at ../bootstrap/vectors
TARGET = "snowball_drill/judge.py"
SKIP_ENV = "SNOWBALL_DRILL_MUTANT"  # set in a mutant run: the anchor test would otherwise kill every mutant

# (name, text found exactly once in judge.py, replacement, what the mutant stands for)
MUTANTS = [
    # The five branches of gap E48.
    ("duplicate_pairs_counted", "if len(set(ids)) != len(ids):", "if False:",
     "DA: one instance recorded twice reaches k and the effect"),
    ("birth_outside_the_family", '"instance_in_family": _family(key, b["instance_id"]) == key["family"],',
     '"instance_in_family": True,', "DB: a lesson born from an instance of another family"),
    ("use_without_negatives_passes", "return (PASS if positives and negatives else UNMEASURABLE), detail",
     "return (PASS if positives and negatives else PASS), detail",
     "DC: a lesson never withheld from another family passes use"),
    ("wrong_records_in_file_order", 'records = sorted(t["wrong"], key=lambda r: r["seq"])', 'records = t["wrong"]',
     "DE: the first contradiction is the first in the file, not the earliest"),
    ("empty_view_hash_accepted", '"view_rebuilt_identical": bool(p["view_sha256_before"]) and',
     '"view_rebuilt_identical": True and', "DF: two empty view hashes count as an identical rebuild"),
    # Commitment and birth.
    ("commitment_unchecked", 'if commitment(key) != doc["commitment_sha256"]:', "if False:",
     "an answer key edited after the run is believed"),
    ("not_reverted_accepted", '"reverted": b["reverted"] is True,', '"reverted": True,',
     "a bad merge left in place still gives a birth"),
    # Use.
    ("use_without_positives_passes", "PASS if positives and negatives else", "PASS if negatives else",
     "a lesson never offered to its own family passes use"),
    ("unknown_instance_ignored", "wrong.append(f\"{rec['instance_id']}:not_in_key\")", "pass",
     "a use record for an instance the answer key does not hold is skipped"),
    ("blind_roles_unchecked", 'if rec["lessons_injected"]:', "if False:",
     "the test-writer and the oracle may receive lessons"),
    ("missing_lesson_allowed", "if injected != expected:", "if injected and not expected:",
     "a planner or fixer of the family that got no lesson is not wrong"),
    ("leaked_lesson_allowed", "if injected != expected:", "if expected and not injected:",
     "a lesson given to another family is not wrong"),
    # Effect.
    ("pairs_from_any_family", 'pairs = [p for p in t["effect"] if _family(key, p["instance_id"]) == key["family"]]',
     'pairs = list(t["effect"])', "the effect is read on instances outside the trap family"),
    ("too_few_pairs_measured", 'if len(pairs) < params["k"] or broken_without', "if broken_without",
     "fewer than k pairs give a verdict"),
    ("weak_family_measured", ' or broken_without < params["min_broken_without"]:', ":",
     "a family the lessonless arm rarely breaks gives FAIL instead of UNMEASURABLE"),
    ("few_discordant_pairs_enough", 'ok = b + c >= params["min_discordant"] and c > b', "ok = c > b",
     "fewer than eight discordant pairs show an effect"),
    ("p_value_unchecked", ' and p_value < Fraction(params["alpha"])', "",
     "more discordant pairs for the lesson are enough, however likely by chance"),
    ("mcnemar_off_by_one", "for i in range(c, n + 1)", "for i in range(c + 1, n + 1)",
     "the p-value leaves out the observed count"),
    # Wrong lesson.
    ("contradiction_without_the_lesson", 'and r["injected"] and r["failed_test"] is not None',
     'and r["failed_test"] is not None', "a trap test that broke without the lesson contradicts the lesson"),
    ("any_failure_contradicts", ' and r["failed_test"] == key["instances"][r["instance_id"]].get("trap_test")', "",
     "an unrelated failure counts as the lesson's contradiction"),
    ("superseded_not_a_withdrawal", 'withdrawn = state["superseded"] or harmful in state["excluded_conditions"]',
     'withdrawn = harmful in state["excluded_conditions"]', "a superseded lesson is not withdrawn"),
    ("narrowing_not_a_withdrawal", 'withdrawn = state["superseded"] or harmful in state["excluded_conditions"]',
     'withdrawn = state["superseded"]', "excluding the harmful condition is not a withdrawal"),
    ("nothing_after_still_judged", "if not later_harmful:", "if False:",
     "a contradiction with no harmful instance after it passes"),
    ("injection_after_ignored", "return (PASS if withdrawn and not later else FAIL), detail",
     "return (PASS if withdrawn else FAIL), detail", "a withdrawn lesson the dispatcher still gives passes"),
    ("withdrawal_record_ignored", "return (PASS if withdrawn and not later else FAIL), detail",
     "return (PASS if not later else FAIL), detail", "a withdrawal never written to the lesson passes"),
    # Placebo.
    ("small_arm_measured", 'if min(n1, n2) < params["min_arm"]:', "if False:",
     "an arm of fewer than eight instances gives a credit"),
    ("ranking_may_omit_a_lesson", 'if lesson_id not in ranking or key["placebo"] not in ranking:', "if False:",
     "a ranking without the lesson or the placebo is read anyway"),
    ("placebo_credit_unchecked", "ok = placebo_no_credit and credit_matches and", "ok = credit_matches and",
     "a placebo whose credit clears zero passes"),
    ("placebo_at_the_live_level", 'newcombe_lower(*_arms(key, t, key["placebo"]), strict) <= 0',
     'newcombe_lower(*_arms(key, t, key["placebo"]), z) <= 0',
     "the placebo is held to the live level and fails a learner one drill in ten"),
    ("reported_credit_unchecked", "all(lid in reported and abs(float(reported[lid]) - bounds[lid]) <= CREDIT_TOLERANCE",
     "all(True", "the brain may report any credit"),
    ("credit_may_omit_a_lesson", "all(lid in reported and abs(", "all(abs(",
     "a credit report without the placebo ends the judge in a traceback"),
    ("credit_tolerance_loose", "CREDIT_TOLERANCE = 0.0001", "CREDIT_TOLERANCE = 0.001",
     "a credit rounded to three decimals is taken as the referee's"),
    ("ranked_by_the_last_place", "ranked_first = min(bounds, key=ranking.index)",
     "ranked_first = max(bounds, key=ranking.index)", "the ranking is read backwards"),
    # Persistence.
    ("empty_injection_hash_accepted", '"same_lesson_after_restart": bool(p["injected_sha256_before"]) and',
     '"same_lesson_after_restart": True and', "no lesson before or after the restart counts as the same lesson"),
    ("rebuilt_view_unchecked", 'p["view_sha256_before"] == p["view_sha256_rebuilt"],', "True,",
     "a view rebuilt differently from the ledger passes"),
    ("lesson_after_restart_unchecked", 'p["injected_sha256_before"] == p["injected_sha256_after_restart"],', "True,",
     "a different lesson after the restart passes"),
    # Blind scope (E64): what a scope covers, never a label.
    ("scope_label_matches", "if not isinstance(scope, dict) or set(scope) - set(SCOPE_FIELDS):",
     "if not isinstance(scope, dict):", "a scope naming the answer key's family covers jobs"),
    ("scope_vocabulary_unchecked", '"scope_public": isinstance(scope, dict) and not set(scope) - set(SCOPE_FIELDS),',
     '"scope_public": True,', "a scope outside the public vocabulary passes birth"),
    ("birth_instance_coverage_unchecked", '"scope_covers_birth": scope_matches(scope, _observables(key, b["instance_id"])),',
     '"scope_covers_birth": True,', "a scope that misses the instance it was born from passes birth"),
    ("family_coverage_unchecked",
     '"scope_covers_family": bool(family) and Fraction(covered, len(family)) >= Fraction(params["scope_coverage"]),',
     '"scope_covers_family": bool(family),', "a scope covering one job of its family passes birth"),
    ("family_coverage_strict", '>= Fraction(params["scope_coverage"])', '> Fraction(params["scope_coverage"])',
     "a scope covering exactly the policy's share of the family fails birth"),
    ("other_families_unchecked", '"scope_excludes_other_families": not any(',
     '"scope_excludes_other_families": True or not any(', "a scope covering another family passes birth"),
    ("use_by_the_label", 'covered = scope_matches(lesson["scope"], _observables(key, rec["instance_id"]))',
     'covered = _family(key, rec["instance_id"]) == key["family"]',
     "use reads the family label instead of what the lesson's scope covers"),
    # Right lesson (E318): a useful imported lesson survives a red that is not its own.
    ("control_from_any_family",
     'records = sorted((r for r in t["control"] if _family(key, r["instance_id"]) == family), key=lambda r: r["seq"])',
     'records = sorted(t["control"], key=lambda r: r["seq"])', "records outside the control family are read"),
    ("control_in_file_order",
     'records = sorted((r for r in t["control"] if _family(key, r["instance_id"]) == family), key=lambda r: r["seq"])',
     'records = [r for r in t["control"] if _family(key, r["instance_id"]) == family]',
     "the first unrelated red is the first in the file, not the earliest"),
    ("unrelated_red_without_the_lesson",
     'unrelated = next((r for r in records if r["injected"] and r["failed_test"] is not None',
     'unrelated = next((r for r in records if r["failed_test"] is not None',
     "a red while the lesson was not given tests whether it is kept"),
    ("own_trap_red_is_unrelated",
     'and r["failed_test"] != key["instances"][r["instance_id"]].get("trap_test")), None)', "), None)",
     "the lesson's own trap test going red counts as an unrelated red"),
    ("useful_lesson_superseded_kept", 'withdrawn = state["superseded"] or narrowed', "withdrawn = narrowed",
     "a useful lesson superseded at an unrelated red passes"),
    ("useful_lesson_narrowed_kept", 'withdrawn = state["superseded"] or narrowed', 'withdrawn = state["superseded"]',
     "a useful lesson narrowed at an unrelated red passes"),
    ("useful_lesson_dropped_later", "return (PASS if not withdrawn and not dropped else FAIL), detail",
     "return (PASS if not withdrawn else FAIL), detail", "a useful lesson the dispatcher stops giving passes"),
    ("nothing_after_the_unrelated_red_judged", "if not later:", "if False:",
     "an unrelated red with nothing after it passes"),
    # Referee's arms (E65).
    ("arms_off_the_draw_trusted", "if off_draw:", "if False:",
     "a dispatcher serving the arms against the referee's draw passes"),
    ("draw_ignores_the_seed", "hmac.new(bytes.fromhex(seed_hex), ", 'hmac.new(b"", ',
     "the withholding draw does not depend on the committed seed"),
    ("unequal_arms_tolerated", "if unequal:", "if False:", "the given arm may run with more effort"),
    ("run_settings_unread", 'canonical({f: a["run"].get(f) for f in RUN_FIELDS})', "canonical({})",
     "arms of one lesson are equal whatever they ran with"),
    # Headline.
    ("unmeasurable_outranks_fail",
     "overall = FAIL if FAIL in values else UNMEASURABLE if UNMEASURABLE in values else PASS",
     "overall = UNMEASURABLE if UNMEASURABLE in values else FAIL if FAIL in values else PASS",
     "a drill with a FAIL and an UNMEASURABLE is re-run instead of failed"),
]


def run_tests(workdir: Path, mutant_name: str = "") -> tuple[int, str]:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", **{SKIP_ENV: mutant_name})
    proc = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-f"], cwd=workdir, env=env,
                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
    killers = [line.split(" ")[1] for line in (proc.stdout + proc.stderr).splitlines()
               if line.startswith(("FAIL: ", "ERROR: "))]
    return proc.returncode, (killers[0] if killers else "(no test named)")


def run_mutant(mutant: tuple[str, str, str, str] | None) -> tuple[bool, str, float]:
    """Apply one mutant (or none: the baseline) to a fresh copy of the drill and run its tests there."""
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="drill-mutant-") as tmp:
        work = Path(tmp) / "drill"
        shutil.copytree(DRILL, work, ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(VECTORS, Path(tmp) / "bootstrap" / "vectors")
        name = ""
        if mutant is not None:
            name, old, new, _why = mutant
            target = work / TARGET
            text = target.read_text(encoding="utf-8")
            if text.count(old) != 1:
                return False, f"ANCHOR MISSING in {TARGET} (found {text.count(old)}x): update the mutant", 0.0
            target.write_bytes(text.replace(old, new).encode("utf-8"))
        code, killer = run_tests(work, name)
    return code != 0, killer, time.monotonic() - started


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", help="run only the mutant with this name")
    parser.add_argument("--list", action="store_true", help="list the mutants and what each stands for")
    args = parser.parse_args()
    chosen = [m for m in MUTANTS if not args.only or m[0] == args.only]
    if not chosen:
        print("no such mutant", file=sys.stderr)
        return 2
    if args.list:
        for name, _old, _new, why in chosen:
            print(f"{name:34} {why}")
        return 0
    failed, detail, _ = run_mutant(None)  # without this a failing environment makes every mutant "killed"
    if failed:
        print(f"the unmutated judge already fails its tests ({detail}); fix that first", file=sys.stderr)
        return 2
    survivors = []
    for mutant in chosen:
        killed, detail, seconds = run_mutant(mutant)
        print(f"{'killed  ' if killed else 'SURVIVED'} {mutant[0]:34} {seconds:5.1f}s  {detail}", flush=True)
        if not killed:
            survivors.append(mutant[0])
    print(f"\n{len(chosen) - len(survivors)}/{len(chosen)} mutants killed")
    if survivors:
        print("not measured by any test:", ", ".join(survivors))
    return 1 if survivors else 0


if __name__ == "__main__":
    sys.exit(main())
