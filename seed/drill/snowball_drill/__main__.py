"""``python -m snowball_drill judge <file>`` | ``simulate <brain> <seed>`` | ``power [runs]`` |
``vectors <vectors dir>``."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .judge import judge
from .power import power_table
from .sim import BRAINS, run_drill
from .vectors import write_vectors


def main(argv: list[str]) -> int:
    if argv[:1] == ["judge"] and len(argv) == 2:
        with open(argv[1], encoding="utf-8") as handle:
            print(json.dumps(judge(json.load(handle)), sort_keys=True))
        return 0
    if argv[:1] == ["simulate"] and len(argv) == 3 and argv[1] in BRAINS:
        print(json.dumps(run_drill(BRAINS[argv[1]], int(argv[2])), sort_keys=True))
        return 0
    if argv[:1] == ["power"] and len(argv) <= 2:
        print(json.dumps(power_table(int(argv[1]) if len(argv) == 2 else 500), indent=2, sort_keys=True))
        return 0
    if argv[:1] == ["vectors"] and len(argv) == 2:
        group = write_vectors(Path(argv[1]))
        print(json.dumps({c["name"]: c["drill"] for c in group["cases"]}, indent=2))
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
