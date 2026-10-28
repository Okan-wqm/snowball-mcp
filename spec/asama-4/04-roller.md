# Aşama 4 §4.4 — Roller

Tarih: 2026-10-28 · Sürüm: 2.0 · Durum: hedef taslak · Sahibi: operatör
Okunma: Aşama 4 çalışırken
Çapa: beklemede: aşama 4 çıkış raporu

---

| Rol | Model | Ne yapar | Ne yapamaz |
|---|---|---|---|
| Kurucu | Opus | Avcı promptunu yazar, dev setinde yineler, exit koşusunu talep eder | Vaka bazlı held-out sonucunu göremez; harness'e, oracle takımına, panel koltuklarına dokunamaz |
| Avcı | Opus, keşif basamağı | Tek ajan; snapshot içinde `Read`, `Grep`, `Glob`; her koşu soğuk | Alt ajan, yazma, ağ, önceki koşu çıktısı yok |
| Savcı | Opus | Bulgunun gerçek olduğunu kanıtlar | |
| Savunma | Sonnet, ayrı bağlam | Yanlış, erişilemez ya da kasıtlı olduğunu kanıtlar; avcının promptunu görmez | |
| Uygulayıcı temsilcisi | Sonnet | Düzeltme maliyeti, etki kümesi, katman iddiası | |
| Oracle takımı | Sonnet | Test-yazıcı ve düzeltici (`tohum/04a`) | Avcıyla aynı model olamaz; avcının promptunu görmez |
| Maliyet mühendisi | Sonnet | PASS'ten sonra merdiveni koşar | Eşik değiştiremez |
| Gözcü | Deterministik | Eğilim ve dondurma | |
| Operatör | — | Döngü dışı | |

İkili ayrıklık `run_meta`'da kapı tarafından doğrulanır (`tohum/09a`).
