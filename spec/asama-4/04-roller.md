# Aşama 4 §4.4 — Roller

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: hedef taslak · Sahibi: operatör
Okunma: Aşama 4 çalışırken
Çapa: beklemede: aşama 4 çıkış raporu

---

| Rol | Model | Ne yapar | Ne yapamaz |
|---|---|---|---|
| Kurucu | Opus | Avcı promptunu yazar, dev setinde yineler, exit talep eder | Vaka bazlı held-out sonucunu göremez; hakem bileşenlerine yazamaz |
| Avcı | Opus, keşif basamağı | Tek ajan; snapshot içinde `Read`, `Grep`, `Glob`; her koşu soğuk | Alt ajan, yazma, ağ, önceki koşu çıktısı yok; exit'te ders yok |
| Savcı | Opus | Bulgunun gerçek olduğunu kanıtlar; avcıyla aynı taraftadır | |
| Savunma | Sonnet, ayrı bağlam | Yanlış, erişilemez ya da kasıtlı olduğunu kanıtlar; avcının promptunu görmez | Testi yazamaz |
| Uygulayıcı temsilcisi | Sonnet, ayrı bağlam | Düzeltme maliyeti, etki kümesi, katman iddiası | |
| Test-yazıcı ve oracle düzelticisi | Sonnet, Savunma'dan ayrı bağlam | `tohum/04a`; oracle düzeltmesi kanıt içindir, merge edilmez | Ders okumaz; Savunma'nın çıktısını görmez |
| Implementer | Opus | Kalıcı düzeltmeyi kök neden kuralıyla yazar (`tohum/23`) | Testi değiştiremez |
| Maliyet mühendisi | Sonnet | Merdiveni koşar | Eşik değiştiremez |
| Gözcü | Deterministik | `tohum/28` | |

Karşı koltuklar ve oracle avcıdan farklı modeldedir; ayrıklık `run_meta` ile kapıda doğrulanır
(`tohum/09a`).
