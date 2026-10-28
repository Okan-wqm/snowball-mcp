# Aşama 0 — Ölçüm Zemini

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: taslak · Sahibi: operatör
Okunma: aşama başında
Çapa: beklemede: aşama 0 çıkış raporu; CI kilit kapısı (aşama 0, spec hash)

---

**Ön koşul:** kurulumun birinci bölümü tamamlanmış ve özeti mühürlü depoda (`tohum/25`).
İkinci bölüm bu aşamanın çıkışından sonra gelir (`tohum/25a`).

**Çıkış kapısı:** §0.10'daki koşulların tamamı CI'da makine doğrulamalı; verdict `PASS`.

**Yerleşim:** harness hakem reposunda, oyuncu kodu beyin reposunda, veri hedef reponun
`brain/state` dalında, held-out mühürlü depoda (`tohum/01a`, `tohum/24`). Tohum yasaları ve tüm tohum sayfaları geçerlidir.

## Sayfalar

| Sayfa | Bölüm | Satır |
|---|---|---|
| `01-amac.md` | Amaç | 17 |
| `02-dogruluk-ozellikleri.md` | Doğruluk özellikleri | 24 |
| `03-roller.md` | Roller | 15 |
| `04-hata-seti.md` | Hata seti | 38 |
| `05-property-ve-sinif-etiketleri.md` | Property ve sınıf etiketleri | 34 |
| `06-snapshot-uretimi.md` | Snapshot üretimi | 23 |
| `07-bulgu-ve-kosu-semasi.md` | Bulgu ve koşu şeması | 25 |
| `08-puanlama-ve-metrikler.md` | Puanlama ve metrikler | 28 |
| `09-harness-in-kendi-testleri.md` | Harness'in kendi testleri | 29 |
| `10-cikis-testi.md` | Çıkış testi (hepsi birlikte PASS) | 25 |
| `11-yasaklar.md` | Yasaklar | 15 |
| `12-butce.md` | Bütçe (başlangıç değerleri; yalnız operatör değiştirir) | 17 |
| `13-teslim-listesi.md` | Teslim listesi | 23 |
| `14-sirali-mikro-ozellikler.md` | Sıralı mikro özellikler | 24 |
