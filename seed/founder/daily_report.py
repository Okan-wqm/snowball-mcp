"""The operator's daily observer report (register E537; the autonomy plan, section 6): ten lines, generated from the
pilot's records by this script and never written by hand. Stdlib only. It runs on its own, never inside the launcher.

    python seed/founder/daily_report.py [--work F:\\snowball-work] [--at 2026-11-04T18:00:00Z] [--offline] [--out F]

What it reads, every file opened read-only: <work>/pilot-metrics.jsonl and <work>/pilot-log.md (the launcher's two
records of each cycle), <work>/HALT, <work>/reports-seen.json, <work>/scorecard/karne.json (the card, E310) and each
window session's loader record <work>/logs/<stamp>/brain-definitions.json (E531). Without --offline, two GETs through
the operator's `gh` login: the referee's `policy.json` (its caps, parsed by the referee's own `policy_of`) and
`setup/stage.json` (the open stage; none is Stage 0). What it writes: only the report, <work>/gunluk-rapor/<date>.md
(the UTC date of --at), or --out. The report holds counts, ids and times, never the Founder's text.

The window is the 24 hours up to --at (the launcher's day cap counts the same window), and the report is as of --at:
a metrics row, a log cycle or a timed log line after it counts nowhere, so yesterday's report can be made today. Four
inputs are read as they are now: the HALT file, reports-seen.json, the card and the disk. The counts are the
launcher's own rules, imported, never copied: a session's spend is `launch.session_spend` (a cost the CLI did not
report counts at the session's brake), how it ended is its metrics row's `end` (a row from before E528 is classed
from its fields by `launch.session_end`; a brake cannot be told from an exit there), report ages are
`launch.report_ages`, and whether improvement is proved is the card's `scorecard.proved` (only the controlled exam
proves it).

Reconciliation (line 1): every cycle the log heads `## Döngü <n> — <stamp>` is matched by stamp to a metrics row. A
difference is explained only when the records say why: a session logged before the metrics file's first row (the file
began at cycle 9, `docs/pilot-gunlugu.md`), or a verdict the row corrects itself (`corrected_by`, E241). Every other
difference (a row the log lacks, a logged session without a row, a stamp twice, a verdict or push that disagrees, a
line that does not parse) is unexplained: the line then says UZLAŞMADI, and no rule may use the counts until it does
not. A mechanism the pilot does not have yet is named with its register id, never counted as zero.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import statistics
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "bootstrap"))
sys.path.insert(0, str(HERE))
import forecast_score  # noqa: E402  (the forecasts' scorer, E534)
import launch  # noqa: E402  (the launcher's own rules: spend, end, report ages, record times)
import scorecard  # noqa: E402  (the card's GET-only gh read and its rule for "proved")
from snowball_bootstrap.config import policy_of  # noqa: E402  (the referee's policy parser)

WINDOW = timedelta(hours=24)  # the launcher's day cap window (`launch.DAY_WINDOW_S`)
LINES = 10  # the plan's section 6: at most ten lines
REPORT_DIR = "gunluk-rapor"
LOADER_RECORD = "brain-definitions.json"
STALE_REPORT_H = 12  # an open report older than this is the plan's alarm age
OLD_REPORT_H = 72
TRAP_SESSIONS = 20
WEEK = timedelta(days=7)  # the owner's trend unit: human touches fall week on week (sabah-sorulari 2026-11-03)
END_ORDER = ("exit", "usage_limit", "timeout", "brake", "error")
CYCLE_RE = re.compile(r"^## Döngü (\d+) — (\d{8}T\d{6}Z)\s*$", re.M)
HEADING_RE = re.compile(r"^## ", re.M)
VERDICT_RE = re.compile(r"^- Hakemin kararı: \*\*([A-Za-z_]+)\*\*", re.M)
BRAIN_RE = re.compile(r"^- Beyin: `[0-9a-f]+` → `[0-9a-f]+`( \(push yok\))?", re.M)
TIMED_RE = re.compile(r"^- (\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ) (.*)$", re.M)
OPEN_RE = re.compile(r"^- Açık raporlar \((\d+), beyin `([0-9a-f]+)`[^:]*: (.*)$", re.M)
OPEN_ID_RE = re.compile(r"`([^`\s]+)` \d+ sa")
# the operator's touch records in the log (their form is not fixed, E277): a heading `## Operatör dokunuşu — <time>`
# or `## İnsan dokunuşu — … (<time>)`, and a timed line marked `(insan dokunuşu`
TOUCH_HEAD_RE = re.compile(r"^## (?:Operatör|İnsan) dokunuşu\b(?:[^\n]*?(\d{4}-\d\d-\d\d)[T ]~?(\d\d:\d\d))?", re.M)
TOUCH_MARK = "(insan dokunuşu"

Get = Callable[[str, bool], bytes]


def utc(text: str) -> datetime:
    return datetime.strptime(text, launch.TS_FORMAT).replace(tzinfo=timezone.utc)


def _number(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _num(x: float) -> str:
    return f"{x:.2f}".replace(".", ",")


# ---- reading -------------------------------------------------------------------------------------------------------
def _read(path: Path) -> bytes | None:
    try:
        return path.read_bytes()
    except OSError:
        return None


def _json(path: Path) -> Any:
    raw = _read(path)
    if raw is None:
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except ValueError:
        return {"unreadable": path.name}


def read_caps(referee: str, get: Get) -> dict[str, Any]:
    """The referee policy's caps and the open stage, or why they could not be read."""
    try:
        policy = policy_of(json.loads(get(f"repos/{referee}/contents/policy.json", True)))
        try:
            lock = json.loads(get(f"repos/{referee}/contents/setup/stage.json", True))
            stage = lock.get("stage") if isinstance(lock, dict) else None
        except scorecard.NotFound:
            stage = 0
        if type(stage) is not int or stage < 0:
            raise ValueError(f"setup/stage.json names no stage: {stage!r}")
    except (scorecard.ScorecardError, ValueError, KeyError, TypeError) as exc:
        return {"error": f"{type(exc).__name__}: {str(exc)[:120]}"}
    return {"session": policy.session_cap_usd_micros, "day": policy.day_cap_usd_micros, "stage": stage,
            "stage_cap": policy.stage_founder_usd_micros.get(stage)}


def parse_rows(metrics: bytes | None) -> list[Any]:
    """Every metrics line, a dict or None for one that does not parse."""
    return [launch._json_or_none(line) for line in (metrics or b"").decode("utf-8", "replace").splitlines()
            if line.strip()]


def gather(work: Path, at: datetime, referee: str | None, get: Get = scorecard.gh_get) -> dict[str, Any]:
    """Everything the report is built from; nothing here is written."""
    metrics = _read(work / "pilot-metrics.jsonl")
    log = _read(work / "pilot-log.md")
    rows = parse_rows(metrics)
    stamps = sorted({str(r.get("stamp")) for r in rows if isinstance(r, dict) and r.get("stamp")
                     and r.get("kind") != launch.INTERVENTION and in_window(launch._row_time(r), at)})
    loaders = {s: _json(work / "logs" / s / LOADER_RECORD) for s in stamps}
    try:
        free = shutil.disk_usage(work).free
    except OSError:
        free = None
    text = None if log is None else log_until(log.decode("utf-8", "replace").replace("\r\n", "\n"), at)  # CRLF: by hand
    return {"at": at, "metrics": metrics, "log": text,
            "halt": _json(work / launch.HALT_FILE), "seen": _json(work / launch.REPORTS_SEEN) or {},
            "karne": _json(work / "scorecard" / "karne.json"), "loaders": loaders, "disk_free": free,
            "caps": {"error": "okunmadı (--offline)"} if referee is None else read_caps(referee, get)}


# ---- the records ---------------------------------------------------------------------------------------------------
def in_window(when: datetime | None, at: datetime) -> bool:
    return when is not None and at - WINDOW < when <= at


def as_of(rows: list[Any], at: datetime) -> list[Any]:
    """The metrics rows as of `at`: a row timed after it is dropped; a line that does not parse has no time, stays."""
    return [r for r in rows if not isinstance(r, dict) or (launch._row_time(r) or at) <= at]


def log_until(log: str, at: datetime) -> str:
    """The log as of `at`: it is appended in order, so it is cut at the first cycle heading stamped after `at`."""
    stamp = at.strftime(launch.STAMP_FORMAT)
    later = next((m.start() for m in CYCLE_RE.finditer(log) if m.group(2) > stamp), len(log))
    return log[:later]


def log_cycles(log: str) -> list[dict[str, Any]]:
    """Each `## Döngü` section of the log: its stamp, whether a session ran, its push and verdict as logged."""
    out = []
    heads = [m.start() for m in HEADING_RE.finditer(log)] + [len(log)]
    for m in CYCLE_RE.finditer(log):
        body = log[m.end():min(h for h in heads if h > m.start())]
        brain = BRAIN_RE.search(body)
        verdict = VERDICT_RE.search(body)
        out.append({"stamp": m.group(2), "session": bool(re.search(r"^- Oturum:", body, re.M)),
                    "pushed": None if not brain else brain.group(1) is None,
                    "verdict": verdict.group(1) if verdict else None})
    return out


def reconcile(log: str | None, rows: list[Any]) -> dict[str, Any]:
    """The log's cycles against the metrics rows, by stamp (see the module's docstring)."""
    cycles = log_cycles(log or "")
    sessions = [c for c in rows if isinstance(c, dict) and c.get("kind") != launch.INTERVENTION]
    first = min((str(r.get("stamp")) for r in sessions if r.get("stamp")), default=None)
    unexplained: list[str] = [f"okunamayan metrik satırı {sum(1 for r in rows if not isinstance(r, dict))}"] \
        if any(not isinstance(r, dict) for r in rows) else []
    by_stamp: dict[str, dict[str, Any]] = {}
    for r in sessions:
        if str(r.get("stamp")) in by_stamp:
            unexplained.append(f"{r.get('stamp')} metrikte iki kez")
        by_stamp[str(r.get("stamp"))] = r
    logged: dict[str, dict[str, Any]] = {}
    before = 0
    corrected: list[str] = []  # the register id each correcting row names
    for c in cycles:
        if c["stamp"] in logged:
            unexplained.append(f"{c['stamp']} günlükte iki kez")
        logged[c["stamp"]] = c
        row = by_stamp.get(c["stamp"])
        if row is None:
            if not c["session"]:
                continue  # an outage's section: no session, no row
            if first is not None and c["stamp"] < first:
                before += 1
            else:
                unexplained.append(f"{c['stamp']} metrikte yok")
            continue
        if c["pushed"] is not None and c["pushed"] != bool(row.get("pushed")):
            unexplained.append(f"{c['stamp']} push farklı")
        if c["verdict"] != row.get("verdict"):
            if row.get("corrected_by"):
                corrected.append(str(row.get("corrected_by")).split(":")[0][:12])
            else:
                unexplained.append(f"{c['stamp']} karar farklı")
    unexplained += [f"{s} günlükte yok" for s in sorted(set(by_stamp) - set(logged))]
    return {"log_cycles": len(cycles), "log_sessions": sum(1 for c in cycles if c["session"]),
            "rows": len(sessions), "before_metrics": before, "corrected": corrected, "unexplained": unexplained}


def row_end(row: dict[str, Any]) -> str:
    """How a session ended: its row's `end` (E528), or the launcher's rule on the fields a row before E528 holds."""
    if isinstance(row.get("end"), str):
        return row["end"]
    return launch.session_end({"api_error": row.get("api_error"), "api_error_status": row.get("api_error_status"),
                               "timed_out": bool(row.get("timed_out")) or row.get("session_exit") == -1,
                               "exit": row.get("session_exit")})


# ---- the ten lines -------------------------------------------------------------------------------------------------
def build(inputs: dict[str, Any]) -> list[str]:
    """The report's lines from its inputs: deterministic, no clock, no network."""
    at: datetime = inputs["at"]
    rows = as_of(parse_rows(inputs["metrics"]), at)
    good = [r for r in rows if isinstance(r, dict)]
    sessions = [r for r in good if r.get("kind") != launch.INTERVENTION and in_window(launch._row_time(r), at)]
    starts = [r for r in good if r.get("kind") == launch.INTERVENTION and in_window(launch._row_time(r), at)]
    rec = reconcile(inputs["log"], rows)
    every = [(utc(m.group(1)), m.group(2)) for m in TIMED_RE.finditer(inputs["log"] or "")]
    timed = [(when, text) for when, text in every if in_window(when, at)]
    return [line1(inputs, sessions, rec, timed), line2(inputs, sessions), line3(sessions), line4(inputs, good),
            line5(forecast_score.score(good)), line6(), line7(inputs, good),
            line8(inputs, good, sessions, starts, timed, every),
            line9(inputs), line10(inputs)]


def line1(inputs: dict[str, Any], sessions: list[dict], rec: dict[str, Any], timed: list) -> str:
    pushed = [r for r in sessions if r.get("pushed")]
    verdicts = [r.get("verdict") for r in pushed]
    ends: dict[str, int] = {}
    for r in sessions:
        ends[row_end(r)] = ends.get(row_end(r), 0) + 1
    order = sorted(ends, key=lambda e: (END_ORDER.index(e) if e in END_ORDER else len(END_ORDER), e))
    end_text = ", ".join(f"{e} {ends[e]}" for e in order) or "—"
    halt = inputs["halt"]
    halt_text = "yok" if halt is None else f"var ({str(halt.get('reason', halt))[:80]})"
    if inputs["metrics"] is None:
        head = "metrik dosyası okunamadı"
    else:
        accepted, rejected = verdicts.count("accepted"), verdicts.count("rejected")
        head = (f"{len(sessions)}; push {len(pushed)} (kabul {accepted}, ret {rejected}, karar yok "
                f"{len(pushed) - accepted - rejected}), push yok {len(sessions) - len(pushed)}; bitiş {end_text}")
    un = rec["unexplained"]
    recon = (f"günlük {rec['log_cycles']} döngü ({rec['log_sessions']} oturumlu), metrik {rec['rows']}; açıklanan: "
             f"metrik öncesi {rec['before_metrics']}, düzeltilmiş satır {len(rec['corrected'])}"
             + (f" ({', '.join(sorted(set(rec['corrected'])))})" if rec["corrected"] else "") + "; "
             + (f"UZLAŞMADI, açıklanmayan {len(un)} ({'; '.join(un[:3])}): bu sayılarla kural kurulmaz" if un
                else "açıklanmayan 0"))
    halts = sum(1 for _when, text in timed if text.startswith("**HALT**"))
    return (f"1. Oturumlar (son 24 sa, bitiş {inputs['at'].strftime(launch.TS_FORMAT)}): {head}; HALT satırı "
            f"{halts}, HALT dosyası {halt_text}. Kayıt uzlaşması: {recon}.")


def line2(inputs: dict[str, Any], sessions: list[dict]) -> str:
    caps = inputs["caps"]
    at = inputs["at"]
    if inputs["metrics"] is None:
        return "2. Harcama: metrik dosyası okunamadı; geliştirme payı ölçülmedi (E535 kurulmadı), sınır %15."
    spend = [s for s in launch.session_spend(inputs["metrics"], at) if s[0] <= at]  # day_spent has no upper bound
    day = launch.day_spent(spend, at) / 1e6
    unreported = sum(1 for r in sessions if not isinstance(r.get("cost_usd"), (int, float)))
    head = (f"2. Harcama (24 sa): {_num(day)} USD (başlatıcının sayımı; maliyeti bildirilmeyen {unreported} oturum "
            "freniyle sayıldı)")
    if "error" in caps:
        return head + f"; tavanlar okunamadı: {caps['error']}; geliştirme payı ölçülmedi (E535 kurulmadı), sınır %15."
    stage = caps["stage"]
    stage_spent = sum(usd for _when, usd, row_stage in spend if row_stage == stage) / 1e6

    def cap(v: int | None) -> str:
        return "yok" if v is None else f"{v // 1_000_000} USD"
    stage_cap = ("tavanı yok (sahip belirlemedi; tavan yalnız uyarır)" if caps["stage_cap"] is None
                 else f"tavanı {cap(caps['stage_cap'])} (yalnız uyarı)")
    return (head + f", gün tavanı {cap(caps['day'])}, oturum tavanı {cap(caps['session'])}; aşama {stage} Kurucu "
            f"toplamı {_num(stage_spent)} USD, {stage_cap}; geliştirme payı ölçülmedi (E535 kurulmadı), sınır %15.")


def line3(sessions: list[dict]) -> str:
    targets = sorted({str(r["target_sha"])[:7] for r in sessions if r.get("target_sha")})
    return ("3. Hedef: kullanılabilir birim (/32), PR ve birleştirme kayıtta yok: ölçülmedi (hedef sınavı yok); "
            f"oturumların hedef commit'i {', '.join(f'`{t}`' for t in targets) or '—'}.")


def _loaded(inputs: dict[str, Any]) -> list[tuple[str, dict]]:
    return [(s, r) for s, r in sorted(inputs["loaders"].items()) if isinstance(r, dict) and "unreadable" not in r]


def weeks(when: datetime | None, at: datetime) -> int | None:
    """0 for the 7 days up to `at`, 1 for the 7 days before them, None otherwise; each week is open at its start, as
    the day window is."""
    if when is None or when > at:
        return None
    back = int((at - when) / WEEK)
    return back if back < 2 else None


def effort(good: list[dict], at: datetime) -> str:
    """The owner's measure of a skill that grows (sabah-sorulari 2026-11-03): the effort of one kind of work over time,
    the median cost, minutes and turns of an accepted code push, this week against the week before. The records
    name no finer kind of work."""
    out = []
    for back, name in ((0, "son 7 gün"), (1, "önceki 7 gün")):
        done = [r for r in good if r.get("kind") == "code" and r.get("verdict") == "accepted"
                and r.get("pushed") and weeks(launch._row_time(r), at) == back]
        cost = [launch._row_cost(r) / 1e6 for r in done]
        minutes = [r["minutes"] for r in done if _number(r.get("minutes"))]
        turns = [r["turns"] for r in done if _number(r.get("turns"))]
        out.append(f"{name} n={len(done)}" + ("" if not done else (
            f", {_num(statistics.median(cost))} USD, "
            f"{'—' if not minutes else _num(statistics.median(minutes))} dk, "
            f"{'—' if not turns else format(statistics.median(turns), 'g').replace('.', ',')} tur")))
    return "aynı türden işin emeği (kabul edilen kod push'u, medyan): " + "; ".join(out)


def touches(good: list[dict], log: str | None, every: list[tuple[datetime, str]], at: datetime) -> str:
    """The owner's counter of human touches, this week against the week before (sabah-sorulari 2026-11-03): a
    launcher started by hand (its row, not a --resume) and each touch the operator logs."""
    count = [0, 0]
    when_of = [launch._row_time(r) for r in good if r.get("kind") == launch.INTERVENTION
               and str((r.get("args") or {}).get("resume")) != "True"]
    when_of += [when for when, text in every if TOUCH_MARK in text]
    unread = 0  # a touch heading without a time it can be placed by is counted, never dropped
    for m in TOUCH_HEAD_RE.finditer(log or ""):
        try:
            when = datetime.strptime(f"{m.group(1)}T{m.group(2)}", "%Y-%m-%dT%H:%M")
        except (TypeError, ValueError):
            unread += 1
            continue
        when_of.append(when.replace(tzinfo=timezone.utc))
    for when in when_of:
        back = weeks(when, at)
        if back is not None:
            count[back] += 1
    return (f"insan dokunuşu (elle başlatma ve günlükteki dokunuş kaydı; kaydın biçimi tanımsız, E277) son 7 gün "
            f"{count[0]}, önceki 7 gün {count[1]}" + (f", zamanı okunamayan {unread}" if unread else ""))


def line4(inputs: dict[str, Any], good: list[dict]) -> str:
    loaded = _loaded(inputs)
    if loaded:
        stamp, rec = loaded[-1]
        last = (f"son yükleme ({stamp}, commit `{str(rec.get('brain'))[:7]}`): ajan {len(rec.get('agents') or [])}, "
                f"beceri {len(rec.get('skills') or [])}")
    else:
        last = "pencerede yükleyici kaydı yok"
    return (f"4. Büyüme: sinyal ve DRAFT/SHADOW/LIVE/emekli organ kaydı yok (E536 kurulmadı); {last}; "
            f"{effort(good, inputs['at'])}.")


def _pair(score: dict[str, Any], digits: int) -> str:
    """The Founder's mean loss against the base rate's on the same events, or a dash when there is none."""
    if not score["n"]:
        return "—"
    return "/".join(f"{score[k]:.{digits}f}".replace(".", ",") for k in ("founder", "base"))


def line5(fc: dict[str, Any]) -> str:
    """The forecasts over the whole record up to --at (`forecast_score`, E534): calibration needs history."""
    acc, sol = fc["accept"], fc["solve"]
    need = (f"yetersiz olay n_fail={fc['fail_events']}/{fc['fail_needed']} (tahminli ret): güven haritası çizilmez"
            if fc["fail_events"] < fc["fail_needed"] else
            f"olay yeterli n_fail={fc['fail_events']}/{fc['fail_needed']}: güven haritası kurulmadı")
    return (f"5. Tahmin (kaydın tümü, Kurucu/taban): kabul olayı {fc['pushes']} (tahminli {fc['forecasted']}; "
            f"tahminsiz olay taban oranla), Brier {_pair(acc['brier'], 4)}, log-loss {_pair(acc['log'], 4)}; çözüm "
            f"olayı {sol['brier']['n']} (açık {fc['solve_open']}), Brier {_pair(sol['brier'], 4)}; pinball maliyet "
            f"{_pair(fc['cost'], 2)} USD (n={fc['cost']['n']}), tur {_pair(fc['turns'], 2)} (n={fc['turns']['n']}); "
            f"biçime uymayan {fc['invalid']}, aynı push'ta fazladan {fc['extra']}; {need}.")


def line6() -> str:
    return (f"6. Tuzak alarmı: ölçülmedi (E535 kurulmadı: iş ile geliştirme ayrılmıyor; {TRAP_SESSIONS} oturumluk iç "
            "büyüme ve dış hareket hesaplanmıyor).")


def line7(inputs: dict[str, Any], good: list[dict]) -> str:
    found = list(OPEN_RE.finditer(inputs["log"] or ""))
    if not found:
        return "7. Açık raporlar: günlükte kayıt yok; engelleyici ayrımı ve sahip kapısı kaydı yok."
    m = found[-1]
    ids = OPEN_ID_RE.findall(m.group(3))
    seen = inputs["seen"] if isinstance(inputs["seen"], dict) and "unreadable" not in inputs["seen"] else {}
    ages = [age for _rid, age in launch.report_ages([{"id": i, "state": "open"} for i in ids], dict(seen),
                                                    inputs["at"].strftime(launch.TS_FORMAT))]
    young = sum(1 for a in ages if a < STALE_REPORT_H)
    old = sum(1 for a in ages if a > OLD_REPORT_H)
    unanswered = next((r.get("reports_unanswered") for r in reversed(good)
                       if r.get("kind") != launch.INTERVENTION and "reports_unanswered" in r), None)
    return (f"7. Açık rapor {m.group(1)} (son döngü, beyin `{m.group(2)}`): {STALE_REPORT_H} saatten yeni {young}, "
            f"{STALE_REPORT_H}–{OLD_REPORT_H} sa {len(ages) - young - old}, {OLD_REPORT_H} saatten eski {old}, en eski "
            f"{max(ages, default=0)} sa; cevapsız (operatör) {'kayıt yok' if unanswered is None else unanswered}; "
            "engelleyici ayrımı ve sahip kapısı kaydı yok.")


def line8(inputs: dict[str, Any], good: list[dict], sessions: list[dict], starts: list[dict], timed: list,
          every: list) -> str:
    at = inputs["at"]
    limits = sum(1 for r in sessions if row_end(r) == "usage_limit")
    resumes = sum(1 for r in starts if str((r.get("args") or {}).get("resume")) == "True")
    count = {k: sum(1 for _when, text in timed if needle in text) for k, needle in
             (("orphan", "hâlâ koşan kapsül durduruldu"), ("breaker", "başarısızlık,"), ("day", "günlük tavan:"))}
    times = sorted(t for t in (launch._row_time(r) for r in good) if t is not None and t <= at) + [at]
    gaps = [(b - a).total_seconds() / 3600 for a, b in zip(times, times[1:]) if b > at - WINDOW]
    free = inputs["disk_free"]
    return (f"8. Olaylar (24 sa): kullanım sınırı {limits}, başlatıcı başlangıcı {len(starts)} (--resume {resumes}), "
            f"yetim kapsül durdurma {count['orphan']}, kesici beklemesi {count['breaker']}, gün tavanı beklemesi "
            f"{count['day']}; boş disk {'okunamadı' if free is None else _num(free / 1e9) + ' GB'}; nabız yok "
            f"(E529 kurulmadı), kayıtlar arası en uzun boşluk {_num(max(gaps)) if gaps else '—'} sa; "
            f"{touches(good, inputs['log'], every, at)}.")


def line9(inputs: dict[str, Any]) -> str:
    recs = inputs["loaders"]
    loaded = _loaded(inputs)
    failed = sum(1 for _s, r in loaded if r.get("error"))
    skipped = sum(int(r.get("skipped_total") or 0) for _s, r in loaded)
    unreadable = sum(1 for r in recs.values() if isinstance(r, dict) and "unreadable" in r)
    return ("9. Kapsama: kanarya isabeti ve dışa çıkış reddi ölçülmedi (E532 kurulmadı); yükleyici (24 sa): kayıt "
            f"{len(loaded)}/{len(recs)} oturum (okunamayan {unreadable}), yükleyemeyen {failed}, atlanan tanım "
            f"{skipped}.")


def line10(inputs: dict[str, Any]) -> str:
    karne = inputs["karne"]
    if not isinstance(karne, dict) or not isinstance(karne.get("public"), dict):
        return "10. Kendini geliştirdiği kanıtlandı: hayır — karne yok ya da okunamadı (`scorecard.py`)."
    public = karne["public"]
    verified = ((karne.get("private") or {}).get("self_found") or {}).get("verified") or []
    card_at = ((public.get("as_of") or {}).get("last_run") or {}).get("created_at", "—")
    exam = public.get("exam") or {}
    proved = scorecard.proved({"exam": {"status": exam.get("status")}})
    why = f"kontrollü sınav {exam.get('status', '—')} ({exam.get('register', '—')})"
    return (f"10. Kendini geliştirdiği kanıtlandı: {'evet' if proved else 'hayır'} — {why}; karne {card_at} "
            f"itibarıyla; doğrulanmış öz-tespit satırı: {', '.join(verified) or 'yok'} (tek başına kanıt değil).")


def render(lines: list[str]) -> str:
    if len(lines) > LINES:
        raise ValueError(f"the report has {len(lines)} lines; the plan allows {LINES}")
    return "\n".join(lines) + "\n"


def update(work: Path, at: datetime, referee: str | None, out: Path | None = None,
           get: Get = scorecard.gh_get) -> Path:
    """Gather, build and write the report; the only file written."""
    text = render(build(gather(work, at, referee, get)))
    path = out or work / REPORT_DIR / f"{at.strftime('%Y-%m-%d')}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))
    return path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--work", type=Path, default=Path(r"F:\snowball-work"))
    p.add_argument("--referee", default="Okan-wqm/snowball-rehearsal-referee")
    p.add_argument("--at", type=utc, help="the window's end, UTC (default: now)")
    p.add_argument("--offline", action="store_true", help="no GitHub read: the caps line says they were not read")
    p.add_argument("--out", type=Path, help="write the report here instead of <work>/gunluk-rapor/<date>.md")
    args = p.parse_args(argv)
    at = args.at or datetime.now(timezone.utc).replace(microsecond=0)
    path = update(args.work, at, None if args.offline else args.referee, args.out)
    sys.stdout.write(path.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
