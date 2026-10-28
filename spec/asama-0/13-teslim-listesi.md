# Aşama 0 §0.13 — Teslim listesi

Tarih: 2026-10-28 · Sürüm: 2.0 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: beklemede: aşama 0 çıkış raporu

---

Beyin reposunda:

- `harness/`: `cases.build` (mutasyon kataloğu dahil), `snapshot.make`, `harness.score`,
  `harness.baseline` (grep kümesi), kendi testleri, `schemas/`.
- `cli/`: `snowball init`, `snowball harness ...`, `snowball chain verify`, `snowball docs index`.
- `mcp/`: bu aşamanın MCP araçları (`tohum/24`), `allowed_callers` ile.
- `spec-lint`: bölüm listesi, bütçe tavanı, kalıp sızıntısı, hedef repoya özgü ad denetimi.
- `tests/fixtures/toy-repo/`.
- `.github/workflows/hunt-harness.yml` şablonu: tetikler, `permissions`, `concurrency`,
  `timeout-minutes`, tam geçmiş çekimi, önbellek yolları.

Hedef repoda (`brain/state`): `<state_root>/profile.json` (okuyucu kayıtlarıyla),
`cases/` (dev), `cost-ledger.jsonl`, `chain/root.jsonl`, `status.md` (Aşama 0 şablonu),
`docs/` ve `INDEX.md` üreticisinin ilk çıktısı.

Mühürlü depoda: held-out vakalar, `heldout.seal.json`, ilk kök hash attestation'ı.

`asama-0/` altında: tarihli çıkış raporu (taban recall ve maliyeti dahil).
