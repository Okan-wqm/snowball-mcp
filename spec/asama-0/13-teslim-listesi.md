# Aşama 0 §0.13 — Teslim listesi

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: beklemede: aşama 0 çıkış raporu

---

Hakem reposunda, kurulum istisnasıyla: `harness/` (`cases.build` ve mutasyon kataloğu,
`snapshot.make`, `harness.score`, `harness.baseline` ve grep kümesi), `spec.lint`, `ledger/`
(zincir, `chain.verify`, `chain.asof`), `drift.check` iskeleti, `seats/` (tohum koltukları),
`schemas/`, kendi testleri, hakem CI'ı ve `hunt-harness.yml` içeriği.

Beyin reposunda: `cli/` (`snowball init`), `profile.propose`, `mcp/` (bu aşamanın beyin araçları,
`tohum/26a`), `tests/fixtures/toy-repo/`.

Hedef repoda (`brain/state`): `<state_root>/profile.json` (okuyucu kayıtlarıyla),
`cases/` (dev), `cost-ledger.jsonl`, `chain/root.jsonl`, `status.md` (Aşama 0 şablonu),
`docs/` ve `INDEX.md` üreticisinin ilk çıktısı.

Mühürlü depoda: held-out vakalar, `heldout.seal.json`, ilk kök hash attestation'ı.

`asama-0/` altında: tarihli çıkış raporu (taban recall ve maliyeti dahil).
