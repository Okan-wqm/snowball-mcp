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

**Girdi.** Yalnız beyin reposunun SHA'sı. Kurucu rakibin neyi göreceğini seçemez: diff her zaman
son kabul edilmiş SHA'dan bu yana tamdır.

**Kabul.** Bir SHA ancak şu dördü birlikte doğruysa kabul edilmiş SHA olur: Kurucu'nun "Aşama 0"
işaretli kendi testleri yeşil; vektörlerin hepsi geçer ve bozulmuş girdileri reddeder; kırmızı
kontrol kırmızı; rakip açık `not_refuted` verdi ya da hiçbir çürütmesi yeniden üretilemedi. Kabul
edilmeyen SHA'nın nedeni artefaktta tipli alanlarla yazar; Kurucu oradan okur.

**Aşama 0 çıkışının (A) parçası.** Kurucu bir SHA'yı çıkış adayı olarak işaretler; önyükleme
hakemi o SHA'da Aşama 0'ın tüm kendi-testlerini, vektörleri, kırmızı kontrolü, `spec.lint`'i ve
etkinleştirme provasını koşar ve rakibin o SHA'ya en az beş denemesini toplar. Hepsi tutarsa
`referee/` ağacının hash'iyle birlikte Rekor'a "aktarılabilir" kaydı yazar (`25a` 1).

**Asla yapmadıkları.** Hedef repoya, beyin reposuna ve hakem reposunun koduna yazmaz; merge
etmez; Kurucu'nun kodunu sırlı bir işte koşturmaz; Actions önbelleği kullanmaz; kill switch
(`control.json`) kapalı değilse ya da bütçe tavanı aşılmışsa hiçbir iş başlatmaz. Kendi kodunu
değiştirmez: önyükleme hakemi yalnız operatörce kurulur ve aktarımla emekli olur.

**Bütçe ve kayıt.** Rakip çağrıları Aşama 0'ın inşa-zamanı rakip kalemindedir; her çağrının
maliyeti ve sunulan modeli `çağır` işinin yanıttan yazdığı artefakttadır. Bu kayıtlar ve Rekor
kimlikleri etkinleştirmede `brain/state` genesis satırına bağlanır.
