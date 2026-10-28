# Ölçüm İstatistiği: PASS Ne Zaman Anlamlıdır

Tarih: 2026-10-28 · Sürüm: 1.0 · Durum: taslak · Sahibi: operatör
Okunma: her çıkış testi tasarlanırken ve her verdict okunurken
Çapa: harness raporundaki `n`, `lower_bound` ve `verdict` alanları

---

Küçük sette eşik, yazı turadır. Beş vakalık held-out'ta "3/5 geçti" kararının %95 güven
aralığı 0,23 ile 0,88 arasındadır; gerçek recall'u 0,40 olan bir avcı üç denemede %40 ihtimalle
geçer, gerçek recall'u 0,60 olan %34 ihtimalle kalır. Bu kurallar o yüzden vardır.

## Üç verdict

`PASS`, `FAIL`, `UNMEASURABLE`. Örneklem yetersizse sonuç `UNMEASURABLE`'dır; ne geçer ne
kalır, nedeni yazılır ve vaka arzı bir gap sinyali olur. `UNMEASURABLE` asla `PASS` gibi
davranmaz.

## Asgari örneklem

| Ölçüm | Asgari | Karar kuralı |
|---|---|---|
| K5, K6 held-out recall | 25 vaka | Nokta tahmini eşiğin üstünde VE tek yönlü %90 küme-bootstrap alt sınırı taban eşiğin üstünde |
| K0 mutasyon recall | 60 mutasyon | Üçler kuralı: 0,95 iddiası için sıfır kaçırmayla en az 60 |
| Clean precision | 40 karara bağlanmış bulgu, birden çok clean base | Alt sınır taban eşiğin üstünde |
| Maliyet inişi | Aynı vakalarda eşli karşılaştırma, n ≥ 20 | McNemar non-inferiority, bir vaka marjı |

Koşu bütçesi daha çok snapshot'a, aynı snapshot'ın tekrarına değil harcanır: tekrar koşu
koşu-arası gürültüyü ölçer, vaka örnekleme gürültüsünü değil.

## Mühür ve bakış bütçesi

Bir held-out mührüne en fazla üç bakış vardır ve her bakış yalnız pass/fail döner. Üç bakıştan
sonra set dev'e taşınır ve yeni held-out yeni vakalardan çekilir; en geç 90 günde rotasyon.
Maliyet merdiveni basamakları da birer bakıştır ve aynı bütçeden düşer.

## Bulaşma

- TP-türevi vakalar aynı avcı soyunun held-out'una giremez; avcı onları zaten bulmuştur.
- Yalnız insan yazarlı düzeltmelerden gelen vakalar exit kapısında sayılır (`provenance`).
- dev/held-out bölmesi modül ya da PR grubu bazında yapılır; yakın kopyalar aynı tarafta kalır.
- Dar kapsam basamağının glob'u yalnız dev koşularının okuduğu dosyalardan türetilir.

## Başarısız basamak

Bir koşu bir hüküm değildir. Eşiği tutmayan basamak deftere yazılır ve vaka havuzu yarı yarıya
büyüyünce bir kez daha denenir.
