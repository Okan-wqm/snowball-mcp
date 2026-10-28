# Önyükleme Hakemi: Aşama 0'ın Yargıcı

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: kurulumda ve Aşama 0 boyunca
Çapa: beklemede: kurulum — beyin reposundaki `seed/bootstrap/` ve hakem reposundaki kopyası

---

Aşama 0'da Kurucu hakemi yazar; o hakem henüz yoktur, Kurucu da kendi yargıcı olamaz (Y6).
Aradaki boşluğu önyükleme hakemi kapatır: tohumla gelen, küçük, deterministik bir hakem.

**Kim yazar.** Kodu beyin reposunun `seed/bootstrap/` dizinindedir ve Kurucu'dan önce, Kurucu
olmayan bir yazarca yazılır; kendi testlerinden ve tohum vektörlerinden geçer. Kurulum bu kod
olmadan başlamaz (`25`). Operatör onu kurulumda hakem reposuna kurar; Kurucu ona yazamaz.
Aşama 0 çıkışında aktarılan hakem onun yerini alır.

**Boru hattı.** Hakem reposunun zamanlayıcısı beyin reposunun izlenen dalını yoklar; son
kabul edilmiş SHA'dan farklı bir SHA görünce beş iş koşar:

| İş | Sır | Ne yapar | Çıktı |
|---|---|---|---|
| `çek` | Okuyucu App'i | Yeni SHA'nın ağacını ve son kabul edilmiş SHA'dan bu yana tam diff'i çeker | İçerik kimlikli artefakt |
| `getir` | Yok, ağ var | Kurucu'nun kilit dosyasındaki bağımlılıkları kurulum betikleri kapalı getirir | İçerik adresli bağımlılık artefaktı |
| `koş` | Yok, `permissions: {}`, ağ yok | Kurucu'nun kendi testlerini ve tohum vektörlerini (`29a`) iç içe konteynerde koşar: `--network none --cap-drop ALL --read-only --user <uid>`, `ACTIONS_*` yok, docker soketi yok; aynı koşuda bilinen kötü bir girdiyle kırmızı kontrol | Test ve vektör sonuçları, konteyner dışında hash'lenmiş |
| `çağır` | Sağlayıcı kimliği | Tohum rakibini (`29`) tam diff ve ilgili tohum sayfalarıyla, Read/Grep/Glob araçlarıyla, `24`'teki dispatch sözleşmesiyle çağırır; rakibin yeniden üreticilerini bir sonraki `koş`a verir | Rakip kararı ve yeniden üretme sonucu |
| `yaz` | OIDC | Sonuçları hash'leriyle hakem reposunun koşu artefaktlarına ve Rekor'a yazar | Rekor kayıt kimliği |

**Girdi ve taban.** Yalnız beyin reposunun SHA'sı. İlk kabul edilmiş SHA, kurulumda özete yazılan
tohum commit'idir; diff her zaman son kabul edilmiş SHA'dan bu yana tamdır, Kurucu rakibin neyi
göreceğini seçemez.

**Test bildirimi.** Kurucu beyin reposunun kökünde `snowball-tests.json` tutar (`26b`): her §0.9
test numarası için koşturulacak komut, bittiğini söylediği mikro özellikler (`done_mf`) ve
bağımlılık kilit dosyaları. Önyükleme hakemi yalnız bu komutları koşturur; bitti denen her mikro
özelliğin `asama-0/14`'teki test numarası bildirimde bir komuta bağlı değilse ya da hiç komut yoksa
sonuç kırmızıdır (sıfır test kırmızıdır, `04`). Vektörleri hakem kendi koşturucusuyla, `29a`'daki
arayüz üzerinden Kurucu'nun koduna uygular.

**İki tür push.** Yalnız `spec/asama-*/` değiştiren push **spec isteğidir**: test aranmaz; rakip
spec'i tam diff ve ilgili tohum sayfalarıyla çürütmeyi dener; açık `not_refuted` gelirse spec'in
hash'i "donmuş" olarak Rekor'a yazılır. Diğer her push **kod isteğidir** ve aşağıdaki kabulden geçer.
İkisini karıştıran push reddedilir.

**Kabul.** Bir kod SHA'sı ancak şu dördü birlikte doğruysa kabul edilmiş SHA olur: bildirimdeki
Aşama 0 testleri yeşil; vektörlerin hepsi geçer ve bayt değiştirilmiş girdileri reddeder; kırmızı
kontrol kırmızı; rakip açık `not_refuted` verdi ya da hiçbir çürütmesi yeniden üretilemedi.
**Ret artefaktı** tiplidir: `{sha, kind: spec|code, reasons: [{kind, test_id?, ref, detail_sha256}]}`;
Kurucu nedeni oradan okur.

**Aşama 0 çıkışının (A) parçası.** Kurucu `exit-request.json`'a SHA'yı yazar; önyükleme hakemi o
SHA'da Aşama 0'ın tüm kendi-testlerini, vektörleri, kırmızı kontrolü, `spec.lint`'i ve etkinleştirme
provasını koşar. Rakip aşama boyunca en az `stage_params.rival_min_attempts` ayrı artefakta birer
deneme yapmış ve çıkış SHA'sına da bir deneme yapmış olmalıdır. Hepsi tutarsa `referee/` kod
ağacının hash'iyle birlikte Rekor'a "aktarılabilir" kaydı yazar (`25a` 1).

**Asla yapmadıkları.** Hedef repoya, beyin reposuna ve hakem reposunun koduna yazmaz; merge
etmez; Kurucu'nun kodunu sırlı bir işte koşturmaz; Actions önbelleği kullanmaz; kill switch
(`control.json`) kapalı değilse ya da bütçe tavanı aşılmışsa hiçbir iş başlatmaz. Kendi kodunu
değiştirmez: önyükleme hakemi yalnız operatörce kurulur ve aktarımla emekli olur.

**Bütçe ve kayıt.** Rakip çağrıları Aşama 0'ın inşa-zamanı rakip kalemindedir; her çağrının
maliyeti ve sunulan modeli `çağır` işinin yanıttan yazdığı artefakttadır. Bu kayıtlar ve Rekor
kimlikleri etkinleştirmede `brain/state` genesis satırına bağlanır.
