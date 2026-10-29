# snowball-mcp

A self-improving code-maintenance brain, delivered as an MCP server. It attaches to any
repository, in any language, keeps all repository-specific state inside that repository, and
grows its own adapters, judges, memories and agents from measured need. Every decision is closed
by execution (a test, a tool rerun, a measured harness), not by a model's opinion.

## Status

This repository currently holds the **specification** (version 2.2) a single founder agent builds
from. No brain code exists yet. Four places (the sealed store opens at Stage 4) keep the player from
grading itself:

- **Brain repository** (this one): player code, plus the referee's candidate code while Stage 0 builds it.
- **Referee repository** (public while the system is for internal use and only public targets connect,
  since its run logs are public too; private before the first private target, the sealed store or a sale): the
  accepted referee. Only the operator writes it; referee changes are imported by the operator
  at stage exits and counted as human touches.
- **Target repository**: the repository being maintained. Only the referee's writer App writes there,
  on the `brain/*` branches.
- **Sealed store** (private, from Stage 4): the held-out pool and its seal. Only the seal App writes there.

The founder cannot build the judge of its own first stage, so the **bootstrap referee** ships with
the seed under `seed/bootstrap/` (see `spec/tohum/29b-onyukleme-hakemi.md`): a GitHub Actions
workflow and a standard-library Python package that pulls each founder commit, runs its tests and
the seed vectors in network-less containers, asks a rival model to refute it, and signs the verdict
into Sigstore's Rekor log. It polls hourly; standard runners are free in a public repository, while a private one would spend about
720 of the free plan's Actions minutes a month (the arithmetic is in `spec/tohum/25-kurulum-gunu.md`). It has not yet run on
GitHub Actions; setup installs it.

Two rules run through everything:

- **Only open, commercially usable licenses.** Every dependency must carry a license on the
  allowlist in `spec/tohum/18a-politika-baslangic-degerleri.md` (MIT, BSD, Apache-2.0, ISC, PSF,
  MPL-2.0 and similar; no GPL, LGPL, AGPL, source-available or non-commercial licenses). The
  license is read from the wheel itself, every place in it that names a license must be allowed,
  and an unknown license is refused. The bootstrap applies this to the founder's dependencies and
  to its own pinned wheels before installing them (`seed/bootstrap/requirements/licenses.json`).
  The one exception is the `claude` CLI the rival runs through: a proprietary vendor tool pinned by
  `seed/bootstrap/requirements/claude-cli/package-lock.json`, outside the wheel gate (`spec/tohum/24`).
  Patterns learned from other repositories are re-written, not copied.
- **Learning and self-improvement are tested, not assumed.** Drills on a toy target, with answers
  committed in advance, check that a lesson is born from the right event, given to the right work,
  reduces errors there, is withdrawn when wrong, earns no credit when irrelevant, and survives a
  restart (`spec/tohum/22a-ders-provasi.md`); and that the system grows an organ from a measured
  gap, retires a useless one, replaces a weak one and does not grow without need
  (`spec/tohum/12a-genesis-provasi.md`; the lesson drill exists as code, the genesis drill is specified but not yet
  implemented). A stage that brings one of these capabilities cannot pass
  its exit without the drill. The lesson drill's judge is itself tested: `seed/drill/` holds a
  reference judge and simulated brains, one that learns and uses what it learned and fourteen that
  each lack one part of it. Over 500 drills each, the learner passed 498 times and was never
  failed. None of the fourteen ever passed. The founder's own judge must give the same verdicts on
  the resulting vectors (`spec/tohum/29c-prova-vektorleri.md`). These are simulated brains; whether
  the real brain learns is shown when the drill runs on it. The bootstrap also remembers its own rejections and reports `not_learning` when the
  same rejection comes back three times in a row; the Founder is specified to stop then (`spec/tohum/24`).

Run its tests with:

```
cd seed/bootstrap && PYTHONPATH=.:tests python3 -m unittest discover -s tests
cd seed/drill && python3 -m unittest discover -s tests
```

Linux is the reference platform: several tests need a POSIX shell and skip elsewhere, so on Windows run
them in a `python:3.12-slim` container with git installed. Four more checks go beyond the unit tests:

- `python3 local/e2e.py [--rival]`, run from `seed/bootstrap` (needs git, Python 3.12 and Docker), runs the whole
  referee against real containers. The brain it pushes is `local/reference_brain/`: a real, tested implementation of
  micro-feature 1 (the hash-chained ledger) that claims nothing else. It also carries reference implementations of
  micro-features 2-7, on which `tests/test_reference_brain.py` shows their seed vectors green, and red on every break
  each case is there to catch; the brain does not declare them done. With `--rival` the real rival runs through your
  own `claude` login, so it also needs Claude Code signed in; there is no API key anywhere while this system is for
  internal use.
- `python3 local/mutate.py`, run from `seed/bootstrap` on Linux, breaks the referee's code on purpose and demands that a test
  notices. A mutant that survives names behaviour no test measures.
- `python3 local/mutate_brain.py` does the same to the reference brain, so its tests cannot be the vacuous kind a
  rival refutes.
- `tests/test_live_cli.py` runs when `claude` is on `PATH`. It spends nothing (a made-up token) and fails
  when the CLI renames a flag or changes its output format.

One limit of running the rival on Windows: the MCP server's per-call deadline for a model-chosen regex uses the POSIX
interval timer, so there it does not exist and a runaway `grep` ends only at the CLI timeout. Run the rival on Linux
(or in Docker) when that matters; the referee's workflow does.

The rival's CLI is pinned in `seed/bootstrap/requirements/claude-cli/`. To move the pin, edit the version
of both packages and of `allowScripts` in `package.json` (the platform package holding the binary is a hard dependency, so that
a wrong digest fails the install instead of being skipped), regenerate the lock on Linux x64
(`docker run --rm -v <that dir>:/lock -w /lock node:22 npx -y npm@11 install --package-lock-only`), and run
`tests/test_live_cli.py`; the workflow refuses a CLI whose `--version` differs from the pin.

## Where to start

| Read | Why |
|---|---|
| [`spec/INDEX.md`](spec/INDEX.md) | Every page, when to read it, and the task-to-page map |
| [`spec/tohum/00-cekirdek.md`](spec/tohum/00-cekirdek.md) | The founder agent's core and the laws |
| [`spec/tohum/00a-sinirlar-operator-ilk-gorev.md`](spec/tohum/00a-sinirlar-operator-ilk-gorev.md) | Founder limits, the operator's role, the first task |
| [`spec/tohum/00b-gorev-haritasi.md`](spec/tohum/00b-gorev-haritasi.md) | Which pages to read for which task |
| [`spec/tohum/25-kurulum-gunu.md`](spec/tohum/25-kurulum-gunu.md), [`25a`](spec/tohum/25a-kurulum-etkinlestirme.md) | One-time operator setup: before the build, and after Stage 0 |

## Layout

```
spec/
  INDEX.md      generated index
  tohum/        seed: core, laws, protocols (one feature per dated page)
  asama-0/      Stage 0: measurement harness and the whole referee
  asama-1/      Stage 1: first adapter (lint), simplest closed loop, player organs only
  asama-4/      Stage 4: pattern-free LLM hunter for logic bugs (target draft)
seed/
  bootstrap/    the bootstrap referee: package, workflow, pinned requirements, vectors, tests
  drill/        reference judge of the lesson drill and the simulated brains that test it
```

**Why there is no Stage 2 or Stage 3 directory.** The stage protocol makes the founder draft each
stage's specification from the measured results of the stage before it, and only the next stage is
ever frozen. The seed therefore holds just the goal row of every stage (`spec/tohum/03-sinif-merdiveni.md`).
Stages 0 and 1 are written in full because they are the starting point and the trust root. Stage 4
is written as a target draft to show where the system is heading, so earlier stages know what they
must deliver. Stages 2 and 3 are drafted by the founder when Stage 1 passes.

The specification is written in Turkish, the operator's language. Everything the system itself
produces (findings, organ pages, ledgers, status reports) is in English.

## License

Proprietary. All rights reserved. No license is granted to any person or entity for any purpose,
in any jurisdiction, for any version of this work. See [`LICENSE`](LICENSE).
