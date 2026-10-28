# Bağımsızlık, Donmuş Koltuklar, Şerit Yazarı

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: taslak · Sahibi: operatör
Okunma: her dispatch'te ve her koltuk değişikliğinde
Çapa: beklemede: aşama 1 — run_meta model alanları; hakem reposundaki koltuk özetleri

---

**Model kuralı.** Yalnız iki model ailesiyle bağımsızlık yapıyla sağlanır:

1. Bir artefaktın **karşı koltukları** (Savunma, Uygulayıcı temsilcisi, rakip) ve **oracle'ı**
   üreticiden farklı modeldedir. Karşı koltuk ile oracle aynı modelde olabilir; o zaman ayrı
   bağlamda koşar ve birbirinin çıktısını görmez. Savcı üreticiyle aynı taraftadır, aynı modelde
   olabilir.
2. Kapı ayrıklığı `run_meta`'dan doğrular: her koşu yargıladığı koşuyu `subject_run_id` ile
   gösterir; model alanlarını dispatcher yazar.
3. Aynı aileden iki model birlikte yanılabilir. Bu yüzden hiçbir karar model görüşüyle kapanmaz,
   yürütmeyle kapanır (Y8). Operatör, rakip için başka bir sağlayıcı yapılandırabilir; yapılandırılmışsa
   kapı onu zorunlu kılar.

**Donmuş koltuklar.** Rakip ve oracle koltukları, Gözcü, taban avcı, itibar puanlayıcısı,
dispatcher, harness ve kapı hakem reposundadır.

- **Tohum koltukları.** Tohum rakibinin ve test-yazıcının ilk promptları tohumla gelir (`29`);
  Kurucu onları yazmaz.
- **Kurulum istisnası.** Diğer koltukların ilk sürümlerini Aşama 0 ve 1'de Kurucu yazar, çünkü
  başka yazar yoktur. Her biri tohum rakibinden ve harness kendi testlerinden geçer, aşama çıkışında
  hakem reposuna taşınır ve donar. Bu sistemin güven köküdür; zayıflığı açıktır ve çıkış raporunda
  yazılır.
- **Şerit yazarı.** Donmuş bir koltuğu yalnız şerit yazarı değiştirebilir: Kurucu değildir,
  Kurucu'nun defterini görmez, gerekçesini hakem raporlarından ve kanaryalardan alır. Değişikliği
  görevdeki kapı arşivde yeniden oynatır ve farklı modelden rakip çürütmeye çalışır.
- **Geri dönüş.** Kanaryada başarısız olan koltuk, son pinli sürümüne geri döner ve şerit yazarına
  bir görev düşer; sistem koltuksuz kalmaz.

**Rakip kanaryası.** Hakem, rakiplere ara sıra kusurlu artefaktlar verir: gerçek geçmiş
artefaktlara mekanik olarak enjekte edilmiş kusurlar (sızdıran snapshot, önemsizce sağlanan
eşleşme, belirti düzelten yama). Eşiğin altını çürüten rakip son pinli sürüme döner.

**Gözcü deterministik koddur.** LLM değildir, itibarla puanlanmaz; kuralları `28`'de, eşikleri
`policy.json`'dadır. **Bağımsızlık ölçülür:** iki koltuğun karar ve referans benzerliği eşiği
aşarsa Gözcü işaret yazar; işaretin okuyucusu şerit yazarıdır.
