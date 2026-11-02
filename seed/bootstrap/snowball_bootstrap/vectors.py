"""Apply the seed vectors (`tohum/29a`, `29d`) to the founder's code through the fixed interface.

A vector group applies once a micro-feature of the stage table that owns it is declared done; a group the
table does not name has no owner in this stage and does not run (`cp_lower`, `mcnemar`, `match` are P1's,
`drill` the Stage 2 batch's). Every vector is checked twice: the right input must give the expected answer,
and a changed input must not.

`chain` and the P1 and drill groups have judges of their own, written before `29d`. Every other group is data
(`"runner": "data"`) and one judge applies it, so a seed epoch adds a group without adding code (`29d`).

The judges only judge; who runs a call is the run's (E440). `VectorRun` runs every call itself, `PartRun` only the
inputs one part of `kos` owns, `Replay` none: it hands each call the answer a part recorded for it, so the join judges
every vector over the parts' answers exactly as the single job judges over its own.

The expected answers are the exam's, not the public's (E509). The vectors the referee publishes hold the inputs alone
(`public_vectors`); the answers come from the private store, checked against the epoch's pin (`answers`), and only the
job that judges reads them. On the inputs alone the judges still ask every call in order, so `kos`'s parts run their
share without an answer at hand; nothing is judged on them. A record never shows an expected value: a pass shows
nothing, a fail shows only the parts of the Founder's answer that differ from the expected one.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import shlex
import shutil
import time
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable

from . import answers, stages
from .container import Runner

CWD = "referee"
SEED_FILE = "vectors.json"  # every case's command (and, in the seed, its expected answer); the fixtures beside it
CASES_FILE = "cases.json"  # what the Founder's capsule reads of the data cases: their inputs, no answer (E244)
_HASH = re.compile("[0-9a-f]{40}|[0-9a-f]{64}")
# `docker run` exits with this when docker itself failed. Since E01 the container turns a command's own 125 into 1,
# so 125 here never comes from the Founder's code: such a vector is the sandbox failing, not a wrong answer (E141).
DOCKER_ERROR = 125
# Every vector call of one `kos` part together, retries included: a part is its own job, and the single job is one
# part (E440). The spec names no limit; this one keeps a command that hangs on every input from outliving the job
# (60 min), which would book the push as an outage that never reaches the Founder. What the budget leaves unrun is red
# as `not_run:time_budget` and the Founder's (E18's plan).
BUDGET_S = 1200
_now = time.monotonic
TAPE_FIELDS = ("input", "line", "exit", "fault")  # one call's answer as a part records it (E440)


def fixtures(vectors_dir: Path, dest: Path) -> Path:
    """What the sandbox mounts at `/vec`: the seed's vectors without ``vectors.json``. The commands read their fixtures
    there; the expected values stay with the referee, or Founder code could print the answer it finds for its argv."""
    if dest.exists():  # a work directory used twice gets a fresh copy, never an old one
        shutil.rmtree(dest)
    shutil.copytree(vectors_dir, dest)
    (dest / SEED_FILE).unlink()
    return dest


def founder_inputs(vectors_dir: Path, dest: Path) -> Path:
    """What the Founder's capsule mounts at `/vec` (E244, Founder report f97): the files `fixtures` gives the referee's
    containers, so each case's command runs there verbatim, and `cases.json`, every data case's inputs with no expected
    value: inputs yes, answers never. A seed with a fixture that carries an answer its case must compute is refused
    before anything is written, since the Founder would read the answer there; on the public vectors, which hold no
    answer, that check is the exam's admission's (`local/exam_admit.py`, E509). The referee's containers keep
    `fixtures`."""
    spec = _seed(vectors_dir)
    inputs, own = answers.split(spec, strict=False)
    lookups = _lookups(vectors_dir, spec) if own else []  # on the public inputs the admission checked it (E509)
    if lookups:
        raise ValueError("a fixture carries an answer its case must compute: " + "; ".join(lookups))
    if (vectors_dir / CASES_FILE).exists():
        raise ValueError(f"the seed has a fixture named {CASES_FILE}; the inputs would overwrite it")
    cases = [_inputs(case) for case in _data_cases(inputs)]
    fixtures(vectors_dir, dest)
    (dest / CASES_FILE).write_text(json.dumps(cases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return dest


def public_vectors(vectors_dir: Path, dest: Path) -> Path:
    """The vectors as the referee publishes them (E509): every fixture, and ``vectors.json`` with the inputs alone
    (`answers.split`). What the operator installs as the referee's `vectors/`, so no snapshot, artifact or `/vec`
    holds an expected value. Returns ``dest``."""
    inputs, _answers = answers.split(_seed(vectors_dir))
    fixtures(vectors_dir, dest)
    (dest / SEED_FILE).write_text(json.dumps(inputs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return dest


def fixture_lookups(vectors_dir: Path, exam: answers.Exam) -> list[str]:
    """`case: file` for each public fixture that carries an answer its case must compute, the answers being the exam's
    (E244's check, made where the answers are: the admission and the judging job)."""
    return _lookups(vectors_dir, answers.join(answers.split(_seed(vectors_dir), strict=False)[0], exam))


def _inputs(case: dict[str, Any]) -> dict[str, Any]:
    """A data case as the Founder reads it. Named fields only, so nothing of `expect` or `expect_not` comes along; a
    missing stdin is the empty one the runner sends."""
    changed = case["changed"]
    return {"id": case["id"], "purpose": case["purpose"], "cmd": case["cmd"], "stdin": case.get("stdin", ""),
            "fixture": case["fixture"],
            "changed": {"description": changed["description"], "cmd": changed["cmd"],
                        "stdin": changed.get("stdin", ""), "fixture": changed["fixture"]}}


def answer_atoms(value: Any) -> list[str]:
    """The parts of an expected value shaped like an answer only code computes: content addresses, reasons bound to a
    path, git and sha256 hashes. Short values (a count, a verdict, a bare path) are everywhere and tell nothing."""
    if isinstance(value, dict):
        return [a for v in value.values() for a in answer_atoms(v)]
    if isinstance(value, list):
        return [a for v in value for a in answer_atoms(v)]
    shaped = isinstance(value, str) and (value.startswith("sha256:") or (":" in value and "/" in value)
                                         or _HASH.fullmatch(value) is not None)
    return [value] if shaped else []


def _given(vectors_dir: Path, variant: dict[str, Any]) -> list[bytes]:
    """What one variant of a case hands its command: the argv, the stdin and its fixtures (a file or a tree)."""
    given = [variant["cmd"].encode("utf-8"), variant.get("stdin", "").encode("utf-8")]
    for rel in variant["fixture"]:
        path = vectors_dir / rel
        given += [p.read_bytes() for p in ([path] if path.is_file() else sorted(path.rglob("*"))) if p.is_file()]
    return given


def _data_cases(spec: dict[str, Any]) -> list[dict[str, Any]]:
    return [case for group in spec.values() if isinstance(group, dict) and group.get("runner") == DATA_RUNNER
            for case in group["cases"]]


def _lookups(vectors_dir: Path, spec: dict[str, Any]) -> list[str]:
    """`case: file` for each fixture file that carries an answer its case must compute, one the case's own inputs do
    not carry. What an input carries is an echo (the image a recipe names, the tip hash a ledger row holds)."""
    files = {p: p.read_bytes() for p in sorted(vectors_dir.rglob("*")) if p.is_file() and p != vectors_dir / SEED_FILE}
    found = set()
    for case in _data_cases(spec):
        given = _given(vectors_dir, case) + _given(vectors_dir, case["changed"])
        for atom in answer_atoms([case["expect"], case["changed"]["expect_not"]]):
            raw = atom.encode("utf-8")
            if not any(raw in part for part in given):
                found |= {f"{case['id']}: {p.relative_to(vectors_dir).as_posix()}" for p, data in files.items()
                          if raw in data}
    return sorted(found)


def _last_line(stdout: bytes) -> str | None:
    """A call's answer as it printed it: the last line of stdout that is not blank, or None when every line is. The
    line is what a part records, so the join reads the object, its fields and their order as the single job does."""
    for line in reversed(stdout.decode("utf-8", "replace").splitlines()):
        line = line.strip()
        if line:
            return line
    return None


def _parse(line: str | None) -> dict[str, Any] | None:
    """The JSON object an answer's line holds, or None."""
    if line is None:
        return None
    try:
        value = json.loads(line)
    except (json.JSONDecodeError, RecursionError):  # nested deeper than the parser goes is no answer, not a crash
        return None
    return value if isinstance(value, dict) else None


def input_key(cmd: str, stdin: bytes) -> str:
    """One input of the run (E273: one command on one stdin over the same tree and `/vec`), as a tape names it."""
    raw = cmd.encode("utf-8", "surrogatepass")
    return hashlib.sha256(len(raw).to_bytes(8, "big") + raw + stdin).hexdigest()


class TapeError(ValueError):
    """The answers handed to the judges are not the calls the judges make (E440): nothing is judged on them."""


def _rounded(value: Any, like: str) -> str | None:
    if not isinstance(value, str):
        return None
    places = len(like.split(".", 1)[1]) if "." in like else 0
    try:
        return str(Decimal(value).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP))
    except InvalidOperation:
        return None


class VectorRun:
    def __init__(self, runner: Runner, timeout_s: int, budget_s: int = BUDGET_S):
        self.runner = runner
        self.timeout_s = timeout_s
        self.deadline = _now() + budget_s
        self.results: list[dict[str, Any]] = []
        self.fault = ""
        self.exit: int | None = None  # the exit code of the last try of the last call
        # E273: one command on one stdin over the same read-only tree and `/vec` is one input. A case whose input an
        # earlier case ran (a changed input is often another case's input) reuses that answer: a container less, the
        # budget kept for inputs not yet asked. Only answers are kept; a call that gave none is asked again.
        self.answers: dict[tuple[str, bytes], tuple[str | None, int]] = {}
        # E440: every call in order, with what a record reads of it (the answer's line, the exit, the fault): what a
        # part of `kos` hands the join.
        self.tape: list[dict[str, Any]] = []

    def call(self, cmd: str, stdin: bytes = b"") -> dict[str, Any] | None:
        line = self._ask(cmd, stdin)
        self.tape.append({"input": input_key(cmd, stdin), "line": line, "exit": self.exit, "fault": self.fault})
        return _parse(line)

    def _ask(self, cmd: str, stdin: bytes) -> str | None:
        if (cmd, stdin) in self.answers:
            line, self.exit = self.answers[(cmd, stdin)]
            self.fault = ""
            return line
        res = None
        for _ in range(2):  # a container the host killed under load answers nothing: ask again before blaming the judge
            left = self.deadline - _now()
            if left <= 0:
                break
            res = self.runner.run(cmd, cwd=CWD, stdin=stdin, timeout_s=min(self.timeout_s, math.ceil(left)))
            self.exit = res.exit_code
            if not res.timed_out and res.stdout.strip():
                self.fault = ""
                self.answers[(cmd, stdin)] = (_last_line(res.stdout), res.exit_code)
                return self.answers[(cmd, stdin)][0]
        if res is None:  # the budget was spent before this call: it never ran
            self.exit = None
            self.fault = "not_run:time_budget"
            return None
        tail = res.stderr[-100:].decode("utf-8", "replace") if isinstance(res.stderr, bytes) else ""
        self.fault = f"no answer: exit {res.exit_code}{', timed out' if res.timed_out else ''} {tail}".strip()
        return None

    def record(self, vid: str, ok: bool, detail: str = "") -> None:
        if not ok and self.fault:
            detail = f"{detail} | {self.fault}"
            self.fault = ""
        self.results.append({"id": vid, "ok": ok, "detail": detail[:200], "exit": self.exit,
                             "runner_fault": not ok and self.exit == DOCKER_ERROR})


class PartRun(VectorRun):
    """One part's share of a push (E440): it runs the calls whose input ``mine`` holds, each exactly as the single job
    runs it (the same retries, the same remembered answers, its own budget), and no other. A record after a call it
    left to another part reads no answer of its own: it is not kept here (the join writes every record)."""

    def __init__(self, runner: Runner, timeout_s: int, mine: set[str]):
        super().__init__(runner, timeout_s)
        self.mine = mine
        self.blind = False

    def call(self, cmd: str, stdin: bytes = b"") -> dict[str, Any] | None:
        if input_key(cmd, stdin) in self.mine:
            return super().call(cmd, stdin)
        self.blind = True
        return None

    def record(self, vid: str, ok: bool, detail: str = "") -> None:
        if self.blind:
            self.blind = False
            return
        super().record(vid, ok, detail)


class Replay(VectorRun):
    """The join's run (E440): no container. Each call takes the next answer of the parts' merged tape, which must be
    this call's input, and leaves its exit and fault where the record reads them, as the call that answered did."""

    def __init__(self, tape: list[dict[str, Any]]):
        super().__init__(None, 0)  # it runs nothing
        self.queue, self.next = tape, 0

    def call(self, cmd: str, stdin: bytes = b"") -> dict[str, Any] | None:
        if self.next >= len(self.queue) or self.queue[self.next]["input"] != input_key(cmd, stdin):
            raise TapeError(f"call {self.next} of the judges is not the parts' call {self.next}")
        entry = self.queue[self.next]
        self.next += 1
        self.exit, self.fault = entry["exit"], entry["fault"]
        return _parse(entry["line"])


class _Plan(VectorRun):
    """Runs nothing: it notes the input of every call the judges make. No judge asks a call for what an earlier
    call answered, so this is the order every run asks them in (`Replay` refuses a tape that is not)."""

    def __init__(self) -> None:
        super().__init__(None, 0)
        self.inputs: list[str] = []

    def call(self, cmd: str, stdin: bytes = b"") -> dict[str, Any] | None:
        self.inputs.append(input_key(cmd, stdin))
        return None


# What a record shows of the Founder's answer (E509). The signed result is public: a value shown on a pass, or a field
# shown that matched, is the expected value itself, for every reader. So a pass shows nothing, and a fail shows the
# Founder's value only where it differs from the expected one; an answer that is the one a changed input must not
# give is named, not shown. A wrong answer's detail still begins with "got ".
GAVE_THE_ORIGINAL = "got the answer a changed input must not give"


def _got(ok: bool, got: Any, *avoid: Any) -> str:
    if ok:
        return ""
    if any(_same(got, a) for a in avoid):
        return GAVE_THE_ORIGINAL
    return f"got {got}"


def _differing(out: dict[str, Any] | None, fields: dict[str, Any]) -> str:
    """Of the fields ``fields`` names, those ``out`` gives with another value, and those it leaves out."""
    if out is None:
        return "no JSON object"
    shown = {k: out[k] for k in fields if k in out and not _same(out[k], fields[k])}
    absent = [k for k in fields if k not in out]
    if not shown and not absent:
        return GAVE_THE_ORIGINAL
    return "got " + json.dumps(shown) + (f", without {', '.join(absent)}" if absent else "")


def _chain(run: VectorRun, spec: dict[str, Any]) -> None:
    for i, item in enumerate(spec["rows"], start=1):
        row, expected = item["row"], item["row_hash"]
        out = run.call("python -m ledger.chain hash", json.dumps(row).encode())
        got = out.get("row_hash") if out else None
        run.record(f"chain.V{i}.hash", got == expected, _got(got == expected, got))
        changed = dict(row, row_id=row["row_id"] + "x")
        out = run.call("python -m ledger.chain hash", json.dumps(changed).encode())
        got = out.get("row_hash") if out else None
        ok = isinstance(got, str) and got != expected
        run.record(f"chain.V{i}.hash_changed_input", ok, _got(ok, got, expected))
    out = run.call(f"python -m ledger.chain verify {shlex.quote('/vec/' + spec['verify_good'])}")
    ok = bool(out) and out.get("valid") is True
    run.record("chain.verify_good", ok, "" if ok else json.dumps(out)[:120])
    out = run.call(f"python -m ledger.chain verify {shlex.quote('/vec/' + spec['verify_v3'])}")
    ok = bool(out) and out.get("valid") is False and out.get("broken_row") == spec["v3_broken_row"]
    run.record("chain.V3", ok, "" if ok else _differing(out, {"valid": False, "broken_row": spec["v3_broken_row"]}))


def _cp(run: VectorRun, spec: dict[str, Any]) -> None:
    alpha = spec["alpha"]
    for x, n, expected in spec["cases"]:
        out = run.call(f"python -m harness.stats cp_lower {x} {n} {alpha}")
        got = _rounded(out.get("lb") if out else None, expected)
        run.record(f"cp_lower.{x}/{n}", got == expected, _got(got == expected, got))
        lower_x = str(Decimal(x) - 1)
        out = run.call(f"python -m harness.stats cp_lower {lower_x} {n} {alpha}")
        got = _rounded(out.get("lb") if out else None, expected)
        ok = got is not None and got != expected
        run.record(f"cp_lower.{x}/{n}.changed_input", ok, _got(ok, got, expected))


def _mcnemar(run: VectorRun, spec: dict[str, Any]) -> None:
    for b, c, expected in spec["cases"]:
        out = run.call(f"python -m harness.stats mcnemar {b} {c}")
        got = _rounded(out.get("p") if out else None, expected)
        run.record(f"mcnemar.{b},{c}", got == expected, _got(got == expected, got))
        out = run.call(f"python -m harness.stats mcnemar {b + 1} {c}")
        got = _rounded(out.get("p") if out else None, expected)
        ok = got is not None and got != expected
        run.record(f"mcnemar.{b},{c}.changed_input", ok, _got(ok, got, expected))


def _match(run: VectorRun, spec: dict[str, Any]) -> None:
    for i, item in enumerate(spec["cases"], start=1):
        cmd = ("python -m harness.score "
               f"{shlex.quote('/vec/' + item['findings'])} {shlex.quote('/vec/' + item['cases'])}")
        out = run.call(cmd)
        got = out.get("hits") if out else None
        ok = isinstance(got, int) and not isinstance(got, bool) and got == item["hits"]
        run.record(f"match.{i}", ok, _got(ok, got))


def _drill(run: VectorRun, spec: dict[str, Any]) -> None:
    """Lesson drill judge (`tohum/29c`): every simulated brain gets the reference verdicts. The edited
    cases are the changed inputs: a brain's run with its answer key (``tampered_key``) or its transcript
    edited after it."""
    for item in spec["cases"]:
        out = run.call(f"python -m harness.drill judge {shlex.quote('/vec/' + item['file'])}")
        got = (out.get("drill"), out.get("verdicts")) if out else (None, None)
        ok = got == (item["drill"], item["verdicts"])
        run.record(f"drill.{item['name']}", ok,
                   "" if ok else _differing(out, {"drill": item["drill"], "verdicts": item["verdicts"]}))


def _same(a: Any, b: Any) -> bool:
    """Equal as JSON values. Python's ``==`` would take ``1`` for ``true`` and ``1.0`` for ``1``; JSON does not."""
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def _gives(out: dict[str, Any] | None, fields: dict[str, Any]) -> bool:
    return out is not None and all(name in out and _same(out[name], value) for name, value in fields.items())


def _shown(out: dict[str, Any] | None, fields: dict[str, Any]) -> str:
    """A data case's detail: nothing when ``out`` gives ``fields``, else what differs (E509)."""
    return "" if _gives(out, fields) else _differing(out, fields)


def _shown_not(out: dict[str, Any] | None, avoid: dict[str, Any]) -> str:
    """A changed input's detail: nothing when ``out`` answers every field of ``avoid`` and not with it, else what
    differs from it (nothing of it, when it is ``avoid``: that answer is the original input's, E509)."""
    if out is not None and all(name in out for name in avoid) and not _gives(out, avoid):
        return ""
    return _differing(out, avoid)


def _data(run: VectorRun, spec: dict[str, Any]) -> None:
    """The generic data runner (`29d`). A case's command, run from ``referee/`` with its stdin, must print every
    field ``expect`` names with that value; other fields of the line (an argv, a reason) are not compared. Its
    changed input must answer the same fields, and not with ``expect_not``: an answer that ignores the input
    fails there, and so does no answer at all."""
    for case in spec["cases"]:
        out = run.call(case["cmd"], case.get("stdin", "").encode("utf-8"))
        run.record(case["id"], _gives(out, case["expect"]), _shown(out, case["expect"]))
        changed = case["changed"]
        avoid = changed["expect_not"]
        out = run.call(changed["cmd"], changed.get("stdin", "").encode("utf-8"))
        run.record(f"{case['id']}.changed_input",
                   out is not None and all(name in out for name in avoid) and not _gives(out, avoid),
                   _shown_not(out, avoid))


GROUPS = (("chain", _chain), ("cp_lower", _cp), ("mcnemar", _mcnemar), ("match", _match), ("drill", _drill))
DATA_RUNNER = "data"  # a group of `{cmd, stdin?, fixture, expect, changed: {..., expect_not}}` cases (`29d`)


def _seed(vectors_dir: Path) -> dict[str, Any]:
    return json.loads((vectors_dir / SEED_FILE).read_text(encoding="utf-8"))


def _delivered(group: dict[str, Any], tree: Path | None) -> bool:
    """A data group's interface page (`29f`, `29g`) is all the Founder reads of it. The group applies to a tree whose
    seed carries that page; vectors the referee got before the Founder's seed did are the seed's gap, not a red push.
    Without a tree (a check of the seed alone) nothing is asked of it."""
    page = group.get("interface")
    return tree is None or (isinstance(page, str) and (tree / page).is_file())


def _judges(spec: dict[str, Any], tree: Path | None = None) -> dict[str, Callable[[VectorRun, dict[str, Any]], None]]:
    """Every group the seed has a judge for, in the seed's order: its own judge, or the data runner for a group
    marked as data whose page the tree has. A group with neither cannot run."""
    own = dict(GROUPS)
    judges: dict[str, Callable[[VectorRun, dict[str, Any]], None]] = {}
    for name, group in spec.items():
        if name in own:
            judges[name] = own[name]
        elif isinstance(group, dict) and group.get("runner") == DATA_RUNNER and _delivered(group, tree):
            judges[name] = _data
    return judges


def missing_groups(vectors_dir: Path, done_mf: tuple[int, ...], table: stages.StageTable, *,
                   tree: Path | None = None) -> list[str]:
    """Groups a finished micro-feature owns that the seed has no vectors (or no runner) for yet, or whose interface
    page is not yet in the Founder's seed (``tree``).

    Their expected values come with the seed, computed twice independently (`29a`), and since E509 from the exam's
    store; the referee never makes them up. `decide` warns on a code push and refuses the exit while any is missing.
    """
    judges = _judges(_seed(vectors_dir), tree)
    return [g for g in table.groups_of(done_mf) if g not in judges]


class Applied(list):
    """The groups one push runs, in the seed's order, each ``(judge, vectors)``. ``answered`` is False for groups read
    from the public inputs alone (E509): every call is asked in order on them, and nothing is judged on them."""

    def __init__(self, items: Any = (), *, answered: bool = True):
        super().__init__(items)
        self.answered = answered


def exam_seed(vectors_dir: Path, exam: answers.Exam | None = None) -> tuple[dict[str, Any], bool]:
    """The vectors the judges run, and whether they hold the answers (E509). With ``exam``, the public inputs filled
    with its answers: inputs that hold an answer of their own are refused, never mixed with the store's. Without it,
    a seed that holds every answer is itself (the seed's own vectors, before an exam was pinned); one that holds the
    inputs alone is the plan of the calls, ``answered`` False."""
    spec = _seed(vectors_dir)
    inputs, own = answers.split(spec, strict=False)
    if exam is not None:
        if own:
            raise answers.AnswersError("the public vectors hold answers: install the projection, not the seed")
        return answers.join(inputs, exam), True
    if own or not answers.slot_pointers(inputs):
        return spec, True
    return answers.blank(inputs), False


def applied(vectors_dir: Path, done_mf: tuple[int, ...], *, table: stages.StageTable | None = None,
            tree: Path | None = None, exam: answers.Exam | None = None) -> Applied:
    """The groups one push runs, in the seed's order, each with its judge and its vectors: those a finished
    micro-feature owns and the seed has a judge for (E151, E199). The single job, every part and the join run these;
    the join with the exam's answers (``exam``), the parts on the inputs alone (E509)."""
    owned = set((table or stages.load(0)).groups_of(done_mf))
    spec, answered = exam_seed(vectors_dir, exam)
    found = Applied(answered=answered)
    for name, judge in _judges(spec, tree).items():
        if name in owned:
            found.append((judge, spec[name]))
    return found


def _judge(run: VectorRun, groups: Applied) -> list[dict]:
    for judge, group in groups:
        judge(run, group)
    return run.results


def _answered(groups: Applied) -> Applied:
    """Groups that may be judged: built with every answer at hand. A verdict on the inputs alone would be the store's
    outage passed off as the Founder's work, green or red (E509)."""
    if not isinstance(groups, Applied) or not groups.answered:
        raise answers.AnswersError("these vectors hold the inputs alone: nothing is judged without the exam's answers")
    return groups


def run_vectors(runner: Runner, vectors_dir: Path, done_mf: tuple[int, ...], timeout_s: int = 120, *,
                table: stages.StageTable | None = None, tree: Path | None = None,
                exam: answers.Exam | None = None) -> list[dict]:
    groups = _answered(applied(vectors_dir, done_mf, table=table, tree=tree, exam=exam))
    return _judge(VectorRun(runner, timeout_s), groups)


def call_inputs(groups: Applied) -> list[str]:
    """The input of every call a push's judges make, in order; nothing runs (E440)."""
    plan = _Plan()
    _judge(plan, groups)
    return plan.inputs


def run_part(runner: Runner, groups: Applied, mine: set[str], timeout_s: int = 120) -> tuple[list[dict], list[dict]]:
    """One part's calls (E440): its tape, and the records it could write from its own answers alone. On the inputs
    alone (E509) it knows no record: none of its vectors counts as red, and it runs its share of module-less red."""
    run = PartRun(runner, timeout_s, mine)
    known = _judge(run, groups)
    return run.tape, known if groups.answered else []


def replay(tape: list[dict[str, Any]], groups: Applied) -> list[dict]:
    """Every record of a push, judged over ``tape``: the parts' answers merged in the judges' call order (E440)."""
    run = Replay(tape)
    records = _judge(run, _answered(groups))
    if run.next != len(tape):
        raise TapeError(f"the parts answered {len(tape) - run.next} calls the judges never make")
    return records
