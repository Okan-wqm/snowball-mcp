# Dokümantasyon: Her Özellik Tarihli Tek Sayfa, Her Organ ve Bulgu Üretilmiş Sayfa

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: taslak · Sahibi: operatör
Okunma: her sayfa yazarken ve her döngüde doküman üretilirken
Çapa: INDEX.md üretimi; çapa çözümleme kontrolü; docs/organs ve docs/findings

---

1. **Bir özellik, bir sayfa.** Bir organ, bir kural, bir karar, bir aşama bölümü: her biri tek
   sayfa. Sayfa 80 satırı geçerse bölünür. Üretilmiş dizinler bu sınırdan muaftır.
2. **Tarih başlıkta.** Tarih, sürüm, durum ve sahibi; sürüm yalnız başlıkta yaşar.
3. **Her sayfanın çapası vardır.** Sayfayı kanıtlayan dosya, defter ya da test. Çapası
   çözülmeyen sayfa bayattır ve bir kapıyı kırmızıya boyar. Tek istisna: `taslak` sayfada
   "beklemede: aşama N" çapası; aşama N PASS alınca çözülmelidir.
4. **Üretilebilen sayfa üretilir.** Defterden türetilebilen her şey elle yazılmaz; beyin her
   döngüde yeniden üretir. Üretilmiş sayfa elle düzenlenemez; düzenleme zincir kırığıdır.
5. **Dizin mekaniktir.** `INDEX.md` başlıklardan üretilir; üretici Aşama 0 teslimatıdır. Görev
   haritası elle yazılan ayrı bir sayfadır (`00b`).
6. **Aşama spec'i sayfadır.** Her bölüm ayrı sayfa; özet sayfası ön koşulu, çıkış kapısını ve
   sayfa listesini taşır; çıkış raporu aynı dizine tarihli sayfa olarak girer.
7. **Değişiklik günlüğü ayrı ve sıralıdır.** Sayfalar bugünü anlatır; geçmiş `CHANGELOG.md`'de
   ve zincirdedir.
8. **Spec operatörün dilinde, sistem çıktısı İngilizce.** Bulgular, organ sayfaları, defterler ve
   `status.md` İngilizcedir; ajanlar ve dış okuyucular için tek dil.

**Her organın sayfası.** `<state_root>/docs/organs/<kimlik-hash>.md`, zincirden üretilir:
amaç ve kapsam, doğduğu boşluk ve ölçüm, prompt ve araç yüzeyi hash'i, yaşam döngüsü geçişleri
tarihleriyle, itibar eğrisi, ablasyon sonuçları, soyağacı, ürettiği bulgular, yaptığı
düzeltmeler, hayatta kalma ve geri alma sayıları, maliyet.

**Her bulgunun sayfası, iki format.** Makine için `findings.jsonl` satırı; insan için
`<state_root>/docs/findings/<fingerprint>.md`: iddia ve kanıt, sınıf ve property, bulan organ,
panel fazları ve her fazın kararı (hangi yargıç, hangi referansla), oracle sonucu (K0–K2'de araç
yeniden koşusunun, K5'ten itibaren test koşularının hash'leri),
düzeltme özeti ve etki kümesi, merge ve hayatta kalma durumu, geri alındıysa nedeni, doğan
dersler, toplam maliyet. Unresolved ve FP bulgular da sayfa alır; kapanış nedeni yazılır.
İndeksler üretilir: organlar sınıf ve durum başına, bulgular sınıf ve yaşam döngüsü başına.

**Şablon ve güvenlik.** Üretilmiş sayfalar sabit şablondan yazılır; ajan metinleri kaçışlı,
uzunluk sınırlı kod alanlarına konur; bağlantı, HTML, kişi anma ve "kapatır" anahtar kelimeleri
temizlenir. Üretilmiş sayfalar memory değil rapordur: okuyucusu operatördür, yeni bilgi
taşımaz, defterden yeniden üretilebilir. **K6** bulgularının sayfaları, testleri ve iddiaları
düzeltme `main`'e girene kadar mühürlü depoda durur; hedef repo herkese açık olabilir.

**Yerleşim.** Beyne ait sayfalar `tohum/`, aşama sayfaları `asama-N/`, repoya özgü üretilmiş
sayfalar `<state_root>/docs/`. Kurucu her oturum `00` ve `00a` ile başlar; görev başına
`INDEX.md`'nin gösterdiği sayfaları okur, fazlasını değil.
