"""Write the drill vectors the bootstrap applies (`tohum/29c`): one drill per simulated brain, plus
the learner's drill with its answer key edited after the run."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from .judge import judge
from .sim import BRAINS, LEARNER, run_drill

SEED = 7


def drill_docs() -> dict[str, dict[str, Any]]:
    docs = {name: run_drill(traits, SEED) for name, traits in BRAINS.items()}
    tampered = copy.deepcopy(run_drill(LEARNER, SEED))
    tampered["answer_key"]["cause"] = "test_failure"
    tampered["transcript"]["birth"]["cause"] = "test_failure"
    docs["tampered_key"] = tampered
    return docs


def write_vectors(vectors_dir: Path) -> dict[str, Any]:
    out = vectors_dir / "drill"
    out.mkdir(parents=True, exist_ok=True)
    cases = []
    for name, doc in drill_docs().items():
        (out / f"{name}.json").write_text(json.dumps(doc, sort_keys=True, separators=(",", ":")) + "\n",
                                          encoding="utf-8")
        result = judge(doc)
        cases.append({"name": name, "file": f"drill/{name}.json", "drill": result["drill"],
                      "verdicts": result["verdicts"]})
    index = vectors_dir / "vectors.json"
    spec = json.loads(index.read_text(encoding="utf-8"))
    spec["drill"] = {"mf": 18, "source": f"seed/drill: python -m snowball_drill vectors (seed {SEED})",
                     "cases": cases}
    index.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
    return spec["drill"]
