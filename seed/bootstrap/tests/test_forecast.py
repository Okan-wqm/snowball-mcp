"""The Founder's forecast rows (register E534; `tohum/26g`; the autonomy plan, section 3): the form the seed owns, the
referee's binding (a signed result names only the forecast rows of the head it judged, never as a reason), the
launcher's copy into the metrics row, and the operator's scorer (`seed/founder/forecast_score.py`): a forecast
written after dispatch is ignored for that verdict, a push without one scores as the base rate."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from snowball_bootstrap import forecast, ledgercheck

import test_flow
from helpers import commit, ledger_bytes, ledger_rows, quiet_pilot

ROOT = Path(__file__).resolve().parents[3]
FOUNDER = ROOT / "seed" / "founder"
GOOD = {"task": "MF3 chain verify", "capability": "can", "reason": "MF1 and MF2 share the chain code",
        "p_solve_permille": 800, "p_accept_first_push_permille": 700, "horizon_runs": 2,
        "cost_micros": {"p10": 2_000_000, "p50": 5_000_000, "p90": 9_000_000},
        "turns": {"p10": 20, "p50": 40, "p90": 70}, "evidence": ["f12", "f30"], "unknowns": ["the toy's lint exit"]}


def load(name: str):
    sys.path.insert(0, str(FOUNDER))
    spec = importlib.util.spec_from_file_location(f"founder_{name}", FOUNDER / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def forecast_row(fields=None, **edits) -> dict:
    """One `kind: forecast` row's fields for `ledger_rows`' edits."""
    return {"kind": "forecast", "payload": {"summary": "forecast", "refs": [], "forecast": fields or GOOD}, **edits}


class ForecastFormTest(unittest.TestCase):
    """`26g`'s form: every field there, nothing else, integers where `26` allows no floats."""

    def test_a_forecast_in_26gs_form_holds_and_each_broken_rule_is_named(self):
        # forecast_unknown_field_allowed forecast_capability_unchecked forecast_permille_unbounded
        # forecast_horizon_unbounded forecast_quantiles_unordered forecast_bool_as_number
        self.assertIsNone(forecast.broken_rule(GOOD))
        cases = [({"extra": 1}, "unknown_field"), ({"capability": "maybe"}, "field:capability"),
                 ({"p_solve_permille": 1001}, "field:p_solve_permille"),
                 ({"p_accept_first_push_permille": -1}, "field:p_accept_first_push_permille"),
                 ({"p_accept_first_push_permille": True}, "field:p_accept_first_push_permille"),
                 ({"horizon_runs": 11}, "field:horizon_runs"), ({"horizon_runs": 0}, "field:horizon_runs"),
                 ({"cost_micros": {"p10": 3, "p50": 2, "p90": 4}}, "field:cost_micros"),
                 ({"turns": {"p10": 1, "p50": 2}}, "field:turns"), ({"task": ""}, "field:task"),
                 ({"reason": "x" * 501}, "field:reason"), ({"evidence": ["f"] * 21}, "field:evidence"),
                 ({"unknowns": [7]}, "field:unknowns")]
        for edit, rule in cases:
            with self.subTest(edit=edit):
                self.assertEqual(forecast.broken_rule({**GOOD, **edit}), rule)
        self.assertEqual(forecast.broken_rule({k: v for k, v in GOOD.items() if k != "turns"}), "missing:turns")
        self.assertEqual(forecast.broken_rule([GOOD]), "not_an_object")
        self.assertEqual(forecast.broken_rule({**GOOD, "p_solve_permille": 0, "horizon_runs": 10}), None)

    def test_the_projection_keeps_the_numbers_and_no_free_text(self):  # forecast_free_text_in_result
        """The signed result keeps what is scored: the task as its hash, how many evidence ids and unknowns."""
        kept = forecast.projection(GOOD)
        self.assertEqual(kept, {"task_sha256": hashlib.sha256(GOOD["task"].encode("utf-8")).hexdigest(),
                                "capability": "can", "horizon_runs": 2, "p_solve_permille": 800,
                                "p_accept_first_push_permille": 700, "cost_micros": GOOD["cost_micros"],
                                "turns": GOOD["turns"], "evidence_n": 2, "unknowns_n": 1})
        text = json.dumps(kept)
        for said in (GOOD["task"], GOOD["reason"], "f12", "lint exit"):
            self.assertNotIn(said, text)
        self.assertTrue(forecast.valid_projection(kept))
        for broken in ({**kept, "p_solve_permille": 1001}, {**kept, "task_sha256": "x"}, {**kept, "reason": "r"},
                       {k: v for k, v in kept.items() if k != "turns"}):
            self.assertFalse(forecast.valid_projection(broken), broken)

    def test_forecast_is_a_founder_kind_and_a_float_probability_breaks_the_ledger(self):  # forecast_kind_refused
        """`26` admits the kind; its number rule stands: 0.8 makes the row noncanonical, 800 is the form."""
        self.assertIn("forecast", ledgercheck.FOUNDER_KINDS)
        rows = ledger_rows(2, edits={1: forecast_row()})
        self.assertEqual(ledgercheck.check(ledger_bytes(rows), None, whole=False), [])
        line = json.dumps({**rows[1], "payload": {"summary": "f", "refs": [], "forecast": {"p": 0.8}}}).encode()
        self.assertEqual(ledgercheck.check(ledger_bytes(rows[:1]) + line + b"\n", None, whole=False),
                         [f"{ledgercheck.INVALID}:noncanonical:L2"])


class ForecastListingTest(unittest.TestCase):
    """`forecast.listed`: the rows the head carries past the last accepted ledger, by `row_hash`, in line order."""

    def test_only_forecast_rows_past_the_accepted_ledger_are_named(self):
        # forecast_accepted_rows_listed forecast_other_kind_listed
        rows = ledger_rows(5, edits={0: forecast_row(), 2: forecast_row({**GOOD, "capability": "no"}),
                                     4: forecast_row({**GOOD, "task": "MF4"})})
        base, head = ledger_bytes(rows[:1]), ledger_bytes(rows)
        found = forecast.listed(head, base)
        self.assertEqual(found, [{"row_hash": rows[2]["row_hash"], "line": 3, "invalid": "field:capability"},
                                 {"row_hash": rows[4]["row_hash"], "line": 5,
                                  "forecast": forecast.projection({**GOOD, "task": "MF4"})}])
        self.assertEqual([e["row_hash"] for e in forecast.listed(head, None)],
                         [rows[0]["row_hash"], rows[2]["row_hash"], rows[4]["row_hash"]])
        self.assertEqual(forecast.listed(None, base), [])

    def test_a_row_whose_hash_is_not_its_own_is_not_named(self):  # forecast_unverified_hash_listed
        rows = ledger_rows(1, edits={0: forecast_row()})
        forged = dict(rows[0], row_hash="f" * 64)
        self.assertEqual(forecast.listed(ledger_bytes([forged]), None), [])
        self.assertEqual(forecast.listed(ledger_bytes([dict(rows[0], prev_hash="zz")]), None), [])

    def test_the_newest_rows_are_named_when_there_are_too_many(self):  # forecast_listing_keeps_the_oldest
        rows = ledger_rows(forecast.MAX_LISTED + 3, edits={i: forecast_row() for i in range(forecast.MAX_LISTED + 3)})
        found = forecast.listed(ledger_bytes(rows), None)
        self.assertEqual(len(found), forecast.MAX_LISTED)
        self.assertEqual(found[-1]["row_hash"], rows[-1]["row_hash"])
        self.assertEqual(found[0]["line"], 4)


class ForecastSignedResultTest(unittest.TestCase):
    """End to end over local git repositories (`test_flow.Flow`'s world): pull names the head's forecast rows,
    decide signs them, and they are never a reason."""

    def setUp(self):
        self.flow = test_flow.Flow("test_full_stage0_path")
        self.flow.setUp()
        self.addCleanup(self.flow.tearDown)
        self.brain, self.pull, self.finish = self.flow.brain, self.flow.pull, self.flow.finish

    @property
    def state(self):
        return self.flow.state

    def test_the_signed_result_names_the_judged_heads_forecasts_and_never_one_pushed_after_dispatch(self):
        # forecasts_not_named_in_pull forecasts_dropped_from_result forecasts_read_from_the_base
        rows = ledger_rows(3, edits={1: forecast_row(), 2: forecast_row({**GOOD, "turns": {"p10": 9}})})
        commit(self.brain, {"referee/a.py": "x = 1\n", "founder-ledger.jsonl": ledger_bytes(rows[:2])}, "work")
        meta = self.pull()
        self.assertEqual(meta["kind"], "code")
        self.assertEqual(meta["forecasts"], [{"row_hash": rows[1]["row_hash"], "line": 2,
                                              "forecast": forecast.projection(GOOD)}])
        result = self.finish(meta)
        self.assertEqual(result["forecasts"], meta["forecasts"])
        # The row written after this run was dispatched (here: after its pull) is not in its result; the next run of
        # a new head names it, and the rows the last accepted commit holds are never named again.
        commit(self.brain, {"referee/a.py": "x = 2\n", "founder-ledger.jsonl": ledger_bytes(rows)}, "after")
        self.state["last_accepted_sha"] = self.state["last_evaluated_sha"]  # as if the first head was accepted
        meta2 = self.pull()
        self.assertEqual(meta2["forecasts"], [{"row_hash": rows[2]["row_hash"], "line": 3, "invalid": "field:turns"}])
        self.assertNotIn(rows[2]["row_hash"], json.dumps(result))

    def test_a_forecast_is_never_a_reason(self):
        commit(self.brain, {"referee/a.py": "x = 1\n"}, "work without a forecast")
        without = self.pull()
        rows = ledger_rows(1, edits={0: forecast_row({**GOOD, "capability": "no"})})
        commit(self.brain, {"referee/a.py": "x = 2\n", "founder-ledger.jsonl": ledger_bytes(rows)}, "with a broken one")
        with_one = self.pull()
        self.assertEqual(with_one["forecasts"][0]["invalid"], "field:capability")
        self.assertEqual(with_one["pre_reasons"], without["pre_reasons"])
        self.assertEqual([r["kind"] for r in self.finish(with_one)["reasons"]],
                         [r["kind"] for r in self.finish(without)["reasons"]])

    def test_a_ledger_only_push_names_nothing(self):
        """A head with ledger rows alone is `none` (a `noop`): no verdict, no event, nothing named; the row waits for
        the next judged head, which names it."""
        rows = ledger_rows(1, edits={0: forecast_row()})
        commit(self.brain, {"founder-ledger.jsonl": ledger_bytes(rows)}, "a forecast alone")
        meta = self.pull()
        self.assertEqual((meta["kind"], meta["forecasts"]), ("none", []))
        self.finish(meta)
        commit(self.brain, {"referee/a.py": "x = 1\n"}, "the work")
        self.assertEqual([e["row_hash"] for e in self.pull()["forecasts"]], [rows[0]["row_hash"]])


class LauncherForecastRecordTest(unittest.TestCase):
    """The launcher copies the signed `forecasts[]` of the head it dispatched into the cycle's metrics row."""

    def cycle(self, result_extra):
        launch = load("launch")
        before, after = "a" * 40, "b" * 40

        class Fake(quiet_pilot(launch)):
            heads = [before, after]
            dispatches = 0

            def fetch_result(self):
                if not self.dispatches:
                    return None
                return {"head": after, "verdict": "accepted", "warnings": [], "rival": None,
                        "state": {"last_evaluated_sha": after, "last_accepted_sha": after}, **result_extra}

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
                return {"exit": 0, "minutes": 1, "turns": 3, "cost_usd": 1.5}

            def write(self, text):
                pass

        pilot = Fake(Path(tempfile.mkdtemp()), "o/brain", "o/referee", "target")
        pilot.idle, pilot.seed = 0, before
        pilot.prompt_sha256, pilot.image_id = "p" * 64, "sha256:" + "i" * 64
        args = type("Args", (), dict(model="claude-opus-5-5", max_turns=1, budget_usd=1, session_timeout=1,
                                     referee_timeout=1))
        with mock.patch.object(launch, "say"):
            pilot.cycle(1, args)
        return json.loads(pilot.metrics.read_text(encoding="utf-8").splitlines()[-1])

    def test_the_cycles_row_carries_the_referees_forecasts(self):  # metrics_drop_the_forecasts
        listing = [{"row_hash": "h" * 64, "line": 7, "forecast": forecast.projection(GOOD)}]
        self.assertEqual(self.cycle({"forecasts": listing})["forecasts"], listing)
        self.assertIsNone(self.cycle({})["forecasts"])  # a referee before E534 names none


def entry(row_hash: str, fields=None, invalid=None) -> dict:
    if invalid:
        return {"row_hash": row_hash, "line": 1, "invalid": invalid}
    return {"row_hash": row_hash, "line": 1, "forecast": forecast.projection(fields or GOOD)}


def push(verdict="accepted", forecasts=None, cost=5.0, turns=40, stamp="20261105T000000Z") -> dict:
    return {"stamp": stamp, "pushed": True, "verdict": verdict, "kind": "code", "cost_usd": cost, "turns": turns,
            "forecasts": forecasts}


class ForecastScoreTest(unittest.TestCase):
    """The operator's scorer: binding, the base rate, and each score against the base-rate forecaster."""

    def setUp(self):
        self.fs = load("forecast_score")

    def test_a_forecast_after_dispatch_is_ignored_for_that_verdict(self):
        # score_rebinds_a_seen_row score_base_sees_the_outcome
        """The plan's test. Push 1 was rejected with no forecast in its head; the Founder saw the verdict and wrote a
        row that calls it (p_accept 0). That row is first named by push 2's run, so it is push 2's forecast, scored
        against push 2's verdict; push 1 scores at the base rate. Named again by push 3's run, it stays push 2's."""
        late = {**GOOD, "p_accept_first_push_permille": 0}
        rows = [push("rejected", []), push("accepted", [entry("L" * 64, late)]),
                push("accepted", [entry("L" * 64, late)])]
        runs = self.fs.bind(rows)
        self.assertEqual([r["forecast"] is not None for r in runs], [False, True, False])
        acc = self.fs.score(rows)["accept"]["brier"]
        base = [0.5, 1 / 3, 2 / 4]  # Laplace on the earlier verdicts only: none, [0], [0, 1]
        founder = [(0.5 - 0) ** 2, (0.0 - 1) ** 2, (2 / 4 - 1) ** 2]
        self.assertAlmostEqual(acc["base"], sum((b - y) ** 2 for b, y in zip(base, (0, 1, 1))) / 3)
        self.assertAlmostEqual(acc["founder"], sum(founder) / 3)

    def test_a_missing_forecast_scores_as_the_base_rate(self):  # score_missing_not_base score_invalid_forecast_counted
        """A push without a counted forecast (none named, or only rows whose form does not hold) scores exactly what
        the base rate scores, in every score; it is never a point forecast of its own."""
        rows = []
        for n in range(5):
            rows += [push("accepted", None, 4.0, 30), push("rejected", [], 7.0, 55),
                     push("accepted", [entry(f"{n:064x}", invalid="payload")], 3.0, 25)]
        # a record whose copy of a listing was altered: its numbers are off the form, so it is no forecast
        rows.append(push("accepted", [entry("x" * 64, {**GOOD, "p_solve_permille": 1001})], 6.0, 41))
        out = self.fs.score(rows)
        self.assertEqual((out["pushes"], out["forecasted"], out["invalid"]), (16, 0, 6))
        for name in ("brier", "log"):
            self.assertEqual(out["accept"][name]["founder"], out["accept"][name]["base"])
        for name in ("cost", "turns"):
            self.assertEqual(out[name]["n"], 6)
            self.assertEqual(out[name]["founder"], out[name]["base"])
        self.assertEqual(out["solve"]["brier"]["n"], 0)

    def test_the_last_new_valid_row_of_a_push_counts_and_the_others_are_extra(self):  # score_counts_the_first_row
        first, last = {**GOOD, "p_accept_first_push_permille": 100}, {**GOOD, "p_accept_first_push_permille": 900}
        runs = self.fs.bind([push("accepted", [entry("a" * 64, first), entry("b" * 64, last)])])
        self.assertEqual((runs[0]["forecast"]["p_accept_first_push_permille"], runs[0]["extra"]), (900, 1))

    def test_only_a_judged_push_is_an_event_and_frozen_is_accepted(self):  # score_frozen_as_rejected
        rows = [push(None, [entry("a" * 64)]), {"pushed": False, "verdict": None, "stamp": "s"},
                push("frozen", [entry("a" * 64)]), {"kind": "intervention", "ts": "2026-11-05T00:00:00Z"}]
        runs = self.fs.bind(rows)
        self.assertEqual([(r["y"], r["forecast"] is not None) for r in runs], [(1, True)])  # bound at the judged run

    def test_p_solve_resolves_within_its_horizon_on_the_same_task(self):
        # score_solve_any_task score_solve_horizon_off_by_one
        """A task is solved at the first accepted push, within `horizon_runs` judged pushes from the forecast's own,
        whose counted forecast names the same task; unsolved once the horizon passes; open until then."""
        t1 = {**GOOD, "task": "T1", "horizon_runs": 2, "p_solve_permille": 900}
        t2 = {**GOOD, "task": "T2", "horizon_runs": 1, "p_solve_permille": 600}
        t3 = {**GOOD, "task": "T3", "horizon_runs": 3, "p_solve_permille": 500}
        rows = [push("rejected", [entry("1" * 64, t1)]), push("accepted", [entry("2" * 64, t2)]),
                push("accepted", [entry("3" * 64, t1)]), push("rejected", [entry("4" * 64, t3)])]
        out = self.fs.score(rows)
        # T1 (first forecast) is not solved by push 2 (another task) and push 3 is past its horizon of 2: 0. T2 is
        # solved at its own push: 1. T1's second forecast is solved at its own push 3: 1. T3 stays open.
        self.assertEqual((out["solve"]["brier"]["n"], out["solve_open"]), (3, 1))
        self.assertAlmostEqual(out["solve"]["brier"]["founder"], ((0.9 - 0) ** 2 + (0.6 - 1) ** 2 + (0.9 - 1) ** 2) / 3)
        # The base rate of each is the Laplace rate of the solve events resolved before its own push: none for T1 and
        # T2 (0.5); for T1's second, T1's first (0) and T2 (1), both resolved at push 2 (2/4).
        self.assertAlmostEqual(out["solve"]["brier"]["base"], ((0.5 - 0) ** 2 + (0.5 - 1) ** 2 + (0.5 - 1) ** 2) / 3)

    def test_pinball_waits_for_history_and_scores_against_the_earlier_quantiles(self):
        # score_pinball_without_history
        history = [push("accepted", None, cost=float(c), turns=c) for c in range(1, self.fs.MIN_HISTORY + 1)]
        said = {**GOOD, "cost_micros": {"p10": 1_000_000, "p50": 4_000_000, "p90": 8_000_000},
                "turns": {"p10": 2, "p50": 5, "p90": 9}}
        out = self.fs.score(history + [push("accepted", [entry("c" * 64, said)], cost=4.0, turns=12)])
        self.assertEqual((out["cost"]["n"], out["turns"]["n"]), (1, 1))
        base = {k: self.fs.quantile([float(c) for c in range(1, 11)], q) for k, q in self.fs.QUANTILES}
        self.assertAlmostEqual(base["p10"], 1.9)
        self.assertAlmostEqual(out["cost"]["founder"], self.fs.pinball({"p10": 1.0, "p50": 4.0, "p90": 8.0}, 4.0))
        self.assertAlmostEqual(out["cost"]["base"], self.fs.pinball(base, 4.0))
        self.assertAlmostEqual(out["turns"]["founder"], self.fs.pinball({"p10": 2, "p50": 5, "p90": 9}, 12))

    def test_log_loss_is_clipped_and_fails_count_only_with_a_forecast(self):  # score_fails_without_forecast
        sure = {**GOOD, "p_accept_first_push_permille": 1000}
        out = self.fs.score([push("rejected", [entry("s" * 64, sure)]), push("rejected", None)])
        self.assertAlmostEqual(out["accept"]["log"]["founder"] * 2, -math.log(self.fs.CLIP) - math.log(2 / 3))
        self.assertEqual((out["fail_events"], out["fail_needed"]), (1, 30))

    def test_the_daily_reports_line_5_says_how_few_failures_there_are(self):
        # daily_forecasts_windowed daily_fail_need_ignored
        """Line 5 is the scorer's over the whole record up to --at, not the day: calibration needs history."""
        report = load("daily_report")
        old = push("rejected", [entry("o" * 64)], stamp="20261020T000000Z")
        fc = self.fs.score([old])
        line = report.line5(fc)
        self.assertTrue(line.startswith("5. Tahmin (kaydın tümü, Kurucu/taban): kabul olayı 1 (tahminli 1;"))
        self.assertIn("yetersiz olay n_fail=1/30 (tahminli ret): güven haritası çizilmez.", line)
        fc["fail_events"] = 30
        self.assertIn("olay yeterli n_fail=30/30: güven haritası kurulmadı.", report.line5(fc))
        inputs = {"at": report.utc("2026-11-05T00:00:00Z"), "metrics": (json.dumps(old) + "\n").encode(),
                  "log": "", "halt": None, "seen": {}, "karne": None, "loaders": {}, "disk_free": None,
                  "caps": {"error": "x"}}
        self.assertIn("n_fail=1/30", report.build(copy.deepcopy(inputs))[4])  # 16 days old, still counted


if __name__ == "__main__":
    unittest.main()
