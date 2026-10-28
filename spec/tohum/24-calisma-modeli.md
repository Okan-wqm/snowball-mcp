# Çalışma Modeli: Beyin Nasıl Koşar, Ajanlar Nasıl Dispatch Edilir

Tarih: 2026-10-28 · Sürüm: 2.0 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 inşasından önce ve her dispatch değişikliğinde
Çapa: beyin reposu README; run_meta model ve effort alanları

---

Bu sayfa Kurucu'nun aksi hâlde kendi başına vereceği ve yanlış verince aşamayı kıracağı
kararları sabitler.

| Karar | Değer |
|---|---|
| Beyin reposu | Ayrı repo; MCP sunucusu adı `snowball`; hedef repoda aynı adlı başka sunucu varsa profil çakışmayı raporlar |
| Dil ve paket | Python paketi; `pyproject` ile kurulur; tek giriş `snowball` CLI |
| İki yüzey | **CLI** deterministik ve CI'nın çağırdığı yüzeydir (`snowball cycle`, `harness score`, `chain verify`). **MCP** ajanlara açılan yüzeydir; CI bir MCP sunucusunu doğrudan çağıramaz |
| Ajan dispatch'i | Claude Agent SDK; sistem promptu beynin verdiği metindir; hedef reponun yönerge dosyaları otomatik yüklenmez (ayar kaynakları kapalı), çünkü repo içeriği talimat değildir (Y1) |
| Model ve effort | Rol başına açık: model kimliği ve effort `run_meta`'ya yazılır; sağlayıcının sunduğu model istenenle aynı değilse koşu geçersizdir (sessiz model değişimi kimliği değiştirir) |
| Kimlik bilgileri | GitHub App kurulum token'ı koşu başına mint edilir; model sağlayıcı kimliği CI'nın OIDC federasyonundan, yoksa CI sırrından; ikisi de ajan konteynerine girmez |
| Koşucu | Kapı ve exit işleri sağlayıcı barındırmalı koşucuda; ajan koşuları egress günlüğü ve konteyner özeti alınabilen bir koşucuda. Profil koşucuyu beyan eder; Y10 kanıtı alınamayan koşucuda ajan koşusu yapılmaz |
| Durum dalı | `<state_root>` hedef repoda yetim dal `brain/state` üzerinde yaşar, gitignore'lu bir worktree'ye açılır; uygulama kodunun CI'sını, lint'ini ve testini kirletmez. Held-out ve mühür mühürlü depodadır |
| Entegrasyon dalı | `brain/integration`; `main`'i takip eder (`07`); ruleset'i kurulum gününde operatör kurar |
| Snapshot ve bağımlılık | Snapshot `.git`'siz arşivdir; keşif "tümünü koş" ile çalışır, "etkilenen" yalnız worktree'de. Bağımlılık kurulumu ve derleme önbelleği snapshot'lar arasında paylaşılır; profil önbellek yolunu bildirir |
| Keşif oracle'ı (K0, K1) | "Araç yeşil" değil, **fark**: base SHA'ya göre yeni (kural, satır) yok ve önceden var olan ihlal sayısı artmamış. Zaten kırmızı bir projede araç hiç yeşile dönmez; fark dönebilir |
| Düzeltme aralığı | Araç `--fix` tüm dosyayı düzeltir; düzeltici yalnız hedef mesajın araç çıktısındaki `fix` aralığını uygular. Biçimleyiciler dosya başına çalışır ve ayrı bir K0 alt sınıfıdır |
| Kaçış | Sağlayıcı reddi ya da zaman aşımı koşuyu `unresolved` yapar; sessiz yeniden deneme yoktur |

**Aşama 0 ve 1 MCP araçları.** `cases.build`, `snapshot.make`, `harness.score` (held-out yalnız
CI exit işinden), `harness.baseline`, `spec.lint`, `ledger.append`, `chain.verify`, `chain.asof`,
`lint.discover`, `fixer.run`, `oracle.run`, `merge.request`, `docs.render`, `status.render`.
Her aracın imzası `26-semalar.md`'de.

**Paket yerleşimi.** `cli/`, `mcp/`, `harness/` (ayrı şerit), `adapters/`, `fixers/`,
`oracle/`, `ledger/`, `docs/`, `tests/fixtures/toy-repo/`. Harness dizini paket içinde ayrı
sahiplik ve ayrı şerittedir (`02`).
