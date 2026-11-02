"""The exam's admission, and the move of its answers out of the public vectors into the private store (E509).

Operator-side: it reads and writes local folders only, never a repository, a key or the network.

    cd seed/bootstrap
    python3 local/exam_admit.py migrate [--vectors vectors] [--store DIR] [--public-out DIR]
    python3 local/exam_admit.py admit --store DIR --pin HEX --vectors DIR [--public PATH ...]

`migrate` splits the seed's vectors into the projection the referee installs as its `vectors/` (every fixture, the
inputs alone) and a new exam version in the store (`exams/<pin>/`: the manifest and the visible answers), then admits
it. These answers were public before, so the version is marked burned: a regression floor with no secrecy credit.
`admit` checks an exam version before an epoch pins it: the store opens on the pin (every byte as the manifest lists
it), the public vectors hold no answer, every slot of the inputs has exactly one answer and the answers are those of
these inputs, no public fixture carries an answer its case must compute, the canary is in no public path, and an
unburned version's answers are in none either.

Both print a JSON report and never an answer or the canary: the pin (the epoch row's `exam_sha256`), counts and
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

from snowball_bootstrap import answers, vectors  # noqa: E402  (the referee's code, never a copy of it)

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
    args = parser.parse_args(argv)
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
