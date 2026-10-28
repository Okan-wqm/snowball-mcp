# Aşama 0 §0.4 — Hata seti

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: beklemede: aşama 0 çıkış raporu

---

**Kaynak, iki yol.** (1) Geçmişte lint kuralı ihlali düzelten commit'ler; commit türü filtresi
yoktur. (2) **Mutasyon:** aracın kural kataloğundan bilinen ihlaller temiz dosyalara
deterministik operatörlerle enjekte edilir. K0'da ana kaynak mutasyondur.

**Vaka ebeveyne sabitlenir.** Gerçek düzeltme F için `base_sha` F'nin ebeveynidir; snapshot o
ağaçtan çıkarılır, HEAD'e ters yama uygulanmaz.

**Geçerlilik.** Araç mutasyonlu ve mutasyonsuz ağaçta koşar; satırlar mutasyon hunk'ı üzerinden
eşlenir, böylece kayan satırlar yeni ihlal sayılmaz. Vaka, mutasyon bölgesinde **tam olarak bir**
yeni (kural, satır) ihlali doğuyorsa geçerlidir; birden fazla ihlal doğuran mutasyon reddedilir.
Zaten kırmızı projelerde ölçü "araç kırmızı" değil, bu farktır.

**Sınıf etiketi.** `class_level` deterministik haritayla verilir. Profildeki `rule_property_map`,
anlamsal lint kurallarını (örneğin beklenmeyen promise kuralları) K0'a değil, ilgili K5
property'sine bağlar; böylece K5 havuzu aç kalmaz.

**Provenance.** `human_fix`, `mutation`, `system_tp`, `system_regression`. Exit kapısında
`human_fix` ve `mutation` sayılır (`tohum/19`); sistemin ürettiği vakalar aynı organ soyunun
held-out'una ve hiçbir exit kapısına girmez.

**Üç iş.** Vaka üretimi sırlı hakem işinde koşar (**hazırla**); avcı ve adapter sırsız işte koşar
(**koş**); puanlama sırlı hakem işinde koşar (**puanla**) (`tohum/08` 1). Kurucu `cases.build`'i
yalnız dev için çağırabilir.

**Held-out kaynağı.** Mutasyonlar gizli tohumla çok büyük bir aday havuzundan seçilir; insan
düzeltmeleri mühürlü kesim tarihinden sonra merge edilenlerden gelir; ayrıca yayımlanmayan bir
yedek havuz tutulur. Bölme modül ya da mutasyon operatörü grubuna göredir. Held-out: K0 için en az
60 mutasyon. Mühür HMAC'lidir; yalnız hakem rotate işi yazar; bakış bütçesi `tohum/19`.

**Yerleşim.** Dev vakalar `<state_root>/cases/`; held-out, yedek havuz ve mühür mühürlü depoda.
