# snowball-mcp

A self-improving code-maintenance brain, delivered as an MCP server. It attaches to any
repository, in any language, keeps all repository-specific state inside that repository, and
grows its own adapters, judges, memories and agents from measured need. Every decision is closed
by execution (a test, a tool rerun, a measured harness), not by a model's opinion.

## Status

This repository currently holds the **specification** (version 2.2) a single founder agent builds
from. No brain code exists yet. Three places keep the player from grading itself:

- **Brain repository** (this one): player code, plus the referee's candidate code while Stage 0 builds it.
- **Referee repository** (private): the accepted referee. Only the operator writes it, because a
  free-plan private repository cannot carry rulesets; referee changes are imported by the operator
  at stage exits and counted as human touches.
- **Target repository**: the repository being maintained. Only the referee's writer App writes there,
  on the `brain/*` branches.

Before setup, one piece still has to be written by an author other than the founder: the bootstrap
referee under `seed/bootstrap/` (see `spec/tohum/29b-onyukleme-hakemi.md`). The founder cannot build
the judge of its own first stage.

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
