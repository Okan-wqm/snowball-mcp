# Aşama 0 §0.10 — Çıkış testi (hepsi birlikte PASS)

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: hunt-harness.yml koşu kimliği

---

- Hakem reposunun CI'ı kendi testlerini zamanlayıcıyla ve push'ta koşar; koşu kimliği raporda.
- §0.9'da "Aşama 0" işaretli testler yeşil.
- Hata seti: K0 için dev ≥ 40 ve held-out ≥ 60 mutasyon; en az bir K5 property için ≥ 25
  held-out vakası varsa raporlanır, yoksa Aşama 4 için `UNMEASURABLE` notu düşer.
- Held-out mühürlü depoda, mühür HMAC'li, `looks_used = 0`.
- **Canlı prova ve taban:** taban avcı 0.7 şemasında bulgu üretir; harness onu planted, clean ve
  kanarya snapshot'larında uçtan uca puanlar. Taban recall ve maliyeti `cost-ledger.jsonl`'a
  yazılır; sonraki her avcı tabanı geçmek zorundadır.
- `spec.lint` aracı çalışır ve bu aşamanın spec'ini temiz geçer.
- Tohum rakibi §0.9'daki testleri atlatan bir girdi üretememiştir; en az beş denemesi rakip
  defterindedir.
- Kurulum istisnasıyla yazılan hakem bileşenleri hakem reposunda donmuş, hash'leri raporda;
  çıkış raporu güven kökünün bu olduğunu açıkça yazar.
- Zincir: tüm defterler zincirli, ilk kök hash yazılmış, CI yalnız-ekleme doğrulaması yeşil.
- PASS, bu koşulların CI'da makine tarafından doğrulanmasıdır; imza yoktur. Rapor `asama-0/`
  altına tarihli sayfa olarak girer. PASS'ten sonra operatör kurulumun ikinci bölümünü yapar
  (`tohum/25a`).
