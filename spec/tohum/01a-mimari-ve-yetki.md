# Mimari ve Yetki: Beyin, Hedef Repo, Mühürlü Depo

Tarih: 2026-10-28 · Sürüm: 2.0 · Durum: taslak · Sahibi: operatör
Okunma: ilk oturumda ve her yeni repoya bağlanırken
Çapa: beyin reposundaki zorunlu iş akışı SHA'sı; <state_root>/profile.json; genellik kendi-testi

---

GitHub'da bir repo içinde dosya bazlı izin yoktur. Bu yüzden yetki üç ayrı yerde durur ve "depo
izni zorlar" cümlesi yalnız bu üçlü için doğrudur.

| Yer | İçerik | Kim yazar |
|---|---|---|
| **Beyin reposu** | Beyin kodu (MCP sunucusu, harness, oracle koşucusu, dispatcher, puanlayıcı, Gözcü), SHA-pinli zorunlu CI iş akışı | Kurucu, kendi PR'larıyla; harness şeridi ayrı |
| **Hedef repo** | `<state_root>`: profil, defterler, zincir, dev vakalar, organ tanımları, dersler, üretilmiş dokümanlar; beyni çağıran CI dosyası | Beyin, bot kimliğiyle ve kapıdan |
| **Mühürlü depo** | Held-out vakalar, mühür, mühürlü görünümler, kök hash attestation'ları | Yalnız CI'daki exit ve rotate işleri; beynin App'i okuyamaz |

**Beyin bir MCP sunucusudur.** Repo-bağımsız koddur. Hedef repoya bağlanınca `<state_root>`
açar (varsayılan `.brain/`; Kurucu belirler, profile yazar). Beynin kodu bu dosyalara bağımlı
değildir; verisi bu dosyalardır. Beyin repoda ne bırakacağını önceden bilmez: her dosya ancak
okuyucusu doğunca açılır (Y4), okuyucusu kalmayınca canlı yoldan çıkar.

**Kapı, beyin reposundan gelir.** Hedef repodaki merge ve kilit kapısı, org kuralıyla zorunlu
kılınmış ve SHA ile pinlenmiş bir iş akışıdır; ayrı bir GitHub App altında koşar ve beynin App'i
`workflows` iznine sahip değildir. Böylece bir PR kendi kapısını düzenleyemez. Kapı şu yollara
dokunan diff'leri reddeder: `.github/**`, lint, tip ve test yapılandırmaları, lockfile'lar,
`<state_root>/{cases*,heldout*,chain/*,policy.json}`.

**Tetik.** Hedef reponun CI zamanlayıcısı tam döngüyü, her `main` push'u yalnız ucuz
basamakları çağırır. Tetikler aktöre göre süzülür: beynin kendi push'u beyni tetiklemez. CI
işinin zaman aşımı beynin dışındaki watchdog'dur.

**Döngü bir işlemdir.** Her döngü deftere başlangıç ve bitiş satırı yazar. Bitiş satırı olmayan
döngü çökmüş sayılır; sonraki döngü önce onun worktree'lerini ve kiralarını temizler.

**Genellik testi.** Beyin, harness'in kendi testlerinde boş bir oyuncak repoya bağlanır ve
`<state_root>` sıfırdan büyür. Beyin koduna ya da tohum sayfalarına hedef repoya özgü bir yol,
araç ya da karar belgesi adı sızmışsa test kırmızıdır. Beyin, bu repo için yazılmış değil, bu
repoya bağlanmış bir sistemdir.

**Kurulum, bir kez.** Operatör beyin reposunu ve App'ini açar, hedef repoda branch protection
ve zorunlu iş akışını kurar, mühürlü depoyu ve secret store'u açar, beyni ilk kez başlatır.
Bundan sonra döngü içinde insan yoktur.
