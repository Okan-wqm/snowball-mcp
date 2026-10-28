# Aşama 0 §0.11 — Yasaklar

Tarih: 2026-10-28 · Sürüm: 2.0 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: beklemede: aşama 0 çıkış raporu

---

- Çalışma zamanında hiçbir LLM çağrısı: harness'te, set üretiminde, snapshot üretiminde, taban
  avcıda.
- LLM avcı, yargıç, dedektör, hafıza (hata seti, maliyet defteri ve zincir dışında).
- Uygulama koduna değişiklik yok. Hedef repoya giren tek şey `brain/state` dalındaki
  `<state_root>` ve beyni çağıran `hunt-harness.yml`; harness kodu beyin paketine girer.
- Aşama 0 kapandıktan sonra harness yalnız `tohum/02`'deki şeritten değişir.
- Held-out vakaların hedef repoda ya da beynin okuyabildiği bir yerde durması.
