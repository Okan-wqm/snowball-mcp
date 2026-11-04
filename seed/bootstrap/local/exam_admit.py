"""The exam's admission, and the move of its answers out of the public vectors into the private store (E509).

Operator-side: it reads and writes local folders only, never a repository, a key or the network.

    cd seed/bootstrap
    python3 local/exam_admit.py migrate [--vectors vectors] [--store DIR] [--public-out DIR]
    python3 local/exam_admit.py admit --store DIR --pin HEX --vectors DIR [--public PATH ...]
    python3 local/exam_admit.py k6-summary --k6 DIR --salt HEX --referee DIR --out FILE
    python3 local/exam_admit.py kos-view --store DIR --pin HEX --out DIR

`migrate` splits the seed's vectors into the projection the referee installs as its `vectors/` (every fixture, the
inputs alone) and a new exam version in the store (`exams/<pin>/`: the manifest and the visible answers), then admits
it. These answers were public before, so the version is marked burned: a regression floor with no secrecy credit.
`admit` checks an exam version before an epoch pins it: the store opens on the pin (every byte as the manifest lists
it), the public vectors hold no answer, every slot of the inputs has exactly one answer and the answers are those of
these inputs, no public fixture carries an answer its case must compute, the canary is in no public path, and an
unburned version's answers are in none either.

`k6-summary` evaluates the K6 exam of a version being assembled on the private side (`k6.summarize`, E522): its
documents in ``--k6`` (``exam.json``, ``runs.json``, ``held_paths.json``, ``live_ready.json``, each optional), under the
version's salt, for the copy target's base and the owner's safety list in the referee checkout ``--referee``, the held
paths measured by the referee's own fence matcher. It writes the summary, the one K6 file `kos` reads, to go into the
version as ``k6/summary.json`` with that salt (`answers.write_exam(..., salt=)`). `kos-view` copies of a pinned version
the files `kos` reads (`answers.KOS_FILES` and the manifest) into ``--out``, a working copy of the repository whose read
key `kos` holds: that repository holds nothing else (`answers.kos_view`), so the key reaches no held input.

All print a JSON report and never an answer or the canary: the pin (the epoch row's `exam_sha256`), counts and
paths. Neither writes inside this repository; the store's folders and files are the owner's alone where the system
allows it. The store's default lives beside the operator's other held material, never in a repository.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable

BOOT = Path(__file__).resolve().parents[1]
ROOT = BOOT.parents[1]
if str(BOOT) not in sys.path:
    sys.path.insert(0, str(BOOT))

from snowball_bootstrap import answers, canon, config, fence, k6, vectors  # noqa: E402  (the referee's code)

DEFAULT_STORE = Path("F:/snowball-work/held/exam-store")
DEFAULT_PUBLIC = Path("F:/snowball-work/held/exam-public-vectors")


class AdmitError(Exception):
    """The migration cannot be written where it was asked to be."""


def _inside(path: Path, parent: Path) -> bool:
    path, parent = Path(path).resolve(), Path(parent).resolve()
    return path == parent or parent in path.parents


def _private(base: Path) -> None:
    """Folders 0700 and files 0600 below ``base`` (on Windows only the read-only bit exists; the folder's ACL rules)."""
    for path in [base, *base.rglob("*")]:
        os.chmod(path, 0o700 if path.is_dir() else 0o600)


def _atoms(exam: answers.Exam) -> set[str]:
    return set(vectors.answer_atoms(list(exam.answers.values())))


def _public_atoms(paths: Iterable[Path], atoms: set[str]) -> int:
    """How many shaped answers (hashes, content addresses) of the exam appear somewhere under ``paths``."""
    raw = {a.encode("utf-8") for a in atoms}
    seen: set[bytes] = set()
    for _name, data in answers.blobs(paths):
        seen |= {a for a in raw - seen if a in data}
    return len(seen)


def admit(store: Path, pin: str, vectors_dir: Path, public: Iterable[Path] = ()) -> dict[str, Any]:
    """One exam version checked against the public vectors it answers. ``admitted`` is the verdict."""
    public = [Path(p) for p in public]
    report: dict[str, Any] = {"pin": pin, "admitted": False}
    try:
        exam = answers.open_store(store, pin)
        held = answers.carrying([vectors_dir])
        if held:
            raise answers.AnswersError(f"the public vectors hold answers: {', '.join(held)}")
        inputs, _own = answers.split(json.loads((vectors_dir / vectors.SEED_FILE).read_text(encoding="utf-8")))
        answers.join(inputs, exam)
        found = vectors.fixture_lookups(vectors_dir, exam)
    except (answers.AnswersError, ValueError, OSError) as exc:
        report["refused"] = f"{type(exc).__name__}: {exc}"
        return report
    hits = answers.canary_hits([vectors_dir, *public], exam.canary)
    atoms = _public_atoms([vectors_dir, *public], _atoms(exam))
    report.update(slots=len(exam.answers), burned=exam.burned, fixture_lookups=found, canary_hits=hits,
                  public_answer_atoms=atoms)
    report["admitted"] = not found and not hits and (exam.burned or atoms == 0)
    return report


def migrate(vectors_dir: Path, store: Path, public_out: Path, *, forbidden: Iterable[Path] = (ROOT,),
            public: Iterable[Path] = ()) -> dict[str, Any]:
    """The seed's vectors as the referee's projection in ``public_out`` and a burned exam version in ``store``."""
    for out in (store, public_out):
        for place in forbidden:
            if _inside(out, place):
                raise AdmitError(f"{out} is inside {place}: the store and its projection are written outside it")
    if _inside(store, public_out) or _inside(public_out, store):
        raise AdmitError("the store and the public projection are separate folders, neither inside the other")
    if public_out.exists() and any(public_out.iterdir()):
        raise AdmitError(f"{public_out} is not empty")
    inputs, own = answers.split(json.loads((vectors_dir / vectors.SEED_FILE).read_text(encoding="utf-8")))
    if not own:
        raise AdmitError(f"{vectors_dir} holds no answer to move")
    vectors.public_vectors(vectors_dir, public_out)
    store.mkdir(parents=True, exist_ok=True)
    pin, _canary = answers.write_exam(store, inputs, own, burned=True)
    _private(store / answers.EXAMS / pin)
    report = admit(store, pin, public_out, [*public])
    report.update(store=str(store / answers.EXAMS / pin), public_vectors=str(public_out))
    return report


K6_DOCS = ("exam.json", "runs.json", "held_paths.json", "live_ready.json")  # what `k6.summarize` reads, by name


def k6_summary(k6_dir: Path, salt: str, referee: Path) -> bytes:
    """The store's ``k6/summary.json`` of the K6 documents in ``k6_dir`` under ``salt`` (64 hex), for the one copy
    target of the referee checkout ``referee`` (E522). A missing document is missing evidence, never an error."""
    def doc(name: str) -> bytes | None:
        path = Path(k6_dir) / name
        return path.read_bytes() if path.is_file() else None

    def parsed(name: str):
        raw = doc(name)
        try:
            return None if raw is None else json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            return None

    copies = [t for t in config.load_summary(Path(referee)).targets or () if t.kind == "copy"]
    copy = copies[0] if len(copies) == 1 else None
    paths = copy.safety_paths if copy is not None else None
    exam, runs, held, ready = K6_DOCS
    summary = k6.summarize(doc(exam), parsed(runs), parsed(held), parsed(ready),
                           salt=bytes.fromhex(salt), base_commit=copy.base_sha if copy is not None else None,
                           safety_paths=paths, is_safety=lambda path: bool(fence.touches_safety([path], paths or ())))
    return canon.canonical(summary) + b"\n"


def kos_view(store: Path, pin: str, out: Path) -> dict[str, Any]:
    """The files of the version ``pin`` that `kos` reads, copied from ``store`` into ``out`` at the same paths, each
    checked against the pinned manifest first; ``out`` must then hold `kos`'s view alone (`answers.kos_view`)."""
    wanted = [rel for rel in answers.KOS_FILES
              if rel in json.loads((Path(store) / answers.EXAMS / pin / answers.MANIFEST).read_bytes())["files"]]
    manifest, files = answers.read_store(Path(store), pin, wanted)
    answers.verify(manifest, files, pin)
    base = Path(out) / answers.EXAMS / pin
    for rel, content in {answers.MANIFEST: manifest, **files}.items():
        target = base / rel
        if target.exists() and target.read_bytes() != content:
            raise AdmitError(f"{target} exists with other bytes")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    names = [q.relative_to(out).as_posix() for q in Path(out).rglob("*")
             if q.is_file() and ".git" not in q.relative_to(out).parts]
    if not answers.kos_view(names):
        raise AdmitError(f"{out} holds files kos does not read: its key would reach them")
    return {"pin": pin, "files": sorted([answers.MANIFEST, *files]), "out": str(base)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    move = sub.add_parser("migrate", help="the seed's answers into a new burned exam version")
    move.add_argument("--vectors", default=str(BOOT / "vectors"))
    move.add_argument("--store", default=str(DEFAULT_STORE))
    move.add_argument("--public-out", default=str(DEFAULT_PUBLIC))
    move.add_argument("--public", action="append", default=[], help="a public path the canary must not be in")
    check = sub.add_parser("admit", help="check an exam version before an epoch pins it")
    check.add_argument("--store", required=True)
    check.add_argument("--pin", required=True)
    check.add_argument("--vectors", required=True, help="the public vectors it answers (the referee's vectors/)")
    check.add_argument("--public", action="append", default=[], help="a public path the canary must not be in")
    summ = sub.add_parser("k6-summary", help="the private K6 evaluation of a version, as the store's summary (E522)")
    summ.add_argument("--k6", required=True, help="the version's K6 documents")
    summ.add_argument("--salt", required=True, help="the version's salt (64 hex), given to write_exam too")
    summ.add_argument("--referee", required=True, help="the referee checkout (setup/summary.json)")
    summ.add_argument("--out", required=True)
    view = sub.add_parser("kos-view", help="the files kos reads of a version, for kos's own repository (E522)")
    view.add_argument("--store", required=True)
    view.add_argument("--pin", required=True)
    view.add_argument("--out", required=True, help="a working copy of the repository whose key kos holds")
    args = parser.parse_args(argv)
    try:
        if args.command == "k6-summary":
            raw = k6_summary(Path(args.k6), args.salt, Path(args.referee))
            Path(args.out).write_bytes(raw)
            print(json.dumps({"reached": json.loads(raw)["reached"], "out": args.out}))
            return 0
        if args.command == "kos-view":
            print(json.dumps(kos_view(Path(args.store), args.pin, Path(args.out)), indent=2, sort_keys=True))
            return 0
    except (AdmitError, answers.AnswersError, k6.K6Error, config.ConfigError, OSError, ValueError) as exc:
        print(json.dumps({"refused": f"{type(exc).__name__}: {exc}"}))
        return 2
    if args.command == "migrate":
        try:
            report = migrate(Path(args.vectors), Path(args.store), Path(args.public_out),
                             public=[Path(p) for p in args.public] or [ROOT])
        except AdmitError as exc:
            print(json.dumps({"refused": str(exc)}))
            return 2
    else:
        report = admit(Path(args.store), args.pin, Path(args.vectors), [Path(p) for p in args.public])
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["admitted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
