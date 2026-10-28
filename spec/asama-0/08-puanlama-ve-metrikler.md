# Aşama 0 §0.8 — Puanlama ve metrikler

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: beklemede: aşama 0 çıkış raporu

---

**`match-rule v2`, sürümlü.**

- **K0–K2:** bulgu, vakayı ancak `tool`, `rule_id` ve hunk üzerinden eşlenmiş satır aynıysa
  isabet eder; dokuz yüz ihlali döken bir adapter tesadüfen isabet alamaz.
- **K3 ve üstü:** `evidence_refs`'ten biri vakanın dokunulan dosyasında ve aynı sembolde ya da
  hunk'ın ±15 satırı içinde; `property` eşit; `required_change` dolu.
- Bir bulgu en fazla bir vakayı, bir vaka bir koşuda en fazla bir kez.

| Metrik | Tanım |
|---|---|
| `recall`, `recall_lb` | İsabet / planted; tek yönlü Clopper–Pearson alt sınırı, etkin n = grup sayısı |
| `clean_findings` | Clean'deki bulgu sayısı; avcı precision'ı hepsini sayar |
| `precision`, `precision_lb` | Oracle'ın karara bağladığı bulgular; `unresolved` FP gibi sayılır |
| `cost_usd`, `value_per_usd` | Şiddet ağırlıklı değer / USD; maliyet sıfırsa oran raporlanmaz, isabet ve kapsama karşılaştırılır |
| `verdict` | `PASS` / `FAIL` / `UNMEASURABLE` |

**Görünümler.** Mühürlü görünüm vaka bazlıdır, yalnız mühürlü depoya yazılır. Ajan görünümü
toplamlardır. Held-out bakışı yalnız verdict, n ve alt sınır döndürür; kaçırma nedenleri yalnız dev
koşularından gelir. **Maliyet defteri** her koşuya satır ekler; Aşama 0'daki okuyucusu harness'in
taban satırıdır, Aşama 3'ten itibaren maliyet merdivenidir.
