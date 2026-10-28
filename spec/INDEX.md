# Dizin

Tarih: 2026-10-28 · Sürüm: 2.0 · Durum: taslak · Sahibi: operatör
Okunma: her oturumda, görev seçilirken
Çapa: bu dizin dosya başlıklarından üretilir; elle düzenlenmez

---

## Tohum: çekirdek, yasalar ve protokoller

| Sayfa | Başlık | Okunma |
|---|---|---|
| `tohum/00-cekirdek.md` | Çekirdek — Kurucu Ajan ve Yasalar | her oturumda |
| `tohum/00a-sinirlar-operator-ilk-gorev.md` | Kurucu'nun Sınırları, Operatörün İşi, İlk Görev | her oturumda, çekirdekten hemen sonra |
| `tohum/01-hedef-sistem.md` | Hedef Sistem | ilk oturumda |
| `tohum/01a-mimari-ve-yetki.md` | Mimari ve Yetki: Beyin, Hedef Repo, Mühürlü Depo | ilk oturumda ve her yeni repoya bağlanırken |
| `tohum/02-asama-protokolu.md` | Aşama Protokolü | her aşama başında ve sonunda |
| `tohum/03-sinif-merdiveni.md` | Sınıf Merdiveni ve Aşama Sırası | yeni sınıf ya da aşama açılırken |
| `tohum/04-is-boyutu-ve-gercek-test.md` | İş Boyutu ve Gerçek Test | her mikro görevde ve her test yazarken |
| `tohum/04a-oracle-sertlestirme.md` | Oracle Sertleştirme: Test Yanlış Nedenle Yeşile Dönmesin | her oracle koşusunda ve test-yazıcı tasarlarken |
| `tohum/05-etki-kumesi-ve-baglanti.md` | Etki Kümesi ve Bağlantı Kuralı | koda dokunmadan önce ve yeni organ tasarlarken |
| `tohum/06-maliyet-merdiveni.md` | Maliyet Merdiveni ve Bütçe | bir yetenek harness'te geçtikten sonra ve her bütçe kararında |
| `tohum/07-entegrasyon-dali-ve-geri-alma.md` | Entegrasyon Dalı, Geri Alma, Bulgu Kimliği | her döngü başında ve her merge'de |
| `tohum/08-sandbox-ve-durust-bildirim.md` | Sandbox ve Dürüst Bildirim (Y10) | her ajan dispatch'inde |
| `tohum/09-takim-kurma.md` | Takım Kurma Kuralları | takım kurarken ve ajan önerirken |
| `tohum/09a-bagimsizlik.md` | Bağımsızlık ve Donmuş Koltuklar | her dispatch'te ve her koltuk ataması değiştiğinde |
| `tohum/10-cekisme-protokolu.md` | Çekişme Protokolü: Her Artefakt İçin | her artefakt üretildiğinde |
| `tohum/10a-bulgu-paneli.md` | Bulgu Paneli (K5 ve üstü): Beş Faz | K5 ve üstü bulgu değerlendirirken |
| `tohum/11-itibar.md` | İtibar ve Puanlama | dispatch ve yeniden yazım kararlarında |
| `tohum/12-genesis.md` | Genesis: Organ Yazma, Ölçme, Kaldırma, Yeniden Yazma | yeni organ yazarken ve ablasyonda |
| `tohum/13-memory-ve-zincir.md` | Memory Kuralları ve Zincirli Defterler | yeni memory açarken ve her defter yazımında |
| `tohum/14-repoya-baglanma.md` | Repoya Bağlanma | yeni repoda ve property eklerken |
| `tohum/15-dokumantasyon.md` | Dokümantasyon: Her Özellik Tarihli Tek Sayfa, Her Organ ve Bulgu Üretilmiş Sayfa | her sayfa yazarken ve her döngüde doküman üretilirken |
| `tohum/16-hafiza-modeli.md` | Hafıza Modeli: Sekiz Hafıza, Tek Defter | yeni hafıza türü önerirken ve her defter şeması değişikliğinde |
| `tohum/17-kas-buyutme-sinyalleri.md` | Kas Büyütme Sinyalleri: Hangi Ölçüm Hangi Organı Doğurur | her döngü sonunda, genesis kuyruğu kurulurken |
| `tohum/18-politika-ve-dinamik-esikler.md` | Politika Dosyası ve Dinamik Eşikler | her kapı kararında ve her eşik değişikliği önerisinde |
| `tohum/19-olcum-istatistigi.md` | Ölçüm İstatistiği: PASS Ne Zaman Anlamlıdır | her çıkış testi tasarlanırken ve her verdict okunurken |
| `tohum/20-metrikler.md` | Metrikler: Bir Bakım Sistemi Neyi Sayar | `status.md` üretilirken ve her Gözcü değerlendirmesinde |
| `tohum/21-cok-repo.md` | Çok Repo: Ne Taşınır, Ne Taşınmaz | beyin yeni bir repoya bağlanırken |
| `tohum/22-dersler.md` | Dersler: Öğrenme Planlayıcıya ve Implementer'a Akar | plan yaparken, düzeltme yazarken, test yazarken |
| `tohum/23-yama-degil-mimari-cozum.md` | Yama Değil, Mimari Çözüm | her düzeltme tasarlanırken ve panel faz 4'te |
| `tohum/24-calisma-modeli.md` | Çalışma Modeli: Beyin Nasıl Koşar, Ajanlar Nasıl Dispatch Edilir | Aşama 0 inşasından önce ve her dispatch değişikliğinde |
| `tohum/25-kurulum-gunu.md` | Kurulum Günü: Operatörün Bir Kerelik İşi | ilk başlatmadan önce, bir kez |
| `tohum/26-semalar.md` | Şemalar, Araç İmzaları, Kanonik Biçimler | Aşama 0 inşasında ve her şema değişikliğinde |
| `tohum/CHANGELOG.md` | Değişiklik Günlüğü — Tohum |  |

## Aşama 0 — Ölçüm Zemini

| Sayfa | Başlık | Okunma |
|---|---|---|
| `asama-0/00-ozet.md` | Aşama 0 — Ölçüm Zemini | aşama başında |
| `asama-0/01-amac.md` | Aşama 0 §0.1 — Amaç | Aşama 0 çalışırken |
| `asama-0/02-dogruluk-ozellikleri.md` | Aşama 0 §0.2 — Doğruluk özellikleri | Aşama 0 çalışırken |
| `asama-0/03-roller.md` | Aşama 0 §0.3 — Roller | Aşama 0 çalışırken |
| `asama-0/04-hata-seti.md` | Aşama 0 §0.4 — Hata seti | Aşama 0 çalışırken |
| `asama-0/05-property-ve-sinif-etiketleri.md` | Aşama 0 §0.5 — Property ve sınıf etiketleri | Aşama 0 çalışırken |
| `asama-0/06-snapshot-uretimi.md` | Aşama 0 §0.6 — Snapshot üretimi | Aşama 0 çalışırken |
| `asama-0/07-bulgu-ve-kosu-semasi.md` | Aşama 0 §0.7 — Bulgu ve koşu şeması | Aşama 0 çalışırken |
| `asama-0/08-puanlama-ve-metrikler.md` | Aşama 0 §0.8 — Puanlama ve metrikler | Aşama 0 çalışırken |
| `asama-0/09-harness-in-kendi-testleri.md` | Aşama 0 §0.9 — Harness'in kendi testleri | Aşama 0 çalışırken |
| `asama-0/10-cikis-testi.md` | Aşama 0 §0.10 — Çıkış testi (hepsi birlikte PASS) | Aşama 0 çalışırken |
| `asama-0/11-yasaklar.md` | Aşama 0 §0.11 — Yasaklar | Aşama 0 çalışırken |
| `asama-0/12-butce.md` | Aşama 0 §0.12 — Bütçe (başlangıç değerleri; yalnız operatör değiştirir) | Aşama 0 çalışırken |
| `asama-0/13-teslim-listesi.md` | Aşama 0 §0.13 — Teslim listesi | Aşama 0 çalışırken |
| `asama-0/14-sirali-mikro-ozellikler.md` | Aşama 0 §0.14 — Sıralı mikro özellikler | Aşama 0 çalışırken |
| `asama-0/CHANGELOG.md` | Değişiklik Günlüğü — Aşama 0 |  |

## Aşama 1 — İlk Adapter: Lint (K0)

| Sayfa | Başlık | Okunma |
|---|---|---|
| `asama-1/00-ozet.md` | Aşama 1 — İlk Adapter: Lint (K0), Döngü En Basit Hâliyle | aşama başında |
| `asama-1/01-amac.md` | Aşama 1 §1.1 — Amaç | Aşama 1 çalışırken |
| `asama-1/02-dogruluk-ozellikleri.md` | Aşama 1 §1.2 — Doğruluk özellikleri | Aşama 1 çalışırken |
| `asama-1/03-girisler.md` | Aşama 1 §1.3 — Girişler | Aşama 1 çalışırken |
| `asama-1/04-roller.md` | Aşama 1 §1.4 — Roller | Aşama 1 çalışırken |
| `asama-1/05-dongu-adim-adim.md` | Aşama 1 §1.5 — Döngü, adım adım | Aşama 1 çalışırken |
| `asama-1/06-sirali-mikro-ozellikler.md` | Aşama 1 §1.6 — Sıralı mikro özellikler | Aşama 1 çalışırken |
| `asama-1/07-harness-olcumu.md` | Aşama 1 §1.7 — Harness ölçümü | Aşama 1 çalışırken |
| `asama-1/08-cikis-testi.md` | Aşama 1 §1.8 — Çıkış testi (hepsi birlikte PASS) | Aşama 1 çalışırken |
| `asama-1/09-yasaklar.md` | Aşama 1 §1.9 — Yasaklar | Aşama 1 çalışırken |
| `asama-1/10-butce.md` | Aşama 1 §1.10 — Bütçe (başlangıç değerleri; yalnız operatör değiştirir) | Aşama 1 çalışırken |
| `asama-1/11-sonuc-ne-soyler.md` | Aşama 1 §1.11 — Sonuç ne söyler | Aşama 1 çalışırken |
| `asama-1/12-teslim-listesi.md` | Aşama 1 §1.12 — Teslim listesi | Aşama 1 çalışırken |
| `asama-1/CHANGELOG.md` | Değişiklik Günlüğü — Aşama 1 |  |

## Aşama 4 — LLM Avcı: Mantık Hataları (K5), hedef taslak

| Sayfa | Başlık | Okunma |
|---|---|---|
| `asama-4/00-ozet.md` | Aşama 4 — LLM Avcı: Mantık Hataları (K5), Kalıpsız | aşama başında; Aşama 3 PASS alınca yeniden yazılır |
| `asama-4/01-amac.md` | Aşama 4 §4.1 — Amaç | Aşama 4 çalışırken |
| `asama-4/02-dogruluk-ozellikleri.md` | Aşama 4 §4.2 — Doğruluk özellikleri | Aşama 4 çalışırken |
| `asama-4/03-girisler.md` | Aşama 4 §4.3 — Girişler | Aşama 4 çalışırken |
| `asama-4/04-roller.md` | Aşama 4 §4.4 — Roller | Aşama 4 çalışırken |
| `asama-4/05-avci-bildigi-ve-ciktisi.md` | Aşama 4 §4.5 — Avcının bildiği ve çıktısı | Aşama 4 çalışırken |
| `asama-4/06-kosu-protokolu.md` | Aşama 4 §4.6 — Koşu protokolü | Aşama 4 çalışırken |
| `asama-4/07-panel-ve-oracle.md` | Aşama 4 §4.7 — Panel ve yürütme oracle'ı | Aşama 4 çalışırken |
| `asama-4/08-cikis-birinci-kapi.md` | Aşama 4 §4.8 — Çıkış testi, birinci kapı: isabet | Aşama 4 çalışırken |
| `asama-4/09-cikis-ikinci-kapi.md` | Aşama 4 §4.9 — Çıkış testi, ikinci kapı: maliyet inişi | Aşama 4 çalışırken |
| `asama-4/10-yasaklar.md` | Aşama 4 §4.10 — Yasaklar | Aşama 4 çalışırken |
| `asama-4/11-butce.md` | Aşama 4 §4.11 — Bütçe (başlangıç; yalnız operatör değiştirir) | Aşama 4 çalışırken |
| `asama-4/12-sonuc-ve-teslim.md` | Aşama 4 §4.12 — Sonuç ne söyler ve teslim listesi | Aşama 4 çalışırken |
| `asama-4/CHANGELOG.md` | Değişiklik Günlüğü — Aşama 4 |  |

## Görev → sayfa

| Görev | Oku |
|---|---|
| Her oturum | `tohum/00`, `tohum/00a` |
| Kurulum ve ilk başlatma | `tohum/25`, `tohum/24`, `tohum/01a` |
| Yeni repoya bağlanma | `tohum/01`, `tohum/14`, `tohum/21` |
| Aşama açma ve kapama | `tohum/02`, `tohum/03`, `tohum/19`, ilgili `asama-N/00-ozet.md` |
| Koda dokunma | `tohum/04`, `tohum/04a`, `tohum/05`, `tohum/07`, `tohum/08`, `tohum/23` |
| Artefakt üretme ve değerlendirme | `tohum/10`, `tohum/10a`, `tohum/09a`, `tohum/11` |
| Organ yazma ve kaldırma | `tohum/09`, `tohum/12`, `tohum/17` |
| Hafıza, defter, ders | `tohum/13`, `tohum/16`, `tohum/22` |
| Eşik ve bütçe | `tohum/18`, `tohum/06`, `tohum/20` |
| Şema ve araç imzası | `tohum/26` |
| Sayfa yazma | `tohum/15` |
