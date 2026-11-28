# Değişiklik Günlüğü — Tohum, 2.2'nin Yirmi İkinci Kayıtları

Tarih: 2026-11-28 · Sürüm: 2.2
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

- 2.2 (2026-11-28, E751; tohum dönemi AN; tohumun kendi testleri gerçek bir gecikme beklemez).
  **İlk iş** (`25` 10b). Teslimden itibaren önyükleme hakeminin hiçbir denetimi kırmızı olmaz: bu dönem yalnız
  tohumun kendi testlerini ve `04`'ün sonunu değiştirir; ne bir tablo, ne bir vektör, ne hakemin kodu değişir.
  Kurucu'nun bugünkü işi sürer, sırası `CHANGELOG-14`'ünkidir.
  Tohumun ipuçsuz tam mutasyon koşusu parça 19'da kırmızıydı (2026-11-25, 2026-11-26 ve koşu 46072742202):
  `manifest_read_retries` kabul edilmiş manifestin okumasını `gh_read`'in yeniden deneme gecikmelerine geri koyar,
  bir test onlara mock'suz ulaşıp gerçekten uyudu ve bütün takım 900 s'yi geçti (zaman aşımı, öldürme değil, E738).
  Sınıf testlerin kendi katmanında kapandı (E751): her test modülü önce `tests/no_real_delays.py`'yi içe aktarır ve
  tohumun kodunun sıfırdan büyük her uykusu o anda kırmızıdır (`RealDelay`). Kural `04`'ün sonundadır (`04:50-57`);
  `04:1-48` yer değiştirmedi. Testler `test_panel_epoch_an`; mutantlar, biri muhafızı kaldırır.
  Yanıtlanan rapor yok. Gevşetme yok.
