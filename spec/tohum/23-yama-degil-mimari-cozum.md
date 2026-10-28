# Yama Değil, Mimari Çözüm

Tarih: 2026-10-28 · Sürüm: 2.0 · Durum: taslak · Sahibi: operatör
Okunma: her düzeltme tasarlanırken ve panel faz 4'te
Çapa: düzeltme PR'ındaki katman iddiası; faz 4 kararları

---

Öncelik her zaman gerçek, kanıtlanmış mimari çözümdür. Yama, belirtiyi susturan koddur; sistem
yama üretirse hatayı değil, hatanın görünürlüğünü azaltır ve ablasyon bunu yakalayamaz.

**Test sorusu.** Her düzeltme tek soruya cevap verir: *üst akış doğru olsaydı bu kod var olmak
zorunda kalır mıydı?* Cevap hayırsa düzeltme yanlış yerdedir. Arayüz uyuşmazlığı arayüzde,
eksik alan şemada, iki uç tutarsızlığı sözleşmede ve iki uçta birden çözülür; çağrı yerinde
savunma yazılmaz.

**Dört katman.** Her düzeltme bir katman iddiası taşır; iddiayı implementer değil, panel doğrular.

| Katman | Anlamı | Örnek |
|---|---|---|
| 1 İmkânsız kılmak | Tip sistemi, derleyici ya da çalışma zamanı yanlışı yapısal olarak engeller | Dallı tip, kapalı enum, kurucuda doğrulama |
| 2 Otomatik kılmak | Doğru davranış sıfır çabayla varsayılan olur | Middleware, üretilmiş kod, varsayılan yapılandırma |
| 3 Tespit edilebilir kılmak | Yanlış davranış derleme ya da test zamanında yakalanır | Invariant testi, lint kuralı |
| 4 Belgelemek | Yalnız 1–3 gerçekten imkânsızsa | Runbook maddesi |

Katman 4 iddiası, 1–3'ün neden imkânsız olduğunun kanıtını ister; kanıtsız katman 4, faz 4'te
ölür. İddia edilen katmanın altında kalan düzeltme de faz 4'te ölür: "katman 1" denip yazılan
bir null kontrolü kabul edilmez.

**Yasak kalıplar.** Deterministik diff-guard (`04a-oracle-sertlestirme.md`) şunları reddeder:
savunmacı `?.` ve boş yakalama, tip kaçışları, bastırma yorumları, tek seferlik uyumluluk
katmanları, "ileride düzeltilecek" notları, yasaklı ifadeler. Bunlar kod incelemesine bile
ulaşmaz.

**Kapsam kuralı.** Kök neden dokunduğu her çağrı yerini aynı değişiklikte günceller; "başka bir
PR halleder" bir plan değil, yasaklı ifadedir. Değişiklik büyüyorsa mikro görev bölünür, kapsam
daraltılmaz.

**Olgunluk bir sıfat değil, ölçümdür.** "Kıdemli" ajan, deftere göre kıdemlidir: düzeltmelerinin
hayatta kalma oranı, katman iddialarının panelde tutma oranı, geri alınma oranı ve kök neden
başına değer / USD. Bu sayılar itibardır (`11-itibar.md`); promptta "kıdemli gibi davran"
yazmak hiçbir sayıyı değiştirmez. Takımın olgunluğu, yamanın kapıdan geçemediği bir sistemde
zorunlu olarak büyür; başka yolu yoktur.
