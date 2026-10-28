# Aşama 4 §4.5 — Avcının bildiği ve çıktısı

Tarih: 2026-10-28 · Sürüm: 2.0 · Durum: hedef taslak · Sahibi: operatör
Okunma: Aşama 4 çalışırken
Çapa: beklemede: aşama 4 çıkış raporu

---

**Bilir:** property spec; snapshot (geçmişsiz, ID'leri temizlenmiş); bulgu şeması; harita
katmanları (a) ve (b); ilgili dersler ipucu olarak.

**Veri olarak okuyabilir:** reponun yönerge ve karar dosyaları, kod, testler. "Yönerge şunu
yasaklıyor" bir kanıt değil, kodda doğrulanacak bir iddiadır.

**Bilmez:** hangi snapshot'ın clean olduğu; kaç vaka yerleştirildiği; vaka listesi; harness
kaynağı; fix commit geçmişi.

**Çıktı:** `findings.jsonl` (`asama-0/07`, `required_change` yapısal); `repo_model.md`: avcının
bu koşuda P için bulduğu mekanizmalar, her satır bir `evidence_ref` ile; harness puanlamaz,
harita adapter'ları aday kenar olarak okur. `run_meta.json`: `previous_run_ref` her zaman boş.
