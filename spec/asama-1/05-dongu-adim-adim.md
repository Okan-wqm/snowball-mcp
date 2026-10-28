# Aşama 1 §1.5 — Döngü, adım adım

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 1 çalışırken
Çapa: beklemede: aşama 1 çıkış raporu

---

1. **Discover.** Adapter, `brain/integration` başının snapshot'ında aracı koşar ve tüm ihlalleri
   bulgu sayar, taban borcu dahil. Parmak izi `tohum/07`'deki gibidir; aynı parmak izi yeniden
   gözlemdir.
2. **Execute.** Düzeltici bulgu başına worktree açar; önce etki kümesini haritadan okur. Dosya
   güvenlik yolundaysa bulgu `blocked`. Önce aracın `fix` aralığı; araç düzeltemezse Sonnet,
   yalnız o dosyada ve o aralıkta. Dispatcher hangi dersleri verdiğini kaydeder.
3. **Approve.** Oracle aynı worktree'de aracı yeniden koşar: hedef ihlal kaybolmuş, mandal
   tutmuş. Diff-guard temiz. Tutmazsa worktree atılır, bulgu `unresolved.jsonl`'a düşer.
4. **Merge.** Kabul edilen düzeltme PR olur. Hakem kapısı aracı, diff-guard'ı ve etkilenen
   testleri kendi işinde yeniden koşturur; geçerse `brain/integration`'a merge eder. Tavanlar
   `policy.json`'da.
5. **Watch.** Nöbetçi merge'den sonra etkilenen testleri koşar; kırmızıysa `tohum/07`'deki bisect
   ve geri alma yürür, `cause` yazılır ve şablondan bir ders doğar.
6. **Learn.** Hakem işleri defter satırlarını yazar; organ ve bulgu sayfaları ile `status.md`
   yeniden üretilir; kök hash ve attestation yazılır.
7. **Discover again.** Zamanlayıcı ya da `main` push'u; beynin ve hakemin kendi push'ları tetiklemez.
