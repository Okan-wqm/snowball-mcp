# Aşama Protokolü

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: taslak · Sahibi: operatör
Okunma: her aşama başında ve sonunda
Çapa: aşama çıkış raporları; hakem kilit kapısı (aşama, spec hash) anahtarlı

---

1. Kurucu spec'i taslaklar. Bölümleri sabittir: amaç, doğruluk özellikleri, roller, sıralı mikro
   özellikler, çıkış testi, yasaklar, bütçe, teslim listesi. Aşama özeti ön koşulu ve çıkış
   kapısını taşır.
2. Spec **yapısal kontrol listesinden** geçer ve tohum rakibi (`29`) onu çürütmeyi dener. Liste
   temiz ve çürütme başarısızsa spec dondurulur ve hash'i zincire yazılır. Aşama 0'da liste elle,
   Aşama 0'dan sonra `spec.lint` aracıyla denetlenir; araç da aynı listeyi uygular:
   - sekiz bölüm var ve boş değil;
   - her eşik ya `policy.json`'a atıf ya da anayasal tabana atıf;
   - bütçe `policy.json` tavanının altında;
   - property spec'lerinde kalıp yok (`asama-4/06`);
   - hedef repoya özgü yol, araç ya da karar belgesi adı yok;
   - her yeni dosyanın okuyucusu `27`'de;
   - her çapa ya çözülüyor ya da "beklemede: aşama N".
3. Kurucu inşa eder; takımı bu aşamanın bütçesi içinde kurar.
4. Hakem harness'i ölçer. Çıkış testi canlı ve uçtan ucadır; birim testi ve mock çıkış kanıtı
   değildir. Verdict `PASS`, `FAIL` ya da `UNMEASURABLE`'dır (`19`).
5. Harness PASS verir ve raporu aşama dizinine tarihli sayfa olarak commit eder. Bir sonraki
   aşamanın ajan dosyaları, araçları ve izinleri ancak o raporu taşıyan PR ile eklenir; PR'ı hakem
   kilit kapısı kabul eder ve kilit (aşama, spec hash) çiftine anahtarlıdır.

**Dikey dilim kuralı.** Hiçbir aşama döngünün tek bir fazını "tamamen" kurmaz. Her aşama
döngünün tamamını daha dar bir kapsamda canlı çalıştırır, sonra kapsam genişler.

**Bir aşama ileri kuralı.** Yalnız bir sonraki aşamanın spec'i donar. Daha sonraki aşamaların
sayfaları "hedef taslak" durumundadır: okunur, sırası gelince yeniden yazılır ve ancak o zaman donar.

**Çapa kuralı.** `taslak` ya da `hedef taslak` durumundaki sayfada çapa "beklemede: aşama N"
olarak yazılabilir. Aşama N PASS alınca çapa çözülmelidir; çözülmeyen çapa bayatlıktır.

**Harness şeridi.** Harness ve donmuş koltuklar hakem reposundadır (`01a`). Değişikliği yalnız
şerit yazarı önerir; değişiklik hatayı gösteren yeni bir kendi-testi ekler (kasıtlı bozma),
mevcutları yeşil tutar, performans eşiklerini yalnız `18`'deki prosedürle oynatır ve farklı
modelden rakip çürütemez. Arşivde yeniden oynatma **yalnız dev arşivinde** yapılır; held-out
görünümüne dokunan hiçbir şerit işlemi yoktur. Geçmiş bir kararı gevşeten değişiklik reddedilir.
