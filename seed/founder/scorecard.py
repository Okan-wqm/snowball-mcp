"""The self-improvement scorecard (karne, register E310): the teacher's measuring instrument, generated from the
pilot's records and never written by hand. Stdlib only. It runs on its own, never inside the launcher's loop.

    python seed/founder/scorecard.py [--work F:\\snowball-work] [--public docs/karne]

What it reads, every call a GET through the operator's `gh` login:
  - the referee's results: every `bootstrap-state` artifact of the referee repository's main branch, its zip
    checked against the digest GitHub gives for it (an artifact without one refuses the card) and kept in an
    append-only cache, <work>/scorecard/results/ (artifacts expire after 90 days; the cache keeps the card
    reproducible after that; a cached file that changed refuses the card). The referee signs each result with
    Sigstore; the card keeps the bundle but does not verify it (stdlib only): `python -m sigstore verify` does;
  - the brain's ledger at the head of the referee's last result, so the card has one record point; its hash chain
    verified with the seed's own `canon.row_hash`: a broken link or hash refuses the card;
  - `snowball-tests.json` at each judged head and base: the micro-features each push declared done;
  - <work>/pilot-metrics.jsonl and <work>/fikir-olcutu.md, opened read-only, for the private card only.

What it writes: <work>/scorecard/karne.json and karne.md, the private card (with cost and discovery), and with
--public the public card: <prefix>.json (counts, the inputs' digests, the definitions' hash) and <prefix>.md rendered
from it. The public card is counts only, from public signed inputs: no claim text, no ledger text, no idea, no name.

What it is not: proof. Improvement is shown by a controlled exam: a fixed yardstick, a counterfactual, a decision
rule written before the data and a judge independent of the student (`tohum/22a`, `22b`). The live pilot has none
of the first three (the specs, the vectors, the rival's rules and the operator's help all changed along the way), so
the card's first line says "kanıtlanmadı" until a controlled exam has a result, every measure carries its grade, and
no measure is summed into a score. Events are ordered by the referee's artifacts, never by ledger or commit times,
which the Founder's capsule writes (E316).
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import statistics
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "bootstrap"))
from snowball_bootstrap import canon  # noqa: E402  (the chain's own hash, not a copy)
from snowball_bootstrap.ledgercheck import FOUNDER_KINDS  # noqa: E402  (the kinds the seed defines)
from snowball_bootstrap.decide import counts_against_founder  # noqa: E402  (the referee's owner rule, not a copy)

STATE_ARTIFACT = "bootstrap-state"
LEDGER = "founder-ledger.jsonl"
MANIFEST = "snowball-tests.json"
RESULT_FILES = ("result.json", "result.json.sigstore.json")
EXCLUSIONS = HERE / "scorecard_exclusions.json"
GH_TIMEOUT_S = 120
ZERO = "0" * 64
MIN_N = 5  # below this many units an interval is not drawn: UNMEASURABLE (`tohum/19`)
JUDGED_KINDS = ("spec", "code", "exit")

# Every measure on the card and its grade, frozen with the card: a change here changes `definitions_sha256`, which
# the card prints and a seed test holds to the committed card. Grades: mechanical (from the referee's digest-checked
# results or hashed records), observational (mechanical, but confounded: the specs, vectors, rival and operator
# changed along the way), operator-judged (the operator's private notes), controlled (an exam with a fixed key; none
# has run).
DEFINITIONS = {
    "unit": "A micro-feature (MF). The MFs a judged push adds are done_mf at its head minus done_mf at its base (the "
            "last accepted commit), from snowball-tests.json; a push that adds none is a work push.",
    "judged_push": "A spec, code or exit push whose result says it was evaluated (state.last_evaluated_sha is its "
                   "head) with verdict accepted, frozen or rejected; outages and rival-side retries are not judged.",
    "founder_owned": "A rejection reason the referee's own rule (decide.counts_against_founder) holds against the "
                     "Founder; a push is a Founder-owned rejection when at least one of its reasons is.",
    "first_attempt": "Observational. A unit is accepted at the first attempt when the first judged push that adds it "
                     "is accepted. Referee column: every judged push; adjusted column: without the pushes and units "
                     "the exclusions file names, each with its register row, so a unit whose first attempt is a "
                     "flagged push is read at its first unflagged attempt.",
    "segment": "Seed epochs: a seed_update result opens a new segment; a unit belongs to the segment of its first "
               "attempt. Segments coincide with new vectors and rival rules, so a difference between them is not "
               "attributable to learning.",
    "interval": "Exact two-sided 95% Clopper-Pearson interval; below 5 units: UNMEASURABLE (tohum/19).",
    "proven_defects": "Mechanical. A defect the rival proved stays open, and the referee re-runs its reproducer on "
                      "every later code head until an accepted head no longer shows it; then it is closed and never "
                      "run again (state.py, E08). Counted: distinct defects re-run, re-runs, and defects that still "
                      "reproduced on a later head (refutation_still_reproduces). An open claim's reproducer proves "
                      "nothing on a later head (E260) and is not counted.",
    "retention": "UNMEASURABLE: no defect is re-run after the head that closed it, so a defect coming back in "
                 "accepted work has no record (E320).",
    "module_less": "Mechanical. Each judged push runs the tests of the MFs it adds without their module, again on "
                   "every attempt; counted: test runs, distinct MFs, runs that stayed green.",
    "repeat": "Mechanical, the referee's own count: learning.repeat_events, a rejection signature repeated on the next "
              "evaluated push. Cross-push recurrence of an error class is UNMEASURABLE: no frozen class identity.",
    "rival": "Mechanical. Rival artifacts that survived or were refuted. How much the rival finds (recall) is "
             "UNMEASURABLE until planted canaries exist (E311), so 'survived' is weak evidence.",
    "autonomy": "Mechanical. Human touches the referee's results show: seed epochs (seed_update results), waived "
                "refutations (distinct keys), unevaluated runs (outages and retries). Operator restarts and prompt "
                "changes have no record: a gap.",
    "record_point": "One moment: the referee's last result in signing order; the ledger is read at that result's "
                    "head, never at a later commit.",
    "provenance": "The referee signs each result with Sigstore; the card does not verify the signature (stdlib only; "
                  "the bundle is cached for `python -m sigstore verify`). It checks each artifact's zip against the "
                  "digest GitHub gives through the operator's gh login and refuses an artifact without one.",
    "cost": "Private. Founder USD, minutes and turns per session from pilot-metrics.jsonl (read-only); missing data is "
            "a gap, never 0. The rival's spend from the latest signed state.",
    "discovery": "Private, operator-judged. In fikir-olcutu.md: held gaps whose status cell starts with **evet** "
                 "(found by the system) over all held gaps; held ideas likewise.",
    "exam": "Controlled. The lesson drill (tohum/22a, 22b) on the real brain, judged by the reference judge; the only "
            "measure that can say 'proved'. Not run: it waits on the owner's decision (E317).",
}
DEFINITIONS_SHA256 = canon.sha256_hex(canon.canonical(DEFINITIONS))


class ScorecardError(RuntimeError):
    """The card is refused: a broken chain, a cache file that changed, a digest missing or not matching, a ledger read
    at another head than the last result's, a failed read."""


class NotFound(ScorecardError):
    """A path GitHub answers with 404 (a commit with no test manifest)."""


Get = Callable[[str, bool], bytes]


def gh_get(path: str, raw: bool = False) -> bytes:
    """One read through the operator's gh login: always GET, never a field or a body."""
    argv = ["gh", "api", "--method", "GET", *(["-H", "Accept: application/vnd.github.raw"] if raw else []), path]
    try:
        proc = subprocess.run(argv, capture_output=True, timeout=GH_TIMEOUT_S, check=False)
    except subprocess.TimeoutExpired as exc:
        raise ScorecardError(f"gh api {path}: timed out") from exc
    if proc.returncode != 0:
        err = proc.stderr.decode(errors="replace").strip()[-300:]
        raise (NotFound if "HTTP 404" in err else ScorecardError)(f"gh api {path}: {err}")
    return proc.stdout


# ---- inputs -------------------------------------------------------------------------------------------------------
def verify_chain(text: str) -> list[dict[str, Any]]:
    """The ledger's rows, each linked to the one before and hashed as the seed hashes it; anything else refuses."""
    rows: list[dict[str, Any]] = []
    prev = ZERO
    for n, line in enumerate(text.splitlines(), start=1):
        try:
            row = json.loads(line)
            ok = isinstance(row, dict) and row.get("prev_hash") == prev
            if ok and canon.row_hash(row) != row.get("row_hash"):
                raise ScorecardError(f"{LEDGER} line {n}: row_hash does not match the row")
        except (ValueError, canon.CanonicalError) as exc:
            raise ScorecardError(f"{LEDGER} line {n}: unreadable ({exc})") from exc
        if not ok:
            raise ScorecardError(f"{LEDGER} line {n}: prev_hash does not link to the row before")
        rows.append(row)
        prev = row["row_hash"]
    return rows


def done_mf(raw: bytes | None) -> list[int]:
    """The micro-features a manifest declares done; none when it is absent or unreadable, as the referee reads a base
    (`cli._base_done`)."""
    try:
        data = json.loads(raw.decode("utf-8")) if raw is not None else {}
        return sorted({int(k) for k in data.get("done_mf", []) if isinstance(k, int) and not isinstance(k, bool)})
    except (ValueError, AttributeError, TypeError):
        return []


class Cache:
    """<work>/scorecard: the signed results (append-only, digest-checked) and the manifests read at each commit."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.results = root / "results"
        self.index = self.results / "index.jsonl"
        self.manifests = root / "manifests.jsonl"

    def entries(self) -> dict[int, dict[str, Any]]:
        out: dict[int, dict[str, Any]] = {}
        lines = self.index.read_text(encoding="utf-8").splitlines() if self.index.is_file() else []
        for line in lines:
            entry = json.loads(line)
            if entry["artifact_id"] in out:
                raise ScorecardError(f"cache index names artifact {entry['artifact_id']} twice")
            for name, digest in entry["files"].items():
                path = self.results / str(entry["artifact_id"]) / name
                if not path.is_file() or canon.sha256_file(str(path)) != digest:
                    raise ScorecardError(f"cache: {path} is missing or changed since it was cached")
            out[entry["artifact_id"]] = entry
        return out

    def add(self, art: dict[str, Any], blob: bytes) -> dict[str, Any]:
        digest = art.get("digest")  # no digest is no check: refused like a wrong one, never cached unchecked
        if digest != "sha256:" + hashlib.sha256(blob).hexdigest():
            raise ScorecardError(f"artifact {art['id']}: the zip does not match the digest GitHub gives for it "
                                 f"({digest or 'none given'})")
        folder = self.results / str(art["id"])
        folder.mkdir(parents=True, exist_ok=True)
        files = {}
        with zipfile.ZipFile(io.BytesIO(blob)) as zf:
            for name in RESULT_FILES:
                if name in zf.namelist():
                    data = zf.read(name)
                    (folder / name).write_bytes(data)
                    files[name] = hashlib.sha256(data).hexdigest()
        run = art.get("workflow_run") or {}
        entry = {"artifact_id": art["id"], "digest": digest, "created_at": art["created_at"],
                 "run_id": run.get("id"), "head_sha": run.get("head_sha"), "files": files}
        with self.index.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(entry, sort_keys=True) + "\n")
        return entry

    def manifest_cache(self) -> dict[str, list[int]]:
        lines = self.manifests.read_text(encoding="utf-8").splitlines() if self.manifests.is_file() else []
        return {d["sha"]: d["done_mf"] for d in map(json.loads, lines)}

    def add_manifest(self, sha: str, done: list[int]) -> None:
        with self.manifests.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps({"sha": sha, "done_mf": done}, sort_keys=True) + "\n")


def _signed_order(item: dict[str, Any]) -> tuple[str, int, int]:
    """The referee's order: its artifacts' creation time, then run and artifact id (never ledger or commit times,
    which the Founder's capsule writes, E316)."""
    art = item["artifact"]
    return art["created_at"], int(art["run_id"] or 0), art["artifact_id"]


def _artifacts(referee: str, get: Get) -> list[dict[str, Any]]:
    out, page = [], 1
    while True:
        listing = json.loads(get(f"repos/{referee}/actions/artifacts?name={STATE_ARTIFACT}&per_page=100&page={page}",
                                 False))
        arts = listing.get("artifacts", [])
        out += [a for a in arts if (a.get("workflow_run") or {}).get("head_branch") == "main"]
        if len(arts) < 100:
            return out
        page += 1


def read_ideas(text: str | None) -> dict[str, Any] | None:
    """Counts from the operator's private idea sheet: rows of its "Fikir" and "Boşluk" tables, and how many of them
    have a status cell starting with **evet** (the system found or proposed it). Nothing else of the sheet is kept."""
    if text is None:
        return None
    counts = {"ideas": [0, 0], "gaps": [0, 0]}
    table = None
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")] if line.startswith("|") else None
        if cells is None:
            table = None
        elif table is None:
            table = "ideas" if "Fikir" in cells else "gaps" if "Boşluk" in cells else "other"
        elif table != "other" and not set(cells[0]) <= set("-: "):
            status = cells[-1] if table == "ideas" else cells[1] if len(cells) > 1 else ""
            counts[table][0] += status.startswith("**evet**")
            counts[table][1] += 1
    return {"ideas_proposed": counts["ideas"][0], "ideas_held": counts["ideas"][1],
            "gaps_found": counts["gaps"][0], "gaps_held": counts["gaps"][1]}


def fetch(work: Path, brain: str, referee: str, get: Get = gh_get) -> dict[str, Any]:
    """Everything the card is built from. Writes only under <work>/scorecard; the metrics and the idea sheet are
    opened read-only."""
    cache = Cache(work / "scorecard")
    cache.results.mkdir(parents=True, exist_ok=True)
    entries = cache.entries()
    gaps = []
    for art in _artifacts(referee, get):
        if art["id"] in entries:
            continue
        if art.get("expired"):
            gaps.append(f"artefakt {art['id']} önbelleğe alınmadan süresi doldu")
            continue
        entries[art["id"]] = cache.add(art, get(f"repos/{referee}/actions/artifacts/{art['id']}/zip", False))
    results = []
    for aid, entry in sorted(entries.items()):
        if "result.json" not in entry["files"]:
            gaps.append(f"artefakt {aid} `result.json` taşımıyor")
            continue
        result = json.loads((cache.results / str(aid) / "result.json").read_text(encoding="utf-8"))
        results.append({"artifact": entry, "result": result})
    if not results:
        raise ScorecardError("the referee has no result yet: nothing to count")
    # One record point: the ledger as it was at the head of the referee's last result, not at the brain's main,
    # which may have moved past every judged head.
    ledger_at = str(max(results, key=_signed_order)["result"].get("head"))
    ledger = get(f"repos/{brain}/contents/{LEDGER}?ref={ledger_at}", True).decode("utf-8")
    known = cache.manifest_cache()
    for item in results:
        r = item["result"]
        for sha in (r.get("head"), r.get("base")) if r.get("kind") in JUDGED_KINDS else ():
            if sha and sha not in known:
                try:
                    known[sha] = done_mf(get(f"repos/{brain}/contents/{MANIFEST}?ref={sha}", True))
                except NotFound:
                    known[sha] = []
                cache.add_manifest(sha, known[sha])
    metrics_path, ideas_path = work / "pilot-metrics.jsonl", work / "fikir-olcutu.md"
    metrics = None
    if metrics_path.is_file():
        with metrics_path.open("r", encoding="utf-8") as fh:
            metrics = [json.loads(line) for line in fh if line.strip()]
    ideas = None
    if ideas_path.is_file():
        with ideas_path.open("r", encoding="utf-8") as fh:
            ideas = fh.read()
    return {"results": results, "ledger_at": ledger_at, "ledger": ledger, "manifests": known,
            "metrics": metrics, "ideas": ideas, "exclusions": json.loads(EXCLUSIONS.read_text(encoding="utf-8")),
            "gaps": gaps}


# ---- statistics ---------------------------------------------------------------------------------------------------
def _tail_ge(x: int, n: int, p: float) -> float:
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(x, n + 1))


def _bisect(f: Callable[[float], float]) -> float:
    lo, hi = 0.0, 1.0  # f increases from negative to positive on [0, 1]
    for _ in range(100):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if f(mid) < 0 else (lo, mid)
    return (lo + hi) / 2


def clopper_pearson(x: int, n: int) -> tuple[float, float]:
    """Exact two-sided 95% interval for x successes in n (`tohum/19`: 3/5 gives 0.15 to 0.95)."""
    if n <= 0 or not 0 <= x <= n:
        raise ValueError("need 0 <= x <= n and n > 0")
    lo = 0.0 if x == 0 else _bisect(lambda p: _tail_ge(x, n, p) - 0.025)
    hi = 1.0 if x == n else _bisect(lambda p: 0.025 - (1 - _tail_ge(x + 1, n, p)))
    return lo, hi


def share(x: int, n: int) -> dict[str, Any]:
    out: dict[str, Any] = {"x": x, "n": n}
    if n < MIN_N:
        out["verdict"] = "UNMEASURABLE"
    else:
        lo, hi = clopper_pearson(x, n)
        out["ci95"] = [f"{lo:.2f}", f"{hi:.2f}"]
    return out


# ---- the model (pure) ---------------------------------------------------------------------------------------------
def _founder_owned(reasons: list[dict[str, Any]]) -> bool:
    return any(counts_against_founder({"kind": str(r.get("kind", "")), "ref": str(r.get("ref") or "")}) for r in reasons)


def build(inputs: dict[str, Any]) -> dict[str, Any]:
    """The card's model from its inputs: deterministic, no clock, no network. ``public`` holds what may be published."""
    rows = verify_chain(inputs["ledger"])
    manifests = inputs["manifests"]
    excl = inputs["exclusions"]["entries"]
    excluded_heads = {e["head"]: e["id"] for e in excl if "head" in e}
    excluded_units = {e["unit"]: e["id"] for e in excl if "unit" in e}
    items = sorted(inputs["results"], key=_signed_order)
    if not items or inputs["ledger_at"] != items[-1]["result"].get("head"):
        raise ScorecardError("the ledger was not read at the head of the referee's last result: two record points")
    segment, repeats_prev = 0, 0
    pushes: list[dict[str, Any]] = []
    unevaluated = seed_epochs = rival_retries = 0
    waived: set[str] = set()
    defects: set[str] = set()  # proven defects the referee re-ran, by key
    again: dict[str, bool] = {}  # defects that still reproduced on a later head -> on an unflagged one too
    reruns = module_runs = module_green = 0
    module_mfs: set[int] = set()
    repeat = {"events": 0, "events_adjusted": 0, "not_learning_runs": 0}
    for item in items:
        r = item["result"]
        kind, head = r.get("kind"), r.get("head")
        waived |= set(r.get("waived") or [])
        rival_retries += sum(1 for w in r.get("warnings") or [] if str(w).startswith("rival_side_retry"))
        if kind == "seed_update":
            seed_epochs += 1
            segment += 1
            continue
        if kind not in JUDGED_KINDS:
            continue
        evaluated = (r.get("state") or {}).get("last_evaluated_sha") == head
        if not evaluated:
            unevaluated += 1
            continue
        flag = excluded_heads.get(head)
        reps = (r.get("learning") or {}).get("repeat_events", repeats_prev)
        repeat["events"] += reps - repeats_prev
        repeat["events_adjusted"] += 0 if flag else reps - repeats_prev
        repeats_prev = reps
        repeat["not_learning_runs"] += bool((r.get("learning") or {}).get("not_learning"))
        # An open claim's reproducer (source claim) proves nothing on a later head (E260): only proven defects count.
        rerun = [str(s.get("key")) for s in r.get("state_reproducers") or [] if s.get("source") == "refutation"]
        reruns += len(rerun)
        defects.update(rerun)
        for x in r.get("reasons") or []:
            if x.get("kind") == "refutation_still_reproduces":
                again[str(x.get("ref"))] = again.get(str(x.get("ref")), False) or not flag
        checks = r.get("module_less") or []
        module_runs += len(checks)
        module_mfs.update(int(m["mf"]) for m in checks if isinstance(m.get("mf"), int))
        module_green += sum(1 for m in checks if m.get("stayed_green"))
        new = sorted(set(manifests.get(head, [])) - set(manifests.get(r.get("base"), []))) if kind != "spec" else []
        pushes.append({"head": head, "kind": kind, "segment": segment,
                       "verdict": r.get("verdict"), "founder_owned": _founder_owned(r.get("reasons") or []),
                       "new_mf": new, "flag": flag})
    units: dict[int, dict[str, Any]] = {}
    for p in pushes:
        for mf in p["new_mf"]:
            u = units.setdefault(mf, {"mf": mf, "segment": p["segment"], "attempts": [], "accepted": False})
            if not u["accepted"]:
                u["attempts"].append(p)
                u["accepted"] = p["verdict"] == "accepted"
    unit_rows = []
    for mf, u in sorted(units.items()):
        kept = [a for a in u["attempts"] if not a["flag"]]
        flags = sorted({a["flag"] for a in u["attempts"] if a["flag"]} | ({excluded_units[f"MF{mf}"]}
                                                                         if f"MF{mf}" in excluded_units else set()))
        unit_rows.append({
            "mf": mf, "segment": u["segment"], "attempts": len(u["attempts"]), "accepted": u["accepted"],
            "founder_rejections": sum(1 for a in u["attempts"] if a["verdict"] == "rejected" and a["founder_owned"]),
            "other_rejections": sum(1 for a in u["attempts"] if a["verdict"] == "rejected" and not a["founder_owned"]),
            "first": u["attempts"][0]["verdict"] == "accepted",
            "first_adjusted": None if f"MF{mf}" in excluded_units or not kept else kept[0]["verdict"] == "accepted",
            "heads": [a["head"][:7] for a in u["attempts"]], "flags": flags})

    def first_share(rows_: list[dict[str, Any]], col: str) -> dict[str, Any]:
        counted = [u for u in rows_ if u[col] is not None]
        return share(sum(1 for u in counted if u[col]), len(counted))

    segments = sorted({u["segment"] for u in unit_rows})
    code = [p for p in pushes if p["kind"] != "spec"]
    latest = items[-1]["result"].get("state") or {}
    rival_arts = latest.get("rival_artifacts") or []
    public = {
        "schema": "snowball-karne/2",
        "definitions_sha256": DEFINITIONS_SHA256,
        "as_of": {"results": len(items),
                  "last_run": {"run_id": str(items[-1]["artifact"]["run_id"]),
                               "created_at": items[-1]["artifact"]["created_at"],
                               "head": items[-1]["result"].get("head")},
                  # the ledger as it was at last_run.head (record_point)
                  "ledger_rows": len(rows),
                  "ledger_tip": {"row_id": rows[-1]["row_id"], "row_hash": rows[-1]["row_hash"]} if rows else None,
                  "ledger_sha256": canon.sha256_hex(inputs["ledger"].encode("utf-8"))},
        "inputs": {"artifacts": [{"artifact_id": i["artifact"]["artifact_id"], "digest": i["artifact"]["digest"],
                                  "run_id": str(i["artifact"]["run_id"]),
                                  "result_sha256": i["artifact"]["files"]["result.json"]} for i in items],
                   "exclusions": [{"id": e["id"], "on": e.get("head", e.get("unit"))} for e in excl]},
        "gaps": sorted(inputs["gaps"] + ["operatörün yeniden başlatmaları ve talimat değişiklikleri kaydedilmiyor"]),
        # Kinds outside the seed's set are counted together: a free-text kind is never published.
        "ledger_kinds": dict(sorted(_count(k if k in FOUNDER_KINDS else "diğer"
                                           for k in (str(r.get("kind")) for r in rows)).items())),
        "units": unit_rows,
        "first_attempt": {
            "all": {"referee": first_share(unit_rows, "first"), "adjusted": first_share(unit_rows, "first_adjusted")},
            "segments": [{"segment": s,
                          "referee": first_share([u for u in unit_rows if u["segment"] == s], "first"),
                          "adjusted": first_share([u for u in unit_rows if u["segment"] == s], "first_adjusted")}
                         for s in segments]},
        "pushes": {"judged": len(pushes), "by_kind": dict(sorted(_count(p["kind"] for p in pushes).items())),
                   "work_pushes": sum(1 for p in code if not p["new_mf"]),
                   "founder_rejected": {"referee": share(sum(p["founder_owned"] and p["verdict"] == "rejected"
                                                             for p in code), len(code)),
                                        "adjusted": share(sum(p["founder_owned"] and p["verdict"] == "rejected"
                                                              for p in code if not p["flag"]),
                                                          sum(1 for p in code if not p["flag"]))}},
        "proven_defects": {"defects": len(defects), "reruns": reruns, "reproduced_again": len(again),
                           "reproduced_again_adjusted": sum(again.values()), "retention": "UNMEASURABLE"},
        "module_less": {"runs": module_runs, "mfs": len(module_mfs), "green": module_green},
        "repeat": repeat,
        "rival": {"survived": sum(1 for a in rival_arts if a.get("outcome") == "survived"),
                  "refuted": sum(1 for a in rival_arts if a.get("outcome") == "refuted"),
                  "open_refutations": len(latest.get("open_refutations") or []),
                  "open_claims": len(latest.get("open_claims") or []), "recall": "UNMEASURABLE"},
        "autonomy": {"seed_epochs": seed_epochs, "waived_refutations": len(waived), "unevaluated_runs": unevaluated,
                     "rival_side_retries": rival_retries},
        "exam": {"status": "not_run", "register": "E317"},
    }
    return {"public": public, "private": _private(inputs, unit_rows, latest)}


def _count(values: Any) -> dict[str, int]:
    out: dict[str, int] = {}
    for v in values:
        out[v] = out.get(v, 0) + 1
    return out


def _private(inputs: dict[str, Any], units: list[dict[str, Any]], latest: dict[str, Any]) -> dict[str, Any]:
    metrics = inputs["metrics"]
    cost: dict[str, Any] = {"rival_usd": f"{int(latest.get('stage_spend_usd_micros', 0)) / 1e6:.2f}"}
    if metrics is None:
        cost["founder"] = "GAP: pilot-metrics.jsonl not read"
    else:
        usd = [float(m["cost_usd"]) for m in metrics if isinstance(m.get("cost_usd"), (int, float))]
        minutes = [float(m["minutes"]) for m in metrics if isinstance(m.get("minutes"), (int, float))]
        accepted = sum(1 for u in units if u["accepted"])
        cost["founder"] = {"sessions": len(metrics), "sessions_without_cost": len(metrics) - len(usd),
                           "usd_total": f"{sum(usd):.2f}", "usd_median": f"{statistics.median(usd):.2f}" if usd else None,
                           "minutes_total": f"{sum(minutes):.1f}", "accepted_units": accepted,
                           "first_stamp": min((str(m.get("stamp")) for m in metrics), default=None)}
    return {"cost": cost, "discovery": read_ideas(inputs["ideas"])}


# ---- rendering ----------------------------------------------------------------------------------------------------
def _num(text: str) -> str:
    return text.replace(".", ",")


def _share_text(s: dict[str, Any]) -> str:
    if s["n"] == 0:
        return "—"
    if "ci95" in s:
        return f"{s['x']}/{s['n']} ({_num(s['ci95'][0])}–{_num(s['ci95'][1])})"
    return f"{s['x']}/{s['n']} (ölçülemez: n < {MIN_N})"


def _verbs(m: dict[str, Any]) -> tuple[tuple[str, str, str], ...]:
    """The owner's MVP sentence verb by verb: what the pilot shows, and its grade; only the exam can say more."""
    fa, pd, ml, rp = m["first_attempt"]["all"], m["proven_defects"], m["module_less"], m["repeat"]
    return (
        ("öğrenir", f"aynı ret imzasının art arda tekrarı (`repeat_events`) {rp['events']}, düzeltilmiş "
                    f"{rp['events_adjusted']}; rakibin kanıtladığı {pd['defects']} ayrı kusurdan sonraki bir başta "
                    f"yeniden üretilen {pd['reproduced_again']}, düzeltilmiş {pd['reproduced_again_adjusted']} "
                    "(kusur yalnız kapanana kadar izlenir)", "mekanik"),
        ("öğrendiğini uygular", f"ilk denemede kabul {_share_text(fa['referee'])}, düzeltilmiş "
                                f"{_share_text(fa['adjusted'])}; dönemlere göre aşağıda", "gözlemsel"),
        ("yanlışı yanlış bilir", "kendi hatasını kendisinin bulduğunun doğrulanmış kaydı yok (E315)", "ölçülemez"),
        ("doğruyu doğru bilir", "yanlış kararda doğru kodu korumak: mekanik kaydı yok", "ölçülemez"),
        ("tartar", "derslerin kredisi ve sıralaması: Aşama 0'da ders organı yok", "ölçülemez"),
        ("test eder ve uygular", f"{ml['mfs']} MF'nin testleri modülü olmadan koşuldu: {ml['runs']} test koşusu "
                                 f"(her denemede yeniden), yeşil kalan {ml['green']}", "mekanik"),
    )


def render_public(m: dict[str, Any]) -> str:
    a = m["as_of"]
    fa, pu, pd, ml, rp, rv, au = (m["first_attempt"], m["pushes"], m["proven_defects"], m["module_less"],
                                  m["repeat"], m["rival"], m["autonomy"])
    tip = a["ledger_tip"] or {"row_id": "—", "row_hash": "—"}
    last = a["last_run"]
    proved = "evet" if m["exam"]["status"] == "pass" else "hayır"
    out = [
        "# Karne: Kendini Geliştirmenin Ölçüsü",
        "",
        f"Üretilmiş sayfa; elle düzenlenmez (`python seed/founder/scorecard.py --public docs/karne`, E310). "
        f"Kaynak: `docs/karne.json`. Tanımlar: `{m['definitions_sha256'][:16]}`.",
        "",
        f"**Kendini geliştirdiği kanıtlandı mı: {proved}.** Kanıtı yalnız kontrollü sınav verir (ders provası, "
        f"`tohum/22a`, `22b`); sınav koşmadı ({m['exam']['register']}). Aşağıdaki her sayı canlı pilotun "
        "gözlemidir: spec, vektörler, rakibin kuralları ve operatörün yardımı yol boyunca değişti; puan "
        "toplanmaz, her ölçü kendi derecesiyle okunur.",
        "",
        "## Kayıt noktası",
        "",
        "Tek an: hakemin son sonucu. Defter o sonucun başında okunur, beynin sonraki commit'lerinde değil.",
        "",
        "| Ne | Değer |",
        "|---|---|",
        f"| Hakemin son sonucu | koşu {last['run_id']}, {last['created_at']}, baş `{str(last['head'])[:12]}` |",
        f"| Kurucu defteri, o başta | {a['ledger_rows']} satır, zincir doğrulandı; uç `{tip['row_id']}` "
        f"`{tip['row_hash'][:16]}` |",
        f"| Hakemin sonuçları | {a['results']}; hakem her birini Sigstore'la imzalar, karne imzayı doğrulamaz: "
        "her artefaktın zip'i GitHub'ın verdiği özetle denetlenir, özetsiz artefakt karneyi reddeder |",
        f"| Veri boşlukları | {len(m['gaps'])}: " + "; ".join(m["gaps"]) + " |",
        "",
        "## Fiil fiil",
        "",
        "| Sahibin fiili | Kontrollü sınav | Pilotun gözlemi | Derece |",
        "|---|---|---|---|",
    ]
    out += [f"| {verb} | koşmadı | {seen} | {grade} |" for verb, seen, grade in _verbs(m)]
    out += [
        "",
        "## Birimler (MF)",
        "",
        "Bir MF'nin denemeleri, onu ilk ekleyen yargılanmış push'tan kabul edilene kadarki push'lardır. Ret sahibi "
        "hakemin kendi kuralıdır (`counts_against_founder`). İşaretli push ve birimler düzeltilmiş sütunda yoktur: "
        "ilk denemesi işaretli push olan birim ilk işaretsiz denemesiyle okunur, hiç işaretsiz denemesi yoksa "
        "sayılmaz. Her işaret kayıttaki satırıdır.",
        "",
        "| MF | Dönem | Deneme | Kurucu'nun reddi | Başka ret | İlk denemede | Düzeltilmiş | İşaret | Başlar |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    yes = {True: "evet", False: "hayır", None: "—"}
    for u in m["units"]:
        out.append(f"| MF{u['mf']} | {u['segment']} | {u['attempts']}{'' if u['accepted'] else ' (açık)'} | "
                   f"{u['founder_rejections']} | {u['other_rejections']} | {yes[u['first']]} | "
                   f"{yes[u['first_adjusted']]} | {', '.join(u['flags']) or '—'} | "
                   f"{' '.join('`' + h + '`' for h in u['heads'])} |")
    out += [
        "",
        "## İlk denemede kabul (gözlemsel)",
        "",
        "Dönemler tohum dönemleridir: her dönem yeni vektörler ve rakip kuralları getirdi, bu yüzden dönemler arası "
        "fark öğrenmeye bağlanamaz. Aralık tam iki yönlü %95 Clopper–Pearson'dur.",
        "",
        "| Dönem | Hakemin kuralı | Düzeltilmiş |",
        "|---|---|---|",
    ]
    for s in fa["segments"]:
        out.append(f"| {s['segment']} | {_share_text(s['referee'])} | {_share_text(s['adjusted'])} |")
    out.append(f"| hepsi | {_share_text(fa['all']['referee'])} | {_share_text(fa['all']['adjusted'])} |")
    fr = pu["founder_rejected"]
    out += [
        "",
        "## Push'lar, kanıtlanmış kusurlar, tekrar",
        "",
        "Rakibin kanıtladığı kusur, onu artık göstermeyen ilk kabul edilmiş başa kadar her kod başında yeniden "
        "koşulur, sonra kapanır ve bir daha koşulmaz (E08). Kabul edilen başta kusur yeniden üretilemez (o baş "
        "reddedilirdi); kabulden sonra geri dönüp dönmediği hiçbir kayıtta yoktur.",
        "",
        "| Ölçü | Hakemin kuralı | Düzeltilmiş |",
        "|---|---|---|",
        f"| Yargılanan push (spec, kod, çıkış) | {pu['judged']} "
        f"({', '.join(f'{k} {v}' for k, v in pu['by_kind'].items())}) | |",
        f"| MF eklemeyen kod push'u | {pu['work_pushes']} | |",
        f"| Kurucu'nun reddettirdiği kod push'u | {_share_text(fr['referee'])} | {_share_text(fr['adjusted'])} |",
        f"| Kanıtlanmış kusur, kapanana kadar yeniden koşulan: ayrı kusur / koşu | {pd['defects']} / {pd['reruns']} "
        "| |",
        f"| ... sonraki bir başta yeniden üretilen ayrı kusur | {pd['reproduced_again']} "
        f"| {pd['reproduced_again_adjusted']} |",
        "| Kalıcılık: kabul edilmiş işte kapanmış kusurun geri dönmesi | ölçülemez: kapanan kusur bir daha koşulmaz "
        "(E320) | |",
        f"| Modülü olmadan koşulan test: koşu / MF / yeşil kalan | {ml['runs']} / {ml['mfs']} / {ml['green']} | |",
        f"| Tekrar eden ret imzası (`repeat_events`) | {rp['events']} | {rp['events_adjusted']} |",
        f"| `not_learning` diyen koşu | {rp['not_learning_runs']} | |",
        "| Hata sınıfının push'lar arası tekrarı | ölçülemez: donmuş sınıf kimliği yok (E70) | |",
        "",
        "## Rakip ve insan dokunuşu",
        "",
        "| Ölçü | Değer |",
        "|---|---|",
        f"| Rakibin incelediği artefakt: hayatta kalan / çürütülen | {rv['survived']} / {rv['refuted']} |",
        f"| Açık kanıtlanmış kusur / açık iddia (son durum) | {rv['open_refutations']} / {rv['open_claims']} |",
        "| Rakibin bulma gücü (recall) | ölçülemez: ekilmiş kanarya yok (E311); \"hayatta kaldı\" zayıf kanıttır |",
        f"| Tohum dönemi (`seed_update`) | {au['seed_epochs']} |",
        f"| Feragat edilen çürütme | {au['waived_refutations']} |",
        f"| Değerlendirilmeyen koşu (kesinti, yeniden inceleme) | {au['unevaluated_runs']} |",
        f"| Rakip tarafı yeniden inceleme uyarısı | {au['rival_side_retries']} |",
        "",
        "## Defter",
        "",
        "Satır türleri (Kurucu'nun kendi beyanı; içerik okunmaz): "
        + ", ".join(f"`{k}` {v}" for k, v in m["ledger_kinds"].items()) + ".",
        "",
        "## Girdiler",
        "",
        f"Hakemin {len(m['inputs']['artifacts'])} sonucu; her birinin artefakt özeti ve `result.json` hash'i "
        "`docs/karne.json`'dadır, herkes aynı girdilerden aynı sayfayı üretir (artefaktlar 90 gün yaşar; operatörün "
        "önbelleği onları ve Sigstore paketlerini tutar, `python -m sigstore verify` ile doğrulanır). İşaretler: " + ", ".join(f"{e['id']} (`{e['on'][:7] if len(e['on']) == 40 else e['on']}`)"
                                                     for e in m["inputs"]["exclusions"]) + ".",
        "",
    ]
    return "\n".join(out)


def render_private(model: dict[str, Any]) -> str:
    p = model["private"]
    lines = [render_public(model["public"]).rstrip("\n"), "", "## Yalnız operatör: maliyet ve keşif", "",
             "```json", json.dumps(p, indent=2, ensure_ascii=False, sort_keys=True), "```", ""]
    return "\n".join(lines)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def update(work: Path, brain: str, referee: str, public: Path | None = None, get: Get = gh_get) -> dict[str, Any]:
    """Fetch, build and write the private card under <work>/scorecard, and the public card when asked."""
    model = build(fetch(work, brain, referee, get))
    _write(work / "scorecard" / "karne.json", json.dumps(model, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    _write(work / "scorecard" / "karne.md", render_private(model))
    if public is not None:
        _write(public.with_suffix(".json"), json.dumps(model["public"], indent=2, ensure_ascii=False,
                                                       sort_keys=True) + "\n")
        _write(public.with_suffix(".md"), render_public(model["public"]))
    return model


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--work", type=Path, default=Path(r"F:\snowball-work"))
    p.add_argument("--brain", default="Okan-wqm/snowball-rehearsal-brain")
    p.add_argument("--referee", default="Okan-wqm/snowball-rehearsal-referee")
    p.add_argument("--public", type=Path, help="also write the public card, e.g. docs/karne (.json and .md)")
    args = p.parse_args(argv)
    try:
        model = update(args.work, args.brain, args.referee, args.public)
    except ScorecardError as exc:
        print(f"no card: {exc}", file=sys.stderr)
        return 1
    print(f"card written: {model['public']['as_of']['results']} referee results, "
          f"{model['public']['as_of']['ledger_rows']} ledger rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
