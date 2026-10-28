# Aşama 0 §0.7 — Bulgu ve koşu şeması

Tarih: 2026-10-28 · Sürüm: 2.0 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: beklemede: aşama 0 çıkış raporu

---

İki format, tek kaynak: ajan için `findings.jsonl` satırı, insan için üretilmiş sayfa
(`tohum/15`). Alanlar İngilizcedir ve `tohum/26`'da JSON Schema olarak durur.

| Alan | Anlamı |
|---|---|
| `finding_id`, `fingerprint` | Parmak izi `property + file + symbol + normalize(claim)`; satır girmez |
| `class_level`, `property` | §0.5 |
| `tool`, `rule_id` | K0–K2 için zorunlu; K0 isabeti kural + satırdır |
| `claim` | Ürün hakkında tek cümle |
| `evidence_refs` | `[{path, line_start, line_end}]`; manifestte var olmalı; tek birincil ref ≤ 30 satır |
| `required_change` | `{file, symbol, op}`; boşsa gözlemdir, puanlanmaz |
| `severity`, `confidence`, `derivation`, `trust` | |

Gerekçe: gerçek hata, birinin değiştirmesi gereken şeydir; bir kuralın tetiklenmesi hata değildir.

`run_meta.json` alanları `tohum/26`'dadır: model istenen ve sunulan, effort, prompt hash,
basamak, maliyet, süre, okunan dosya, okunan dersler, boş `previous_run_ref`, `containment`.
