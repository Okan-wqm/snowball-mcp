# Politika Dosyası ve Dinamik Eşikler

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: taslak · Sahibi: operatör
Okunma: her kapı kararında ve her eşik değişikliği önerisinde
Çapa: beklemede: aşama 0 — policy.json ve zincirdeki hash geçmişi

---

Eşik sayı değil, prosedürdür. Ama sistem kendi eşiğini serbestçe oynatabilseydi ilk işi eşiği
her şeyin geçeceği yere çekmek olurdu. Organizma benzetmesi tam bunu söyler: vücut ısısı
dinamiktir, termostatın kuralı ve canlılık sınırı sabittir.

## policy.json ne tutar

Tek hash'li dosya; şeması `26`'da. Her kapı kararı onu okur, değişikliği zincire yazılır.

| Sınıf | İçerik | Kim değiştirir |
|---|---|---|
| Anayasal | Aylık tavan ve paylar, **sınıf başına çıkış ve merge tabanları**, regresyon dondurma kuralı, döngü ve gün tavanları, güvenlik yolu listesi, yasaklı ifadeler, aşama sırası | Yalnız operatör |
| Performans | SHADOW, ACTIVE, genesis ve sıralama kararlarının eşikleri; pencere uzunlukları; merdiven sırası; itibar parametreleri | Prosedür; değişiklik çekişme protokolünden geçer |

Performans eşikleri kural olarak yazılır, örnek:

- `recall_gate`: "anayasal tabanın ve taban avcının alt sınırının büyüğü + gürültü marjı".
- `precision_gate`: "clean koşularda gözlenen dağılımın Q yüzdeliği; en az anayasal taban".
- `shadow_min_runs`: "pencere başına koşu sayısının yarısı, en az 3".

## Yönlülük

- **Çıkış ve merge kapıları yalnız sıkılaşabilir.** Prosedür bu kapılarda eşiği anayasal tabanın
  altına indiremez; tabanın üstünde yalnız yukarı oynar. Bir organın kendi sonucu kendi kapısını
  belirleyemez: `recall_gate` üretim basamağının değil, tabanın ve taban avcının sayılarına bakar.
- **Diğer kararlarda iki yönlü.** SHADOW, genesis tetikleri ve sıralama eşikleri veriyle iki yöne
  oynar; bunlar eylemi değil dikkat ve sırayı yönetir.
- **Eşik keşfi durdurmaz.** Eşiğin altında kalan organ SHADOW'da koşar ve ölçülür; bulguları
  atılmaz, yalnız karara girmez. "Bu pencerede hiçbir şey geçmedi" bir sonuçtur ve gap sinyalidir.

## Eşik değişikliği bir artefakttır

Çekişme protokolünden geçer. Oracle'ı **dev arşivinde yeniden oynatmadır**: önerilen kural
geçmiş kararlara uygulanır; geri alınmış bir işi geçirecek ya da hayatta kalmış bir işi
düşürecek kural reddedilir. Hayatta kalma etiketi olmayan, eski kuralla geçmiş işler geri alınmış
sayılır. Gözcü kümülatif kaymayı izler: bir eşiğin başlangıçtan bu yana net hareketi `policy.json`'daki
sınırı aşarsa işaret yazar; işaretin okuyucusu şerit yazarıdır. Her değişiklik zincire yazılır;
`chain.asof` ile "o gün eşik neydi" görülür.
