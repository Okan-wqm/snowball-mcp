# Mimari ve Yetki: Dört Yer

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: taslak · Sahibi: operatör
Okunma: ilk oturumda ve her yeni repoya bağlanırken
Çapa: beklemede: aşama 0 — hakem reposu korumalı dalı; brain/state ruleset'i

---

GitHub'da bir repo içinde dosya bazlı izin yoktur. Oyuncu kendi hakemini yazamasın diye yetki
dört ayrı yerde durur.

| Yer | İçerik | Kim yazar |
|---|---|---|
| **Beyin reposu** (oyuncu) | MCP sunucusu, CLI, adapter'lar, düzelticiler, avcılar, planlayıcı, doküman üreticisi | Kurucu, PR'larla |
| **Hakem reposu** | Kapı, harness (vaka üretici, snapshot, puanlama, taban avcı, `spec.lint`), oracle koşucusu, dispatcher, itibar puanlayıcısı, Gözcü, rakip ve oracle koltuk tanımları, kayma denetimi | Kurulum istisnası dışında yalnız şerit yazarı, PR ile; merge'ü görevdeki kapı yapar |
| **Hedef repo** | `brain/state` dalında `<state_root>`; `brain/integration` dalı; beyni çağıran iş akışı | Hakem işleri, tipli kurallarla (`01b`) |
| **Mühürlü depo** | Held-out vakalar ve yedek havuz, mühür, mühürlü görünümler, kurulum özeti, kök hash attestation'ları, K6 artefaktları | Yalnız hakem exit, rotate ve attestation işleri |

**Beyin bir MCP sunucusudur.** Repo-bağımsız koddur. Hedef repoya bağlanınca `<state_root>` açar
(varsayılan `.brain/`). Beyin repoda ne bırakacağını önceden bilmez: her dosya ancak okuyucusu
doğunca açılır (Y4), okuyucusu kalmayınca canlı yoldan çıkar.

**Hakem, oyuncudan ayrıdır.** Beynin GitHub App'i hakem reposunda yalnız okuma ve PR açma iznine
sahiptir; `workflows` izni hiçbir yerde yoktur. Hedef repodaki kapı, repo ruleset'inde zorunlu bir
durum kontrolüdür ve kaynağı **hakem App'i** olarak sabitlenmiştir: kontrolü başka hiçbir kimlik
raporlayamaz. Bu, kullanıcı hesabındaki repolarda da çalışır; org düzeyi kural gerekmez. Kontrolü
hakem reposunun kendi CI'ı koşar: hedef repodaki tetik bir olay gönderir, hakem işi PR'ı kendi
işinde çeker, kapıyı koşturur ve sonucu hakem App'iyle yazar. Hakem reposuna merge yalnız
görevdeki kapının adayı doğrulamasıyla olur: adayın kendi testleri yeşil, arşiv yeniden
oynatması geçmiş bir kararı gevşetmiyor, farklı modelden rakip çürütemiyor. Böylece kapı
halefini kendisi doğrular ve hiçbir insan pin güncellemez.

**Şerit yazarı** hakem reposuna PR açabilen tek ajan kimliğidir. Kurucu değildir, Kurucu'nun
defterini görmez, kendi promptu ve kimliği vardır; değişiklik gerekçesini yalnız hakem
raporlarından ve kanaryalardan alır (`09a`).

**Genellik testi.** Beyin ve hakem, kendi testlerinde boş bir oyuncak repoya bağlanır ve
`<state_root>` sıfırdan büyür. Beyin koduna, hakem koduna ya da tohum sayfalarına hedef repoya
özgü bir yol, araç ya da karar belgesi adı sızmışsa test kırmızıdır.

**Kurulum.** `25` inşadan önceki, `25a` Aşama 0 çıkışındaki operatör işidir. Bundan sonra döngü
içinde insan yoktur; kurulumun bozulmadığını her döngü hakem kayma denetimi doğrular.
