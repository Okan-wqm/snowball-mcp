# Hafıza Modeli: Sekiz Hafıza, Tek Defter

Tarih: 2026-10-28 · Sürüm: 1.0 · Durum: taslak · Sahibi: operatör
Okunma: yeni hafıza türü önerirken ve her defter şeması değişikliğinde
Çapa: `chain/root.jsonl`; her defter satırındaki `derivation` ve `trust` alanları

---

Sekiz hafıza vardır ama sekiz veritabanı yoktur. Tek gerçek kaynak, zincirli olay defteridir;
`ledger.jsonl`, `cost-ledger.jsonl`, `containment.jsonl` gibi dosyalar aynı defterin türe göre
bölümleridir ve tek kök hash'e bağlanır. İtibar, ders sayaçları, kapsama ve organ durumu
**görünümdür**: defterden yeniden kurulur ve harness'in bir kendi-testi onları sıfırdan kurup
mevcut hâlleriyle karşılaştırır. Ayrı tutulan bir gerçek zamanla diğerleriyle çelişir.

| # | Hafıza | Cevapladığı soru | Tohumda | Büyüme yolu |
|---|---|---|---|---|
| 1 | Episodik | Ne oldu, ne zaman, hangi koşulda, sonuç ve neden | Evet: olay defteri | "Neden" alanı mekanik çıkarımla dolar |
| 2 | Semantik | Ne nedir, neye bağlı | Yalnız import grafiği | Kaçırma nedenleri harita katmanı doğurur |
| 3 | Prosedürel | Nasıl yapılır | Hayır | Aynı tür düzeltme üç kez hayatta kalınca skill taslağı |
| 4 | Zamansal | Ne zaman ne doğruydu | Evet: zincir, git, `as-of` | Ölçek gerektirince sembol düzeyi kimlik |
| 5 | Çalışma | Şu an ne yapılıyor | Evet: döngü durumu, kiralar | Döngü bitince kapanır; kalıcı olan episodik deftere geçer |
| 6 | Amaç ve değerler | Neden yapılıyor | Evet: çekirdek, yasalar, property'ler | Büyümez; yalnız operatör yazar |
| 7 | Kaynak ve güven | Bunu nereden biliyorum | Evet: her satırda iki alan | Yeni türetme yolları eklenir |
| 8 | Öz değerlendirme | Nasıl performans gösteriyorum | Ölçüm evet; dersler hayır | Kaçırma nedeni kategorileri ve dersler (`22-dersler.md`) |

## Tohumda zorunlu şema alanları

Her defter satırı, hangi hafızaya ait olursa olsun, şu alanları taşır:

- `derivation`: `tool` | `static_analysis` | `test_verified` | `llm_inference` | `name_similarity`.
- `trust`: `verified` | `observed` | `inferred`. Merge kararına giren kanıt yalnız `tool`,
  `static_analysis` ya da `test_verified` kaynaklı olabilir. `llm_inference` ve
  `name_similarity` yalnız "buraya bak" ipucudur; etki kümesine girebilir, güvenlik kararını
  taşıyamaz.
- `snapshot_id` ve `evidence_refs`.
- `cause`: başarısız ya da geri alınan olaylarda zorunlu. Bisect, test çıktısı ve diff'ten
  mekanik çıkarılır. Çıkarılamıyorsa değeri `unknown` olur; LLM tahmini buraya yazılmaz.

Bu alanlar ilk günden vardır, çünkü sonradan eklemek bütün geçmişi yeniden yazmak demektir.

## Çalışma hafızası

Döngü başında açılır, sonunda kapanır. İçeriği: açık mikro görevler, her görevin kirası
(hangi ajan, ne zamana kadar), beklenen sonuçlar, `blocked` listesi. Kirası dolan görev
serbest kalır ve deftere düşer. Kapanmayan çalışma hafızası bayat gerçeğe dönüşür; bir
sonraki döngü önce onu temizler.

## Dersler okuyucusuyla gelir

Öğrenme, planlayıcıya ve implementer'a akmadıkça öğrenme değildir. Derslerin yapısı, yanlış
dersin ne olacağı ve kullanım izi `22-dersler.md`'dedir.

## Kişisel hafıza yoktur

Ajanlar koşu başına durumsuzdur. Kişisel hafıza bağımsızlığı ve tekrar üretilebilirliği bozar;
rakibin aynı geçmişi taşıması korelasyonlu yanılma üretir. Bir ajanın geçmişi itibar defterinde
ve soyağacında durur; ortak proje hafızası herkesindir.

## Hafıza üçlüsü

Her hafıza türü, yazarı, okuyucusu ve okuyucunun değiştirdiği kararla birlikte aynı PR'da gelir
(`13-memory-ve-zincir.md`). Yeni hafıza türünün tetiği `17-kas-buyutme-sinyalleri.md`'deki
sinyallerdir; gerekliliği ablasyonla kanıtlanır (`12-genesis.md`).
