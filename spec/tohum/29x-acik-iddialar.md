# Açık İddialar: Yaş, Cevap ve Kapanış

Tarih: 2026-11-14 · Sürüm: 2.3 · Durum: taslak · Sahibi: operatör
Okunma: imzalı sonucun `claims` bloğu ya da bir `claim_*` adı okunurken ve bir iddiaya cevap yazılırken
Çapa: `seed/bootstrap/snowball_bootstrap/claims.py`; `decide.py`; `state.py` `claim_book`; `cli.py` `claim_inputs`

---

`29`'un açık iddia kuralının devamıdır (E07, E260); `29t` gibi koşar, `29b`'nin kuralları geçerlidir. Açık iddia,
rakibin bir başa karşı öne sürdüğü ve o başta yeniden üreticisiyle kanıtlanmamış çürütmedir (en çok 10). Cevapsız
iddia kalmaz (sahibin kararı 2026-11-14). Hakem bir iddiaya nasıl cevap verileceğini söylemez; yaşı, cevabın biçimini
ve kapanışı ölçer.

**Yaş.** `accepted_heads`: iddianın açıldığı baştan sonra kabul edilen spec, kod ve çıkış başlarının sayısı;
reddedilen ve `noop` baş sayılmaz, iddiayı kapatan baş sayılır. `days`: açıldığı koşudan bu yana tam gün; yalnız
ölçüdür, hiçbir kural onu okumaz. Bu kuraldan önce açılmış iddianın yaşı ilk başından sonra rakipten sağ çıkan
başların sayısıyla başlar (yaklaşık), günü ilk başın commit zamanındandır; `basis` bunu `seeded` diye, sonra açılanı
`run` diye adlandırır.

**Gecikme.** Cevapsız iddia, `accepted_heads`'i `stage_params`'ın `rival_min_attempts`'ine (`18a`) ulaşınca
gecikmiştir. Sayı çıkışın kendi güven penceresidir (`asama-0/10` #rakip): bir baş, ondan sonra o kadar baş rakipten
sağ çıkınca güvenilir sayılır; o noktada ona karşı cevapsız bir şüphe varsa güven o şüphenin üstünde durur. Yeni sabit
yoktur: operatör ölçüyü değiştirirse eşik de değişir. Aşama 0'da (`setup/stage.json` yok) gecikmiş iddia
`claim_overdue:<id>` uyarısıdır; karar, ret nedenleri ve kabul edilmiş çıkış değişmez. Kilit Aşama 1'i açınca
(`asama-0/10a`) aynı ad ret nedenidir (`ref` `claim:<id>`, `detail` `accepted_heads` ve `days`); Kurucu'nun
düzeltebildiği rettir ve ret hafızasında sayılır (`29b`). Kural bu başın öncesini okur: cevabı taşıyan baş o
iddia için reddedilmez.

**Cevap.** `reports/claim-<id>.json`, kökte, Kurucu kaydıdır (`29e`): `{id: claim-<id>, kind: claim_answer, ref: <id>,
state: answer, answer: fix|refute, evidence_refs: [{path, line_start, line_end}], note?}`; en çok 5 kanıt satırı, `note`
en çok 2000 karakterdir ve yalnız operatörün okumasıdır. Hakem cevabı mekanik sınar: biçim; her kanıt satırı koşulan
başın ağacında vardır; `fix` iddianın ilk başından bu yana değişmiş bir dosyayı, iddianın kanıt yolu varsa onlardan
değişmiş birini (`fix_cites_no_claim_change`), `refute` iddianın kendi kanıt yollarından birini anar. Tutmayan cevap
`claim_answer_invalid:<id>` uyarısıdır, ret nedeni değildir. Geçerli cevap gecikmeyi durdurur, iddiayı kapatmaz: Kurucu
rakibin iddiasının yargıcı değildir (Y6) ve seçtiği bir komut bir şey kanıtlamaz (Y8; değişen tek bir yorum satırı her
komutu iki başta farklı gösterebilir). Cevap bekleyen iddiaların sayısı operatöre `claims_answered:<n>` uyarısıyla
gider.

**Cevabın düşmesi.** Operatör bir cevabı reddeder (`control.json` `refused_answers`, dosyanın sha256'sı) ya da rakip
cevaptan sonra iddiayı yeniden gönderir (`open_claim`, `29`; sayaç `challenged`): o baytlar o iddiaya bir daha cevap
sayılmaz ve yaş hiç durmadığı için gecikme kuralı hemen yeniden okunur. Yeni baytlar yeni cevaptır.

**Kapanış.** Üç yoldur ve `claims.closed`'ta ayrı sayılır:
- `observed`: iddianın kayıtlı yeniden üreticisi kabul edilen başta sonuna dek koştu, belirtiyi göstermedi, kendi
  doğru çıktısını gösterdi. Tutma işidir, kanıt değildir (`29`); rakip aynı iddiayı yeniden açabilir, dönen kimlik
  `reopened`'ı artırır.
- `proven`: rakip iddiayı yeniden üreticisiyle kanıtlar; kusur olur (`29`, E08).
- `operator`: operatör iddia kimliğini `control.json` `waived_claims`'e yazar; her koşuda işler.
Sınırın düşürdüğü iddia (`claim_evicted`) kapanmış sayılmaz, `evicted`'a girer.

**Ölçü.** Sonucun her türünde (`noop` dahil) `claims`: `{open, answered, overdue, closed {observed, operator, proven,
total}, closed_now, evicted, reopened, challenged, time_to_close {n, median_accepted_heads, median_days}, window,
items [{id, status, accepted_heads, days, basis, answer}]}`; blok bu baştan sonrasını söyler. İddia metni bloğa girmez
(`state.open_claims`'te kalır). İddia başına yaş, sayaçlar ve son 50 kapanış imzalı durumun isteğe bağlı
`claim_book`'undadır; yoksa boş sayılır, bu kuraldan önce imzalanmış her durum olduğu gibi geçerlidir. Sayılar
ölçüdür; kapı yalnız gecikmedir.

**Sınırlar.** Cevap mekanik sınanır, doğruluğu sınanmaz: ucuz bir cevap gecikmeyi durdurur; onu operatör
`refused_answers` ile ya da rakip yeniden göndererek düşürür. Tembel rakip ve okunmayan uyarı bunu açık bırakır;
`claims_answered` ve `challenged` onu ölçer, önlemez. Yeniden üreticisi olmayan iddiayı yalnız rakip ya da operatör
kapatır. `observed` kanıt değildir. Tohumlanmış yaş yaklaşıktır, günü Kurucu'nun commit zamanından gelebilir.
