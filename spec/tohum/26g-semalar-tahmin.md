# Şemalar, Devam: Kurucu'nun Tahmin Satırı

Tarih: 2026-11-05 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Kurucu defterine `forecast` satırı yazılırken ve imzalı sonucun `forecasts[]`'ı okunurken
Çapa: `seed/bootstrap/snowball_bootstrap/forecast.py`; `founder-ledger.jsonl`'daki `kind: forecast` satırları

---

`26`'nın devamıdır: satır alanları, zincir ve sayı kuralı (kayan nokta yok) oradadır. Bu sayfa `founder` bölümünün
`forecast` satırının yükünü ve önyükleme hakeminin onu imzalı sonuçta nasıl adlandırdığını verir.

**Satır** (`part: founder`, `kind: forecast`): `payload {summary, refs[], forecast}`. `forecast`'ın alanları; hepsi
vardır, başka alan yoktur:

| Alan | Biçim |
|---|---|
| `task` | işin Kurucu'nun verdiği kimliği; 1–200 karakter dizgi |
| `capability` | `can`, `can_with_question` ya da `cannot_with_current_self` |
| `reason` | 1–500 karakter dizgi |
| `p_solve_permille`, `p_accept_first_push_permille` | 0–1000 tamsayı (binde) |
| `horizon_runs` | 1–10 tamsayı |
| `cost_micros`, `turns` | `{p10, p50, p90}`: 0 ya da üstü tamsayılar, `p10 ≤ p50 ≤ p90`; maliyet mikro USD |
| `evidence` | en çok 20 dizgi, her biri 1–200 karakter: benzer geçmiş işlerin kimlikleri |
| `unknowns` | en çok 20 dizgi, her biri 1–500 karakter |

Olasılık kayan nokta olamaz (`26` "Sayılar"): `0.8` taşıyan satır defteri bozar ve push'u
`founder_ledger_invalid:noncanonical` ile reddettirir; `800` binde olarak geçerlidir.

**Söylediği olaylar.** Tahmin, onu adlandıran ve kararı `accepted`, `frozen` ya da `rejected` olan ilk hakem koşusunun
yargıladığı push içindir. `p_accept_first_push_permille` o kararın kabul olmasının olasılığıdır (`accepted` ve `frozen`
1, `rejected` 0). `cost_micros` ve `turns` o push'u yapan oturumun maliyetinin ve turunun 10., 50. ve 90.
yüzdelikleridir (başlatıcının ölçtüğü). `p_solve_permille`, bu koşudan başlayarak en çok `horizon_runs` karar koşusu
içinde aynı `task`'ı adlandıran sayılmış tahminli bir push'un kabul edilmesinin olasılığıdır. Karar vermeyen koşu
(`noop`, kesinti, karar yok) olay değildir; tahmin karar veren sonraki koşuya kalır.

**İmzalı sonuç.** Önyükleme hakemi `none` dışındaki her push'ta, ağacı okunabiliyorsa, defterin son kabul edilmiş
commit'tekinde olmayan (`row_hash`'le) `forecast` satırlarını satır sırasıyla, en yeni 50'si, `forecasts[]`'ta
adlandırır: biçimi tutan satır `{row_hash, line, forecast}`, tutmayan `{row_hash, line, invalid}`. Sonuçtaki `forecast`
sayıları ve `capability`'yi, `horizon_runs`'ı, `task` yerine `task_sha256`'yı (UTF-8 baytlarının sha256'sı), `evidence`
ve `unknowns` yerine `evidence_n` ve `unknowns_n` sayılarını taşır; serbest metin taşımaz. `invalid` ilk bozulan kuralın
adıdır (`unknown_field`, `missing:<alan>`, `field:<alan>`, `payload`, `not_an_object`). Bildirdiği `row_hash` kendi
hash'i olmayan satır adlandırılmaz (defterin denetimi onu adlandırır). `forecasts[]` hiçbir zaman ret nedeni değildir;
defterin kuralları (`26`, `13`) her satırda olduğu gibi geçerlidir.

**Ne sayılır.** Bir koşu yalnız yargıladığı baştaki satırları adlandırır: o koşu başlatıldıktan sonra push'lanan satır o
koşuda yoktur ve onun kararını söyleyemez, sonraki karar koşusunun tahminidir. Daha önce karar veren bir koşuda
adlandırılmış satır yeniden adlandırılsa da ilk koşusuna bağlı kalır. Bir koşunun yeni adlandırdığı satırlardan biçimi
tutan sonuncusu o push'un tahminidir; öbürleri sayılmaz. Sayılmış tahmini olmayan karar koşusu taban oranla puanlanır.
Puanlama beynin dışındadır.
