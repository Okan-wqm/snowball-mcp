# Aşama 4 §4.7 — Panel ve yürütme oracle'ı

Tarih: 2026-10-28 · Sürüm: 2.0 · Durum: hedef taslak · Sahibi: operatör
Okunma: Aşama 4 çalışırken
Çapa: beklemede: aşama 4 çıkış raporu

---

Clean snapshot'taki her bulgu önce panelin 1–4. fazlarından geçer (`tohum/10a`). Faz 1 mekanik ve
bedava; çoğu yanlış bulgu burada ya da faz 2'de ölür. Dört fazı geçen bulgu faz 5'e gelir; bir
yargıç daha erken bir fazda üreme testini yazarsa bulgu doğrudan faz 5'e atlar.

Faz 5, `tohum/04a`'daki şartlarla: test önce mühürlenir; kırmızı = derlenen kodda başarısız
assertion; 3/3 kırmızı, 3/3 yeşil, önbellek kapalı, taze konteyner; mutant öldürme; etki kümesi
testleri yeşil; düzeltici yalnız `required_change` dosyalarına yazar; diff-guard temiz.

Sonuçlar: **TP** → düzeltme `brain/integration`'a gider ve yeni vaka adayı olur
(`provenance: system_tp`; aynı avcı soyunun held-out'una giremez). **FP** → `fp-corpus.jsonl`.
**Unresolved** → `unresolved.jsonl`; oranı yüksekse oracle takımı yetersizdir, avcı değil.
Panel ve oracle maliyeti bulgu başına deftere yazılır ve değer / USD'ye girer.
