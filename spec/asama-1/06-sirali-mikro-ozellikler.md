# Aşama 1 §1.6 — Sıralı mikro özellikler

Tarih: 2026-10-28 · Sürüm: 2.0 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 1 çalışırken
Çapa: beklemede: aşama 1 çıkış raporu

---

Her satır tek oturumda biter, kendi gerçek testiyle gelir ve `brain/integration` üzerinde bir
canlı koşuyla kapanır.

1. Lint adapter ve fark oracle'ı; dev snapshot'larında recall alt sınırı tabanı geçer.
2. Dispatcher: kısa ömürlü konteyner, kira, `run_meta`, model ayrıklık kontrolü.
3. Kapsayıcılık ölçümü: koşu öncesi ve sonrası özet CI tarafından, egress günlüğü,
   `containment.jsonl`; ilk kanarya koşusu.
4. Düzeltici: `fix` aralığı yolu; sonra Sonnet yolu; güvenlik yolu bloğu; test yolu yazma yasağı.
5. Diff-guard, kapıda.
6. Merge kapısı çağrısı ve ilk merge; döngü başına tavanlar.
7. Organ kaydı: adapter ve düzeltici DRAFT → SHADOW → ACTIVE, dev sayılarıyla (N = 3).
8. Puanlayıcı ve `reputation.jsonl`; hayatta kalma penceresi K0 için 72 saat.
9. Entegrasyon dalı `main` senkronu; çakışmada geri alma ve `blocked`.
10. Bisect geri alma; `cause` çıkarımı; ilk ders satırı.
11. `docs.render`: organ ve bulgu sayfaları, iki format; `status.md` Aşama 1 içeriği.
12. Gözcü eşikleri ve ilk yumuşak dondurma provası (yapay regresyonla).
13. Çıkış koşusu.
