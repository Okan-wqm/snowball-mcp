# Aşama 1 §1.3 — Girişler

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 1 çalışırken
Çapa: beklemede: aşama 1 çıkış raporu

---

- Aşama 0 PASS raporu, K0 dev ve held-out setleri, taban avcının recall ve maliyeti.
- Kurulumun ikinci bölümü tamamlanmış (`tohum/25a`).
- Profildeki lint araç zinciri. Aşama 1 K0'ı yalnız kural kimliği ve satır veren lint aracıdır;
  biçimleyiciler ve derleme grafiği dışındaki dillerin lint'i Aşama 2'de açılır. Yeni kural
  yazılmaz; var olan sarılır. Anlamsal lint kuralları K5'e bağlıdır ve bu aşamada düzeltilmez.
- **Taban:** beyin bağlanınca her aracın mevcut ihlallerinden taban çıkarır (`tohum/07`); keşif bu
  borcu da kapsar. Güvenlik yollarındaki borç `blocked`'dır.
- Harita katmanı (a) bu aşamada `map.build` ile kurulur.
