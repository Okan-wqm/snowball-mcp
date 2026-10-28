# Entegrasyon Dalı, Nöbetçi, Geri Alma, Bulgu Kimliği

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: taslak · Sahibi: operatör
Okunma: her döngü başında ve her merge'de
Çapa: beklemede: aşama 1 — merge ve geri alma defteri

---

**Entegrasyon dalı `main`'i takip eder.** Her döngü başında `main` `brain/integration`'a merge
edilir. Çakışma çözülmez: çakışan beyin değişikliği geri alınır, `blocked` yazılır ve yeni bir
mikro görev olarak kuyruğa girer. Zorla itme yoktur.

**Taban ve mandal.** Beyin bir repoya bağlandığında her aracın mevcut ihlallerinden bir taban
çıkarır ve deftere yazar. Keşif tabandaki ve sonradan doğan tüm ihlalleri bulgu sayar; mevcut borç
kapsam içindedir. Mandal kuralı: hiçbir merge bir aracın toplam ihlal sayısını artıramaz.

**Nöbetçi.** Her merge'den sonra hakemin nöbetçi işi `brain/integration` başında etkilenen testleri
koşar. Kırmızı çıkarsa önce 3/3 kuralıyla flaky olmadığı doğrulanır, sonra `git bisect
--first-parent` yalnız son yeşilden bu yana beynin merge commit'leri üzerinde yürür; insan
commit'leri bölünmez. Bisect adımı başına süre ve toplam adım sayısı `policy.json`'dadır.

**Kendi merge'ünü geri alır.** Bisect beynin bir merge'ünü gösterirse beyin onu otomatik geri
alır, geri almayı `cause` ile yazar (`26`'daki kapalı küme) ve regresyonu vaka adayı olarak
ekler (`provenance: system_regression`). Geri alma, merge kadar sıradan bir işlemdir ve aynı
kapıdan geçer. Bisect bir insan commit'ini gösterirse beyin geri almaz; bunu raporlar.

**Hayatta kalma penceresi.** Hiçbir merge pencere dolmadan sayılmaz ya da puanlanmaz. Pencere
sınıfa göredir ve `policy.json`'dadır: başlangıç K0 ve K1 için 72 saat, K5 ve K6 için 14 gün.
Pencerede geri alınan iş artısını almadan eksisini alır.

**Bulgu kimliği.** Parmak izi `property + dosya + sembol + normalize(iddia)`'dan türetilir.
Sembol yoksa, örneğin dosya düzeyindeki lint ihlallerinde, `kural + kapsayan sembol ya da dosya
+ normalize(satır içeriği)` kullanılır; satır numarası hiçbir parmak izine girmez. Aynı parmak
izi ikinci kez bulunursa yeni bulgu değil, yeniden gözlemdir. Yaşam döngüsü
`open → fixed → verified → reopened`. Üç kez `reopened` olan bulgu salınımdır; `blocked`'a
düşer ve ikisini birlikte ele alan tek bir mikro görev olmadan yeniden denenmez. İtibar kredisi
kök neden başınadır (çakışan hunk ya da aynı sembol).
