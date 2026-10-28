# Aşama 1 §1.7 — Harness ölçümü

Tarih: 2026-10-28 · Sürüm: 2.0 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 1 çalışırken
Çapa: beklemede: aşama 1 çıkış raporu

---

Harness, adapter'ı Aşama 0'daki K0 planted, clean ve kanarya snapshot'larında puanlar. Beklenen:
recall alt sınırı 0,95'in üstünde (60 mutasyonda sıfır kaçırma), clean'de yalnız gerçek
ihlaller. Düşük recall adapter'ın aracı yanlış sardığı anlamına gelir; aracın kendisi doğrudur.

Düzeltici ayrıca ölçülür: dev vakalarında kabul oranı, `fix` aralığı / Sonnet oranı, değer / USD,
diff-guard red oranı. Oracle duvar saati ve CI dakikası `cost-ledger.jsonl`'a yazılır.
