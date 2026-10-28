# Aşama 4 §4.7 — Panel, oracle ve kalıcı düzeltme

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: hedef taslak · Sahibi: operatör
Okunma: Aşama 4 çalışırken
Çapa: beklemede: aşama 4 çıkış raporu

---

Clean snapshot'taki her bulgu önce panelin 1–4. fazlarından geçer (`tohum/10a`). Faz 1 mekanik ve
bedava; çoğu yanlış bulgu burada ya da faz 2'de ölür. Bir yargıç üreme testi talep ederse
test-yazıcı yazar ve bulgu faz 5'e atlar.

**Faz 5, kanıt için.** `tohum/04a` şartlarıyla: test property'den yazılır ve önce mühürlenir;
kırmızı başarısız assertion'dır; 3/3 kırmızı, 3/3 yeşil; hunk kapsaması; mutant öldürme. Oracle
düzelticisinin asgari düzeltmesi yalnız kanıttır ve merge edilmez.

**Güncel kod.** Clean snapshot güncel `brain/integration` başıdır. Bulgu daha eski bir ağaçta
bulunduysa test önce güncel başta kırmızı olmalıdır; değilse bulgu `withdrawn`.

**Kalıcı düzeltme.** TP için implementer kök neden kuralıyla kalıcı düzeltmeyi yazar
(`required_change` dizisi, tüm çağrı yerleri). Aynı mühürlü test, ikinci panel (faz 2–4, diff
üzerinde) ve hakem kapısı ondan geçer; kapı etkilenen testleri yeniden koşturur ve merge eder.

**Sonuçlar.** TP → vaka adayı (`provenance: system_tp`; aynı soyun held-out'una ve exit'e girmez).
FP → `fp-corpus.jsonl`; okuyucusu rakip kanaryası ve yargıç kalibrasyonu. Unresolved →
`unresolved.jsonl`; oranı yüksekse oracle takımı yetersizdir. Panel ve oracle maliyeti deftere yazılır.
