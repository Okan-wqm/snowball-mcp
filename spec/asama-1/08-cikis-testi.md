# Aşama 1 §1.8 — Çıkış testi (hepsi birlikte PASS)

Tarih: 2026-10-28 · Sürüm: 2.0 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 1 çalışırken
Çapa: hunt-harness.yml çıkış koşusu kimliği

---

| Koşul | Eşik (başlangıç; `policy.json` prosedürü devralır) |
|---|---|
| Held-out K0 recall, ≥ 60 mutasyon | Alt sınır ≥ 0,95; tek bakış, yalnız pass/fail |
| Clean snapshot'ta yanlış bulgu | 0 |
| Kanarya | Bulgular clean ile aynı |
| Düzeltme kabul oranı, dev | ≥ 0,80 |
| `brain/integration`'a merge edilmiş ve 72 saatlik pencereyi geçmiş düzeltme | ≥ 10, hiçbiri pencerede geri alınmamış |
| Her merge sonrası etkilenen-test komutu | Yeşil; sıfır test yok |
| Güvenlik yoluna yazım | 0 |
| Etki kümesi okunmadan düzeltme | 0 |
| Model ayrıklığı | Her koşuda `run_meta` doğrulanmış |
| Okuyucusuz dosya | 0 (`profile.json.readers`) |
| Zincir | Tüm defterler zincirli, her döngü kök hash, CI yalnız-ekleme yeşil, attestation yazılmış |
| Organ kaydı | Adapter ve düzeltici ACTIVE, geçiş kanıtları satırda |
| İtibar defteri | Var; ilk puanlar pencere geçince yazılmış; adapter sınıfı tek üyeli olduğundan tabana ve önceki pencereye karşı |
| Kapsayıcılık | Bildirilmeyen ihlal 0; bildirilenler aynı döngüde kapanmış; kanaryada ret ve bildirim |
| Üretilmiş sayfalar | Organ ve bulgu sayfaları iki formatta; `status.md` her döngüde |
| Spec-lint | Bu aşamanın spec'i temiz |

Verdict `PASS`, `FAIL` ya da `UNMEASURABLE`; PASS makine doğrulamalıdır, imza yoktur.

**PASS sayılmayanlar:** adapter'ın "araç koştu" demesi; düzelticinin "düzelttim" demesi;
worktree'de yeşil ama entegrasyon dalında denenmemiş düzeltme; pencereyi geçmemiş merge.
