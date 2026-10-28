# Aşama 1 §1.3 — Girişler

Tarih: 2026-10-28 · Sürüm: 2.0 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 1 çalışırken
Çapa: beklemede: aşama 1 çıkış raporu

---

- Aşama 0 PASS raporu, K0 dev ve held-out setleri, taban avcının recall ve maliyeti.
- Profildeki lint araç zinciri. Aşama 1 K0'ı yalnız kural kimliği ve satır veren lint aracıdır;
  biçimleyiciler (dosya başına, satırsız) ve derleme grafiği dışındaki dillerin lint'i ayrı K0 alt
  sınıflarıdır ve Aşama 2'de açılır. Yeni kural yazılmaz; var olan sarılır.
- `brain/integration` dalı ve ruleset'i, kurulum gününden.
- Harita katmanı (a): profildeki graf aracından import grafiği.
