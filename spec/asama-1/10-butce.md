# Aşama 1 §1.10 — Bütçe (kaçak freni; değerleri yalnız operatör değiştirir)

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 1 çalışırken
Çapa: beklemede: aşama 1 çıkış raporu

---

Bütçe Aşama 0'daki gibi bir kısıt değil, kaçak frenidir (`asama-0/12`): olağan işi durdurmayacak kadar
yüksek kurulur, döngüyü keser. Değerler `stage_budgets.asama_1` ve anayasal anahtarlardır; tablo
başlangıç fren değerlerini verir. USD liste fiyatı tahminidir (`tohum/06`).

| Kalem | Başlangıç fren değeri |
|---|---|
| Adapter koşusu | 0 USD; `operating{}` sınırları (`kos_wall_s`) |
| Sonnet düzeltmesi | Bulgu başına 0,50 USD ve 5 dk; sınırı `llm.call`'ın çağrı başı tavanı uygular (iç kullanımda `claude` CLI'sinin `--max-budget-usd`'si). Anahtarları çağrı başınadır: `constitutional.stage_params.fix_call_max_usd` (`"0.500000"`) ve `constitutional.stage_params.fix_call_max_s` (`300`); sahip kararı (2026-11-23), `tohum/18a`, `tohum/26s` |
| Çalışma-zamanı LLM, aşama toplamı | `stage_budgets.asama_1.runtime_llm_usd`: 10.000 USD (`tohum/18a`) |
| İnşa-zamanı LLM: Kurucu | `stage_budgets.asama_1.founder_usd`: aşama toplamı 10.000 USD; oturum başına `session_cap_usd` |
| İnşa-zamanı LLM: tohum rakibi | `stage_budgets.asama_1.rival_usd`: 10.000 USD; yalnız kaçak freni (`tohum/18a`) |
| Güvenlik avcısı | Aşama 1'de yok (`tohum/30f`); `security_hunter_usd` yazılmaz |
| Actions dakikası | Döngü başına `cycle_caps`; döngü sıklığı aylık anayasal tavandan türetilir (`policy.json`) |
| Operatör emeği | Parti ve çıkış aktarımları, `stage-open`; her biri sayılır |

**Ölçüm, kapı değil.** Kurucu oturum sayısı, USD toplamları ve takvim (tahmin: yaklaşık 12 oturum, artı
partiler ve hayatta kalma penceresi) ölçüdür; çıkış koşulu değildir, Kurucu'yu durdurmaz. Frene takılmak
operatör uyarısıdır, ret değil; olağan işse operatör değeri yükseltir.

**Gerçek sınır abonelik penceresidir.** 5 saatlik ya da haftalık kotaya takılmak (HTTP 429) operatör
uyarısı ve kesintidir; Kurucu reddi ya da kapı nedeni değildir.
