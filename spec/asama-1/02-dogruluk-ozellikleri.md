# Aşama 1 §1.2 — Doğruluk özellikleri

Tarih: 2026-10-28 · Sürüm: 2.0 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 1 çalışırken
Çapa: beklemede: aşama 1 çıkış raporu

---

1. **Fark:** entegrasyon dalında base SHA'ya göre yeni (kural, satır) ihlali doğmaz ve mevcut
   ihlal sayısı artmaz. Zaten kırmızı projelerde "araç yeşil" ulaşılamaz bir hedeftir; fark
   ulaşılabilirdir.
2. **Davranış korunur:** düzeltme yalnız hedef mesajın `fix` aralığına dokunur; etkilenen-test
   komutu ve etki kümesi testleri yeşil kalır; sıfır test koşması kırmızıdır.
3. **Güvenlik yollarına dokunulmaz:** K0'da güvenlik yollarındaki ihlaller `blocked` kalır,
   `--fix` dahil.
4. **Her organın okuyucusu vardır:** `profile.json.readers` her yazılan dosyaya bir okuyucu bağlar.
5. **Kapı rapora bakar:** merge kapısı oracle raporunu ve baseline'ı yeniden doğrular.
6. **Kapsayıcılık:** ölçülmüş bildirilmeyen ihlal yoktur.
7. **Zincir ve üretilmiş dokümanlar:** her döngü kök hash yazar; organ ve bulgu sayfaları üretilir.
