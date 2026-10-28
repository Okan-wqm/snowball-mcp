# İtibar ve Puanlama

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: taslak · Sahibi: operatör
Okunma: dispatch ve yeniden yazım kararlarında
Çapa: reputation.jsonl; puanlayıcı deterministik koddur

---

Her ajan kimliğinin (prompt hash + model + araç yüzeyi) bir itibarı vardır. İtibar bir memory'dir:
yazarı defterleri okuyan deterministik puanlayıcı, okuyucusu dispatcher ve genesis, değiştirdiği
karar "bu işi kime, hangi modelle, ne bütçeyle vereceğim ve kimi yeniden yazacağım"dır. Puanı
hiçbir zaman bir LLM vermez.

**Skor.** `skor = Σ hayatta kalan sonuçların şiddet ağırlığı − λ · USD`; sıralama noktaya göre
değil, Beta posteriorunun alt sınırına göre yapılır. λ, Beta önseli ve pencere `policy.json`'dadır.
Hacim puan getirmez; kredi kök neden başınadır. **Şiddet avcıdan gelmez:** property ve sınıftan
`policy.json`'daki haritayla türetilir; avcının yazdığı şiddet yalnız ipucudur.

| Rol | Artı | Eksi |
|---|---|---|
| Avcı, adapter | Pencereyi geçmiş TP; faz 1–2'de ölmeyen bulgu oranı | FP; faz 1'de ölen bulgu; parmak izi bölme |
| Düzeltici, implementer | Hayatta kalan düzeltme; katman iddiası panelde tutmuş | Geri alınan düzeltme, etki kümesi büyüklüğüyle orantılı; kapsam dışı yazım |
| Yargıç | Faz 5 ile uyuşan faz kararı | Faz 5'in çürüttüğü karar; referanssız söz |
| Maliyet mühendisi | Eşiği tutan daha ucuz basamak | Eşiği tutmayan basamağa harcanan bütçe |
| Oracle takımı | Flake'siz, geri alınmayan TP | Flaky test; geri alınan TP düzeltmesi |

**Soğuk başlangıç ve dilimler.** Bir ajan en az on karara bağlanmış sonucu olmadan sırasızdır;
SHADOW'daki oracle-doğrulanmış sonuçlar `policy.json`'daki indirimle sayılır, çünkü geri alınma
riski taşımazlar. Göreli
sıralama yalnız üç ya da daha çok üyeli sınıfta yapılır; tek üyeli sınıf taban avcıya ve kendi
önceki penceresine karşı ölçülür. Yeniden yazım yalnız mutlak alt sınır iki pencere üst üste
sınıf eşiğinin altında kalınca olur, her pencerede değil.

**Hayatta kalma ve yarı ömür.** Hiçbir sonuç merge anında puanlanmaz; pencere sınıfa göredir
(`07`). İtibar yarı ömürle çürür (`policy.json`, başlangıç 30 gün); eski kazanç bugünkü işi
taşımaz.

**İtibar ne yapar.** Aynı sınıfta en yüksek alt sınıra sahip ajan işi önce alır ve daha geniş
bütçe kullanır. Model basamağı değişiklikleri en az iki pencere beklenir (histerezis); Sonnet'te
kazanan Sonnet'te kalır, düşen o sınıf için Opus'a çıkar. Geride kalan ajan genesis şeridine
gider: yeni kimlik, deneme süresi, soyağacı. `derived_from` zincirinde itibar tabanı taşınır;
yeniden yazım eksiyi sıfırlamaz. İki yeniden yazımdan sonra da alt dilimde kalan tür emekli olur.

**Puan için iş.** Aynı dosyada ardışık küçük düzeltmeler, aynı kök nedenden bulgu bölmeleri,
pencere sonrası geri almalar Gözcü'nün ölçtüğü kalıplardır; ölçülen ajan o pencerede sıfır
puan alır ve kalıp harness'e puan kanaryası olarak girer. Ders okuma kaydını ajan değil
dispatcher tutar. Lig tablosu sınıf ve basamak başınadır ve
`status.md`'de görünür.
