# Aşama 1 §1.6 — Sıralı mikro özellikler

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 1 çalışırken
Çapa: beklemede: aşama 1 çıkış raporu

---

Her satır tek oturumda biter, kendi gerçek testiyle gelir ve `brain/integration` üzerinde bir
canlı koşuyla kapanır.

1. Taban çıkarma ve lint adapter; dev snapshot'larında recall alt sınırı tabanı geçer.
2. `map.build`: katman (a) ve kapsama haritası.
3. Sözleşme: adapter ile düzeltici arasındaki bulgu biçimi `contracts/` altında donar.
4. Dispatcher: konteyner, kira, sağlayıcı geçidi, `run_meta`, model ayrıklığı, `subject_run_id`.
5. Kapsayıcılık ölçümü, `containment.jsonl`, sandbox kanaryası, `secrets.scan`.
6. Düzeltici: `fix` aralığı yolu, Sonnet yolu, güvenlik yolu bloğu, test yolu yasağı; `unresolved.jsonl`.
7. Diff-guard ve kapı: yeniden koşturma, mandal, durum kontrolü, ilk merge, tavanlar.
8. Nöbetçi, bisect, geri alma, `cause`; şablonlu ilk ders; düzeltici dersin ilk okuyucusu.
9. Organ kaydı: SHADOW → ACTIVE, `shadow_min_runs` kuralıyla; `genesis-queue.jsonl` açılır.
10. İtibar puanlayıcısı, `reputation.jsonl`, hayatta kalma penceresi (K0 için 72 saat).
11. Entegrasyon dalı `main` senkronu; çakışmada geri alma ve `blocked`.
12. `drift.check` her döngü başında; Gözcü ve `tohum/28` dondurma provası (yapay regresyonla).
13. `docs.render` ve `status.render`: organ ve bulgu sayfaları iki formatta; görünüm testi 17.
14. Çıkış koşusu.
