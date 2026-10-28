# Araç İmzaları: Aşama 0 ve 1

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: taslak · Sahibi: operatör
Okunma: araç yazarken ve çağırırken
Çapa: beklemede: aşama 0 — hakem ve beyin MCP araç tanımları

---

Her araç `{input, output, side_effects, allowed_callers}` ile tanımlıdır; `allowed_callers` boş
araç yoktur. "Hakem işi", hakem reposunun CI'ında koşan iştir.

| Araç | Yer | Girdi | Çıktı | Yan etki | Çağıran |
|---|---|---|---|---|---|
| `cases.build` | Hakem | sınıf, kaynak (geçmiş, mutasyon), gizli tohum | dev vakaları; held-out mühürlü depoya | `cases/`, mühürlü depo | hakem: hazırla |
| `snapshot.make` | Hakem | `base_sha`, vaka listesi, tür (planted, clean, kanarya) | `snapshot_id`, manifest | geçici dizin | hakem: hazırla |
| `harness.score` | Hakem | bulgu dosyası, `snapshot_id` | harness raporu (`26`) | rapor; held-out için mühürlü görünüm | dev: Kurucu; held-out: hakem exit |
| `harness.baseline` | Hakem | `snapshot_id`, property | bulgu dosyası | yok | hakem |
| `spec.lint` | Hakem | spec dizini | ihlal listesi | yok | Kurucu, hakem kilit |
| `ledger.append` | Hakem | bölüm, satır | `row_hash` | `brain/state` PR'ı | hakem işleri |
| `chain.verify` | Hakem | dal ya da commit | geçerli / kırık satır | yok | herkes |
| `chain.asof` | Hakem | tarih ya da SHA | o anki görünümler | yok | herkes |
| `secrets.scan` | Hakem | diff, satır, prompt | eşleşmeler | koşuyu geçersiz kılabilir | dispatcher, kapı |
| `drift.check` | Hakem | — | kurulum özetiyle fark | sert durma | hakem döngü başı |
| `oracle.run` | Hakem | bulgu, düzeltme worktree'si | kırmızı/yeşil hash'leri, kapsama | rapor | hakem |
| `gate.check` | Hakem | PR | durum kontrolü | merge | hedef repo tetiği |
| `profile.propose` | Beyin | hedef repo | profil önerisi | PR | Kurucu, `snowball init` |
| `lint.discover` | Beyin | `snapshot_id` | bulgu dosyası | yok | dispatcher |
| `fixer.run` | Beyin | bulgu | worktree diff'i | worktree | dispatcher |
| `merge.request` | Beyin | worktree, bulgu | PR | PR | dispatcher |
| `map.build` | Beyin | `snapshot_id` | harita (a) kenarları, kapsama | aday satırlar | dispatcher |
| `docs.render` | Beyin | defter görünümleri | sayfalar | `docs/` PR'ı | hakem döngü sonu |
| `docs.index` | Beyin | spec ve `docs/` dizini | `INDEX.md` | PR | hakem döngü sonu |
| `status.render` | Beyin | defter görünümleri | `status.md` | PR | hakem döngü sonu |

Beyin araçlarının yazdığı her şey ya bir PR'dır ya da bir worktree'dir; `brain/state`'e doğrudan
yazamaz. Hakem araçları oyuncu kodu koşturmaz; oyuncu kodu yalnız sırsız işlerde koşar (`08` 1).
