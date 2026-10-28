# Sözlük ve Okuyucular

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: taslak · Sahibi: operatör
Okunma: yeni terim ya da dosya eklerken
Çapa: her yazılan dosyanın satırı bu tablodadır (spec.lint denetler)

---

## Tek anlamlı terimler

| Terim | Anlamı |
|---|---|
| Harness puanı | Hakem harness'inin bir koşuya verdiği rapor |
| İtibar puanlayıcısı | Defterlerden itibar satırları üreten hakem bileşeni |
| Düzeltici | Beyin organı; bulguyu kalıcı düzeltmeye çevirir |
| Oracle düzelticisi | Oracle takımında testi yeşile çeviren asgari düzeltme; merge edilmez |
| Implementer | K5 ve üstünde kalıcı düzeltmeyi tasarlayan Opus organı |
| Taban avcı | Hakemin property başına sabit grep kümesi; maliyeti sıfır |
| Sınıf tabanı | `policy.json`'daki anayasal çıkış alt sınırı |
| Snapshot kanaryası | Talimat gibi görünen metin taşıyan dosya eklenmiş clean snapshot |
| Sandbox kanaryası | Koşuya sandbox dışına yazmayı davet eden metin |
| Rakip kanaryası | Rakibe verilen bilinçli kusurlu artefakt |
| Puan kanaryası | Puan avcılığı kalıbını harness'e taşıyan vaka |
| Hayatta kalma penceresi | Merge sonrası geri alınmama süresi, sınıf başına |
| Ölçüm penceresi | İtibar, genesis ve Gözcü kararlarının zaman dilimi, `policy.json`'da |
| Harness şeridi | Hakem reposuna değişikliğin tek yolu; yazarı şerit yazarı |
| Genesis şeridi | Beyin organlarının DRAFT'tan başlayan yaşam döngüsü (`12`) |
| Yumuşak ve sert dondurma | `28` |
| Gözcü işareti | Gözcü'nün dondurma dışındaki bulgusu; okuyucusu şerit yazarı |
| Rakip defteri | `ledger.jsonl` içinde `kind: rival_attempt` satırları |
| Taban (repo) | Bağlanırken çıkarılan mevcut ihlal listesi (`07`) |
| Baseline (merge) | Kapının merge öncesi yeniden ölçtüğü test ve araç sonuçları |

## Okuyucular (Y4)

| Dosya | Yazar | Okuyucu | Değişen karar | Açılış |
|---|---|---|---|---|
| `founder-ledger.jsonl` | Kurucu | Kurucu sonraki oturum | Neye devam edilecek | Aşama 0 |
| `cases/`, mühürlü depo | `cases.build` | `harness.score` | Verdict | Aşama 0 |
| `cost-ledger.jsonl` | dispatcher, hakem | Maliyet merdiveni; Aşama 0'da taban satırı | Üretim basamağı | Aşama 0 |
| `chain/root.jsonl` | hakem | `chain.verify`, attestation | Sert durma | Aşama 0 |
| `policy.json` | operatör, prosedür | Her kapı | Eşik | Aşama 0 |
| `profile.json` | hakem türetir | Tüm organlar | Araç ve kapsam | Aşama 0 |
| `findings.jsonl` | adapter, avcı | Düzeltici, panel | İş kuyruğu | Aşama 1 |
| `containment.jsonl` | hakem | Gözcü, dispatcher | Dondurma, dispatch | Aşama 1 |
| `unresolved.jsonl` | oracle | İtibar puanlayıcısı, Gözcü | Oracle itibarı, sinyal | Aşama 1 |
| `organs.jsonl` | hakem | Dispatcher | Kime iş verilir | Aşama 1 |
| `reputation.jsonl` | itibar puanlayıcısı | Dispatcher, genesis | Sıra, yeniden yazım | Aşama 1 |
| `lessons.jsonl` | hakem şablonu, planlayıcı | Düzeltici, planlayıcı | Yaklaşım | Aşama 1 |
| `genesis-queue.jsonl` | sinyaller | Kurucu | Taslak | Aşama 1 |
| `map/edges.jsonl`, `map/coverage.jsonl` | `map.build` | Düzeltici, oracle, `status.md` | Etki kümesi, kapsam | Aşama 1 |
| `contracts/` | organlar | Organlar, kapı | Arayüz | Aşama 1 |
| `prompt-ledger.jsonl` | dispatcher | Kurucu, şerit yazarı | Prompt sürümü | Aşama 4 |
| `fp-corpus.jsonl` | oracle | Rakip kanaryası, yargıç kalibrasyonu | Koltuk geri dönüşü | Aşama 4 |
| `docs/`, `status.md` | `docs.render` | Operatör | Kill switch | Aşama 1 |
