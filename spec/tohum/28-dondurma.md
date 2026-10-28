# Dondurma: Ne Durur, Nasıl Kalkar

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: taslak · Sahibi: operatör
Okunma: Gözcü kararlarında ve her dondurmada
Çapa: beklemede: aşama 1 — ledger.jsonl part=freeze satırları

---

Dondurma bir ağrı refleksidir: zarar büyümeden eylemi durdurur, gözlemi durdurmaz. Kuralları
deterministiktir; Gözcü uygular, eşikleri `policy.json`'dadır.

**Yumuşak dondurma.**

- **Tetik:** regresyon kuralı (`20`), aynı pencerede iki kapsayıcılık ihlali (`08`), zincir kırığı
  (`13`), kümülatif eşik kayması (`18`), salınım birikimi.
- **Kapsam:** merge kapısı ilgili sınıf için kapanır; genesis yeni ACTIVE geçişi yapmaz. Keşif,
  ölçüm, SHADOW koşuları ve oracle sürer.
- **Kayıt:** `ledger.jsonl`'a `part: freeze` satırı: tetik, kapsam, ölçüm, başlangıç.
- **Kalkış:** dondurulmuş sistem boşta olduğu için "üç döngü sınır içinde" kanıt değildir. Kalkış
  için **sonda döngüsü** gerekir: dondurulmuş kapsamda SHADOW'da en az `policy.json`'daki sayıda
  düzeltme koşar, oracle'dan geçer ve tetik ölçüsü sınırın içindedir. Sonda döngüsü üst üste iki
  kez temizse dondurma kalkar ve kalkış da bir satırdır.

**Sert durma.**

- **Tetik:** bir pencerede `policy.json`'daki sayıdan fazla yumuşak dondurma; kurulum kayması
  (`01b`); attestation yazılamaması; kill switch.
- **Kapsam:** beyin hiçbir oyuncu koşusu yapmaz; yalnız hakem okuma işleri ve raporlama sürer.
- **Kalkış:** operatörün işidir; bu, döngü içinde insanın girdiği tek yerdir ve bilerek öyledir.
  `status.md` sert durmanın nedenini ve gereken eylemi en üstte yazar.
