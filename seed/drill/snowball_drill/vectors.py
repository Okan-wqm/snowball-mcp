"""Write the drill vectors the bootstrap applies (`tohum/29c`): one drill per simulated brain, plus drills
edited after the run. ``tampered_key`` edits the learner's answer key; ``second_attempt`` writes a key with its
commitment, as a later attempt's referee would; the other edited drills change only the referee's transcript, each
in a way a judge that skips one of its rules would not notice."""

from __future__ import annotations

import copy
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .judge import commitment, judge
from .sim import BRAINS, run_drill

SEED = 7


def _tampered_key(doc: dict[str, Any]) -> None:
    """The answer key changed after the run: every question fails."""
    doc["answer_key"]["cause"] = "test_failure"
    doc["transcript"]["birth"]["cause"] = "test_failure"


def _reused_instances(doc: dict[str, Any]) -> None:
    """The birth names an instance of the placebo's family, and the effect reaches k by recording its first
    k/2 instances twice: birth and effect fail."""
    t = doc["transcript"]
    placebo = doc["answer_key"]["placebo"]
    t["birth"]["instance_id"] = next(a["instance_id"] for a in t["placebo"]["arms"] if a["lesson_id"] == placebo)
    t["effect"] = [dict(pair) for pair in t["effect"][:len(t["effect"]) // 2] for _ in range(2)]


def _missing_evidence(doc: dict[str, Any]) -> None:
    """No use record of another family, so nothing shows the lesson is withheld where it does not belong (use is
    unmeasurable); no view hash, so nothing shows the view was rebuilt (persistence fails); and one effect pair's
    prompt hashes empty, so nothing shows its two runs had the same prompt outside the lesson block (effect fails,
    E321): two empty hashes are equal and show nothing."""
    key, t = doc["answer_key"], doc["transcript"]
    t["use"] = [r for r in t["use"] if key["instances"][r["instance_id"]]["family"] == key["family"]]
    t["persistence"]["view_sha256_before"] = t["persistence"]["view_sha256_rebuilt"] = ""
    for run in t["effect"][0]["run"].values():
        run["prompt_sha256_without_lessons"] = ""


def _reversed_wrong(doc: dict[str, Any]) -> None:
    """The wrong-lesson records in reverse order: "after the contradiction" is by ``seq``, not by file order."""
    doc["transcript"]["wrong"].reverse()


def _second_attempt(doc: dict[str, Any]) -> None:
    """The stage's second attempt (E323), committed in the key, with one pair broken only with the lesson and seven
    only without it: p = 9/256 passes the first attempt's α_1 = 0.05, not the second's α_2 = 0.025 (effect fails). A
    judge holding every attempt at one level, the whole 0.10 or the first attempt's, passes it."""
    key = doc["answer_key"]
    key["attempt"] = 2
    doc["commitment_sha256"] = commitment(key)
    for i, pair in enumerate(doc["transcript"]["effect"]):
        pair["without"], pair["with"] = (True, False) if i < 1 else (False, True) if i < 8 else (False, False)


# name -> (the simulated brain whose drill is edited, the edit)
EDITED: dict[str, tuple[str, Callable[[dict[str, Any]], None]]] = {
    "tampered_key": ("learner", _tampered_key),
    "reused_instances": ("learner", _reused_instances),
    "missing_evidence": ("learner", _missing_evidence),
    "stubborn_reversed": ("stubborn", _reversed_wrong),
    "second_attempt": ("learner", _second_attempt),
}


def drill_docs() -> dict[str, dict[str, Any]]:
    docs = {name: run_drill(traits, SEED) for name, traits in BRAINS.items()}
    for name, (base, edit) in EDITED.items():
        doc = copy.deepcopy(docs[base])
        edit(doc)
        docs[name] = doc
    return docs


def write_vectors(vectors_dir: Path) -> dict[str, Any]:
    out = vectors_dir / "drill"
    out.mkdir(parents=True, exist_ok=True)
    cases = []
    for name, doc in drill_docs().items():
        (out / f"{name}.json").write_text(json.dumps(doc, sort_keys=True, separators=(",", ":")) + "\n", newline="\n",
                                          encoding="utf-8")
        result = judge(doc)
        cases.append({"name": name, "file": f"drill/{name}.json", "drill": result["drill"],
                      "verdicts": result["verdicts"]})
    index = vectors_dir / "vectors.json"
    spec = json.loads(index.read_text(encoding="utf-8"))
    # The group's owner is the Stage 2 batch (`29a`, `29c`); when it runs comes from that batch's stage table.
    spec["drill"] = {"owner": "asama-2", "source": f"seed/drill: python -m snowball_drill vectors (seed {SEED})",
                     "cases": cases}
    index.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8", newline="\n")
    return spec["drill"]
