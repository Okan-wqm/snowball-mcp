"""The measurement mirror: `/work/logs/mirror.json` (the owner's decision of 2026-11-19, E647). Stdlib only.

Facts the Founder reads at each session start: what each model version cost and what the referee said of its pushes,
what the live loop's runs did after each transfer, which rejection and red classes came back, how large the transferred
referee is, how often a session handed work to agents, and how long the pilot stood between sessions. Facts only: no
advice, no ranking, no judgement of what could have been seen earlier (no-feeding). Every section names its source and
its window. A metric that cannot be computed is null and its reason is in the section's ``null_reasons``; a section that
fails is ``{"value": null, "reason": ...}`` and the others stand. Every list has a cap and says what it left out. The
same files give the same bytes: no clock is read, the session's stamp is the time. Nothing here reaches the network:
the launcher's own records on disk, and the referee repository's tarball the launcher downloads for /vec anyway.
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
SESSIONS_MAX = 20  # the newest sessions `delegation` and `waiting` read
MODELS_MAX, TRANSFERS_MAX, RUNS_MAX, UNATTRIBUTED_MAX, REPEATS_MAX, DATES_MAX = 10, 30, 10, 10, 20, 10
TEXT_MAX = 200  # characters of a recorded output line
OUTPUT_LINES = 2  # of a red job's recorded output
FILE_MAX = 4 * 1024 * 1024  # bytes of one referee tarball member or session-folder note that is read
TRANSCRIPT_MAX = 64 * 1024 * 1024
USD_LABEL = "cli_estimate"  # the CLI's own total_cost_usd: an estimate, never an invoice
AGENT_TOOLS = ("Agent", "Task")  # the CLI's subagent tool, under both of its names
RED = ("failure", "timed_out", "startup_failure")
REJECTED = ("rejected", "frozen")
INTERVENTION = "intervention"  # a launcher start's metrics row (launch.py)
STAMP_RE = re.compile(r"[0-9]{8}T[0-9]{6}Z")
TIME_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")
SHA_RE = re.compile(r"[0-9a-f]{40}")
WORD_RE = re.compile(r"[A-Za-z0-9_.:@/+\[\]-]{1,80}")  # a model id may carry brackets: claude-x[1m]
CONTROL, IMPORTS = "control.json", "setup/imports.jsonl"  # the operator's files in the referee repository
OFF_LIVE, MUTANTS_DIR = "status/off_live.json", "tests/mutants/"  # the brain's own records in its referee/ tree
TEST_RE = re.compile(rb"(?m)^[ \t]*(?:async[ \t]+)?def[ \t]+test\w*[ \t]*\(")

SOURCES = {
    "per_model": "pilot-metrics.jsonl cycle rows (model_served or model, effort, pushed, kind, verdict, reasons, "
                 "cost_usd, minutes); a push whose row has no verdict takes the verdict the next session's "
                 "previous-session.json recorded (verdicts_from_next_session: kind and reasons unknown). accepted: "
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
                  "result event lists",
    "waiting": "pilot-metrics.jsonl: from a session's end (its stamp plus its minutes) to the next session's start; the "
               "gap holds the referee's verdict wait, outage and usage-limit waits and any time the launcher was not "
               "running (a STOP, a crash); launcher_starts_in_gap counts the intervention rows in it. The launcher "
               "logs no wait by its cause",
}


def mirror(stamp: str, metrics: Path, logs: Path, referee: dict | None, spec: Path) -> dict:
    """The mirror for the session starting at ``stamp``: ValueError for a stamp that is not one. Each section reads
    its own inputs, so a file that cannot be read is the null of the sections that need it."""
    at = stamp_time(stamp)
    sections = {
        "per_model": lambda: per_model(cycles(metrics, stamp), late_verdicts(logs, folders(logs, stamp))),
        "live_attempts": lambda: live_attempts(referee, loop_runs(logs, folders(logs, stamp))),
        "repeats": lambda: repeats(cycles(metrics, stamp), loop_runs(logs, folders(logs, stamp)), at),
        "size": lambda: size(referee, spec),
        "delegation": lambda: delegation(logs, [f for f in folders(logs, stamp) if f < stamp][-SESSIONS_MAX:]),
        "waiting": lambda: waiting(cycles(metrics, stamp), starts(metrics), at),
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


def late_verdicts(logs: Path, folders: list[str]) -> dict[str, str]:
    """stamp -> the verdict a later session's previous-session.json recorded for it (the launcher's E381 look-up)."""
    out = {}
    for folder in folders:
        path = logs / folder / "previous-session.json"
        try:
            note = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None
        except (ValueError, RecursionError):
            continue
        if isinstance(note, dict) and isinstance(note.get("stamp"), str) and word(note.get("verdict")):
            out[note["stamp"]] = note["verdict"]
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


def per_model(rows: list[dict], late: dict[str, str]) -> dict:
    groups: dict[tuple, dict] = {}
    for row in rows:
        key = (word(row.get("model_served")) or word(row.get("model")) or "unrecorded",
               (word(row.get("effort")) or "default") if "effort" in row else "unrecorded")
        g = groups.setdefault(key, {"rows": [], "pushes": 0, "verdicts": Counter(), "late": Counter(), "unjudged": 0,
                                    "reasons": Counter(), "accepted": 0, "usd": [], "no_usd": 0, "minutes": []})
        g["rows"].append(row["stamp"])
        g["pushes"] += row.get("pushed") is True
        verdict = word(row.get("verdict"))
        if verdict:
            g["verdicts"][f"{word(row.get('kind')) or 'unknown'}:{verdict}"] += 1
            if verdict in REJECTED:
                g["reasons"].update(reason_kinds(row))
        elif row.get("pushed") is True:
            verdict = word(late.get(row["stamp"]))
            if verdict:
                g["late"][verdict] += 1
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
                       "pushes_without_verdict": g["unjudged"], "rejected_rows_by_reason": dict(g["reasons"]),
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
                                "stage": row.get("stage") if isinstance(row.get("stage"), int) else None})
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
        if day >= since and word(row.get("verdict")) in REJECTED:
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
def delegation(logs: Path, stamps: list[str]) -> dict:
    sessions = []
    for stamp in stamps:
        path = logs / stamp / f"session-{stamp}.jsonl"
        if not path.is_file() or path.stat().st_size > TRANSCRIPT_MAX:
            sessions.append({"stamp": stamp, "agent_calls": None,
                             "reason": "no transcript" if not path.is_file() else "transcript too large"})
            continue
        models, kinds, calls, flows, used = Counter(), Counter(), 0, 0, []
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                compact = line.replace(" ", "")
                if '"tool_use"' not in compact and '"type":"result"' not in compact:
                    continue
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(event, dict):
                    continue
                if event.get("type") == "result" and isinstance(event.get("modelUsage"), dict):
                    used = sorted(m for m in map(word, event["modelUsage"]) if m)
                content = (event.get("message") or {}).get("content") if event.get("type") == "assistant" else None
                for item in content if isinstance(content, list) else []:
                    if not isinstance(item, dict) or item.get("type") != "tool_use":
                        continue
                    given = item.get("input") if isinstance(item.get("input"), dict) else {}
                    if item.get("name") in AGENT_TOOLS:
                        calls += 1
                        models[word(given.get("model")) or "inherit"] += 1
                        kinds[word(given.get("subagent_type")) or "default"] += 1
                    elif item.get("name") == "Workflow":
                        flows += 1
        sessions.append({"stamp": stamp, "agent_calls": calls, "agent_models": dict(models),
                         "agent_types": dict(kinds), "workflow_calls": flows, "models_used": used})
    read = [s for s in sessions if s["agent_calls"] is not None]
    return {"window": f"the newest {SESSIONS_MAX} session folders before this one", "sessions": sessions,
            "sessions_read": len(read), "sessions_with_agent_calls": sum(1 for s in read if s["agent_calls"]),
            "agent_calls": sum(s["agent_calls"] for s in read)}


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
