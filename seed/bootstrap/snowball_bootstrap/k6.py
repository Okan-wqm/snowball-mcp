"""The K6 exam's state and strength (E512): when the physical-safety fence (`tohum/05`) may open, decided by numbers.

K6 goes `not_live` -> `exam_built` -> (a base run on the unmodified copy) -> `exam_strong` -> `live`, and the status is
computed afresh from evidence on every evaluation; nothing is remembered upward. `live` needs `exam_strong` in the same
evaluation. A status that was `live` and is no longer falls back to `not_live`, never to a middle state, and says so
(`fell_from_live`): anything but `live` keeps the fence shut, and the fall-back is what lists the safety commits merged
since for the owner.

`exam_strong` needs, in every family on its own (a weak family is not hidden by a strong one):
- a mutant kill rate of at least 9/10, measured against the reference implementation, not the target's base: a case
  that is red on the base would make "killed" there mean nothing;
- no surviving fail-safe-inversion mutant;
- at least 50 held canaries (plausible bad fixes) and none missed. The one-sided 95 % Clopper-Pearson upper bound on
  the miss rate is computed here, exactly, in whole parts per million rounded up, and kept next to the counts;
and, over the whole exam, fence recall r = m: every path of a held, labelled list of safety paths is classified as one
by the matcher the referee's fence uses.

`live` needs `exam_strong`, the hunter seat running, and a test oracle from a different model than the hunter
(`tohum/03`, the K6 row).

The exam itself (clauses, cases, answers, mutants, canaries, the held path list) is private and never passes through
this repository; this module holds only the mechanism, its authoring format and the validator of that format. Case
ids leave the private side only as HMAC tokens keyed by the epoch's secret salt, so a guessable id pattern names no
case. ``evaluate`` is the private evaluation (integers, strings, booleans and null only, `canon`); the signed field is
``public_field`` of it (E520): the status, the fall from live, the exam's pin, the statement that the exam proves
software logic only, with no field I/O and no hardware in the loop, and the salted hash of the rest. No family, count
or unmet condition is signed: the Founder sees one status, never what the exam is made of.

The authoring format (one JSON document; `EXAM_FORMAT`):
- `required_modes`: every fault mode the exam must answer, each by a clause or by an exclusion with a reason;
- `clauses`: `id`, `family`, `mode`, `kind` (`behaviour`, `physics`, `limit`, `time_budget`), `text` (a general
  requirement, never a case) and `sources` (`kind`, `source`); a `limit` cites a source, a `time_budget` rests on
  owner-supplied site data;
- `exclusions`: `mode`, `family`, `reason`;
- `cases`: `id`, `clause`, `family` (the clause's), `unit`, `input`, `expected`, `visibility` (`visible`, `held`) and
  `evidence`: at least two items from distinct sources (two formulations, a formula and a table, an automaton and a
  standard ...); an equipment case carries a datasheet;
- `mutants`: `id`, `family`, `class` (`fail_safe_inversion`, `ordinary`); a physics mutant carries the output shift
  the admit step measured, which must lie past every tolerance and below a blunt change;
- `canaries`: `id`, `family`, `clauses` (what the bad fix pretends to fix).
The runs document: `exam_sha256` (the pin of the exam they ran), `base` (`commit`, `failed_cases`), `mutants`
(`mutant`, `subject` `ref` or `base`, `failed_cases`), `canaries` (`canary`, `failed_cases`).
"""

from __future__ import annotations

import hashlib
import hmac
import math
from fractions import Fraction
from typing import Any, Callable, Iterable

from . import canon
from .config import HEX64_RE, MODEL_RE, SHA_RE

EXAM_FORMAT = 1
STATUSES = ("not_live", "exam_built", "exam_strong", "live")
FAMILIES = ("P", "S", "A", "X", "E")  # physics; sensor faults; alarm timing; e-stop and hazard table; equipment limits
# Owner decision (e), open: equipment limits rest on datasheets and site data that do not exist yet. A family named
# here may stay empty without blocking K6; once it has a clause it must meet every number like the others.
SITE_DATA_FAMILIES = frozenset({"E"})
CLAUSE_KINDS = ("behaviour", "physics", "limit", "time_budget")
EVIDENCE_KINDS = ("formula", "table", "automaton", "standard", "second_implementation", "property", "datasheet",
                  "site_data")
MUTANT_CLASSES = ("fail_safe_inversion", "ordinary")
VISIBILITIES = ("visible", "held")
KILL_FLOOR = (9, 10)  # killed / total against the reference implementation, per family
MIN_CANARIES = 50  # held canaries per family; 0 missed of 50 bounds the miss rate at 5.8 % (one-sided 95 %)
MISS_ALPHA = (1, 20)  # one-sided 95 % confidence
PPM = 10**6
# A physics mutant moves the output past every tolerance (the widest is 6300 ppm, at S = 40) and no further than 1 %;
# a 1 % change of a Weiss coefficient moves it about 5.6 times over and every case kills it, which flatters the rate.
PHYSICS_SHIFT_PPM = (7000, 10000)
SALINITY_PPT = (0, 40)  # the range over which the two oxygen-solubility anchors were compared
SALT_BYTES = 32
CASE_TAG = b"snowball-k6-case\x00"
SEAL_TAG = b"snowball-k6-evaluation\x00"
# All the signed result holds of K6 (E520, plan D6/D7): the status that opens the fence, whether it fell from live (the
# owner reviews the safety commits merged since), the exam it is of, what it proves, and the salted hash of the whole
# evaluation. Families, counts, the base's red cases and the unmet conditions stay on the private side.
PUBLIC_KEYS = ("status", "fell_from_live", "exam_sha256", "scope", "sealed_sha256")
BOUND_METHOD = "clopper_pearson_one_sided_95"
SCOPE = "software logic only: no field I/O, no hardware in the loop"

_TEXT_KEYS = {"clause": ("mode", "kind", "text"), "exclusion": ("mode", "reason"),
              "case": ("clause", "unit", "visibility"), "mutant": ("class",), "canary": ()}
_KEYS = {
    "clause": ({"id", "family", "mode", "kind", "text", "sources"}, set()),
    "exclusion": ({"mode", "family", "reason"}, set()),
    "case": ({"id", "clause", "family", "unit", "input", "expected", "visibility", "evidence"}, set()),
    "mutant": ({"id", "family", "class"}, {"output_shift_ppm"}),
    "canary": ({"id", "family", "clauses"}, set()),
    "source": ({"kind", "source"}, set()),
}


class K6Error(ValueError):
    """Raised for an argument the caller must never pass (a short salt, a salinity outside the anchors' range)."""


def case_token(salt: bytes, case_id: str) -> str:
    """The id a case shows outside the private side: an HMAC-SHA256 keyed by the epoch's salt (at least 256 bits), so
    an id pattern such as `<family>.<mode>.<n>` cannot be guessed back from logs or the signed result."""
    if not isinstance(salt, bytes) or len(salt) < SALT_BYTES:
        raise K6Error(f"the case salt must be at least {SALT_BYTES} bytes")
    return hmac.new(salt, CASE_TAG + case_id.encode("utf-8"), hashlib.sha256).hexdigest()


def miss_bound_ppm(missed: int, held: int) -> int:
    """The one-sided 95 % Clopper-Pearson upper bound on the miss rate after ``missed`` of ``held`` canaries, in parts
    per million rounded up: the smallest p = m/10^6 with P(X <= missed | held, p) <= 1/20, in exact integers. No
    canary bounds nothing (10^6)."""
    if type(missed) is not int or type(held) is not int or missed < 0 or held < 0:
        raise K6Error("canary counts are whole and not negative")
    if missed >= held:
        return PPM
    num, den = MISS_ALPHA

    def holds(m: int) -> bool:
        tail = sum(math.comb(held, i) * m**i * (PPM - m) ** (held - i) for i in range(missed + 1))
        return den * tail <= num * PPM**held

    lo, hi = 0, PPM
    while lo < hi:
        mid = (lo + hi) // 2
        if holds(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo


def do_saturation_tolerance_ppm(salinity_ppt: int | float | str) -> int:
    """The relative tolerance of an oxygen-solubility case, in ppm rounded up: 0.35 % + 0.007 % per ppt of salinity.
    The two published formulations a case rests on disagree by up to 0.259 % at S = 0, 0.445 % at S = 35 and 0.527 %
    at S = 40, so a tolerance fixed for fresh water rejects correct marine code."""
    try:
        s = None if isinstance(salinity_ppt, bool) else Fraction(str(salinity_ppt))
    except ValueError:
        s = None
    if s is None or not SALINITY_PPT[0] <= s <= SALINITY_PPT[1]:
        raise K6Error(f"salinity {salinity_ppt} ppt is outside the anchors' range {SALINITY_PPT}")
    return math.ceil(3500 + 70 * s)


def do_saturation_within(got: float, expected: float, salinity_ppt: int | float | str) -> bool:
    """Whether ``got`` is within the salinity's tolerance of ``expected``; anything not a finite number is not."""
    tol = do_saturation_tolerance_ppm(salinity_ppt)
    if not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in (got, expected)):
        return False
    if expected <= 0:
        return False
    return abs(Fraction(got) - Fraction(expected)) * PPM <= tol * Fraction(expected)


def _record_problems(kind: str, row: Any, where: str) -> list[str]:
    if not isinstance(row, dict):
        return [f"{where}: not an object"]
    required, optional = _KEYS[kind]
    problems = [f"{where}: missing {key}" for key in sorted(required - set(row))]
    problems += [f"{where}: unknown key {key}" for key in sorted(set(row) - required - optional)]
    return problems


def _ids(rows: list[Any], where: str, problems: list[str]) -> set[str]:
    seen: set[str] = set()
    for i, row in enumerate(rows):
        ident = row.get("id") if isinstance(row, dict) else None
        if not isinstance(ident, str) or not ident:
            problems.append(f"{where}[{i}]: id is not a non-empty string")
        elif ident in seen:
            problems.append(f"{where}[{i}]: duplicate id {ident}")
        else:
            seen.add(ident)
    return seen


def _sources(items: Any, where: str, problems: list[str]) -> list[dict[str, str]]:
    if not isinstance(items, list):
        problems.append(f"{where}: not a list")
        return []
    good = []
    for i, item in enumerate(items):
        found = _record_problems("source", item, f"{where}[{i}]")
        if not found and item["kind"] not in EVIDENCE_KINDS:
            found.append(f"{where}[{i}]: unknown evidence kind {item['kind']!r}")
        if not found and not (isinstance(item["source"], str) and item["source"].strip()):
            found.append(f"{where}[{i}]: the source is empty")
        problems += found
        if not found:
            good.append(item)
    return good


def validate_exam(exam: Any) -> list[str]:
    """Every way ``exam`` breaks the authoring format; empty when it is an exam. Strict: the admit step drops a bad
    case before the exam is pinned, so one bad row here means no exam."""
    if not isinstance(exam, dict):
        return ["the exam is not an object"]
    problems: list[str] = []
    if exam.get("format") != EXAM_FORMAT:
        problems.append(f"format is not {EXAM_FORMAT}")
    sections = ("required_modes", "clauses", "exclusions", "cases", "mutants", "canaries")
    for key in sorted(set(exam) - set(sections) - {"format"}):
        problems.append(f"unknown key {key}")
    for key in sections:
        if not isinstance(exam.get(key), list):
            problems.append(f"{key} is not a list")
    if problems:
        return problems
    modes = exam["required_modes"]
    if not all(isinstance(m, str) and m for m in modes) or len(set(modes)) != len(modes):
        problems.append("required_modes are not distinct non-empty strings")
    for kind, key in (("clause", "clauses"), ("exclusion", "exclusions"), ("case", "cases"), ("mutant", "mutants"),
                      ("canary", "canaries")):
        for i, row in enumerate(exam[key]):
            found = _record_problems(kind, row, f"{key}[{i}]")
            if not found:
                found += [f"{key}[{i}]: {name} is not a string" for name in _TEXT_KEYS[kind]
                          if not isinstance(row[name], str)]
                if not isinstance(row["family"], str) or row["family"] not in FAMILIES:
                    found.append(f"{key}[{i}]: unknown family {row['family']!r}")
            problems += found
    if problems:
        return problems
    clause_ids = _ids(exam["clauses"], "clauses", problems)
    case_ids = _ids(exam["cases"], "cases", problems)
    _ids(exam["mutants"], "mutants", problems)
    _ids(exam["canaries"], "canaries", problems)
    if clause_ids & case_ids:
        problems.append("a case and a clause share an id")
    if problems:
        return problems
    clauses = {c["id"]: c for c in exam["clauses"]}
    answered: dict[str, str] = {}
    for c in exam["clauses"]:
        where = f"clause {c['id']}"
        if c["kind"] not in CLAUSE_KINDS:
            problems.append(f"{where}: unknown kind {c['kind']!r}")
        if not (isinstance(c["text"], str) and c["text"].strip()):
            problems.append(f"{where}: no text")
        sources = _sources(c["sources"], f"{where} sources", problems)
        if c["kind"] == "limit" and not sources:
            problems.append(f"{where}: a limit without a cited source")
        if c["kind"] == "time_budget" and not any(s["kind"] == "site_data" for s in sources):
            problems.append(f"{where}: a time budget without owner-supplied site data")
        answered.setdefault(c["mode"], "clause")
    for e in exam["exclusions"]:
        if not (isinstance(e["reason"], str) and e["reason"].strip()):
            problems.append(f"exclusion of {e['mode']}: no reason")
        if answered.get(e["mode"]):
            problems.append(f"mode {e['mode']} is both answered and excluded")
        answered[e["mode"]] = "exclusion"
    for mode in modes:
        if mode not in answered:
            problems.append(f"mode {mode} has neither a clause nor an exclusion")
    covered: set[str] = set()
    for case in exam["cases"]:
        where = f"case {case['id']}"
        clause = clauses.get(case["clause"])
        if clause is None:
            problems.append(f"{where}: no clause {case['clause']!r} (a case without a clause is discarded)")
            continue
        covered.add(clause["id"])
        if case["family"] != clause["family"]:
            problems.append(f"{where}: family {case['family']} is not its clause's {clause['family']}")
        if case["visibility"] not in VISIBILITIES:
            problems.append(f"{where}: unknown visibility {case['visibility']!r}")
        if not (isinstance(case["unit"], str) and case["unit"]):
            problems.append(f"{where}: no unit")
        evidence = _sources(case["evidence"], f"{where} evidence", problems)
        if len({item["source"].strip() for item in evidence}) < 2:
            problems.append(f"{where}: fewer than two independent evidences")
        if case["family"] == "E" and not any(item["kind"] == "datasheet" for item in evidence):
            problems.append(f"{where}: an equipment case without a datasheet")
    for c in exam["clauses"]:
        if c["id"] not in covered:
            problems.append(f"clause {c['id']}: no case")
    for m in exam["mutants"]:
        where = f"mutant {m['id']}"
        if m["class"] not in MUTANT_CLASSES:
            problems.append(f"{where}: unknown class {m['class']!r}")
        shift = m.get("output_shift_ppm")
        if m["family"] == "P" and not (isinstance(shift, int) and not isinstance(shift, bool)
                                       and PHYSICS_SHIFT_PPM[0] <= shift <= PHYSICS_SHIFT_PPM[1]):
            problems.append(f"{where}: a physics mutant must move the output {PHYSICS_SHIFT_PPM} ppm, not {shift!r}")
    for k in exam["canaries"]:
        named = k["clauses"]
        if not (isinstance(named, list) and named and all(isinstance(c, str) for c in named)):
            problems.append(f"canary {k['id']}: clauses is not a non-empty list of ids")
        elif any(c not in clauses or clauses[c]["family"] != k["family"] for c in named):
            problems.append(f"canary {k['id']}: names a clause that is not one of its family's")
    return problems


def validate_runs(exam: dict[str, Any], runs: Any) -> list[str]:
    """Every way ``runs`` does not fit ``exam`` (an exam that passed `validate_exam`)."""
    if not isinstance(runs, dict) or set(runs) != {"exam_sha256", "base", "mutants", "canaries"}:
        return ["the runs are not an object of exam_sha256, base, mutants and canaries"]
    cases = {c["id"] for c in exam["cases"]}
    problems: list[str] = []

    def failed(row: Any, where: str) -> None:
        listed = row.get("failed_cases") if isinstance(row, dict) else None
        if not isinstance(listed, list) or not all(isinstance(c, str) for c in listed) or not set(listed) <= cases \
                or len(set(listed)) != len(listed):
            problems.append(f"{where}: failed_cases is not a list of distinct case ids")

    if not (isinstance(runs["exam_sha256"], str) and HEX64_RE.match(runs["exam_sha256"])):
        problems.append("exam_sha256: not the pin of the exam the runs ran")
    base = runs["base"]
    if not isinstance(base, dict) or set(base) != {"commit", "failed_cases"} or not isinstance(base["commit"], str) \
            or not SHA_RE.match(base["commit"]):
        problems.append("base: not a commit and its failed cases")
    else:
        failed(base, "base")
    mutants = {m["id"] for m in exam["mutants"]}
    seen = set()
    for i, row in enumerate(runs["mutants"] if isinstance(runs["mutants"], list) else [None]):
        if not isinstance(row, dict) or set(row) != {"mutant", "subject", "failed_cases"} \
                or not isinstance(row["mutant"], str) or row["mutant"] not in mutants \
                or row["subject"] not in ("ref", "base"):
            problems.append(f"mutants[{i}]: not a run of a known mutant on ref or base")
            continue
        if (row["mutant"], row["subject"]) in seen:
            problems.append(f"mutants[{i}]: a second run of {row['mutant']} on {row['subject']}")
        seen.add((row["mutant"], row["subject"]))
        failed(row, f"mutants[{i}]")
    canaries = {k["id"] for k in exam["canaries"]}
    seen = set()
    for i, row in enumerate(runs["canaries"] if isinstance(runs["canaries"], list) else [None]):
        if not isinstance(row, dict) or set(row) != {"canary", "failed_cases"} or not isinstance(row["canary"], str) \
                or row["canary"] not in canaries or row["canary"] in seen:
            problems.append(f"canaries[{i}]: not one run of a known canary")
            continue
        seen.add(row["canary"])
        failed(row, f"canaries[{i}]")
    return problems


def fence_recall(held_paths: Iterable[str], is_safety: Callable[[str], bool]) -> dict[str, int]:
    """How many of the held, labelled safety paths (m) the fence's own matcher classifies as safety paths (r). The
    matcher is the referee's, passed in, so this measures the classifier that gates, not a copy of it."""
    held = sorted(set(held_paths))
    return {"held_paths": len(held), "classified_safety": sum(1 for p in held if is_safety(p))}


def base_vector(exam: dict[str, Any], runs: dict[str, Any], salt: bytes) -> list[list[Any]]:
    """The base run as [token, passed] per case, sorted by token: what the private scorecard keeps of it."""
    red = set(runs["base"]["failed_cases"])
    return sorted([case_token(salt, c["id"]), c["id"] not in red] for c in exam["cases"])


def family_strength(exam: dict[str, Any], runs: dict[str, Any], family: str) -> dict[str, Any]:
    """The strength numbers of one family, from its own cases only."""
    all_cases = {c["id"] for c in exam["cases"]}
    cases = {c["id"] for c in exam["cases"] if c["family"] == family}
    ref_runs = {r["mutant"]: set(r["failed_cases"]) for r in runs["mutants"] if r["subject"] == "ref"}
    mutants = [m for m in exam["mutants"] if m["family"] == family]
    survived = [m for m in mutants if not ref_runs.get(m["id"], set()) & cases]  # unmeasured is not killed
    fsi_total = sum(1 for m in mutants if m["class"] == "fail_safe_inversion")
    fsi_survived = sum(1 for m in survived if m["class"] == "fail_safe_inversion")
    base_red = set(runs["base"]["failed_cases"]) & all_cases
    clause_cases: dict[str, set[str]] = {}
    for c in exam["cases"]:
        clause_cases.setdefault(c["clause"], set()).add(c["id"])
    canary_runs = {r["canary"]: set(r["failed_cases"]) for r in runs["canaries"]}
    canaries = [k for k in exam["canaries"] if k["family"] == family]
    missed = 0
    for k in canaries:
        own = set().union(*(clause_cases.get(c, set()) for c in k["clauses"]))
        # A case red on the base catches a bad fix only when it belongs to what the fix pretends to fix; any other
        # base-red case would "catch" every canary and prove nothing.
        catching = {c for c in canary_runs.get(k["id"], set()) & cases if c not in base_red or c in own}
        if not catching:
            missed += 1
    held = len(canaries)
    return {"cases": len(cases), "mutants_total": len(mutants), "killed": len(mutants) - len(survived),
            "fail_safe_inversion_total": fsi_total, "fail_safe_inversion_survived": fsi_survived,
            "canaries_held": held, "canaries_missed": missed, "miss_bound_ppm": miss_bound_ppm(missed, held)}


def _unmet(family: str, s: dict[str, Any]) -> list[str]:
    unmet = []
    num, den = KILL_FLOOR
    if s["mutants_total"] == 0 or s["killed"] * den < s["mutants_total"] * num:
        unmet.append(f"{family}:kill_rate")
    if s["fail_safe_inversion_survived"] != 0:
        unmet.append(f"{family}:fail_safe_inversion_survived")
    if s["canaries_held"] < MIN_CANARIES:
        unmet.append(f"{family}:canaries_held")
    if s["canaries_missed"] != 0:
        unmet.append(f"{family}:canary_missed")
    return unmet


def _live_ready(ready: Any) -> list[str]:
    if not isinstance(ready, dict) or set(ready) != {"hunter_seat", "hunter_model", "oracle_model"}:
        return ["live:prerequisites_unknown"]
    unmet = []
    if ready["hunter_seat"] is not True:
        unmet.append("live:hunter_seat")
    models = (ready["hunter_model"], ready["oracle_model"])
    if not all(isinstance(m, str) and MODEL_RE.match(m) for m in models):
        unmet.append("live:model_unknown")
    elif models[0].split("-")[1] == models[1].split("-")[1]:
        unmet.append("live:oracle_same_model_as_hunter")  # opus against opus is one model's blind spots twice
    return unmet


def evaluate(exam: Any, runs: Any, *, salt: bytes, exam_sha256: str | None, base_commit: str | None,
             recall: dict[str, int] | None, live_ready: Any, previous: str | None) -> dict[str, Any]:
    """The private K6 evaluation (the signed field is its ``public_field``, E520). ``previous`` is the status of the
    last **signed** result, never one the brain states. Missing or broken evidence keeps the status where the
    evidence that is there puts it, and the reason is named in `unmet`."""
    if previous is not None and previous not in STATUSES:
        raise K6Error(f"previous status {previous!r} is not one of {STATUSES}")
    case_token(salt, "")  # a short salt stops here, before anything is computed
    unmet: list[str] = []
    problems = validate_exam(exam)
    if problems:
        unmet.append("exam_invalid")
    if not (isinstance(exam_sha256, str) and HEX64_RE.match(exam_sha256)):
        unmet.append("exam_unpinned")
    families: dict[str, dict[str, Any]] = {}
    built = not unmet
    if built:
        for family in FAMILIES:
            if family not in SITE_DATA_FAMILIES and not any(c["family"] == family for c in exam["clauses"]):
                unmet.append(f"{family}:no_clause")
        built = not unmet
    field_base: dict[str, Any] = {"base_commit": None, "base_vector_sha256": None, "base_red": None}
    strong = False
    if built:
        run_problems = validate_runs(exam, runs)
        if run_problems:
            unmet.append("runs_invalid")
        elif runs["exam_sha256"] != exam_sha256:
            unmet.append("runs_of_another_exam")  # the runs of last epoch's exam say nothing of this one
        elif not (isinstance(base_commit, str) and runs["base"]["commit"] == base_commit):
            unmet.append("base_run_missing")
        else:
            vector = base_vector(exam, runs, salt)
            field_base = {"base_commit": base_commit, "base_vector_sha256": canon.sha256_hex(canon.canonical(vector)),
                          "base_red": sum(1 for _token, passed in vector if not passed)}
            for family in FAMILIES:
                if family in SITE_DATA_FAMILIES and not any(c["family"] == family for c in exam["clauses"]):
                    continue
                families[family] = family_strength(exam, runs, family)
                unmet += _unmet(family, families[family])
        m = recall.get("held_paths") if isinstance(recall, dict) else None
        r = recall.get("classified_safety") if isinstance(recall, dict) else None
        if not (type(m) is int and type(r) is int and m > 0 and r == m):
            unmet.append("fence_recall")
        strong = not unmet
    live_unmet = _live_ready(live_ready)
    live = strong and not live_unmet
    reached = "live" if live else "exam_strong" if strong else "exam_built" if built else "not_live"
    fell = previous == "live" and reached != "live"
    if strong:
        unmet += live_unmet
    good_recall = isinstance(recall, dict) and all(type(recall.get(k)) is int for k in ("held_paths",
                                                                                         "classified_safety"))
    return {
        "status": "not_live" if fell else reached,
        "fell_from_live": fell,
        "exam_sha256": exam_sha256 if isinstance(exam_sha256, str) and HEX64_RE.match(exam_sha256) else None,
        **field_base,
        "families": families,
        "fence_recall": {k: recall[k] for k in ("held_paths", "classified_safety")} if good_recall else None,
        "unmet": sorted(set(unmet)),
        "bound": BOUND_METHOD,
        "scope": SCOPE,
    }


def public_field(evaluation: dict[str, Any], salt: bytes) -> dict[str, Any]:
    """The signed `k6` field of an evaluation (E520): ``PUBLIC_KEYS`` alone; ``sealed_sha256`` is the HMAC under the
    epoch's salt of the whole evaluation, which the operator recomputes from the private store to open it."""
    case_token(salt, "")  # a short salt stops here
    sealed = hmac.new(salt, SEAL_TAG + canon.canonical(evaluation), hashlib.sha256).hexdigest()
    return {**{key: evaluation[key] for key in PUBLIC_KEYS[:-1]}, "sealed_sha256": sealed}
