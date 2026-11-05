"""The operator's daily observer report (`seed/founder/daily_report.py`, E537): ten lines generated from the pilot's
records, the log reconciled with the metrics by stamp, the launcher's own counting rules, unmeasured never zero, and
nothing written but the report. The world is the fixture work folder `fixtures/daily_report/work`: no live pilot."""

from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from collections import namedtuple
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
FOUNDER = ROOT / "seed" / "founder"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "daily_report"
AT = "2026-11-04T18:00:00Z"
POLICY = {"constitutional": {
    "monthly_cap_usd": 300, "stage_params": {"rival_min_attempts": 2, "repeat_reject_limit": 3},
    "stage_budgets": {"asama_0": {"rival_usd": 30, "founder_usd": 220}}, "license_allowlist": ["MIT"],
    "license_exceptions": {}, "session_cap_usd": 15, "day_cap_usd": 100}}
DISK = namedtuple("Usage", "total used free")(0, 0, 123_456_000_000)


def load():
    spec = importlib.util.spec_from_file_location("founder_daily_report", FOUNDER / "daily_report.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DailyReportTest(unittest.TestCase):
    """E537: the plan's section 6, script-only."""

    def setUp(self):
        self.report = load()
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.work = self.tmp / "work"
        shutil.copytree(FIXTURE / "work", self.work)
        self.reads: list[str] = []

    def get(self, policy=POLICY, stage=None):
        def read(path: str, raw: bool) -> bytes:
            self.reads.append(path)
            if path.endswith("/policy.json"):
                return json.dumps(policy).encode()
            if stage is None:
                raise self.report.scorecard.NotFound(f"gh api {path}: HTTP 404")
            return json.dumps({"stage": stage}).encode()
        return read

    def lines(self, referee="owner/referee", get=None, at=AT) -> list[str]:
        with mock.patch.object(self.report.shutil, "disk_usage", return_value=DISK):
            inputs = self.report.gather(self.work, self.report.utc(at), referee, get or self.get())
        return self.report.build(inputs)

    def edit(self, name: str, old: str, new: str) -> None:
        path = self.work / name
        text = path.read_text(encoding="utf-8")
        self.assertEqual(text.count(old), 1, old)
        path.write_text(text.replace(old, new), encoding="utf-8", newline="\n")

    def test_the_report_from_fixture_rows_is_the_golden_file(self):
        # daily_window_closed_at_the_start daily_spend_reported_only daily_end_ignores_the_row
        # daily_halt_file_unread daily_section_runs_past_a_heading
        """The plan's test: the report built from the fixture rows is the committed golden file, line for line, and it
        has exactly the plan's ten lines. The fixture holds a session exactly 24 hours old (outside the window), a
        cost the CLI did not report (counted at the brake), a row from before E528 without `end`, a halt outside
        the window, an outage's section without a session, and an operator's note quoting a verdict line."""
        golden = (FIXTURE / "golden.md").read_text(encoding="utf-8")
        text = self.report.render(self.lines())
        self.assertEqual(text, golden)
        self.assertEqual([line.split(".", 1)[0] for line in text.splitlines()], [str(n) for n in range(1, 11)])
        self.assertEqual(self.reads, ["repos/owner/referee/contents/policy.json",
                                      "repos/owner/referee/contents/setup/stage.json"])

    def test_records_after_the_end_count_nowhere(self):
        # daily_spend_after_the_end daily_rows_after_the_end daily_log_past_the_end
        """The report is as of --at, so yesterday's can be made today: a session, its log section, its open reports
        and a halt line written after the window's end change no line. The launcher's `day_spent` has no upper bound
        (its `at` is always now), so the report drops later spend itself."""
        with (self.work / "pilot-metrics.jsonl").open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps({"budget_usd": 15, "cost_usd": 9.0, "end": "exit", "kind": "code", "pushed": True,
                                 "reports_unanswered": 7, "session_exit": 0, "stage": 0,
                                 "stamp": "20261104T200000Z", "verdict": "rejected"}) + "\n")
            fh.write(json.dumps({"args": {"resume": "True"}, "kind": "intervention",
                                 "ts": "2026-11-04T19:00:00Z"}) + "\n")
        with (self.work / "pilot-log.md").open("a", encoding="utf-8", newline="\n") as fh:
            fh.write("\n## Döngü 6 — 20261104T200000Z\n\n- Beyin: `ddddddd` → `eeeeeee`\n"
                     "- Oturum: çıkış 0, 10.0 dk, tur 20, maliyet 9.0 USD, sonuç success, bitiş exit\n"
                     "- Açık raporlar (1, beyin `eeeeeee`; yaş: başlatıcının ilk görmesinden bu yana saat): "
                     "`seed-009-late` 0 sa\n- Hakemin kararı: **rejected**, nedenler []\n"
                     "\n- 2026-11-04T21:00:00Z **HALT**: later. `RUNNING` duruyor (kalan 1 döngü)\n")
        golden = (FIXTURE / "golden.md").read_text(encoding="utf-8")
        self.assertEqual(self.report.render(self.lines()), golden)
        later = self.lines(at="2026-11-05T00:00:00Z")  # the same records, a day on: the later session counts
        self.assertIn("günlük 11 döngü (10 oturumlu), metrik 9;", later[0])
        self.assertIn("ret 2", later[0])
        self.assertIn("79,65 USD", later[1])

    def test_the_reconciliation_explains_only_what_the_records_say(self):
        # daily_pre_metrics_unbounded daily_correction_unchecked daily_push_not_compared daily_log_only_rows_unflagged
        """Explained: a session logged before the metrics file's first row, and a verdict the row corrects itself
        (`corrected_by`). Anything else is UZLAŞMADI, named by stamp: the live log's 12 rejections against the
        metrics' 7 were five sessions logged before the metrics file began."""
        base = self.lines()[0]
        self.assertIn("metrik öncesi 1, düzeltilmiş satır 1 (E241); açıklanmayan 0.", base)
        rows = (self.work / "pilot-metrics.jsonl").read_text(encoding="utf-8").splitlines(keepends=True)
        cases = {
            "a row the log has, gone from the metrics": (
                lambda: (self.work / "pilot-metrics.jsonl").write_text(
                    "".join(r for r in rows if "20261104T120000Z" not in r), encoding="utf-8"),
                "20261104T120000Z metrikte yok"),
            "a row the log lacks": (
                lambda: self.edit("pilot-log.md", "\n## Döngü 4 — 20261104T150000Z\n", "\n## Not — 4\n"),
                "20261104T150000Z günlükte yok"),
            "a verdict that differs without a correction": (
                lambda: self.edit("pilot-metrics.jsonl", '"corrected_by": "E241: the launcher had written the older '
                                                         'head\'s acceptance", ', ""),
                "20261102T120000Z karar farklı"),
            "a push that differs": (
                lambda: self.edit("pilot-metrics.jsonl", '"pushed": false, "session_exit": 1, "stage": 0',
                                  '"pushed": true, "session_exit": 1, "stage": 0'),
                "20261104T100000Z push farklı"),
            "a line that does not parse": (
                lambda: (self.work / "pilot-metrics.jsonl").write_text("".join(rows) + '{"stamp": "2026\n',
                                                                       encoding="utf-8"),
                "okunamayan metrik satırı 1"),
            "a cycle logged twice": (
                lambda: self.edit("pilot-log.md", "\n## Döngü 5 — 20261104T170000Z\n",
                                  "\n## Döngü 4 — 20261104T150000Z\n\n## Döngü 5 — 20261104T170000Z\n"),
                "20261104T150000Z günlükte iki kez"),
        }
        for name, (change, said) in cases.items():
            with self.subTest(name):
                shutil.rmtree(self.work)
                shutil.copytree(FIXTURE / "work", self.work)
                change()
                line = self.lines()[0]
                self.assertIn("UZLAŞMADI", line)
                self.assertIn(said, line)
                self.assertIn("bu sayılarla kural kurulmaz", line)

    def test_what_is_not_built_is_named_never_counted_as_zero(self):
        """A mechanism the pilot lacks is named with its register id ("ölçülmedi", "kurulmadı"); a record that cannot
        be read says so. A missing metrics file leaves every logged session unexplained, never zero sessions."""
        lines = self.lines()
        for n, register in ((1, "E535"), (3, "E536"), (5, "E535"), (7, "E529"), (8, "E532")):
            self.assertIn(register, lines[n])
        self.assertIn("ölçülmedi (hedef sınavı yok)", lines[2])
        (self.work / "pilot-metrics.jsonl").unlink()
        lines = self.lines()
        self.assertIn("metrik dosyası okunamadı", lines[0])
        self.assertIn("UZLAŞMADI, açıklanmayan 9", lines[0])
        self.assertTrue(lines[1].startswith("2. Harcama: metrik dosyası okunamadı"))

    def test_the_owners_two_measures_go_week_on_week(self):
        # daily_effort_any_verdict daily_week_closed_at_the_start daily_touch_counts_a_resume
        # daily_touch_heading_without_a_time_dropped
        """The owner's two measures (sabah-sorulari 2026-11-03), each this week against the week before: the effort of
        one kind of work (the median cost, minutes and turns of an accepted code push; a rejected push is not that
        work) and the human touches (a launcher started by hand, never a --resume, and each touch the operator logs;
        a touch heading without a time is counted as such, never dropped). A week is open at its start, as the day."""
        at = self.report.utc(AT)

        def row(stamp, verdict="accepted", cost=1.0, minutes=10.0, turns=10):
            return {"kind": "code", "pushed": True, "verdict": verdict, "stamp": stamp, "cost_usd": cost,
                    "minutes": minutes, "turns": turns}
        rows = [row("20261104T180000Z", cost=2.0, turns=11), row("20261104T000000Z", cost=4.0, turns=12),
                row("20261103T000000Z", verdict="rejected", cost=99.0),
                row("20261028T180000Z", cost=6.0, minutes=30.0),  # exactly 7 days old: the week before
                row("20261021T180000Z", cost=50.0)]  # exactly 14 days old: neither
        self.assertEqual(self.report.effort(rows, at), "aynı türden işin emeği (kabul edilen kod push'u, medyan): "
                         "son 7 gün n=2, 3,00 USD, 10,00 dk, 11,5 tur; önceki 7 gün n=1, 6,00 USD, 30,00 dk, 10 tur")
        starts = [{"kind": "intervention", "ts": "2026-11-04T10:00:00Z", "args": {"resume": "True"}},
                  {"kind": "intervention", "ts": "2026-11-04T11:00:00Z", "args": {"resume": "False"}},
                  {"kind": "intervention", "ts": "2026-10-28T18:00:00Z", "args": {}}]
        log = ("## Operatör dokunuşu — 2026-11-02 ~09:30Z (yaşam desteği)\n\n## Operatör dokunuşu — bir gün\n\n"
               "## Operatörün notu — 2026-11-02 10:00Z\n")
        marked = [(self.report.utc("2026-10-30T00:00:00Z"), "operatör: tohum dönemi (insan dokunuşu, `27`)"),
                  (self.report.utc("2026-11-01T00:00:00Z"), "operatör: bir not")]
        self.assertTrue(self.report.touches(starts, log, marked, at).endswith(
            "son 7 gün 3, önceki 7 gün 1, zamanı okunamayan 1"))

    def test_the_caps_are_the_referees_policy_or_said_unread(self):
        """The caps come from main's `policy.json` through the referee's own parser and the open stage from its lock;
        offline, unreadable or absent they are said so, never guessed."""
        no_stage_cap = json.loads(json.dumps(POLICY))
        del no_stage_cap["constitutional"]["stage_budgets"]["asama_0"]["founder_usd"]
        self.assertIn("aşama 0 Kurucu toplamı 82,65 USD, tavanı yok (sahip belirlemedi",
                      self.lines(get=self.get(no_stage_cap))[1])
        self.assertIn("aşama 1 Kurucu toplamı 0,00 USD", self.lines(get=self.get(stage=1))[1])
        no_caps = json.loads(json.dumps(POLICY))
        del no_caps["constitutional"]["day_cap_usd"], no_caps["constitutional"]["session_cap_usd"]
        self.assertIn("gün tavanı yok, oturum tavanı yok", self.lines(get=self.get(no_caps))[1])

        def down(path, raw):
            raise self.report.scorecard.ScorecardError(f"gh api {path}: HTTP 502")
        self.assertIn("tavanlar okunamadı: ScorecardError", self.lines(get=down)[1])
        self.reads.clear()
        self.assertIn("tavanlar okunamadı: okunmadı (--offline)", self.lines(referee=None)[1])
        self.assertEqual(self.reads, [])

    def test_improvement_is_proved_only_by_a_passed_exam(self):
        # scorecard_proved_without_the_exam
        """The card's own rule (`scorecard.proved`): only a controlled exam that passed says yes; verified self-found
        rows are shown as rows, never as proof; without a card the answer is no."""
        self.assertIn("kanıtlandı: hayır — kontrollü sınav not_run (E317)", self.lines()[9])
        karne = json.loads((self.work / "scorecard" / "karne.json").read_text(encoding="utf-8"))
        karne["public"]["exam"]["status"] = "pass"
        (self.work / "scorecard" / "karne.json").write_text(json.dumps(karne), encoding="utf-8")
        self.assertIn("kanıtlandı: evet — kontrollü sınav pass (E317)", self.lines()[9])
        karne["public"]["exam"]["status"] = "fail"
        (self.work / "scorecard" / "karne.json").write_text(json.dumps(karne), encoding="utf-8")
        self.assertIn("kanıtlandı: hayır", self.lines()[9])
        (self.work / "scorecard" / "karne.json").unlink()
        self.assertIn("kanıtlandı: hayır — karne yok", self.lines()[9])

    def test_the_report_writes_only_its_own_file(self):
        """Every input stays byte for byte; the one file added is <work>/gunluk-rapor/<date>.md, or --out."""
        before = {p.relative_to(self.work): p.read_bytes() for p in self.work.rglob("*") if p.is_file()}
        with mock.patch.object(self.report.shutil, "disk_usage", return_value=DISK):
            path = self.report.update(self.work, self.report.utc(AT), "owner/referee", get=self.get())
            out = self.report.update(self.work, self.report.utc(AT), None, out=self.tmp / "elsewhere.md")
        self.assertEqual(path, self.work / "gunluk-rapor" / "2026-11-04.md")
        self.assertEqual(out, self.tmp / "elsewhere.md")
        after = {p.relative_to(self.work): p.read_bytes() for p in self.work.rglob("*") if p.is_file()}
        self.assertEqual(set(after) - set(before), {Path("gunluk-rapor") / "2026-11-04.md"})
        self.assertEqual({k: v for k, v in after.items() if k in before}, before)
        self.assertEqual(path.read_text(encoding="utf-8"), (FIXTURE / "golden.md").read_text(encoding="utf-8"))
        with self.assertRaises(ValueError):
            self.report.render(["x"] * 11)


if __name__ == "__main__":
    unittest.main()
