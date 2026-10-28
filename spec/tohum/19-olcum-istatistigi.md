# Ölçüm İstatistiği: PASS Ne Zaman Anlamlıdır

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: taslak · Sahibi: operatör
Okunma: her çıkış testi tasarlanırken ve her verdict okunurken
Çapa: beklemede: aşama 0 — harness raporundaki n, lb ve verdict alanları

---

Küçük sette eşik yazı turadır: beş vakada "3/5" kararının %95 güven aralığı 0,23 ile 0,88
arasındadır. Bu kurallar o yüzden vardır.

**Üç verdict.** `PASS`, `FAIL`, `UNMEASURABLE`. Örneklem yetersizse sonuç `UNMEASURABLE`'dır;
nedeni yazılır ve vaka arzı bir gap sinyali olur. `UNMEASURABLE` asla `PASS` gibi davranmaz.

**Alt sınır.** Tüm alt sınırlar tek yönlü Clopper–Pearson'dur; güven düzeyi `policy.json`'da,
başlangıç %90. Vakalar aynı modül grubundan geliyorsa etkin örneklem grup sayısıdır.

| Ölçüm | Asgari | Karar kuralı |
|---|---|---|
| K5, K6 held-out recall | 25 vaka, en az 10 grup | Nokta tahmini ve alt sınır sınıf tabanının üstünde |
| K0 mutasyon recall | 60 mutasyon | Sıfır kaçırmayla alt sınır 0,96'dır; taban 0,95 |
| Clean precision | 40 karara bağlanmış bulgu, birden çok clean base | Alt sınır tabanın üstünde; `unresolved` kötümser sayılır, FP gibi |
| Organ kabulü (üstünlük) | Aynı vakalarda eşli, n ≥ 20 | McNemar, p < 0,10, yön lehte |
| Maliyet inişi (eşdeğerlik) | Aynı vakalarda eşli, n ≥ 20 | McNemar non-inferiority, bir vaka marjı |

Koşu bütçesi daha çok snapshot'a harcanır; aynı snapshot'ın tekrarı vaka gürültüsünü değil, koşu
gürültüsünü ölçer.

**Held-out kaynağı.** Held-out, Kurucu'nun hesaplayamayacağı bir havuzdan gelir: (1) mutasyonlar,
gizli tohumla çok büyük bir aday havuzundan seçilir; (2) insan düzeltmeleri, mühürlenmiş bir kesim
tarihinden sonra merge edilenlerden gelir; (3) hiçbir zaman yayımlanmayan bir yedek havuz
tutulur. "Tüm vakalar eksi dev" hesabı bu yüzden held-out'u vermez.

**Exit'te ne sayılır.** `human_fix` ve `mutation`. K5 ve K6'da mutasyonların payı held-out'un en
fazla yarısıdır ve ayrı raporlanır; anlamsal mutasyon geçerliliği: kod derlenir, mevcut testler
yeşil kalır, operatör property'ye bağlıdır. `system_tp` ve `system_regression` aynı organ
soyunun held-out'una ve hiçbir exit kapısına girmez.

**Bakış bütçesi.** Bir property ve organ soyu için toplam held-out bakışı `policy.json`'da sınırlıdır
ve rotasyonla sıfırlanmaz. Bir bakış yalnız verdict, n ve alt sınır döndürür; kaçırma nedenleri
yalnız dev koşularından raporlanır. Maliyet merdiveninde yalnız kazanan basamak bir bakış harcar.
Bütçe bitince o soy için held-out ölçümü `UNMEASURABLE`'dır ve yeni kesim sonrası vakalar beklenir.

**Bulaşma.** dev/held-out bölmesi modül grubu bazındadır. Exit koşularında avcı ders almaz ve
harita dondurulur. Dar kapsam basamağının glob'u yalnız dev koşularından türetilir.

**Başarısız basamak.** Bir koşu hüküm değildir. Eşiği tutmayan basamak vaka havuzu yarı yarıya
büyüyünce bir kez daha denenir.
