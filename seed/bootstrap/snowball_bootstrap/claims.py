"""Open claims: their age, the Founder's answer and how they close (`tohum/29x`; the owner's decision, E596).

An open claim is a refutation of the rival's that no reproducer proved on the head it was made for (`29`, E07, E260).
The signed result shows each with its age: ``accepted_heads``, the accepted spec, code and exit heads since the claim
was opened (the one rule input), and ``days`` (a measurement only). A claim must not stay unanswered: once its age
reaches the exit's own trust window (``stage_params.rival_min_attempts``) unanswered, it is ``claim_overdue``, a warning
in Stage 0 and a reason from Stage 1 (the shape of `29t`).

The Founder answers a claim with a record, ``reports/claim-<id>.json``: a fix or a refutation and the lines it cites.
The referee checks the record mechanically (its shape; every cited line is in the head; a fix cites a file changed since
the claim's first head, one of the claim's own evidence files where it has any; a refutation cites one of these). A
valid answer stops the overdue rule; it never closes the claim, because the Founder is no judge of the rival's claim
(Y6) and a command it chose proves nothing (Y8: one changed comment line can make any command differ between two heads).
A claim closes only by: ``observed`` (its own reproducer, run on an accepted head, shows what it calls correct and not
the symptom: `29` calls that bookkeeping, not proof, so the rival may send the claim again and a returning id counts
``reopened``), ``proven`` (the rival proves it, `29`), or ``operator`` (``control.json`` ``waived_claims``). The
operator may refuse an answer (``refused_answers``, the file's sha256) and the rival may send the claim again after it
(``challenged``): either way the answer no longer counts and the age, which never stopped, decides again.

The memory is the optional state key ``claim_book`` (absent means empty, so a state written before this rule
validates unchanged): each open claim's age and opening time, the closures by kind, the evicted, reopened and challenged
counts, and the last 50 closures. Nothing here runs code or reads a network; `pull` hands the answers it read.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import re
import statistics
from typing import Any

from .config import CLAIM_RE as CLAIM_ID_RE, HEX64_RE
from .treehash import TreeError, iter_files

BOOK = "claim_book"  # the optional state key
ANSWER_DIR = "reports"
ANSWER_NAME = re.compile(r"^claim-([0-9a-f]{12})\.json\Z")
ANSWER_KIND = "claim_answer"
ANSWER_STATE = "answer"  # not `open`: an answer is no report the operator owes a seed epoch (`reports_open`)
ANSWERS = ("fix", "refute")
ANSWER_KEYS = frozenset({"id", "kind", "ref", "state", "answer", "evidence_refs"})
ANSWER_OPTIONAL = frozenset({"note"})
MAX_REFS = 5
MAX_NOTE = 2000
MAX_ANSWERS = 10  # one per open claim (`state.MAX_OPEN_CLAIMS`)
RECENT = 50  # closures kept for `time_to_close`
MAX_CHALLENGED = 5  # answer hashes the rival sent the claim again after, per claim
HOWS = ("observed", "operator", "proven")
BASES = ("run", "seeded")
OVERDUE = "claim_overdue"
INVALID = "claim_answer_invalid"
ANSWERED = "claims_answered"
NAMES = (OVERDUE, INVALID, ANSWERED)
TIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z")
ROW_KEYS = frozenset({"accepted_heads", "opened_at", "basis", "challenged"})
RECENT_KEYS = frozenset({"id", "how", "accepted_heads", "days"})
BOOK_KEYS = frozenset({"claims", "closed", "evicted", "reopened", "challenged", "recent"})


# ---------------------------------------------------------------- the answers `pull` reads


def _lines(content: bytes) -> int:
    return content.count(b"\n") + (0 if content.endswith(b"\n") or not content else 1)


def _refs(value: Any, lines: dict[str, int]) -> tuple[list[dict[str, Any]] | None, str | None]:
    if not isinstance(value, list) or not 1 <= len(value) <= MAX_REFS:
        return None, "evidence_refs"
    refs = []
    for ref in value:
        if not (isinstance(ref, dict) and set(ref) == {"path", "line_start", "line_end"}
                and isinstance(ref["path"], str) and all(type(ref[k]) is int for k in ("line_start", "line_end"))
                and 1 <= ref["line_start"] <= ref["line_end"]):
            return None, "evidence_refs"
        if ref["path"] not in lines:
            return None, f"ref_missing:{ref['path'][:200]}"
        if ref["line_end"] > lines[ref["path"]]:
            return None, f"ref_lines:{ref['path'][:200]}"
        refs.append(dict(ref))
    return refs, None


def read_answers(tar_bytes: bytes) -> list[dict[str, Any]]:
    """Every ``reports/claim-<id>.json`` directly under the root, by path: ``{ref, sha256, answer, paths, problem}``.
    ``problem`` is None for a record of the right shape whose every cited line is in this tree; otherwise it names the
    first thing wrong. The free text (``note``) is the operator's to read in the file; nothing of it is kept here."""
    lines: dict[str, int] = {}
    found: list[tuple[str, str, bytes]] = []
    try:
        for path, content, _exec in iter_files(tar_bytes):
            rel = path.as_posix()
            lines[rel] = _lines(content)
            name = ANSWER_NAME.match(path.name)
            if len(path.parts) == 2 and path.parts[0] == ANSWER_DIR and name:
                found.append((rel, name.group(1), content))
    except TreeError:
        return []
    rows = []
    for _rel, ref, content in sorted(found)[:MAX_ANSWERS]:
        row: dict[str, Any] = {"ref": ref, "sha256": hashlib.sha256(content).hexdigest(), "answer": None, "paths": [],
                               "problem": None}
        try:
            data = json.loads(content.decode("utf-8"))
        except (UnicodeDecodeError, ValueError, RecursionError):
            data = None
        if not (isinstance(data, dict) and ANSWER_KEYS <= set(data) <= ANSWER_KEYS | ANSWER_OPTIONAL
                and data["kind"] == ANSWER_KIND and data["state"] == ANSWER_STATE and data["answer"] in ANSWERS
                and (not isinstance(data.get("note"), str) or len(data["note"]) <= MAX_NOTE)
                and ("note" not in data or isinstance(data["note"], str))):
            row["problem"] = "malformed"
        elif data["id"] != f"claim-{ref}" or data["ref"] != ref:
            row["problem"] = "id_mismatch"
        else:
            refs, problem = _refs(data["evidence_refs"], lines)
            row["answer"] = data["answer"]
            row["paths"] = sorted({r["path"] for r in refs or []})
            row["problem"] = problem
        rows.append(row)
    return rows


def engage(rows: list[dict[str, Any]], open_claims: list[dict[str, Any]],
           changed_since: dict[str, set[str] | None]) -> list[dict[str, Any]]:
    """The answers to claims that are open, each held to what it says it is: a fix cites a file changed between the
    claim's first head and this head (``changed_since`` by claim, None when the first head is not in the brain) and, for
    a claim with evidence, one of the claim's own evidence files among them; a refutation cites a file of the claim's
    own evidence (a claim with none asks for nothing more). An answer to a
    claim that is not open is no answer (it is dropped). The cited paths do not leave this function."""
    claims = {c["id"]: c for c in open_claims}
    kept = []
    for row in rows:
        claim = claims.get(row["ref"])
        if claim is None:
            continue
        problem = row["problem"]
        own = {r.get("path") for r in claim["evidence_refs"] if isinstance(r, dict)}
        if problem is None and row["answer"] == "fix":
            changed = changed_since.get(row["ref"])
            if changed is None:
                problem = "first_head_unknown"
            elif not set(row["paths"]) & changed:
                problem = "fix_cites_no_change"
            elif own and not set(row["paths"]) & changed & own:
                problem = "fix_cites_no_claim_change"
        elif problem is None and row["answer"] == "refute":
            if own and not set(row["paths"]) & own:
                problem = "refute_cites_no_claim_path"
        kept.append({"ref": row["ref"], "sha256": row["sha256"], "answer": row["answer"], "problem": problem})
    return kept


# ---------------------------------------------------------------- the book


def empty_book() -> dict[str, Any]:
    return {"claims": {}, "closed": {how: 0 for how in HOWS}, "evicted": 0, "reopened": 0, "challenged": 0,
            "recent": []}


def _count(value: Any) -> bool:
    return type(value) is int and value >= 0


def valid_book(book: Any, open_ids: set[str]) -> bool:
    """The state's ``claim_book``: every key, a row only for an open claim, counts that are counts."""
    if not (isinstance(book, dict) and set(book) == BOOK_KEYS and isinstance(book["claims"], dict)
            and isinstance(book["closed"], dict) and set(book["closed"]) == set(HOWS)
            and all(_count(book["closed"][h]) for h in HOWS)
            and all(_count(book[k]) for k in ("evicted", "reopened", "challenged"))
            and isinstance(book["recent"], list) and len(book["recent"]) <= RECENT):
        return False
    for cid, row in book["claims"].items():
        if not (cid in open_ids and isinstance(row, dict) and set(row) == ROW_KEYS and _count(row["accepted_heads"])
                and (row["opened_at"] is None or TIME_RE.match(str(row["opened_at"])))
                and row["basis"] in BASES and isinstance(row["challenged"], list)
                and len(row["challenged"]) <= MAX_CHALLENGED
                and all(isinstance(h, str) and HEX64_RE.match(h) for h in row["challenged"])):
            return False
    return all(isinstance(r, dict) and set(r) == RECENT_KEYS and CLAIM_ID_RE.match(str(r["id"])) and r["how"] in HOWS
               and _count(r["accepted_heads"]) and (r["days"] is None or _count(r["days"])) for r in book["recent"])


def _seeded_age(state: dict[str, Any], first_head: str) -> int:
    """A claim opened before this rule: the heads that survived the rival after its first head (`rival_artifacts`,
    in the order they were judged), the nearest the state holds to the accepted heads since (an approximation, named
    ``seeded``). A first head the list does not hold counts every survivor."""
    arts = state["rival_artifacts"]
    start = next((i + 1 for i, a in enumerate(arts) if a["sha"] == first_head), 0)
    return sum(1 for a in arts[start:] if a["outcome"] == "survived")


def _days(opened_at: str | None, now: str) -> int | None:
    if opened_at is None:
        return None
    when = datetime.datetime.strptime(opened_at, "%Y-%m-%dT%H:%M:%SZ")
    return max(0, (datetime.datetime.strptime(now, "%Y-%m-%dT%H:%M:%SZ") - when).days)


class Claims:
    """One run's view of the open claims, built from the state `pull` read; `decide` calls it in order:
    ``answers`` and ``challenge`` while it reads the run, ``overdue`` before the verdict, ``settle`` after it."""

    def __init__(self, state: dict[str, Any], meta_claims: dict[str, Any] | None, now: str) -> None:
        meta_claims = meta_claims if isinstance(meta_claims, dict) else {}
        self.now = now
        self.book = json.loads(json.dumps(state.get(BOOK) or empty_book()))
        self.prior = [c["id"] for c in state["open_claims"]]
        self.first_heads = {c["id"]: c["first_head"] for c in state["open_claims"]}
        dates = meta_claims.get("dates") or {}
        for cid in self.prior:  # a claim with no row was opened before this rule: its age is seeded once
            if cid not in self.book["claims"]:
                opened = dates.get(cid)
                self.book["claims"][cid] = {
                    "accepted_heads": _seeded_age(state, self.first_heads[cid]),
                    "opened_at": opened if isinstance(opened, str) and TIME_RE.match(opened) else None,
                    "basis": "seeded", "challenged": []}
        self.waived = sorted(set(meta_claims.get("waived") or []) & set(self.prior))
        refused = set(meta_claims.get("refused") or [])
        self.answers: dict[str, dict[str, Any]] = {}
        for row in meta_claims.get("answers") or []:
            if row.get("ref") not in self.book["claims"] or row["ref"] in self.answers:
                continue
            status = "invalid" if row.get("problem") else "answered"
            if status == "answered" and row["sha256"] in refused:
                status = "refused"
            elif status == "answered" and row["sha256"] in self.book["claims"][row["ref"]]["challenged"]:
                status = "challenged"
            self.answers[row["ref"]] = {"sha256": row["sha256"], "answer": row.get("answer"), "status": status,
                                        "problem": row.get("problem")}
        self.challenged_now = 0

    def answered(self, cid: str) -> bool:
        return self.answers.get(cid, {}).get("status") == "answered"

    def warnings(self) -> list[str]:
        """What the operator reads: each answer the referee could not take, and how many answers wait for a reader."""
        bad = [f"{INVALID}:{cid}" for cid, a in sorted(self.answers.items()) if a["status"] == "invalid"]
        waiting = sum(1 for cid in self.answers if self.answered(cid))
        return bad + ([f"{ANSWERED}:{waiting}"] if waiting else [])

    def challenge(self, attempts: list[dict[str, Any]]) -> None:
        """The rival sent an answered claim again (`open_claim`, `29`): it still holds it, so the answer stops counting
        and these bytes never count again for the claim."""
        for cid in sorted({a.get("open_claim") for a in attempts if a.get("open_claim")}):
            if self.answered(cid):
                row = self.book["claims"][cid]
                row["challenged"] = (row["challenged"] + [self.answers[cid]["sha256"]])[-MAX_CHALLENGED:]
                self.answers[cid]["status"] = "challenged"
                self.book["challenged"] += 1
                self.challenged_now += 1

    def overdue(self, open_ids: list[str], closing: set[str], min_attempts: int) -> list[tuple[str, int, int | None]]:
        """The claims open before this head, unanswered, not closing on it, whose age reached the window."""
        found = []
        for cid in open_ids:
            row = self.book["claims"].get(cid)
            if row is None or cid in closing or self.answered(cid):
                continue
            if row["accepted_heads"] >= min_attempts:
                found.append((cid, row["accepted_heads"], _days(row["opened_at"], self.now)))
        return found

    def _close(self, cid: str, how: str) -> None:
        row = self.book["claims"].pop(cid)
        self.book["closed"][how] += 1
        self.book["recent"] = (self.book["recent"] + [{"id": cid, "how": how, "accepted_heads": row["accepted_heads"],
                                                       "days": _days(row["opened_at"], self.now)}])[-RECENT:]

    def settle(self, final: list[dict[str, Any]], accepted: bool, observed: set[str], evicted: list[str],
               min_attempts: int) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        """The book after this head and the result's ``claims`` block. An accepted head ages every claim open before
        it (the one it closes too); closures are named by kind; a claim the cap dropped is counted apart."""
        if accepted:
            for cid in self.prior:
                if cid in self.book["claims"]:
                    self.book["claims"][cid]["accepted_heads"] += 1
        final_ids = [c["id"] for c in final]
        closed_now = []
        self.book["evicted"] += len(evicted)
        for cid in self.prior:
            if cid in final_ids or cid not in self.book["claims"]:
                continue
            if cid in evicted:
                self.book["claims"].pop(cid)
                continue
            how = "operator" if cid in self.waived else "observed" if cid in observed else "proven"
            self._close(cid, how)
            closed_now.append({"id": cid, "how": how})
        recent_ids = {r["id"] for r in self.book["recent"]}
        for cid in final_ids:
            if cid not in self.book["claims"]:
                self.book["claims"][cid] = {"accepted_heads": 0, "opened_at": self.now, "basis": "run",
                                            "challenged": []}
                if cid in recent_ids:
                    self.book["reopened"] += 1
        self.book["claims"] = {cid: self.book["claims"][cid] for cid in final_ids}
        items = []
        for cid in final_ids:
            row = self.book["claims"][cid]
            answer = self.answers.get(cid)
            status = ("answered" if self.answered(cid) else
                      "overdue" if row["accepted_heads"] >= min_attempts else "open")
            items.append({"id": cid, "status": status, "accepted_heads": row["accepted_heads"],
                          "days": _days(row["opened_at"], self.now), "basis": row["basis"],
                          "answer": None if answer is None else {k: answer[k] for k in ("sha256", "answer", "status")}})
        recent = self.book["recent"]
        days = [r["days"] for r in recent if r["days"] is not None]
        block = {
            "open": len(items),
            "answered": sum(1 for i in items if i["status"] == "answered"),
            "overdue": sum(1 for i in items if i["status"] == "overdue"),
            "closed": dict(self.book["closed"], total=sum(self.book["closed"].values())),
            "closed_now": closed_now,
            "evicted": self.book["evicted"],
            "reopened": self.book["reopened"],
            "challenged": self.book["challenged"],
            "time_to_close": {"n": len(recent),
                              "median_accepted_heads": statistics.median(r["accepted_heads"] for r in recent)
                              if recent else None,
                              "median_days": statistics.median(days) if days else None},
            "window": min_attempts,
            "items": items,
        }
        return (None if self.book == empty_book() else self.book), block


def observed_closing(open_claims: list[dict[str, Any]], state_results: list[dict[str, Any]]) -> set[str]:
    """The claims whose own reproducer ran to the end on this head and showed what it calls correct and not the symptom
    (`29`: bookkeeping, not proof). They close only if the head is accepted."""
    ids = {c["id"] for c in open_claims if c["reproducer"] is not None}
    return {s["key"] for s in state_results
            if s.get("source") == "claim" and s["key"] in ids and not s.get("timed_out") and not s.get("runner_fault")
            and not s.get("shown") and s.get("contradicted")}
