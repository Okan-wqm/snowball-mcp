# Aşama 1 §1.2 — Doğruluk özellikleri

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 1 çalışırken
Çapa: beklemede: aşama 1 çıkış raporu

---

1. **Mandal:** hiçbir merge bir aracın toplam ihlal sayısını artırmaz; hedef ihlal kaybolur.
2. **Davranış korunur:** düzeltme yalnız hedef mesajın `fix` aralığına dokunur; kapı etkilenen
   testleri yeniden koşturur; sıfır test kırmızıdır.
3. **Güvenlik yollarına dokunulmaz:** K6 canlı olana kadar, biçimleyici ve `--fix` dahil.
4. **Her dosyanın okuyucusu vardır:** `tohum/27` tablosu.
5. **Kapı yeniden koşturur:** oracle raporunu okumakla yetinmez (`tohum/01b`).
6. **Kapsayıcılık:** ölçülmüş bildirilmeyen ihlal yoktur.
7. **Zincir ve görünümler:** her döngü kök hash yazar; itibar, ders sayaçları ve kapsama defterden
   yeniden kurulabilir.
