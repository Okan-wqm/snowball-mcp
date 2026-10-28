# Kas Büyütme Sinyalleri: Hangi Ölçüm Hangi Organı Doğurur

Tarih: 2026-10-28 · Sürüm: 1.0 · Durum: taslak · Sahibi: operatör
Okunma: her döngü sonunda, genesis kuyruğu kurulurken
Çapa: `genesis-queue.jsonl`; harness kaçırma nedeni sayıları

---

Tohum organ vermez, organ büyütme refleksi verir. Kurucu'ya "şu hafızayı kur" ya da "şu adapter'ı
yaz" denmez. Ona şu denir: bu sayı bu eşiği aşınca bu türde bir organ taslakla, çekişme
protokolünden geçir (`10-cekisme-protokolu.md`), gerekliliğini ablasyonla kanıtla
(`12-genesis.md`). Sistem son durum mimarisine kendi başına varır; varamıyorsa ölçüm o parçanın
gerekmediğini söylüyordur.

## Başlangıç sinyal tablosu

| Ölçülen sinyal | Eşik | Doğan organ |
|---|---|---|
| Harness kaçırması, neden `map_edge_missing` | Pencerede ≥ 3 | Harita adapter'ı; semantik hafızaya yeni katman |
| Aynı tür düzeltme merge edilip hayatta kaldı | ≥ 3 | Prosedürel skill |
| Geri alma, neden `contract_counterpart` | ≥ 1 | Haritaya yeni kenar türü; oracle kapsamı genişler |
| Aynı `cause` tekrarı | ≥ 3 | Geçerlilik sayaçlı ders kaydı |
| Yeniden analiz maliyeti / değişen satır oranı | Medyanın 3 katı | Sembol düzeyi kimlik ve geçersizleştirme |
| Yargıç faz kararı, faz 5'le uyuşmazlık | Pencerede > %30 | Yargıç yeniden yazımı ya da yeni koltuk |
| Sınıfta vaka var, recall eşiğin altında | 2 pencere | Yeni avcı ya da adapter |
| Çözülemeyen bulgu oranı | > %30 | Oracle kası: test yazıcı yeniden yazılır |
| Aynı dosyalar koşular arasında yeniden okunuyor | Okumaların > %50'si | Önbellek ya da özet hafızası (maliyet merdiveni) |
| Sınıflandırılamayan kaçırma | Pencerede ≥ 3 | Yeni `cause` kategorisi ve yeni sinyal |

Eşikler başlangıç değeridir ve yalnız operatör değiştirir. Pencere, aşama spec'inde yazar.

## Boşluk formülü

Sinyallerin çoğu tek bir büyüklüğe bağlanır:

```
gap = (1 − recall_alt_sınırı) × şiddet_ağırlığı × görülmemiş_dosya_payı
```

Genesis, bir sınıf ve property için gap iki pencere üst üste eşiğin üstündeyse ve vaka havuzu
asgari örneklemi sağlıyorsa tetiklenir (`19-olcum-istatistigi.md`). Küçük havuzda gap
hesaplanmaz; önce vaka arzı sinyali gelir.

## Kurallar

- **Sinyal tek başına organ doğurmaz, taslak doğurur.** Taslak DRAFT olarak başlar ve
  `12-genesis.md` yaşam döngüsünden geçer. Kabul, eşli testte anlamlı kazanç ya da aynı
  isabette en az beşte bir daha düşük USD / TP ister; tek koşuluk fark kabul değildir.
- **Bir sinyal, bir taslak.** Aynı sinyal için açık bir taslak varken ikincisi açılmaz.
- **Kaçırma nedeni harness'te sınıflandırılır.** Held-out kaçırmaları ajanlara vaka bazında
  gösterilmez; neden kategorileri yalnız toplam sayı olarak görünür.
- **Tablo da büyür.** Son satır, tablonun kendini genişletme yoludur. Yeni sinyal de bir
  organdır: çekişme protokolünden geçer, ablasyonda bir şey kazandırmıyorsa emekli olur.
- **Kuyruk sınırlıdır.** `genesis-queue.jsonl` derinliği bütçeyle sınırlıdır; taşan sinyal
  Gözcü'nün işaretidir.
