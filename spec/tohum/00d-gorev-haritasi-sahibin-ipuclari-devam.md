# Görev Haritası, Devam: Sahibin İpuçları II

Tarih: 2026-11-20 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: her oturumda, görev seçilirken (`00c`'nin devamı)
Çapa: elle yazılır; `00c` 80 satıra yaklaştığı için (`15` 1) ipuçları burada sürer

---

**Sahibin ipucu (2026-11-20, E654; ipucu, reçete değil). Derslerin kendiliğinden yeniden sınanması.**
- Olgu (2026-11-20): defterde 26 `lesson` satırı var. Hepsinin bir `recheck`'i var, hepsi `trust: inferred`, hiçbiri
  bağımsız olarak yeniden koşturulmadı. `26g` gereği başlatıcı ve hakem `recheck`'i koşturmaz. Bugün dersleri yeniden
  sınayan bir şey yoktur.
- Amaç: sahip ilkesi (2026-11-06) her dersin yeniden sınanan, yanlışlanabilir bir kayıt olmasıdır. Yanlış bir ders
  sessizce kalmamalı.
- İpucu: dersler otomatik ve düzenli olarak yeniden sınansın; sonucu derse geri yazılsın (hâlâ tutuyor mu, ne zaman
  tutmadı, `closes:` ile kapanma). Ne zaman koşacağı, nerede koşacağı ve sonucun nasıl kaydedileceği Kurucu'nun
  tasarımıdır. Tohumda bir değişiklik gerekiyorsa Kurucu bunu bir rapor olarak önerir.
- Ölçülür: kaç ders yeniden sınandı, kaçı tuttu, kaçı kapandı.
