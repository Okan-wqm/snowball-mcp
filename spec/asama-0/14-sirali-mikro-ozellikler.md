# Aşama 0 §0.14 — Sıralı mikro özellikler

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: beklemede: aşama 0 çıkış raporu

---

Her satır tek mekanizmadır, tek oturumda biter, kendi gerçek testiyle gelir ve önyükleme hakeminin
koşusu yeşilken kapanır; sonraki satır öncekinin koşusu yeşilken başlar. Canlı koşular oyuncak
repodadır; hedefe bu aşamada yazılmaz. Test numaraları §0.9'dandır.

1. Zincirli defter yazıcı ve `chain.verify`; test 13.
2. `founder-ledger.jsonl`, 1 ile zincirli.
3. `control.json` okuyucu: kill switch ve bütçe tavanı, kapalıya düşer; test 26.
4. `profile.propose` ve `profile.derive`, fark; test 19.
5. `snapshot.make`; test 8.
6. K0 mutasyon kataloğu, `cases.build` (dev), hunk üzerinden satır eşleme; testler 2, 4.
7. `exit.sample`: gizli tohum, kural sayımı; test 27.
8. `harness.score` ve match-rule v2; testler 1, 6, 7, 12, 14, 28.
9. `harness.baseline` ve taban satırı.
10. LLM yokluğu ve genellik; testler 9, 11.
11. `spec.lint`, `required_exit_rows` denetimi dahil; bu aşamanın spec'i üzerinde.
12. `run.contained`: iç içe ağsız konteyner, dışarıda hash, kırmızı kontrol; testler 20, 21.
13. `deps.fetch`: sırsız, kurulum betikleri kapalı, içerik adresli.
14. `gate.diffguard`; test 23.
15. `gate.check`: artefakt kimliğiyle okuma, yeniden ölçüm, sıfır test kırmızı, mandal, izin
    listesi, sıralı merge.
16. `sentinel.run` ve `gate.revert`; test 25.
17. `drift.check`; test 24.
18. `llm.call`: araçsız, yapılandırılmış çıktılı tek çağrı, bütçe belirteci, sunulan model.
19. `secrets.scan`: diff, defter satırı, giden prompt.
20. `agent.dispatch`: `tohum/24` sözleşmesi; test 22.
21. `ledger.append` (döngü başına tek commit) ve `rekor.anchor`.
22. `gozcu.evaluate` ve `status.block`.
23. `brain.accept`: testler, vektörler ve rakip satırı → kabul SHA'sı ve `accept` satırı.
24. `lock.check`; test 29.
25. `docs.index`.
26. Etkinleştirme provası: aktarım ve etkinleştirme betikleri yerel bir git uzağına ve taklit
    GitHub API'sine karşı uçtan uca.

Sonra çıkış isteği (§0.10).
