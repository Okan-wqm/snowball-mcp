# Aşama 1 §1.13 — Aktarım partileri

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör (sıra: sahip kararı (2026-11-20), `tohum/26h`)
Okunma: Aşama 0 çıkışından sonra, her parti yazılırken ve aktarılırken
Çapa: beklemede: her partinin `imports.jsonl` satırı ve (B) satırı

---

Aşama 0 yalnız ilk canlı döngünün okuduğu 18 mikro özelliği kurar (`asama-0/14`). Hakemin geri kalanı,
ilk okuyucusundan hemen önceki bir **parti** ile gelir (Y4). Parti, aşama çıkışındaki (A) → aktarım → (B)
protokolünün dar hâlidir (`tohum/01a`, `tohum/02`):

1. Kurucu partinin MF'lerini beyin reposunda `referee/` altında yazar; önyükleme hakemi her push'u Aşama
   0'daki gibi yargılar (testler, vektörler, modülsüz kırmızı, rakip). Partinin tablosu tohumdadır
   (`seed/bootstrap/stages/`) ve `setup/stage.json` açtıktan sonra geçerlidir.
2. MF'ler bitince Kurucu parti çıkış isteğini yapar; (A) önyükleme hakeminin imzalı sonucudur.
3. Operatör aktarır (insan dokunuşu); aktarım önyükleme hakemine dokunmaz.
4. (B): döngü hakemi partinin ilk okuyucusunu canlı koşar; kırmızıysa operatör aktarımı geri alır.

| Parti | Ne zaman | İlk okuyucu |
|---|---|---|
| P1 organ ve ölçüm | Aşama 1 MF1'in canlı koşusundan önce | Aşama 1 MF1 `lint.discover`'ın dev ölçümü; Aşama 1 MF5'in özerk döngüsü; P1 MF8'in bulgu satırlarını Aşama 1 MF1'in keşfi, P1 MF9'un izin listesini Aşama 1 MF5'in reddi ve Aşama 1 MF6'nın `accept` satırı okur |
| P2 güvenlik gözlemi | Aşama 1 içinde, P1'den sonra | Aşama 1'den güvenlik profili ve testi (`tohum/30d`) |
| P3 ertelenenler | Aşama 1 MF6'dan (ilk organ merge'ü) ve P2'den sonra, MF4'ten önce (`tohum/26h`) | Aşama 1 MF4 `fixer.llm`'in canlı koşusu |
| Aşama 1 çıkışı | Aşama 1 (A) ile (B) arasında | Aşama 1 (B)'nin kural sayımı; Aşama 2 spec isteği |
| Aşama 2 | Aşama 2'nin ilk partisi, ders görünümünden önce | ders provası (`tohum/22a`), sahibin MVP sınavı (`tohum/22b`) |
| Aşama 4 | ilk LLM avcısından önce | taban kıyası |

| Parti | MF | Mekanizma | Test (`asama-0/09`) | Vektör grubu |
|---|---|---|---|---|
| P1 | 1 | Organ koşucusu: `koş`ta yalnız kabul edilmiş organların giriş noktaları | 51 | — |
| P1 | 2 | `snapshot.make` (§1.13c) | 8 | — |
| P1 | 3 | K0 mutasyon kataloğu, `cases.build` (dev), hunk eşleme (§1.13a; eşleme kuralı `asama-0/08`) | 2, 4 | — |
| P1 | 4 | `harness.score`, match-rule v2'nin K0 dalı, istatistik (§1.13e); `26a` ile `29a` CLI'si önce uyumlanır | 1, 6, 7, 28 | `match`, `cp_lower`, `mcnemar` |
| P1 | 5 | LLM yokluğu ve `<state_root>`'un sıfırdan büyümesi | 9, 11 | — |
| P1 | 6 | `drift.check`, her devir (`tohum/21`) | 24 | — |
| P1 | 7 | `gozcu.evaluate` (`tohum/28`) | 41 | — |
| P1 | 8 | Bulgu yazıcısı `findings.write`: `findings.jsonl` ve `unresolved.jsonl`, parmak izi ve durumlar (§1.13d; `tohum/26h`, `tohum/26j`) | 12 | `root_files` |
| P1 | 9 | İzin listesi ve `accept` yazıcısı `gate.allowlist` (`tohum/26h`, `tohum/26j`) | 55 | — |
| P1 | 10 | `koş` bir organın çıktısını koşu sonuçlarında tutar (`tohum/26j`) | 56 | — |
| P1 | 11 | `koş` bir çalışma-zamanı adayını kapıdan önce yeniden koşar (`tohum/26j`) | 57 | — |
| P1 | 12 | `yaz` `candidates/<id>/`'yi sonuçlardan hash'iyle okur (`tohum/26j`) | 58 | — |
| P2 | 1 | `security.derive` ve `security.run` (`tohum/30d`) | `30d`'nin profil testleri | — |
| P3 | 1 | `operating{}` sınırlarının bant içinde ayarı (`tohum/18a`); sahip kararıyla ertelendi (`tohum/26h`) | 52 | — |
| P3 | 2 | Düzeltme gidiş-dönüşü `koş` → `çağır` → `koş` (§1.5 3; `tohum/26h`) | P3'ün tablosuyla | — |
| Aşama 1 çıkışı | 1 | `exit.sample` (§1.13a); payda tohumun `census` vektörü (`tohum/29za`) | 27 | `census` |
| Aşama 1 çıkışı | 2 | `spec.lint` (`tohum/02` listesi) | 33 | — |
| Aşama 1 çıkışı | 3 | `exit.adversarial`: düzeltici istemine prompt injection, kaçan diff, gizlenmiş ya da kodlanmış sır (`tohum/29za`, E648) | 54 | — |
| Aşama 2 | 1 | Ders provası yargıcı `harness.drill` (`tohum/29c`) | 25'in ders kısmı | `drill` |
| Aşama 4 | 1 | `harness.baseline`; grep kümesi tohumdan, hash'i özette | 32 | — |
| Aşama 4 | 2 | Snapshot kanaryası, clean ve planted (Aşama 1 çıkışından taşındı, `asama-4/13`) | 16 | — |

Oyuncu parçaları partiye girmez: `profile.propose` (test 31) ikinci birim ya da ikinci hedef bağlanırken
gelir; `docs.index` (test 44) Aşama 1 MF7'de `docs.render` ile gelir (§1.6).

**Aşama 0 2.2'nin 30 MF'sinin yeri.** Aşama 0'da kalanlar (eski → yeni MF): 1 → 1, 5 → 4, 13 → 3, 14 → 5 (npm), 15 →
7, 16 → 8 ve 9, 17 → 12, 18 → 13 ve 14, 20 → 15, 21 → 2, 23 → 10, 24 → 11, 26 → 16, 30 → 18 (taklit API). Yeni:
`unit.verify` (6), iş akışı (17). Partilere: 6, 7, 9, 11 (LLM yokluğu), 19, 25 → P1; 22 → araç kullanan ilk
çalışma-zamanı ajanı (en geç Aşama 4, `tohum/30f`); 8, 12 → Aşama 1 çıkışı; 18'in ders provası → Aşama 2; 10 → Aşama
4; 29 → Aşama 1 MF7; 4 → ikinci birim ya da hedef. Tohuma: 2 (Kurucu defteri aracı), 3 (`control` komutu), 11'in ad
denetimi (`asama-0/10` #genellik), 27 (`brain.accept`: önyükleme hakemi itme yargıcı kalır; `accept` satırını P1 MF9'un
yazıcısıyla döngünün `yaz`'ı yazar, ilk kez Aşama 1 MF6'da), 28 (`lock.check`: önyükleme hakeminin aşama kapısı `setup/stage.json`).