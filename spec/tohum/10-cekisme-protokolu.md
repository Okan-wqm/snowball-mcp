# Çekişme Protokolü: Her Artefakt İçin

Tarih: 2026-10-28 · Sürüm: 2.0 · Durum: taslak · Sahibi: operatör
Okunma: her artefakt üretildiğinde
Çapa: faz kararları ve oracle sonuçları defterde

---

Bu protokol tek bir yerde yazılır ve her artefakta uygulanır: spec, property tanımı, bulgu,
düzeltme, adapter, maliyet basamağı, memory türü, yeni ajan, harita kenarı, eşik değişikliği,
harness değişikliği. Şekli her yerde aynıdır; yalnız oracle değişir.

**Şekil.** Bir üretici artefaktı yazar. Üç koltuk onu beş fazda çekiştirir: **Savcı** artefaktın
gerekli ve doğru olduğunu, **Savunma** gereksiz, yanlış ya da zararlı olduğunu, **Uygulayıcı
temsilcisi** neye mal olacağını ve neyi bozacağını kanıtlamakla yükümlüdür. Her fazda kararlar
mühürlenir, sonra açılır; faz başına en fazla iki tur. Son sözü hiçbir zaman oy değil, o
artefaktın yürütme oracle'ı söyler. Üretici koltuklardan hiçbirine oturamaz (Y6); koltuk
modelleri `09a-bagimsizlik.md`'ye uyar.

| Faz | Soru |
|---|---|
| 1 Varlık | Artefakt iyi biçimli mi, referansları snapshot'ta var mı, kendi çıktısına mı dayanıyor. Mekanik, bedava |
| 2 Gereklilik | Bunu isteyen ölçülmüş bir boşluk ya da gerçek bir yol var mı (Y5) |
| 3 Sonuç | Kabul edilirse ne değişir, kim görür; kasıt ya da konvansiyon mu |
| 4 Etki ve maliyet | Etki kümesinde ne var, ne bozulabilir, değer / USD ne, katman iddiası tutuyor mu |
| 5 Yürütme | Oracle koşar ve karar verir |

**Artefakt başına oracle.**

| Artefakt | Faz 5 oracle'ı |
|---|---|
| Aşama spec'i, property spec'i | Yapısal lint + kalıp sızıntısı denetimi; sonra o aşamanın çıkış testi |
| Bulgu (K5 ve üstü) | Üreme testi: kırmızı → düzeltme → yeşil, etki kümesi yeşil (`04a`) |
| Düzeltme, PR | Aynı test + etkilenen-test komutu + diff-guard; sonra ikinci panel diff üzerinde |
| Adapter, dedektör | Harness: held-out recall ve clean precision alt sınırları tabanı geçer |
| Maliyet basamağı | Aynı vakalarda eşli non-inferiority, daha düşük maliyet |
| Memory türü, ders | Okuyucusu bir sayıyı anlamlı oynatır; yoksa canlı yoldan çıkar |
| Yeni ajan | Ölçülmüş boşluk pencerede küçülür |
| Repo haritası kenarı | İki ucu snapshot'ta doğrulanır; stale kenar yeniden doğrulanır |
| Eşik ve harness değişikliği | Arşivde yeniden oynatma: geçmiş skoru yükseltmez, geri alınmışı geçirmez |

**İki sınır.** Oracle yoksa panel yoktur; artefakt `blocked`'dır (Y8). Araç karar veriyorsa
panel yoktur; K0–K2 ve K4'te yargıç aracın kendisidir, panel mekanik kararın bittiği yerde
başlar. Aşama 0 ve 1'de yalnız faz 1, tek rakip ve faz 5 çalışır.

**Panelin maliyet merdiveni.** Faz 1 mekanik ve bedava; faz 2 repo haritası varsa çoğunlukla
mekanik; faz 3 ve 4 keşif basamağında Opus, kalibrasyon oturunca Sonnet; faz 1–2 en ucuz
modelde koşabilir. Bulguların çoğu faz 1 ve 2'de sıfır maliyetle ölmelidir.
