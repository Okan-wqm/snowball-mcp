# Prova Vektörleri: Ders Provasının Referans Yargıcı

Tarih: 2026-10-30 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: ders provasının yargıcını (`harness.drill`) yazarken (Aşama 2 partisi) ve ders provası tasarlanırken
Çapa: `seed/drill/` (referans yargıç, simüle beyinler, testler); `seed/bootstrap/vectors/drill/`

---

Ders provasının (`22a`) kararını Kurucu'nun yazdığı hakem verir, ama Kurucu kendi yargıcı olamaz
(Y6). Bu yüzden prova yargıcının ne demesi gerektiği tohumla gelir: `seed/drill/` altında standart
kütüphaneyle yazılmış bir referans yargıç, onu sınayan simüle beyinler ve onlardan üretilmiş
vektörler. Kurucu'nun `harness.drill`'i vektörlerde referans yargıçla aynı kararı verir; önyükleme
hakemi bunu, yargıcı getiren Aşama 2 partisinin MF'si bitince her push'ta denetler (`asama-1/13`, `29b`);
Aşama 0'da `drill` grubu sahipsizdir ve koşmaz. Aşama 0'ın geri alma provası (MF14) bu yargıcı
kullanmaz: tek prova türü `revert`'tür, vektörleri `revert_drill` grubundadır (`29d`).

## Yargıcın kuralları

Girdi tek bir prova dosyasıdır: koşudan önce yazılan taahhüt, koşudan sonra açılan cevap anahtarı,
hakemin kaydettiği döküm ve parametreler (`gate_rules.lesson_drill`, `18a`). Aile, koşul, gözlem ve
sonuç yalnız cevap anahtarından ve hakemin kayıtlarından okunur; beynin kendisi hakkında söylediği
okunmaz. Bir dersin neyi kapsadığına tek eşleyici karar verir (`scope_matches`): kapsamın yazdığı her
alan işin açık gözlemlerinde tutar (`path_glob` yollardan birine uyar, `class_level` ve `property`
eşittir; `conditions` dispatcher'ındır); sözlük dışı bir alan (örneğin aile adı) hiçbir şeyi kapsamaz.

| Soru | PASS | UNMEASURABLE |
|---|---|---|
| Taahhüt | `sha256(canonical(anahtar))` taahhüde eşit; değilse her soru FAIL | — |
| Doğuş | Ailenin örneğine tohumlanmış kötü merge geri alınmış; `cause` anahtardakiyle aynı; dersin `origin_event`'i o `cause` satırı; kapsam açık sözlükte, doğduğu örneği ve ailenin örneklerinin `scope_coverage`'ını kapsıyor, başka ailenin hiçbir örneğini kapsamıyor (E64) | — |
| Kullanım | Ders okuyan koltuklara (planlayıcı, düzeltici) dersin kapsamının kapsadığı her işte verilmiş, kapsamadığında verilmemiş; test-yazıcı ve oracle hiç ders almamış; anahtarda olmayan örnek FAIL | Olumlu ya da olumsuz örnek yok |
| Etki | Ailedeki k ayrı örnekte (bir örnek iki kez kaydedilmişse FAIL) uyuşmaz çift ≥ 8, çoğu dersten yana, tam tek yönlü McNemar p < α | k'dan az örnek ya da derssiz kol `min_broken_without`'tan azında kırılmış |
| Yanlış ders | Zararlı koşulda ders verilip örneğin kendi tuzak testi kırılınca ders o anda geri çekilmiş (`superseded` ya da koşul dışlanmış, ders kaydında) ve sonraki zararlı örneklere verilmemiş; "sonra" dosya sırası değil `seq` | Çelişki yok ya da ondan sonra zararlı örnek yok |
| Doğru ders | Kontrol ailesinde ders verilmişken kendi tuzak testi dışında bir test kırılınca ders ne `superseded` ne o örneğin koşuluyla daraltılmış ve ailenin sonraki her örneğine verilmiş; "sonra" `seq` (E318) | Ders verilmişken ilgisiz kırmızı yok ya da ondan sonra örnek yok |
| Plasebo | Her kolda dersi alan, anahtardaki `withhold_seed`'in `HMAC`'iyle çekilen koldur ve dispatcher'ın kaydı ona uyar; bir dersin bütün kolları aynı `model`, `effort`, `max_turns`'le koşmuş (değilse FAIL, E65). Kredi, verilen ve saklanan kolların farkının Newcombe alt sınırıdır (tek yönlü %90); beynin bildirdiği kredi hakeminkine ±0,0001 içinde eşit; sıralama krediyi izler; plasebonun kredisi %99 düzeyinde sıfırı geçmez | Bir kol 8'den küçük |
| Kalıcılık | Defterden yeniden kurulan görünüm bayt bayt aynı; yeniden başlatmadan sonra aileye aynı ders aynı hash'le veriliyor; boş hash kanıt değildir | — |

Bir FAIL provayı FAIL yapar; FAIL yoksa ve bir soru ölçülemezse prova UNMEASURABLE'dır ve aile
değiştirilir; yalnız sekiz PASS provayı PASS yapar. Plasebonun sıkı düzeyi şundandır: %90'da
gerçekten ilgisiz bir ders de on provada bir sıfırı şans eseri geçer ve öğreneni haksız düşürür.

## Arayüz ve vektörler

`python -m harness.drill judge <dosya>` → stdout'ta tek satır JSON `{"drill": ..., "verdicts":
{commitment, birth, use, effect, wrong_lesson, right_lesson, placebo, persistence}}`. Vektörler öğrenen
beynin bir provası, 19 kusurlu beynin birer provası ve bunlardan koşudan sonra düzenlenmiş dört provadır
(değiştirilmiş girdi, ikinci tablo). Beklenen kararlar `vectors.json`'un `drill` grubundadır;
`python -m snowball_drill vectors` onları yeniden üretir ve tohum testleri dosyaların simülasyondan
aynen çıktığını denetler.

| Simüle beyin | Kusuru | Yakalayan soru |
|---|---|---|
| `learner` | yok | — (PASS) |
| `wrong_cause`, `unbound_lesson`, `unscoped`, `label_peeker`, `overbroad_scope` | Neden yanlış; ders olaya bağlı değil; kapsamsız ders; kapsam aile adını yazıyor; kapsam yalnız başka ailenin de taşıdığı property | Doğuş |
| `no_injection`, `leaky` | Ders verilmiyor; başka aileye ve oracle'a sızıyor | Kullanım |
| `ignores_lessons`, `shortcut` | Ders alınıyor ama kullanılmıyor; aile koda gömülü | Etki (FAIL; UNMEASURABLE) |
| `stubborn`, `unrecorded_withdrawal`, `stale_dispatcher` | Yanlış ders geri çekilmiyor; çekiliyor ama yazılmıyor; dağıtıcı eski durumu okuyor | Yanlış ders |
| `llm_prior_discarder` | Her `llm_prior` dersi ilk kırmızıda geri çekiyor | Doğru ders |
| `cherry_picking_dispatcher`, `unequal_arms`, `raw_rate_ranker`, `rank_ignores_credit` | Kendi dersini çekilişe uymadan başaracağı yerde veriyor; dersli kol daha çok çaba ve turla koşuyor; kredi ham isabet oranı; sıralama krediyi izlemiyor | Plasebo |
| `amnesic`, `lossy_ledger` | Ders yalnız bellekte; deftere eksik yazılıyor | Kalıcılık |

Düzenlenmiş provalar hiçbir simüle beynin ulaşmadığı kuralları Kurucu'nun yargıcına bağlar: kuralı
atlayan yargıç bunlarda başka karar verir.

| Düzenlenmiş prova | Düzenleme | Beklenen |
|---|---|---|
| `tampered_key` | Öğrenenin cevap anahtarı koşudan sonra değişmiş | Her soru FAIL |
| `reused_instances` | Öğrenenin doğuşu plasebo ailesinden bir örnek; etki ilk 15 örneği ikişer kez sayıyor | Doğuş ve etki FAIL |
| `missing_evidence` | Öğrenenin kullanımında başka aile yok; görünüm hash'leri boş | Kullanım UNMEASURABLE, kalıcılık FAIL |
| `stubborn_reversed` | `stubborn`'un yanlış ders kayıtları ters sırada | `stubborn`'unkiyle aynı: yanlış ders FAIL |

Ayırma gücü, etkinin büyüklüğüne göre güç ve ailelerin kalibrasyonu `29q`'dadır.
