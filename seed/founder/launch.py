"""Run the Founder pilot on the operator's machine (register E32, E90, E91). Stdlib only.

One cycle:
  1. download the referee's last signed result (`bootstrap-state` artifact of the referee's main branch);
  2. run one Founder session in the capsule (seed/founder/Dockerfile);
  3. if the brain moved, dispatch the referee (its schedule does not fire, E32) and wait for it;
  4. append what happened to <work>/pilot-log.md.

Everything lives in one folder, <work> (the operator deletes it to remove the pilot):
  <work>/snowball-founder.env   the Founder's two secrets; written by the operator, never read by this script
  <work>/aquaculture_platform   the target clone, mounted read-only
  <work>/referee/               the last referee result the Founder reads
  <work>/logs/                  session transcripts
  <work>/pilot-log.md           the operator's report
  <work>/STOP                   create this file to stop after the current step

The operator's own `gh` login dispatches the referee and reads results; it never enters the capsule.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEED = HERE.parent
sys.path.insert(0, str(SEED / "bootstrap"))
from snowball_bootstrap.decide import counts_against_founder  # noqa: E402  (the referee's rule, not a copy)
IMAGE = "snowball-founder:pilot"
REFEREE_WORKFLOW = "bootstrap.yml"
STATE_ARTIFACT = "bootstrap-state"
MAX_REFEREE_RETRIES = 2  # with the first run, as many as the referee's own retries (decide.RIVAL_SIDE_WARN)
BUILD_FILES = ("founder/Dockerfile", "founder/entrypoint.sh", "founder/prompt.md",
               "bootstrap/requirements/claude-cli/package.json", "bootstrap/requirements/claude-cli/package-lock.json")


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run(*args: str, check: bool = True, timeout: float | None = None, stdin: bytes | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(args, check=check, timeout=timeout, input=stdin, capture_output=True)


def gh_json(*args: str):
    return json.loads(run("gh", *args).stdout or b"null")


def say(msg: str) -> None:
    print(f"[{now()}] {msg}", flush=True)


def reason_owner(reason: dict) -> str:
    """Whose move a rejection reason asks for, by the referee's own rule (one source of truth): the measure of
    whether every rejection the Founder sees is one it can act on (E166, E167)."""
    item = {"kind": str(reason.get("kind", "")), "ref": str(reason.get("ref") or "")}
    if counts_against_founder(item):
        return "founder"
    return "rival" if item["kind"] in ("rival_unresolved", "rival_missing") else "referee"


def write_build_context(ctx: Path) -> None:
    """Copy exactly the files the image needs, with LF line ends: a Windows checkout may hand over CRLF, and a CR
    after the entrypoint's shebang makes the container fail before it starts (E152)."""
    for rel in BUILD_FILES:
        dest = ctx / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((SEED / rel).read_bytes().replace(b"\r\n", b"\n"))


class Pilot:
    def __init__(self, work: Path, brain: str, referee: str, target: str) -> None:
        self.work, self.brain, self.referee = work, brain, referee
        self.target = work / target
        self.env_file = work / "snowball-founder.env"
        self.result_dir = work / "referee"
        self.logs = work / "logs"
        self.report = work / "pilot-log.md"
        self.metrics = work / "pilot-metrics.jsonl"  # one machine-readable line per cycle (what docs/pilot-gunlugu.md counts)
        self.seed = ""  # the brain commit the referee's setup summary pins; the capsule cuts history there

    # ---- checks -------------------------------------------------------------------------------------------
    def stopped(self) -> bool:
        return (self.work / "STOP").exists()

    def preflight(self) -> None:
        problems = []
        if not self.env_file.is_file() or self.env_file.stat().st_size < 40:
            problems.append(f"{self.env_file} is missing or empty")
        if not self.target.is_dir():
            problems.append(f"target clone {self.target} is missing")
        if run("docker", "info", check=False).returncode != 0:
            problems.append("docker is not running")
        if run("gh", "auth", "status", check=False).returncode != 0:
            problems.append("gh is not logged in")
        else:
            self.seed = self.seed_commit()
            if not re.fullmatch(r"[0-9a-f]{40}", self.seed):
                problems.append(f"{self.referee} setup/summary.json has no seed_commit")
        if problems:
            sys.exit("preflight failed:\n  " + "\n  ".join(problems))
        self.result_dir.mkdir(exist_ok=True)
        self.logs.mkdir(exist_ok=True)

    def seed_commit(self) -> str:
        raw = run("gh", "api", "-H", "Accept: application/vnd.github.raw",
                  f"repos/{self.referee}/contents/setup/summary.json", check=False).stdout
        try:
            return str(json.loads(raw).get("seed_commit", ""))
        except ValueError:
            return ""

    def build(self) -> None:
        """Build from a copy of exactly the files the image needs: a synced folder (iCloud) can hand docker
        placeholders it cannot read, and nothing else of the repository belongs in the capsule."""
        say("building the capsule image")
        with tempfile.TemporaryDirectory(prefix="snowball-founder-") as ctx:
            write_build_context(Path(ctx))
            proc = run("docker", "build", "--quiet", "-t", IMAGE, "-f", str(Path(ctx, "founder/Dockerfile")), ctx,
                       check=False, timeout=3600)
        if proc.returncode != 0:
            sys.exit("image build failed:\n" + proc.stderr.decode(errors="replace")[-4000:])

    # ---- GitHub -------------------------------------------------------------------------------------------
    def brain_head(self) -> str:
        return gh_json("api", f"repos/{self.brain}/commits/main")["sha"]

    def ledger_rows(self, sha: str) -> list[dict]:
        proc = run("gh", "api", "-H", "Accept: application/vnd.github.raw",
                   f"repos/{self.brain}/contents/founder-ledger.jsonl?ref={sha}", check=False)
        rows = []
        for line in proc.stdout.decode(errors="replace").splitlines() if proc.returncode == 0 else []:
            try:
                rows.append(json.loads(line))
            except ValueError:
                rows.append({"kind": "<unreadable line>"})
        return rows

    def fetch_result(self) -> dict | None:
        """The newest bootstrap-state artifact made on the referee's main branch, unpacked into <work>/referee."""
        listing = gh_json("api", f"repos/{self.referee}/actions/artifacts?name={STATE_ARTIFACT}&per_page=30")
        arts = [a for a in listing.get("artifacts", [])
                if not a["expired"] and (a.get("workflow_run") or {}).get("head_branch") == "main"]
        for old in self.result_dir.iterdir():
            old.unlink()
        if not arts:
            return None
        newest = max(arts, key=lambda a: a["created_at"])
        blob = run("gh", "api", f"repos/{self.referee}/actions/artifacts/{newest['id']}/zip").stdout
        with zipfile.ZipFile(io.BytesIO(blob)) as zf:
            for name in zf.namelist():
                if "/" in name or "\\" in name or name.startswith("."):
                    continue
                (self.result_dir / name).write_bytes(zf.read(name))
        path = self.result_dir / "result.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None

    def dispatch_referee(self, timeout_s: int) -> dict:
        """Dispatch the referee on main and wait for that run; returns {id, conclusion, url}."""
        since = datetime.now(timezone.utc)
        run("gh", "workflow", "run", REFEREE_WORKFLOW, "--repo", self.referee, "--ref", "main")
        run_id = None
        for _ in range(30):
            time.sleep(5)
            runs = gh_json("run", "list", "--repo", self.referee, "--workflow", REFEREE_WORKFLOW,
                           "--event", "workflow_dispatch", "--limit", "5", "--json", "databaseId,createdAt")
            fresh = [r for r in runs if datetime.fromisoformat(r["createdAt"].replace("Z", "+00:00")) >= since]
            if fresh:
                run_id = str(min(fresh, key=lambda r: r["createdAt"])["databaseId"])
                break
        if run_id is None:
            return {"id": None, "conclusion": "not_started", "url": ""}
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            view = gh_json("run", "view", run_id, "--repo", self.referee, "--json", "status,conclusion,url")
            if view["status"] == "completed":
                return {"id": run_id, "conclusion": view["conclusion"], "url": view["url"]}
            if self.stopped():
                break
            time.sleep(30)
        return {"id": run_id, "conclusion": "still_running", "url": ""}

    # ---- the session --------------------------------------------------------------------------------------
    def session_logs(self, stamp: str) -> Path:
        return self.logs / stamp

    def capsule_argv(self, stamp: str, model: str, max_turns: int, budget_usd: int) -> list[str]:
        def bind(src: Path, dst: str, ro: bool) -> list[str]:
            return ["--mount", f"type=bind,src={src},dst={dst}" + (",readonly" if ro else "")]

        return ["docker", "run", "--rm", "--name", f"snowball_founder_{stamp.lower()}",
               "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
               "--pids-limit", "1024", "--memory", "8g", "--cpus", "4",
               "--tmpfs", "/tmp:rw,exec,size=2g,mode=1777",
               "--tmpfs", "/home/founder:rw,size=256m,mode=1777",
               "--tmpfs", "/work/brain:rw,exec,size=2g,mode=1777",
               *bind(self.env_file, "/run/secrets/founder.env", True),
               *bind(self.result_dir, "/work/referee", True),
               *bind(self.target, "/work/target", True),
               *bind(self.session_logs(stamp), "/work/logs", False),  # its own folder: memory is the ledger (E155)
               "-e", f"BRAIN_REPO={self.brain}", "-e", f"BRAIN_SEED={self.seed}", "-e", f"SESSION_STAMP={stamp}",
               "-e", f"FOUNDER_MODEL={model}", "-e", f"FOUNDER_MAX_TURNS={max_turns}",
               "-e", f"FOUNDER_MAX_BUDGET_USD={budget_usd}",
               IMAGE]

    def session(self, stamp: str, model: str, max_turns: int, budget_usd: int, timeout_s: int) -> dict:
        self.session_logs(stamp).mkdir(parents=True, exist_ok=True)
        cmd = self.capsule_argv(stamp, model, max_turns, budget_usd)
        started = time.monotonic()
        err = ""
        try:
            proc = run(*cmd, check=False, timeout=timeout_s)
            exit_code, tail = proc.returncode, proc.stdout.decode(errors="replace").strip().splitlines()[-1:]
            err = proc.stderr.decode(errors="replace").strip()[-600:]  # docker's own complaint; the CLI's goes to logs/
        except subprocess.TimeoutExpired:
            run("docker", "stop", f"snowball_founder_{stamp.lower()}", check=False)  # the container this script started
            exit_code, tail = -1, ["session timed out"]
        out = {"exit": exit_code, "minutes": round((time.monotonic() - started) / 60, 1), "line": tail[0] if tail else "",
               "stderr": err}
        out.update(self.transcript_summary(self.session_logs(stamp) / f"session-{stamp}.jsonl"))
        return out

    @staticmethod
    def transcript_summary(path: Path) -> dict:
        """The CLI's closing `result` event: turns, cost, whether it ended in an error."""
        if not path.is_file():
            return {"transcript": "missing"}
        last = None
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if '"type":"result"' in line.replace(" ", ""):
                try:
                    last = json.loads(line)
                except ValueError:
                    pass
        if last is None:
            return {"transcript": "no result event"}
        return {"turns": last.get("num_turns"), "cost_usd": last.get("total_cost_usd"),
                "subtype": last.get("subtype"), "final": str(last.get("result") or "")[:1500]}

    # ---- the report ---------------------------------------------------------------------------------------
    def write(self, text: str) -> None:
        with self.report.open("a", encoding="utf-8") as fh:
            fh.write(text)

    def record_metrics(self, row: dict) -> None:
        with self.metrics.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    @staticmethod
    def evaluated(verdict: dict | None, head: str) -> bool:
        return bool(verdict) and verdict.get("head") == head and (verdict.get("state") or {}).get("last_evaluated_sha") == head

    def judge(self, n: int, head: str, timeout_s: int) -> tuple[dict, dict | None, int]:
        """Dispatch the referee for head, and again while it leaves head unevaluated (the rival failed on its own
        side, or an outage): the Founder is never asked to fix what was not its fault (E166)."""
        dispatched = self.dispatch_referee(timeout_s)
        verdict, retries = self.fetch_result(), 0
        while (retries < MAX_REFEREE_RETRIES and verdict and verdict.get("head") == head
               and not self.evaluated(verdict, head) and not self.stopped()):
            retries += 1
            say(f"cycle {n}: {head[:7]} was not evaluated ({verdict.get('warnings')}); referee again, retry {retries}")
            dispatched = self.dispatch_referee(timeout_s)
            verdict = self.fetch_result()
        return dispatched, verdict, retries

    def cycle(self, n: int, args) -> bool:
        """One cycle; False when the pilot should stop."""
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        prior = self.fetch_result()
        before = self.brain_head()
        if before != self.seed and not self.evaluated(prior, before) and not self.stopped():
            # A push the referee never judged (the launcher stopped in between, an outage): judge it before the
            # Founder works on, so its next session reads the verdict on its own last push (E168).
            say(f"cycle {n}: {before[:7]} has no verdict yet; referee first")
            _, caught_up, _ = self.judge(n, before, args.referee_timeout)
            prior = caught_up or prior
        rows_before = self.ledger_rows(before)
        say(f"cycle {n}: Founder session {stamp} (brain {before[:7]})")
        sess = self.session(stamp, args.model, args.max_turns, args.budget_usd, args.session_timeout)
        after = self.brain_head()
        rows_after = self.ledger_rows(after)
        new_rows = rows_after[len(rows_before):] if rows_after[:len(rows_before)] == rows_before else rows_after
        verdict = None
        dispatched = None
        retries = 0
        if after != before and not self.stopped():
            say(f"cycle {n}: brain moved to {after[:7]}, dispatching the referee")
            dispatched, verdict, retries = self.judge(n, after, args.referee_timeout)
        kinds: dict[str, int] = {}
        for row in new_rows:
            kinds[str(row.get("kind"))] = kinds.get(str(row.get("kind")), 0) + 1
        lines = [f"\n## Döngü {n} — {stamp}\n",
                 f"- Beyin: `{before[:7]}` → `{after[:7]}`" + (" (push yok)" if after == before else ""),
                 f"- Oturum: çıkış {sess.get('exit')}, {sess.get('minutes')} dk, tur {sess.get('turns')}, "
                 f"maliyet {sess.get('cost_usd')} USD, sonuç {sess.get('subtype', sess.get('transcript'))}",
                 f"- Hakemin önceki kararı (Kurucu'nun okuduğu): {(prior or {}).get('verdict', 'yok')}",
                 f"- Defter: {len(new_rows)} yeni satır " + (json.dumps(kinds, ensure_ascii=False) if kinds else ""),
                 ]
        if sess.get("exit") not in (0, None) and sess.get("stderr"):
            lines.append(f"- Kapsül hatası: `{sess['stderr'].replace('`', chr(39))}`")
        for row in new_rows:
            if row.get("kind") in ("seed_issue", "blocked", "missing_capability"):
                lines.append(f"  - **{row.get('kind')}**: {json.dumps(row, ensure_ascii=False)[:600]}")
        if dispatched is not None:
            lines.append(f"- Hakem koşusu: {dispatched['conclusion']} {dispatched['url']}"
                         + (f" (aynı commit {retries} kez yeniden incelendi)" if retries else ""))
            if verdict:
                lines.append(f"- Hakemin kararı: **{verdict.get('verdict')}**, nedenler {verdict.get('reasons')}")
                if verdict.get("learning"):
                    lines.append(f"- Öğrenme ölçümü: {json.dumps(verdict.get('learning'), ensure_ascii=False)[:600]}")
                if verdict.get("warnings"):
                    lines.append(f"- Uyarılar: {verdict.get('warnings')}")
        if sess.get("final"):
            lines.append("- Kurucu'nun kapanış notu:\n\n  > " + sess["final"].replace("\n", "\n  > "))
        self.write("\n".join(lines) + "\n")
        self.record_metrics({
            "stamp": stamp, "brain_before": before, "brain_after": after, "pushed": after != before,
            "session_exit": sess.get("exit"), "minutes": sess.get("minutes"), "turns": sess.get("turns"),
            "cost_usd": sess.get("cost_usd"), "verdict": (verdict or {}).get("verdict"), "kind": (verdict or {}).get("kind"),
            "reasons": [{"kind": r.get("kind"), "ref": r.get("ref"), "owner": reason_owner(r)}
                        for r in (verdict or {}).get("reasons", [])],
            "warnings": (verdict or {}).get("warnings", []), "referee_retries": retries,
            "rival_attempts": len(((verdict or {}).get("rival") or {}).get("attempts", [])),
            "reproduced": sum(1 for p in (verdict or {}).get("reproducers") or [] if p.get("reproduced") and not p.get("tautological")),
            # The referee's judgement, not the raw re-runs: an open claim's re-run is an observation, never a proof (E260).
            "old_refutations_still_reproducing": sum(1 for r in (verdict or {}).get("reasons") or []
                                                     if r.get("kind") == "refutation_still_reproduces"),
            "ledger_new": kinds,
            "reports_new": [r.get("payload", {}).get("summary", "")[:120] for r in new_rows
                            if r.get("kind") in ("seed_issue", "blocked", "missing_capability")],
        })
        say(f"cycle {n}: done, verdict {(verdict or {}).get('verdict', '-')}")
        self.idle = self.idle + 1 if after == before else 0
        return not (self.stopped() or self.idle >= 2 or sess.get("exit") == -1)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--work", type=Path, default=Path(r"F:\snowball-work"))
    p.add_argument("--brain", default="Okan-wqm/snowball-rehearsal-brain")
    p.add_argument("--referee", default="Okan-wqm/snowball-rehearsal-referee")
    p.add_argument("--target", default="aquaculture_platform")
    p.add_argument("--cycles", type=int, default=1)
    p.add_argument("--model", default="claude-opus-5-5")
    p.add_argument("--max-turns", type=int, default=200)
    p.add_argument("--budget-usd", type=int, default=50, help="runaway brake per session, not a budget")
    p.add_argument("--session-timeout", type=int, default=3 * 3600)
    p.add_argument("--referee-timeout", type=int, default=90 * 60)
    p.add_argument("--no-build", action="store_true")
    args = p.parse_args(argv)
    if shutil.which("gh") is None or shutil.which("docker") is None:
        sys.exit("gh and docker must be on PATH")
    pilot = Pilot(args.work, args.brain, args.referee, args.target)
    pilot.idle = 0
    pilot.preflight()
    if not args.no_build:
        pilot.build()
    if not pilot.report.exists():
        pilot.write("# Snowball pilot günlüğü\n\nHer döngü: Kurucu oturumu → push → hakem → karar.\n")
    for n in range(1, args.cycles + 1):
        if pilot.stopped():
            say("STOP file found; stopping")
            break
        if not pilot.cycle(n, args):
            say("stopping (STOP file, two sessions without a push, or a timed-out session)")
            break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
