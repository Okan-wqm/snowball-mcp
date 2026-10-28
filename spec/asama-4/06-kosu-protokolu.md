# Aşama 4 §4.6 — Koşu protokolü

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: hedef taslak · Sahibi: operatör
Okunma: Aşama 4 çalışırken
Çapa: beklemede: aşama 4 çıkış raporu

---

**Dev döngüsü** (Kurucu yönetir): dev setinden planted snapshot'lar (snapshot başına ≤ 5 vaka),
en az bir clean ve bir kanarya, karışık sırada; her snapshot için avcı bir kez koşar; harness
puanlar; Kurucu dev sonucunu vaka bazlı görür, promptu düzeltir; her prompt sürümü hash'lenir
ve dev skorları ile maliyetiyle `prompt-ledger.jsonl`'a yazılır.

**Exit koşusu** (hakem exit işi tetikler): mühür doğrulanır; held-out planted snapshot'lar ve aynı
sayıda clean ile kanarya, karışık, etiketsiz; her snapshot bir kez koşar; avcı ders almaz ve harita
dondurulmuştur. Kurucuya yalnız verdict, n ve alt sınır verilir. Bakış bütçesi property ve organ
soyu başınadır ve rotasyonla sıfırlanmaz (`tohum/19`).

**Kalıp sızıntısı denetimi:** her exit öncesi prompt ve spec, snapshot'tan çıkarılan tanımlayıcı
listesiyle kesişmez ve regex, glob ya da "ara" ifadesi içermez; denetim harness'tedir ve avcının
her girdisine uygulanır, dar kapsam basamağının glob'u dahil.
