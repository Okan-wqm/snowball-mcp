# Aşama 0 §0.14 — Sıralı mikro özellikler

Tarih: 2026-10-28 · Sürüm: 2.0 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: beklemede: aşama 0 çıkış raporu

---

Her satır tek oturumda biter, kendi gerçek testiyle gelir ve oyuncak repoda bir canlı koşuyla
kapanır; sonraki satır öncekinin koşusu yeşilken başlar.

1. `profile.json` üretimi ve şeması; oyuncak repoda kanıt.
2. Zincirli defter yazıcı ve `chain.verify`; test 13.
3. `snapshot.make`: arşiv, hariç tutma, ID temizleme, manifest; test 8.
4. Mutasyon kataloğu ve `cases.build` (K0); geçerlilik = fark; test 2, 4.
5. dev/held-out bölme, HMAC mühür, mühürlü depo yazımı; test 15.
6. `harness.score` ve `match-rule v2`; testler 1, 6, 7, 12.
7. `harness.baseline` ve taban satırı; test 10'un K0 kısmı.
8. Kanarya snapshot; test 16 (Aşama 1'de zorunlu olur).
9. `spec-lint`; bu aşamanın spec'i üzerinde çalıştırılır.
10. `docs.index` üreticisi ve `status.md` şablonu.
11. `hunt-harness.yml` şablonu; CI'da uçtan uca koşu, koşu kimliği raporda.
12. Genellik testi (test 11) ve şema testi (test 14) son olarak; hepsi birlikte PASS.
