# Aşama 0 §0.4 — Hata seti

Tarih: 2026-10-28 · Sürüm: 2.0 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: beklemede: aşama 0 çıkış raporu

---

**Kaynak, iki yol.** (1) Reponun geçmişinde lint kuralı ihlali düzelten commit'ler; commit türü
filtresi yoktur, çünkü lint düzeltmeleri çoğu repoda `chore`, `refactor` ya da `test` olarak
gelir. (2) **Mutasyon:** aracın kural kataloğundan bilinen ihlaller temiz dosyalara deterministik
operatörlerle enjekte edilir. K0'da ana kaynak mutasyondur; gerçek düzeltmeler azdır ve geçmişe
göre uygulanamaz olur.

**Vaka, ebeveyne sabitlenir.** Gerçek düzeltme F için `base_sha` = F'nin ebeveyni; snapshot
`archive(base_sha)`'dır, HEAD'e ters yama uygulanmaz. Böylece eski düzeltmeler de vaka olur.

**Geçerlilik.** K0 vakası geçerlidir ancak ve ancak araç, snapshot'ta tam olarak o (kural, satır)
için kırmızı verir ve clean snapshot'ta aynı (kural, satır) yoktur. "Araç kırmızı" tek başına
anlamsızdır, çünkü birçok proje zaten kırmızıdır; ölçü farktır.

**Provenance.** Her vaka `provenance` taşır: `human_fix`, `mutation`, `system_tp`,
`system_regression`. Exit kapısında ve held-out'ta yalnız `human_fix` ve `mutation` sayılır;
sistemin kendi ürettiği vakalar aynı organ soyunun held-out'una giremez.

**Yerleşim.** Dev vakalar `<state_root>/cases/`; held-out vakalar ve mühür mühürlü depoda.
Vaka kaydı şeması `tohum/26`.

**Bölme.** `cases.build`, vakaları CI sırrından türetilen tohumla **dev** ve **held-out** olarak
ayırır; bölme mutasyon operatörü ya da modül grubu bazındadır, yakın kopyalar aynı tarafta kalır.
Held-out: K0 için en az 60 mutasyon, K5 ve üstü için en az 25 vaka (`tohum/19`). Mühür HMAC
tuzludur; yalnız CI `rotate` işi yazar. Mühre en fazla üç bakış, sonra rotasyon.

**Sınıf etiketi.** `class_level` deterministik bir haritayla verilir: kural kimliği ve araç →
K0–K2; property → K3–K8 (§0.5). Harita `cases.build` içinde sürümlüdür.
