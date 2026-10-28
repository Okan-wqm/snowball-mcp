# Aşama 0 §0.10 — Çıkış testi (hepsi birlikte PASS)

Tarih: 2026-10-28 · Sürüm: 2.0 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: hunt-harness.yml koşu kimliği

---

- `hunt-harness.yml` hedef repoda zamanlayıcıyla ve push'ta kendi-testleri koşar; koşu kimliği
  raporda. (Reponun kendi test-erişilebilirlik denetimi dış bir paketi göremez; kanıt koşu
  kimliğidir.)
- §0.9'daki zorunlu testler yeşil.
- Hata seti: K0 için dev ≥ 40 ve held-out ≥ 60 mutasyon; en az bir K5 property için ≥ 25
  held-out vakası varsa raporlanır, yoksa Aşama 4 için `UNMEASURABLE` notu düşer.
- Held-out mühürlü depoda, mühür HMAC'li, `looks_used = 0`.
- **Canlı prova ve taban:** taban avcı 0.7 şemasında bulgu üretir; harness onu planted, clean ve
  kanarya snapshot'larında uçtan uca puanlar. Taban recall ve maliyeti `cost-ledger.jsonl`'a
  yazılır; sonraki her avcı tabanı geçmek zorundadır.
- Spec-lint aracı çalışır ve bu aşamanın spec'ini temiz geçer.
- Rakip, §0.9'daki testleri atlatan bir girdi üretememiştir; en az beş denemesi deftere yazılmıştır.
- Zincir: tüm defterler zincirli, ilk kök hash yazılmış, CI yalnız-ekleme doğrulaması yeşil.
- PASS, bu koşulların CI'da makine tarafından doğrulanmasıdır; imza yoktur. Rapor `asama-0/`
  altına tarihli sayfa olarak girer.
