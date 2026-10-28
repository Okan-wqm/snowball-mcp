# Bulgu Paneli (K5 ve üstü): Beş Faz

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: taslak · Sahibi: operatör
Okunma: K5 ve üstü bulgu değerlendirirken
Çapa: faz ölüm sayıları; yargıç kalibrasyon defteri

---

Panelin amacı bulguyu "doğru mu" diye oylamak değil, beş fazda kanıtla çürütmeye çalışmak ve
çürütülemeyeni implementer'a eksiksiz bir dosya olarak vermektir.

**Bağımsızlığı üreten şey karakter değil, yapıdır.** Yargıçlara "birbirinize güvenmeyin" yazılmaz;
dört şey yazılır: zıt ispat yükü (üç koltuk, üç farklı soru), mühürlü karar (her fazda kararlar
hash'lenir, sonra açılır, tek çürütme turu), ayrı bağlam ve ikili ayrık model (`09a`), ve son
sözü yürütmenin söylemesi. Tartışmayı bitirmenin en ucuz yolu kanıttır: herhangi bir yargıç
herhangi bir fazda üreme testi **talep ederse** tartışma durur ve test-yazıcı testi yazar; testi
hiçbir yargıç yazmaz. "Bir an önce teslim edip kurtulma" dürtüsü sisteme böyle bağlanır.

| Faz | Soru | Yük | Kapanış |
|---|---|---|---|
| 1 Varlık | Referanslar var mı, kod iddia edileni söylüyor mu, kendi çıktısı kanıt sayılmış mı | Mekanik | Referans doğrulaması, bedava |
| 2 Erişilebilirlik | Gerçek bir çağırandan ya da girdiden bu koda yol var mı | Savcı yolu gösterir; Savunma ölü ya da korumalı olduğunu | Repo haritasında yol + kod referansı |
| 3 Sonuç | Kim neyi yanlış görür, ne bozulur; konvansiyon mu | Savcı sonucu adlandırır; Savunma kasıt kanıtı getirir | Sonuç adlandırılmış, kasıt kanıtı yok; niyet kanıtı yalnız beyin dışı yazardan (`04a` 8) |
| 4 Düzeltme ve etki | Ne değişecek, etki kümesi, maliyet, katman iddiası | Uygulayıcı temsilcisi; Savunma düzeltmenin bir şeyi bozacağını gösterebilir | `required_change` yapısal, etki kümesi, katman doğrulanmış (`23`) |
| 5 Üreme | Test kırmızı mı, düzeltmeyle yeşil mi, etki kümesi yeşil mi | Test-yazıcı ve düzeltici | Yürütme, `04a` şartlarıyla |

**Konuşma kuralları.** Her tur, her yargıç için en fazla bir cümle ve en az bir `path:line`.
Referanssız "katılıyorum" ya da "katılmıyorum" geçersizdir; o yargıç o turda söz hakkını
kaybeder. Kabul eden yargıç hangi referansın onu ikna ettiğini yazar. İki turda kapanmayan faz
faz 5'e gider: test karar verir. Turda karar mühürlemeyen yargıç o fazda eksi puan alır. Bir
bulgu bir fazı geçemezse orada ölür ve defter fazı, her yargıcın kararını ve referansını yazar.

**Implementer'a giden dosya.** Yalnız beş fazı geçen bulgu gider ve yalnız şunlarla: iddia,
kanıt referansları, erişim yolu, görünür sonuç, yapısal `required_change`, etki kümesi, üreme
testi, okunması gereken dersler. Tartışma dökümü arşivlenir, implementer'a verilmez.

**Düzeltme sonrası ikinci panel.** Implementer'ın diff'i 2., 3. ve 4. fazlardan bir kez daha
geçer: yol kapandı mı, etki kümesinde yeni kenar doğdu mu, güvenlik sınırına dokunuldu mu,
katman iddiası tutuyor mu. Geçemeyen diff merge kapısına ulaşmaz.

**Kalite takıntısı bir sayıdır.** Her yargıcın her fazdaki kararı faz 5 sonucuna karşı puanlanır
ve `11-itibar.md`'deki kurallarla ağırlığı değişir. Bağımsızlık `09a` ile ölçülür.
