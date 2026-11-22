"""The measurement mirror: `/work/logs/mirror.json` (the owner's decision of 2026-11-19, E647). Stdlib only.

Facts the Founder reads at each session start: what each model version cost and what the referee said of its pushes,
what the live loop's runs did after each transfer, which rejection and red classes came back, how large the transferred
referee is, how often a session handed work to agents, how long the pilot stood between sessions, where each session's
time and the quota buckets went (epoch Z), and which micro-features of Stage 1's first slice (`26h`) are not accepted
yet. Facts only: no
advice, no ranking, no judgement of what could have been seen earlier (no-feeding). Every section names its source and
its window. A metric that cannot be computed is null and its reason is in the section's ``null_reasons``; a section that
fails is ``{"value": null, "reason": ...}`` and the others stand. Every list has a cap and says what it left out. The
same files give the same bytes: no clock is read, the session's stamp is the time. Nothing here reaches the network:
the launcher's own records on disk, the referee repository's tarball the launcher downloads for /vec anyway, the
seed's own batch table, and the accepted manifest's `done_mf` the launcher read for it (``accepted``).
"""

from __future__ import annotations

import io
import json
import math
import re
import statistics
import tarfile
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

VERSION = 1
FACTS_ONLY = ("observation: the launcher's records and the referee tarball, counted; no advice, no ranking, "
              "no judgement; lists in a fixed order (time, or class name), never by size")
WINDOW_DAYS = 14  # the window of `repeats`
SESSIONS_MAX = 20  # the newest sessions `delegation`, `waiting` and `session_time` read
MODELS_MAX, TRANSFERS_MAX, RUNS_MAX, UNATTRIBUTED_MAX, REPEATS_MAX, DATES_MAX = 10, 30, 10, 10, 20, 10
TEXT_MAX = 200  # characters of a recorded output line
OUTPUT_LINES = 2  # of a red job's recorded output
FILE_MAX = 4 * 1024 * 1024  # bytes of one referee tarball member or session-folder note that is read
TRANSCRIPT_MAX = 64 * 1024 * 1024
USD_LABEL = "cli_estimate"  # the CLI's own total_cost_usd: an estimate, never an invoice
AGENT_TOOLS = ("Agent", "Task")  # the CLI's subagent tool, under both of its names
RUNS_MAX = 50  # agent runs listed per session; the rest are counted in runs_left_out
# The operator's price table (seed/founder/prices.json): USD micros per million tokens of each kind (seed-097, E720)
PRICE_KEYS = ("in", "out", "cache_read", "cache_write_5m", "cache_write_1h")
UNKNOWN_BASIS = "unknown"
IN_KEYS = ("in", "cache_read", "cache_write_5m", "cache_write_1h")  # what a transcript message gives exactly  # the CLI's costBasis for a model whose price basis it does not know
COST_IS = ("derived: the run's tokens by kind times the operator's price table row of its served model, rounded to "
           "whole micros; never the CLI's figure. The transcript gives each API message's input, cache read and "
           "cache write tokens (a foreground run's last message only in its Agent call's tool_use_result usage); "
           "its output_tokens is the count as the message's stream began, so a run's output "
           "tokens are the closing modelUsage's outputTokens of its model when it is that model's only run in the "
           "session and the session's own model is another (out_from cli_model_line), else null. cost_floor: the "
           "same without output tokens. Null with not_measured: output_tokens_unlogged (cost_floor stands), "
           "price_unknown:<model> when the table has no row for the model or the session's closing modelUsage gives "
           "that model no known costBasis, no_usage when no message of the run carries usage, usage_unreadable when "
           "one carries no input or cache count or no split of its cache writes")
EXACTNESS = ("models_cli is the CLI's figure per model for the whole session: it equals one run's cost only when the "
             "session ran that agent once on that model and the session's own model is another one")
# A rival-side failure (the referee's rule, decide.py: any api_error reason leaves the head unevaluated): an outage,
# never the Founder's rejection (E721). An isolation fault is the referee's own stop, not the rival's.
OUTAGE_REF, ISOLATION_REF = "api_error:", "api_error:isolation_"
UNJUDGED_OUTAGE = {"cause": "outage", "owner": "rival"}
RED = ("failure", "timed_out", "startup_failure")
REJECTED = ("rejected", "frozen")
INTERVENTION = "intervention"  # a launcher start's metrics row (launch.py)
STAMP_RE = re.compile(r"[0-9]{8}T[0-9]{6}Z")
TIME_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")
SHA_RE = re.compile(r"[0-9a-f]{40}")
WORD_RE = re.compile(r"[A-Za-z0-9_.:@/+\[\]-]{1,80}")  # a model id may carry brackets: claude-x[1m]
CONTROL, IMPORTS = "control.json", "setup/imports.jsonl"  # the operator's files in the referee repository
OFF_LIVE, MUTANTS_DIR = "status/off_live.json", "tests/mutants/"  # the brain's own records in its referee/ tree
# A Bash call counts as the session's own check when its command matches (the epoch Z panels' method, stated, not tuned)
OWN_CHECKS = re.compile(r"mutant|mutate|prepush|unittest|pytest|test_|tests")
# rate_limit_info.unifiedWindows.<bucket>.utilization, each bucket named as the CLI names it
QUOTA_WINDOWS = ("seven_day_overage_included", "seven_day", "five_hour")
BLOCKED_IS = ("a sum over the session's foreground Bash calls whose command matches own_checks_pattern: calls that "
              "ran at once each count, so it can exceed wall_s; a lower bound otherwise (a call under about 30 s "
              "sends no heartbeat)")
P1_TABLE = "stage1-P1.json"  # the seed's batch table of the first slice's batch (`26e`, `26h`)
SLICE_OWN = (1, 2, 3, 5, 6)  # Stage 1's own micro-features of the first slice, in `26h`'s order
TEST_RE = re.compile(rb"(?m)^[ \t]*(?:async[ \t]+)?def[ \t]+test\w*[ \t]*\(")

SOURCES = {
    "per_model": "pilot-metrics.jsonl cycle rows (model_served or model, effort, pushed, kind, verdict, reasons, "
                 "cost_usd, minutes); a push whose row has no verdict takes the verdict the next session's "
                 "previous-session.json recorded (verdicts_from_next_session: kind and reasons unknown). outages: "
                 "pushes the rival's own failure left unjudged (the row's unjudged cause outage, or an older row "
                 "rejected for api_error rival reasons alone), never a verdict or a rejection reason; one takes a "
                 "later verdict only from a note that names it evaluated. accepted: "
                 "every accepted verdict, code and exit alike, and those from the next session. rejected_rows_by_reason: "
                 "rejected or frozen rows carrying a reason kind, a row once per kind. founder_cli_usd: the Founder's "
                 "own CLI sessions only (cli_estimate); the referee's runs, the rival's calls and any review are not "
                 "in it, so founder_cli_usd_per_accepted is not the total cost per accepted change",
    "live_attempts": "the referee tarball's control.json reverted_exits and setup/imports.jsonl (a reverted import's "
                     "row is gone with its revert); logs/*/loop-runs.jsonl, each session's read of the newest loop.yml "
                     "runs, the newest read of a run kept; a run belongs to the transfer its cek job's summary names "
                     "(accepted.transfer_sha); runs no session read are not here. A transfer's outcome counts only the "
                     "runs tied to it: a red run whose cek named no transfer is in unattributed_red_runs and in no "
                     "transfer's outcome",
    "repeats": "rejection reason kinds of rejected and frozen rows in pilot-metrics.jsonl, and red job classes "
               "(job:reason) of the loop runs in logs/*/loop-runs.jsonl; count: the rows or runs that carry the "
               "class, each once; a class carried by more than one, in class order",
    "size": "the referee repository tarball the launcher downloaded for /vec this cycle: the referee/ tree of the last "
            "transfer (every top folder but the operator's and bootstrap/); spec pages: the launcher's checkout",
    "delegation": "logs/<stamp>/session-<stamp>.jsonl: every Agent or Task tool call (a subagent's own too), its "
                  "model (inherit when none is named) and subagent_type; Workflow calls; the models the closing "
                  "result event lists. runs: one entry per call, keyed by its tool_use_id: the model its messages "
                  "were served by, the call's effort, the calling run (parent, null for the session's own call), "
                  "status and wall_ms from its task_notification (unfinished when none), tokens by kind summed once "
                  "per API message id over the messages whose parent_tool_use_id is the call's (a nested run is its "
                  "own entry), and cost_usd_micros (cost_is). models_cli: the closing result event's modelUsage per "
                  "model (tokens, costUSD as micros, costBasis). prices: seed/founder/prices.json as the operator "
                  "wrote it",
    "waiting": "pilot-metrics.jsonl: from a session's end (its stamp plus its minutes) to the next session's start; the "
               "gap holds the referee's verdict wait, outage and usage-limit waits and any time the launcher was not "
               "running (a STOP, a crash); launcher_starts_in_gap counts the intervention rows in it. The launcher "
               "logs no wait by its cause",
    "session_time": "wall_s: the session's pilot-metrics.jsonl minutes (the launcher's clock around the container), "
                    "times 60; the transcript's result events time only their own turn, so they give no wall time. "
                    "logs/<stamp>/session-<stamp>.jsonl: api_s, the largest duration_api_ms of its result events "
                    "(the CLI sums it over the session); blocked_on_own_checks_s, every foreground Bash call whose "
                    "command matches own_checks_pattern, its largest tool_progress elapsed_time_seconds, summed: a "
                    "lower bound (a call under about 30 s sends no heartbeat, a background call and a wait outside "
                    "Bash are not counted) and calls that ran at once each count, so it can exceed wall_s; null for a "
                    "session whose transcript has no result event; quota_start and quota_end, per bucket "
                    "(seven_day_overage_included, seven_day, five_hour), the first and the last rate_limit_event's "
                    "rate_limit_info.unifiedWindows.<bucket>.utilization",
    "path": "26h's first slice: the seed's P1 table (stages/stage1-P1.json), then Stage 1's own MF1, MF2, MF3, MF5 and "
            "MF6. path_mfs_left: P1's micro-features the manifest (snowball-tests.json) at the signed state's "
            "last_accepted_sha does not list in done_mf, the launcher's read of it; none once the referee tarball's "
            "setup/imports.jsonl has P1's transfer row. Stage 1's own micro-features are in no table and no signed "
            "record accepts them, so they are listed apart",
}


def mirror(stamp: str, metrics: Path, logs: Path, referee: dict | None, spec: Path, accepted: dict | None = None,
           stages: Path | None = None, prices=None) -> dict:
    """The mirror for the session starting at ``stamp``: ValueError for a stamp that is not one. Each section reads
    its own inputs, so a file that cannot be read is the null of the sections that need it. ``accepted`` is the
    launcher's read of the accepted manifest (``{"sha", "done_mf"}`` or ``{"error"}``), ``stages`` the seed's
    table folder, ``prices`` the operator's price table as read (``{"error": <class>}`` when it could not be)."""
    at = stamp_time(stamp)
    before = lambda: [f for f in folders(logs, stamp) if f < stamp][-SESSIONS_MAX:]  # noqa: E731
    sections = {
        "per_model": lambda: per_model(cycles(metrics, stamp), late_verdicts(logs, folders(logs, stamp))),
        "live_attempts": lambda: live_attempts(referee, loop_runs(logs, folders(logs, stamp))),
        "repeats": lambda: repeats(cycles(metrics, stamp), loop_runs(logs, folders(logs, stamp)), at),
        "size": lambda: size(referee, spec),
        "delegation": lambda: delegation(logs, before(), prices),
        "waiting": lambda: waiting(cycles(metrics, stamp), starts(metrics), at),
        "session_time": lambda: session_time(logs, before(), cycles(metrics, stamp)),
        "path": lambda: path(accepted, referee, stages),
    }
    note = {"mirror": VERSION, "stamp": stamp, "facts_only": FACTS_ONLY}
    for name, build in sections.items():
        try:
            note[name] = dict(build(), source=SOURCES[name])
        except Exception as exc:  # one section's failure is its own null, never the others' nor the session's
            note[name] = {"value": None, "reason": f"not computed: {type(exc).__name__}", "source": SOURCES[name]}
    return note


# ---- reading -----------------------------------------------------------------------------------------------------
def stamp_time(stamp: str) -> datetime:
    if not isinstance(stamp, str) or not STAMP_RE.fullmatch(stamp):
        raise ValueError("not a session stamp")
    return datetime.strptime(stamp, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)


def iso_time(text) -> datetime | None:
    return (datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            if isinstance(text, str) and TIME_RE.fullmatch(text) else None)


def word(value) -> str | None:
    """A model, kind, class or name as recorded, when it is one bounded word; else None (never a free text)."""
    return value if isinstance(value, str) and WORD_RE.fullmatch(value) else None


def rival_outage(reasons) -> bool:
    """Whether every reason is the rival's own failure on its side (`rival_unresolved` with an `api_error:` ref other
    than an isolation fault): the referee leaves such a head unevaluated (decide.py), so it is an outage (E721)."""
    if not isinstance(reasons, list) or not reasons:
        return False
    return all(isinstance(r, dict) and r.get("kind") == "rival_unresolved"
               and str(r.get("ref") or "").startswith(OUTAGE_REF) and not str(r.get("ref")).startswith(ISOLATION_REF)
               for r in reasons)


def outage(row: dict) -> bool:
    """A cycle row whose push the rival's outage left unjudged: its ``unjudged`` names the outage, or an older row
    (written before the launcher named outages) says rejected for such reasons alone."""
    unjudged = row.get("unjudged")
    if isinstance(unjudged, dict) and unjudged.get("cause") == UNJUDGED_OUTAGE["cause"]:
        return True
    return row.get("verdict") == "rejected" and rival_outage(row.get("reasons"))


def number(value) -> float | None:
    ok = isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0
    return float(value) if ok else None


def json_lines(path: Path, limit: int = FILE_MAX) -> list[dict]:
    """The JSON objects of a JSON-lines file; a broken line is skipped, a missing or larger file is []."""
    if not path.is_file() or path.stat().st_size > limit:
        return []
    out = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            row = json.loads(line)
        except (ValueError, RecursionError):  # a broken or too deeply nested line is skipped, never the file
            continue
        if isinstance(row, dict):
            out.append(row)
    return out


def cycles(metrics: Path, stamp: str) -> list[dict]:
    """The cycle rows of `pilot-metrics.jsonl` before the session at ``stamp``, in stamp order."""
    rows = [r for r in json_lines(metrics, limit=1 << 30) if r.get("kind") != INTERVENTION
            and isinstance(r.get("stamp"), str) and STAMP_RE.fullmatch(r["stamp"]) and r["stamp"] < stamp]
    return sorted(rows, key=lambda r: r["stamp"])


def starts(metrics: Path) -> list[str]:
    """When the launcher started (its `intervention` rows' `ts`), in order."""
    return sorted(r["ts"] for r in json_lines(metrics, limit=1 << 30) if r.get("kind") == INTERVENTION
                  and isinstance(r.get("ts"), str) and TIME_RE.fullmatch(r["ts"]))


def folders(logs: Path, stamp: str) -> list[str]:
    """The session folders up to this session's own, in order."""
    return sorted(p.name for p in logs.iterdir() if p.is_dir() and STAMP_RE.fullmatch(p.name)
                  and p.name <= stamp) if logs.is_dir() else []


def late_verdicts(logs: Path, folders: list[str]) -> dict[str, dict]:
    """stamp -> {verdict, evaluated} a later session's previous-session.json recorded for it (the launcher's E381
    look-up; ``evaluated`` is true only when the note says the referee evaluated the head)."""
    out = {}
    for folder in folders:
        path = logs / folder / "previous-session.json"
        try:
            note = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None
        except (ValueError, RecursionError):
            continue
        if isinstance(note, dict) and isinstance(note.get("stamp"), str) and word(note.get("verdict")):
            out[note["stamp"]] = {"verdict": note["verdict"], "evaluated": note.get("evaluated") is True}
    return out


def loop_runs(logs: Path, folders: list[str]) -> dict[int, dict]:
    """run id -> {run, jobs}: the newest session folder's read of each run replaces an older one's whole."""
    runs: dict[int, dict] = {}
    for folder in folders:
        seen: dict[int, dict] = {}
        for row in json_lines(logs / folder / "loop-runs.jsonl"):
            rid = row.get("id") if row.get("kind") == "run" else row.get("run")
            if not isinstance(rid, int) or isinstance(rid, bool):
                continue
            if row.get("kind") == "run":
                seen.setdefault(rid, {"run": row, "jobs": []})["run"] = row
            elif row.get("kind") == "job":
                seen.setdefault(rid, {"run": None, "jobs": []})["jobs"].append(row)
        runs.update({rid: one for rid, one in seen.items() if one["run"] is not None})
    return runs


# ---- per model version -------------------------------------------------------------------------------------------
def reason_kinds(row: dict) -> list[str]:
    """The reason kinds a verdict row carries, each once: four `exit_condition` reasons are one rejection."""
    return sorted({word(r.get("kind")) or "unknown" for r in row.get("reasons") or [] if isinstance(r, dict)})


def per_model(rows: list[dict], late: dict[str, dict]) -> dict:
    groups: dict[tuple, dict] = {}
    for row in rows:
        key = (word(row.get("model_served")) or word(row.get("model")) or "unrecorded",
               (word(row.get("effort")) or "default") if "effort" in row else "unrecorded")
        g = groups.setdefault(key, {"rows": [], "pushes": 0, "verdicts": Counter(), "late": Counter(), "unjudged": 0,
                                    "reasons": Counter(), "accepted": 0, "usd": [], "no_usd": 0, "minutes": [],
                                    "outages": 0})
        g["rows"].append(row["stamp"])
        g["pushes"] += row.get("pushed") is True
        verdict = word(row.get("verdict"))
        unjudged = outage(row)  # the rival's outage: never a verdict, never a rejection reason (E721)
        if verdict and not unjudged:
            g["verdicts"][f"{word(row.get('kind')) or 'unknown'}:{verdict}"] += 1
            if verdict in REJECTED:
                g["reasons"].update(reason_kinds(row))
        elif row.get("pushed") is True:
            seen = late.get(row["stamp"]) or {}
            verdict = word(seen.get("verdict")) if seen.get("evaluated") or not unjudged else None
            if verdict:
                g["late"][verdict] += 1
            elif unjudged:
                g["outages"] += 1
            else:
                g["unjudged"] += 1
        g["accepted"] += verdict == "accepted"
        cost = number(row.get("cost_usd"))
        if cost is None:
            g["no_usd"] += 1
        else:
            g["usd"].append(cost)
        if number(row.get("minutes")) is not None:
            g["minutes"].append(number(row["minutes"]))
    models = []
    for (model, effort), g in groups.items():
        nulls = {}
        usd = round(sum(g["usd"]), 2) if g["usd"] else None
        if usd is None:
            nulls["founder_cli_usd"] = "no row of this version carries cost_usd"
        per = round(sum(g["usd"]) / g["accepted"], 2) if usd is not None and g["accepted"] else None
        if per is None:
            nulls["founder_cli_usd_per_accepted"] = "no accepted verdict" if not g["accepted"] else "no cost recorded"
        minutes = round(statistics.median(g["minutes"]), 1) if g["minutes"] else None
        if minutes is None:
            nulls["median_session_minutes"] = "no row of this version carries minutes"
        models.append({"model": model, "effort": effort, "first_session": g["rows"][0], "last_session": g["rows"][-1],
                       "sessions": len(g["rows"]), "pushes": g["pushes"],
                       "verdicts": dict(g["verdicts"]), "verdicts_from_next_session": dict(g["late"]),
                       "pushes_without_verdict": g["unjudged"], "outages": g["outages"],
                       "rejected_rows_by_reason": dict(g["reasons"]),
                       "accepted": g["accepted"], "founder_cli_usd": usd, "usd_label": USD_LABEL,
                       "sessions_with_usd": len(g["usd"]), "sessions_without_usd": g["no_usd"],
                       "founder_cli_usd_per_accepted": per, "median_session_minutes": minutes, "null_reasons": nulls})
    models.sort(key=lambda m: (m["last_session"], m["model"], m["effort"]), reverse=True)
    window = f"{rows[0]['stamp']}..{rows[-1]['stamp']}" if rows else None
    return {"window": window, "models": models[:MODELS_MAX], "left_out": max(0, len(models) - MODELS_MAX)}


# ---- live attempts -----------------------------------------------------------------------------------------------
def red_jobs(one: dict) -> list[dict]:
    out = []
    for job in one["jobs"]:
        if job.get("conclusion") not in RED:
            continue
        summary = job.get("summary") if isinstance(job.get("summary"), dict) else {}
        steps = summary.get("steps") if isinstance(summary.get("steps"), list) else []
        lines = job.get("output") if isinstance(job.get("output"), list) else []
        out.append({"job": word(job.get("name")), "conclusion": job.get("conclusion"),
                    "steps": [s for s in map(word, steps[:8]) if s], "reason": word(summary.get("reason")),
                    "summary_why": word(job.get("summary_why")),
                    "output": [str(line)[:TEXT_MAX] for line in lines[:OUTPUT_LINES]]})
    return out


def red_class(job: dict) -> str:
    """job:reason, the reason being the summary's own, else the first output line's lead before a colon."""
    reason = job["reason"]
    if reason is None and job["output"]:
        lead = re.sub(r"\s+", "_", job["output"][0].split(":", 1)[0].strip())
        reason = re.sub(r"[^A-Za-z0-9_.-]", "", lead)[:60] or None
    return f"{job['job'] or 'unknown'}:{reason or job['summary_why'] or job['conclusion']}"


def run_fact(rid: int, one: dict) -> dict:
    run = one["run"]
    reds = red_jobs(one)
    return {"id": rid, "created_at": run.get("created_at") if iso_time(run.get("created_at")) else None,
            "status": word(run.get("status")), "conclusion": word(run.get("conclusion")),
            "red": run.get("conclusion") in RED or bool(reds), "red_jobs": reds}


def transfer_of(one: dict) -> str | None:
    for job in one["jobs"]:
        summary = job.get("summary") if job.get("name") == "cek" and isinstance(job.get("summary"), dict) else {}
        accepted = summary.get("accepted") if isinstance(summary.get("accepted"), dict) else {}
        sha = accepted.get("transfer_sha")
        if isinstance(sha, str) and SHA_RE.fullmatch(sha):
            return sha
    return None


def unread(referee: dict | None) -> str | None:
    """Why this cycle's referee tarball gives nothing (never downloaded, or `referee_facts` failed); None when read."""
    if not referee or referee.get("error"):
        return "the referee tarball was not read this cycle" + (f": {referee['error']}" if referee else "")
    return None


def operator_records(referee: dict | None) -> tuple[list | None, list | None, dict]:
    """(reverted_exits, import rows, null reasons) from the referee tarball's control.json and setup/imports.jsonl."""
    why = unread(referee)
    if why:
        return None, None, {"reverted_exits": why, "imports": why}
    nulls, reverted, imports = {}, None, None
    try:
        control = json.loads(referee.get("control") or b"")
        listed = control.get("reverted_exits", []) if isinstance(control, dict) else None
        reverted = list(dict.fromkeys(s for s in listed if isinstance(s, str) and SHA_RE.fullmatch(s))) \
            if isinstance(listed, list) else None
        if reverted is None:
            nulls["reverted_exits"] = "control.json reverted_exits is not a list"
    except ValueError:
        nulls["reverted_exits"] = "control.json is missing or not JSON"
    if referee.get("imports") is None:
        nulls["imports"] = "setup/imports.jsonl is missing"
    else:
        imports = []
        for line in referee["imports"].decode("utf-8", "replace").splitlines():
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if isinstance(row, dict) and isinstance(row.get("brain_sha"), str) and SHA_RE.fullmatch(row["brain_sha"]):
                imports.append({"brain_sha": row["brain_sha"], "ts": row.get("ts") if iso_time(row.get("ts")) else None,
                                "stage": row.get("stage") if isinstance(row.get("stage"), int) else None,
                                "batch": word(row.get("batch"))})
    return reverted, imports, nulls


def live_attempts(referee: dict | None, runs: dict[int, dict]) -> dict:
    reverted, imports, nulls = operator_records(referee)
    by_transfer: dict[str | None, list] = {}
    for rid in sorted(runs, key=lambda r: (str(runs[r]["run"].get("created_at")), r)):
        by_transfer.setdefault(transfer_of(runs[rid]), []).append(run_fact(rid, runs[rid]))
    rows = {i["brain_sha"]: i for i in imports or []}
    order = list(dict.fromkeys([*(reverted or []), *rows, *(s for s in by_transfer if s)]))
    transfers = []
    for sha in order:
        facts = by_transfer.get(sha, [])
        reds = [f for f in facts if f["red"]]
        transfers.append({
            "brain_sha": sha, "reverted": None if reverted is None else sha in reverted,
            "import_row": {k: rows[sha][k] for k in ("ts", "stage")} if sha in rows else None,
            "runs_seen": len(facts), "conclusions": dict(Counter(f["conclusion"] or "none" for f in facts)),
            "outcome": "red" if reds else ("no_red_in_runs_seen" if facts else "no_run_seen"),
            "first_red": reds[0] if reds else None,
            "runs": [{k: f[k] for k in ("id", "created_at", "conclusion", "red")} for f in facts[:RUNS_MAX]],
            "runs_left_out": max(0, len(facts) - RUNS_MAX)})
    loose = by_transfer.get(None, [])
    return {"window": "every run a session folder recorded", "unattributed_red_runs": sum(f["red"] for f in loose),
            "transfers": transfers[-TRANSFERS_MAX:],
            "transfers_left_out": max(0, len(transfers) - TRANSFERS_MAX),
            "unattributed_runs": loose[-UNATTRIBUTED_MAX:], "unattributed_left_out": max(0, len(loose) - UNATTRIBUTED_MAX),
            "null_reasons": nulls}


# ---- repeats -----------------------------------------------------------------------------------------------------
def repeats(rows: list[dict], runs: dict[int, dict], at: datetime) -> dict:
    since = at - timedelta(days=WINDOW_DAYS)
    seen: dict[tuple[str, str], list[str]] = {}
    for row in rows:
        day = stamp_time(row["stamp"])
        if day >= since and word(row.get("verdict")) in REJECTED and not outage(row):
            for kind in reason_kinds(row):
                seen.setdefault(("rejection", kind), []).append(row["stamp"][:8])
    for rid, one in runs.items():
        created = iso_time(one["run"].get("created_at"))
        if created is not None and created >= since:
            for name in sorted({red_class(job) for job in red_jobs(one)}):  # a run once per class
                seen.setdefault(("red", name), []).append(created.strftime("%Y%m%d"))
    found = [{"kind": kind, "class": name, "count": len(days), "first": min(days), "last": max(days),
              "dates": sorted(set(days))[-DATES_MAX:]} for (kind, name), days in seen.items() if len(days) > 1]
    found.sort(key=lambda f: (f["kind"], f["class"]))  # a fixed order, never a ranking
    return {"window": f"{since.strftime('%Y%m%dT%H%M%SZ')}..{at.strftime('%Y%m%dT%H%M%SZ')}",
            "repeats": found[:REPEATS_MAX], "left_out": max(0, len(found) - REPEATS_MAX)}


# ---- size --------------------------------------------------------------------------------------------------------
def referee_facts(blob: bytes, reserved) -> dict:
    """What the mirror reads of a referee repository tarball (`gh api .../tarball/main`), in memory: control.json and
    setup/imports.jsonl as bytes, and the size of the referee/ tree, every top folder but ``reserved`` (the operator's
    names and bootstrap/) and dot folders. Nothing is unpacked to disk and nothing is run."""
    folded = {name.casefold() for name in reserved}
    out = {"control": None, "imports": None}
    tree = Counter()
    off = None
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r:*") as tar:
        for member in tar:
            parts = member.name.split("/", 1)  # GitHub's one top folder, then the repository's path
            rel = parts[1] if len(parts) == 2 else ""
            top = rel.split("/", 1)[0]
            operator = rel in (CONTROL, IMPORTS)
            tree_file = not (top.casefold() in folded or top.startswith(".")) and (
                rel.endswith(".py") or rel == OFF_LIVE or rel.startswith(MUTANTS_DIR) and rel.endswith(".json"))
            if not member.isfile() or not (operator or tree_file):
                continue
            if member.size > FILE_MAX:
                tree["files_too_large"] += 1
                continue
            data = tar.extractfile(member).read()
            if rel == CONTROL:
                out["control"] = data
            elif rel == IMPORTS:
                out["imports"] = data
            elif rel.endswith(".py"):
                part = "tests" if rel.startswith("tests/") else "code"
                tree[f"py_files_{part}"] += 1
                tree[f"py_lines_{part}"] += len(data.splitlines())
                if part == "tests":
                    tree["test_functions"] += len(TEST_RE.findall(data))
            elif rel == OFF_LIVE:
                try:
                    listed = json.loads(data)
                    off = len(listed) if isinstance(listed, dict) else None
                except ValueError:
                    off = None
            else:
                try:
                    mutants = json.loads(data).get("mutants")
                    tree["mutants"] += len(mutants) if isinstance(mutants, list) else 0
                    tree["mutant_files"] += 1
                except (ValueError, AttributeError):
                    tree["mutant_files_unreadable"] += 1
    keys = ("py_files_code", "py_lines_code", "py_files_tests", "py_lines_tests", "test_functions", "mutant_files",
            "mutants", "mutant_files_unreadable", "files_too_large")
    out["tree"] = dict({k: tree[k] for k in keys}, off_live_modules=off)
    return out


def size(referee: dict | None, spec: Path) -> dict:
    nulls = {"fan_in_top": "not available in this launcher's inputs",
             "ci_duration_s": "not available in this launcher's inputs"}
    tree = None
    transfer = None
    if unread(referee):
        nulls["referee_tree"] = unread(referee)
    else:
        tree = referee.get("tree")
        _, imports, _ = operator_records(referee)
        transfer = imports[-1]["brain_sha"] if imports else None
        if tree and tree.get("off_live_modules") is None:
            nulls["off_live_modules"] = "status/off_live.json is missing or not a JSON object"
    pages = None
    if spec.is_dir():
        found = sorted(p.relative_to(spec).as_posix() for p in spec.rglob("*.md") if p.is_file())
        pages = {"total": len(found), "by_folder": dict(Counter(p.split("/")[0] if "/" in p else "." for p in found))}
    else:
        nulls["spec_pages"] = "the launcher's checkout has no spec/"
    return {"window": "now", "referee_tree": tree, "referee_tree_transfer": transfer, "spec_pages": pages,
            "fan_in_top": None, "ci_duration_s": None, "null_reasons": nulls}


# ---- delegation --------------------------------------------------------------------------------------------------
def price_table(prices) -> dict:
    """The operator's price table (seed/founder/prices.json) as the mirror shows it, or ValueError naming what is not
    in its form: ``{source, as_of, unit, models: {<model>: {<PRICE_KEYS>: whole USD micros per million tokens}}}``."""
    if not isinstance(prices, dict) or prices.get("error"):
        raise ValueError("not read" + (f": {word(prices.get('error')) or 'error'}" if isinstance(prices, dict) else ""))
    models = prices.get("models")
    if not isinstance(models, dict) or not all(
            word(m) == m and isinstance(row, dict) and set(row) == set(PRICE_KEYS)
            and all(isinstance(v, int) and not isinstance(v, bool) and v >= 0 for v in row.values())
            for m, row in models.items()):
        raise ValueError("models is not {<model>: {in, out, cache_read, cache_write_5m, cache_write_1h}} of whole "
                         "non-negative micros")
    if not (isinstance(prices.get("source"), str) and iso_date(prices.get("as_of"))):
        raise ValueError("source or as_of is missing")
    return {"source": prices["source"][:TEXT_MAX], "as_of": prices["as_of"], "unit": "usd_micros_per_million_tokens",
            "models": {m: dict(models[m]) for m in sorted(models)}}


def iso_date(text) -> bool:
    return isinstance(text, str) and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", text) is not None


def message_tokens(usage) -> dict | None:
    """One API message's input-side tokens by kind (``IN_KEYS``), or None when a count or the split of its cache writes
    is not there. Its output_tokens is the count as the stream began (``COST_IS``): not read."""
    if not isinstance(usage, dict):
        return None
    split = usage.get("cache_creation")
    if isinstance(split, dict):
        writes = (count(split.get("ephemeral_5m_input_tokens")), count(split.get("ephemeral_1h_input_tokens")))
    else:  # no split: known only when nothing was written
        writes = (0, 0) if count(usage.get("cache_creation_input_tokens") or 0) == 0 else (None, None)
    tokens = {"in": count(usage.get("input_tokens")), "cache_read": count(usage.get("cache_read_input_tokens") or 0),
              "cache_write_5m": writes[0], "cache_write_1h": writes[1]}
    return None if any(v is None for v in tokens.values()) else tokens


def count(value) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def model_cli(usage) -> dict:
    """The closing result event's modelUsage entry of one model, as the mirror shows it."""
    usage = usage if isinstance(usage, dict) else {}
    cost = number(usage.get("costUSD"))
    return {"in": count(usage.get("inputTokens")), "out": count(usage.get("outputTokens")),
            "cache_read": count(usage.get("cacheReadInputTokens")),
            "cache_write": count(usage.get("cacheCreationInputTokens")),
            "cost_usd_micros": None if cost is None else round(cost * 1_000_000), "cost_basis": word(usage.get("costBasis"))}


def micros(total: int) -> int:
    """Tokens times micros per million tokens, as whole micros (half up)."""
    return (total + 500_000) // 1_000_000


def run_cost(messages: list, out: int | None, prices: dict | None, basis: dict) -> tuple:
    """(cost_usd_micros, cost_floor_usd_micros, not_measured) of a run's messages [(model, tokens)] and its output
    tokens (``COST_IS``)."""
    if not messages:
        return None, None, "no_usage"
    floor = 0
    for model, tokens in messages:
        if tokens is None:
            return None, None, "usage_unreadable"
        row = (prices or {}).get(model)
        if row is None or basis.get(model) in (None, UNKNOWN_BASIS):
            return None, None, f"price_unknown:{model}"
        floor += sum(tokens[k] * row[k] for k in IN_KEYS)
    if out is None:
        return None, micros(floor), "output_tokens_unlogged"
    return micros(floor + out * prices[messages[0][0]]["out"]), micros(floor), None


def session_runs(path: Path, prices: dict | None) -> dict:
    """One transcript's agent calls, Workflow calls and agent runs (``SOURCES["delegation"]``)."""
    models, kinds, flows, used, cli, own = Counter(), Counter(), 0, [], {}, None
    calls: dict[str, dict] = {}  # tool_use_id -> the call, in the order the calls were made
    said: dict[tuple, tuple] = {}  # (parent, message id) -> (model, tokens): each API message once
    ended: dict[str, dict] = {}  # tool_use_id -> its task_notification
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            compact = line.replace(" ", "")
            if not any(k in compact for k in ('"tool_use"', '"type":"result"', '"parent_tool_use_id":"',
                                              '"task_notification"', '"subtype":"init"', '"tool_use_result"')):
                continue
            try:
                event = json.loads(line)
            except (ValueError, RecursionError):
                continue
            if not isinstance(event, dict):
                continue
            if event.get("type") == "system" and event.get("subtype") == "init" and own is None:
                own = word(event.get("model"))
            if event.get("type") == "result" and isinstance(event.get("modelUsage"), dict):
                used = sorted(m for m in map(word, event["modelUsage"]) if m)
                cli = {m: model_cli(u) for m, u in event["modelUsage"].items() if word(m)}
            if event.get("type") == "system" and event.get("subtype") == "task_notification" \
                    and isinstance(event.get("tool_use_id"), str):
                ended[event["tool_use_id"]] = event
            result = event.get("tool_use_result") if event.get("type") == "user" else None
            if isinstance(result, dict) and isinstance(result.get("usage"), dict):  # a foreground run's last message
                for item in (event.get("message") or {}).get("content") or []:
                    if isinstance(item, dict) and isinstance(item.get("tool_use_id"), str):
                        said[(item["tool_use_id"], None)] = (word(result.get("resolvedModel")) or "unrecorded",
                                                             message_tokens(result["usage"]))
            parent = event.get("parent_tool_use_id") if isinstance(event.get("parent_tool_use_id"), str) else None
            message = event.get("message") if event.get("type") == "assistant" and isinstance(event.get("message"),
                                                                                                 dict) else {}
            if parent is not None and message:
                key = (parent, message.get("id") if isinstance(message.get("id"), str) else event.get("uuid"))
                said[key] = (word(message.get("model")) or "unrecorded", message_tokens(message.get("usage")))
            content = message.get("content")
            for item in content if isinstance(content, list) else []:
                if not isinstance(item, dict) or item.get("type") != "tool_use":
                    continue
                given = item.get("input") if isinstance(item.get("input"), dict) else {}
                if item.get("name") in AGENT_TOOLS:
                    models[word(given.get("model")) or "inherit"] += 1
                    kinds[word(given.get("subagent_type")) or "default"] += 1
                    if isinstance(item.get("id"), str):
                        calls.setdefault(item["id"], {"subagent_type": word(given.get("subagent_type")),
                                                      "effort": word(given.get("effort")), "parent": parent})
                elif item.get("name") == "Workflow":
                    flows += 1
    basis = {m: fact["cost_basis"] for m, fact in cli.items()}
    table = (prices or {}).get("models")
    runs_of = {use_id: [said[key] for key in said if key[0] == use_id] for use_id in calls}
    served = {use_id: sorted({model for model, _t in messages}) for use_id, messages in runs_of.items()}
    alone = Counter(names[0] for names in served.values() if len(names) == 1)  # runs per served model
    runs = []
    for use_id, call in calls.items():
        messages, names = runs_of[use_id], served[use_id]
        sole = len(names) == 1 and alone[names[0]] == 1 and names[0] != own
        out = (cli.get(names[0]) or {}).get("out") if sole else None
        tokens = None
        if messages and all(t is not None for _m, t in messages):
            tokens = dict({k: sum(t[k] for _m, t in messages) for k in IN_KEYS}, out=out)
        cost, floor, why = run_cost(messages, out, table, basis)
        note = ended.get(use_id) or {}
        wall = count(note["usage"].get("duration_ms")) if isinstance(note.get("usage"), dict) else None
        runs.append({"tool_use_id": word(use_id), "subagent_type": call["subagent_type"],
                     "model": "+".join(names) or None, "effort": call["effort"], "parent": word(call["parent"]),
                     "status": word(note.get("status")) or "unfinished", "wall_ms": wall, "tokens": tokens,
                     "out_from": "cli_model_line" if out is not None else None, "cost_usd_micros": cost,
                     "cost_floor_usd_micros": floor, "cost_basis": None if floor is None else "derived:price_table",
                     "not_measured": why})
    return {"agent_calls": sum(models.values()), "agent_models": dict(models), "agent_types": dict(kinds),
            "workflow_calls": flows, "models_used": used, "session_model": own,
            "models_cli": {m: cli[m] for m in sorted(cli)}, "runs": runs[:RUNS_MAX],
            "runs_left_out": max(0, len(runs) - RUNS_MAX)}


def delegation(logs: Path, stamps: list[str], prices=None) -> dict:
    nulls = {}
    try:
        table = price_table(prices)
    except ValueError as exc:
        table = None
        nulls["prices"] = f"seed/founder/prices.json: {exc}"
    sessions = []
    for stamp in stamps:
        path = logs / stamp / f"session-{stamp}.jsonl"
        if not path.is_file() or path.stat().st_size > TRANSCRIPT_MAX:
            sessions.append({"stamp": stamp, "agent_calls": None,
                             "reason": "no transcript" if not path.is_file() else "transcript too large"})
            continue
        sessions.append(dict({"stamp": stamp}, **session_runs(path, table)))
    read = [s for s in sessions if s["agent_calls"] is not None]
    return {"window": f"the newest {SESSIONS_MAX} session folders before this one", "sessions": sessions,
            "sessions_read": len(read), "sessions_with_agent_calls": sum(1 for s in read if s["agent_calls"]),
            "agent_calls": sum(s["agent_calls"] for s in read), "prices": table, "cost_is": COST_IS,
            "exactness": EXACTNESS, "null_reasons": nulls}


# ---- waiting -----------------------------------------------------------------------------------------------------
def waiting(rows: list[dict], launched: list[str], at: datetime) -> dict:
    sessions = []
    for i, row in enumerate(rows):
        if i < len(rows) - SESSIONS_MAX:
            continue
        began = stamp_time(row["stamp"])
        following = stamp_time(rows[i + 1]["stamp"]) if i + 1 < len(rows) else at
        minutes = number(row.get("minutes"))
        fact = {"stamp": row["stamp"], "minutes": minutes, "end": word(row.get("end")),
                "pushed": row.get("pushed") is True, "gap_to_next_start_min": None, "launcher_starts_in_gap": None}
        if minutes is None:
            fact["reason"] = "the row carries no minutes"
        else:
            ended = began + timedelta(minutes=minutes)
            fact["gap_to_next_start_min"] = round(max(0.0, (following - ended).total_seconds() / 60), 1)
            fact["launcher_starts_in_gap"] = sum(1 for ts in launched if ended < iso_time(ts) <= following)
        sessions.append(fact)
    gaps = [s for s in sessions if s["gap_to_next_start_min"] is not None]
    return {"window": f"the newest {SESSIONS_MAX} cycle rows before this session", "sessions": sessions,
            "gap_total_min": round(sum(s["gap_to_next_start_min"] for s in gaps), 1),
            "gap_with_launcher_start_min": round(sum(s["gap_to_next_start_min"] for s in gaps
                                                     if s["launcher_starts_in_gap"]), 1)}


# ---- session time and quota (epoch Z) -------------------------------------------------------------------------
def transcript_time(path: Path) -> dict:
    """api_s, blocked_on_own_checks_s and the quota's first and last utilization, from one session's transcript."""
    api_ms, commands, elapsed, quota = None, {}, {}, {bucket: [] for bucket in QUOTA_WINDOWS}
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            compact = line.replace(" ", "")
            if not any(k in compact for k in ('"type":"result"', '"tool_use"', '"type":"tool_progress"',
                                              '"type":"rate_limit_event"')):
                continue
            try:
                event = json.loads(line)
            except (ValueError, RecursionError):
                continue
            if not isinstance(event, dict):
                continue
            kind = event.get("type")
            if kind == "result" and number(event.get("duration_api_ms")) is not None:
                api_ms = max(api_ms or 0.0, number(event["duration_api_ms"]))
            elif kind == "tool_progress" and event.get("tool_name") == "Bash":
                seconds, parent = number(event.get("elapsed_time_seconds")), event.get("parent_tool_use_id")
                if seconds is not None and isinstance(parent, str):
                    elapsed[parent] = max(elapsed.get(parent, 0.0), seconds)
            elif kind == "rate_limit_event":
                info = event.get("rate_limit_info") if isinstance(event.get("rate_limit_info"), dict) else {}
                windows = info.get("unifiedWindows") if isinstance(info.get("unifiedWindows"), dict) else {}
                for bucket in QUOTA_WINDOWS:
                    window = windows.get(bucket) if isinstance(windows.get(bucket), dict) else {}
                    if number(window.get("utilization")) is not None:
                        quota[bucket].append(number(window["utilization"]))
            elif kind == "assistant":
                content = (event.get("message") or {}).get("content")
                for item in content if isinstance(content, list) else []:
                    given = item.get("input") if isinstance(item, dict) and isinstance(item.get("input"), dict) else {}
                    if (isinstance(item, dict) and item.get("type") == "tool_use" and item.get("name") == "Bash"
                            and isinstance(item.get("id"), str) and given.get("run_in_background") is not True):
                        commands[item["id"]] = str(given.get("command") or "")
    blocked = sum(s for i, s in elapsed.items() if i in commands and OWN_CHECKS.search(commands[i]))
    nulls = {}
    if api_ms is None:
        nulls["api_s"] = "no result event with duration_api_ms"
        nulls["blocked_on_own_checks_s"] = "no result event: the transcript does not reach the session's end"
    for bucket, seen in quota.items():
        if not seen:
            nulls[f"quota.{bucket}"] = f"no rate_limit_event with {bucket}.utilization"
    return {"api_s": None if api_ms is None else round(api_ms / 1000),
            "blocked_on_own_checks_s": None if api_ms is None else round(blocked),
            "quota_start": {b: seen[0] if seen else None for b, seen in quota.items()},
            "quota_end": {b: seen[-1] if seen else None for b, seen in quota.items()},
            "null_reasons": nulls}


def session_time(logs: Path, stamps: list[str], rows: list[dict]) -> dict:
    minutes = {r["stamp"]: number(r.get("minutes")) for r in rows}
    sessions = []
    for stamp in stamps:
        fact = {"stamp": stamp, "wall_s": None, "api_s": None, "blocked_on_own_checks_s": None,
                "quota_start": None, "quota_end": None, "null_reasons": {}}
        if minutes.get(stamp) is None:
            fact["null_reasons"]["wall_s"] = "no cycle row of this session carries minutes"
        else:
            fact["wall_s"] = round(minutes[stamp] * 60)
        path = logs / stamp / f"session-{stamp}.jsonl"
        if not path.is_file() or path.stat().st_size > TRANSCRIPT_MAX:
            why = "no transcript" if not path.is_file() else "transcript too large"
            fact["null_reasons"].update({k: why for k in ("api_s", "blocked_on_own_checks_s", "quota_start",
                                                          "quota_end")})
        else:
            read = transcript_time(path)
            fact["null_reasons"].update(read.pop("null_reasons"))
            fact.update(read)
        sessions.append(fact)
    return {"window": f"the newest {SESSIONS_MAX} session folders before this one", "sessions": sessions,
            "own_checks_pattern": OWN_CHECKS.pattern, "blocked_on_own_checks_is": BLOCKED_IS,
            "quota_buckets": list(QUOTA_WINDOWS)}


# ---- the first slice's path (epoch Z, `26h`) --------------------------------------------------------------------
def path(accepted: dict | None, referee: dict | None, stages: Path | None) -> dict:
    nulls = {"organ_merges_copy": "no input of this launcher tells an organ's merge from a ready-made candidate's: the "
                                  "loop's yaz summary names a merge per target without its candidate's organ_ids, "
                                  "and the brain's ledger (its accept and merge rows) is not read here",
             "path_mfs_unrecorded": "Stage 1's own micro-features are in no batch table and no signed record "
                                    "accepts them before Stage 1's exit (26e)"}
    table = json.loads((stages / P1_TABLE).read_text(encoding="utf-8")) if stages else None
    mfs = [f["mf"] for f in table["mfs"]] if table else None
    _, imports, _ = operator_records(referee)
    done = word(accepted.get("sha")) if isinstance(accepted, dict) else None
    left = None
    if mfs is None:
        nulls["path_mfs_left"] = "the seed's P1 table was not given"
    elif imports is None:  # without the transfer rows a later batch's done_mf would read as P1's
        nulls["path_mfs_left"] = unread(referee) or "setup/imports.jsonl is missing"
    elif any(r["batch"] == "P1" for r in imports):
        left = []
    elif not isinstance(accepted, dict) or accepted.get("error") or not isinstance(accepted.get("done_mf"), list):
        nulls["path_mfs_left"] = ("the accepted manifest was not read: "
                                  f"{word((accepted or {}).get('error')) or 'no signed state'}")
    elif not all(isinstance(k, int) and not isinstance(k, bool) and k in mfs for k in accepted["done_mf"]):
        nulls["path_mfs_left"] = "the accepted done_mf is not P1's numbering"
    else:
        left = [f"P1:MF{k}" for k in mfs if k not in accepted["done_mf"]]
    return {"window": "now", "accepted_sha": done if done and SHA_RE.fullmatch(done) else None,
            "path_mfs_left": left, "path_mfs_left_count": None if left is None else len(left),
            "path_mfs_unrecorded": [f"stage1:MF{k}" for k in SLICE_OWN], "organ_merges_copy": None,
            "null_reasons": nulls}
