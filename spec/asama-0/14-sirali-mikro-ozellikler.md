# Aşama 0 §0.14 — Sıralı mikro özellikler

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: beklemede: aşama 0 çıkış raporu

---

Her satır tek oturumda biter, kendi gerçek testiyle gelir ve oyuncak repoda bir canlı koşuyla
kapanır; sonraki satır öncekinin koşusu yeşilken başlar.

1. Zincirli defter yazıcı, `chain.verify` ve `founder-ledger.jsonl`; test 13.
2. Tohum koltuklarını `seats/`'e kopyalama ve hash'leme (`tohum/29`).
3. `profile.propose` (beyin) ve hakem türetmesi; test 19.
4. Kill switch okuma ve `drift.check` iskeleti; kurulumun birinci bölüm özetine karşı.
5. `snapshot.make`: çıkarma, hariç tutma, temizleme, manifest; test 8.
6. Mutasyon kataloğu ve `cases.build` (K0), hunk üzerinden satır eşleme; testler 2, 4.
7. Bölme, gizli tohum, HMAC mühür, mühürlü depo, üç iş deseni; testler 15, 18.
8. `harness.score` ve `match-rule v2`; testler 1, 6, 7, 12.
9. `harness.baseline` ve taban satırı.
10. LLM yokluğu ve genellik; testler 9, 11.
11. `spec.lint`; bu aşamanın spec'i üzerinde.
12. `docs.index` üreticisi, `status.md` şablonu, şema testi 14.
13. `hunt-harness.yml` içeriği hakem reposunda; operatör onu `tohum/25a`'da kurar. Hakem CI'ında uçtan uca koşu.
