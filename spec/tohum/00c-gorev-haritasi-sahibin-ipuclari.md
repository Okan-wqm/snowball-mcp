# Görev Haritası, Devam: Sahibin İpuçları

Tarih: 2026-11-19 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: her oturumda, görev seçilirken (`00b`'nin devamı)
Çapa: elle yazılır; `00b` 80 satırı doldurduğu için (`15` 1) ipuçları burada sürer

---

**Öğrenme (sahibin ipucu, 2026-11-19, E649; ipucu, reçete değil).**
- Olgular (2026-11-19): defterde 20 `lesson` satırı var; 9'una sonraki kararlarda adıyla atıf var, 11'ine hiç yok.
  Hiçbirinde `scope` yok (`22`: sınıf, dosya kalıbı, koşullar). f1537: doğru bir ders, kendisinden önce yazılmış
  koda ulaşmadı, çünkü eski kodu yeni derse göre yeniden okuyan olmadı.
- İpucu: bir ders, geçerli olduğu iş geldiğinde bulunabilir olmalı. Yeni bir ders, ondan önce yazılmış kodu da
  kapsamalı. Tekrar eden ya da çürüyen dersler birleşmeli veya `superseded_at` almalı. Ajanlar devreye girince model
  sürümüne bağlı dersler de buna dahil olmalı (E644).

**Önleme ve yapı (sahibin ipucu, 2026-11-19, E650; ipucu, reçete değil).**
- Olgular: Kurucu'nun "aktarımdan önce yakala" türünde beş önerisi var (f1538, f1546, f1553, f1560, f1567); hiçbiri
  kurulmadı. 18 ve 19 Kasım'da dört (B) denemesi, aktarımdan önce görülebilecek bir eksik yüzünden kırmızı bitti;
  ölçüm aynası (`/work/logs/mirror.json`) bunların kaydını tutar. `status.depmap`'e göre `cli`'yı 45 modül içe
  aktarır, `loop.job` 36 modülü içe aktarır, ve iki sayı da büyüyor (`01` karmaşıklık maliyeti). f1551 hâlâ açık:
  hedefin kendi `@nx/enforce-module-boundaries` kuralı, kimse fark etmeden atlanıyor.
- İpucu: bir sonraki aktarımdan önce bu önerilerden en az biri kurulup ölçülsün. Yapı da ölçülerek sadeleşsin.
  Gerçek ürün reposundan önce, hedefin kendi kurallarından hiçbiri sessizce atlanmamalı.
