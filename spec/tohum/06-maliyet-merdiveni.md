# Maliyet Merdiveni ve Bütçe

Tarih: 2026-10-28 · Sürüm: 2.0 · Durum: taslak · Sahibi: operatör
Okunma: bir yetenek harness'te geçtikten sonra ve her bütçe kararında
Çapa: cost-ledger.jsonl; policy.json bütçe payları

---

Bir yetenek harness'te eşiği tutunca aynı yeteneğin daha ucuz basamakları sırayla denenir.
Sıra, kazancın büyüklüğüne göredir:

1. **Önbellek, varsayılan.** Prompt önbelleği her koşuda açıktır; girdi maliyetinin büyük
   kısmını siler ve bir basamak değil, zemin şartıdır.
2. **Küçük model.** Aynı prompt, Opus yerine Sonnet. Üretici-yargıç-oracle ayrıklığı korunur
   (`09a-bagimsizlik.md`); ayrıklığı bozan iniş yapılmaz.
3. **Kısa prompt.**
4. **Mekanik dedektör.** Bulunan sınıf için LLM'siz dedektör; tek büyük tasarruf budur
   (Aşama 3'ten itibaren).
5. **Dar kapsam, kapsama tabanıyla.** Yalnız dev koşularının okuduğu dosyalardan türetilen glob;
   kapsama haritasında görülmeyen dosya payı artıyorsa bu basamak reddedilir, çünkü kör noktayı
   pekiştirir.

Her basamak önce dev setinde, aynı vakalarda eşli olarak denenir ve `19-olcum-istatistigi.md`'deki
non-inferiority kuralıyla doğrulanır. Eşiği tutan en ucuz basamak üretim basamağı olur. Pahalı
basamak silinmez; bilinmeyen sınıfları aramak için keşif basamağı olarak kalır. Başarısız
basamak deftere yazılır ve vaka havuzu yarı yarıya büyüyünce bir kez daha denenir. Panelin faz 1
ve 2'si en ucuz modelde koşabilir.

**Ölçü.** USD / isabet değil, şiddet ağırlıklı değer / USD (`20-metrikler.md`); yoksa sistem
ucuz ve önemsiz işi öğrenir.

**Bütçe.** Aylık tavanı operatör koyar (`policy.json`, anayasal). Paylar başlangıçta: keşif
≤ %30, üretim ≤ %40, ölçüm ≤ %20, genel ≤ %10. Ölçüm payı ablasyon, held-out koşuları ve panel
kalibrasyonunu içerir. Aşama bütçeleri yargılama ve oracle maliyetini de kapsar; "koşu başına"
tavanlar bunların toplamını aşamaz. İnşa-zamanı LLM bütçesi (Kurucu ve rakip) ile çalışma-zamanı
LLM bütçesi (sistemin kendisi) ayrı kalemlerdir; Aşama 0'ın çalışma-zamanı LLM maliyeti sıfırdır.
