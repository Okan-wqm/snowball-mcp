# Değişiklik Günlüğü — Tohum, 2.2'nin İkinci Kayıtları

Tarih: 2026-11-01 · Sürüm: 2.2
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

- 2.2 (2026-10-30, E64, E65, E317–E319; sahibin onayı, uzman tartışmasıyla daraltıldı): ders provasında aileler gizli,
  taahhüt edilmiş havuzdan gelir, donan yalnız sözleşmeleridir (`22a`, yeni `22b`); dersin kapsamı tek eşleyiciyle açık
  gözlemlerden yargılanır (E64); plasebo kollarını hakemin tohumu çeker, etki ve plasebo kolları eşit koşar (E65); yeni
  soru doğru ders (E318); k = 30, aile ≥ %85 kalibrasyonla girer, risk alt sınırda da verilir (E319, `18a`, yeni `29q`).
  Provayı gerçek beyinde öne almak aşama planını değiştirir, sahibin kararıdır (E317).
- 2.2 (2026-10-30, E301; sahip): hedefin ve sistemin kendi kodunun haritası insan okunur çizim olarak da üretilir, kodla yenilenir (`15` 4).
- 2.2 (2026-10-30, E280, E282, E287, E293, E294, E296, E297): Aşama 0 çıkışının karar verilemeyen koşulları.
  Kurucu defterinde kapatma, emekliliğin defterdeki karşılığı olan yeni kural: hakemin kabul ettiği ama anlam
  kurallarından birini (`part`, `kind`, `supersedes`) bozan satır silinmez, sonraki geçerli satır `supersedes`'iyle
  onun `row_hash`'ini adlandırarak onu kapatır; bayt ve zincir kırığı kapanmaz, kurcalama kanıtıdır; push'un eklediği
  bozuk satır kapatılsa da reddedilir; kapatılmamış anlam kırığı çıkışı kapalı tutar ve Kurucu'nundur; defterin
  içeriği değil yapısı denetlenir (`13`, `26`). Tohumun `control` komutunun döngü arayüzü: çağrı, çıkışlar, `go`,
  her işin bayt bayt ilk adımı ve `wiring` kuralı; kill switch ya da fren işi kırmızı durdurur, `loop_schedule`
  kapalıyken zamanlanmış koşu `paused`; adımın üstünde yalnız kuralın saydığı anahtarlar durur (`services` ve
  `container` ilk adımdan önce başlar) (yeni `29p`; `08`, `00b`). Sahip istisnası: ölçümü aşama başlamadan yapılacak
  bir işe dayanan koşul (bugün yalnız #durustluk) o iş yapılmadıysa adıyla istisna edilir; geçmiş ya da
  `UNMEASURABLE` sayılmaz, sonraki aşamanın çıkışına taşınır, ikinci istisna yoktur, insan dokunuşudur; yanında
  taşıma hedefinin ekiminin taahhüdü yoksa koşulu kaldırmaz (`02`, `26c`, `27`). Aşama 0'ın ilk durumu, durum
  kaybolunca da, kopya hedefin `identifiers`'ı ve `honesty_commitment` olmadan kurulmaz (`25`). 80 satır sınırı için
  2026-10-28 kaydı `CHANGELOG-2.md`'ye taşındı.
