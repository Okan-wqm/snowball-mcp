# Değişiklik Günlüğü — Tohum, Dizinin Arşivi

Tarih: 2026-11-22 · Sürüm: 2.2
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

`CHANGELOG.md`'nin en eski dizin satırları, oradaki 80 satır sınırı için tohum dönemi AF'de ve AO'da taşındı;
içerikleri değişmedi. Yeni girdiler `CHANGELOG.md`'dedir.

- 2.2 (2026-11-16, E600–E605; Kurucu raporları, sahibin onayı): yeni `29z`. Önyükleme hakemi çıkış isteğinde ayrı,
  sırsız ve izinsiz `kanarya` işinde beynin `python -m runner.contained run`'ını konteynerin dışında, oyuncağın birim
  tarifinin imajında bir kez koşturur; geçerli olmayan ya da kırmızı kanarya `exit.missing`'de `canary:<durum>`, iş
  başarısızsa `canary:job_<sonuç>`; sonuç `exit.canary`'de imzalanır (E600–E602). `genesis` grubuna dört vaka (E603).
  Yanıtlanan raporlar: `seed-058-no-real-container-before-b` → `29b:73`, `29z` (komut, istek, okunan, durumlar, kayıt);
  `seed-059-genesis-vector-toy-base-not-setups-form` → `29o:45-46`, `29o:69-76` (kurulumun özetteki biçimi;
  `toy_base_empty`, `toy_base_absent`, `copy_base_empty`, `seed_epoch_seed_null`: `29o:63-67`); `seed-060-app-secret-form-not-stated` → `29s:78-80` (iki sırrın
  adı ve girilişi; `WRITER_APP_ID`'nin çevresindeki boşluk bilinmiyor). (B)'nin beşinci ve altıncı denemesi: `CHANGELOG-7.md`.
- 2.2 (2026-11-14 – 2026-11-15, E585–E599): `29t` kendi haritası, `29u` çıkıştan sonra, `29v` politika okuması,
  `29y` döngü koşuları ve Kurucu'nun hafızasının yeri: `CHANGELOG-8.md`.
- 2.2 (2026-11-12 – 2026-11-13, E569–E574, E577–E582): `29e` "Genellik okuması", hedeflerin `targets.json`'u, yasa
  `00` Y12 "Maliyet", başlatıcının `targets.json`'u ve `operating.json`'u: `CHANGELOG-7.md`.
- 2.2 (2026-11-05 – 2026-11-06, E550, E551, E553, E560–E566): rakibin bütçe durması, çıkış sırası ve sahip
  istisnasının #spec'i: `CHANGELOG-6.md`.
- 2.2 (2026-11-02 – 2026-11-04, E499, E506, E507, E540–E546): kırmızı bir (B)'den sonra dalların arşivi ve
  silinmesi, tohum güvenlik defteri, imzalı (A) sonucunun aktarımdaki yeri, canlı prova fikstürleri, kapsülde
  defterin salt-okur dizini ve standart kütüphaneyi gizleyen modül adı: `CHANGELOG-5.md`.
- 2.2 (2026-11-01, E411–E417, E470–E475, E478–E485, E490–E499): `26d`'nin olguları (son kökün paketi, zincirli
  satır, Rekor v1, genesis satırı), içe aktarmanın git nesneleriyle anlatımı, `stage-open`'ın bağları ve döngünün
  üç girdisi (`29s`): `CHANGELOG-5.md`.
- 2.2 (2026-10-31 – 2026-11-01, E93, E333, E342, E390–E400, E404, E405, E421–E436, E450): önyükleme hakeminin
  çıkıştan sonraki kuralı, imzalı durumun arayüzü, Kurucu raporlarının yanıtları, npm workspaces kilidi, PASS
  satırı, `stage-open`, fiziksel güvenlik ve kapsülün ajan/skill tanımları: `CHANGELOG-4.md`.
- 2.2 (2026-10-30 – 2026-10-31, E64, E65, E249, E280–E301, E308, E317–E324, E338, E339, E341, E344): ders provasının
  aileleri ve sınav tarafı, sistem haritası, Aşama 0 çıkışının karar verilemeyen koşulları, `control`'ün döngü arayüzü,
  sınıf merdiveninin varsayılanlığı, yük altında performans ve `main`'in salt okunur okunuşu: `CHANGELOG-3.md`.
- 2.2 (2026-10-28 – 2026-10-30, E246–E247 ve öncesi): üçüncü inceleme, önyükleme hakeminin yazılışı ve sonraki kararlar: `CHANGELOG-2.md`.
- 2.1 ve öncesi (2026-10-28): `CHANGELOG-1.md`.
