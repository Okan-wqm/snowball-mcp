# Metrikler: Bir Bakım Sistemi Neyi Sayar

Tarih: 2026-10-28 · Sürüm: 1.0 · Durum: taslak · Sahibi: operatör
Okunma: `status.md` üretilirken ve her Gözcü değerlendirmesinde
Çapa: `status.md` bölümleri ve `cost-ledger.jsonl`

---

Recall ve precision, planted vakalar üzerinde ölçülür ve yalnız bilineni ölçer. Bir bakım
sistemi şunları da sayar; hepsi `status.md`'de, hepsi zincirde.

| Metrik | Tanım | Kullanımı |
|---|---|---|
| Regresyon oranı | 100 merge başına geri alma + bisect ile sisteme bağlanan merge sonrası kırmızı, 30 gün | Anayasal: eşiğin üstü dondurma |
| Kaçış oranı | Sistemin taradığı dosyalarda, hata oradayken, insanların yazdığı düzeltmeler; property başına | Her kaçış yeni vaka; koşular arası capture–recapture ile gerçek kaçırma tahmini |
| Değer / USD | Şiddet ağırlıklı hayatta kalan sonuç (CRIT 10, HIGH 5, MED 2, LOW 1, lint 0,05) bölü USD | USD / isabetin yerine; itibar ve merdiven bunu okur |
| Düzeltme süresi | Bulgudan merge'e medyan ve p90, sınıf başına; `blocked` işlerin yaşı | Gözcü eğilimi |
| Risk ağırlıklı kapsama | Dosya × property × sınıf; güvenlik yolları ağırlıklı | Kör noktayı gösterir; gap sinyali |
| Oracle geçerliliği | Flake oranı (3/3 kırmızı, 3/3 yeşil şartı), TP düzeltmelerinin geri alınma oranı | Oracle takımının itibarı |
| Maliyet payları | Keşif, üretim, ölçüm, genel; aylık tavana karşı | Anayasal |

"Geçen yıl bugün" bölümü bu tablonun o günkü ve bugünkü değerlerini yan yana koyar; sistemin
ne öğrendiği bir anlatı değil, bu farktır.
