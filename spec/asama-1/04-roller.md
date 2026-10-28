# Aşama 1 §1.4 — Roller

Tarih: 2026-10-28 · Sürüm: 2.0 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 1 çalışırken
Çapa: beklemede: aşama 1 çıkış raporu

---

| Rol | Ne yapar | Ne yapamaz |
|---|---|---|
| Kurucu, Opus | Adapter'ı, düzelticiyi, dispatcher'ı, merge çağrısını yazar; döngüyü kurar | Puanlayamaz, merge edemez, eşik değiştiremez, donmuş koltukları yazamaz |
| Lint adapter | Mekanik. Snapshot'ta aracı koşar, çıktıyı bulgu şemasına çevirir (`tool`, `rule_id`, satır) | LLM çağıramaz |
| Düzeltici | Önce hedef mesajın `fix` aralığı; kalanlar için Sonnet, tek bulgu, tek dosya, izole worktree | Bulgu dışı satıra ve test yollarına yazamaz; birden fazla bulguyu tek PR'da düzeltemez |
| Rakip, Opus, ayrı bağlam | Adapter çıktısını, düzelticinin kapsam dışına taşmasını ve kapıyı çürütmeye çalışır; Sonnet üretirse rakip Opus'tur | |
| Gözcü, deterministik | `status.md` ve defterlerden eğilim; yumuşak dondurma | LLM değildir |
| Operatör | Döngü dışı | |
