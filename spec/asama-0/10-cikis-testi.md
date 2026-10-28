# Aşama 0 §0.10 — Çıkış testi (hepsi birlikte PASS)

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: beklemede: aşama 0 — önyükleme hakemi koşu kimliği; etkinleştirme genesis satırı

---

Çıkış iki parçalıdır; ikisi birlikte `PASS`'tır. Hiçbir koşul Kurucu'nun beyanıyla kapanmaz.

## (A) Pinli SHA'da önyükleme hakemi

Kurucu çıkış isteğini beyin reposunda tipli bir dosyayla yapar; önyükleme hakemi o SHA'yı pinler ve
şunları makine doğrulamalı olarak koşu artefaktlarına ve Rekor'a yazar:

- §0.9'da "Aşama 0" işaretli testler yeşil; tohum vektörleri geçer; kırmızı kontrol kırmızı.
- Tohum rakibi en az beş deneme yapmış; hiçbir çürütmesi hakemin `koş`ta yeniden koşturduğu bir
  yeniden üreticiyle doğrulanmamış. Zaman aşımı, ret ve `unresolved` kabul değildir; deneme
  sayısına girmez.
- `spec.lint` bu aşamanın spec'ini temiz geçer, `required_exit_rows` dahil.
- Etkinleştirme provası (yerel git uzağı, taklit GitHub API'si) yeşil.
- Pinli SHA ile çıkış koşusu arasında beyin reposunda değişiklik yok.

## (B) Aktarım ve etkinleştirme (`tohum/25a`)

- Operatör aktarım betiğini koşar: hakem reposundaki yeni ağaç, pinli SHA'nın `referee/` ağacıyla
  aynıdır; oyuncak hedefin `main`'i `tests/fixtures/toy-repo/` ağacıdır.
- Aktarılan hakem oyuncak hedefte ve gerçek hedefte `brain/state`'i genesis satırıyla açar: hakem
  ağaç hash'i, tohum hash'i, anayasal politika hash'i, kurulum özeti hash'i, (A) sonuçlarının Rekor
  kimlikleri. `brain/integration` `main`'den kesilir.
- **Oyuncak hedefte canlı döngü:** hazır iyi aday kapıdan geçip `brain/integration`'a merge olur;
  hazır kötü aday reddedilir; nöbetçi yeşil; `drift.check` yeşil; kök hash Rekor'da.
- **Gerçek hedefte:** profil türetilir, K0 dev vakaları `cases/`'e yazılır; taban avcı koşar,
  taban recall ve maliyeti `cost` bölümüne yazılır. Sonraki her avcı tabanı geçmek zorundadır.
- PASS satırını aktarılan hakem `brain/state`'e yazar. Çıkış raporu bu satırın kopyası olarak
  `asama-0/` altına tarihli sayfa olarak girer; hash'i satırla eşleşmezse `spec.lint` kırmızıdır.
- Rapor güven kökünü açıkça yazar: önyükleme hakemi, tohum vektörleri, tohum rakibi ve operatör
  aktarımı. İnsan dokunuşu sayacı (aktarım sayısı) raporun başındadır.

**Başarısızlık.** (A) kırmızıysa Kurucu düzeltir ve yeni SHA için yeniden ister. (B) kırmızıysa
sistem sert durur; düzeltilmiş SHA'nın aktarımı yine operatörün işidir ve sayaca eklenir.

PASS bir imza değil, bu koşulların makine doğrulamasıdır. PASS'ten sonra hakem kodu yalnız
operatör aktarımıyla, aşama çıkışında değişir (`tohum/01a`).
