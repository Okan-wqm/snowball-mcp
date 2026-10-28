# Kapı Kuralları, Tetik, Döngü İşlemi

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: taslak · Sahibi: operatör
Okunma: her merge ve her state yazımında
Çapa: beklemede: aşama 1 — hakem kapısı iş akışı

---

**Kod PR'ları için ret listesi.** Kapı, `brain/integration` ve beyin reposuna gelen kod PR'larında
şu yollara dokunan diff'leri reddeder: `.github/**`, `.gitattributes`, lint, tip ve test
yapılandırmaları, bağımlılık manifestleri ve lockfile'lar, `<state_root>/**`.

**State için tipli kurallar.** `brain/state`'e yazım yalnız hakem işleriyle ve PR ile olur;
dalın ruleset'i zorla itmeyi ve atlamayı yasaklar ve şu zorunlu kontrolleri ister:

| Yol | Kural |
|---|---|
| `chain/*`, defterler | Yalnız ekleme: önceki satırlar bayt düzeyinde aynı, yeni satırlar zincire bağlı |
| `cases/` | Yalnız ekleme; `provenance` alanı zorunlu; dev vakası silinmez, `withdrawn` satırıyla kapanır |
| `policy.json` | Anayasal bölüm değişmez; performans bölümü yalnız `18`'deki prosedürle ve arşiv yeniden oynatma raporuyla |
| `profile.json` | Hakem işi profili hedef repodan yeniden türetir ve fark alır; güvenlik yolları, hariç dizinler, etkilenen-test komutu ve test yolu kurallarındaki her daralma rakip ve yeniden oynatmadan geçer |
| `docs/`, `status.md` | Yalnız `docs.render` çıktısı; elle düzenleme ret |

**Kapı yeniden koşturur.** Merge kararında kapı oracle raporunu okumakla yetinmez: oracle testini,
etkilenen-test komutunu ve diff-guard'ı kendi işinde yeniden koşturur ve baseline'ı yeniden ölçer.

**Tetik.** Hedef reponun zamanlayıcısı tam döngüyü, her `main` push'u yalnız ucuz basamakları
çağırır. Beyin App'inin, şerit yazarının ve kapının kendi push ve merge'leri döngüyü tetiklemez.

**Döngü bir işlemdir.** Her döngü deftere başlangıç ve bitiş satırı yazar. Bitiş satırı olmayan
döngü çökmüş sayılır; sonraki döngü önce onun worktree'lerini ve kiralarını temizler. Her döngü
hakem kayma denetimiyle başlar: hedef reponun ruleset'leri, atlama aktörleri, App izinleri ve
`brain/*` dallarında sırla koşan iş akışı olmadığı, mühürlü depodaki kurulum özetiyle
karşılaştırılır; fark varsa sert durma (`28`).

**Tavanlar.** Döngü başına ve gün başına PR, merge ve CI dakikası tavanı `policy.json`'dadır.
