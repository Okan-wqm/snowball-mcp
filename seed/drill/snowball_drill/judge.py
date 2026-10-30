"""Reference judge of the lesson drill (`tohum/22a`, `tohum/29c`, `tohum/29q`).

A pure function of one drill file: the answer key revealed after the run, the commitment written
before it, the transcript the referee recorded, and the parameters. It never asks the brain
anything. Every family, condition, observable and outcome is read from the answer key or from the
referee's records, never from what the brain says about itself.

The brain never sees a family's name: a lesson's scope speaks the public vocabulary of a job's
observables, and one matcher (``scope_matches``) decides what a scope covers (E64). Who gets a
lesson in the placebo arms is the referee's draw from the committed seed, re-derived here (E65).

Verdicts per question are ``PASS``, ``FAIL`` or ``UNMEASURABLE``. The drill is ``PASS`` only when
every question passes; any ``FAIL`` makes it ``FAIL``; otherwise it is ``UNMEASURABLE`` and the
family is replaced (`tohum/22a`).
"""

from __future__ import annotations

import fnmatch
import hashlib
import hmac
import json
import math
from fractions import Fraction
from typing import Any

QUESTIONS = ("commitment", "birth", "use", "effect", "wrong_lesson", "right_lesson", "placebo", "persistence")
LESSON_ROLES = ("planner", "fixer")
BLIND_ROLES = ("test_writer", "oracle")
SCOPE_FIELDS = ("class_level", "property", "path_glob", "conditions")  # a lesson's scope, all public (`26b`)
RUN_FIELDS = ("model", "effort", "max_turns")  # what both arms of a lesson must share (E65)
PASS, FAIL, UNMEASURABLE = "PASS", "FAIL", "UNMEASURABLE"
CREDIT_TOLERANCE = 0.0001  # reported credit is a four-decimal string


def canonical(value: Any) -> bytes:
    """RFC 8785 for the value types a drill file may hold (ASCII keys, strings, ints, bools)."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def commitment(answer_key: dict[str, Any]) -> str:
    return hashlib.sha256(canonical(answer_key)).hexdigest()


def scope_matches(scope: Any, observables: dict[str, Any]) -> bool:
    """Whether a lesson's scope covers a job, from the job's public observables only (E64).

    Every field the scope sets must hold: ``path_glob`` matches one of the job's paths (``fnmatch``: ``*`` also
    crosses ``/``), ``class_level`` and ``property`` are equal. ``conditions`` names where the lesson is known to
    be wrong; the dispatcher reads it against the job's conditions, so it narrows no coverage here. A field outside
    the vocabulary never matches: a scope cannot lean on what the brain cannot see, such as the answer key's family
    label. An empty scope covers every job, which the birth question refuses as covering other families.
    """
    if not isinstance(scope, dict) or set(scope) - set(SCOPE_FIELDS):
        return False
    if "path_glob" in scope and not any(fnmatch.fnmatchcase(p, str(scope["path_glob"]))
                                        for p in observables.get("paths", [])):
        return False
    return all(scope[f] == observables.get(f) for f in ("class_level", "property") if f in scope)


def withheld(seed_hex: str, instance_id: str) -> bool:
    """The referee's draw for one placebo arm (E65): the lesson is withheld when the lowest bit of the first byte
    of HMAC-SHA256(seed, instance id) is set. The seed is in the answer key, so it is committed before the run."""
    return bool(hmac.new(bytes.fromhex(seed_hex), instance_id.encode("utf-8"), hashlib.sha256).digest()[0] & 1)


def mcnemar_p(b: int, c: int) -> Fraction:
    """Exact one-sided p-value for c or more of b + c discordant pairs favouring the lesson."""
    n = b + c
    return Fraction(sum(math.comb(n, i) for i in range(c, n + 1)), 2 ** n)


def _wilson(x: int, n: int, z: float) -> tuple[float, float]:
    p = x / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return centre - half, centre + half


def newcombe_lower(x1: int, n1: int, x2: int, n2: int, z: float) -> float:
    """Lower bound of p1 - p2 by Newcombe's hybrid score method (`tohum/22`, "Kredi ve sıralama")."""
    p1, p2 = x1 / n1, x2 / n2
    l1, _ = _wilson(x1, n1, z)
    _, u2 = _wilson(x2, n2, z)
    return (p1 - p2) - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)


def _family(key: dict[str, Any], instance_id: str) -> str | None:
    inst = key["instances"].get(instance_id)
    return None if inst is None else inst["family"]


def _conditions(key: dict[str, Any], instance_id: str) -> list[str]:
    inst = key["instances"].get(instance_id)
    return [] if inst is None else list(inst["conditions"])


def _observables(key: dict[str, Any], instance_id: str) -> dict[str, Any]:
    inst = key["instances"].get(instance_id)
    return {} if inst is None else inst["observables"]


def _birth(key: dict[str, Any], t: dict[str, Any], params: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """The scope is judged by what it covers, never by a label (E64): the birth instance, at least
    ``scope_coverage`` of the family's instances in the key, and no instance of another family."""
    b = t["birth"]
    lesson = b["lesson"]
    scope = lesson["scope"]
    family = [i for i, v in key["instances"].items() if v["family"] == key["family"]]
    others = [i for i, v in key["instances"].items() if v["family"] != key["family"]]
    covered = sum(1 for i in family if scope_matches(scope, _observables(key, i)))
    checks = {
        "instance_in_family": _family(key, b["instance_id"]) == key["family"],
        "reverted": b["reverted"] is True,
        "cause_matches_key": b["cause"] == key["cause"],
        "lesson_bound_to_cause_row": lesson["origin_event"] == b["cause_row"],
        "scope_public": isinstance(scope, dict) and not set(scope) - set(SCOPE_FIELDS),
        "scope_covers_birth": scope_matches(scope, _observables(key, b["instance_id"])),
        "scope_covers_family": bool(family) and Fraction(covered, len(family)) >= Fraction(params["scope_coverage"]),
        "scope_excludes_other_families": not any(scope_matches(scope, _observables(key, i)) for i in others),
    }
    return (PASS if all(checks.values()) else FAIL), checks


def _use(key: dict[str, Any], t: dict[str, Any], lesson: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """The dispatcher gives the lesson to every lesson-reading seat whose job its scope covers, and to no other."""
    wrong: list[str] = []
    positives = negatives = 0
    for rec in t["use"]:
        if _family(key, rec["instance_id"]) is None:
            wrong.append(f"{rec['instance_id']}:not_in_key")
            continue
        injected = lesson["lesson_id"] in rec["lessons_injected"]
        if rec["role"] in BLIND_ROLES:
            if rec["lessons_injected"]:
                wrong.append(f"{rec['instance_id']}:{rec['role']}_got_lessons")
            continue
        covered = scope_matches(lesson["scope"], _observables(key, rec["instance_id"]))
        expected = rec["role"] in LESSON_ROLES and covered
        positives += expected
        negatives += not expected
        if injected != expected:
            wrong.append(f"{rec['instance_id']}:{rec['role']}:{'missing' if expected else 'leaked'}")
    detail = {"wrong": wrong[:20], "positives": positives, "negatives": negatives}
    if wrong:
        return FAIL, detail
    return (PASS if positives and negatives else UNMEASURABLE), detail


def _effect(key: dict[str, Any], t: dict[str, Any], params: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    pairs = [p for p in t["effect"] if _family(key, p["instance_id"]) == key["family"]]
    ids = [p["instance_id"] for p in pairs]
    if len(set(ids)) != len(ids):
        return FAIL, {"duplicate_instances": True}
    broken_without = sum(1 for p in pairs if not p["without"])
    b = sum(1 for p in pairs if p["without"] and not p["with"])
    c = sum(1 for p in pairs if p["with"] and not p["without"])
    p_value = mcnemar_p(b, c) if b + c else Fraction(1)
    detail = {"k": len(pairs), "broken_without": broken_without, "b": b, "c": c,
              "p": f"{float(p_value):.6f}"}
    if len(pairs) < params["k"] or broken_without < params["min_broken_without"]:
        # The family does not break a lessonless run often enough for k pairs to show an effect.
        return UNMEASURABLE, detail
    ok = b + c >= params["min_discordant"] and c > b and p_value < Fraction(params["alpha"])
    return (PASS if ok else FAIL), detail


def _wrong_lesson(key: dict[str, Any], t: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    harmful = key["wrong"]["harmful_condition"]
    records = sorted(t["wrong"], key=lambda r: r["seq"])
    # A contradiction is the instance's own trap test going red while the lesson was given; an
    # unrelated failure says nothing about the lesson.
    contradiction = next((r for r in records if harmful in _conditions(key, r["instance_id"])
                          and r["injected"] and r["failed_test"] is not None
                          and r["failed_test"] == key["instances"][r["instance_id"]].get("trap_test")), None)
    if contradiction is None:
        return UNMEASURABLE, {"contradiction": None}
    state = contradiction["lesson_state"]
    withdrawn = state["superseded"] or harmful in state["excluded_conditions"]
    later = [r["instance_id"] for r in records if r["seq"] > contradiction["seq"]
             and harmful in _conditions(key, r["instance_id"]) and r["injected"]]
    later_harmful = sum(1 for r in records if r["seq"] > contradiction["seq"]
                        and harmful in _conditions(key, r["instance_id"]))
    detail = {"contradiction_seq": contradiction["seq"], "withdrawn": withdrawn,
              "injected_after": later[:20], "harmful_after": later_harmful}
    if not later_harmful:
        return UNMEASURABLE, detail
    return (PASS if withdrawn and not later else FAIL), detail


def _right_lesson(key: dict[str, Any], t: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """The positive control (E318): a useful imported lesson stays through a failure that is not its own.

    Every imported (``llm_prior``) lesson in a drill is a planted probe, so a brain that withdraws any of them at
    the first red would pass the wrong-lesson question without telling a wrong lesson from a right one. The
    referee plants a red unrelated test on some instances of the control family; the lesson given there must be
    neither superseded nor narrowed, and must still be given to the family's later instances ("later" by ``seq``).
    """
    family = key["control"]["family"]
    records = sorted((r for r in t["control"] if _family(key, r["instance_id"]) == family), key=lambda r: r["seq"])
    unrelated = next((r for r in records if r["injected"] and r["failed_test"] is not None
                      and r["failed_test"] != key["instances"][r["instance_id"]].get("trap_test")), None)
    if unrelated is None:
        return UNMEASURABLE, {"unrelated_red": None}
    state = unrelated["lesson_state"]
    narrowed = any(c in state["excluded_conditions"] for c in _conditions(key, unrelated["instance_id"]))
    withdrawn = state["superseded"] or narrowed
    later = [r for r in records if r["seq"] > unrelated["seq"]]
    dropped = [r["instance_id"] for r in later if not r["injected"]]
    detail = {"unrelated_seq": unrelated["seq"], "withdrawn": withdrawn, "later": len(later),
              "dropped_after": dropped[:20]}
    if not later:
        return UNMEASURABLE, detail
    return (PASS if not withdrawn and not dropped else FAIL), detail


def _arms(key: dict[str, Any], t: dict[str, Any], lesson_id: str) -> tuple[int, int, int, int]:
    """Successes and sizes of the given and withheld arms, by the referee's draw, not by the transcript."""
    arms = [a for a in t["placebo"]["arms"] if a["lesson_id"] == lesson_id]
    given = [a["ok"] for a in arms if not withheld(key["withhold_seed"], a["instance_id"])]
    held = [a["ok"] for a in arms if withheld(key["withhold_seed"], a["instance_id"])]
    return sum(given), len(given), sum(held), len(held)


def _placebo(key: dict[str, Any], t: dict[str, Any], lesson_id: str,
             params: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Credit is the lower bound of the difference between the given and withheld arms; the
    brain's reported credit must equal the referee's, and its ranking must follow it, not the raw
    hit rate. The placebo's own credit is checked at a stricter level (``placebo_z``): at the live
    level a truly irrelevant lesson clears zero by chance about one drill in ten.

    The arms are the referee's (E65): an arm the dispatcher served against the draw, or arms of one lesson run with
    different settings, make every credit meaningless, and the question fails before any credit is read.
    """
    seed = key["withhold_seed"]
    off_draw = [a["instance_id"] for a in t["placebo"]["arms"]
                if (a["lesson_id"] in a["lessons_injected"]) == withheld(seed, a["instance_id"])]
    if off_draw:
        return FAIL, {"arms_off_the_draw": off_draw[:20]}
    unequal = sorted(lid for lid in {a["lesson_id"] for a in t["placebo"]["arms"]}
                     if len({canonical({f: a["run"].get(f) for f in RUN_FIELDS})
                             for a in t["placebo"]["arms"] if a["lesson_id"] == lid}) != 1)
    if unequal:
        return FAIL, {"unequal_arms": unequal}
    z, strict = float(params["z"]), float(params["placebo_z"])
    bounds = {}
    for lid in (lesson_id, key["placebo"]):
        x1, n1, x2, n2 = _arms(key, t, lid)
        if min(n1, n2) < params["min_arm"]:
            return UNMEASURABLE, {"arm_too_small": lid}
        bounds[lid] = newcombe_lower(x1, n1, x2, n2, z)
    ranking = t["placebo"]["ranking"]
    if lesson_id not in ranking or key["placebo"] not in ranking:
        return FAIL, {"ranking_missing": True}
    placebo_no_credit = newcombe_lower(*_arms(key, t, key["placebo"]), strict) <= 0
    reported = t["placebo"]["credit"]
    credit_matches = all(lid in reported and abs(float(reported[lid]) - bounds[lid]) <= CREDIT_TOLERANCE
                         for lid in bounds)
    expected_first = max(bounds, key=lambda lid: bounds[lid])
    ranked_first = min(bounds, key=ranking.index)
    detail = {"lower_bounds": {k: f"{v:.4f}" for k, v in bounds.items()}, "credit_matches": credit_matches,
              "placebo_no_credit": placebo_no_credit, "expected_first": expected_first,
              "ranked_first": ranked_first}
    ok = placebo_no_credit and credit_matches and ranked_first == expected_first
    return (PASS if ok else FAIL), detail


def _persistence(t: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    p = t["persistence"]
    checks = {
        "view_rebuilt_identical": bool(p["view_sha256_before"]) and
        p["view_sha256_before"] == p["view_sha256_rebuilt"],
        "same_lesson_after_restart": bool(p["injected_sha256_before"]) and
        p["injected_sha256_before"] == p["injected_sha256_after_restart"],
    }
    return (PASS if all(checks.values()) else FAIL), checks


def judge(doc: dict[str, Any]) -> dict[str, Any]:
    key, t, params = doc["answer_key"], doc["transcript"], doc["params"]
    if commitment(key) != doc["commitment_sha256"]:
        return {"verdicts": {q: FAIL for q in QUESTIONS}, "drill": FAIL,
                "details": {"commitment": "answer key does not match the commitment written before the run"}}
    lesson = t["birth"]["lesson"]
    results = {
        "commitment": (PASS, {}),
        "birth": _birth(key, t, params),
        "use": _use(key, t, lesson),
        "effect": _effect(key, t, params),
        "wrong_lesson": _wrong_lesson(key, t),
        "right_lesson": _right_lesson(key, t),
        "placebo": _placebo(key, t, lesson["lesson_id"], params),
        "persistence": _persistence(t),
    }
    verdicts = {q: results[q][0] for q in QUESTIONS}
    values = set(verdicts.values())
    overall = FAIL if FAIL in values else UNMEASURABLE if UNMEASURABLE in values else PASS
    return {"verdicts": verdicts, "drill": overall, "details": {q: results[q][1] for q in QUESTIONS}}
