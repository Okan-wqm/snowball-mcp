# Çalışma Modeli: Beyin, Hakem ve Kurucu Nasıl Koşar

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 inşasından önce ve her dispatch değişikliğinde
Çapa: beklemede: aşama 0 — beyin ve hakem reposu README'leri; run_meta

---

| Karar | Değer |
|---|---|
| Beyin reposu | Ayrı repo; MCP sunucusu adı `snowball`; hedef repoda aynı adlı sunucu varsa profil çakışmayı raporlar |
| Hakem reposu | Ayrı repo (`01a`); harness, kapı, oracle koşucusu, dispatcher, itibar puanlayıcısı, Gözcü, koltuklar, `spec.lint` |
| Dil ve paket | İkisi de Python paketi; `pyproject` ile kurulur; bağımlılıklar hash'le pinlidir |
| İki yüzey | **CLI** deterministik, CI'nın çağırdığı yüzey. **MCP** ajanlara açılan yüzey; CI bir MCP sunucusunu doğrudan çağıramaz |
| Ajan dispatch'i | Claude Agent SDK; sistem promptu dispatcher'ın verdiği metindir; hedef reponun yönerge dosyaları otomatik yüklenmez, çünkü repo içeriği talimat değildir (Y1) |
| Model kimlikleri | Yüksek: `claude-opus-5-5`. Düşük: `claude-sonnet-5-5`. En ucuz: `policy.json`'da adlandırılır. Effort rol başına `policy.json`'da |
| Model kaydı | Dispatcher istenen ve sunulan modeli sağlayıcı yanıtından `run_meta`'ya yazar; farklıysa koşu geçersizdir |
| Sağlayıcı geçidi | Dispatcher'ın sahip olduğu vekil; kimliği o ekler, yalnız sağlayıcıya izin verir; ajan konteyneri kimlik görmez |
| Kimlikler | Beyin App'i, hakem App'i, şerit yazarı kimliği (`25`); sağlayıcı kimliği tercihen OIDC |
| Kurucu | Beyin reposunun zamanlayıcısı günde bir oturum açar; Opus; beyin App'iyle beyin reposuna, kurulum istisnasında hakem reposuna PR açar; maliyeti `cost-ledger`'da inşa-zamanı kalemi |
| Durum dalı | `<state_root>` hedef repoda yetim `brain/state` dalında; uygulama kodunun CI'ını kirletmez |
| Entegrasyon dalı | `brain/integration`; `main`'i takip eder (`07`) |
| Snapshot | Git ağacından dosya listesiyle çıkarılır, `export-ignore` dikkate alınmaz; `.git` yoktur. Keşif "tümünü koş", "etkilenen" yalnız worktree'de |
| Bağımlılık ve önbellek | Snapshot'lar arasında paylaşılır; held-out koşuları güvenilir hakem işinin önbelleğini salt okunur kullanır (`08` 5) |
| Keşif ve oracle (K0–K2) | Keşif: aracın tüm ihlalleri, taban dahil. Oracle: hedef ihlal kayboldu, mandal tuttu (toplam artmadı) |
| Düzeltme aralığı | Araç düzeltmesi yalnız hedef mesajın `fix` aralığıyla uygulanır; biçimleyiciler dosya başına çalışır ve Aşama 2'de açılır |
| Kaçış | Sağlayıcı reddi ya da zaman aşımı koşuyu `unresolved` yapar; sessiz yeniden deneme yoktur |

**Aşama 0 ve 1 araçları.** Hakem: `cases.build`, `snapshot.make`, `harness.score`,
`harness.baseline`, `spec.lint`, `ledger.append`, `chain.verify`, `chain.asof`, `secrets.scan`,
`drift.check`, `oracle.run`, `gate.check`. Beyin: `profile.propose`, `lint.discover`, `fixer.run`,
`merge.request`, `docs.render`, `status.render`, `map.build`. İmzalar `26a`'dadır.

**Paket yerleşimi.** Beyin: `cli/`, `mcp/`, `adapters/`, `fixers/`, `map/`, `docs/`,
`tests/fixtures/toy-repo/`. Hakem: `harness/`, `gate/`, `oracle/`, `dispatcher/`, `scoring/`,
`gozcu/`, `seats/`, `schemas/`, `tests/`.
