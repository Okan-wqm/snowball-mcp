# Tohum Teklifi: Kurucu'nun Eklemeli Yaması ve Hakemin Denetimi

Tarih: 2026-11-14 · Sürüm: 2.3 · Durum: taslak · Sahibi: operatör
Okunma: tohumdaki bir kusura yama önerilirken, bir `proposal_*` adı okunurken ve bir adayın merge'ünde
Çapa: `seed/bootstrap/snowball_bootstrap/proposals.py`; `cli.py` `_pull_classify`; `local/proposal_check.py`

---

`29b`'nin kurallarıyla koşan bir denetimdir. **Kural** (sahibin kararı 2026-11-14). Kurucu tohuma yazmaz;
`snowball-mcp`'ye karşı eklemeli bir yama ve onu kanıtlayan bir test önerir. Hakem öneriyi mekanik ve kapalıya düşerek
sınar; geçen öneri yalnız **aday**dır, merge'ü ve tohum dönemini panel ya da sahip yapar (`25` 10b). Kurucu hakem
reposuna ve donmuş koltuklara yine yazamaz (`09a`) ve kendi sınavının yargıcı olmaz (Y6). Kendi yazdığını (kod, harita,
rapor) kanıtla değiştirir; defter yalnız eklenir (`00a`), donmuş spec dizinini yalnız operatör açar (`29b`).

**Dosya.** `reports/<id>.json` ve `reports/<id>.patch`, kökte; ikisi de Kurucu kaydıdır (`29e`). `.json`: `{id, kind:
seed_proposal, ref, state: open|withdrawn, base: {spec_tohum_sha256, bootstrap_sha256}, patch_sha256, evidence: {tests:
[..]}}`; `ref` yanıtlanan rapor ya da `sayfa:satır`; `evidence` yamanın eklediği test dosyalarındaki en çok 5
`test_<ad>.<Sınıf>.<test>` kimliğidir. `.patch` `git diff` çıktısıdır, `diff --git` ile başlar, posta başlığı taşımaz
(`proposal_not_a_diff`). Biçimsiz kayıt, eksik yama ya da tutmayan `patch_sha256` `proposal_malformed`'dır. `base` son
tohum döneminin satırındaki iki özettir (`26c` `seed_epochs[]`), değilse `proposal_base_unknown`: teklif yalnız teslim
edilmiş tohuma uygulanır, başka teklife yaslanmaz. Teklifi tohum dönemi `CHANGELOG*.md`'de kimliğini anarak ya da
`declined:` yazarak yanıtlar; Kurucu merge'ü beyan edemez.

**Kapalı yüzey.** Yama yalnız var olan bir `spec/tohum/*.md` sayfasına, `seed/bootstrap/snowball_bootstrap/`'taki var
olan ya da yeni bir modüle, yeni bir `seed/bootstrap/tests/test_<ad>.py`'ye ve `local/mutate.py`'nin `MUTANTS`'ına
dokunur; başka her yol (aşama tabloları, vektörler, iş akışları, kapsül, dokümanlar, `INDEX.md`, yeni sayfa)
`proposal_surface_closed:<yol>`'dır. Açık yüzeyde de kapalı olanlar: `00-cekirdek.md`, `09a-bagimsizlik.md`,
`29w-tohum-teklifi.md`, `29x-acik-iddialar.md`, `CHANGELOG*.md`, `__init__.py`, `__main__.py`, `canon.py`, `claims.py`,
`classify.py`, `config.py`, `container.py`, `controls.py`, `ghapi.py`, `gitio.py`, `importer.py`, `ledgercheck.py`,
`licenses.py`, `proposals.py`, `reproduce.py`, `rival.py`, `rival_mcp.py`, `secretscan.py`, `stagelock.py`, `stages.py`,
`state.py`, `treehash.py`. Liste tohumun kararıdır ve `proposals.CLOSED`'ta durur; bir test bunu sınar.

**Eklemeli** (mekanik; ilk tutmayan madde öneriyi reddeder). Yama yalnız satır ekler: `-` satırı, silinen, adı ya da
kipi değişen, ikili ya da bağ olan dosya yoktur (`proposal_not_additive:<yol>`). Python'da tabanın her deyimi yerinde ve
aynıdır: eklenen deyimler çıkarılınca tabanın AST'si kalır. Eklenen her deyim modül düzeyinde ve eylemsizdir: içe
aktarma, `def`, `class` ya da düz değerli sabit; adı tabanda hiç geçmez, yerleşik değildir, `__` ile başlamaz,
`setUpModule`, `tearDownModule`, `load_tests` ya da `skip*` değildir; dekoratör, sınıf anahtar kelimesi, yabancı taban
sınıf, varsayılanda ya da tembel olmayan açıklamada çağrı, kodlama bildirimi yoktur. Var olan bir işlevin ya da sınıfın
içine bir şey eklenmez: tabanın çalıştırdığı hiçbir kod yeni koda ulaşamaz (`proposal_meaning:<yol>:<satır>`).
`mutate.py`'de yalnız `MUTANTS`'ın sonuna yeni adlı satır eklenir, çapası dosyasında tam bir kez bulunur
(`proposal_anchor:<ad>`); dokunulan dosyadaki eski satırların çapası da tam bir kez kalır, böylece taban her mutantını
yine yerinde uygular. Sayfada en çok 80 satır, eklenen satırda en çok 120 karakter (`proposal_page_cap:<yol>`); CR
yoktur (`proposal_line_ending`); eklenen satır sır, e-posta, `Co-Authored-By`, `Signed-off-by` ya da hedef adı taşımaz
(`proposal_identity:<kural>`, `29e`); en çok 2000 satır (`proposal_too_large`). `evidence`'daki her test yamanın yeni
test dosyasındadır (`proposal_evidence:<id>`).

**Durum.** Sonuç her tekliften `proposals [{id, json_sha256, patch_sha256, status, reasons, review}]` taşır. `status`:
`candidate`, `rejected`, `incomplete` (hakemin kopyasında okunamayan taban dosyası, `proposal_unread:<yol>`, ya da
bitmeyen denetim, `proposal_unchecked`; asla aday değil), `deferred` (bir baş en çok 3 açık teklif sınar) ya da
`withdrawn`. Aday `proposal_candidate:<id>` uyarısıdır. Teklif hiçbir aşamada ret nedeni, seri ya da kabul koşulu
değildir. Yalnız kayıt push'u `noop`'tur ve sonucu teklifi yine adlandırır. Bir bulgu en çok 200 karakterdir.

**Erişim ve koşucu** (E600, E601). Eklenen kod, test gövdesi de, bir izin listesine uzanır (`proposals.reach`):
`STDLIB`'deki birkaç modül ve adlı üyeleri; `EFFECTS`'ten bir şey içe aktarmayan paket ya da test modülü, tanımladığı
açık adlarla. `__` ile başlayan ad, `_` ile başlayan öznitelik, `BANNED_NAMES`, `BANNED_ATTRS`, `global`, `__init__`
dışı dunder yöntem, sınıf anahtar kelimesi ve modül düzeyindeki adı değiştirme yoktur; öznitelik yalnız kendi örneğine
(yamanın sınıfındaki yöntemin ilk parametresi) atanır, takma adla paylaşılan nesneye değil; yeni test
`unittest.TestCase`'in `setUp` ve `tearDown` dışındaki bir üyesini (`run`, `debug`, `failureException` ...) tanımlamaz
(`proposal_meaning:<yol>:<satır>`). Takımı koşan, toplayan ya da raporlayan şey Kurucu'nun değildir: var olan testler ve
yardımcıları, `local/` betikleri (`mutate.py`'de yalnız `MUTANTS` satırları açıktır), `conftest.py`, `sitecustomize.py`,
`usercustomize.py`, `.pth` ve `unittest` adlı modül. Bunlara dokunan teklif `proposal_runner:<yol>`'dur.

**Kanıt.** Hakem kod koşturmaz; merge'ü yapan adayı `local/proposal_check.py` ile koşar, taban HEAD'in git'teki
dosyalarıdır. Kurucu'nun testi takımın sürecinde ortak sonuca uzanabilir (`run`'ı ezer, `shouldStop` koyar) ve bunu
metne bakan kural kapatamaz; bu yüzden iki karar hiç buluşmaz. (1) Var olan takım: tabanın testleri ve koşucusu bayt
bayt, üstünde yalnız yamanın sayfaları ve modülleri (harita yeniden çizilir); `--full` birim takımını tek süreçte,
dokunulan dosyalara çapalı taban mutantlarını her biri kendi sürecinde koşar (`proposal_suite_red`,
`proposal_mutant_survived`). (2) Kanıt: her test kendi sürecinde tabanda (yalnız yeni test dosyalarıyla) kırmızı, tüm
yamayla iki kez yeşil; `--full` yeni mutantları ekler; kararı (1)'i beslemez. Testler ağsız bir kapta (`--image`, özetle
sabit) ya da yerel süreçte (`--unsandboxed`) koşar. `proposal/<id>` PR'ında CI aynısını yapar (`ci.yml`): birim ve
mutasyon işleri tabanın `tests/` ve `local/`'ünü geri koyar, yeni testler `proposal-evidence`'ta koşar.

**İnceleme.** Mekanik denetim gereklidir, yeterli değildir: her adayı, test gövdeleri ve sayfa satırlarıyla, merge'den
önce bir insan ya da panel okur. `review`'i hakem farktan yazar, Kurucu'nun sözünden değil:
`page_text:<yol>:<satırlar>`, `appended:<yol>:<ad>`, `new_module:<yol>`, `tests:<yol>`, `mutants:+<n>`; merge'ü yapan,
bir istisna, atlama, geniş izin listesi, ret yerine uyarı ya da gevşeyen eşik gelmediğini CHANGELOG'a yazar.

**Sınırlar.** Yapı yön bilmez: kırmızıdan yeşile geçen test gevşetmeyi de kanıtlar, sayfa metni anlam taşır. Merge'den
sonra yeni test takımın sürecindedir; ona okuma ve main'in tam mutasyon koşusu bakar. İzinli işlevin yan etkisi ve takma
adla değişen bir sözlük AST'de görünmez. Geçmek kuralların tuttuğunu söyler, adayın doğru olduğunu değil.
