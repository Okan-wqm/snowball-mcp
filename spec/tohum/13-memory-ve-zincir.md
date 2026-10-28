# Memory Kuralları ve Zincirli Defterler

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: taslak · Sahibi: operatör
Okunma: yeni memory açarken ve her defter yazımında
Çapa: beklemede: aşama 0 — chain/root.jsonl; hakem attestation'ları; chain.asof

---

- Memory bir üçlüdür: **yazar, okuyucu, okuyucunun değiştirdiği karar.** Üçü aynı PR'da gelir.
  Sekiz hafıza türü ve tohumda hangisinin verildiği `16-hafiza-modeli.md`'dedir.
- İlk memory, Aşama 0'daki hata seti ve oracle kararlarıdır. İkincisi maliyet defteri, üçüncüsü
  itibar, dördüncüsü dersler (`22-dersler.md`). Semantik ya da vektör memory ancak ölçülmüş bir
  geri çağırma boşluğunda eklenir.
- **Repo haritası** sınıf merdiveniyle büyür; `map/edges.jsonl`'da durur. Katmanları: (a) derleme
  ve import grafiği, profildeki graf aracından, Aşama 1'de bedava; (b) çalışma zamanı bağları: event üretici ve
  tüketicileri, HTTP uçları, tablo sahipleri, mesaj konuları, env değişkenleri, feature flag'ler,
  K3 ve K4 ile; (c) güvenlik sınırları: yetki kapıları, kimlik bağlamının kaynağı, satır düzeyi
  güvenlikli tablolar, sır ve PII noktaları, K6 ile; (d) dış bağımlılıklar: paket → sürüm →
  tüketici, lockfile ve bilinen açıklar, K6 ile. Her kenar `evidence_ref`, `derivation`, `trust`
  ve `snapshot_id` taşır; iki ucundan birine dokunan diff kenarı `stale` yapar. Haritayı çıkaran
  ajan ile kullanan ajan ayrı bağlamda koşar. Bir avcının yazdığı aday kenar, statik analiz ya da
  test onu doğrulayıp `trust: verified` yapana kadar hiçbir avcıya verilmez; exit koşularından önce
  harita dondurulur.
- **Kapsama haritası** `map/coverage.jsonl`'dadır: her döngü her dosyaya bir kader yazar (hangi
  basamak gördü, hiçbiri görmedi, kaba); Aşama 1'de açılır. Görülmeyen dosya payı birinci sınıf
  sayıdır ve `status.md`'nin tepesindedir.
- Memory'de duran hiçbir şey kanıt değildir (Y1). Memory nereye bakılacağını söyler.

**Zincirli defterler.** Her defter yalnız sonuna eklenen JSONL'dir; her satır `prev_hash` ve
`row_hash` taşır. `row_hash`, RFC 8785 ile kanonikleştirilmiş satırın ve önceki hash'in
SHA-256'sıdır. Her döngü sonunda tüm defterlerin son hash'lerinden bir kök hash türetilir ve
`chain/root.jsonl`'a eklenir.

- **Zincirin güvencesi dışarıdan gelir.** Satırları ve kökü hakem işleri yazar; `brain/state`'e
  her yazım PR ile ve yalnız-ekleme zorunlu kontrolüyle girer (`01b`). Her kök hash, hakem App'inin
  imzasıyla mühürlü depoya attestation olarak yazılır; attestation beyin SHA'sını, hakem SHA'sını,
  koltuk özetlerini ve `policy.json` hash'ini de bağlar. `row_hash` küçük harf onaltılık SHA-256'dır;
  ilk satırın `prev_hash`'i 64 sıfırdır.
- **Zincir kırığı dondurmadır.** Hash uyuşmazlığı bulunursa defter salt okunur olur, Gözcü
  yumuşak dondurma yazar, kırığın satırı ve commit'i raporlanır. Kırık düzeltilmez; kırığın
  kendisi yeni bir satır olarak yazılır.
- **Geçmişe sorgu.** `chain.asof <tarih|sha>` herhangi bir an için durumu kurar: ACTIVE
  organlar, itibarları, kapsama, açık property'ler, değer / USD, eşikler. `status.md`'nin
  "geçen yıl bugün" bölümü bu araçtan üretilir.
- **Silme yoktur, emeklilik vardır.** Hiçbir organ tanımı, bulgu, ders ya da puan zincirden
  silinmez; RETIRED, `withdrawn` ya da `superseded` satırıyla kapatılır. Eski satırlar değişmez
  blob olarak arşivlenir, hash'i zincirde kalır; arşivleme de bir satırdır.
