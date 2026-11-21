"""Append the operator's restart row to the referee's `setup/imports.jsonl` (`26i` "Yeniden başlatma satırı", `28a`
(h), `26c`; seed-085 h, E687).

    python seed/founder/restart_row.py <referee checkout> --target ID --hard-stop ROW_HASH --stage N [--note TEXT]

The row is ``{ts, stage, touch: "restart", target, hard_stop, note, prev_hash, row_hash}``: ``prev_hash`` is the
counter's last ``row_hash`` (64 zeros for an empty counter), ``row_hash`` the bootstrap referee's own
``canon.row_hash``, and the line is written as the import writes its rows (compact JSON, one LF). The counter is
read and verified first with the referee's own ``stagelock.chained_lines``: a broken counter refuses and nothing is
written, as a hand-written row with a wrong ``row_hash`` would stop every bootstrap run. The row is no transfer
(``stagelock.is_transfer``), so no batch count moves. Nothing is committed or pushed: the operator reviews the line,
commits and pushes it on the referee's ``main`` (a human touch, `27`). Exit 0 written; 2 refused.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "bootstrap"))
from snowball_bootstrap import canon, stagelock  # noqa: E402  (the referee's own chain rules)

COUNTER = Path("setup") / "imports.jsonl"
HEX64 = re.compile(r"[0-9a-f]{64}")
TS = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ")


class Refused(Exception):
    pass


def restart_line(counter: bytes, *, target: str, hard_stop: str, stage: int, note: str, ts: str) -> bytes:
    """The line to append to ``counter`` (the file's bytes), with its LF."""
    if not isinstance(target, str) or not target.strip():
        raise Refused("--target must be a targets[] id")
    if not isinstance(hard_stop, str) or not HEX64.fullmatch(hard_stop):
        raise Refused("--hard-stop must be the row_hash of the freeze/hard_stop row it ends (64 lower-case hex)")
    if type(stage) is not int or stage < 0:
        raise Refused("--stage must be a whole number")
    if not isinstance(ts, str) or not TS.fullmatch(ts):
        raise Refused("ts must be YYYY-MM-DDTHH:MM:SSZ")
    try:
        rows = stagelock.chained_lines(counter, str(COUNTER))
    except stagelock.LockStop as exc:
        raise Refused(f"the counter is broken, nothing written: {exc}") from exc
    row = {"ts": ts, "stage": stage, "touch": "restart", "target": target, "hard_stop": hard_stop, "note": note,
           "prev_hash": rows[-1][1]["row_hash"] if rows else stagelock.ZERO}
    row["row_hash"] = canon.row_hash(row)
    return json.dumps(row, separators=(",", ":")).encode("utf-8") + b"\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    parser.add_argument("referee", help="a checkout of the referee repository")
    parser.add_argument("--target", required=True)
    parser.add_argument("--hard-stop", required=True)
    parser.add_argument("--stage", type=int, required=True)
    parser.add_argument("--note", default="")
    args = parser.parse_args(argv)
    path = Path(args.referee) / COUNTER
    try:
        counter = path.read_bytes() if path.exists() else b""
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        line = restart_line(counter, target=args.target, hard_stop=args.hard_stop, stage=args.stage, note=args.note,
                            ts=ts)
    except (Refused, OSError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab") as fh:
        fh.write(line)
    print(line.decode("utf-8"), end="")
    print(f"appended to {path}; review, commit and push it on the referee's main")
    return 0


if __name__ == "__main__":
    sys.exit(main())
