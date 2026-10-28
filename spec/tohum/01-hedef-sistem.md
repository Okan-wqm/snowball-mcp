# Hedef Sistem

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: taslak · Sahibi: operatör
Okunma: ilk oturumda
Çapa: profile.json; status.md amaç tablosu

---

Son durumda sistem şu döngüyü kendi başına döndürür:

```
Discover → Plan → Execute → Approve → Learn → Cheapen → Discover again
```

- Birden fazla memory'si vardır; her memory'nin yazarı, okuyucusu ve okuyucunun değiştirdiği
  kararı vardır (`16-hafiza-modeli.md`).
- Yeni adapter, skill, ajan, memory ve property'yi ihtiyaç ölçüldüğünde kendisi ekler
  (`17-kas-buyutme-sinyalleri.md`, `12-genesis.md`).
- Her parçası canlı yolda ölçülmüştür. Hiçbir adımda insan onayı beklemez (Y8).
- Bulduğu her hata sınıfını bir sonraki sefer daha ucuza bulmanın yolunu dener (Y9).
- Öğrendiğini planlayıcıya ve implementer'a verir (`22-dersler.md`).

Bu son durumdur, başlangıç değil.

**En basit döngü.** Döngü en basit hâliyle başlar: profildeki lint aracını saran tek bir adapter,
aracın kendisi olan bir oracle, bir defter. İlk döngüde keşif için LLM yoktur; LLM yalnız aracın
düzeltemediği bulguyu düzeltmek için girer. Sonraki her özellik bir mikro görevdir: tek canlı
koşuda test edilebilecek kadar küçük, hemen ölçülür, sonra bir sonraki. Binlerce satırlık bir
parça tek seferde gelmez.

**Amaç.** Bağlandığı repodaki her modülü altı boyutta profesyonel hâle getirmek ve orada tutmak.
Modülün notu en zayıf boyutudur, ortalaması değil. Boyutlar alan bağımsızdır; ölçüleri profilden
gelir.

| Boyut | Ölçüsü |
|---|---|
| Güvenli | Yetki sınırları kanıtlı, girdi sınırda doğrulanmış, sır sızıntısı sıfır, denetim izi tam |
| Performanslı | Ölçülmüş darboğazlar, tanımlı hedefler, kaynak sızıntısı yok |
| Sürdürülebilir | Katman kuralları ihlalsiz, her gerçeğin tek sahibi var, ölü kod sıfır |
| Test edilebilir | Her davranışın CI'da koşan gerçek bir testi var |
| Dokümante | Doküman var olanı anlatır, koddan doğrulanabilir, bayatlaması bir kapıyı kırmızıya boyar |
| Doğru | Sözleşmelerin iki ucu tutarlı, uçtan uca zincir kanıtlı |

Beyin bu repoyu değil, herhangi bir repoyu hedefler; repoya özgü her şey `21-cok-repo.md`'deki
kurala tabidir.
