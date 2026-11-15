# Değişiklik Günlüğü — Tohum, 2.2'nin Altıncı Kayıtları

Tarih: 2026-11-13 · Sürüm: 2.2
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

- 2.2 (2026-11-13, E574; sahibin kararı): yeni yasa `00` Y12 "Maliyet" (metni yalnız orada); `06`, `24`, `24a`
  ona işaret eder; `24a`'daki "Kurucu kendi maliyetini ölçemez" cümlesi Y12 ile çeliştiği için kalktı; `00` 80 satır
  sınırı için yeniden sarıldı, başka içerik değişmedi.
- 2.2 (2026-11-12, E569–E573; Kurucu raporu, iki uzmanlı iki turlu panelin kararı): yeni `29e` "Genellik okuması":
  #genellik'in metin saydığı baytlar (katı UTF-8 ve NUL yok; öbür denetim karakterleri metindir), aradığı yer (yol,
  `referee/`'den sonrası, ve metin; karşılaştırmanın biçimi), iki nedenin adı ve listenin oturuma verilmediği; `26c:32`
  kuralı için oraya bakar, `00b`'nin aşama satırı `29e`'yi okutur; donmuş `asama-0/10` değişmedi. `24a` 3: başlatıcı her
  oturumun klasörüne `targets.json` yazar, `targets[]` sırasıyla `[{id, kind}]`, adsız (`seed/founder/prompt.md`
  "Hedefler"). Yanıtlanan rapor: `seed-049-genellik-text-rule-and-names-unreadable` → (a) `29e:60-62` (metin kuralı ve
  iki nedenin adı), `29e:58-60` (biçim; önce yol, sonra metin); (b) `29e:57-58` (liste de sayısı da oturuma verilmez),
  `29e:64-65` (denetimden geçmek genelliğin kanıtı değildir); `26c:32` listeyi adlandırır, kimin okuduğunu söylemez; (c)
  `24a:32-33` (hedeflerin kimliği ve türü `/work/logs/targets.json`'da), `24a:54` (`targets/<hedef>/`);
  `targets/names.json`'u okuyan ya da reddeden denetim yoktur. 80 satır sınırı için 2026-11-01 E490–E499 kaydı
  `CHANGELOG-5.md`'ye taşındı.
