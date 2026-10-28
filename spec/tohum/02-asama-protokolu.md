# Aşama Protokolü

Tarih: 2026-10-28 · Sürüm: 2.0 · Durum: taslak · Sahibi: operatör
Okunma: her aşama başında ve sonunda
Çapa: aşama çıkış raporları; CI kilit kapısı (aşama, spec hash) anahtarlı

---

1. Kurucu spec'i taslaklar. Bölümleri sabittir: amaç, doğruluk özellikleri, roller, sıralı mikro
   özellikler, çıkış testi, yasaklar, bütçe, teslim listesi. Aşama özeti ön koşulu ve çıkış
   kapısını taşır.
2. Spec yapısal lint'ten geçer (bölümler tam, bütçe tavan içinde, property spec'te kalıp yok,
   hedef repoya özgü ad yok) ve üreticiden farklı modelden, ayrı bağlamda bir rakip onu
   çürütmeyi dener. Lint temiz ve çürütme başarısızsa spec dondurulur ve hash'i zincire yazılır.
3. Kurucu inşa eder; takımı bu aşamanın bütçesi içinde kurar.
4. Harness ölçer. Çıkış testi canlı ve uçtan ucadır; birim testi ve mock çıkış kanıtı değildir.
   Verdict `PASS`, `FAIL` ya da `UNMEASURABLE`'dır (`19-olcum-istatistigi.md`).
5. Harness PASS verir ve raporu aşama dizinine tarihli sayfa olarak commit eder. Bir sonraki
   aşamanın ajan dosyaları, araçları ve izinleri ancak o raporu taşıyan PR ile eklenir; PR'ı CI
   kilit kapısı kabul eder ve kilit (aşama, spec hash) çiftine anahtarlıdır.

**Dikey dilim kuralı.** Hiçbir aşama döngünün tek bir fazını "tamamen" kurmaz. Her aşama
döngünün tamamını daha dar bir kapsamda canlı çalıştırır, sonra kapsam genişler.

**Bir aşama ileri kuralı.** Yalnız bir sonraki aşamanın spec'i donar. Daha sonraki aşamaların
sayfaları "hedef taslak" durumundadır: okunur, tartışılır, sırası gelince yeniden yazılır ve
ancak o zaman donar.

**Çapa kuralı.** Henüz var olmayan bir artefaktı gösteren çapa, sayfa `taslak` iken "beklemede:
aşama N" olarak izinlidir. Aşama N PASS alınca çapa çözülmelidir; çözülmeyen çapa bayatlıktır.

**Harness kuralı.** Harness senin dışındadır. Aşama 0'da sen yazarsın, rakip çürütmeyi dener,
kendi testleri yeşilse CI merge eder. Sonra harness yalnız kendi şeridinden değişir: değişiklik
hatayı gösteren yeni bir kendi-testi ekler (kasıtlı bozma), mevcutları yeşil tutar, performans
eşiklerini yalnız `18-politika-ve-dinamik-esikler.md`'deki prosedürle oynatır ve rakip
çürütemez. Her harness değişikliği arşivdeki geçmiş koşularda yeniden oynatılır; geçmiş bir skoru
yükselten değişiklik reddedilir. Held-out vakaların listesini ve vaka bazlı sonuçlarını hiçbir
ajan göremez.
