# snowball-mcp

A self-improving code-maintenance brain, delivered as an MCP server. It attaches to any
repository, in any language, keeps all repository-specific state inside that repository, and
grows its own adapters, judges, memories and agents from measured need. Every decision is closed
by execution (a test, a tool rerun, a measured harness), not by a model's opinion.

## Status

This repository currently holds the **specification** a single founder agent builds from. No
brain code exists yet; Stage 0 creates it. The system is split into a player (this brain) and a
separate referee repository (harness, gate, scoring), so the player can never grade itself.

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
  asama-0/      Stage 0: measurement harness
  asama-1/      Stage 1: first adapter (lint), simplest closed loop
  asama-4/      Stage 4: pattern-free LLM hunter for logic bugs (target draft)
```

The specification is written in Turkish, the operator's language. Everything the system itself
produces (findings, organ pages, ledgers, status reports) is in English.

## License

Proprietary. All rights reserved. No license is granted to any person or entity for any purpose,
in any jurisdiction, for any version of this work. See [`LICENSE`](LICENSE).
