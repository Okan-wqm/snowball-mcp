# Aşama 1 §1.5 — Döngü, adım adım

Tarih: 2026-10-28 · Sürüm: 2.0 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 1 çalışırken
Çapa: beklemede: aşama 1 çıkış raporu

---

1. **Discover.** Adapter, `brain/integration`'ın güncel snapshot'ında aracı koşar ve base SHA
   ile fark alır. Her yeni ihlal bir bulgudur: `property=lint`, `tool`, `rule_id`, satır,
   `required_change={file, symbol, op}`. Parmak izi `tohum/07`'deki gibidir.
2. **Execute.** Düzeltici bulgu başına worktree açar; önce dosyanın etki kümesini okur (import
   grafiği). Dosya profildeki güvenlik yollarındaysa bulgu `blocked`. Önce aracın `fix`
   aralığı; araç düzeltemezse Sonnet, yalnız o dosyada ve o aralıkta. Dersler varsa okur ve
   `run_meta.lessons_read`'e yazar.
3. **Approve (oracle).** Aynı worktree'de araç yeniden koşar: hedef (kural, satır) kaybolmuş, yeni
   ihlal doğmamış. Profildeki etkilenen-test komutu ve etki kümesindeki projelerin test
   hedefleri yeşil; önbellek kapalı; sıfır test kırmızı. Diff-guard temiz (`tohum/04a`). Tutmazsa
   worktree atılır, bulgu `unresolved`.
4. **Merge.** Kabul edilen düzeltme, beyin reposundan gelen merge kapısıyla `brain/integration`'a
   girer. Kapı oracle raporunu ve baseline'ı yeniden doğrular, ajan sözüne bakmaz. Döngü başına
   PR ve CI dakika tavanı `policy.json`'da.
5. **Learn.** Defter satırı: parmak izi, sınıf, düzeltme yolu, maliyet, süre, sonuç, okunan
   dersler. Geri alma olursa `cause` mekanik çıkarılır ve ilk ders doğar (`tohum/22`). Organ ve
   bulgu sayfaları yeniden üretilir; `status.md` yazılır; kök hash yazılır.
6. **Discover again.** Zamanlayıcı ya da push tetiği; beynin kendi push'u tetiklemez.

Her adımın okuyucusu vardır: adapter çıktısını düzeltici, düzelticiyi oracle, oracle raporunu
kapı, defteri Gözcü ve puanlayıcı, `status.md`'yi Gözcü okur.
