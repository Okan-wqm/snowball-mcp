# Politika Dosyası ve Dinamik Eşikler

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: her kapı kararında, her aşama spec'i dondurulurken ve her eşik değişikliği önerisinde
Çapa: beklemede: aşama 0 — hakem reposundaki policy.json ve kök kayıtlarındaki hash'i

---

Eşik sayı değil, prosedürdür. Ama sistem kendi eşiğini serbestçe oynatabilseydi ilk işi eşiği
her şeyin geçeceği yere çekmek olurdu. Organizma benzetmesi tam bunu söyler: vücut ısısı
dinamiktir, termostatın kuralı ve canlılık sınırı sabittir.

## policy.json ne tutar

Tek hash'li dosya; şeması `26b`'de, başlangıç değerleri `18a`'da. Her kapı kararı onu okur.

| Bölüm | İçerik | Kim değiştirir |
|---|---|---|
| Anayasal | Aylık USD ve CI dakikası tavanları, oturum tavanı ve paylar; **sınıf başına çıkış ve merge tabanları**; `required_exit_rows`; non-inferiority marjı ve eşli test asgarileri; hayatta kalma pencereleri; regresyon dondurma kuralı; döngü ve gün tavanları; güvenlik anahtar kelimeleri; yasaklı ifadeler; aşama sırası; bakış bütçesi; güven düzeyi | Yalnız operatör, hakem reposunda. Hash'i her kök kaydında ve Rekor'dadır; `drift.check` doğrular |
| Performans | SHADOW, genesis ve sıralama eşikleri; pencere uzunlukları; merdiven sırası; itibar parametreleri; sinyal eşikleri | Prosedür; değişiklik çekişme protokolünden geçer |

Performans eşikleri kural olarak yazılır, örnek:

- `recall_gate`: "anayasal tabanın ve taban avcının alt sınırının büyüğü + gürültü marjı".
- `precision_gate`: "clean koşularda gözlenen dağılımın Q yüzdeliği; en az anayasal taban".
- `shadow_min_runs`: "pencere başına koşu sayısının yarısı, en az 3".

## Yönlülük

- **Eylemi kapılayan eşikler yalnız sıkılaşır** (Y11): çıkış ve merge tabanları, kapının izin
  listesine giriş eşikleri, hayatta kalma pencereleri. Hepsi anayasal bölümdedir; prosedür bunları
  tabanın üstünde yalnız yukarı oynatır. Bir organın kendi sonucu kendi kapısını belirleyemez:
  `recall_gate` üretim basamağının değil, tabanın ve taban avcının sayılarına bakar.
- **Diğer kararlarda iki yönlü.** SHADOW, genesis tetikleri, sinyal ve sıralama eşikleri veriyle iki
  yöne oynar; bunlar eylemi değil dikkat ve sırayı yönetir.
- **Eşik keşfi durdurmaz.** Eşiğin altında kalan organ SHADOW'da koşar ve ölçülür; bulguları
  atılmaz, yalnız karara girmez. "Bu pencerede hiçbir şey geçmedi" bir sonuçtur ve gap sinyalidir.

## Yeteneğe anahtarlı çıkış satırları

`required_exit_rows` anayasaldır. Bir aşama yeni bir yetenek getiriyorsa spec'i o yeteneğin
satırlarının hepsini çıkış testinde taşır; `spec.lint` bir satırı eksik spec'i reddeder (`02`).

| Yetenek | Zorunlu çıkış satırları |
|---|---|
| Her aşama | `spec.lint` temiz; `lock.check`; her döngü zincir ve Rekor kökü; her döngü `drift.check`; okuyucusuz dosya 0; her koşuda kırmızı kontrol kırmızı |
| Çalışma-zamanı LLM çağrısı | Sunulan model doğrulanmış; koşu başına bütçe belirteci; giden prompt taranmış |
| Araç kullanan çalışma-zamanı ajanı | Dispatch kanaryası yeşil; kapsayıcılık özetleri; sandbox kanaryası |
| Entegrasyona merge | En az bir canlı merge; hayatta kalma penceresi; mandal; sıfır test kırmızı; nöbetçi |
| Held-out havuzu | Mühür; havuz başına bakış bütçesi; ileriye dönük kesim; ham artefakt mühürde; üyelik testi (`19`) |
| LLM avcı | Clean ve planted snapshot kanaryası; kalıp sızıntısı denetimi; `human_fix` katman tabanı |
| Panel | Yargıç kalibrasyonu; bağımsızlık ölçümü |
| Güvenlik yoluna dokunma | K6 kapısı; özel, çatallanmamış ayna (`15`) |
| Daha ucuz basamak | Tam non-inferiority testi, δ ve n ≥ 45 (`19`) |

## Eşik değişikliği bir artefakttır

Çekişme protokolünden geçer. Oracle'ı **dev arşivinde yeniden oynatmadır**: önerilen kural
geçmiş kararlara uygulanır; geri alınmış bir işi geçirecek ya da hayatta kalmış bir işi düşürecek
kural reddedilir. Hayatta kalma etiketi olmayan, eski kuralla geçmiş işler geri alınmış sayılır.
Gözcü kümülatif kaymayı izler: bir eşiğin başlangıçtan bu yana net hareketi `rules.drift_bound`'u
aşarsa bir **Gözcü işareti** yazar; bu dondurma değildir, işaretin okuyucusu şerit yazarıdır.
Her değişiklik zincire yazılır; "o gün eşik neydi" sorusunun cevabı defterdedir.
