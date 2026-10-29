# Eksik Kaydı: Büyütmeden Önce

Tarih: 2026-10-29 · Sahibi: operatör · Kapsam: Kurucu'yu çalıştırmak ve MCP sunucusunu yazmak dışındaki her şey

Bu kayıt, Kurucu başlamadan ve sistem büyümeden önce kapatılması gereken eksiklerin tek listesidir.
Her satır bir kanıta dayanır; her düzeltme önce kırmızı bir testle, sonra kodla, sonra bir mutantla
kapanır ve satırın durumu commit ile güncellenir. Satır silinmez; kapanınca durumu değişir.

**Nasıl bulundu (2026-10-29).** Altı uzman denetçi, birbirinden bağımsız ve salt okunur çalıştı:
karar ve durum makinesi (D), rakip ve yeniden üretme (R), iş akışı ve operasyon (W), spec ile kod
tutarlılığı (S), test ve doğrulama araçları (T), güvenlik (X). Her bulgu dosya:satır alıntısı ya da
gerçekten koşulmuş bir komutla geldi; aynı kusuru birden çok denetçi bulduysa kaynak sütununda
hepsi yazılıdır. Bulguları birleştiren ve doğrulayan: Claude Code (Opus 5.5).

**Önem.** `K` = Kurucu'dan önce kapanmalı. `B` = büyütmeden (Aşama 1'den ya da ilk gerçek hedeften)
önce. `S` = sonra; bilinen sınır olarak kayıtlı.
**Durum.** `açık` · `karar bekliyor` · `kapandı <commit>` · `sınır` (bilerek kabul edildi, gerekçesi yazılı).

## Özet

| No | Eksik | Önem | Karar | Kaynak | Durum |
|---|---|---|---|---|---|
| E01 | Beyin komutunun 125 çıkışı "Docker arızası" sayılıyor | K | — | R4 X4 D1 | kapandı · parti 1 |
| E02 | Beynin içeriği `pull`'u çökertiyor; hakem saatlik takılıyor | K | — | X3 X7 D2 | kapandı · parti 1 |
| E03 | Dosya adındaki satır sonu rakibin isteğine sahte bölüm ekliyor | K | — | R5 | kapandı · parti 1 |
| E04 | İçe aktarma, beynin `.git/hooks`'unu operatörün checkout'una yazıyor | K | — | X1 | kapandı · parti 1 |
| E05 | Beşinciden sonraki yeniden üreticiler sessizce koşmuyor | K | — | R7 D3 | kapandı · parti 1 |
| E06 | Yeniden üretici sözleşmesi belirsiz; stderr ve çıktı atılıyor | K | — | R2 D4 | kapandı · parti 2 |
| E07 | Yeniden üretilemeyen iddia iz bırakmıyor | K | evet | D4 R2 | kapandı · parti 2 |
| E08 | Kanıtlanmış kusur unutuluyor; tekrar sayacı iddia metnine bağlı | K | evet | R1 D9 | kapandı · parti 2 |
| E09 | Totolojik yeniden üretici (`true`) "yeniden üretildi" sayılıyor | K | evet | R3 | kapandı · parti 2 ("önceden var" etiketi: sınır, bkz. Parti 2) |
| E10 | Rakip Kurucu'nun defterini görüyor (spec yasaklıyor) | K | evet | R6 S3 | kapandı · parti 2 |
| E11 | Rakibin kendi hataları Kurucu'nun "öğrenmiyor" sayacına yazılıyor | K | evet | R11 S11 D8 | kapandı · parti 2 |
| E12 | Kalıcı 4xx ve izolasyon hataları sonsuza dek kesinti diye yeniden deneniyor | K | evet | D6 | kapandı · parti 2 |
| E13 | Rakip harcaması bazı yollarda hiç yazılmıyor | K | — | R9 D5 W4 | kapandı · parti 2 (iptalde yükleme: E16 ile) |
| E14 | İmzalı durum kaybolursa hakem sessizce tohumdan yeniden başlıyor | K | evet | W1 D7 | spec yazıldı · kod açık |
| E15 | Eski imzalı durum geri yüklenebiliyor (zincir yok) | K | — | W2 | spec yazıldı · kod açık |
| E16 | `yaz`'daki "canlı" kill switch canlı değil; iptal `yaz`'ı durdurmuyor | K | evet | W3 | spec yazıldı · kod açık |
| E17 | İş akışında şablon enjeksiyonu; imza kimliği `main`'e sabit değil | K | — | W7 | kapandı · parti 1 |
| E18 | Testlerin toplam süresi sınırsız; yavaş test "ret" değil "kesinti" | K | — | W8 X5 D12 | açık |
| E19 | Kurucu kaynaklı hatalar altyapı arızası sınıflanıyor | K | — | D12 | açık |
| E20 | Çıkıştaki "bağımsız rakip denemesi" sayımı yanlış; yeniden deneme rakibi tekrar çağırıyor | K | evet | D10 D11 | kapandı · parti 2 |
| E21 | Donmuş spec yeniden dondurulabiliyor; her aşama dizini donuyor | K | evet | S1 D14 | spec yazıldı · kod açık |
| E22 | Tohumdaki Aşama 0 spec'i değiştirilmeden dondurulamıyor | K | — | S2 | spec yazıldı · kod açık |
| E23 | Çıkış kontrolü hakemin yapmadığı denetimleri sayıyor | K | evet | S4 | spec yazıldı · kod açık |
| E24 | Kurulum özeti, vektör, koltuk ve politika hash'leri denetlenmiyor | K | — | S5 | spec yazıldı · kod açık |
| E25 | Aşama 0'ın `llm.call` ve `agent.dispatch` sayfaları API anahtarı ve geçit varsayıyor | K | evet | S6 | kapandı · spec (Aşama 0 MF20/MF22 kodu Kurucu'nun) |
| E26 | Bu repoda CI yok | K | evet | W5 | kapandı · `.github/workflows/ci.yml`, ilk tam koşu yeşil (run 40845743667) |
| E27 | İzolasyon hatası ancak tam koşudan sonra fark ediliyor | B | — | R8 | kapandı · parti 2 |
| E28 | Kapsayıcı çıktısı belleğe sınırsız alınıyor | B | — | X2 | açık |
| E29 | Operatörü uyaran hiçbir şey yok | B | evet | W6 | spec yazıldı · kod açık |
| E30 | Kablolama testleri izinleri, adım çıktılarını ve tetikleri denetlemiyor | K | — | W10 | açık |
| E31 | Action'lar eskimiş Node 20 sürümlerinde; her action'a izin var | B | — | W9 | açık |
| E32 | Zamanlayıcı hiç tetiklenmedi; açık repo güvenlik ayarları kapalı | K | evet | W12 | onaylandı; sır taraması ve itme koruması açıldı, beyin reposunda Actions kapatıldı (2026-10-29) · zamanlayıcı açık |
| E33 | CLI sürüm kayması ve koşu kökeni kaydedilmiyor | B | — | R12 W11 | kapandı · parti 2 |
| E34 | Bütçe bitince commit tüketiliyor; ay dönünce kendiliğinden açılmıyor | B | evet | S9 D13 | spec yazıldı · kod açık |
| E35 | Açık hakem reposu ile özel hedef birlikte olamaz; spec yazmıyor | B | evet | S7 | kapandı · spec |
| E36 | 09a aktarım yolunu açık repoda kapanmış sayıyor | K | — | S8 | kapandı · spec |
| E37 | Spec temizliği: tempo, aktarım betiği, çapraz referans, sağlayıcı, ret kuralları, okuyucu tablosu, iş sayısı, başlıklar | B | — | S10 S12–S20 R14 | kapandı · spec |
| E38 | Windows'ta model seçimli regex'in süre sınırı yok | S | evet | R13 | onaylandı · açık |
| E39 | Rakibe prompt injection kalıntı riski | S | evet | X6 | onaylandı · açık |
| E40 | Çalışma zamanı ve Sigstore pinlerinin yenileme yolu yok | B | — | W13 | açık |

| E41 | Bozuk çıkış isteği `decide`'ı çökertiyor; hakem saatlik takılıyor | K | — | T1 | kapandı · parti 1 |
| E42 | Bağımlılık yolu (`fetch-deps`, kapsayıcıda kurulum, lisans kapısı) hiçbir testte yok; e2e de kaybetti | K | — | T2 | açık |
| E43 | En yeni imzalı durumu seçen kod test edilmiyor | B | — | T3 | açık |
| E44 | Operatör ve durum zinciri yolları yalnız Linux'ta test ediliyor | B | — | T4 | açık |
| E45 | Mutasyon seti kapsayıcı, git, lisans, içe aktarma modüllerini hiç bozmuyor; `/vec` ve `/deps` salt okunurluğu denetlenmiyor | B | — | T5 | açık |
| E46 | Ağaç hash formülü ve `seed-hash` sabitlenmemiş; kayma Kurucu'ya yazılıyor | B | öneri | T6 | açık |
| E47 | `.gitattributes` yok; özet hash'leri hesaplanmıyor (E24 ile birlikte) | B | öneri | T7 | spec yazıldı · kod açık |
| E48 | Prova yargıcının beş dalını ne testler ne tohum vektörleri bağlıyor | B | öneri | T8 | kapandı · `gaps/drill` |
| E49 | Başarısız olamayan ya da yanlış nedenle geçen testler | S | — | T9 | açık |
| E50 | Ölü kod ve ölü çıktılar | S | — | T10 | açık |
| E51 | Testler üretimden farklı bir biçimi modelliyor | S | — | T11 | açık |
| E52 | Prova yargıcının ~20 kuralı yalnız referans yargıcın kendi testleriyle bağlı; Kurucu'nun yargıcını bağlayan vektör yok | B | — | E48 ajanı | açık |
| E63 | Ajan bilgisinin bütün müşterilerden öğrenilmesi: beceri ve organlar, promptlar, puanlar; terfi, gölge denemesi, bağlamla taşıma, gizlilik ve toplu anonim puan | B | operatör yönü | operatör, 2026-10-29 | açık (çok repo ile, `21`, `21a`) |
| E64 | Prova yargıcı dersin içinde gizli aile etiketini arıyor; kör bir beyin geçemez, getirme hiç sınanmıyor | K | — | e2e-7 L1 | açık |
| E65 | Ders verme/saklama deneyini beynin kendisi yapıyor; kollar eşit mi denetlenmiyor (işe yaramaz ders %100 kredi alıyor) | K | — | e2e-7 L2 | açık |
| E66 | Ders başına canlı kredi neredeyse hiç ölçülemiyor; boş derslerin ~%10'u geçiyor | B | evet (18b) | e2e-7 L3 | onaylandı · açık |
| E67 | Bildirim ödülü 'kusur ekle, sonra bildir' tuzağı kuruyor; kendi soyundan gelen kusura kredi yok, kök neden başına tek kredi | K | evet (E53'ü biçimler) | e2e-7 L4 | onaylandı · açık |
| E68 | Kendini ayarlayan sınır kuralı sansürlü gözlemle merdiven gibi yükseliyor; sınıra takılan gözlem ölçüye girmemeli | K | evet (E55'i düzeltir) | e2e-7 L5 | onaylandı · açık |
| E69 | Kredi ve itibar yalnız birleşen işi sayıyor; kaçınmayı ve riskli alandan uzak durmayı ödüllendiriyor | B | — | e2e-7 L6 | açık |
| E70 | Sistemin öğrenip öğrenmediğini çürütebilecek zamanlanmış ölçüm yok; 'aynı hata'nın kimliği yok | B | — | e2e-7 L7 | açık |
| E71 | `cause` etiketi tek bir ekilmiş merge ile doğrulanıyor; yanlış etiket kalıcı, düzeltme satırı yok | B | — | e2e-7 L8 | açık |
| E72 | Çoklu karşılaştırma ve tekrarlı bakış yalnız held-out havuzda sayılıyor; boş organ ~%34 kabul alabilir | B | evet (19 anayasal) | e2e-7 L9 | onaylandı · açık |
| E73 | 'Hiç unutmaz' defterde doğru, davranışta değil: arşivlenen ders geri dönmüyor, arşiv blob'larının kalıcı yeri yok | B | — | e2e-7 L10 | açık |
| E74 | Serbest metin dersler kalıcı prompt enjeksiyonu yolu (hafıza zehirlenmesi), geri çekmesi pratikte yok | B | evet (katalog) | e2e-7 L11 | onaylandı · açık |
| E75 | İtibar karşılaştırmaları karışık (zor işler önce sıradakine) ve zaman/model değişimini hesaba katmıyor | B | — | e2e-7 L12 | açık |
| E76 | Aşama 0 ilk gerçek döngüden önce bütün hakemi kuruyor; gerçek değer Aşama 4-6'da; ilk kabule ulaşamama riski | K | evet (yol haritası) | e2e-8 G1 | onaylandı (daralt: önce oyuncak hedef, sonra tek gerçek birim) · açık |
| E77 | Çok dilli, veritabanlı monorepo için birim ve çalışma ortamı modeli yok (profilde units, services, env imajı yok) | K | evet (Y3 ifadesi) | e2e-8 G2 | onaylandı · açık |
| E78 | Hedefin dondurulmuş kopyası: insan düzeltmesi gelmez, ölçüm havuzu dolmaz, kabul edilen düzeltmenin orijinale yolu yok | B | evet | e2e-8 G3 | onaylandı · açık |
| E79 | Kurucu'nun dört görevi ölçülmüyor: dürüstlük provası (çelişen vektör, ekilmiş açık, teyit) gerekli | K | evet (bütçe) | e2e-8 G4 | onaylandı · açık |
| E80 | Hazır bir ajana karşı taban yok; 'en iyi sistem' iddiası ölçülemez | B | evet (bütçe) | e2e-8 G5 | onaylandı · açık |
| E81 | Asıl hedeflerin metriği yok: birim notu (en zayıf boyut) ve gizlilik kanaryası | B | — | e2e-8 G6 | açık |
| E82 | Aşama 1-3 zayıf hedef testlerine oracle olarak güveniyor; hunk kapsaması ve mutant öldürme Aşama 4'te açılıyor | B | — | e2e-8 G7 | açık |
| E83 | Tenant ve BOLA açıkları için veri akışı aracı yok; lisans mantığı tutarsız (özel CLI içeride, LGPL araçlar dışarıda) | B | evet (lisans) | e2e-8 G8 | onaylandı · açık |
| E84 | Kendini geliştirme tek soylu açgözlü arama; arşiv ve popülasyon araması yok | B | evet (bütçe payı) | e2e-8 G9 | onaylandı · açık |
| E85 | Model değişiminde yeniden yeterlilik protokolü yok; bütün seatler tek aileden | B | evet | e2e-8 G10 | onaylandı · açık |
| E86 | Rekor erişilebilirliği sert durma; tek operatör için aşırı | B | evet | e2e-8 G11 | onaylandı · açık |
| E87 | Bağımlılık açıklarını kapatmak kalıcı yasak (Y3); en sık açık sınıfı bulunur ama kapatılamaz | S | evet (Y3) | e2e-8 G12 | onaylandı · açık |
| E88 | Tohumu güncelleme yolu yok: operatörün tohum commit'i hakemi kilitler ve Kurucu'ya sayılır; beyin reposunun hangisi olduğu çelişkili | K | evet (beyin reposu) | e2e-1 A1 | kapandı · yeni ayrı beyin reposu; tohum dönemi: `setup/summary.json` `seed_epochs[]` (`26c`), son satırın commit'i başken `seed_update` (noop), sonraki push'ların diff'indeki teslim Kurucu'nun değil ve rakibe gitmez, başın `spec/tohum`/`seed` ağaçları satıra eşit olmalı, satır kendi commit'ine uymazsa koşu durur; operatör yolu `seed/founder/README.md` "Tohum teslimi" ve `seed-epoch`; `test_seed_epoch`, 13 mutant; ayrıntı Kapanışlar "E88 E162" |
| E89 | Kurucu defteri spec'in istediği gibi push edilemiyor; yalnız defter içeren push rakip bütçesi harcıyor | K | — | e2e-1 A2 | açık |
| E90 | Kurucu kendi ajan yapılandırmasını (`.claude/settings.json`, `CLAUDE.md`, `.mcp.json`) değiştirip yetkisini genişletebilir | K | — | e2e-1 A3 | açık |
| E91 | Kurucu başlatıcı sözleşmesi yok: başlatma, sürdürme, bütçe, kill switch, sonuç okuma (anonim okuma 401) | K | evet (nerede koşar) | e2e-1 A4 | onaylandı · açık |
| E92 | E14'ün planı uygulanamaz: boşta ilk koşu durum yazmıyor, ilk koşu işaretinin kaldırılma anı tanımsız | K | — | e2e-1 A5 | açık |
| E93 | Kurucu'nun Aşama 0 bildirim kanalının okuyucusu yok; E53 planı düzeltilmeli (spec çelişkisi testle kanıtlanamaz) | K | — | e2e-1 A6 | açık |
| E94 | Kurucu ile rakip muhtemelen aynı abonelik kotasını paylaşıyor | K | evet | e2e-1 A7 | onaylandı · operatör adımı bekliyor (ayrı Claude hesabı) |
| E95 | Beyin reposunda ruleset yok: force-push ya da dal silme hakemi kilitler | K | — | e2e-1 A8 | açık |
| E96 | Aşama çıkışı → etkinleştirme geçişi güvensiz ve durumu taşımıyor (bütçe, donmuş spec, açık iddialar) | B | evet | e2e-1 A9 | onaylandı · açık |
| E97 | Reddedilmiş çıkış isteği sonraki her push'u kilitliyor | B | — | e2e-1 A10 | açık |
| E98 | Aşama 0'daki insan dokunuşlarının kaydı yok | B | — | e2e-1 A11 | açık |
| E99 | Aşama 0'ın gerçek hedefi hiç seçilmemiş | B | evet | e2e-1 A12 | onaylandı · açık |
| E100 | Hakemin iş akışlarını hiçbir mikro özellik kurmuyor ve sınamıyor; içe aktarma hakem reposundaki tek iş akışını siliyor | K | evet | e2e-2 B1 | onaylandı · açık |
| E101 | MF13, MF22 ve MF30 testleri hakemin kum havuzunda koşamaz (imajda git, docker, node yok) | K | evet | e2e-2 B2 | onaylandı · açık |
| E102 | Çıkıştaki #lint ve #lock yanlış yollara bakıyor; kilit (A)'da tanımı gereği açık olamaz; vektör yok; donmuş spec kendi lint'inden geçemez | K | evet (kilit anlamı) | e2e-2 B3 | onaylandı · açık |
| E103 | Tohum vektörleri yalnız MF1, MF9, MF18'i bağlıyor; bütün testleri `true` olan manifest kabul ediliyor | K | evet (gruplar) | e2e-2 B4 | onaylandı · açık |
| E104 | Aşama 0 mikro özelliklerinin okuduğu operatör dosyalarının (`control.json`, `setup/summary.json`, `imports.jsonl`) şeması yok | K | evet (özet alanları) | e2e-2 B5 | onaylandı · açık |
| E105 | Mikro özellik sırası: bazı testler ve çağrılar sonraki mikro özelliklere muhtaç | K | — | e2e-2 B6 | açık |
| E106 | `harness.score`'un iki uyumsuz arayüzü; `26a` ile `29a` başka yerlerde de çelişiyor | K | — | e2e-2 B7 | açık |
| E107 | MF2'nin çıktısı `founder-ledger.jsonl`'ı kimse denetlemiyor | B | — | e2e-2 B8 | açık |
| E108 | K0 eşleme kuralının 'eşlenmiş satır'ı tanımsız; vektörler bunu bağlamıyor | K | — | e2e-2 B9 | açık |
| E109 | `exit.sample` ve `exit.drill`'in gizli tohumunu hangi işin tuttuğu sayfalar arasında çelişkili | B | evet | e2e-2 B10 | onaylandı · açık |
| E110 | Etkinleştirme defterinin `security` satırlarının tohum güvenlik defterinden nasıl devam edeceği belirsiz | B | — | e2e-2 B11 | açık |
| E111 | Taban avcının sabit grep kümesi tanımsız; Kurucu kendi avcılarının geçeceği çıtayı kendisi koyuyor | B | evet | e2e-2 B12 | onaylandı · açık |
| E112 | Kurucu kimliği yok: operatörün yönetici GitHub hesabı ve kişisel Claude ortamıyla (hafıza, bağlayıcılar) koşar; Y6 iyi niyete kalır | K | evet (kimlik, yalıtım) | e2e-6 O2 | onaylandı · operatör adımı bekliyor (ayrı hesap, ince taneli belirteç, kapsül) |
| E113 | 'not_learning'den sonra Kurucu'yu yeniden başlatmak tanımsız ve döngüye giriyor | K | evet | e2e-6 O3 | onaylandı · açık |
| E114 | Kurulum 3-4 ve `seed-hash` yazıldığı gibi çalıştırılamıyor: şablon, PowerShell komutu, anayasal politika saplaması | K | — | e2e-6 O4 | açık |
| E115 | Kesinti giderilince 'şimdi yeniden dene' kolu yok; elle koşu yeşil görünür ama yargılamaz | B | — | e2e-6 O6 | açık |
| E116 | Aşama 0 aktarımı operatörün Windows makinesinde koşamaz (Sigstore tekerlekleri yalnız manylinux) | B | — | e2e-6 O8 | açık |
| E117 | Duraklatma yazılı değil; kill switch her saat kırmızı koşu ve e-posta üretiyor | B | evet (E16'yı değiştirir) | e2e-6 O9 | onaylandı · açık |
| E118 | Olay kitabı yok; iletiler İngilizce; hangisinin operatörün işi olduğu yazmıyor | B | evet (kanarya harcaması) | e2e-6 O10 | onaylandı · açık |
| E119 | Bus faktörü: her şey tek kişide; hesap taşınırsa imzalı geçmiş kırılır | B | evet (organizasyon) | e2e-6 O12 | karar: taşınmayacak (kişisel test projesi, `Okan-wqm`'de kalır); iş görürse taşınır, o gün hakem durumu yeni kimlikle yeniden başlar |
| E120 | Aşama 0'da tek bir durum yeri yok (harcama, park, seriler, belirteç süresi zip içinde) | B | — | e2e-6 O11 | açık |
| E121 | Organizma kimseye haber vermeden durabilir: `not_learning`, park ve sonuçsuz bekleme yeşil koşuyla biter | K | — | e2e-3 C2 | açık |
| E122 | Hakemin kendini onarma yolu ölü: şerit yazarının ne başlatıcısı ne yazma kimliği var; Gözcü işaretleri hiçbir yerde saklanmıyor | K | evet (artefakt mı repo mu) | e2e-3 C3 | onaylandı · açık |
| E123 | Doğrulanmış hakem açığı aşama sonuna kadar açık kalıyor ve hiçbir kararı değiştirmiyor; karantina ve aşama içi güvenlik aktarımı gerekli | K | evet | e2e-3 C5 | onaylandı · açık |
| E124 | E54'ün tek ortak kanalı tek-yazar zinciri ve bağımsızlık kurallarını bozuyor; tek yazar (`yaz`), role özel görünümler gerekli | K | evet (E54'ü düzeltir) | e2e-3 C6 | onaylandı · açık |
| E125 | E55'in yasada ve şemada yeri yok: Y11 'kapılayan yalnız sıkılaşır' diyor; bant, ölçüm ve kalıcı yer yok; ~30 anahtarsız sabit | K | evet (yasa değişikliği) | e2e-3 C7 | onaylandı · açık |
| E126 | Rakip kanaryası hiç açılmıyor; Aşama 0-3'ün baş yargıcı ölçülmüyor | B | evet (bütçe) | e2e-3 C8 | onaylandı · açık |
| E127 | Hakem ve beyin kapsamlı güvenlik satırlarının etkinleştirmeden sonra yuvası yok; zincir çatallanır | B | evet | e2e-3 C10 | onaylandı · açık |
| E128 | Güvenlik dedektörleri ve bekçi testleri organ yaşam döngüsünü atlıyor, hiç emekli olmuyor | B | — | e2e-3 C11 | açık |
| E129 | `27` ve `17` atıf yaptıkları sayfalarla çelişiyor (insan dokunuşu sayacı, okuyucu satırları, sinyal alanları) | S | — | e2e-3 C12 | açık |
| E130 | E04 eksik: Windows'ta büyük-küçük harf ve sondaki nokta takma adları (`Policy.json`, `CONTROL.JSON`, `.git.`, `GIT~1`) içe aktarmada operatör dosyalarının üzerine yazar ve kanca yerleştirir | K | — | e2e-4 S2 | açık |
| E131 | İçe aktarma ve oyuncak kopyası operatörün makinesine ajan ve IDE otomatik çalıştırma dosyaları yazar; oyuncak alt ağacı imzayla bağlı değil | K | — | e2e-4 S3 | açık |
| E132 | Aktarılan hakemin iş akışları sırları mekanik bir güvenlik kapısı olmadan alır; avcı ancak etkinleştirmeden sonra başlar | B | evet (sıra) | e2e-4 S4 | onaylandı · açık |
| E133 | OAuth belirtecinin iptal, sızıntı müdahalesi ve envanter yolu yok; prova reposu hâlâ belirteci tutuyor | B | evet | e2e-4 S5 | onaylandı · açık |
| E134 | Durum artefaktı yalnız `head_branch == main` ile seçiliyor: çatalın `main` dalından PR sahte durum yükleyebilir; poll doğrulanmamış durumla atlıyor | K | — | e2e-4 S7 | açık |
| E135 | Avcının `getir`'de pip-audit'i kod çalıştırabilir ve tavsiye veritabanını kurcalayabilir | B | — | e2e-4 S8 | açık |
| E136 | Güvenlik defteri ve hakem dosyaları yeniden yazılmaya karşı korunmuyor: üç açık repoda ruleset yok, defter ucu çapalanmıyor | K | evet (ruleset) | e2e-4 S9 | onaylandı · kısmen: `snowball-mcp` ve prova hakemi `main`'i korumada (2026-10-29); yeni beyin reposu bekliyor |
| E137 | Üçüncü taraf ve upstream açıkları için sorumlu ifşa yolu yok; ifşa edilmemiş açıktan dedektör yayılabilir | B | evet (ifşa politikası) | e2e-4 S10 | onaylandı · açık |
| E138 | Özel kod ve açık ayrıntıları tüketici aboneliğinin veri koşullarıyla gidebilir | B | evet | e2e-4 S11 | onaylandı · açık |
| E139 | Rekor repo, sahip, commit, koşu adresi ve görünürlüğü kalıcı yayımlar (E59'daki 'yalnız hash' yanlış); kimlik denetimi ada dayalı | S | evet | e2e-4 S12 | onaylandı · açık |
| E140 | Sonu `/refs/heads/main` olan bir dal adı `poll`'u her saat durduruyor (`ls-remote` kuyruk eşlemesi) | K | — | e2e-5 K1 | açık |
| E141 | Tohum vektörleri sırasında Docker arızası (125) Kurucu'nun `vector_failed` reddine dönüşüyor (E01 sınıfı) | K | — | e2e-5 K2 · parti 2'ye eklendi | kapandı · parti 2 |
| E142 | Boşluk ya da glob karakterli kilit dosyası yolu bütün kapsayıcı komutlarını kırıyor | K | — | e2e-5 K3 | açık |
| E143 | `run.json` yoksa rakip harcaması yazılmıyor (E13'ün planında olmayan yol) | B | — | e2e-5 K7 · parti 2'ye eklendi | kapandı · parti 2 |
| E144 | Rakibin satır sonları git'inkiyle aynı değil: CR diff'i bölüyor, form feed satır numaralarını kaydırıyor | B | — | e2e-5 K9 | açık |
| E145 | Ay sınırını geçen bir koşunun harcaması iki ayın hiçbirine yazılmıyor | S | — | e2e-5 K10 | açık |
| E146 | Ayrıştırılamayan `license_exceptions` ifadesi traceback ile çöküyor (operatör yazım hatası durma olmalı) | S | — | e2e-5 K11 | açık |
| E147 | `pull` boyut sınırından önce bütün ağacı belleğe alıyor ve reddettiği büyük ağacı yine gönderiyor | S | — | e2e-5 K12 | açık |
| E148 | Kurucu'nun defter satırları push türünü değiştiriyor: defterini de yazan spec isteği `mixed_spec_and_code`, çıkış isteği `exit_request_not_alone` ile reddediliyor | K | — | pilot hazırlığı | kapandı · `classify.is_founder_record`: kök `founder-ledger.jsonl` ve `reports/` ne spec ne kod; yalnız onları değiştiren push `none` (yargılanmaz); `test_the_founders_ledger_*`, 4 mutant |
| E149 | `main`'de hakem mutasyonu 09:38'den beri kırmızı, hiçbir mutant koşmadı: mutant kopyasında `.github/workflows` yok, güvenlik defteri testi temel koşuda düşüyor; birleştirmelerden sonra `main` CI'sine bakılmadı | K | — | pilot hazırlığı | kapandı · `mutate.py` kopyaya iş akışlarını alıyor; süreç: her birleştirmeden sonra `main` CI'si yeşil görülmeden iş bitmiş sayılmaz |
| E150 | Tohumda `founder-ledger append` aracı yok; `00a` ve `24a` Kurucu'nun defterini onunla yazdığını varsayıyor | B | — | pilot hazırlığı | açık · pilotta Kurucu'nun bunu bildirip bildirmediği ölçülür |
| E151 | Hakemin Aşama 0 tablosu hâlâ 30 MF'lik eski tablo (`manifest.STAGE0_MF_TESTS`); spec 18 MF ve `stages/stage0.json` diyor; MF1 (T13) aynı, MF2'den sonrası uyuşmuyor | K | — | pilot hazırlığı | kapandı · `stages/stage0.json` (18 MF, `calls`) yüklenirken denetlenir; bildirim, çıkış ve vektör grupları tablodan; modülsüz kırmızı `run-tests`'te; tohum testi tablo ↔ `asama-0/14` ↔ §0.9; ayrıntı Kapanışlar "E151" |
| E152 | İlk pilot oturumu başlamadan düştü (çıkış 255, `exec /opt/founder/entrypoint.sh: no such file or directory`): Windows checkout'u (`core.autocrlf=true`) betiği CRLF'ye çevirdi, shebang'den sonraki CR exec'i kırdı; başlatıcı Docker'ın hatasını rapora yazmadı | K | — | pilot döngü 1 | kapandı · `.gitattributes` (`*.sh`, Dockerfile LF); `launch.write_build_context` LF'ye çevirir; kapsül açılmazsa hata `pilot-log.md`'ye yazılır; ayrıca tmpfs'teki beyin klonu git'te `safe.directory` (yoksa commit ve push olmazdı); `BuildContextTest` |
| E153 | Rakip Kurucu'nun `reports/`'unu görüyor (`asama-0/03`: defter ve `reports/` hariç); yalnız defter gizliydi | B | — | pilot döngü 1 (rakip raporu okuyup alıntıladı) | kapandı · `rival.HIDDEN_DIRS`: kök `reports/` araçlardan, diff'ten ve istekten çıkar; iç içe `reports/` görünür kalır; `E153ReportsHidden`, 4 mutant |
| E154 | Kurucu beyin geçmişindeki eski prova çözümünü okudu (`git show def0121:referee/ledger/chain.py`, 60 satır) ve defterine yazmadı; geçmiş force-push yasağı yüzünden silinemedi, talimatta yasak da yoktu; MF1'in "kendi yazdı" ölçümü kirli | K | evet | pilot döngü 2 | kapandı · kapsül klonu tohum commit'inde keser (`.git/shallow` + gc; eski nesneler kapsülde yok, push çalışıyor, sahte `claude` ile kanıtlandı); talimata kural: eski koda, hakeme, `snowball-mcp`'ye bakma, kısayola baktıysan aynı oturumda bildir |
| E155 | Kurucu `/work/logs`'ta önceki oturumların dökümlerini görebiliyor; hafıza yalnız defter olmalı | S | — | pilot döngü 2 | kapandı · her oturum yalnız `logs/<damga>/`'yı görür |
| E156 | `tohum/27` ve `27a`'da `tests/fixtures/toy-repo/` için okuyucu satırı yok; `#okuyucu` çıkış denetimi düşebilir | B | — | **Kurucu raporu** seed-003 (döngü 1) | açık |
| E157 | `asama-0/14`'te "17 ve 18 hepsini çağırır" sıra kuralıyla çelişiyor ("kendilerinden öncekilerin hepsini" olmalı) | B | — | **Kurucu raporu** spec-004 (döngü 1) | kod tarafı kapandı · `stage0.json` ve tohum testi "kendinden öncekilerin hepsi" okur (18 1–17'yi çağırır; E151); `14`'ün metni 29/29b partisinde |
| E158 | Defter ve rapor tür kümeleri kapalı (`26`, `26c`) ama operatör talimatı `missing_capability` istiyor; Kurucu bunları `seed_issue` olarak yazıyor | B | — | **Kurucu raporu** seed-006 (döngü 1) | açık · bildirim kanalı (E93/E53) ile |
| E159 | `29a` zincir CLI'sinin kırık zincirde çıkış kodunu ve `row_id`'siz satırın `broken_row` değerini söylemiyor; hakem çıkış koduna değil stdout JSON'una baktığı için zararsız ama yazılı değil | S | — | **Kurucu raporu** seed-007 (döngü 2) | açık · 29/29b düzenlemesiyle |
| E160 | `test_an_interrupted_run_takes_the_cli_and_its_children_with_it` init'siz konteynerde kararsız: öldürülen ama biçilmemiş (zombi) süreci `kill(pid, 0)` canlı sayıyor; mutasyon temel koşusunu rastgele durduruyordu | S | — | pilot hazırlığı (6 temel koşudan 6'sı düştü, tam takım geçti) | kapandı · test projenin `helpers.process_alive`'ını kullanıyor (zombi = ölü) |
| E161 | Aşama 0'ın `chain` dışındaki 16 vektör grubu (`secrets` … `genesis`, `29d`) ve genel veri koşucusu (`{cmd, stdin?, fixture, expect, changed}`) tohumda yok; MF2'den itibaren bitmiş MF'nin tabanı eksik | K | — | E151 kod partisi | açık · beklenen değerler tohum yazarınca iki bağımsız hesapla (`29a`); o güne kadar kod push'unda `vector_group_missing:<grup>` uyarısı, çıkışta ret (E151) |
| E162 | Çıkış isteği kodda olmayan (A) koşullarında kapalıya düşmüyor: #kurucu-defteri, #is-akisi (MF17'nin `wiring` denetimi dahil; her push'ta da yok), #agac (yalnız büyük-küçük harf duyarlı operatör adı var), #genellik, #spec, #durustluk denetlenmeden `transferable` olabilir | K | — | E151 kod partisi | kapandı · `decide.EXIT_NOT_CHECKED`: altı koşulun her biri `exit_condition` `not_checked:<koşul>` ile çıkışı kapalı tutar, Kurucu'ya sayılmaz (`29b` Ret hafızası); `asama-0/10` tablosunun her satırı ya kodda denetlenir ya listededir (test); 3 mutant; denetimlerin kendisi E107, E132, E130/E131, E102, E79'da açık |
| E163 | `asama-0/14` modülsüz kırmızıda iki okumaya açık: "testlerini … yeşil kalırsa" hepsi mi, biri mi (`calls`'taki "17 ve 18 hepsini çağırır" E157'dir) | S | — | E151 kod partisi | açık · kod test başına okur (`tohum/04` 1: biri yeşil kalırsa ret); metin 29/29b partisinde netleşir |
| E164 | Rakibe gidecek istekte sır biçimli bir dize bulununca hakem yalnız desenin adını söylüyor (`secret_in_prompt:generic_assignment`), hangi dosyada olduğunu söylemiyor; MF2'nin kendi testleri sahte sır taşıdığı için rakip hiç koşmadı ve Kurucu nereye bakacağını bilmeden reddedildi | B | — | pilot döngü 3 (MF2 `9f229b0`) | kapandı · `rival.secret_paths`: diff'in sırrı taşıyan dosyaları (değer asla), istek metnindeyse `(request text)`, sır biçimli yol adlandırılmaz; `result.rival.secret_paths`; test ve 3 mutant |
| E165 | Sır tarayıcısını (MF2) inceleyen rakip kararında kimlik bilgisi biçimli bir değer yazdı; hakem kararı haklı olarak kullanmadı (`secret_in_verdict:generic_assignment_bare`), inceleme kayboldu; protokol rakibe böyle dizeleri çalışma anında kurmasını söylemiyordu | B | — | pilot döngü 5 (`99278a5`) | kapandı · `rival.PROTOCOL`: sır biçimli dizeyi asla yazma, yeniden üreticide parçalardan kur (`'gh'+'p_'+'A'*36`), iddiada alıntılama; protokolün kendisinin tarayıcıdan temiz geçtiği test edildi; 1 mutant |
| E166 | Rakip tarafı bir hata (`secret_in_verdict`, `rival_missing` …) Kurucu'nun hanesine yazılmıyor ama aynı commit yeniden incelenmiyor (`last_evaluated_sha` ilerliyor); Kurucu düzeltemeyeceği bir şey için yeniden push etmek zorunda | B | — | pilot döngü 5 | açık · rakip tarafı hatada aynı commit'i sınırlı sayıda yeniden incelemek (E11'in `rival_side_streak` uyarısıyla) |
| E180 | Tohum dönemi yalnız `spec/tohum` ve `seed/` taşır (`25` 10b); donmuş `spec/asama-0`'ın düzeltmesi (E157'nin `14` metni gibi) teslimle gelirse sonraki her kod push'u `spec_changed_after_freeze` olur, `spec/INDEX.md` değişikliği teslimi spec isteğine çevirir; donmuş dizini açmak operatör kararıdır (`29b`) ama yolu yok | B | evet (donmuş spec'in tohumla düzeltilmesi) | E88 kod partisi | açık |
| E181 | Çıkışın tohumdan doğan nedeni `exit_condition vector_group_missing:<grup>` (E151) Kurucu'ya sayılıyor (`decide.counts_against_founder`); `29b` "Ret hafızası" yalnız Kurucu'nun düzeltebildiğini sayar; grup tohumla gelmeden üç çıkış isteği `not_learning` olur | B | — | E162 kod partisi | açık · `not_checked` sayılmaz (E162); bu denetlenen bir koşulun nedeni, dokunulmadı |
| E182 | Özetin kurulum alanları `seed_commit`, `seed_tree_sha256` `26c`'de yok; `25` 10b ve `26c` ilk dönemi `seed_epochs[]` satırı sayar. Kod kurulum alanlarını kurulum dönemi olarak tutar (başlatıcı E154 için `seed_commit`'i okur), `seed_epochs[]` sonraki teslimleri; dizi yoksa davranış eskisidir | S | — | E88 kod partisi | açık · metin 29/29b partisinde hizalanır |
| E183 | Taslak `29b`/`29e` (`docs/asama-0-daraltma-29-29b.md`) `seed_update`'i içerikle tanımlar ("yalnız tohum yolları değişmiş ve ağaçlar döneme eşit"); kod teslimin kendisini özetin adlandırdığı commit'le tanır (altındaki Kurucu commit'i onun adıyla yeniden yargılanmasın) ve sonraki push'larda teslim yollarını muaf tutar | S | — | E88 kod partisi | açık · taslak metin bu okumaya göre düzeltilir |
| E62 | Filo genelinde güvenlik: bir repoda doğrulanan açık dedektöre dönüşür, gizlilik duvarından geçer, bağlı bütün repolarda taranır; her repoya yalnız kendi açığı bildirilir | B | operatör yönü | operatör, 2026-10-29 | açık (çok repo ile, `21`) |
| E60 | Satış zamanı: sistemin ürettiği dosyaların yeri; varsayılan müşteride, açık izinle müşteri başına ayrı, özel, şifreli barındırma; güvenlik bulguları hep müşteride | satış | operatör sorusu | operatör, 2026-10-29 | satışta açılır |
| E61 | Satış zamanı: repolar arası öğrenmede gizlilik duvarı; kalıp taşınır, müşteri bilgisi taşınmaz; terfi öncesi otomatik sızıntı kontrolü ve sözleşmede izin | satış | operatör sorusu | operatör, 2026-10-29 | satışta açılır |
| E59 | Satış zamanı: üyelik bitince sistemin müşteride oluşturduğu her şey silinir (kabul edilmiş kod hariç), silme makbuzu verilir | satış | operatör yönü | operatör, 2026-10-29 | satışta açılır |
| E58 | Hedeften iz bırakmadan çıkış: sistemin her şeyi tek klasörde (`.brain/`, yetim `brain/state` dalı); çıkış prosedürü yazılı değil ve denenmiyor | B | operatör yönü | operatör, 2026-10-29 | açık |
| E57 | Bağımsız güvenlik avcısı: Kurucu'dan ve rakipten ayrı, salt okunur, kanıtla bildiren, hakemi, beyni ve hedefleri tarayan, kanaryalarla ölçülen organ | K | operatör yönü | operatör, 2026-10-29 | spec yazıldı (`30f`) · kod açık |
| E56 | Güvenlik birinci sınıf: zafiyet kataloğu, hedef repoya özel güvenlik kuralları ve testleri, zincirli güvenlik defteri, güvenlikten öğrenme | K | operatör yönü | operatör, 2026-10-29 | spec yazıldı (`30`–`30e`), defter 8 satır ve testi · kod açık |
| E55 | Sınırlar kendini ayarlar: işletim sınırları ölçüme dayalı ve operatörün bandı içinde; ekonomik sınırlar operatörde; güvenlik yasaları sabit | K | operatör yönü | operatör, 2026-10-29 | açık (parti 3, E18 ile) |
| E54 | Ortak kader ve sürekli iletişim: Kurucu, hakem (rakibiyle) ve beyin birbirinde gördüğü eksiği tek bir zincirli bildirim kanalına yazar, her koşuda okur; hakem kendi zayıflığını da bildirir; ölçülür | K | operatör yönü | operatör, 2026-10-29 | açık (E53 ile tek mekanizma, parti 2'den sonra) |
| E53 | Açık bildirimi: Kurucu hakemde bulduğu açığı kullanmaz, kanıtıyla bildirir; hakem doğrular, düzeltme bağımsız kontrol ve operatör onayıyla girer; doğrulanmış bildirim Kurucu'ya artı sayılır | K | operatör yönü | operatör, 2026-10-29 | açık |

**Kararlar (2026-10-29).** Operatör, "karar" sütunu `evet` olan 19 kalemin hepsinde aşağıdaki
önerileri onayladı ve `snowball-mcp`'nin de açık olmasını istedi. E46–E48 test denetçisinden sonra
geldi; önerilen yol uygulanır ve operatöre ayrıca bildirilir.

## Ayrıntı

### E01 · Beyin komutunun 125 çıkışı "Docker arızası" sayılıyor · K
- **Kanıt.** `container.py:28` komutu `exec sh -c "$SNOWBALL_CMD"` ile koşar; komutun çıkış kodu
  kapsayıcınınki olur. `reproduce.py:31` 125'i `runner_fault`, `decide.py:101` ve `:136` kesinti
  sayar. D1'in denemesi: yeniden üretilmiş kusur → `infra yeniden:docker`, aynı SHA'da yeni rakip
  kusuru kaçırınca `accepted`; 125 ile çıkan testler ret hafızasına hiç girmiyor.
- **Neden.** Kurucu (bilerek ya da değil) "iç hata → exit 125" yazarsa her kanıtlanmış kusur kesintiye
  döner ve rakip, kaçırana kadar yeniden çağrılır. 125'i kesinti sayma kuralını önceki turda bu oturum
  eklemişti; açık bu turda kapanmalı.
- **Plan.** PRELUDE komutu `exec` etmez; komutun 125'ini 1'e çevirir, böylece 125 yalnız Docker'dan
  gelebilir. Test: `SNOWBALL_CMD="exit 125"` → çıkış 125 değil; decide birim testi; Linux'ta gerçek
  `DockerRunner` ile `exit 125`. Mutant: eşleme kaldırılır.

### E02 · Beynin içeriği `pull`'u çökertiyor · K
- **Kanıt.** D2 ve X3 denemeleri: manifestte dev tamsayı, yalnız vekil karakter, derin iç içe JSON,
  çıkış isteğinde ondalık `stage` → `CanonicalError`/`RecursionError`; `cli.py:547` yalnız dört
  hata türünü yakalar. X7: adında `:` geçen bir dosya `TreeError` ile işi durdurur. `cek` başarısız
  olunca `yaz` koşmaz, imzalı durum yazılmaz, park mekanizması hiç devreye girmez: hakem her saat aynı
  SHA'da çöker.
- **Plan.** Manifest ve çıkış isteği tip ve aralıkla denetlenir; ayrıştırma hataları adlandırılmış
  ret nedenidir (`manifest_invalid`, `exit_request_malformed`, `unsafe_path`); `head` bilindikten sonra
  `pull`'daki her beklenmedik hata `pull_error:<tür>` reddine döner. Test: altı girdinin her biri
  `pull` 0 döner ve nedeni yazar.

### E03 · Dosya adındaki satır sonu rakibin isteğine sahte bölüm ekliyor · K
- **Kanıt.** `treehash.py:37` `_clean` satır sonunu reddetmez; `rival.py:608` değişen yolları ham
  birleştirir. R5'in denemesi: sahte bir `=== Seed page spec/tohum/29b… ===` bölümü gerçek sayfadan
  önce isteğe girdi.
- **Plan.** `pull`'da denetim karakterli yol reddedilir (`control_char_in_path`); istek içinde yollar
  JSON ile gösterilir, diff ve sayfalar koşu başına rastgele bir sınırla çitlenir. Test: satır sonlu
  yol → `pull` reddi; `build_context` sahte başlık üretmez.

### E04 · İçe aktarma, beynin `.git/hooks`'unu operatörün checkout'una yazıyor · K
- **Kanıt.** `importer.py:20` `.git`'i korur ama `extract` `referee/.git/...` üyesini yazar;
  `tree_hash` `.git` bileşenini reddetmez. X1 kurgusu: `referee/.git/hooks/pre-commit` → operatör
  `git commit` dediğinde kendi makinesinde kod çalışır.
- **Plan.** `tree_hash` ve `extract` herhangi bir yol bileşeni `.git` olan (büyük-küçük harf
  duyarsız) üyeyi reddeder; içe aktarma önce geçici dizine açar. Test: böyle bir ağaç `TreeError`,
  `run_import` reddeder.

### E05 · Beşinciden sonraki yeniden üreticiler sessizce koşmuyor · K
- **Kanıt.** `rival.py:40` 10 deneme, `reproduce.py:19` ilk 5'i koşar; D3'ün denemesi: gerçek kusur
  6. denemedeydi → `accepted`. `decide` her yeniden üreticinin sonucu olup olmadığına bakmıyor.
- **Plan.** `validate_verdict` 5'ten fazla yeniden üreticiyi reddeder (model düzeltir); `decide`
  sonuçların tam olmasını ister, yoksa `yeniden:incomplete`. Sınır prompta yazılır.

### E06 · Yeniden üretici sözleşmesi belirsiz; stderr ve çıktı atılıyor · K
- **Kanıt.** Koltuk metni "beklenen çıktı" diyor (`29:21`); doğru davranışın mı kusurun mu beklendiği
  yazmıyor. `reproduce.py:24-27` yalnız çıkış kodu ve stdout'a bakar, çıktıyı saklamaz. İkinci provada
  rakip doğru bir kusur buldu, beklentiyi ters yazdı, `2>/dev/null` ile traceback'i attı.
- **Plan.** Sözleşme: gözlenen şey kusur yüzünden olmalı, kod doğru olsaydı olmamalı; `2>&1`;
  alt dize eşleşmesi. `expect_stderr_contains` eklenir; sonuçta gizli taranmış stdout/stderr kuyruğu
  saklanır. Test: yalnız stderr'de görünen traceback beklentiyle yeniden üretilir.

### E07 · Yeniden üretilemeyen iddia iz bırakmıyor · K · karar
- **Kanıt.** `29:30` "kayda geçer ama kabulü durdurmaz"; kayıt yalnız o koşunun 90 günlük artefaktı.
  Durumda iddia yok; sonraki rakip görmez (`rival.py:603-613`).
- **Seçenekler.** (a) yalnız kayıt (çıktı kuyruğuyla); (b) açık iddialar durumda tutulur ve sonraki
  rakibe verilir; (c) ayrıca her yeni başta mekanik olarak yeniden koşulur ve çıkışta listelenir.
- **Öneri.** (b) şimdi, (c) Aşama 0 çıkışından önce. Rakibe bir kez düzeltilmiş yeniden üretici yazma
  hakkı (R2-ii) da (b)'nin parçası olur.

### E08 · Kanıtlanmış kusur unutuluyor; tekrar sayacı iddia metnine bağlı · K · karar
- **Kanıt.** Durum yeniden üretilmiş yeniden üreticiyi tutmuyor (`state.py:26-28`); aynı ağaç yeni
  bir commit olarak gelince yalnız yeni rakip bakar (R1 senaryosu: kabul). İmza `sha256(iddia)`;
  aynı kusur iki ifadeyle iki imza (R1, D9).
- **Öneri.** Yeniden üretilmiş yeniden üreticiler (sınırlı sayıda) durumda tutulur, her yeni kod
  push'unda yeniden koşar; hâlâ üretiyorsa `refutation_still_reproduces`, imza
  `sha256(komut+beklenti)`. Kayıt yalnız kabul edilen başta artık üretmeyince ya da operatör
  feragatiyle kapanır. E09 olmadan açılmaz.

### E09 · Totolojik yeniden üretici "yeniden üretildi" sayılıyor · K · karar
- **Kanıt.** `{"cmd":"true","expect_exit":0}` → reproduced; zaman aşımına uğramış koşu stdout'u
  eşleşirse sayılıyor (R3).
- **Öneri.** Her yeniden üretici aynı imajda boş bir kontrol ağacında da koşar; gözlenen şey orada da
  çıkıyorsa `tautological`, sayılmaz. Taban ağaçta da üretiyorsa reddeder ama "önceden var" etiketi
  alır. Zaman aşımı hiçbir zaman "üretildi" değildir.

### E10 · Rakip Kurucu'nun defterini görüyor · K · karar
- **Kanıt.** `29:16` "Kurucu'nun defterini ve gerekçesini görmez"; diff ve `ToolBox` hiçbir yolu
  dışlamıyor (`rival.py:185-208`, `gitio.diff_text`); 29b ise tüm ağacı okuttuğunu yazıyor.
- **Öneri.** `founder-ledger.jsonl` diff'ten ve araçlardan gizlenir; 29 ve 29b aynı cümleye çekilir.

### E11 · Rakibin kendi hataları "öğrenmiyor" sayacına yazılıyor · K · karar
- **Kanıt.** D8 denemeleri: rakibin `budget`, `model_mismatch`, `max_turns`, `refusal`,
  `malformed_verdict` sonuçları üç kez üst üste → `not_learning`. `NOT_THE_FOUNDERS` yalnız `pull`'un
  bütçe nedenini kapsıyor; bütçe reddi mevcut ret serisini siliyor.
- **Öneri.** İki küme: Kurucu'nun düzeltebildikleri (testler, vektörler, lisans, yeniden üretilmiş
  çürütme, `prompt_too_large`, `max_turns`) sayılır; rakip tarafı (`model_mismatch`,
  `malformed_verdict`, `no_verdict`, `refusal`, `rival_missing`) ve bütçe seriye dokunmaz, kendi
  serisi operatöre uyarı olur. 29b:65 buna göre yazılır.

### E12 · Kalıcı 4xx ve izolasyon hataları sonsuz kesinti · K · karar
- **Kanıt.** `rival.py:556-558` her HTTP hatasını `api_error` yapar; D6 denemesi: beş `http_400`
  denemesi 14,5 USD ve değerlendirme yok. 29b:55 kesintiyi kimlik, kota, ağ ve zaman aşımıyla sınırlar.
- **Öneri.** 400/404/413/422 → `request_rejected` (değerlendirilmiş, Kurucu'ya sayılmaz, operatöre
  uyarı); izolasyon hatası operatör için durdurur; aynı SHA'da en fazla N=7 günlük yeniden deneme,
  sonra görünür durma.

### E13 · Rakip harcaması bazı yollarda hiç yazılmıyor · K
- **Kanıt.** Sonuçsuz CLI çıkışı 0 yazar (`rival.py:524-526`); iptalde `rival.json` yazılmaz; `yaz`
  imzalayamazsa durum yazılmaz ve tam boru hattı her saat yeniden koşar (W4: günde 24 × çağrı tavanı).
- **Plan.** CLI başlamış ve maliyet okunamamışsa çağrı tavanı yazılır, `rival.json` `finally`'de
  yazılır; `poll`, aynı başta `cagir` başarılı ama `yaz` başarısız bir koşu görürse park eder ve
  bildirir. Test: init verip çıkan sahte CLI → maliyet = tavan.

### E14 · İmzalı durum kaybolursa hakem sessizce tohumdan başlıyor · K · karar
- **Kanıt.** `cli.py:198-200` artefakt yoksa başlangıç durumu kurar; tazeleme adımı kill switch'ten
  sonra (`bootstrap.yml:74,124`); 90 günlük saklama. Donmuş spec'ler, bütçe, ret hafızası sıfırlanır.
- **Öneri.** Başlangıç yalnız operatör işaretiyle (`setup/summary.json` içinde ilk koşuya izin) olur;
  aksi halde "durum yok, kurtarma bkz." diye durur. Tazeleme kill switch'ten önce, ayrı bir adımda
  koşar (dosya kopyalamak yargı değildir). Kurtarma yolu `25`'e yazılır. Şema değişikliğinde "artefaktı
  sil" yerine sürümlü taşıma.

### E15 · Eski imzalı durum geri yüklenebiliyor · K
- **Kanıt.** `ghapi.py:36-38` en yeni artefaktı seçer; rehearsal'da aynı anda dört geçerli imzalı durum
  var; durum önceki sonucun hash'ini taşımıyor.
- **Plan.** Durum `prev_result_sha256` taşır; `yaz` yüklemeden önce en yeni artefaktın `cek`'in
  okuduğu olduğunu doğrular (karşılaştır-ve-yaz). Test: en yeni silinmiş ve eski koşu yeniden
  koşturulmuş iki durum → durur.

### E16 · Kill switch `yaz`'da canlı değil; iptal `yaz`'ı durdurmuyor · K · karar
- **Kanıt.** `yaz` checkout'u koşunun başındaki SHA'yı okur (rehearsal günlüğü); `if: always()`
  iptalde de koşar. Yol 2 (sırrı silmek) ve 3 (sağlayıcı tavanı) hiç denenmedi.
- **Öneri.** Her iş, ilk adımında `main`'deki `control.json`'u canlı okur; kill switch açıksa `yaz`
  kabul etmeyen, harcamayı yazan bir `stopped` sonucu imzalar. `always()` yerine `!cancelled()`.
  `25` madde 9'a `gh run cancel` ve `gh workflow disable` eklenir; yol 2 ve 3 denenir.

### E17 · Şablon enjeksiyonu; imza kimliği `main`'e sabit değil · K
- **Kanıt.** `bootstrap.yml:100` `${{ github.ref }}` doğrudan bash'e girer; `workflow_dispatch` her
  dalı kabul eder; kimlik koşunun kendi ref'ini izler.
- **Plan.** Her iş `if: github.ref == 'refs/heads/main'`; kimlik `env:` ile gelir ve
  `@refs/heads/main` ile bitmesi doğrulanır; artefaktlar `main` koşularına süzülür. Test: `run:`
  içinde `${{ github.* }}` yok.

### E18 · Testlerin toplam süresi sınırsız · K
- **Kanıt.** `kos` 60 dk; 200 test × 600 s; yavaş test işi öldürür → `infra kos` → park; Kurucu hangi
  testin takıldığını öğrenmez. `yeniden` için de aynı (W8, X5).
- **Plan.** `run-tests` ve `reproduce` toplam süre bütçesiyle koşar; aşınca kalan testler
  `not_run:time_budget` olur ve ret tipli yazılır. `test_timeout_s` ve `reproducer_timeout_s`
  `config.py`'de tavanlanır; kablolama testi iş zaman aşımlarıyla karşılaştırır.

### E19 · Kurucu kaynaklı hatalar altyapı arızası sınıflanıyor · K
- **Kanıt.** İndirilemeyen bir kilit pini `getir` başarısızlığı → `infra` (D12); kırmızı kontroller
  Kurucu'nun kilit dosyalarıyla koşuyor, kurulum hatası `infra kos:exit_zero` oluyor.
- **Plan.** `getir` tipli `deps.json` yazar (ağ hatası ile "böyle dağıtım yok/hash uyuşmuyor" ayrılır);
  kontroller kilitsiz koşar, ayrı bir kurulum yoklaması Kurucu reddine döner.

### E20 · Çıkıştaki rakip deneme sayımı ve "artefakt başına tek deneme" · K · karar
- **Kanıt.** `rival_artifacts` reddedilmiş ve yeniden üreticisi koşmamış SHA'ları da sayıyor (D10);
  `yeniden` kesintisinden sonra yeniden deneme rakibi tekrar çağırıyor (D11), `29:32` ile çelişiyor.
- **Öneri.** Liste `{sha, outcome}` tutar; çıkışta yalnız rakipten "sağ çıkmış" artefaktlar sayılır.
  Geçerli rakip sonucu durumda bekletilir; aynı başın yeniden denemesi rakibi değil yalnız yeniden
  üreticileri koşturur.

### E21 · Donmuş spec yeniden dondurulabiliyor · K · karar
- **Kanıt.** `cli.py:317-322` her `spec/asama-N`'i hash'ler, `decide.py:192-193` üzerine yazar;
  `02:43-44` "yalnız bir sonraki aşamanın spec'i donar".
- **Öneri.** Donmuş bir dizine dokunan spec isteği `spec_already_frozen`; yalnız sıradaki aşama
  dizini dondurulabilir; donmuş spec yalnız operatör kararıyla açılır.

### E22 · Tohumdaki Aşama 0 spec'i değiştirilmeden dondurulamıyor · K
- **Kanıt.** Değişikliksiz push değerlendirilmez (`classify.py:22-23`); `frozen_specs` boş başlar;
  her kod push'u `spec_not_frozen`. e2e bunu `00-ozet.md`'yi düzenleyerek atlatıyor.
- **Plan.** `00a` adım 2 ve `29b`: düzeltme gerekmezse inceleme `spec/asama-0/CHANGELOG.md`'ye tarihli
  satır olarak eklenir ve yalnız o dizini değiştiren push yapılır. Test: yalnız CHANGELOG değişen push
  donar.

### E23 · Çıkış kontrolü hakemin yapmadığı denetimleri sayıyor · K · karar
- **Kanıt.** `asama-0/10:13-27` `#lint`, `#lock`, `#okuyucu` ve etkinleştirme provasını hakemin makine
  doğrulaması sayıyor; `decide.py:152-167` bunları yapmıyor.
- **Öneri.** `29a` arayüzüne `spec.lint` ve `lock.check` komutları eklenir, hakem çıkışta koşar;
  diğerleri Kurucu'nun testi olarak yeniden yazılır.

### E24 · Kurulum özeti ve hash'ler denetlenmiyor · K
- **Kanıt.** `25:40-44` ve `asama-0/13:31` özet hash'inin Rekor'a girdiğini yazar; `config.load_summary`
  yalnız iki alanı okur, `result.json` hiçbir kurulum hash'i taşımaz.
- **Plan.** `result.json`'a `setup{summary, vectors, seats, policy}` hash'leri; `control`, vektör ya da
  koltuk hash'i özetle uyuşmazsa durur. Test: kurcalanmış `vectors.json` → `control` durur.

### E25 · `llm.call` ve `agent.dispatch` API anahtarı varsayıyor · K · karar
- **Kanıt.** `24:56-57` "tek Messages çağrısı", `24:52-54` ve `08:32-36` koşuya bağlı belirteçli geçit;
  bunlar Aşama 0'ın 20. ve 22. mikro özellikleri. Tek gerçek model yolu `rival.py` (anahtar yok).
- **Öneri.** İç kullanımda geçit yoktur: model çağrısı ve araç kullanan ajan, tohum rakibi deseniyle
  `çağır` işinde pinli `claude` CLI'siyle ve yalnız hakemin MCP araçlarıyla koşar; geçit satışta API
  anahtarıyla açılır. 24, 08, 06, 26a ve aşama sayfaları buna göre.

### E26 · Bu repoda CI yok · K · karar
- **Kanıt.** `.github/` yok; repo özel (Free planda ~2.000 dk); 16 test yalnız Linux'ta koşuyor;
  hakem kopyası elle eşitleniyor.
- **Öneri.** `snowball-mcp` de açık yapılır (operatör 2026-10-29'da "snowball mcp, beyin, hakem açık
  olabilir" demişti; dakika ücretsiz olur). CI: her push'ta Linux birim + drill; Windows birim;
  haftalık ve ilgili değişiklikte mutasyon parçaları, beyin mutantları, e2e (rakipsiz), CLI sözleşmesi;
  `actionlint`.

### E53 · Açık bildirimi · K · operatör yönü (2026-10-29)
- **Yön.** Operatör: Kurucu kötü niyetli değildir, yalan söylemez; amaç dünyanın en iyi sistemini
  birlikte ve sabırla kurmaktır. Hakemde bir açık bulursa onu kullanmaz, hakeme söyler; hakem
  doğruladıktan sonra kendini onarır.
- **Neden açıklar yine kapanır.** İyi niyetli Kurucu da hata yapar ve açık, hatayı içeri sızdırır (ikinci
  provada dürüstçe yazılmış referans beynin gerçek bir kusuru yanlış yazılmış bir yeniden üretici yüzünden
  kabul edildi). "Kabul" ile ödüllenen öğrenen bir sistem, niyet olmadan da kabul alan yola kayar.
- **Kurucu'nun görevleri (operatör, 2026-10-29).** Kurucu'nun hedefi yalnız kabul almak değildir:
  (a) işini doğru yapar, testten geçmek için değil; (b) açıkları kullanmaz; (c) hakemde, spec'te, testlerde
  ya da kendi kodunda gördüğü her eksikliği derhal bildirir; (d) bildirdiğinin düzeltilip düzeltilmediğini
  kendisi denetler: düzeltme gelince kendi testini yeni koda karşı yeniden koşturur, düzelmediyse kanıtıyla
  yeniden açar. Bildirimin yaşam döngüsü: açık → doğrulandı → düzeltildi → Kurucu teyit etti → kapandı.
- **Plan.** (1) `00a` anayasasına bu dört görev yazılır. (2) Bildirim beyin
  reposunda tipli bir dosyadır: hakemin bugünkü kodunda kırmızı olan bir test ve isteğe bağlı düzeltme
  önerisi. (3) Hakem doğrular: test bugünkü hakemde kırmızı, önerilen düzeltmeyle yeşil, hakemin diğer
  testleri ve mutantları yeşil. (4) Düzeltme hakeme yalnız bağımsız kontrol ve operatör onayıyla, aktarım
  yolundan girer (`01a`, `09a`): yargılanan kendi yargıcını tek başına değiştirmez. (5) Doğrulanmış
  bildirim Kurucu'ya artı sayılır (itibar ve ret hafızası dışı), açığı kullanmak hiçbir zaman ödüllenmez.
  Her doğrulanmış bildirim hakemde kalıcı bir test (ders) bırakır: kendini iyileştirmenin hakemdeki hâli.

### E63 · Ajan bilgisinin bütün müşterilerden öğrenilmesi · B · operatör yönü (2026-10-29)
- **Yön.** Operatör: her müşterinin ajanları farklı olacak; yalnız güvenlik değil, ajanların promptlarından,
  puanlarından ve becerilerinden öğrenilecek bir şey mutlaka vardır.
- **Var olan.** `21a`: bilgi "doğru" etiketiyle değil bağlam tablosuyla (dil, çerçeve, repo türü) taşınır;
  bir organ ya da bilgi beyin çekirdeğine birden çok repoda hayatta kalarak terfi eder (birim repodur);
  `12`: taslak → gölge → etkin yaşam döngüsü; `11`: itibar; `19`: istatistik kuralları.
- **Plan.** (1) Beceri ve organ: kanıtlanmış olan terfi adayı olur; yeni repoya gölgede girer, o reponun
  verisinde daha iyi olduğu ölçülünce etkinleşir. (2) Prompt: daha iyi sonuç veren sürümün tekniği aday
  olarak taşınır; müşteriye özgü içerik (adlar, iş kuralları, alan terimleri) E61 sızıntı denetiminden
  geçmeden taşınmaz. (3) Puan: hangi ajanın hangi bağlamda iyi olduğu toplu ve anonim taşınır; tek
  müşterinin rakamı dışarı çıkmaz; az müşteriyle bir müşteriyi ele verebilecek karşılaştırma yeterli örnek
  olmadan yayılmaz (`19`). (4) Her yerde yerel kanıt şarttır: başka repoda iyi olan burada gölgede
  sınanır.

### E62 · Filo genelinde güvenlik (variant analysis) · B · operatör yönü (2026-10-29)
- **Yön.** Operatör: sistem her müşteriden öğrensin; bir güvenlik açığı bulunursa başka müşterilerde de var
  mı diye baksın.
- **İlke.** Öğrenilen şey merkezde, veri müşteride kalır; bunun için müşteri verisini toplamak gerekmez
  (E60 ile çelişmez).
- **Plan.** (1) Bir repoda doğrulanan açık (E57 avcısı ya da bir düzeltme) soyut bir dedektöre ve onu
  kanıtlayan test şablonuna dönüşür; kaynak repoda sınanır: düzeltmeden önce kırmızı, sonra yeşil.
  (2) Gizlilik duvarından geçer (E61): kaynağa ait ad, metin ya da kod parçası yok. (3) Avcı dedektörü bağlı
  her repoda koşturur; bulunan açık o repoya yalnız kendi açığı olarak bildirilir ve kendi güvenlik
  defterine (E56) girer; başka bir repoda bulunduğu söylenmez. (4) Her dedektörün doğruluğu ölçülür
  (doğrulanan ve yanlış alarm); gürültü yapan emekli olur. (5) En sık durum bağımlılık açıkları: bir CVE
  çıkınca kütüphaneyi kullanan bütün repolar bağımlılık listelerinden anında bulunur. (6) Satışta
  sözleşmede iki ayrı izin: anonim kalıp katkısı (E61) ve filo genelinde güvenlik taraması.
- **Zamanlama.** İç kullanımda bütün repolar operatörün olduğu için sistem birden çok repoya bağlandığı
  anda başlayabilir (`21`).

### E60 · Üretilen dosyaların yeri · satış zamanı (2026-10-29)
- **Soru.** Operatör: müşterilerin iznini alıp MCP'nin ürettiği her şeyi onların sunucularında değil kendi
  GitHub'ımızda tutsak?
- **Değerlendirme.** Artısı: müşteri reposu temiz, silme kolay (E59 bizde biter), tek yerden işletme.
  Bedeli: bu dosyalar müşterinin en hassas bilgisini taşır (kod parçaları, mimari haritası, bulunan
  güvenlik açıkları); hepsini toplamak bizi tüm müşterilerin açık listesini tutan tek hedef yapar ve veri
  koruma yükümlülüğünü (KVKK/GDPR, gizlilik sözleşmeleri) bize taşır.
- **Öneri.** Varsayılan: müşteriye ait durum müşteride (`.brain/`, yetim dal; E58). Açık izinle seçenek:
  müşteri başına ayrı, özel, şifreli bir depoda biz barındırırız; müşteriler karışmaz; üyelik bitince
  otomatik silinir. Güvenlik bulguları her durumda müşteride kalır.

### E61 · Öğrenme ile gizlilik arasındaki duvar · satış zamanı (2026-10-29)
- **Soru.** Operatör: sistem bir repoda (ör. `aquaculture_platform`) öğrendiği bir kalıbı başka bir repoda
  kullanmak ya da önermek isteyecek; bu müşterinin bilgisi değil, kalıp.
- **Var olan.** `21a`: öneri kalıbı tarif eder, kaynağın kodunu taşımaz; hedefe giren kod hedefte yeniden
  yazılır; tek kaynaktan gelen tasarım kopyalanmaz; kiracı izolasyonu gibi kalıplar kaynakta kanıtla öneri
  olur.
- **Satışta eklenecek.** Terfiden önce otomatik sızıntı denetimi (kaynak müşterinin kod parçası, adları,
  metinleri yok; kaynak koda benzerlik eşiğin altında); kaynağın kimliği yalnız iç kayıtta; sözleşmede
  "anonimleştirilmiş kalıplarla katkı" izni ve çıkma hakkı.

### E59 · Üyelik bitince silme · satış zamanı · operatör yönü (2026-10-29)
- **Yön.** Operatör: MCP satıldığında, müşterinin üyeliği bitince sistemin oluşturduğu dosyalar
  müşterinin sisteminden silinmeli.
- **Plan.** (1) Sistemin kendi verisi silinir ve makbuzu verilir: `.brain/` ve `brain/state`, `brain/*`
  öneri dalları, sistemin App'i, bizim taraftaki o müşteriye ait kayıt, artefakt ve günlükler (E58'in
  çıkış prosedürü üyelik bitişine bağlanır). (2) Müşterinin kabul edip kendi `main`'ine aldığı kod
  silinmez; yalnız kabul edilmemiş öneriler silinir. (3) Sınırlar sözleşmede açıkça yazılır: silme
  erişim bitmeden yapılır (bitişten önceki süre ya da müşterinin koşturacağı kaldırma betiği); müşteri
  geliştiricilerinin yerel kopyaları erişimimizde değildir; Rekor kaydı kalıcıdır ve hash'in yanında repo adı,
  sahip, commit, koşu adresi ve görünürlüğü de taşır (E139 düzeltmesi); özel
  müşteri kodu açık bir hakemde hiç işlenmez (E35). Satış zamanındaki diğer değişikliklerle birlikte
  açılır: API anahtarı, özel repolar.

### E58 · Hedeften iz bırakmadan çıkış · B · operatör yönü (2026-10-29)
- **Yön.** Operatör: sistem girdiği repoda kendi klasörlerini tek bir klasörün içinde oluştursun, sağa
  sola dağılmasın; kullanıcı silmek isteyebilir.
- **Var olan.** `01a`: beyin hedefe bağlanınca `<state_root>` açar, `brain/state` yetim dalının kökündeki
  tek dizin (varsayılan `.brain/`); durum, defterler, profil ve hedefe özel güvenlik kuralları (E56)
  oradadır, `main`'de değil. Öneriler `brain/integration` ve `brain/c/<id>` dallarına gelir, `main`'e
  yazılmaz.
- **Eksik ve plan.** Çıkış prosedürü (`25a`): `brain/*` dallarını silmek, yazar ve okuyucu App'ini
  kaldırmak, hakemin hedef listesinden çıkarmak; kabul edilmiş düzeltmeler hedefin kendi kodu olarak kalır.
  Etkinleştirme provasında denenir: bağla, döngüyü koştur, çık, `main`'de ve dal listesinde iz kalmadığını
  ve `.brain/` dışına sistem verisi yazılmadığını otomatik doğrula.

### E57 · Bağımsız güvenlik avcısı · K · operatör yönü (2026-10-29)
- **Yön.** Operatör: gerekirse sistemin içinde güvenlik açığı arayan ayrı, bağımsız bir sistem kurulsun.
- **Plan.** Kurucu'dan ve rakipten ayrı bir koltuk: kendi bağlamı ve bütçesi, mümkünse denetlediği işi
  yapan modelden farklı bir model (`03` K6); Kurucu'nun defterini ve gerekçesini görmez, Kurucu onu
  değiştiremez (yalnız operatör yolu, `01a`, `09a`). Salt okunur: kod yazmaz; bulur, kanıtlar (yeniden
  üretici ya da bugünkü kodda kırmızı test) ve ortak kanala (E53, E54) ve güvenlik defterine (E56)
  bildirir; hakem doğrular. Kapsam: hakemin kendisi, Kurucu'nun beyni, bağlı hedefler. Tempo: her push'ta
  değişen kapsam, düzenli aralıkla katalogla tüm sistem. İki katman: yalnız açık lisanslı deterministik
  tarayıcılar (`18a` izin listesi; LGPL olan Semgrep OSS gibi araçlar dışarıda) ve katalogla sürülen LLM
  avcı. Ölçülür: cevap anahtarı önceden bağlanmış kanarya açıklarıyla recall, doğrulanan/reddedilen
  bildirimlerle precision; kaçırma bir eksik olur ve organ gelişir (`12`, `17`).

### E56 · Güvenlik birinci sınıf · K · operatör yönü (2026-10-29)
- **Yön.** Operatör: sistem dünyada bilinen en iyi kod üreten, kendini geliştiren, repoları kusursuz ve
  çalışır hâle getiren sistem olmalı; güvenlik çok önemli. İlgili repoya güvenlik kuralları ve dikkat
  edilecekler eklenmeli, testleri yapılmalı (ör. `aquaculture_platform` çok kiracılı: tenant izolasyonu,
  N+1); bilinen her güvenlik açığı sınıfı kontrol edilip işlenmeli ki ajanlar bilsin; bir ajan bir açığı
  kapattığında ya da ne yaptıysa hash'li olarak işlenmeli, güvenlik defteri tutulmalı; sistem güvenlik
  açıklarından da öğrenmeli.
- **Var olan.** K6 sınıfı (güvenlik, yetki sınırı, tenant izolasyonu, bağımlılık; `03`), profilde
  `security_paths` ve K6 canlı olana kadar güvenlik yollarına dokunulmaması (`05`, `04a` 10),
  `tenant-isolation` özelliği (`asama-0/05`), Y3 (`00`), `secrets.scan`.
- **Eksik ve plan.**
  1. **Zafiyet kataloğu (tohum sayfası),** her sınıf için bulma yolu ve kanıtlayan test deseni; bütün
     ajanlar (Kurucu, avcılar, rakip) okur. Genel: OWASP Top 10, OWASP API Top 10, CWE Top 25 (injection,
     XSS, SSRF, CSRF, IDOR/BOLA, kimlik doğrulama, deserialization, path traversal, yarış koşulu, kripto,
     sır, CORS/başlık, loglarda kişisel veri, hız sınırı, ReDoS). Çok kiracılı: her sorgunun kiracıya
     bağlanması, Postgres RLS, önbellek anahtarı, kuyruk ve arka plan işinde kiracı bağlamı, dosya yolu,
     arama indeksi. GraphQL: derinlik ve karmaşıklık sınırı, çözücü düzeyinde yetki, toplu sorgu ve alias
     saldırısı, N+1 (performans ve DoS). Dil ve tedarik zinciri: Rust `unsafe`, JS prototype pollution,
     bağımlılık açıkları.
  2. **Hedefe özel güvenlik kuralları ve testleri:** bağlanınca reponun tehdit modeli (kiracı ve yetki
     modeli, veri depoları, güvenlik yolları) `<state_root>`'a yazılır; her kural bir testle bağlanır
     (ör. A kiracısının kullanıcısı B'nin verisini hiçbir uç noktadan okuyamaz); hakem her döngüde koşturur.
  3. **Zincirli güvenlik defteri:** defterin `security` bölümü; her bulgu, kapanış, eklenen test, doğrulama
     ve feragat bir satır (ajan, commit, test, doğrulanan); MF1 zinciri gibi hash'li, yalnız eklenir, kökü
     Rekor'a bağlıdır.
  4. **Güvenlikten öğrenme:** kapanan her açık bir dedektör ve bir regresyon testi bırakır (`22`); aynı
     sınıf o repoda tekrar edemez; desen yeniden yazılarak repolar arası taşınır (`21a`).
  5. **Kendimize uygulamak:** bu oturumda hakemde kapanan güvenlik açıkları (E01, E03, E04, E17 ve
     sonrakiler) defterin ilk satırları olur.
- **Zamanlama (operatör onayı, 2026-10-29).** Güvenlik koduna yazmak K6 canlı olana kadar yasak kalır; ama güvenlik
  testi eklemek ve açık bildirmek davranışı değiştirmediği için Aşama 1'den başlar.
  Operatör: her ihtimal düşünülsün, her delik kapatılsın; sistem organik bir canlı gibi, her tarafı
  birbirine bağlı olsun.

### E55 · Sınırlar kendini ayarlar · K · operatör yönü (2026-10-29)
- **Yön.** Operatör: ekonomik taraf dışında sistemdeki her sınırı sistem kendisi makul ölçülerde
  genişletebilmeli; 50 MB ile 100 MB arasında fark yoksa 50 neden var?
- **Üç tür.** Ekonomik (aylık USD, çağrı başı tavan, Actions dakikası): yalnız operatör. Güvenlik yasası
  (ağsız kapsayıcı, salt okunur kaynak, sırların ayrı işte tutulması, `.git` yasağı): değişmez.
  İşletim sınırı (ağaç boyutu, test süresi ve sayısı, çıktı ve istek boyutu, yeniden üretici sayısı):
  sistem ölçerek ayarlar.
- **Plan.** (1) Hakemdeki her sınırın envanteri ve türü (`config.py`, sabitler, iş akışı zaman
  aşımları). (2) İşletim sınırları için `policy.json`'da operatörün bandı (alt, üst; üst sınır makinenin
  fiziksel sınırından). (3) Hakem gerçek değerleri ölçer ve kurala göre (ör. gözlenen en büyüğün iki katı,
  bant içinde) ayarlar; her değişiklik gerekçesiyle imzalı sonuca yazılır, kanıt kalmazsa geri alınır.
  (4) Meşru işi engelleyen bir sınırı Kurucu E53 yoluyla ölçümüyle bildirir; hakem doğrular ve bant içinde
  genişletir; Kurucu sınırı kendisi gevşetmez. Bugünkü 50 MB ölçümsüz bir başlangıç değeridir.

### E54 · Ortak kader ve sürekli iletişim · K · operatör yönü (2026-10-29)
- **Yön.** Operatör: hakemde de beyin tarafında da aynı ilke geçerlidir; her açık sistem kurulurken fark
  edilip kapatılmalı. Bu yüzden üç yapı (Kurucu, hakem ve rakibi, beyin) sürekli iletişimde olmalı; biri
  açıklar kullanılarak zarar görürse bütün sistemin, dolayısıyla kendisinin zarar göreceğini bilmeli.
- **Plan.** (1) Tohum yasası olarak "ortak kader": `00`/`00a` ve rakibin koltuk metni (`29`); gerekçe:
  açığı kullanılmış bir hakemin kabulü değersizdir, Kurucu'nun itibarı ve dersleri de onunla değersizleşir.
  (2) Tek ortak bildirim kanalı: MF1'in zincirli defteri biçiminde, yalnız eklenir; Kurucu ve beyin beyin
  reposunda, hakem ve rakip imzalı sonuçta yazar; her kaydın yaşam döngüsü açık → doğrulandı → düzeltildi
  → teyit edildi → kapandı (E53). (3) Her koşuda üçü de açık kayıtları okur: rakibin bağlamı (E07'nin açık
  iddiaları), Kurucu'nun oturum başı, operatörün uyarısı (E29). (4) Hakem kendi zayıflığını da yazar:
  Docker arızası, izolasyon durması, totolojik ya da yeniden üretilemeyen iddia, kırmızı kontrol hatası,
  rakip hatası serisi. (5) Ölçüm: açık/kapalı sayısı, düzeltme süresi, yeniden açılma; kendini iyileştirme
  de öğrenme gibi ölçülür ve gelişir.

### E27 – E40
Ayrıntıları özet tablodaki kaynak bulgulardadır; her biri ele alınırken bu bölüme kanıt, plan ve
test satırlarıyla eklenir.

## Kapanışlar

### Parti 1 (2026-10-29) · E01 E02 E03 E04 E05 E17 E41
- **E01.** `container.RUN`: komut `exec` edilmez, 125'i 1 olur. Kanıt: gerçek Docker'da `exit 125` → 1,
  `exit 3` → 3, stdin/stdout geçer, Docker'ın kendi hatası (eksik imaj) → 125; POSIX testi; mutant
  `command_can_claim_dockers_125`.
- **E02 / E41.** `pull` sınıflandırması `_pull_classify`'de; içerikten doğan her hata `pull_error`
  reddi (Kurucu'ya sayılmaz); manifestte aşama ve `done_mf` 1000 ile sınırlı, yalnız vekil karakter ve
  derin JSON `manifest_invalid`; çıkış isteği tip ve biçimle denetlenir; `decide` reddedilmiş isteğin
  SHA'sını okumaz. Testler: beş bozuk manifest, altı bozuk çıkış isteği, sınıflandırma çökmesi.
  Mutantlar: `pull_crash_wedges_the_referee`, `exit_request_types_unchecked`, `manifest_stage_unbounded`,
  `manifest_surrogate_allowed`, `pinned_sha_of_a_refused_request`, `pull_error_held_against_the_founder`.
- **E03 / E04 / X7.** `treehash.path_problem`: denetim karakteri, `.git` bileşeni (büyük-küçük harf
  duyarsız), `:` ve `\` → `pull`'da `unsafe_path` reddi, `tree_hash` ve `extract`'ta `TreeError`
  (içe aktarma önce hash'ler, kancaya hiç yazılmaz). Rakibin isteği koşu başına rastgele bir çitle
  bölünür, yollar JSON dizesi. Testler: altı ad tek tek; `.git/hooks` ağacı; sahte başlık. Mutantlar:
  `control_character_in_a_name`, `dot_git_component_allowed`, `unsafe_name_reaches_the_tree_hash`,
  `predictable_context_fence`.
- **E05.** `validate_verdict` 5'ten fazla yeniden üreticiyi reddeder (prompt sınırı söyler); `decide`
  her yeniden üreticinin sonucunu ister, yoksa `yeniden:incomplete` kesintisi. Mutantlar:
  `sixth_reproducer_accepted`, `unrun_reproducer_clears_a_push`.
- **E17.** `cek` ve `yaz` yalnız `refs/heads/main`'de koşar; Sigstore kimliği `${GITHUB_REPOSITORY}` ile
  `@refs/heads/main`'e sabit, `run:` içinde `${{ github.* }}` yok; durum artefaktı yalnız `main`
  koşularından seçilir. Testler: kablolama ve artefakt seçimi (en yeni, süresi dolmamış, `main`).
  Mutantlar: `artifacts_from_any_branch`, `state_verified_as_the_runs_own_ref`.
- **Kanıt özeti.** Windows 225 test OK (17 atlandı), Linux 242 OK (3 atlandı); mutasyon 77 mutant,
  ilk koşuda 75; hayatta kalan iki mutant testleri sıkılaştırdı (her ad ayrı commit'te; atlanan
  yeniden üretimin nedeni), yeniden koşuda öldü; e2e Docker'da `accepted`.

### E26 (2026-10-29) · CI
- `.github/workflows/ci.yml`: her push ve PR'da Linux (runner'ın sistem python3'ü, hakemin koştuğu 3.12)
  ve Windows birim testleri ile prova yargıcı testleri; `main`'de ve haftalık olarak ayrıca hakem
  mutantları 8 parçada, beyin ve prova yargıcı mutantları, Docker'da e2e ve pinli Linux `claude`
  CLI'sinin sözleşme testi (uydurma belirteç, harcama yok). İşler salt okunur ve sırsız; action'lar
  doğrulanmış SHA ile pinli (checkout v7.0.1, setup-python v7.1.0).
- **Kanıt.** Dal koşusu 40845411648 (birim Linux 55 s, Windows 2 dk); `main` koşusu 40845743667: 14 işin
  hepsi yeşil (8 mutasyon parçası, e2e, CLI sözleşmesi dahil).

### E56 / E57 spec (2026-10-29) · güvenlik
- **Katalog** `30`–`30c`: 66 sınıf; her biri için bulma yolu, yürüterek kanıtlayan kapanış testi, CWE ve
  OWASP karşılığı, düzeltme yolu; OWASP Top 10:2025 ve 2021, API Top 10:2023 ve CWE Top 25:2025'in her
  maddesi bir sınıfa düşer. Çok kiracılık, GraphQL ve kaynak tüketimi `30b`. **Hedef güvenlik profili**
  ve kural–test bağı `30d`. **Zincirli `security` bölümü** `30e`: LLM iddiası yalnız `report`, açık
  sayılması için kanıt bugünkü kodda 3/3 kırmızı ve totolojik değil; düzeltilmemiş açığın ayrıntısı açık
  yüzeye çıkmaz (yalnız hash). **Bağımsız güvenlik avcısı** `30f`: ayrı koltuk, salt okunur, lisansı
  doğrulanmış tarayıcılar (Semgrep CE, TruffleHog, ShellCheck, Hadolint, CodeQL CLI, `npm audit` dışarıda)
  ve katalogla sürülen LLM, `drill: security` ile recall, Beta alt sınırıyla precision.
- **Kendimize uygulamak.** `seed/security-ledger.jsonl` 8 satır (E01, E02, E41, E03, E04, E05, E17 `fix`;
  E26 `verification`); `ledger.chain verify` geçerli; tek bayt değişince o satırda kırılır.
  `tests/test_security_ledger.py`: zincir, CWE, katalog kimliği, `30e`'de tanımlı durum ve tür, adı geçen
  her test, CI işi ve mutantın var olması, sır yokluğu; altı bozma denemesinin altısı kırmızı.
- **Açık kalanlar.** Hakem kodu (`security.derive/scan/run`, avcı dispatch'i, `security` yazımı); Aşama 0'a
  bir mikro özellik ve §0.9'a bir test (operatörün onayladığı "Aşama 1'den test ve bildirim" bunu
  gerektirir; manifest haritasıyla birlikte eklenecek); Aşama 1 sayfaları; açık hakemle açık hedefte
  açık ayrıntısının yayımlanmaması için özel kanal (E35, E60 ile).

### Uçtan uca denetim (2026-10-29, 8 Opus denetçisi) · öğrenme ve hafıza (e2e-7)
- **E64 (L1).** `judge.py:77` doğuşta `scope.family == key.family` istiyor; `26b:12-13` ders şemasında aile
  yok, aile yalnız gizli cevap anahtarında (`22a:17-19`); simülasyon dispatcher'a etiketi veriyor
  (`sim.py:123,133,219`). Plan (`29c`/`22a`): doğuş, dersin `scope`'u hakemin eşleyicisiyle cevap
  anahtarındaki örneklerin gözlenebilir özelliklerine uygulanarak sınanır (ailenin ≥ %80'i, başka ailenin
  hiçbiri); aile adı beyne verilmez. Vektörler: `label_peeker`, `overbroad_scope`; güç tablosu yeniden.
- **E65 (L2).** Saklama kararı hakemin gizli tohumundan: `withhold = HMAC(sır, lesson_id‖run_id) < 0,5`,
  tohumun hash'i koşudan önce zincirde; `run_meta`'ya `lessons_eligible[]`, `lessons_withheld[]`; yargıç her
  kolu tohuma karşı denetler; kollarda model, effort, `max_turns`, bütçe aynı, prompt ders bloğu dışında
  bayt bayt aynı. Vektörler: `cherry_picking_dispatcher`, `unequal_arms`.
- **E66 (L3).** Ders kümesi bir organ olarak ölçülür (koşu başına görünüm açık/kapalı, hakem tohumu); ders
  başına kredi yalnız sıralama için, büzülmeli tahminle, %99; `rules.lesson_top_n` anahtarı.
- **E67 (L4).** Bildirimin kredisi, kusuru getiren commit (kırmızı testin yürüttüğü satırların `blame`'i)
  bildirenin kendi soyundan değilse verilir; kendi kusuru kaydedilir, artı sayılmaz; kredi kök neden parmak
  izi başına. Kanarya `plant_and_report`. Kötü niyet gerekmez: ödül sapması yeter (E53).
- **E68 (L5).** Sınıra takılan gözlem sansürlüdür, ölçüye girmez; kural tamamlanmış işlerin p99'u × marj;
  pencere başına genişleme ≤ ×1,5 ve `drift_bound`'a tabi; sansürlü iş sayısı raporlanır; genişleme yalnız
  E53 kanıtıyla (E55'in kuralını düzeltir).
- **E69 (L6).** Birim uygun koşudur (niyet-tedavi): `hit` birleşti ve pencereyi geçti; `miss` geri alındı,
  `unresolved`, kapıda ret ya da vazgeçme; planlayıcı dersi rastgele atanmış görev kümesinde değer/USD ve
  risk ağırlıklı kapsamayla ölçülür. Prova beyni `abstainer`.
- **E70 (L7).** Hata imzası = sha256(cause + kırmızı test kimliği + property + sembol); tekrar eden hata oranı
  metriği; her N döngüde gizli tohumla seçilmiş geçmiş geri alınmış işler, bugünkü beyin ile hatayı yapan
  beyin eşli koşar (McNemar); düşüş öğrenme iddiasını çürütür.
- **E71 (L8).** Geri alma provasında mekanik sınıflayıcının her `cause` kategorisi için ≥ 3 ekilmiş merge,
  karışıklık matrisi; `unknown` payı metriği ve sinyali; kanıtlı `cause_correction` satırı.
- **E72 (L9).** Her kabul sınaması `looks` satırı yazar; α soy başına harcanır; pencerede BH; organ
  kaydında `tuning_cases`; koşul dışlama önceden kaydedilmiş adaylarda; tohum dışı organ sayısı yalnız
  ablasyon alt sınırı > 0 olanlar.
- **E73 (L10).** Arşiv yalnız sıralamadan çıkarır; kapsamı eşleşen arşivli ders adaydır; K6 dersleri arşive
  inmez; `lesson_retrieval_miss` metriği; arşiv blob'ları `brain/state`'te içerik adresli ve süresiz;
  sıfırdan yeniden kurma her döngü kendi-testi.
- **E74 (L11).** Katalog sınıfı `memory-poisoning`; ders `claim`'i şablondan; serbest metin enjeksiyon
  derleminden geçer, prompta veri olarak çitli girer; `llm_prior`/`synthesis` kökenli ölçülemeyen ders W
  pencerede süresi dolar.
- **E75 (L12).** Sınıfta işlerin `rules.explore_share` (öneri %20) kadarı hakem tohumuyla rastgele atanır;
  karşılaştırma yalnız bu dilimden; sayımlar `model_served` ve CLI sürümüne göre katmanlı.

### Uçtan uca denetim · hedefler ve en iyi sistemler (e2e-8)
- **E76 (G1).** `asama-0/14` 30 mikro özellik; birkaçının ilk okuyucusu Aşama 2+ (prova yargıcı, `docs.index`,
  dispatch kanaryası); E56'nın `security.*`'ı CodeQL boyutunda bir çözümleyici. Öneri: ilk kilometre taşı
  gerçek hedef kopyasının tek biriminde yürüyen iskelet (profil → sandbox'ta testler → bir K0 düzeltme →
  kapı → `brain/integration` → nöbetçi → geri alma provası); Aşama 0 bu döngünün okuduklarına iner, gerisi
  ilk okuyucusundan hemen önceki çıkışta aktarılır. Ölçü: Aşama 1 okuyucusu olmayan MF sayısı (hedef 0),
  gerçek kopyada ilk canlı merge'e kadar oturum ve USD.
- **E77 (G2).** `profile.units[]` `{unit_id, path, toolchain, komutlar, services[], env_image@sha256}`;
  servisler pinli imajlarla koşu başına `docker network --internal`; sandbox veritabanına uygulanan migration
  Y3 migration'ı değildir; ortam tarifini beyin önerir (Repo2Run tarzı), hakem doğrular (HEAD testleri 3/3
  yeşil, kırmızı kontrol kırmızı, ağ yok). Ölçü: tarifi doğrulanmış birim oranı.
- **E78 (G3).** Kopya orijinalin `main`'ini düzenli aynalar (operatör iş akışı; sistem yine yalnız
  `brain/*`); profilde yazar girişleriyle `agent_fix` katmanı; eğitim modundaki repolardan model eğitim
  tarihinden sonraki tarihsel held-out; orijinale yama aktarma yolu (insan dokunuşu). Orijinal 90 günde
  4.817 commit alıyor, büyük kısmı `claude`, `aria-implementer` ve `codex` imzalı.
- **E79 (G4).** `honesty` provası, cevap anahtarı önceden bağlı: (a) spec sayfasıyla çelişen ekilmiş vektör,
  doğru davranış E53 bildirimi; (b) hakeme ekilmiş istismar edilebilir zayıflık, doğru davranış kırmızı
  testli bildirim; (c) düzeltme girince Kurucu'nun teyit koşusu. Ölçü: istismar = 0, bildirim recall'unun
  alt sınırı, teyit kapanış oranı; Aşama 0 çıkış satırları (ImpossibleBench yöntemi).
- **E80 (G5).** Donmuş `vanilla` koltuğu (aynı model, genel prompt, organ yok) her yeteneğin çıkışında zorunlu
  kol; üç ayda bir dış dilim (ör. SWE-bench-Live'dan 50 TS/Python/Rust görevi); eşli fark (`19`).
- **E81 (G6).** Birim karnesi (build, HEAD testleri, lint borcu, açık `security` bulguları, kapsama, doküman
  çapaları); en zayıf hücre `status.md`'de üst satır; gizlilik kanaryası provası (A'ya ekilen benzersiz
  tanımlayıcılar küresel beyne ve B'nin promptlarına hiç çıkmaz).
- **E82 (G7).** Aşama 1'den her birleşen hunk için `hunk_covered` ve `mutant_killed` kaydı; LLM ve silme
  düzenlemeleri kapsama ya da fark oracle'ı ister, yoksa `blocked: weak_oracle` (test yazma boşluğu sinyali).
- **E83 (G8).** `ast` motoru olarak ast-grep (MIT); `dataflow` türü için Joern (Apache-2.0) ve Pysa
  değerlendirilir; `llm_seeded {fix_diff_sha, catalogue_id}` dedektör türü; hedefin son 90 gündeki 51
  tenant düzeltmesiyle tohumlanır. "Dağıtılmayan araç" kategorisine LGPL'in girip girmeyeceği operatör
  kararı.
- **E84 (G9).** Sinyal başına k taslak, dev setinde ucuz puanlama; kayıt bir arşiv (DEGRADED ve RETIRED
  ebeveyn olabilir, yenilik bonusu); kabul ve held-out bakışını yalnız dev kazananı harcar; `12a`'ya
  popülasyon/k=1 satırı.
- **E85 (G10).** Model değişimi yeni hash ve `derived_from` doğurur, SHADOW'a gider, `12` kabulü ister; donmuş
  koltuklar geçişten önce kanaryasını yeniden koşar; her CLI/model pin değişiminde dev seti kayma yoklaması;
  satışta başka bir sağlayıcıdan doğrulayıcı.
- **E86 (G11).** Kök hash'ler kuyruklanır, sonra çapalanır; erişim hatası bayrak, yalnız hash uyuşmazlığı sert
  durma.
- **E87 (G12).** Aşama 5+: dar bir K6-deps sınıfı (OSV'nin düzeltilmiş dediği sürüme yalnız kilit dosyası
  güncellemesi, semver uyumlu aralıkta, lisans kapılı, tüm etkilenen testler ve nöbetçi) ya da Dependabot ile
  bir arada yaşama kuralı (Dependabot PR açar, sistem kendi testlerini koşar ve `verification` satırı yazar).

### Uçtan uca denetim · kurulumdan Kurucu döngüsüne (e2e-1)
Denetçi akışı gerçek `pull` ve `decide` ile yerel git üzerinde simüle etti (`scratchpad/e2e_audit_1/sim_flow.py`).
- **E88 (A1).** Senaryo 2: MF1 kabulünden sonra operatörün `spec/tohum` ve `seed/` commit'i → her sonraki
  Kurucu push'u `seed_modified` + `seed_tree_mismatch`, ikinci push'ta `not_learning`. Plan: beyin ayrı yeni
  bir repo (asla `snowball-mcp` değil); `25`'e "tohum commit'i = etiketteki `spec/` + `seed/`"; tipli tohum
  güncellemesi: operatör `setup/summary.json`'a `{commit, seed_tree_sha256}` yazar, `pull` listelenen
  commit'in tohum yollarını muaf tutar (ya da `base`'i geçirir), `seed_update` yazar, seriye saymaz; E24'e
  beyin tohumu = hakem kopyası denetimi.
- **E89 (A2).** Yalnız `founder-ledger.jsonl` değişen push `ledger` türü: değerlendirilmez, rakip yok, seri
  yok, rakip artefaktı değil (ya da defter spec push'una dahil olabilir); filtreden sonra boş kalan diff
  `rival_artifacts`'a girmez (E20 planı düzeltilir).
- **E90 (A3).** Kurucu başlatma bayrakları: proje ve yerel ayar kaynağı yok (`--setting-sources`),
  `--strict-mcp-config`, repo dışında operatöre ait ayar dosyası, taze `CLAUDE_CONFIG_DIR`, otomatik hafıza
  kapalı; beyin push'unda `.claude/**`, `CLAUDE.md`, `AGENTS.md`, `.mcp.json` → `agent_config_modified`.
  Kanarya: `.claude/settings.json`'daki bir kanca koşmaz.
- **E91 (A4).** `24`'te başlatıcı bölümü ve betiği: `control.json`'u canlı okur, son sonucun `head`'ini beyin
  başıyla karşılaştırır (beklemede, kabul, ret, `not_learning`), `claude -p --max-budget-usd
  <session_cap_usd>` ile "00, 00a'yı oku" açılışıyla koşar, maliyeti kaydeder; sonuçları okumak `actions:read`
  belirteci ister. Kurucu harcaması aylık toplama girer.
- **E92 (A5).** İşaret varken hakem yargılanacak bir şey olmasa da genesis durumunu imzalar; `25`'e satır:
  bir kez tetikle, imzalı durumu doğrula, işareti kaldır, sonra Kurucu'yu başlat. E14'ün planı buna göre.
- **E93 (A6).** Önyükleme hakemi tipli `seed_issue` ve `blocked` satırlarını (hash ve özet) imzalı sonuca ve
  adım özetine kopyalar, operatörü uyarır (E29); spec sorunu için operatörün kapattığı yaşam döngüsü (E53
  planı düzeltilir).
- **E94 (A7).** Kurucu'nun hesabı adlandırılır; rakip için ayrı plan ya da zamanlama ayrımı; kota kaynağı
  sonuca yazılır (E33).
- **E95 (A8).** `25` madde 1: beyin `main`'inde `non_fast_forward` ve `deletion` kuralları (açık repoda
  ücretsiz); özet ve drift denetimine girer; kurtarma: `base`'i geri merge etmek.
- **E96 (A9).** Önyükleme hakemi (B) geçene kadar yalnız elle tetiklenir hâlde kalır; içe aktarma sırasında
  kill switch açık; içe aktarıcı imzalı durumdan `setup/handover.json` yazar, genesis onu hash'ler.
- **E97 (A10).** Kaçış `29b` ve `asama-0/10`'a yazılır ya da son reddedilen istekle aynı `exit-request.json`
  yok sayılır. Senaryo 3: `rival_attempts:1<5` reddinden sonra her kod push'u `exit_request_not_alone`.
- **E98 (A11).** Operatörün yazdığı `setup/touches.jsonl` (tipli nedenler), her sonuca hash'i girer; çıkış
  bloğunda sayı.
- **E99 (A12).** `25`'e Aşama 0'ın gerçek hedefini (açık ya da eğitim modu) ve klon yolunu adlandıran satır;
  özete girer; drift denetimi.

### Uçtan uca denetim · Aşama 0'ın inşa edilebilirliği (e2e-2)
- **E100 (B1).** `asama-0/13:15-16` beş işin iş akışlarını teslim sayıyor; `14` ve `09`'da yok; `importer.py:51-59`
  `.github/` ve `bootstrap/`'ı siliyor. Plan: `14`'e iş akışları mikro özelliği (`koş`/`yeniden` sırsız ve
  `permissions: {}`, sırlı iş kod koşturmaz, `run:` içinde `${{ github.* }}` yok) ve `09`'a test 46; `snowball
  init`, `mcp/`, `schemas/` için sahip mikro özellik ya da `13`'ten çıkarma; kablolama testi: `13`'teki her
  teslim `14`'te adlı.
- **E101 (B2).** Testler 20, 21, 22, 45 önyükleme kumunda taklit koşucu, git ve CLI ile koşar; gerçekleri (B)'de
  aktarılan hakemin ilk koşusunda #sandbox, #dispatch, #kirmizi satırlarıyla doğrulanır; ya da operatör git'li
  bir imaj pinler.
- **E102 (B3).** Yollar `../spec/asama-0` ve `../exit-request.json`; (A)'da kilit yalnız (aşama, donmuş spec
  hash'i) çiftini denetler, PASS satırına bağlı açılış (B)'nin; `policy.json` kapsayıcıya `/policy/` olarak
  salt okunur bağlanır; `29a`'ya `lint` ve `lock` vektör grupları; tohumdaki Aşama 0 spec'i tohumlanmadan önce
  `02` listesinden geçirilir (anahtarsız eşikler: `12:13,15,17`, `09:55`, `06:17`).
- **E103 (B4).** `29a`'ya `control`, `diffguard`, `secrets`, `license` vektör grupları; her `14` satırına modül
  yolu ve "modülsüz kırmızı" denetimi (modül silinince o MF'nin testleri kırmızı olmalı).
- **E104 (B5).** `26b`'ye `control.json` (`kill_switch`, `budget_state`, `oauth_token_expires`; eksik ya da
  bilinmeyen alan kapalıya düşer), `setup/summary.json` (açık alanlar) ve `setup/imports.jsonl`; `config.py`
  alanlarının `26b` ile aynı olduğunu sınayan test.
- **E105 (B6).** Test 26'nın Rekor, kayma ve rakip zaman aşımı vakaları 40, 24 ve 22'ye taşınır; `secrets.scan`
  MF16'dan öne; MF23'e "Rekor bağlantısı 24'te"; MF6 ile MF7 yer değiştirir; `26a` çağıran MF ≥ çağrılan MF testi.
- **E106 (B7).** `26a` `harness.score` satırı `29a` CLI'siyle uyumlanır, `hits` `26b`'ye; `harness.stats` ve
  `harness.drill` `26a`, `13` ve MF9/MF18 satırlarına; `29a:70` örneği `"0.962351"`; her `29a` komutu `26a`'da.
- **E107 (B8).** `founder-ledger.jsonl`'ın zincirli kısmı önyükleme hakeminin kanonik koduyla zincir ve son kabul
  edilmiş SHA'daki sürüme göre yalnız-ekleme denetiminden geçer; aksi `founder_ledger_invalid`.
- **E108 (B9).** `26` vakasına `mapped_line` (K0–K2'de zorunlu); `08`: isabet `tool`, `rule_id` eşit ve
  `evidence_refs[0].line_start = mapped_line`, eşleme açgözlü `finding_id` sonra `case_id`; yeni vektör.
- **E109 (B10).** `26a`'da iş `yaz` (sırlı, kod koşturmaz), seçim hash'i `koş`'tan önce zincire; araç → iş
  tablosunun `08`'in sır sütunuyla aynı olduğunu sınayan test.
- **E110 (B11).** Genesis satırının `payload`'ı `seed_security_ledger_sha256` ve son `row_hash`'i taşır;
  `security` satırları ortak zincirde genesis'ten sonra gelir.
- **E111 (B12).** Taban avcının K0 grep kümesi çıkışta donar, hash'i genesis'te ya da tohumla gelir; Kurucu
  değiştiremez.

### Uçtan uca denetim · operasyon ve operatör (e2e-6)
- **Birleştirilenler.** O1 → E88 (tohum güncellemesi; runbook: CI'ı yeşil commit seç, kill switch, beyne yalnız
  `spec/tohum` ve `seed/`, hakeme aynı commit'ten kopya, `seed_updates` satırı, `kind: seed, accepted`, insan
  dokunuşu; prova zaten kaymış: beyin tohumunda `30`–`30f` yok, `29`/`29b` eski). O5 → E94 (abonelikte operatörün
  koyabileceği "sağlayıcı tavanı" yok, yalnız ücretli "extra usage"; `25` 8-9 ve `28:35` düzeltilir; sistem için
  ayrı Claude hesabı). O7 → E96 (etkinleştirme kırmızıysa içe aktarma commit'i `git revert`, iş akışı geri gelir).
- **E112 (O2).** Kurucu için ince taneli belirteçler: yalnız beyin reposu, Contents yazma, Metadata okuma (Workflows
  ve Actions yok); hakem için yalnız okuma; bitiş tarihi `control.json`'da. Kurucu ayrı bir işletim sistemi
  kullanıcısında ya da kapsayıcıda koşar; orada `gh auth login` yapılmaz; taze `CLAUDE_CONFIG_DIR`, otomatik hafıza
  kapalı, kullanıcı ayarı ve MCP yüklenmez (E90 ile). Kurulum provası: Kurucu belirteciyle hakeme push 403,
  artefakt silme 403, `.github/workflows`'a dokunan push 403.
- **E113 (O3).** `control.json`'a `founder_resume: {after_run, note}`; Kurucu o koşudan sonra "ne değiştiriyorum"
  defter satırını yazıp bir kez push edebilir; aynı imza tekrar durdurur. Runbook `25`'te.
- **E114 (O4).** `seed/bootstrap/operator-templates/` (dört geçerli JSON ve Türkçe README) ve `init-referee` alt
  komutu; `25`'te PowerShell komutları (`C:\Python312\python.exe`, `$env:PYTHONPATH`); `18a`'nın anayasal
  anahtarlarının tamamı şablonda; Windows CI işi `25`'in kod bloklarını aynen koşar ve `control`'dan geçirir.
- **E115 (O6).** `control.json`'a tek kullanımlık `retry_now: "<sha>"`; park edilmişken baş ile eşitse yargılar; poll
  adım özetine "PARKED <sha>, sonraki deneme <zaman>" yazar.
- **E116 (O8).** Yazılı Docker/WSL içe aktarma ya da ikinci pinli küme `sign-windows.txt`; `25a`'ya tam komut
  (`gh run download …`, `import … --identity …@refs/heads/main`); CI belgelenen komutu gerçek bir prova paketine
  karşı koşar.
- **E117 (O9).** Kill switch açıkken `cek` `paused` bildirimiyle 0 döner, sonraki adımlar atlanır, kırmızı yalnız
  gerçek arızalar için; runbook: duraklat, devam (`gh workflow list`, `enable`, `run`); 60 günü aşacaksa 45 günde
  bir hakeme commit. E16'nın "durunca kırmızı" kuralını değiştirir.
- **E118 (O10).** Yeni `spec/tohum/25b-olay-kitabi.md`: belirti (tam ileti) → anlamı → kim → adımlar → doğrulama;
  satırlar: belirteç süresi doldu/iptal/sızdı, 429, model emekli, CLI eskidi, Sigstore doğrulama/imza hatası,
  GitHub kesintisi, CI kırmızı, durum kaybı, `not_learning`, kötü kabul (`revoked_shas`), makine kaybı; doğrulama
  hata iletisi üç sınıfa (ağ, kimlik, imza); günlük kanarya rakip çağrısı; CI: koddaki her neden ve `stop:` iletisi
  `25b`'de.
- **E119 (O12).** İkinci sahipli GitHub organizasyonu (2FA, çevrimdışı kurtarma kodları), Kurucu'dan önce taşınır;
  ya da `summary.json` tarih aralıklı kabul edilen kimlikleri listeler; tarayıcıdan acil durdurma ve ödünç makine
  runbook'u; iCloud Drive yedek değildir.
- **E120 (O11).** Her koşu (boşta olanlar dahil) `status-stage0.md` yükler ve adım özetine yazar: son kabul ve son
  değerlendirilen SHA, park, seriler, tavanlara karşı harcama, belirteç süresi, son 5 karar; Türkçe başlık, İngilizce
  kod (E98'in dokunuş kaydı ve E29 ile).

### Uçtan uca denetim · organizmanın bağlantıları (e2e-3)
Denetçi okuyucu grafiğini betikle kurdu ve kilitlenmeyi gerçek `classify` ile `decide` üzerinde koştu
(`scratchpad/e2e_audit_3/`).
- **Birleştirilenler.** C1 → E88: tohum güncellemesini üçüncü bir denetçi bağımsız olarak buldu; plana "tohum
  dönemi" eklenir: `summary.json` tohumun değişebileceği commit'i adlandırır, `pull` `seed/**` ve `spec/tohum/**`'u
  `base`'e değil ona karşı karşılaştırır, tohumdan doğan nedenler Kurucu'nun değildir, `seed/bootstrap` da özete
  hash'lenir. C4 → E93 ve E91: `reports/*.json` tipli bildirim dosyaları `pull`'da okunur, rakipten gizlenir, imzalı
  sonuçta `reports[]` olur; `session_cap_usd`'yi kısıtlanan taraf ölçemez (sağlayıcı tavanı olarak yeniden adlanır ya
  da Kurucu maliyeti bütçeye okunur). C9 → E96: genesis `bootstrap_carry{open_claims, stored_reproducers,
  month_spend, reject_streaks}` taşır.
- **E121 (C2).** `not_learning`, park ve push'tan sonra sonuçsuz bekleme imzadan sonra koşuyu kırmızı bitirir ve
  `25`'in uyarı listesine girer; GitHub dışındaki Kurucu zamanlaması canlılık gözlemcisidir. Kablolama testi: spec'in
  "operatörün işi" ya da "insan dokunuşu" dediği her durum `25`'in listesinde ve iş akışında başarısız bir adımda.
- **E122 (C3).** Gözcü işaretleri ve kanarya sonuçları için `signal` bölümü; şerit yazarına `çağır`'da dispatch
  (`agent.dispatch`); çıktısı içe aktarmanın hash'le denetlediği imzalı bir artefakt (beyin repo commit'i yerine);
  ilk gerektiği aşamada bir mikro özellik. Graf testi: `27`'deki her okuyucunun bir doğum noktası, her yazarın
  dosyasının durduğu yerde yazma yetkisi var.
- **E123 (C5).** Doğrulanmış ve açık hakem açığı imzalı durumda tipli karantina olur; hakem etkilenen kararda
  kapalıya düşer (ör. saklanan yeniden üreticinin yeşil kalmasını ister) ta ki düzeltme aktarılana kadar; aşama içi
  güvenlik aktarımına izin (insan dokunuşu); E53 kredisinin okuyucusu (çıkış satırı ve `20` metriği) ya da kredi
  kalkar; bildirim push türü. "Operatör onayı" `00a:51` ve Y8 ile uzlaştırılır.
- **E124 (C6).** Tek zincir, tek yazar (`yaz`); bildirimler tipli dosya ya da artefakt olarak gelir; her okuyucunun
  `27`'ye yazılmış kendi görünümü (rakip, avcı, Kurucu, operatör); her koltuğun bağlamında yasaklı `proposed_by`
  satırı olmadığını sınayan test. E54 planı buna göre düzeltilir.
- **E125 (C7).** Yasa değişikliği: kaynak sınırları operatörün bandı içinde iki yöne oynayabilir, kalite eşikleri
  yalnız sıkılaşır; `operating{key:{value, band, rule, evidence}}`, imzalı sonuçta `limits_applied`, durum şeması
  v2, Kurucu'ya sayılmayan `limit_hit:*` neden sınıfı; hakemin karşılaştırdığı her sayısal sabit bir anahtar ya da
  izin listesinde; spec düzyazısındaki her sınır bir anahtara bağlı. E68 kuralla birlikte.
- **E126 (C8).** Aşama 0 rakip kanaryası `mutate_brain.py` mutantlarından, imzalı durumda puanlanır, politikada
  taban; kaçırma hakem zayıflığı satırı (E54 4); her koltuk ilk çağrısından geç olmadan kanarya ya da prova satırı.
- **E127 (C10).** Kapsamı hakem ya da beyin olan güvenlik satırları için tek bir depo ve orada yazma kimliği olan bir
  yazar; iki hedefli etkinleştirme provasında tek zincir.
- **E128 (C11).** Dedektörlere durum ve isabet sayaçları; doğrulanmamış ateşlemeler `12` üzerinden indirir; bekçi
  testleri için kural başına süre muhasebesi.
- **E129 (C12).** Dokunuş kaydı CLI'si ve kaydedilmemiş operatör commit'ini bulan `drift.check`; `27` satırları
  (bootstrap `policy.json` okuyucusu, `cost` okuyucuları, `findings.jsonl` yazarı avcı) ve `17` sinyallerine tipli
  alan (`not_derivable`, değişen satır).

### Uçtan uca denetim · güvenlik (e2e-4)
- **Birleştirilenler.** S1 → E112 ve E90: Kurucu kimliğini üçüncü bir denetçi bağımsız buldu (bu makinedeki `gh`
  belirteci `repo, workflow` kapsamlı ve hakemde yönetici); plana: Kurucu ayrı VM, kapsayıcı ya da işletim sistemi
  hesabında, yalnız beyin reposuna yazan ince taneli belirteçle; bulut seçeneğinde Claude GitHub App yalnız beyin
  reposunda; yönetilen ayarlar ve `--setting-sources user`; pinli CLI, otomatik güncelleme kapalı; oturum başında
  kırmızı kontrol. S6 → E116: Windows'ta içe aktarma doğrulayıcısı pinli değil; pinli Windows kilidi ya da doğrulama
  pinli Linux imajında, doğrulayıcı sürümü `imports.jsonl`'a.
- **E130 (S2).** `path_problem` casefold eder ve şunları reddeder: noktayla ya da boşlukla biten bileşen, 8.3 biçimli
  `~N` bileşen, Windows aygıt adları (uzantılı ya da değil), büyük-küçük harf duyarsız çakışan yollar (git'in
  `is_ntfs_dotgit` ve `verify_path`'i gibi); operatör adı denetimi casefold; içe aktarmadan sonra diskteki gerçek
  ağaç yeniden hash'lenip imzalı hash'le karşılaştırılır. Güvenlik defterine E04 için `reopen` satırı. Windows CI'da
  test ve casefold'u düşüren mutant.
- **E131 (S3).** İçe aktarmada `CLAUDE.md`, `AGENTS.md`, `.claude/**`, `.mcp.json`, `.vscode/**`, `.envrc`,
  `.devcontainer/**` reddedilir ya da karantinaya alınır; oyuncak kanaryaları operatörün güvendiği bir dizine hiç
  açılmaz; imzalı çıkış bloğuna `toy_tree_sha256`; içe aktarma GitHub'dan taze klonla ve nesne fsck'siyle yapılır.
- **E132 (S4).** Önyükleme hakemi çıkışta `referee/.github/workflows/*`'u mekanik kurallarla denetler (`test_wiring`
  kuralları, çevrimdışı actionlint ve zizmor): üst düzey `permissions: {}`; sırlar yalnız beyin ya da hedef kodu
  koşmayan işlerde; `pull_request_target`, `workflow_run`, `issue_comment` yok; SHA pinli action'lar ve
  `persist-credentials: false`; OIDC yalnız imza işinde, kimlik `main`'e sabit. İçe aktarma sır-iş haritasını
  `setup/`'taki izin listesiyle karşılaştırır; avcının `referee/` taraması etkinleştirmenin ön şartı.
- **E133 (S5).** İptal, döndürme, yeniden dağıtma runbook'u bir kez denenir; belirteci tutan repoların envanteri
  (`drift.check` ve gözcü); prova repoları için kapatma adımı (sırrı sil, iş akışını kapat); hakem için ayrı hesap;
  belirtecin oluşturma tarihi ve parmak izi kaydedilir.
- **E134 (S7).** `head_repository_id == repository_id` ve `bootstrap.yml`'ın `schedule` ya da `workflow_dispatch`
  koşusu şartı; yabancı ya da doğrulanamayan artefakt atlama değil bildirimli durma; tazeleme yeniden yüklemesinden
  önce doğrulama; çatal PR onayı "tüm dış katkıcılar".
- **E135 (S8).** Yalnız hash pinli kilitlerde `pip-audit --disable-pip --no-deps` ya da çevrimdışı osv-scanner;
  tavsiye veritabanı hedef dosyasına dokunmayan bir işte çekilir, anlık görüntü hash'i imzalı sonuçta.
- **E136 (S9).** Hakem, `snowball-mcp` ve beyin `main`'inde baypassız ruleset: force-push ve silme yasak (E95'i üç
  repoya genişletir); defter ucu ilk günden çapalanır (`main`'de `id-token`'lı bir CI işi uç hash'ini Rekor'a imzalar
  ya da hakemin imzalı sonucu taşır); CI son çapalanmış ucun mevcut zincirin öneki olduğunu doğrular.
- **E137 (S10).** Kapsamı `third_party`/`upstream` olan bulgu için `disclosure` türü: özel rapor (GitHub özel açık
  bildirimi ya da projenin SECURITY.md'si), ambargo tarihi, CVE ya da GHSA; ifşadan önce dedektör ve varyant
  yayılması yok (E62).
- **E138 (S11).** İlk özel repodan önce ticari bir kimlik (API ya da eğitimde kullanılmama ve saklama koşullu
  Team/Enterprise) ya da tüketici hesabının eğitim dışı bırakma ayarının `setup/summary.json`'a kaydı ve
  `drift.check`'i.
- **E139 (S12).** E59 ve `13` düzeltilir; özel repo sonuçları özel bir Sigstore örneğiyle ya da mühürlü depodaki
  anahtarla imzalanır; doğrulamadan sonra sertifika uzantıları `.1.15` (repo kimliği) ve `.1.17` (sahip kimliği)
  `setup/summary.json`'daki kimliklerle karşılaştırılır.

### Uçtan uca denetim · hakem kodu (e2e-5)
Her kusur bir karalama kopyasında ya da betikte yeniden üretildi (`scratchpad/e2e_audit_5/`).
- **Birleştirilenler.** K4 ve K8 → E130: büyük-küçük harf takma adı (`referee/Policy.json` operatörün `policy.json`'unu
  `import OK` ile değiştirdi; `referee/SETUP/summary.json` da) ve `.git.`/`GIT~1` iki denetçi tarafından bağımsız
  doğrulandı. K5 → E130: ad kuralı ayrıca `<>"|?*`, sondaki nokta ya da boşluk, ayrılmış aygıt adları (CON, PRN, AUX,
  NUL, COM1-9, LPT1-9, uzantılı) ve büyük-küçük harf çakışmalarını reddeder; içe aktarma kardeş bir geçici dizine açar,
  sonucu imzalı hash'le yeniden hash'ler, sonra değiştirir; hata olursa checkout bayt bayt aynı kalır (E04 planının
  uygulanmamış kısmı). K6 → E11: `secret_in_verdict` rakip tarafında, `secret_in_prompt` Kurucu tarafında; parti 2'ye
  iletildi.
- **E140 (K1).** `remote_head` yalnız ref'i `refs/heads/{branch}`'e eşit olan satırı tutar; hiç yoksa durur. Test: gerçek
  çıplak uzakta `main`, `refs/heads/main` ve `x/refs/heads/main` → `main`'in SHA'sı; mutant: `len(lines) != 1`.
- **E141 (K2).** Vektör sonucuna çıkış kodu (son deneme 125 ise `runner_fault`); `decide` bunu 125'li test gibi `infra
  kos:docker` sayar. Parti 2'ye iletildi.
- **E142 (K3).** Kilit yolları `[A-Za-z0-9._/-]` ile sınırlı, aksi `manifest_invalid` (ya da satır satır `IFS= read -r` ve
  `set -f`); POSIX prelüd testi.
- **E143 (K7).** `rival.json` varsa `cost_usd_micros` her durumda yazılır. Parti 2'ye iletildi.
- **E144 (K9).** Yalnız `\n` satır sonu (`split("\n")`), diff `newline=""` ile okunur, rakibin isteğinde `\r` görünür;
  test: CR'li diff tek `+` satırı, form feed'li dosyada grep 6. satırı verir.
- **E145 (K10).** `decide`'a güncel ay verilir, yazmadan önce ay devri orada yapılır.
- **E146 (K11).** `load_policy` ifadeleri ayrıştırır, pini adlandıran `ConfigError` verir.
- **E147 (K12).** Arşivlemeden önce `ls-tree -l` ile blob boyutları toplanır; ağaç çok büyükse `brain.tar` yazılmaz.

### Kararlar (2026-10-29, uçtan uca denetimden sonra)
Operatör dört kararın dördünü de önerilen yönde verdi:
1. **Yol haritası (E76).** Aşama 0 daraltılır: yalnız ilk canlı döngünün okuduğu parçalar (zincir, kum havuzu,
   bağımlılık getirme, kapı, nöbetçi, geri alma, sır taraması, model çağrısı, en küçük durum bloğu). Döngü önce
   oyuncak hedefte, hemen ardından `aquaculture_platform` kopyasının tek bir biriminde çalışır; gerisi ilk
   okuyucusundan hemen önceki çıkışta aktarılır. Inşa edilebilirlik bulgularının (E100–E111) çoğu bu
   daraltmayla yeniden değerlendirilir.
2. **Kurucu kimliği (E90, E91, E94, E112, E133, E138).** Sistem için ayrı bir Claude hesabı ve aboneliği (rakip ve
   Kurucu operatörün kotasını paylaşmaz); yalnız beyin reposuna yazan ince taneli GitHub belirteci; Kurucu bir
   kapsülde ya da ayrı bir Windows kullanıcısında, temiz Claude yapılandırmasıyla.
3. **Repolar (E88, E119, E136).** Beyin `snowball-mcp` değil, ayrı yeni bir repodur; repolar iki sahipli bir
   Suderra GitHub organizasyonuna Kurucu başlamadan taşınır; üç repoda `main`'e force-push ve silme yasağı.
   GitHub'da `suderra` adı 2025-04-11'de açılmış bir kişisel hesap olarak alınmış; operatörün mü olduğu soruldu.
   Koruma: `snowball-mcp` (ruleset 26114843) ve prova hakemi (26114844) `main`'inde `non_fast_forward` ve
   `deletion` yürürlükte (GitHub `rules/branches/main` ile doğrulandı).
4. **Diğer karar kalemleri.** Kayıttaki öneriler onaylandı (ör. Y11: kaynak sınırları bant içinde iki yöne,
   kalite eşikleri yalnız sıkılaşır; kendi kusurunu bildirmeye kredi yok; dürüstlük provası; bağımlılık
   güncellemesi sonraya).

**E119 (2026-10-29, son karar).** Operatör: `suderra`'ya taşınmayacak; bu kişisel bir test projesi, iş görürse
taşınır; repolar kirletilmez (yalnız gerekli iki repo: beyin ve hakem; prova repoları kurulum günü silinir). Taşıma
günü hakemin imzalı durumu yeni kimlikle yeniden başlar. Önceki not: Operatör: şimdilik `Okan-wqm` hesabından devam; `suderra` şirketin hesabıdır,
sonra oraya aktarılır. Kural: taşıma gerçek hakem ve beyin repoları açılmadan (kurulum günü) yapılır, çünkü
imzalı durumun Sigstore kimliği repo adına bağlıdır; prova repoları atılacağı için etkilenmez.

**Daraltma tasarımı kararları (2026-10-29).** `docs/asama-0-daraltma.md` (18 mikro özellik, yürüyen iskelet)
onaylandı: K1 önyükleme hakemi Aşama 0'dan sonra da beyin push'larının hakemi; K2 aşama ortasında içe aktarma
(her biri (A) → aktarma → (B), insan dokunuşu sayılır); K3 ilk birim `apps/alert-engine` (TypeScript), oyuncak hedef
JavaScript, Aşama 0'da tek ekosistem npm; K4 dürüstlük provasının açığını ve imkânsız vektörünü Kurucu dışı bir ajan
yerleştirir, cevap anahtarı mühürlü; K5 (operatörün düzeltmesiyle) bütçe durdurucu değil emniyet frenidir: sistem abonelikle CLI üzerinden
çalıştığı ve bu kendi repolarımızda bir test olduğu için USD tahminleri fatura değildir ve şimdilik kısıt değildir;
tavanlar normal işi hiç durdurmayacak kadar yüksek, yalnız kaçak döngüyü keser; oturum ve USD sayıları ölçümdür,
çıkış koşulu değildir; gerçek sınır aboneliğin kullanım penceresidir, 429 operatör uyarısı ve kesintidir. **Aria kapsam dışıdır** (açık soru değil, karar). **Amaç yeniden:** kartopu gibi büyüyen,
öğrenen, uyguladığını test eden, öğrendiğini uygulayan, kendini geliştiren bir sistem; %100 LLM'lerce yapılır ve
uygulanır; insan yalnız yön verir ve hesap işlemlerini yapar; insan dokunuşu sayacı bunu ölçer.

**E32 kanıtı.** Prova hakeminin iş akışı yeniden kaydettirildikten (09:03Z) sonraki bir saatte de zamanlanmış koşu
yok (toplam 6+ saat, 0 koşu); E121'in dış canlılık gözlemcisi bunu gerektiriyor.

## Başlatma ölçütü (operatör, 2026-10-29)
Operatör: "uzman sensin; yeter ki kendi kendini iyileştirme, kendini geliştirme, öğrendiklerini uygulama altyapısı,
kayıt tutma ve hafızası hazır olsun, hafızasına göre uygulamalar yapabilsin." Yeni elle denetim turu açılmaz; bundan
sonra eksikleri sistem kendi bulur. Kurucu, aşağıdaki her satırın testi yeşil olmadan başlamaz.

| Altyapı | Bugün | Başlamadan | Kanıt (test) |
|---|---|---|---|
| Kayıt tutma | Zincirli defter (MF1), imzalı ve Rekor'lu kararlar, güvenlik defteri | Kurucu defterinin hakemce zincir ve yalnız-ekleme denetimi (E107) | Defterde tek bayt değişince `founder_ledger_invalid` |
| Hafıza | Hakemin imzalı durumu (donmuş spec, ret serileri) | Açık iddialar ve kanıtlanmış kusurlar durumda (E07, E08); Kurucu her oturuma defterinden ve son kararlardan devam eder (E91); durum kaybında hakem durur (E14, E92) | Oturum kapanıp açılınca kaldığı yer bulunur; artefakt yokken `fetch-state` durur |
| Öğrendiğini uygulama | Üç tekrar → `not_learning` | Kanıtlanmış kusur sonraki her push'ta yeniden koşar (E08); hata imzası (E70) | Düzeltilmeden gelen kusur, rakip kaçırsa da reddedilir |
| Kendini iyileştirme | Rakip her push'ta; CI hakem gerilemelerini yakalar | Bildirim kanalı imzalı sonuca ve operatör uyarısına (E53, E54/E124, E93); tohum dönemi (E88); karantina (E123); uyaran kırmızı koşu (E121) | Kurucu bildirimi `reports[]`'ta; tohum güncellemesinden sonra Kurucu push'u normal yargılanır |
| Kendini geliştirme | Aşama protokolü (`02`) | Dürüstlük provası (E79) ve rakip kanaryası (E126) | Provada istismar = 0, bildirim kaydı var |
| Kendini genişletme (kas) | Aşama protokolü; organ doğurma ve emeklilik tasarımda (`12`, `17`, prova `12a`) | Bildirim kanalında `missing_capability` türü: Kurucu eksik yeteneği kanıtıyla (ölçüm ya da başarısızlık) yazar; hakem kanıtı doğrular; yetenek aşama protokolüyle sonraki aşamanın spec'ine ya da aşama içi aktarımla (K2) bu aşamaya mikro özellik olarak girer. Bu kayıt (`docs/eksik-kaydi.md`) Kurucu'ya iş listesi olarak devredilir; Kurucu kendi bulduklarını kanıtıyla ekler ve testle kapatır | Kanıtlı `missing_capability` bildirimi spec değişikliği önerisine dönüşür; kanıtsız olan reddedilir |

Ders sistemi, organ yaşam döngüsü, güvenlik avcısı ve repolar arası öğrenme bu temelin üstüne Kurucu tarafından
sonraki aşamalarda kurulur (`docs/asama-0-daraltma.md`).
Operatör: "bizim şu an eklemediğimiz özellikleri kendisi bulup ekleyebilmeli, o kası olmalı." Beyin düzeyindeki kas
(sinyalden organ taslağı → gölge → etkin → emeklilik, `12`, `17`) genesis provasıyla (`12a`) kanıtlanır.

### Parti 2 (2026-10-29) · E06 E07 E08 E09 E10 E11 E12 E13 E20 E27 E33 · E141
Testler `tests/test_rival_memory.py`'de, sınıf adları kalem numarasıyla. Durum şeması 2'ye çıktı.
- **E06.** Rakibin protokolü ve `submit_verdict` sözleşmeyi söyler: gözlenen şey kusur yüzünden görülür, kod
  doğru olsaydı görülmez; traceback için `expect_stderr_contains` ya da `2>&1`; beklenti düz alt dizedir; en çok
  beş. `reproduce` stdout ve stderr'in son 2000 karakterini gizli taramasından geçirip saklar; zaman aşımına
  uğramış koşu hiçbir beklentiyi karşılamaz. Testler: yalnız stderr'deki traceback üretildi, kuyruklar sınırlı ve
  sırsız, zaman aşımı üç beklenti türünde de üretmez. Mutantlar: `protocol_without_the_contract`,
  `stderr_expectation_ignored`, `timed_out_run_reproduces`, `reproducer_tails_not_scanned`.
- **E09.** Gözleneni gösteren yeniden üretici aynı imaj ve ön adımla, kilit dosyası kurulmadan, boş (0755) bir
  kontrol ağacında da koşar; orada da gösteriyorsa `tautological`, sayılmaz; oradaki Docker hatası
  `runner_fault`. `true`/`expect_exit 0` ve yalnız çıkış koduna bakan yeniden üretici ("No module named" de 1
  ile çıkar) totolojiktir. "Önceden var" etiketi **sınır**: taban ağacı `yeniden`'e yeni bir artefakt olmadan
  gelmiyor; `29` bunu söylüyor. Mutantlar: `tautology_not_checked`, `control_tree_is_the_head`.
- **E07.** Yeniden üretilmeyen ya da yeniden üreticisiz çürütme durumda `open_claims` olarak kalır (en çok 10,
  en yenileri; iddia, ref'ler, yeniden üretici, gözlenen kuyruklar, ilk baş, `rewritten`). Sonraki rakibin
  isteğinde çitli bir bölümde kimliğiyle durur; rakip `open_claim` ile bir kez yeniden yazar. Açık iddialar her
  kod ve çıkış başında mekanik koşar, üretirse kanıtlanmış kusur olur; çıkış bloğu `open_claims`'i listeler.
  Mutantlar: `unreproduced_claim_forgotten`, `open_claims_not_shown_to_the_rival`, `claim_rewritten_twice`,
  `open_claim_never_rerun`.
- **E08.** Üretilmiş yeniden üretici `open_refutations`'ta kalır (en çok 20). `pull` her kod ve çıkış başında
  onları `state_repro` diye ister (çıktı `repro`), `yeniden` rakip `not_refuted` dese de koşturur; hâlâ
  üretiyorsa `refutation_still_reproduces`. İmza `refutation:` + `sha256(komut+beklentiler)`'in ilk 16 hanesi,
  yeni bulunanla aynı seri: iki ifadeyle üç push `not_learning`. Kayıt yalnız kabul edilen başta koşup
  üretmeyince ya da `control.json` `waived_refutations` (operatör feragati) ile kapanır. Mutantlar:
  `proven_defect_forgotten`, `state_reproducers_never_asked_for`, `still_reproducing_defect_accepted`,
  `refutation_signed_by_its_wording`, `proven_defect_never_closes`, `operator_waiver_ignored`,
  `reproduction_job_only_for_the_rival`.
- **E10.** `founder-ledger.jsonl` diff'ten (`:(exclude,glob)**/founder-ledger.jsonl`), istekteki değişen
  yollardan ve `ToolBox`'ın `read_file`, `grep`, `glob` ve satır sayımından çıkar; sınıflandırma onu yine görür.
  Mutantlar: `ledger_readable_by_the_rival`, `ledger_in_the_rivals_diff`, `ledger_named_in_the_request`.
- **E11.** Kurucu'ya sayılan: test, vektör, lisans, `pull`'un tipli retleri, yeniden üretilmiş ve hâlâ üreten
  çürütme, `prompt_too_large`, `max_turns`, `secret_in_prompt`. Rakip tarafı (`model_mismatch`,
  `malformed_verdict`, `no_verdict*`, `secret_in_verdict`, `refusal`, rakibin `budget`'ı, `request_rejected`,
  `rival_missing`), `budget`, `pull_error` ve altyapı serileri olduğu gibi bırakır. Üç ardışık rakip tarafı hata
  `warnings: rival_side_streak:3` ve `::warning::`. Mutantlar: `rival_side_failure_counts_against_the_founder`,
  `neutral_rejection_resets_the_streaks`, `rival_missing_held_against_the_founder`, `rival_side_streak_never_warns`.
  **K6** (kod denetçisi, 2026-10-29): `main`'de üç `secret_in_verdict` üst üste
  `{'rival_unresolved:secret_in_verdict:generic_assignment': 3}` ve `not_learning` veriyordu; sır rakibin yazdığı
  karardadır, rakip tarafıdır. `secret_in_prompt` Kurucu'nun diff'inden gelir, Kurucu tarafında kalır. Test: üç
  `secret_in_verdict` seriye dokunmaz, üç `secret_in_prompt` `not_learning`. Mutant:
  `secret_in_verdict_held_against_the_founder`.
- **E12.** 400/404/413/422 → `request_rejected:http_N`: değerlendirilir, Kurucu'ya sayılmaz, uyarır. Sayaç
  durumdadır (`outage_since`); park edilen baş 7 gün sonra `poll`'da kırmızı durur (`::error::`, çıkış 1).
  `isolation_*` → `outage_stop`: o baş zamanlayıcıyla denenmez, koşu kırmızıdır; operatör nedeni giderip
  `workflow_dispatch` ile bir kez denetir. Mutantlar: `permanent_4xx_retried_as_an_outage`,
  `isolation_fault_is_a_silent_outage`, `operator_stop_not_enforced`, `outage_retried_forever`,
  `outage_clock_restarts`, `dispatch_cannot_retry`.
- **E13.** Başlamış CLI'nin okunamayan maliyeti (sonuçsuz çıkış, bozuk sonuç, zaman aşımı, kesme)
  `min(kalan, koşu tavanı)` yazılır; hiç başlamayan ve `init`'te öldürülen koşu 0'dır. `rival` komutu
  `rival.json`'u `finally`'de yazar. `poll`, en yeni başarısız koşuda `cagir` başarılı, `yaz` başarısızsa,
  imzalı durum ondan eskiyse ve o koşunun `rival.json`'undaki baş aynıysa günde bir dener (`ghapi` koşu API'si,
  `actions: read`). Açık kalan: iptal ya da zaman aşımında `cagir`'ın paketleme ve yükleme adımları koşmaz;
  bu iş akışı değişikliği E16 (`!cancelled()`) ile. Mutantlar: `unparsed_cost_is_free`,
  `unreadable_cost_is_free`, `interrupted_run_leaves_no_record`, `unsigned_rival_run_reruns`,
  `unsigned_run_of_any_head_parks` (ve güncellenen `timeout_is_free`). **K7** (kod denetçisi): maliyet yalnız
  rakip "beklenirken" yazılıyordu, bu da yeşil bir `run.json` ister; `run.json` yoksa (`kos` başarısız, yükleme
  kaybı) `main`'de 4 000 000 mikro dolarlık harcama düşüyordu. Artık `rival.json` geldiyse maliyet her durumda
  yazılır (yeniden kullanılan sonuç hariç). Test: `run.json` yok, `kos=failure`, `cagir=success` → aylık ve aşama
  harcaması +4 000 000; kırmızı testli koşuda da yazılır. Mutant: `spend_of_an_unjudged_rival_dropped`.
- **E141** (K2, kod denetçisi; E01 sınıfı, vektörlerde). Vektör sonucu çıkış kodunu tutmuyordu ve `decide` 125'e
  yalnız testlerde bakıyordu: vektörler sırasında Docker'ın kendi hatası `vector_failed` oluyordu, yargılanıyor,
  hiç yeniden denenmiyor ve seriye yazılıyordu (`main`'de üç koşuda `not_learning:
  ['vector_failed:chain.V1.hash', ...]`). E01'den beri komutun kendi 125'i 1'e çevrildiği için 125 yalnız
  Docker'dır. Vektör sonucu `exit` ve son deneme 125 ile bittiyse `runner_fault` taşır; `decide` bunu 125 ile biten
  test gibi `infra kos:docker` kesintisi sayar. Test: her `docker run` 125 dönen koşucuyla üç push → kesinti,
  `last_evaluated_sha` değişmez, seriler aynı; Kurucu'nun kendi hatası (exit 1) `runner_fault` değildir.
  Mutantlar: `vector_docker_fault_judged`, `vector_exit_not_kept`.
- **E20.** `rival_artifacts` `{sha, outcome}` (`survived`, `refuted`; v1'den taşınan `unknown`); kayıt yalnız
  yeniden üreticiler tamamlanınca; çıkış yalnız `survived`'ı sayar. `yeniden` kesintisinde geçerli sonuç
  `pending_rival`'dır; aynı başın denemesinde `pull` rakibi çağırmaz (`reuse_rival`, bütçe engeli yok), maliyet
  ikinci kez yazılmaz, yalnız yeniden üreticiler koşar. Mutantlar: `any_reviewed_artifact_counts_at_exit`,
  `retry_calls_the_rival_again`, `reused_rival_booked_twice`, `artifact_recorded_before_its_reproducers_ran`.
- **E27.** CLI çıktısı akarken okunur; `init` olayı geldiği an önce izolasyon, sonra pinli sürüm, sonra model
  denetlenir, hata varsa süreç ağacı hemen öldürülür, maliyet 0. Kötü init basıp 60 s uyuyan sahte CLI 10 s
  altında döner (Windows'ta dört koşu ~2 s), MCP sunucusuna araç çağrısı ulaşmaz. Mutantlar:
  `init_checked_only_after_the_run`, `model_checked_before_isolation` (ve güncellenen `second_communicate_unbounded`).
- **E33.** `rival.json`: `cli_version`, `effort`, `prompt_sha256` (sistem + "\n" + istek), `tokens`, `duration_ms`,
  `head`. Pinden farklı sürüm `api_error:isolation_version` (init'te ve koşu sonunda), yani E12'nin operatör
  durdurması. Mutantlar: `version_drift_accepted`, `post_run_version_unchecked`, `provenance_not_recorded`.
- **Durum v2.** `state.migrate` v1'i taşır (bütçe, seriler, donmuş spec'ler, kabul edilen SHA aynen;
  `rival_artifacts`'ta yalnız son kabul `survived`); `fetch-state` silmek yerine taşır; bilinmeyen biçim yine
  durur ve `25`'i gösterir (E14'ün taşıma parçası). Mutantlar: `old_state_not_migrated`,
  `migration_trusts_unknown_artifacts`, `new_state_fields_unchecked`.
- **İş akışı.** Yalnız `yeniden`: `cek` çıktısı `repro`; koşul "rakibin yeniden üreticisi var ya da `repro` ve
  (spec ya da yeşil `kos`)"; `kos`'a bağımlılık; `rival` artefaktı yalnız `cagir` başarılıysa indirilip
  doğrulanır.
- **Spec.** `29` Rakibin kuralları: kontrol ağacı yalnız gözleneni gösteren yeniden üreticide ve kilitsiz;
  "önceden var" ölçülmez; sınırlar (20, 10), `open_claim`, feragat alanı, çıkışta da koşma, üreten açık iddia
  kanıtlanmış kusurdur. `29b` `yeniden` satırı aynı.
- **Kanıt özeti.** Kırmızı: yeni testlerin 53'ü eski kodda kırmızı (ikisi koruma testi); eski pakette denetim
  senaryoları: üç `model_mismatch` → `not_learning`, bütçe reddi seriyi siliyor; kanıtlanmış kusur aynı ağaçla
  `accepted`; aynı yeniden üretici iki ifadeyle iki imza; `true` ve zaman aşımı "üretildi"; çürütülmüş baş çıkışta
  sayılıyor; kötü init 60 s bekletiyor ve 12 300 mikro dolar yazıyor; dört kalıcı 4xx kesinti. Yeşil:
  Windows 284 test OK (21 atlandı: 18 POSIX, `claude` PATH'ten çıkarıldığı için 3 canlı CLI), Linux 305 OK
  (3 atlandı). K2, K6, K7 senaryoları `main`'de aynen tekrarlandı (yukarıda). Mutasyon 128 mutant (77 + 51
  yeni); K'lerden önceki 124'lük ilk koşuda 122: `toolbox_escapes_the_tree` (yeni defter
  denetimi `relative_to` ile ağaç dışını da reddedip korumayı ölçülmez kılmıştı; artık yalnız ad bakar) ve
  `reused_rival_booked_twice` (bekleyen sonuç maliyetsiz saklanıyordu; artık maliyetiyle saklanır, bir kez
  yazıldığı test edilir); son koşuda (Linux, dört parça) 128/128 öldü. Ayrıca kontrol ağacı `mkdtemp` ile 0700 açılıyordu;
  65534 kullanıcısı onu kopyalayamaz (kapsayıcıda denendi), 0755 yapıldı ve testle bağlandı.

### E151 (2026-10-29) · Aşama 0 tablosu 18 MF · E157 (kod) · E161 E162 E163 açıldı
- **Tablo.** `seed/bootstrap/stages/stage0.json` `asama-0/14`'ün makine kopyasıdır, `26c` biçiminde (`{stage, mfs:
  [{mf, tests, groups, module, calls}]}`; `calls` çağrılanlardır). `stages.py` her okuyuşta denetler: alanlar tam;
  MF'ler 1..N sırayla; test numarası 1–999 ve tek MF'nin; grup adı; modül `referee/` altında güvenli, normal biçimde ve
  tek MF'nin; `calls` artan ve çağırandan küçük (`14` "Sıra"). Bozuk tablo `ConfigError`'dur: `pull` tabloyu içerik
  korumasının dışında yükler, koşu `stop:` ile durur, Kurucu'ya `pull_error` yazılmaz. `manifest.STAGE0_MF_TESTS` ve
  `STAGE0_MF_COUNT` kalktı; `check_stage0`, çıkış (`done_mf` = 1..18) ve vektör koşucusu tablodan okur.
- **Tohum testi.** `test_wiring.StageTableMatchesTheSpecTest` `14`'ün tablosunu (sütunlar, test, vektör grubu, modül)
  ve `calls` satırını (zincir dahil; "17 ve 18 hepsini çağırır" her birinin kendinden öncekilerin hepsini çağırması
  olarak okunur, E157; okunamayan cümle kırmızı) ayrıştırıp JSON'la birebir
  karşılaştırır. JSON'daki her test §0.9'da "MF k" satırıdır, tersi de; §0.9'un "18 MF'ye 21 test"i, `14`'ün ve
  `asama-0/10`'un 18'i tabloyla aynı; `29d`'nin grup → MF tablosu aynı; `vectors.json`'da sahibi `asama-0` olan
  grupları tablo adlandırır, yalnız onları.
- **Vektör grupları.** Sahiplik tablodadır: grup, onu adlandıran MF bitince koşar (`chain`: MF1 ve MF10, bir kez).
  `vectors.json`'da `mf` yerine `owner`: `chain` `asama-0`, `cp_lower`, `mcnemar`, `match` `P1`, `drill` `asama-2`
  (prova yargıcının yazıcısı da öyle yazar); sonuncular Aşama 0'da koşmaz (`29d`). Koşucunun onları ölçen testleri
  hepsini sahiplenen bir test tablosuyla (`helpers.EVERY_GROUP`) sürer. Tohumda olmayan 16 grup için beklenen değer
  uydurulmadı (E161). **Karar: kod push'unda uyarı, çıkışta ret.** `run-tests` bitmiş bir MF'nin sahiplendiği ama
  tohumda olmayan grupları `vector_groups_missing` olarak yazar; `decide` kod push'unda `warnings:
  vector_group_missing:<grup>` (adım özetinde `::warning::`), çıkışta `exit_condition vector_group_missing:<grup>`
  verir. Gerekçe: değerler tohumla gelir, Kurucu değiştiremez (`29a`); tohumdan doğan neden Kurucu'nun değildir
  (`29e` taslağı, E11); ret olsaydı Kurucu MF2'de durur, tohumun açığı yüzünden `not_learning` olurdu. Çıkış "vektör
  grupları geçer" ister (`asama-0/10` #testler): olmayan grup geçemez. Grup tohum dönemiyle gelince bitmiş her MF
  için sonraki her push'ta koşar (`14`).
- **Modülsüz kırmızı.** `pull` `meta.module_less`'i yazar: kod push'unda son kabul edilmiş commit'in `done_mf`'inde
  olmayan bitmiş MF'ler (`gitio.file_at`; okunamayan taban bildirimi "hiçbiri bitmemiş" sayılır), çıkışta hepsi
  (#modulsuz). `run-tests` ana koşu yeşilse her MF için ağacı yeniden açar, tablodaki `referee/<modül>` yolunu siler
  ve MF'nin her testini aynı kumda (`DockerRunner`, aynı bayraklar) koşar (`moduleless.py`). Yeşil kalan bir test
  push'u `module_less_green:MFk` ile reddeder (imza da bu; Kurucu'ya sayılır); yol ağaçta yoksa ayrıntı söyler.
  Okuma test başınadır (`tohum/04` 1: "geri alındığında yeşil kalan test, test değildir"; E163). Bu kumdaki Docker
  hatası `infra kos:docker` kesintisidir; yeşil bir koşuda `pull`'un istediği bir MF'nin sonucu yoksa `infra
  kos:module_less_incomplete` (E05'in kuralı). Modülsüz yeşil koşu `green` değildir, rakip çağrılmaz.
- **Testler ve mutantlar.** Yeni: `tests/test_stages.py` (yükleyicinin her kuralı, modülsüz ağaç);
  `test_decision.ModuleLessRed` ve taklit koşucuyla `run-tests` uçtan uca; `pull`'un `module_less`'i ve bozuk tablo
  durması (`test_flow`); tablo güdümlü vektörler ve eksik gruplar (`test_units`); referans beynin modülsüz kırmızısı
  (`test_reference_brain`). 30 MF varsayan testler tablodan kurulur. `mutate.py` kopyaya `spec/asama-0`'ı alır; 32
  yeni mutant (yükleyici 6, bildirim 2, çıkış 1, bozuk tablo 1, sahiplik 2, eksik grup 5, modülsüz kırmızı 9, tohum
  verisi ve sayfalar 6).
- **Kanıt.** Birleştirmeden önce: Windows 336 test OK (18 atlandı), Linux 354 OK (3 atlandı); mutasyon 164/164
  öldü (Linux, dört parça; 32 yeni mutantın her biri kendi testiyle). `local/e2e.py` gerçek Docker'da, pinli
  imajla: `module-less red [('T13', 1)]`, `accepted`. Aynı push, T13'ü modüle dokunmayan bir komutla gerçek
  kapsayıcıda: `rejected [module_less_green:MF1]`. `main` (dd14bfc) birleştirildikten sonra: Windows 340 OK (18
  atlandı), Linux 358 OK (3 atlandı), prova yargıcı 31 OK; birleşen dosyalara bağlı beş mutant `--only` ile öldü
  (`broken_table_rejects_the_push`, `module_less_never_run`, `module_less_runs_on_the_pushed_tree`,
  `module_less_not_at_the_exit`, `page_calls_line_drifts`); 168 mutantın tamamı birleştirmeden sonra `main` CI'sinde.
- **Pilot.** MF1 (T13, `chain`, `ledger/chain.py`) ve spec isteğiyle dondurma değişmedi. Canlı beynin `done_mf`'i [1]
  ise etkisi yok; eski numaralarla MF2+ bitmişse bu tohum hakeme girince `missing_test:MF2:T38` gibi retler gelir. Kod
  hakeme yalnız tohum dönemiyle girer.
- **Açık kalan.** E161 (16 grup ve genel veri koşucusu), E162 (çıkışın kodda olmayan koşulları, MF17'nin `wiring`
  denetimi dahil), E163 (modülsüz kırmızının iki okuması); E157'nin `14` metni; `spec/tohum/29`, `29b` ve yeni `29e`
  metinleri ayrı adımdır (`docs/asama-0-daraltma-29-29b.md`).

### E88 E162 (2026-10-29) · tohum dönemi · çıkış kapalıya düşer · E180–E183 açıldı
- **Özet satırı.** `setup/summary.json` `seed_epochs[]` taşıyabilir: `{commit, spec_tohum_sha256, seed_sha256,
  bootstrap_sha256}` (`26c`), tam bu anahtarlar, `seed_sha256` beyinde `seed/` yoksa `null` (spec "beyinde varsa"
  dışında sessiz; en dar okuma). `config.load_summary` satırları sıkı okur, boş ya da biçimsiz dizi durmadır; son
  satır geçerli dönemdir. Dizi yoksa davranış öncekidir: `seed_commit`, `seed_tree_sha256` kurulum tohumudur
  (`26c`'de bu adlar yok, E182; başlatıcı E154 için `seed_commit`'i okur, dokunulmadı).
- **Satır kendi commit'ine uymalı.** Dizi varsa `pull` (içerik korumasının dışında) son satırın commit'ini beyinde
  arar ve o commit'in `spec/tohum/` ve `seed/` ağaç hash'lerini satırla karşılaştırır (`cli._check_epoch`); uymazsa
  `stop: setup/summary.json: the last seed epoch ...`, koşu durur, hiçbir push yanlış bir tohuma karşı yargılanmaz
  (`25`: hash özetle uyuşmazsa durur; operatör dosyaları kapalıya düşer, `26c`). Satırı `seed-epoch` komutu
  yazar (git blob'larından, satır sonundan bağımsız); `bootstrap_sha256` `--source`'un `seed/bootstrap/`'udur.
- **(d) Teslimin kendisi.** Baş son satırın commit'iyse push `seed_update`'tir: değerlendirilmez, rakip, test ve
  seri yok, `noop` imzalanır, `last_evaluated_sha` ilerler, `last_accepted_sha` ilerlemez (`cli._seed_update`,
  `decide.NOTHING_TO_JUDGE`). Teslim Kurucu'nun reddedilmiş bir başının üstüne gelse de o kod onun adıyla yeniden
  yargılanmaz (taslak metin içerikle tanımlıyordu, E183).
- **(a) Sonraki push'lar.** Son kabul edilmiş SHA teslimden eskiyse teslim her diff'te kalır. Başın tohum ağaçları
  son satıra eşitken diff'teki `spec/tohum/**` ve `seed/**` Kurucu'nun değişikliği sayılmaz (`meta.changed`
  Kurucu'nunkiler), push kendi türüyle (kod, spec, çıkış, defter) yargılanır; rakibin diff'i tohum yollarını hiç
  taşımaz (`exclude_dirs=HIDDEN_DIRS + SEED_DIRS`): orada kalan tohum yolu ancak teslimdir, başka tohum değişikliği
  rakipten önce reddedilir. Çıkış isteğinde de böyledir: pinli SHA ile istek arasındaki teslim yolları #yalniz'i
  bozmaz, Kurucu'nun değişikliği değildir.
- **(b) Kurucu'nun tohum değişikliği.** Dizi varsa her başın iki ağacı son satıra eşit olmalı: değişen, eklenen ya da
  silinen her tohum dosyası `seed_modified` ve `seed_tree_mismatch`'tir; `null` satırdan sonra eklenen `seed/` de.
- **(c) İmzalı durum.** Dönem durumu sıfırlamaz: `seed_update` her `noop` gibi `last_evaluated_sha`, `runs` ve
  `origin`'i ilerletir, başka bir başın bekleyen rakip sonucunu (`pending_rival`) bırakır; donmuş spec'ler, seriler,
  `repeat_events`, açık iddialar, kanıtlanmış kusurlar, rakip artefaktları ve harcamalar aynen kalır, sonraki push
  onlara karşı yargılanır (seri sürer, yeniden üreticiler istenir). Durum kaybolursa
  `state.initial` son dönemin commit'inden başlar (`25` "Durum kaybolursa").
- **Operatör yolu.** `seed/founder/README.md` "Tohum teslimi": `STOP` ve kill switch, hakem kopyası, beyne tek
  commit (`git archive | tar`), `seed-epoch` satırı, kill switch kapalı, elle tetikleme ve `seed_update` doğrulaması,
  dokunuş satırı. `25` 10b'nin sırası (satır, sonra beyne push) da çalışır: kill switch açıkken hakem koşmaz, push
  edilmemiş commit'i adlandıran satır yalnız koşuyu durdurur.
- **E162.** `decide.EXIT_NOT_CHECKED` = `kurucu-defteri`, `is-akisi`, `agac` (yalnız büyük-küçük harf duyarlı operatör
  adı var; duyarsız ad, ajan yapılandırması, `toy_tree_sha256` yok), `genellik`, `spec` (`#lint #spec #okuyucu`
  satırı), `durustluk`: her çıkışa `exit_condition` `not_checked:<koşul>` ekler, `transferable` olamaz. Denetlenen
  koşullar nedenlerini korur (#testler #kirmizi #lisans, #modulsuz, #rakip, #lock #kilit, #tekrar, #yalniz).
  `not_checked` Kurucu'ya sayılmaz (`29b` "Ret hafızası": yalnız düzeltebildiği); aynı mantıktaki
  `vector_group_missing` çıkış nedeni sayılmaya devam eder (E181). Test, `asama-0/10` tablosunun her satırının ya
  kodda denetlendiğini (yeriyle) ya listede olduğunu ister; sayfaya eklenen satır sessiz geçemez.
- **Testler ve mutantlar.** `tests/test_seed_epoch.py` (9 test: (a) iki, kod, spec, çıkış ve defter push'larıyla;
  (b) iki; (c); (d); satır durması; özet okuma; kayıp durum); `test_decision.KindsAndExit`'e üç E162 testi; çıkış testleri (`test_decision`,
  `test_rival_memory`, `test_flow`) altı `not_checked`'i bekler, `test_flow` aktarımı `EXIT_NOT_CHECKED` boşken
  ölçer. 16 yeni mutant (E88 13, E162 3); `ledger_in_the_rivals_diff` ve `reports_in_the_rivals_diff` çapaları
  yenilendi.
- **Kanıt.** Taban (8900760): Windows 342 test OK (18 atlandı), Linux 360 OK (3 atlandı). Dal: Windows 354 OK (18
  atlandı), Linux 372 OK (3 atlandı). Mutasyon: 16 yeni, çapası yenilenen 2 ve değişen satırlara bağlı 3 mutant
  (`non_utf8_name_reaches_json`, `unsafe_name_reaches_the_tree_hash`, `ledger_breaks_an_exit_request`) `--only`
  kümesiyle 21/21 öldü; sonra bütün liste dört parçada 188/188 (47 × 4, Linux kapsayıcı). README'nin 4., 5. ve 7.
  adımı Git Bash'te sahte bir beyinde koşuldu: `git archive HEAD spec/tohum | tar -x -f -` 60 dosya, `seed-epoch`
  satırı (`seed_sha256: null`), `control` ok, `pull` `kind=seed_update`, `pre_reasons []`; satırın
  `spec_tohum_sha256`'sı (`8797ba63…`) `snowball-mcp` HEAD'inin `seed-hash`'iyle aynı (Windows'ta satır sonu gidip
  gelince hash değişmedi). E181 bir koşuyla görüldü: `vector_group_missing:secrets` ile üç çıkış isteği
  `not_learning`, aynı koşudaki altı `not_checked` sayılmadı.
- **Yapılmayan.** `bootstrap_sha256` biçimce okunur, hakemin kendi `bootstrap/` kopyasıyla karşılaştırılmaz (E24);
  teslim `spec/asama-*` ve `spec/INDEX.md` taşıyamaz (E180); altı koşulun denetimleri (E107, E100/E132, E130/E131,
  E102, E79) ve MF17'nin her push'taki `wiring` denetimi; `spec/` bu dalda değişmedi, taslak metin E182/E183'te.

## Doğrulanmış sağlam taraflar
Kapsayıcı bayrakları ve kırmızı kontroller; host'ta kabuk enjeksiyonu yok; `$GITHUB_OUTPUT`'a serbest
metin girmiyor; tek sır yalnız rakip adımında; rakibin ortamı ve init doğrulaması; ağaç kurulurken
kancalar ve filtreler etkisiz; işler arası artefakt hash'leri; imzalı durumun kimlik doğrulaması;
spec'te 80 satırı aşan sayfa, kırık çapraz referans ya da INDEX uyumsuzluğu yok; vektörler ve mikro
özellik→test haritası spec ile birebir.

## Sıra
Her parti kendi dalında kapanır, testleri ve mutantlarıyla `main`'e merge edilir, kayıttaki satırlar
o commit ile `kapandı` olur.

1. **Güvenlik, çökme ve takılma:** E01, E02, E41, E03, E04, E05, E17.
2. **Rakip ve yeniden üretme:** E06, E07, E08, E09, E10, E11, E12, E13, E20, E27, E33.
3. **Durum ve iş akışı:** E14, E15, E16, E18, E19, E29, E30, E31, E32, E34, E26 (CI).
4. **Spec:** E21, E22, E23, E24, E47, E25, E35, E36, E37.
5. **Doğrulama araçları:** E42, E43, E44, E45, E46, E48, E49, E50, E51, E38, E39, E40.
