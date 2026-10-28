# Aşama 0 §0.3 — Roller

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: beklemede: aşama 0 çıkış raporu

---

| Rol | Var mı | Ne yapar |
|---|---|---|
| Operatör | Döngü dışı | Kurulumun birinci bölümü (`tohum/25`), bütçe, kill switch. Onay vermez |
| Kurucu, Opus | Evet, inşa zamanı | Kurulum istisnasıyla hakem reposuna harness'i, vaka üreticisini, taban avcıyı, `spec.lint`'i yazar; beyin reposuna CLI ve `profile.propose`'u yazar. Puanlayamaz |
| Tohum rakibi, Sonnet, ayrı bağlam | Evet, inşa zamanı | Promptu tohumla gelir (`tohum/29`); harness kodunu, vaka setini ve snapshot üretimini çürütmeye çalışır; denemeleri rakip defterine yazılır |
| Taban avcı | Evet, mekanik | Hakem reposunda, puanlama kodundan ayrı modül |
| LLM avcı, yargıç | Yok | |
