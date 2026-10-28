# Yama Değil, Mimari Çözüm

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: taslak · Sahibi: operatör
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

**Yasak kalıplar.** Deterministik diff-guard (`04a` 9) iki listeyi uygular. Dil başına
**yasak yapılar** profildeki `banned_constructs`'tadır ve repo tanıma onları dilden türetir; örneğin
savunmacı isteğe bağlı erişim, boş yakalama blokları, tip kaçışları, bastırma yorumları, test
atlama. **Yasaklı ifadeler** `policy.json`'dadır; başlangıç listesi: "şimdilik", "geçici",
"geçici çözüm", "pragmatik", "daha basit yaklaşım", "orta yol", "yeterince iyi", "sonra düzeltilir",
"başka bir PR halleder", "kapsam dışı", "ertelendi" ve İngilizce karşılıkları ("for now",
"temporary", "workaround", "pragmatic", "good enough", "follow-up", "out of scope", "deferred",
"TODO later"). Bunlar kod incelemesine bile ulaşmaz.

**Kapsam kuralı.** Kök neden dokunduğu her çağrı yerini aynı değişiklikte günceller; bir kök
neden bir PR'dır ve `required_change` bu yüzden bir dizidir. Değişiklik büyüyorsa mikro görev
bölünür ama kök neden bölünmez: büyük kök neden kendi aşamalı planını alır ve her parçası
kendi başına yeşil ve geri alınabilir olur; kapsam daraltılmaz.

**Olgunluk bir sıfat değil, ölçümdür.** "Kıdemli" ajan, deftere göre kıdemlidir: düzeltmelerinin
hayatta kalma oranı, katman iddialarının panelde tutma oranı, geri alınma oranı ve kök neden
başına değer / USD. Bu sayılar itibardır (`11-itibar.md`); promptta "kıdemli gibi davran"
yazmak hiçbir sayıyı değiştirmez. Takımın olgunluğu, yamanın kapıdan geçemediği bir sistemde
zorunlu olarak büyür; başka yolu yoktur.
