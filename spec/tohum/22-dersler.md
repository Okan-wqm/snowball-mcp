# Dersler: Öğrenme Planlayıcıya ve Implementer'a Akar

Tarih: 2026-10-28 · Sürüm: 1.0 · Durum: taslak · Sahibi: operatör
Okunma: plan yaparken, düzeltme yazarken, test yazarken
Çapa: `<state_root>/lessons.jsonl`; `run_meta.lessons_read`

---

Hafıza, okuyucusu olmadan arşivdir. Derslerin okuyucuları iş yapan ajanlardır: Aşama 1'den
itibaren düzeltici yaklaşım ve nereye dokunmama için; Aşama 2'den itibaren planlayıcı sıralama,
kapsam ve etki tahmini için. **Test-yazıcı ve oracle ders okumaz**; oracle'ın bağımsızlığı derslere
bağlı olamaz. Exit koşularında avcı ders almaz.

## Ders nedir

| Alan | Anlamı |
|---|---|
| `claim` | Tek cümle: "Alan adı değişince sözleşmeyi kullanan tüketiciler de incelenir" |
| `evidence_refs` | Dersi doğuran olayın kanıtı |
| `validity` | Hangi koşulda geçerli: sınıf, property, dosya kalıbı, repo |
| `origin_event` | Zincirdeki olay satırı |
| `hit`, `miss` | Kullanıldığı işin hayatta kalma ve geri alınma sayıları |
| `superseded_at` | Bugünün testi çürüttüyse, kanıtıyla |
| `derived_from` | Yeniden doğan dersin eski sürümü |

Ders ipucu olarak verilir, kanıt olarak değil (Y1). Hiçbir ders bir oracle'ı geçersiz kılamaz.

## Yanlış ders silinmez

Bugün yanlış olan yarın doğru olabilir; o kısım ajanlara ve testlere kalmıştır. Sistem her gün o
gün için doğru olanı yapar ve bunu şöyle sağlar:

- Dersle çelişen bugünün testi kazanır; ders `superseded_at` alır, kanıt yazılır, zincirde kalır.
- Dersi kullanan iş geri alınırsa `miss` artar ve ağrılığı düşer; silinmez.
- Yarın yeniden doğrulanırsa aynı ders yeni sürüm olarak, `derived_from` ile geri gelir.
- Dersler güncel hit oranına göre sıralanır; okuyucu ilk N'i görür.

## Kullanım izi

Hangi derslerin hangi koşuya verildiğini ajan değil **dispatcher** yazar (`lessons_injected`).
Sonuç (hayatta kaldı ya da geri alındı) o derslerin `hit` ve `miss` sayaçlarına itibar
puanlayıcısı tarafından mekanik olarak işlenir. Kredinin nedenselliği için dispatcher bazı uygun
koşularda dersi rastgele saklar; ders yalnız verilen ve saklanan koşular arasındaki farkla kredi
alır. İki pencere boyunca okunmayan ders arşive iner; okunup hep `miss` alan ders `superseded` olur.

## Doğuş ve ilk okuyucu

İlk dersler Aşama 1'de doğar: geri alınan ilk düzeltmenin `cause`'u ilk derstir. Hayatta kalan
başarılar da ders doğurur: aynı tür düzeltmenin işe yarayan yolu. Aşama 1'de ders metni LLM
yazmaz; yapısal alanlardan sabit şablonla üretilir. Serbest metinli dersler Aşama 2'nin
planlayıcısıyla gelir ve her biri kanıt referansı taşır. İlk okuyucu Aşama 1'in düzelticisidir.
Aynı `cause` üç kez tekrarlanınca genesis derslerden bir skill ya da dedektör taslaklar (`17`).
