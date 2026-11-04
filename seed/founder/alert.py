"""The operator's alerts, as issues in a private ops repository (E530; the autonomy plan's alert sender). Stdlib only.

An alert is one open issue per key: the issue's title starts with ``[<key>]`` and carries the label of its class
(``alert:<class>``). A key that already has an open issue opens no other, so a check that repeats while its cause
lasts (the day cap, waited out hour after hour) alerts once; once the operator closes the issue, the next time the
cause comes back is a new alert. Only the classes of `CLASSES` are sent; any other is suppressed.

The operator's own `gh` login sends them (the launcher's, never the Founder's token); the launcher hands the sender
its own `run` (`launch.alert_run`), so its limit holds and a test that stands in for `run` holds the alerts too. A sender without a repository
sends nothing and says so: the caller still writes its line in the pilot log. A dry run (``dry_run=<path>``) appends
what it would send to that JSONL file and reads it back as the open issues; it never calls `gh`. Tests use it, so no
test ever opens a real issue. Every call has a limit, and a failed call is reported, never raised: an alert must not
stop the run it reports on.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

CLASSES = ("halt", "usage-limit", "heartbeat", "budget", "incident")  # the labels the ops repository has
KEY_RE = re.compile(r"[a-z0-9][a-z0-9_.:-]{0,79}\Z")
GH_TIMEOUT_S = 120
ISSUE_URL_RE = re.compile(r"/issues/([0-9]+)\s*\Z")


def label(cls: str) -> str:
    return f"alert:{cls}"


def _run(*argv: str, stdin: bytes | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(argv, input=stdin, capture_output=True, check=False, timeout=GH_TIMEOUT_S)


class Sender:
    def __init__(self, repo: str | None, dry_run: Path | None = None, run=_run) -> None:
        self.repo, self.dry_run, self.run = repo, dry_run, run

    def send(self, cls: str, key: str, title: str, body: str) -> str:
        """Open the alert unless its key has an open issue; what happened, in a few words: ``opened #<n>``,
        ``open #<n>`` (already), ``dry run``, ``no repository``, ``suppressed: ...`` or ``failed: ...``."""
        if cls not in CLASSES:
            return f"suppressed: {cls!r} is not an alert class"
        if not KEY_RE.match(key):
            return f"suppressed: {key!r} is not an alert key"
        if self.dry_run is None and not self.repo:
            return "no repository"
        heading = f"[{key}] {title}"[:250]
        try:
            open_now = self.open_issues(cls)
        except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
            return f"failed: the open alerts could not be listed ({type(exc).__name__}: {str(exc)[:200]})"
        found = [number for number, name in open_now if name.startswith(f"[{key}]")]
        if found:
            return f"open #{min(found)}"
        if self.dry_run is not None:
            row = {"repo": self.repo, "label": label(cls), "title": heading, "body": body}
            with self.dry_run.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            return "dry run"
        try:
            proc = self.run("gh", "issue", "create", "--repo", self.repo, "--label", label(cls), "--title", heading,
                            "--body-file", "-", stdin=body.encode("utf-8"))
        except (OSError, subprocess.SubprocessError) as exc:
            return f"failed: {type(exc).__name__}: {str(exc)[:200]}"
        if proc.returncode != 0:
            return f"failed: gh issue create: {proc.stderr.decode(errors='replace').strip()[-200:]}"
        made = ISSUE_URL_RE.search(proc.stdout.decode(errors="replace"))
        return f"opened #{made.group(1)}" if made else "opened"

    def open_issues(self, cls: str) -> list[tuple[int, str]]:
        """The open alerts of the class: (number, title). A dry run's are the rows it wrote (numbered by line)."""
        if self.dry_run is not None:
            lines = self.dry_run.read_text(encoding="utf-8").splitlines() if self.dry_run.is_file() else []
            rows = [json.loads(line) for line in lines if line.strip()]
            return [(n, row["title"]) for n, row in enumerate(rows, start=1) if row.get("label") == label(cls)]
        proc = self.run("gh", "issue", "list", "--repo", self.repo, "--label", label(cls), "--state", "open",
                        "--limit", "100", "--json", "number,title")
        if proc.returncode != 0:
            raise ValueError(f"gh issue list: {proc.stderr.decode(errors='replace').strip()[-200:]}")
        listed = json.loads(proc.stdout)
        return [(int(item["number"]), str(item["title"])) for item in listed]
