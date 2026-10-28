# Aşama 0 §0.8 — Puanlama ve metrikler

Tarih: 2026-10-28 · Sürüm: 2.0 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: beklemede: aşama 0 çıkış raporu

---

**`match-rule v2`, sürümlü.**

- **K0–K2:** bulgu, vakayı isabet eder ancak `tool`, `rule_id` ve satır tam olarak aynıysa.
  ±15 satır penceresi yoktur; dokuz yüz ihlali döken bir adapter tesadüfen isabet alamaz.
- **K3 ve üstü:** `evidence_refs`'ten biri vakanın dokunulan dosyasında ve aynı sembolde ya da
  hunk'ın ±15 satırı içinde; `property` eşit; `required_change` dolu.
- Bir bulgu en fazla bir vakayı, bir vaka bir koşuda en fazla bir kez.

**Metrikler.**

| Metrik | Tanım |
|---|---|
| `recall`, `recall_lb` | İsabet / planted; tek yönlü %90 küme-bootstrap alt sınırı |
| `clean_findings` | Clean snapshot'taki bulgu sayısı; avcı precision'ı bunların tamamını sayar |
| `precision`, `precision_lb` | Oracle'ın karara bağladığı bulgular üzerinden; `unresolved` ayrı |
| `cost_usd`, `value_per_usd` | Şiddet ağırlıklı değer / USD (`tohum/20`) |
| `verdict` | `PASS` / `FAIL` / `UNMEASURABLE` (`tohum/19`) |

**İki görünüm.** Mühürlü görünüm vaka bazlıdır, yalnız mühürlü depoya yazılır, hiçbir ajan
okuyamaz. Ajan görünümü yalnız toplam sayılar ve kaçırma nedeni kategorileri toplamıdır. Dev
koşularında vaka bazlı sonuç açıktır.

**Maliyet defteri.** Her koşu `cost-ledger.jsonl`'a satır ekler; Aşama 0'daki okuyucusu
harness'in taban satırıdır (tabanı geçmeyen avcı FAIL), Aşama 3'ten itibaren maliyet inişi.
