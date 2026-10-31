"""A toy world and simulated brains, to show that the drill judge separates learning from not learning.

The world has five families of work. In the trap family a change breaks a consumer that calls the
renamed field by string, so a fixer that does not look for string references fails; a lesson
born from the first planted break tells it to look. Each simulated brain is the learner with one
defect switched on. The referee side of the simulation runs the drill as `tohum/22a` describes and
writes the drill file the judge reads; the brain never writes the transcript.

A job shows the brain its observables (paths, class level, property), never its family: the family
is the answer key's label (E64). Only the label peeker reads it, and that is its defect. The
referee draws who gets a lesson in the placebo arms from the seed it committed (E65), and records
both runs of every effect pair: their settings and the hash of the prompt without its lesson block (E321).

The probabilities are assumptions about the world, not measurements of a real brain. They are
chosen so that a lesson that is used has a large effect, as a planted trap family is meant to.
"""

from __future__ import annotations

import hashlib
import posixpath
import random
from dataclasses import dataclass, field, replace
from typing import Any

from .judge import canonical, commitment, newcombe_lower, scope_matches, withheld

TRAP = "string_reference_consumer"
OTHER = "unrelated_rename"
WRONG = "generated_code_edit"
EASY = "docstring_typo"
CONTROL = "migration_order"
HARMFUL = "vendored_copy"
SHARED = "shared_fixture"  # a control instance whose red unrelated test lives in a fixture other jobs share
CAUSE = "impact_miss"

# Each family's public observables: the folder of its paths, its class level and its property. The other family
# shares the trap family's property, so a scope that names the property alone covers another family.
OBSERVABLES = {TRAP: ("src/api", "K2", "field_rename"), OTHER: ("src/ui", "K2", "field_rename"),
               WRONG: ("gen", "K1", "generated_code"), EASY: ("docs", "K0", "docstring"),
               CONTROL: ("src/db", "K2", "migration_order")}

DEFAULT_PARAMS = {"k": 30, "min_discordant": 8, "min_broken_without": 21, "alpha": "0.10",
                  "z": "1.2815515655446004", "placebo_z": "2.3263478740408408", "min_arm": 8,
                  "scope_coverage": "0.8"}
ARMS_PER_LESSON = 60
CONTROL_RUNS = 8
UNRELATED_REDS = (0, 3, 5)  # control instances on which the referee plants a red unrelated test (E318)
RUN = {"model": "claude-sonnet-5-5", "effort": "medium", "max_turns": 20,  # one fixer run's settings
       "max_budget_usd": "0.500000"}
TILT = "Check every file twice before you answer."  # text a dispatcher adds outside the lesson block (E321)

P_TRAP_WITH_LESSON = 0.9    # trap family, the fixer acts on the lesson (or knows the trap already)
P_TRAP_WITHOUT = 0.1        # trap family, nothing tells the fixer to look for string references
P_WRONG_HARMFUL = 0.1       # wrong lesson applied where its condition makes it harmful
P_CONTROL_WITH = 1.0        # the control lesson fixes its family's trap: a red while it is given is the planted one
P_CONTROL_WITHOUT = 0.3
P_PLAIN = 0.8               # any other work
P_EASY = 0.99               # the placebo's family is easier than the trap family even with the
                            # lesson, so ranking by raw hit rate puts the placebo first


@dataclass(frozen=True)
class Traits:
    cause_correct: bool = True        # the revert's cause is classified correctly
    bound: bool = True                # the lesson points at the cause row it was born from
    scope: str = "observed"           # the lesson's scope: "observed" (the birth job's folder and property), "none",
                                      # "property" (the property alone) or "label" (the answer key's family label)
    injects: bool = True              # the dispatcher gives lessons at all
    leaks: bool = False               # ... also to other families and to the test-writer and oracle
    uses: bool = True                 # the fixer acts on a lesson it is given
    shortcut: bool = False            # the fixer avoids the trap with no lesson (hard-coded family)
    withdraws: bool = True            # a contradicted lesson is narrowed or superseded
    records_withdrawal: bool = True   # ... and that is written to the lesson, not only acted on
    fresh_dispatch: bool = True       # the dispatcher reads the current lesson state, not a snapshot
    keeps_priors: bool = True         # an imported lesson is withdrawn on its own contradiction, not on any red
    follows_draw: bool = True         # the placebo arms are the referee's draw, not the dispatcher's choice
    equal_arms: bool = True           # both arms of a lesson run with the same model, effort, turns and budget
                                      # (effect and placebo alike)
    equal_effect_arms: bool = True    # both runs of an effect pair have the same prompt outside the lesson block
    ranks_by_difference: bool = True  # credit is the lower bound of the difference, not the raw hit rate
    ranks_by_credit: bool = True      # the ranking follows the credit
    persists: bool = True             # lesson state is written to the ledger, not kept in memory
    complete_ledger: bool = True      # every lesson field is written to the ledger


LEARNER = Traits()
BRAINS: dict[str, Traits] = {
    "learner": LEARNER,
    "wrong_cause": replace(LEARNER, cause_correct=False),
    "unbound_lesson": replace(LEARNER, bound=False),
    "unscoped": replace(LEARNER, scope="none"),
    "label_peeker": replace(LEARNER, scope="label"),
    "overbroad_scope": replace(LEARNER, scope="property"),
    "no_injection": replace(LEARNER, injects=False),
    "leaky": replace(LEARNER, leaks=True),
    "ignores_lessons": replace(LEARNER, uses=False),
    "shortcut": replace(LEARNER, shortcut=True),
    "unequal_effect_arms": replace(LEARNER, equal_effect_arms=False),
    "stubborn": replace(LEARNER, withdraws=False),
    "unrecorded_withdrawal": replace(LEARNER, records_withdrawal=False),
    "stale_dispatcher": replace(LEARNER, fresh_dispatch=False),
    "llm_prior_discarder": replace(LEARNER, keeps_priors=False),
    "cherry_picking_dispatcher": replace(LEARNER, follows_draw=False),
    "unequal_arms": replace(LEARNER, equal_arms=False),
    "raw_rate_ranker": replace(LEARNER, ranks_by_difference=False),
    "rank_ignores_credit": replace(LEARNER, ranks_by_credit=False),
    "amnesic": replace(LEARNER, persists=False),
    "lossy_ledger": replace(LEARNER, complete_ledger=False),
}


def _sha(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def prompt_hash(instance_id: str, extra: str = "") -> str:
    """The hash of a fixer's prompt for one job with its lesson block taken out (E65, E321): one job run twice has the
    same one, unless the dispatcher adds text outside the lesson block to one run."""
    return _sha({"instance_id": instance_id, "task": "fix", "extra": extra})


def alike_runs(instance_id: str) -> dict[str, dict[str, Any]]:
    """Both runs of an effect pair as the referee records them when they are alike: the same settings, and the same
    prompt once the lesson block is taken out (E65, E321)."""
    run = dict(RUN, prompt_sha256_without_lessons=prompt_hash(instance_id))
    return {"with": dict(run), "without": dict(run)}


def folder_scope(family: str) -> dict[str, Any]:
    """A scope in the public vocabulary: the family's folder and property (the referee's planted lessons use it)."""
    folder, _level, prop = OBSERVABLES[family]
    return {"path_glob": f"{folder}/*", "property": prop}


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

    def own_scope(self, job: dict[str, Any]) -> dict[str, Any]:
        """The scope the brain writes for a lesson it was born from ``job``."""
        obs = job["observables"]
        if self.traits.scope == "observed":
            return {"path_glob": posixpath.dirname(obs["paths"][0]) + "/*", "property": obs["property"]}
        if self.traits.scope == "property":
            return {"property": obs["property"]}
        if self.traits.scope == "label":
            return {"family": job["family"]}  # the answer key's label, which no honest brain can see
        return {}

    def learn(self, lesson_id: str, cause_row: str, scope: dict[str, Any], claim: str, origin: str) -> dict[str, Any]:
        lesson = {"lesson_id": lesson_id, "claim": claim, "origin": origin,
                  "origin_event": cause_row if self.traits.bound or origin != "own_outcome" else "template",
                  "scope": scope, "excluded_conditions": [], "superseded": False}
        self._write(lesson)
        self.dispatch_view[lesson_id] = dict(lesson)
        return lesson

    def fits(self, scope: dict[str, Any], job: dict[str, Any]) -> bool:
        if "family" in scope:  # only the label peeker writes a family into a scope
            return scope["family"] == job["family"]
        return scope_matches(scope, job["observables"])

    def inject(self, job: dict[str, Any], role: str, conditions: list[str]) -> list[str]:
        if not self.traits.injects:
            return []
        if role in ("test_writer", "oracle") and not self.traits.leaks:
            return []
        source = self.lessons if self.traits.fresh_dispatch else self.dispatch_view
        out = []
        for lid in sorted(source):
            lesson = source[lid]
            excluded = set(lesson["excluded_conditions"]) | self.private_exclusions.get(lid, set())
            fits = self.traits.leaks or self.fits(lesson["scope"], job)
            if fits and not lesson["superseded"] and not set(conditions) & excluded:
                out.append(lid)
        return out

    def dispatch_arm(self, job: dict[str, Any], lesson_id: str, held: bool, roll: float) -> list[str]:
        """A placebo arm: the referee says whether ``lesson_id`` is withheld. The cherry picker ignores that for its
        own lessons and gives them where the run will succeed with them, which inflates their credit."""
        if not self.traits.follows_draw and self.lessons[lesson_id]["origin"] == "own_outcome":
            return self.inject(job, "fixer", []) if roll < P_TRAP_WITH_LESSON else []
        return [] if held else self.inject(job, "fixer", [])

    def run_settings(self, given: bool) -> dict[str, Any]:
        if given and not self.traits.equal_arms:
            return dict(RUN, effort="high", max_turns=2 * RUN["max_turns"], max_budget_usd="1.000000")
        return dict(RUN)

    def effect_runs(self, instance_id: str, given: bool) -> dict[str, dict[str, Any]]:
        """An effect pair's two runs as the referee records them (E65, E321). The unequal arms brain gives the
        lesson's run more effort, turns and budget; the unequal effect arms brain keeps the settings equal and adds
        text outside the lesson block of the lesson's run, which only the prompt hash shows."""
        extra = TILT if given and not self.traits.equal_effect_arms else ""
        return {"with": dict(self.run_settings(given), prompt_sha256_without_lessons=prompt_hash(instance_id, extra)),
                "without": dict(self.run_settings(False), prompt_sha256_without_lessons=prompt_hash(instance_id))}

    def fix_ok(self, roll: float, family: str, conditions: list[str], injected: list[str]) -> tuple[bool, str]:
        used = [lid for lid in injected if self.traits.uses]
        if family == TRAP:
            p = P_TRAP_WITH_LESSON if (self.traits.shortcut or "L1" in used) else P_TRAP_WITHOUT
            return roll < p, "other"
        if family == WRONG and "Lw" in used and HARMFUL in conditions:
            ok = roll < P_WRONG_HARMFUL
            return ok, "other" if ok else "lesson_contradicted"
        if family == CONTROL:
            return roll < (P_CONTROL_WITH if "Lc" in used else P_CONTROL_WITHOUT), "other"
        if family == EASY:
            return roll < P_EASY, "other"
        return roll < P_PLAIN, "other"

    def observe(self, lesson_id: str, conditions: list[str], cause: str, red: bool) -> None:
        """A run with ``lesson_id`` given has ended; ``red`` when any test failed in it."""
        contradicted = cause == "lesson_contradicted"
        if red and not self.traits.keeps_priors and self.lessons[lesson_id]["origin"] == "llm_prior":
            contradicted = True  # any red while an imported lesson was given is taken for its contradiction
        if not contradicted or not self.traits.withdraws:
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
            g = [a["ok"] for a in arms if a["lesson_id"] == lid and lid in a["lessons_injected"]]
            w = [a["ok"] for a in arms if a["lesson_id"] == lid and lid not in a["lessons_injected"]]
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


def run_drill(traits: Traits, seed: int, params: dict[str, Any] | None = None, attempt: int = 1) -> dict[str, Any]:
    """Play the referee: plant, run, record, and reveal. Returns the drill file the judge reads.

    A real referee draws every instance and commits to the whole answer key before the run; here
    the key grows while the run is played and is committed at the end. The judge sees only the
    file, so it cannot tell the two apart; the brain never sees the key in either case. ``attempt``
    is the drill's place among the attempts opened in the stage (E323), committed with the key.
    """
    params = dict(DEFAULT_PARAMS if params is None else params)
    rng = random.Random(seed)
    key: dict[str, Any] = {"nonce": f"{rng.getrandbits(256):064x}", "attempt": attempt, "family": TRAP,
                           "cause": CAUSE, "instances": {}, "wrong": {"lesson_id": "Lw", "harmful_condition": HARMFUL},
                           "control": {"lesson_id": "Lc", "family": CONTROL}, "placebo": "Lp",
                           "withhold_seed": f"{rng.getrandbits(256):064x}"}

    def new(family: str, conditions: list[str] | None = None) -> dict[str, Any]:
        iid = f"i{rng.getrandbits(40):010x}"
        folder, level, prop = OBSERVABLES[family]
        obs = {"paths": [f"{folder}/m{rng.getrandbits(24):06x}.py"], "class_level": level, "property": prop}
        key["instances"][iid] = {"family": family, "conditions": conditions or [], "observables": obs}
        return {"instance_id": iid, "family": family, "observables": obs}

    brain = Brain(traits)
    t: dict[str, Any] = {}

    # Birth: the referee plants a bad merge in the trap family; the sentinel turns red and it is reverted.
    birth = new(TRAP)
    cause_row = f"r{rng.getrandbits(32):08x}"
    lesson = brain.learn("L1", cause_row, brain.own_scope(birth), "When a field is renamed, search string references "
                         "too.", "own_outcome")
    t["birth"] = {"instance_id": birth["instance_id"], "reverted": True, "cause": brain.classify(),
                  "cause_row": cause_row, "lesson": {k: lesson[k] for k in ("lesson_id", "origin_event", "scope")}}

    # Use: who gets the lesson.
    use = []
    for i in range(6):
        job = new(TRAP)
        role = ("planner", "fixer")[i % 2]
        use.append({"instance_id": job["instance_id"], "role": role, "lessons_injected": brain.inject(job, role, [])})
    for _ in range(4):
        job = new(OTHER)
        use.append({"instance_id": job["instance_id"], "role": "fixer",
                    "lessons_injected": brain.inject(job, "fixer", [])})
    for role in ("test_writer", "oracle"):
        job = new(TRAP)
        use.append({"instance_id": job["instance_id"], "role": role, "lessons_injected": brain.inject(job, role, [])})
    t["use"] = use

    # Effect: each instance twice, with the dispatcher's own choice and with every lesson withheld; the referee records
    # both runs, their settings and the hash of each prompt without its lesson block, since more effort, turns or
    # budget, or more text, for the lesson's arm would pass for the lesson's effect (E65, E321).
    effect = []
    for _ in range(params["k"]):
        job = new(TRAP)
        injected = brain.inject(job, "fixer", [])
        with_ok, _ = brain.fix_ok(rng.random(), TRAP, [], injected)
        without_ok, _ = brain.fix_ok(rng.random(), TRAP, [], [])
        effect.append({"instance_id": job["instance_id"], "with": with_ok, "without": without_ok,
                       "run": brain.effect_runs(job["instance_id"], "L1" in injected)})
    t["effect"] = effect

    # Wrong lesson: an imported hypothesis that is harmful under one condition.
    brain.learn("Lw", "imported", folder_scope(WRONG), "Edit generated files through their generator.", "llm_prior")
    wrong = []
    for seq in range(10):
        conditions = [HARMFUL] if seq in (1, 4, 6, 8) else []
        job = new(WRONG, conditions)
        trap_test = f"t{rng.getrandbits(32):08x}"
        if conditions:
            key["instances"][job["instance_id"]]["trap_test"] = trap_test
        injected = brain.inject(job, "fixer", conditions)
        ok, cause = brain.fix_ok(rng.random(), WRONG, conditions, injected)
        if "Lw" in injected:
            brain.observe("Lw", conditions, cause, red=not ok)
        state = brain.lessons["Lw"]
        failed_test = None if ok else trap_test if cause == "lesson_contradicted" else "unrelated"
        wrong.append({"seq": seq, "instance_id": job["instance_id"], "injected": "Lw" in injected, "ok": ok,
                      "failed_test": failed_test,
                      "lesson_state": {"superseded": state["superseded"],
                                       "excluded_conditions": list(state["excluded_conditions"])}})
    t["wrong"] = wrong

    # Right lesson: a useful imported lesson, and reds the referee plants that are not its own (E318).
    brain.learn("Lc", "imported", folder_scope(CONTROL), "Apply migrations in dependency order.", "llm_prior")
    control = []
    for seq in range(CONTROL_RUNS):
        conditions = [SHARED] if seq in UNRELATED_REDS else []
        job = new(CONTROL, conditions)
        inst = key["instances"][job["instance_id"]]
        inst["trap_test"] = f"t{rng.getrandbits(32):08x}"
        if conditions:
            inst["unrelated_test"] = f"u{rng.getrandbits(32):08x}"
        injected = brain.inject(job, "fixer", conditions)
        ok, cause = brain.fix_ok(rng.random(), CONTROL, conditions, injected)
        failed_test = inst["trap_test"] if not ok else inst.get("unrelated_test")
        if "Lc" in injected:
            brain.observe("Lc", conditions, cause, red=failed_test is not None)
        state = brain.lessons["Lc"]
        control.append({"seq": seq, "instance_id": job["instance_id"], "injected": "Lc" in injected,
                        "failed_test": failed_test,
                        "lesson_state": {"superseded": state["superseded"],
                                         "excluded_conditions": list(state["excluded_conditions"])}})
    t["control"] = control

    # Placebo: a true but irrelevant lesson; who gets a lesson in each arm is the referee's committed draw.
    brain.learn("Lp", "imported", folder_scope(EASY), "Docstrings are written in the imperative mood.", "llm_prior")
    arms = []
    for lesson_id, family in (("L1", TRAP), ("Lp", EASY)):
        for _ in range(ARMS_PER_LESSON):
            job = new(family)
            roll = rng.random()
            injected = brain.dispatch_arm(job, lesson_id, withheld(key["withhold_seed"], job["instance_id"]), roll)
            ok, _ = brain.fix_ok(roll, family, [], injected)
            arms.append({"instance_id": job["instance_id"], "lesson_id": lesson_id, "lessons_injected": injected,
                         "run": brain.run_settings(lesson_id in injected), "ok": ok})
    ranking, credit = brain.rank(arms, float(params["z"]))
    t["placebo"] = {"arms": arms, "ranking": ranking, "credit": credit}

    # Persistence: rebuild from the ledger in a fresh process and give the next trap instance a lesson.
    before = brain.view()
    restarted = Brain.rebuild(traits, brain.ledger)
    after = new(TRAP)
    injected_before = [brain.lessons[i] for i in brain.inject(after, "fixer", [])]
    injected_after = [restarted.lessons[i] for i in restarted.inject(after, "fixer", [])]
    t["persistence"] = {"instance_id": after["instance_id"], "view_sha256_before": _sha(before),
                        "view_sha256_rebuilt": _sha(restarted.view()),
                        "injected_sha256_before": _sha(injected_before) if injected_before else "",
                        "injected_sha256_after_restart": _sha(injected_after) if injected_after else ""}

    return {"schema": "snowball-drill/2", "drill": "lesson", "commitment_sha256": commitment(key),
            "answer_key": key, "transcript": t, "params": params}
