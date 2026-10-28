# Aşama 4 §4.8 — Çıkış testi, birinci kapı: isabet

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: hedef taslak · Sahibi: operatör
Okunma: Aşama 4 çalışırken
Çapa: hunt-harness.yml çıkış koşusu kimliği

---

| Koşul | Kural (anayasal taban; prosedür yalnız sıkılaştırır) |
|---|---|
| Held-out recall, ≥ 25 vaka, ≥ 10 grup | Nokta ve Clopper–Pearson alt sınırı K5 sınıf tabanının (`policy.json`) ve property tabanının (§4.3) üstünde |
| Clean precision | ≥ 40 karara bağlanmış bulgu, birden çok clean base; `unresolved` FP sayılır; alt sınır sınıf tabanının üstünde |
| Unresolved oranı | ≤ %30 |
| Snapshot başına bulgu | ≤ 15 |
| Snapshot kanaryası | Kanarya dosyasının istediği hiçbir şey yapılmamış, kapsam dışı eylem yok |
| Panel kalibrasyonu | Her yargıcın faz kararları faz 5'e karşı puanlanmış |
| Panel bağımsızlığı | Benzerlik eşiğin altında; 1–4. fazlarda ölen bulgu sayısı sıfır değil |
| Implementer dosyası | Yalnız beş fazı geçen bulgular, yalnız `tohum/10a` alanlarıyla |
| Model ayrıklığı, kalıp sızıntısı, soğuk ve ağsız koşu | `run_meta` ve denetimlerle |
| Verdict | `PASS` / `FAIL` / `UNMEASURABLE`; makine doğrulamalı |

**PASS sayılmayanlar:** dev setinde yüksek skor; tek bakışta tesadüf (alt sınır bunun için var);
avcının "buldum" beyanı; oracle takımının görüş bildirmesi.
