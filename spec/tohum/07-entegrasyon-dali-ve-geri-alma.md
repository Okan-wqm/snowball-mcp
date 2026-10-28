# Entegrasyon Dalı, Geri Alma, Bulgu Kimliği

Tarih: 2026-10-28 · Sürüm: 2.0 · Durum: taslak · Sahibi: operatör
Okunma: her döngü başında ve her merge'de
Çapa: merge ve geri alma defteri; bulgu parmak izleri

---

**Entegrasyon dalı `main`'i takip eder.** Her döngü başında `main` entegrasyon dalına merge
edilir. Çakışma çözülmez: çakışan değişiklik geri alınır, `blocked` yazılır ve yeni bir mikro
görev olarak kuyruğa girer. Zorla itme yoktur.

**Tavanlar.** Döngü başına PR, merge ve CI dakikası tavanı vardır (`policy.json`); merge kuyruğu
sırayla çalışır. Sıfır maliyetli `--fix` yolu da bu tavana tabidir.

**Kendi merge'ünü geri alır.** Entegrasyon dalında bir regresyon `git bisect` ile beynin merge
ettiği bir değişikliğe bağlanıyorsa, beyin o değişikliği otomatik geri alır, geri almayı deftere
`cause` ile yazar ve regresyonu yeni bir vaka adayı olarak sete ekler (`provenance: system`).
Geri alma, merge kadar sıradan bir işlemdir ve aynı kapıdan geçer. Bisect'ten önce testin flaky
olmadığı 3/3 kuralıyla doğrulanır.

**Hayatta kalma penceresi.** Hiçbir merge, pencere dolmadan sayılmaz ya da puanlanmaz. Pencere
sınıfa göredir: K0 ve K1 için 3 gün, K5 ve K6 için 14 gün (`policy.json`). Pencerede geri
alınan iş, artısını almadan eksisini alır.

**Bulgu kimliği.** Her bulgunun parmak izi `property + dosya + sembol + normalize(claim)`'den
türetilir; satır numarası parmak izine girmez, çünkü kod kayınca kimlik değişmemelidir. Aynı
parmak izi ikinci kez bulunursa yeni bulgu değil, yeniden gözlemdir. Yaşam döngüsü
`open → fixed → verified → reopened`. Üç kez `reopened` olan bulgu salınımdır: iki düzeltme
birbirini geri açıyordur; `blocked`'a düşer ve ikisini birlikte ele alan tek bir mikro görev
olmadan yeniden denenmez. İtibar kredisi parmak izi başına değil, kök neden başına verilir
(çakışan hunk ya da aynı sembol).
