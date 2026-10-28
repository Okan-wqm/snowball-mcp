# Aşama 1 §1.11 — Sonuç ne söyler

Tarih: 2026-10-28 · Sürüm: 2.0 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 1 çalışırken
Çapa: beklemede: aşama 1 çıkış raporu

---

- **PASS:** döngü kapanıyor, her organın okuyucusu var, kapı çalışıyor, maliyet tabanı yazılı.
  Aşama 2 aynı döngüye K1 ve K2 adapter'larını ve planlayıcıyı ekler; döngüye dokunmaz.
- **FAIL, recall düşük:** adapter aracı yanlış sarıyor; aracın ham çıktısı ile bulgu dosyası satır
  satır karşılaştırılır.
- **FAIL, kabul oranı düşük:** Sonnet kapsam dışına taşıyor ya da `fix` aralığı yeni ihlal
  üretiyor; ikisi ayrı sayıdır.
- **FAIL, merge sonrası kırmızı:** oracle eksik koşuyor. Döngünün en pahalı kusurudur; Aşama 2 bu
  düzelmeden açılmaz.
- **UNMEASURABLE:** mutasyon seti ya da merge sayısı yetersiz; nedeni yazılır, set büyütülür.
