# Bağımsızlık ve Donmuş Koltuklar

Tarih: 2026-10-28 · Sürüm: 2.0 · Durum: taslak · Sahibi: operatör
Okunma: her dispatch'te ve her koltuk ataması değiştiğinde
Çapa: run_meta model alanları; kapıdaki koltuk hash'leri; rakip kanarya oranı

---

Yalnız iki model ailesiyle bağımsızlık, yapıyla sağlanır:

1. **İkili ayrıklık.** Bir artefaktın üreticisi, yargıcı ve oracle'ı ikili olarak farklı
   modeldedir ve her zaman ayrı bağlamda koşar. Avcı Opus ise Savunma ve test-yazıcı Sonnet'tir;
   Savcı, avcıyla aynı tarafta olduğu için aynı modelde olabilir. Kapı, `run_meta`'daki model
   alanlarından ayrıklığı doğrular; ayrıklığı bozan koşu geçersizdir. Maliyet merdiveni
   ayrıklığı bozan bir inişi atlar.
2. **Aynı aileden iki model birlikte yanılabilir.** Bu bilinir ve kabul edilir; bu yüzden
   hiçbir karar model görüşüyle kapanmaz, yürütmeyle kapanır (Y8). Operatör, spec dondurma ve
   harness şeridi rakipleri için başka bir sağlayıcı yapılandırabilir; yapılandırılmışsa kapı
   onu zorunlu kılar.
3. **Donmuş koltuklar.** Rakip koltukları, oracle takımı, Gözcü, taban avcı, puanlayıcı ve
   dispatcher'ın tanımları Kurucu'nun yazamadığı bir dizindedir; hash'leri kapıda pinlidir.
   Değişiklikleri yalnız harness şeridinden ve arşivde yeniden oynatma oracle'ıyla geçer.
   Kurucu kendi yargıcını yazamaz (Y6).
4. **Rakip kanaryası.** Harness, rakiplere ara sıra bilerek kusurlu artefaktlar verir: sızdıran
   snapshot, önemsizce sağlanan eşleşme, belirti düzelten yama. Kanaryaların eşiğin altını
   çürüten rakip dondurulur ve yeniden yazılır; pasif rakip, rakip değildir.
5. **Gözcü deterministik koddur.** LLM değildir, defter metnini okurken yönlendirilemez, itibarla
   puanlanmaz; eşikleri `policy.json`'dadır.
6. **Bağımsızlık ölçülür.** İki koltuğun karar ve referans benzerliği eşiği aşarsa Gözcü işaretler.
   Hiçbir bulgunun 1–4. fazlarda ölmediği bir pencere, çalışan bir panelin değil, birbirini
   onaylayan bir panelin izidir.
