# Kurulum, Birinci Bölüm: İnşadan Önce

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: taslak · Sahibi: operatör
Okunma: ilk başlatmadan önce, bir kez
Çapa: mühürlü depodaki kurulum özeti

---

Döngü içinde insan yoktur; döngüden önce iki kısa insan işi vardır. Hepsi listededir; listede
olmayan hiçbir şey sonradan insandan istenmez.

| # | İş | Neden |
|---|---|---|
| 1 | Beyin reposunu ve beyin GitHub App'ini aç; App'in `workflows` izni yok | Oyuncu kendi iş akışını değiştiremesin |
| 2 | Hakem reposunu aç; korumalı dal, zorla itme yok, atlama aktörü yok; beyin App'i yalnız okuma ve PR | Hakem ayrı kalsın |
| 3 | **Hakem App'i**: hakem reposunda yazma, hedef repoda durum kontrolü yazma ve `brain/state`'e PR açma izni; attestation imza anahtarı. Ayrıca **şerit yazarı** kimliği: hakem reposunda yalnız PR | Oyuncu ve hakem aynı kimliği taşımasın; kapıyı yalnız hakem raporlasın |
| 4 | Mühürlü depoyu aç; yalnız hakem exit, rotate ve attestation işleri okuyup yazsın | Held-out gizliliği; hedef repo herkese açık olabilir |
| 5 | Secret store: App anahtarları, sağlayıcı kimliği (tercihen OIDC), HMAC mühür anahtarı ve rotasyon takvimi | Ajan konteynerine hiçbiri girmez |
| 6 | Kill switch: bayrak yeri, App askıya alma yolu, sağlayıcı harcama tavanı; üçünü bir kez dene | Durdurma hakkı |
| 7 | `policy.json` anayasal bölümünü yaz: aylık tavan ve paylar, sınıf başına çıkış tabanları, regresyon dondurma kuralı, döngü ve gün tavanları, yasaklı ifade listesi | Operatörün tek döngü dışı kolu |
| 8 | Kurucu'yu başlat; çalışma ortamı yalnız beyin ve hakem reposuna yazabilir | Aşama 0 inşası |

Bu bölümün özeti (ruleset kimlikleri, App izinleri, kimlikler) mühürlü depoya yazılır; Aşama 0
bu özet olmadan başlamaz.
