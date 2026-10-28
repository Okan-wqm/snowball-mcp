"""A toy world and simulated brains, to show that the drill judge separates learning from not learning.

The world has four families of work. In the trap family a change breaks a consumer that calls the
renamed field by string, so a fixer that does not look for string references fails; a lesson
born from the first planted break tells it to look. Each simulated brain is the learner with one
defect switched on. The referee side of the simulation runs the drill as `tohum/22a` describes and
writes the drill file the judge reads; the brain never writes the transcript.

The probabilities are assumptions about the world, not measurements of a real brain. They are
chosen so that a lesson that is used has a large effect, as a planted trap family is meant to.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field, replace
from typing import Any

from .judge import canonical, commitment, newcombe_lower

TRAP = "string_reference_consumer"
OTHER = "unrelated_rename"
WRONG = "generated_code_edit"
EASY = "docstring_typo"
HARMFUL = "vendored_copy"
CAUSE = "impact_miss"

DEFAULT_PARAMS = {"k": 20, "min_discordant": 8, "min_broken_without": 14, "alpha": "0.10",
                  "z": "1.2815515655446004", "placebo_z": "2.3263478740408408", "min_arm": 8}
ARMS_PER_LESSON = 60

P_TRAP_WITH_LESSON = 0.9    # trap family, the fixer acts on the lesson (or knows the trap already)
P_TRAP_WITHOUT = 0.1        # trap family, nothing tells the fixer to look for string references
P_WRONG_HARMFUL = 0.1       # wrong lesson applied where its condition makes it harmful
P_PLAIN = 0.8               # any other work
P_EASY = 0.99               # the placebo's family is easier than the trap family even with the
                            # lesson, so ranking by raw hit rate puts the placebo first


@dataclass(frozen=True)
class Traits:
    cause_correct: bool = True        # the revert's cause is classified correctly
    bound: bool = True                # the lesson points at the cause row it was born from
    scoped: bool = True               # the lesson's scope names the family it came from
    injects: bool = True              # the dispatcher gives lessons at all
    leaks: bool = False               # ... also to other families and to the test-writer and oracle
    uses: bool = True                 # the fixer acts on a lesson it is given
    shortcut: bool = False            # the fixer avoids the trap with no lesson (hard-coded family)
    withdraws: bool = True            # a contradicted lesson is narrowed or superseded
    records_withdrawal: bool = True   # ... and that is written to the lesson, not only acted on
    fresh_dispatch: bool = True       # the dispatcher reads the current lesson state, not a snapshot
    ranks_by_difference: bool = True  # credit is the lower bound of the difference, not the raw hit rate
    ranks_by_credit: bool = True      # the ranking follows the credit
    persists: bool = True             # lesson state is written to the ledger, not kept in memory
    complete_ledger: bool = True      # every lesson field is written to the ledger


LEARNER = Traits()
BRAINS: dict[str, Traits] = {
    "learner": LEARNER,
    "wrong_cause": replace(LEARNER, cause_correct=False),
    "unbound_lesson": replace(LEARNER, bound=False),
    "unscoped": replace(LEARNER, scoped=False),
    "no_injection": replace(LEARNER, injects=False),
    "leaky": replace(LEARNER, leaks=True),
    "ignores_lessons": replace(LEARNER, uses=False),
    "shortcut": replace(LEARNER, shortcut=True),
    "stubborn": replace(LEARNER, withdraws=False),
    "unrecorded_withdrawal": replace(LEARNER, records_withdrawal=False),
    "stale_dispatcher": replace(LEARNER, fresh_dispatch=False),
    "raw_rate_ranker": replace(LEARNER, ranks_by_difference=False),
    "rank_ignores_credit": replace(LEARNER, ranks_by_credit=False),
    "amnesic": replace(LEARNER, persists=False),
    "lossy_ledger": replace(LEARNER, complete_ledger=False),
}


def _sha(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


@dataclass
class Brain:
    traits: Traits
    lessons: dict[str, dict[str, Any]] = field(default_factory=dict)
    ledger: list[dict[str, Any]] = field(default_factory=list)
    dispatch_view: dict[str, dict[str, Any]] = field(default_factory=dict)
    private_exclusions: dict[str, set[str]] = field(default_factory=dict)

    def _write(self, lesson: dict[str, Any]) -> None:
        self.lessons[lesson["lesson_id"]] = lesson
        if self.traits.persists:
            row = dict(lesson)
            if not self.traits.complete_ledger:
                row.pop("excluded_conditions")
                row.pop("superseded")
            self.ledger.append(row)

    @classmethod
    def rebuild(cls, traits: Traits, ledger: list[dict[str, Any]]) -> "Brain":
        brain = cls(traits, ledger=[dict(row) for row in ledger])
        for row in ledger:
            brain.lessons[row["lesson_id"]] = {"excluded_conditions": [], "superseded": False, **row}
        brain.dispatch_view = {k: dict(v) for k, v in brain.lessons.items()}
        return brain

    def view(self) -> list[dict[str, Any]]:
        return [self.lessons[k] for k in sorted(self.lessons)]

    def classify(self) -> str:
        return CAUSE if self.traits.cause_correct else "test_failure"

    def learn(self, lesson_id: str, cause_row: str, family: str, claim: str, origin: str) -> dict[str, Any]:
        lesson = {"lesson_id": lesson_id, "claim": claim, "origin": origin,
                  "origin_event": cause_row if self.traits.bound else "template",
                  "scope": {"family": family} if self.traits.scoped else {}, "excluded_conditions": [],
                  "superseded": False}
        self._write(lesson)
        self.dispatch_view[lesson_id] = dict(lesson)
        return lesson

    def inject(self, family: str, role: str, conditions: list[str]) -> list[str]:
        if not self.traits.injects:
            return []
        if role in ("test_writer", "oracle") and not self.traits.leaks:
            return []
        source = self.lessons if self.traits.fresh_dispatch else self.dispatch_view
        out = []
        for lid in sorted(source):
            lesson = source[lid]
            excluded = set(lesson["excluded_conditions"]) | self.private_exclusions.get(lid, set())
            fits = self.traits.leaks or lesson["scope"].get("family") in (None, family)
            if fits and not lesson["superseded"] and not set(conditions) & excluded:
                out.append(lid)
        return out

    def fix_ok(self, rng: random.Random, family: str, conditions: list[str], injected: list[str]) -> tuple[bool, str]:
        used = [lid for lid in injected if self.traits.uses]
        roll = rng.random()
        if family == TRAP:
            p = P_TRAP_WITH_LESSON if (self.traits.shortcut or "L1" in used) else P_TRAP_WITHOUT
            return roll < p, "other"
        if family == WRONG and "Lw" in used and HARMFUL in conditions:
            ok = roll < P_WRONG_HARMFUL
            return ok, "other" if ok else "lesson_contradicted"
        if family == EASY:
            return roll < P_EASY, "other"
        return roll < P_PLAIN, "other"

    def observe(self, lesson_id: str, conditions: list[str], cause: str) -> None:
        if cause != "lesson_contradicted" or not self.traits.withdraws:
            return
        if not self.traits.records_withdrawal:
            self.private_exclusions.setdefault(lesson_id, set()).update(conditions)
            return
        lesson = dict(self.lessons[lesson_id])
        if conditions:
            lesson["excluded_conditions"] = sorted(set(lesson["excluded_conditions"]) | set(conditions))
        else:
            lesson["superseded"] = True
        self._write(lesson)

    def rank(self, arms: list[dict[str, Any]], z: float) -> tuple[list[str], dict[str, str]]:
        def counts(lid: str) -> tuple[int, int, int, int]:
            g = [a["ok"] for a in arms if a["lesson_id"] == lid and a["given"]]
            w = [a["ok"] for a in arms if a["lesson_id"] == lid and not a["given"]]
            return sum(g), len(g), sum(w), len(w)

        ids = sorted({a["lesson_id"] for a in arms})
        if self.traits.ranks_by_difference:
            def score(lid: str) -> float:
                x1, n1, x2, n2 = counts(lid)
                return newcombe_lower(x1, n1, x2, n2, z) if n1 and n2 else float("-inf")
        else:
            def score(lid: str) -> float:
                x1, n1, _, _ = counts(lid)
                return x1 / n1 if n1 else 0.0
        credit = {lid: f"{score(lid):.4f}" for lid in ids}
        if not self.traits.ranks_by_credit:
            return sorted(ids, reverse=True), credit  # newest lesson first, whatever its credit
        return sorted(ids, key=lambda lid: (-score(lid), lid)), credit


def run_drill(traits: Traits, seed: int, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Play the referee: plant, run, record, and reveal. Returns the drill file the judge reads.

    A real referee draws every instance and commits to the whole answer key before the run; here
    the key grows while the run is played and is committed at the end. The judge sees only the
    file, so it cannot tell the two apart; the brain never sees the key in either case.
    """
    params = dict(DEFAULT_PARAMS if params is None else params)
    rng = random.Random(seed)
    key: dict[str, Any] = {"nonce": f"{rng.getrandbits(256):064x}", "family": TRAP, "cause": CAUSE,
                           "instances": {}, "wrong": {"lesson_id": "Lw", "harmful_condition": HARMFUL},
                           "placebo": "Lp"}

    def new(family: str, conditions: list[str] | None = None) -> str:
        iid = f"i{rng.getrandbits(40):010x}"
        key["instances"][iid] = {"family": family, "conditions": conditions or []}
        return iid

    brain = Brain(traits)
    t: dict[str, Any] = {}

    # Birth: the referee plants a bad merge in the trap family; the sentinel turns red and it is reverted.
    birth_id = new(TRAP)
    cause_row = f"r{rng.getrandbits(32):08x}"
    lesson = brain.learn("L1", cause_row, TRAP, "When a field is renamed, search string references too.",
                         "own_outcome")
    t["birth"] = {"instance_id": birth_id, "reverted": True, "cause": brain.classify(), "cause_row": cause_row,
                  "lesson": {k: lesson[k] for k in ("lesson_id", "origin_event", "scope")}}

    # Use: who gets the lesson.
    use = []
    for i in range(6):
        iid = new(TRAP)
        role = ("planner", "fixer")[i % 2]
        use.append({"instance_id": iid, "role": role, "lessons_injected": brain.inject(TRAP, role, [])})
    for _ in range(4):
        iid = new(OTHER)
        use.append({"instance_id": iid, "role": "fixer", "lessons_injected": brain.inject(OTHER, "fixer", [])})
    for role in ("test_writer", "oracle"):
        iid = new(TRAP)
        use.append({"instance_id": iid, "role": role, "lessons_injected": brain.inject(TRAP, role, [])})
    t["use"] = use

    # Effect: each instance twice, with the dispatcher's own choice and with every lesson withheld.
    effect = []
    for _ in range(params["k"]):
        iid = new(TRAP)
        with_ok, _ = brain.fix_ok(rng, TRAP, [], brain.inject(TRAP, "fixer", []))
        without_ok, _ = brain.fix_ok(rng, TRAP, [], [])
        effect.append({"instance_id": iid, "with": with_ok, "without": without_ok})
    t["effect"] = effect

    # Wrong lesson: an imported hypothesis that is harmful under one condition.
    brain.learn("Lw", "imported", WRONG, "Edit generated files through their generator.", "llm_prior")
    wrong = []
    for seq in range(10):
        conditions = [HARMFUL] if seq in (1, 4, 6, 8) else []
        iid = new(WRONG, conditions)
        trap_test = f"t{rng.getrandbits(32):08x}"
        if conditions:
            key["instances"][iid]["trap_test"] = trap_test
        injected = brain.inject(WRONG, "fixer", conditions)
        ok, cause = brain.fix_ok(rng, WRONG, conditions, injected)
        if "Lw" in injected:
            brain.observe("Lw", conditions, cause)
        state = brain.lessons["Lw"]
        failed_test = None if ok else trap_test if cause == "lesson_contradicted" else "unrelated"
        wrong.append({"seq": seq, "instance_id": iid, "injected": "Lw" in injected, "ok": ok,
                      "failed_test": failed_test,
                      "lesson_state": {"superseded": state["superseded"],
                                       "excluded_conditions": list(state["excluded_conditions"])}})
    t["wrong"] = wrong

    # Placebo: a true but irrelevant lesson, withheld at random like any other.
    brain.learn("Lp", "imported", EASY, "Docstrings are written in the imperative mood.", "llm_prior")
    arms = []
    for lesson_id, family in (("L1", TRAP), ("Lp", EASY)):
        for _ in range(ARMS_PER_LESSON):
            iid = new(family)
            withheld = rng.random() < 0.5
            injected = [] if withheld else brain.inject(family, "fixer", [])
            ok, _ = brain.fix_ok(rng, family, [], injected)
            arms.append({"instance_id": iid, "lesson_id": lesson_id, "given": lesson_id in injected, "ok": ok})
    ranking, credit = brain.rank(arms, float(params["z"]))
    t["placebo"] = {"arms": arms, "ranking": ranking, "credit": credit}

    # Persistence: rebuild from the ledger in a fresh process and give the next trap instance a lesson.
    before = brain.view()
    restarted = Brain.rebuild(traits, brain.ledger)
    after_id = new(TRAP)
    injected_before = [brain.lessons[i] for i in brain.inject(TRAP, "fixer", [])]
    injected_after = [restarted.lessons[i] for i in restarted.inject(TRAP, "fixer", [])]
    t["persistence"] = {"instance_id": after_id, "view_sha256_before": _sha(before),
                        "view_sha256_rebuilt": _sha(restarted.view()),
                        "injected_sha256_before": _sha(injected_before) if injected_before else "",
                        "injected_sha256_after_restart": _sha(injected_after) if injected_after else ""}

    return {"schema": "snowball-drill/1", "drill": "lesson", "commitment_sha256": commitment(key),
            "answer_key": key, "transcript": t, "params": params}
