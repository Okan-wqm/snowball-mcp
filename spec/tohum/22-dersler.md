# Dersler: Öğrenme Planlayıcıya ve Implementer'a Akar

Tarih: 2026-10-28 · Sürüm: 1.0 · Durum: taslak · Sahibi: operatör
Okunma: plan yaparken, düzeltme yazarken, test yazarken
Çapa: `<state_root>/lessons.jsonl`; `run_meta.lessons_read`

---

Hafıza, okuyucusu olmadan arşivdir. Derslerin okuyucuları iş yapan ajanlardır: planlayıcı
sıralama, kapsam ve etki tahmini için; implementer yaklaşım ve nereye dokunmama için;
test-yazıcı neyi test edeceği için.

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

Her plan, düzeltme ve test, hangi dersleri okuduğunu `run_meta.lessons_read`'e yazar. İşin
sonucu (hayatta kaldı ya da geri alındı) o derslerin `hit` ve `miss` sayaçlarına mekanik olarak
işlenir; bunu bir LLM değil, puanlayıcı yapar. İki pencere boyunca okunmayan ders arşive iner;
okunup hep `miss` alan ders `superseded` olur.

## Doğuş ve ilk okuyucu

İlk dersler Aşama 1'de olay defterinin `cause` alanından doğar: geri alınan ilk düzeltmenin nedeni
ilk derstir. İlk okuyucu Aşama 2'nin planlayıcısıdır; o güne kadar dersler yalnız yazılır ve
raporlanır. Dersler de bir organdır: çok sayıda ders bir kalıp oluşturursa genesis onlardan bir
skill ya da dedektör taslaklar (`17-kas-buyutme-sinyalleri.md`).
