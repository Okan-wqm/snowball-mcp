# Sınıf Merdiveni ve Aşama Sırası

Tarih: 2026-10-28 · Sürüm: 2.0 · Durum: taslak · Sahibi: operatör
Okunma: yeni sınıf ya da aşama açılırken
Çapa: harness PASS raporları, sınıf başına; profile.json araç zinciri

---

Adapter'lar en basit hata sınıfından başlar ve sınıf sınıf çoğalır. Sınıflar alan bağımsızdır;
her sınıfın adapter'ı profildeki aracı sarar. LLM, mekanik aracın bittiği yerde başlar.

| Sınıf | Hata türü | Avcı | Oracle |
|---|---|---|---|
| K0 | Lint ve format | Profildeki lint araçlarını saran adapter | Aracın yeniden koşusu |
| K1 | Tip ve derleme hataları | Sarıcı adapter | Araç |
| K2 | Ölü kod, kullanılmayan export, koşmayan test hedefi | Sarıcı adapter, repo invariantları | Araç; silmelerde etki kümesi testleri |
| K3 | Sözleşme paritesi: iki uçlu sözleşmeler | LLM'siz mekanik çapraz kontrol | Kasıtlı bozma |
| K4 | Şema yerleşimi ve mevcut invariant testleri | Sarıcı adapter | Araç |
| K5 | Mantık hataları: eksik await, ters koşul, yanlış sıra, yarım idempotency | LLM avcı, Opus | Test oracle'ı, Sonnet |
| K6 | Güvenlik, yetki sınırı, tenant izolasyonu, bağımlılık değişikliği | LLM avcı, Opus | Test oracle'ı, Sonnet |
| K7 | Performans | Profildeki benchmark ve sorgu planı araçları | Baseline'a karşı ölçüm |
| K8 | Bayat doküman | Çapa çözümleme | Çözülmeyen çapa |

Bir sınıf grubu ancak bir önceki aşama PASS alınca açılır. K3'ün aracı yoktur; oracle'ı kasıtlı
bozmadır. Her açılış aynı döngüyü yeniden koşturur: adapter → oracle → düzeltme → merge → defter
→ maliyet inişi.

| Aşama | Döngüde canlı olan | Oracle |
|---|---|---|
| 0 | Asgari harness: K0 için hata seti, puanlama, mühür, zincirli defterler, taban avcı. LLM avcı yok | Harness'in zorunlu kendi testleri |
| 1 | K0 döngüsü uçtan uca: lint adapter → araç oracle'ı → `--fix`, olmazsa Sonnet → entegrasyon dalına merge → defter → üretilmiş organ ve bulgu sayfaları | Araç yeniden koşusu, profildeki etkilenen-test komutu |
| 2 | K1 ve K2 adapter'ları; **Plan fazı**: Opus planlayıcı kuyruğu kapsama haritası, `blocked` listesi ve derslerden sıralar; ders okuyucusu doğar | Araç; planlayıcı sırası rastgele sıradan daha yüksek değer / USD verir |
| 3 | K3 ve K4; ilk araç-dışı mekanik dedektörler; maliyet inişi canlı; harita katmanı (b) | Kasıtlı bozma, araç |
| 4 | K5: kalıpsız LLM avcı, beş fazlı panel, test oracle'ı, TP'den dedektör üretimi | Held-out recall alt sınırı, yürütme oracle'ı, değer / USD |
| 5 | K6, K7, K8; harita katmanları (c) ve (d); genesis tüm organ türlerine ve property'lere açık | Her ekleme için harness deltası, maliyet deltası, ablasyon |
| 6 | `main`'e terfi: entegrasyon dalında N gün yeşil, canary, otomatik geri alma; push'ta deploy olmadığı kanıtlı | Soak süresi ve geri alma provası |

Genesis'in kendisi Aşama 1'den beri vardır (`12-genesis.md`); aşamalar kapsamını açar. Aşama 2,
3, 5 ve 6'nın ayrıntılı spec'leri sırası gelince yazılır; bu tablo onların hedefidir.
