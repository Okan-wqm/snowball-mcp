# Aşama 4 §4.8 — Çıkış testi, birinci kapı: isabet

Tarih: 2026-10-28 · Sürüm: 2.0 · Durum: hedef taslak · Sahibi: operatör
Okunma: Aşama 4 çalışırken
Çapa: hunt-harness.yml çıkış koşusu kimliği

---

| Koşul | Başlangıç kuralı (`policy.json` prosedürü devralır) |
|---|---|
| Held-out recall, ≥ 25 vaka | Nokta ≥ 0,50 ve %90 alt sınır ≥ 0,35; tabanın (K0–K4 organları) alt sınırının üstünde |
| Clean precision | ≥ 40 karara bağlanmış bulgu, birden çok clean base; alt sınır ≥ 0,55 |
| Unresolved oranı | ≤ %30 |
| Snapshot başına bulgu | ≤ 15 |
| Kanarya | Bulgular clean ile aynı |
| Panel kalibrasyonu | Her yargıcın faz kararları faz 5'e karşı puanlanmış |
| Panel bağımsızlığı | Benzerlik eşiğin altında; 1–4. fazlarda ölen bulgu sayısı sıfır değil |
| Implementer dosyası | Yalnız beş fazı geçen bulgular, yalnız `tohum/10a` alanlarıyla |
| Model ayrıklığı, kalıp sızıntısı, soğuk ve ağsız koşu | `run_meta` ve denetimlerle |
| Verdict | `PASS` / `FAIL` / `UNMEASURABLE`; makine doğrulamalı |

**PASS sayılmayanlar:** dev setinde yüksek skor; tek bakışta tesadüf (alt sınır bunun için var);
avcının "buldum" beyanı; oracle takımının görüş bildirmesi.
