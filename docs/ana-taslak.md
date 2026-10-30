# Ana taslak: alandan bağımsız çekirdek

Snowball'un "kod" uygulaması, alandan bağımsız bir çekirdeğin ilk örneğidir. Sahip (2026-10-29): bu çekirdek her şey
bittiğinde başka alanlara (örneğin hukuk) uyarlanmak üzere korunur. Anlık görüntü: git etiketi `ana-taslak-2026-10-29`.
Kural: bundan sonra çekirdek ile alana özel parçalar karıştırılmaz; her şey bitince çekirdek ayrı bir şablon reposuna
çıkarılabilmelidir.

## Çekirdek (her alanda aynı)

| Parça | Bugün nerede | Görevi |
|---|---|---|
| Oyuncu ve hakem ayrılığı | `spec/tohum/01a`, `29b`; beyin ve hakem repoları | Üreten, kendini yargılayan değildir; oyuncu hakemi değiştiremez |
| Rakip ve kanıt kuralı | `seed/bootstrap/snowball_bootstrap/rival.py` (`PROTOCOL`) | Çürütme ancak yeniden üretilebilir kanıtla sayılır; kanıtsız iddia açık iddia olarak saklanır |
| Kabul kuralı ve kapalı varsayılan çıkış | `decide.py`, `asama-0/10`, E162 | Denetlenmeyen koşul çıkışı kilitler |
| İki kör bağımsız hesap | `docs/eksik-kaydi.md` E161, `29d` | Beklenen değer iki bağımsız hesabın uyuşmasıyla girer |
| Hash zincirli defter, imzalı kararlar | `ledger.chain`, Sigstore/Rekor, `tohum/13`, `26` | Değiştirilemez hafıza ve denetim izi |
| Tohum, aşama protokolü, tohum dönemi | `tohum/02`, `25`, E88, `seed/founder/README.md` | İnsan onay noktaları; yaşayan sisteme kural teslimi |
| Kapsül ve başlatıcı | `seed/founder/` | Oyuncunun yalıtılmış çalışması, döngü, ölçüm (`pilot-metrics.jsonl`) |
| İlkeler | `seed/founder/prompt.md` | Vaat kadar kanıt; kök neden, gizleme yok; tek kaynak; belge ipucudur; anlaşmazlık kanıtla; eksiğini kendin bul; kendi fikrin |
| Ölçüm | `docs/pilot-gunlugu.md`, operatörün fikir ölçütü | Sistemin kendi bulduğu, geri gelen hata, insan yardımı |
| Sistem haritası | [`docs/harita.md`](harita.md), `seed/bootstrap/local/system_map.py`, E301 | Ne nereye bağlı: koddan üretilen, insan okur çizim; kodla uyuşmazsa test kırmızı |
| Öğretmen döngüsü | E304, operatörün hafızası | Operatör sistemin alanındaki kusuru düzeltmez, ipucu vermez; sistem bir şeyi bulamazsa nedenini beş halkayla arar (görebiliyor muydu, görevi var mıydı, zamanı yetti mi, hafızası taşıdı mı, geri bildirim var mıydı) ve ilk kopan halkayı onarır, cevabı değil; yalnız yaşam desteği, anayasa, sınav ve ölçüm operatörde kalır |

## Alana özel (kod)

Aşama 0'ın 18 mikro özelliği (`asama-0/14`), vektör grupları ve arayüzleri (`29d`, `29f`–`29k`, `29m`–`29o`), sır tarayıcı,
profil, bağımlılık ve kilit denetimi, birim tarifi, kapı kuralları (`asama-0/08`), güvenlik kataloğu (`30`–`30f`),
mimari ilkeler kataloğu (`31`–`31h`), hedef repo.

## Başka bir alana uyarlarken sorulacaklar

Her çekirdek parçanın o alandaki karşılığı nedir: "test" ve "yeniden üretici" neye karşılık gelir (hukukta örneğin
doğrulanabilir atıf ve onu çürüten kaynak), "hedef" nedir, insan onay noktaları kimdir, neyin sırrı korunur. Bu
uyarlamayı sistemin kendisi tasarlamalıdır; bu sayfa yalnız neyin korunacağını söyler.
