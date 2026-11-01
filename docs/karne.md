# Karne: Kendini Geliştirmenin Ölçüsü

Üretilmiş sayfa; elle düzenlenmez (`python seed/founder/scorecard.py --public docs/karne`, E310). Kaynak: `docs/karne.json`. Tanımlar: `8231bb8a286011ad`.

**Kendini geliştirdiği kanıtlandı mı: hayır.** Kanıtı yalnız kontrollü sınav verir (ders provası, `tohum/22a`, `22b`); sınav koşmadı (E317). Aşağıdaki her sayı canlı pilotun gözlemidir: spec, vektörler, rakibin kuralları ve operatörün yardımı yol boyunca değişti; puan toplanmaz, her ölçü kendi derecesiyle okunur.

## Kayıt noktası

Tek an: hakemin son sonucu. Defter o sonucun başında okunur, beynin sonraki commit'lerinde değil.

| Ne | Değer |
|---|---|
| Hakemin son sonucu | koşu 41253144708, 2026-10-31T23:58:29Z, baş `386e856664a3` |
| Kurucu defteri, o başta | 407 satır, zincir doğrulandı; uç `f407` `b670e87ab1e3915d` |
| Hakemin sonuçları | 66; hakem her birini Sigstore'la imzalar, karne imzayı doğrulamaz: her artefaktın zip'i GitHub'ın verdiği özetle denetlenir, özetsiz artefakt karneyi reddeder |
| Veri boşlukları | 1: operatörün yeniden başlatmaları ve talimat değişiklikleri kaydedilmiyor |

## Fiil fiil

| Sahibin fiili | Kontrollü sınav | Pilotun gözlemi | Derece |
|---|---|---|---|
| öğrenir | koşmadı | aynı ret imzasının art arda tekrarı (`repeat_events`) 2, düzeltilmiş 0; rakibin kanıtladığı 9 ayrı kusurdan sonraki bir başta yeniden üretilen 1, düzeltilmiş 0 (kusur yalnız kapanana kadar izlenir) | mekanik |
| öğrendiğini uygular | koşmadı | ilk denemede kabul 14/18 (0,52–0,94), düzeltilmiş 14/17 (0,57–0,96); dönemlere göre aşağıda | gözlemsel |
| yanlışı yanlış bilir | koşmadı | kendi hatasını kendisinin bulduğunun doğrulanmış kaydı yok (E315) | ölçülemez |
| doğruyu doğru bilir | koşmadı | yanlış kararda doğru kodu korumak: mekanik kaydı yok | ölçülemez |
| tartar | koşmadı | derslerin kredisi ve sıralaması: Aşama 0'da ders organı yok | ölçülemez |
| test eder ve uygular | koşmadı | 16 MF'nin testleri modülü olmadan koşuldu: 24 test koşusu (her denemede yeniden), yeşil kalan 0; modülü silmek onu içe aktaran her testi düşürür: bu, testlerin modüllerini içe aktardığını gösterir, davranışını sınadığını değil (E386) | mekanik |

## Birimler (MF)

Bir MF'nin denemeleri, onu ilk ekleyen yargılanmış push'tan kabul edilene kadarki push'lardır. Ret sahibi hakemin kendi kuralıdır (`counts_against_founder`). İşaretli push ve birimler düzeltilmiş sütunda yoktur: ilk denemesi işaretli push olan birim ilk işaretsiz denemesiyle okunur, hiç işaretsiz denemesi yoksa sayılmaz. Her işaret kayıttaki satırıdır.

| MF | Dönem | Deneme | Kurucu'nun reddi | Başka ret | İlk denemede | Düzeltilmiş | İşaret | Başlar |
|---|---|---|---|---|---|---|---|---|
| MF1 | 0 | 1 | 0 | 0 | evet | — | E154 | `ffaa457` |
| MF2 | 0 | 8 | 6 | 1 | hayır | hayır | — | `9f229b0` `1c83fb7` `99278a5` `6e29850` `8265299` `11ebc1e` `d02c924` `99d66a9` |
| MF3 | 0 | 1 | 0 | 0 | evet | evet | — | `fe29a7c` |
| MF4 | 0 | 2 | 1 | 0 | hayır | hayır | — | `30c477e` `6c78821` |
| MF5 | 0 | 1 | 0 | 0 | evet | evet | — | `783c853` |
| MF6 | 0 | 1 | 0 | 0 | evet | evet | — | `da85e6b` |
| MF7 | 1 | 1 | 0 | 0 | evet | evet | — | `11ebd7f` |
| MF8 | 1 | 1 | 0 | 0 | evet | evet | — | `2be80ed` |
| MF9 | 1 | 1 | 0 | 0 | evet | evet | — | `d14b44a` |
| MF10 | 2 | 1 | 0 | 0 | evet | evet | — | `1d5f540` |
| MF11 | 2 | 1 | 0 | 0 | evet | evet | — | `8ddb44d` |
| MF12 | 2 | 1 | 0 | 0 | evet | evet | — | `e02b5f9` |
| MF13 | 2 | 1 | 0 | 0 | evet | evet | — | `b23f497` |
| MF14 | 2 | 1 | 0 | 0 | evet | evet | — | `a049954` |
| MF15 | 2 | 3 | 2 | 0 | hayır | hayır | E248 | `f07f215` `d0dc433` `aa70be0` |
| MF16 | 2 | 2 | 1 | 0 | hayır | evet | E248 | `d0dc433` `aa70be0` |
| MF17 | 2 | 1 | 0 | 0 | evet | evet | — | `6f8cef2` |
| MF18 | 2 | 1 | 0 | 0 | evet | evet | — | `ebc999f` |

## İlk denemede kabul (gözlemsel)

Dönemler tohum dönemleridir: her dönem yeni vektörler ve rakip kuralları getirdi, bu yüzden dönemler arası fark öğrenmeye bağlanamaz. Aralık tam iki yönlü %95 Clopper–Pearson'dur.

| Dönem | Hakemin kuralı | Düzeltilmiş |
|---|---|---|
| 0 | 4/6 (0,22–0,96) | 3/5 (0,15–0,95) |
| 1 | 3/3 (ölçülemez: n < 5) | 3/3 (ölçülemez: n < 5) |
| 2 | 7/9 (0,40–0,97) | 8/9 (0,52–1,00) |
| hepsi | 14/18 (0,52–0,94) | 14/17 (0,57–0,96) |

## Push'lar, kanıtlanmış kusurlar, tekrar

Rakibin kanıtladığı kusur, onu artık göstermeyen ilk kabul edilmiş başa kadar her kod başında yeniden koşulur, sonra kapanır ve bir daha koşulmaz (E08). Kabul edilen başta kusur yeniden üretilemez (o baş reddedilirdi); kabulden sonra geri dönüp dönmediği hiçbir kayıtta yoktur.

| Ölçü | Hakemin kuralı | Düzeltilmiş |
|---|---|---|
| Yargılanan push (spec, kod, çıkış) | 60 (code 59, spec 1) | |
| MF eklemeyen kod push'u | 32 | |
| Kurucu'nun reddettirdiği kod push'u | 14/59 (0,14–0,37) | 10/55 (0,09–0,31) |
| Kanıtlanmış kusur, kapanana kadar yeniden koşulan: ayrı kusur / koşu | 9 / 21 | |
| ... sonraki bir başta yeniden üretilen ayrı kusur | 1 | 0 |
| Kalıcılık: kabul edilmiş işte kapanmış kusurun geri dönmesi | ölçülemez: kapanan kusur bir daha koşulmaz (E320) | |
| Modülü olmadan koşulan test: koşu / MF / yeşil kalan | 24 / 16 / 0 | |
| Tekrar eden ret imzası (`repeat_events`) | 2 | 0 |
| `not_learning` diyen koşu | 0 | |
| Hata sınıfının push'lar arası tekrarı | ölçülemez: donmuş sınıf kimliği yok (E70) | |

## Rakip ve insan dokunuşu

| Ölçü | Değer |
|---|---|
| Rakibin incelediği artefakt: hayatta kalan / çürütülen | 45 / 10 |
| Açık kanıtlanmış kusur / açık iddia (son durum) | 0 / 2 |
| Rakibin bulma gücü (recall) | ölçülemez: ekilmiş kanarya yok (E311); "hayatta kaldı" zayıf kanıttır |
| Tohum dönemi (`seed_update`) | 5 |
| Feragat edilen çürütme | 1 |
| Değerlendirilmeyen koşu (kesinti, yeniden inceleme) | 1 |
| Rakip tarafı yeniden inceleme uyarısı | 0 |

## Defter

Satır türleri (Kurucu'nun kendi beyanı; içerik okunmaz): `blocked` 1, `build` 54, `decision` 150, `diğer` 6, `seed_issue` 75, `session_end` 61, `session_start` 60.

## Girdiler

Hakemin 66 sonucu; her birinin artefakt özeti ve `result.json` hash'i `docs/karne.json`'dadır, herkes aynı girdilerden aynı sayfayı üretir (artefaktlar 90 gün yaşar; operatörün önbelleği onları ve Sigstore paketlerini tutar, `python -m sigstore verify` ile doğrulanır). İşaretler: E154 (`MF1`), E248 (`d0dc433`), E260 (`f668776`), E306 (`957f5f6`), E306 (`2bea567`).
