# Aşama 1 §1.4 — Roller

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 1 çalışırken
Çapa: beklemede: aşama 1 çıkış raporu

---

| Rol | Ne yapar | Ne yapamaz |
|---|---|---|
| Kurucu, Opus | Oyuncu organlarını yazar: lint adapter, düzeltici, `map.build`, `docs.render`. Kurulum istisnasıyla hakem reposuna dispatcher, itibar puanlayıcısı, Gözcü, oracle koşucusu, kapı ve nöbetçinin ilk sürümlerini yazar | Puanlayamaz, merge edemez, eşik değiştiremez; aşama çıkışından sonra hakem bileşenlerine yazamaz |
| Lint adapter | Mekanik; aracı koşar, çıktıyı bulgu şemasına çevirir | LLM çağıramaz |
| Düzeltici | Önce hedef mesajın `fix` aralığı; kalanlar için Sonnet, tek bulgu, izole worktree; ders okur | Bulgu dışı satıra ve test yollarına yazamaz |
| Tohum rakibi, Sonnet, ayrı bağlam | Kurucu'nun Opus ile yazdığı her şeyi çürütmeye çalışır; Sonnet'in yazdığı düzeltmeyi Opus rakip denetler | |
| Gözcü, deterministik | `tohum/28` kuralları | LLM değildir |
| Operatör | Döngü dışı | |
