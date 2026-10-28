# Politika Dosyası ve Dinamik Eşikler

Tarih: 2026-10-28 · Sürüm: 1.0 · Durum: taslak · Sahibi: operatör
Okunma: her kapı kararında ve her eşik değişikliği önerisinde
Çapa: `<state_root>/policy.json` ve onun zincirdeki hash geçmişi

---

Eşik sayı değil, prosedürdür. Sistem kendi eşiğini serbestçe oynatabilseydi ilk işi eşiği her
şeyin geçeceği yere çekmek olurdu. Organizma benzetmesi tam bunu söyler: vücut ısısı dinamiktir,
termostatın kuralı sabittir.

## policy.json ne tutar

Tek hash'li dosya; her kapı kararı onu okur, değişikliği zincire yazılır. İçinde iki sınıf
vardır:

| Sınıf | Ne | Kim değiştirir |
|---|---|---|
| Anayasal | Regresyon oranı dondurması, aylık bütçe tavanı ve payları, güvenlik sınırı bloğu, kapsayıcılık, aşama sırası | Yalnız operatör |
| Performans | Recall, precision, maliyet, itibar, SHADOW süresi, pencere uzunlukları, merdiven sırası | Prosedür; değişiklik çekişme protokolünden geçer |

Performans eşikleri değer olarak değil, kural olarak yazılır. Örnekler:

- `recall_gate`: "taban avcının alt sınırının üstü + gürültü marjı; en az son üç pencerede
  üretim basamağının alt sınırı".
- `precision_gate`: "clean koşularda gözlenen dağılımın Q yüzdeliği; en az anayasal taban".
- `shadow_min_runs`: "pencere başına koşu sayısının yarısı, en az 5".

Başlangıç sayıları yalnız ilk pencere içindir. İlk ölçüm gelince prosedür devralır.

## Eşik keşfi durdurmaz

Eşik eylemi kapılar, keşfi değil. Eşiğin altında kalan organ SHADOW'da koşmaya ve ölçülmeye
devam eder; bulguları atılmaz, yalnız karara girmez. "Bu pencerede hiçbir şey geçmedi" bir
sonuçtur: nedeni yazılır ve gap sinyali olarak genesis'e gider (`17-kas-buyutme-sinyalleri.md`).
Yanlış bir eşik bulguyu değil, eylemi geciktirir.

## Eşik değişikliği bir artefakttır

Çekişme protokolünden geçer (`10-cekisme-protokolu.md`). Oracle'ı **arşivde yeniden
oynatmadır**: önerilen kural zincirdeki geçmiş kararlara uygulanır. Geri alınmış bir işi
geçirecek ya da hayatta kalmış bir işi düşürecek kural reddedilir. Bu Pareto kuralıdır: sistem
eşiği oynatabilir, kendi lehine oynatamaz. Gözcü, eşiklerin yalnız tek yöne hareket ettiği
pencereleri işaretler; sürekli gevşeme oyun izidir.

## Aynı ilke her yerde

Prosedür sabit, değer dinamik ayrımı bütçe paylarına, pencere uzunluklarına, SHADOW süresine
ve merdiven sırasına da uygulanır. Hiçbiri sayfalarda sabit sayı olarak yaşamaz; hepsi
`policy.json`'da kural olarak durur ve `as-of` ile "o gün ne idi" sorgulanabilir.
