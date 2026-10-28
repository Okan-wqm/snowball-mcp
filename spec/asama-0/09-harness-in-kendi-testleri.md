# Aşama 0 §0.9 — Harness'in kendi testleri

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: beklemede: aşama 0 çıkış raporu

---

| # | Test | Ne zaman |
|---|---|---|
| 1 | Boş bulgu → recall 0, hata yok | Aşama 0 |
| 2 | Oracle bulguları → recall 1,0 | Aşama 0 |
| 3 | Doğru dosya, yanlış property → 0 | K3 ile |
| 4 | Doğru dosya, eşlenmiş satır farklı → isabet değil (K0); sembol dışı → değil (K3) | Aşama 0 |
| 5 | `required_change` boş → 0 | K3 ile |
| 6 | Manifest dışı ya da hash uyuşmayan ref → red, raporlanır | Aşama 0 |
| 7 | Determinizm: aynı girdi iki kez → aynı rapor | Aşama 0 |
| 8 | Sızıntı: `.git`, `<state_root>`, hariç dizinler yok; planted kimlikleri temizlenmiş | Aşama 0 |
| 9 | LLM yokluğu: hakem harness'i istemci import etmez, ağ kapalıyken geçer | Aşama 0 |
| 10 | Maliyet: `run_meta` eksikse `invalid`; isabet sıfırken `value_per_usd` 0; maliyet sıfırken oran yok | Aşama 3 ile |
| 11 | Genellik: oyuncak repoda `<state_root>` sıfırdan büyür; hedef repoya özgü ad yok, tohum dahil | Aşama 0 |
| 12 | Parmak izi: aynı bulgu iki koşuda tek sayılır; satır kayması kimliği değiştirmez | Aşama 0 |
| 13 | Zincir: bozulmuş satır ve yalnız-ekleme ihlali yakalanır | Aşama 0 |
| 14 | Şema: her artefakt `tohum/26` şemalarına uyar | Aşama 0 |
| 15 | Held-out erişimi: held-out `harness.score` hakem exit işi dışından reddedilir | Aşama 0 |
| 16 | Snapshot kanaryası | Aşama 1 ile |
| 17 | Görünümler: itibar, ders sayaçları, kapsama defterden sıfırdan kurulur ve aynı çıkar | Aşama 1 ile |
| 18 | Held-out hesaplanamaz: dev çıktısı ve araç kodu verilmiş bir saldırgan, havuzdan held-out üyeliğini şanstan iyi tahmin edemez | Aşama 0 |
| 19 | Profil yeniden türetme: önerilen profil hakem türetmesinden daralıyorsa reddedilir | Aşama 0 |
