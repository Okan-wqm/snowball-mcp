"""Seed epoch AO (2026-11-28): the report desk's answer to seed-106 (E753), a merge that landed before a failed state
commit. The operator's decision is (b), as built: after a merge has landed on `brain/integration`, a failed state
commit leaves a head no row names, `13:50-52`'s chain break; the next `çek` refuses it and in (B) only `25a`'s failure
procedure repairs it; `28:54-55`'s takeover (L-AM1) covers only failures before that merge (L-AM1 narrowed, a
tightening). The answer is appended to the end of `28` (61-71); `28:1-60` and `13` do not move. Every fact is cited
`page:line` and each citation is read here; the brain's lines are cited at the brain commit the page names (the brain
is not read here). The trailing comment on a test names the mutants it kills (`local/mutate.py`)."""

import no_real_delays  # noqa: F401  (first: no test waits on a real delay, E751)
import json
import unittest
from pathlib import Path

BOOT = Path(__file__).resolve().parents[1]
ROOT = BOOT.parents[1]
TOHUM = ROOT / "spec" / "tohum"
R106 = "seed-106-a-merge-that-landed-before-a-failed-state-commit-is-a-chain-break-to-the-next-cek"
DECLINED = "reddedildi: operatör kararı (b), bkz. kayıt (E753)"


def page(prefix: str) -> str:
    found = sorted(TOHUM.glob(f"{prefix}-*.md"))
    assert len(found) == 1, (prefix, found)
    return found[0].read_text(encoding="utf-8")


def flat(text: str) -> str:
    return " ".join(text.split())


def cited(prefix: str, first: int, last: int | None = None) -> str:
    return flat("\n".join(page(prefix).splitlines()[first - 1:last or first]))


def register_row(eid: str) -> str:
    rows = (ROOT / "docs" / "eksik-kaydi.md").read_text(encoding="utf-8").splitlines()
    return next(line for line in rows if line.startswith(f"| {eid} |"))


def changelog() -> list[str]:
    return (TOHUM / "CHANGELOG-24.md").read_text(encoding="utf-8").splitlines()


class AnswerTest(unittest.TestCase):
    """`28:62-71`: what a failed state commit after a landed merge is, and each line it cites."""

    def test_the_break_the_refusal_and_the_repair(self):
        # ao_106_not_a_break ao_106_cek_takes_over ao_106_repair_unsaid ao_106_25a_miscited ao_106_kinds_dropped
        # ao_106_lost_answer_dropped ao_106_brain_miscited
        text = cited("28", 62, 71)
        for words in ("**Merge indikten sonra başarısız yazım** (rapor masası uzlaşısı (2026-11-28), seed-106; kurulduğu "
                      "gibi benimsendi: beyin `38715fe`, `referee/loop/write_cycle.py:82-96`, "
                      "`referee/loop/integration.py:21`).",
                      "(bir düzeltmenin, bir geri almanın ya da provanın merge'ü, ya da GitHub'ın cevabı alınamamış ama "
                      "inmiş bir merge) durum commit'i başarısız olursa baş, hiçbir satırın adlandırmadığı bir commit'tir:",
                      "`13:50-52`'nin zincir kırığıdır (yapımda bir `cut` ya da `merge` satırından sonra `head_not_named`).",
                      "Sonraki `çek` onu reddeder (`13:56-57`), döngü onu devralmaz;",
                      "(B)'de onu yalnız `25a`'nın Başarısızlık yolu onarır (`25a:44-46`, E638; `13:58`)."):
            self.assertIn(words, text, words)
        self.assertIn("son imzalı durum satırının adlandırdığı commit'ten başka bir `brain/integration` başı (E637)",
                      cited("13", 50, 51))
        self.assertTrue(cited("13", 50).startswith("- **Zincir kırığı sert duruştur.**"))
        self.assertIn("ondan önce `çek` kırık bulursa döngüyü `hard_stop` ile reddeder ve hiçbir şey yazmaz",
                      cited("13", 56, 57))
        self.assertTrue(cited("13", 58).endswith("bu kırığı (B)'de yalnız `25a` Başarısızlık onarır."))
        self.assertIn("(sahip kararı, 2026-11-18, E638): yazılmış ref'leri adlandıran bir `yaz` sert duruşu, yani hedefe "
                      "yazdıktan sonra kırmızı olan koşu, yeniden tetiklenmez; Başarısızlık uygulanır.", cited("25a", 44, 46))

    def test_the_narrowing_and_what_was_not_granted(self):
        # ao_106_takeover_kept ao_106_loosened ao_106_a_granted
        text = cited("28", 62, 71)
        for words in ("`28:54-55`'in \"başarısız işin bıraktığını devralır\"ı yalnız o merge'den önceki başarısızlıklar "
                      "içindir.",
                      "**L-AM1 daraldı** (bir sıkılaştırma, sahibe bildirilir): başarısız yazım yalnız merge inmeden önce "
                      "operatör adımı istemez.",
                      "`13`'ü gevşetmek sahibindir, verilmedi; iki yazımın hiçbir sırası aradaki durumu kaldırmaz "
                      "(`26d:35`, `13:40-41`)."):
            self.assertIn(words, text, words)
        self.assertNotIn("Gevşetme L-AO", text)
        self.assertIn("başarısız işin bıraktığını devralır", cited("28", 54, 55))
        self.assertIn("**Gevşetme L-AM1** (sahibe bildirilir)", cited("28", 59))
        self.assertIn("`payload` en az `merge_sha`'yı (merge commit'i; `13`, seed-078) taşır", cited("26d", 35))
        self.assertIn("Hakemin `yaz` işi döngü başına `brain/state`'e tek commit atar", cited("13", 40, 41))

    def test_appended_only_and_the_pages_fit(self):  # ao_106_answer_moved ao_106_28_line_moved ao_106_13_touched
        lines = page("28").splitlines()
        self.assertEqual(lines[59], "gevşeğidir; başarısız yazım operatör adımı istemez.")  # 28:60, as it was
        self.assertTrue(lines[50].startswith("**Hedefe yazımın başarısızlığı bir kesintidir**"))  # 28:51, as it was
        self.assertEqual(lines[60], "")
        self.assertTrue(lines[61].startswith("**Merge indikten sonra başarısız yazım**"))
        self.assertEqual(len(lines), 71)
        self.assertEqual([n for n, line in enumerate(lines[60:], 61) if len(line) > 120], [])
        thirteen = page("13").splitlines()
        self.assertEqual(len(thirteen), 80)
        self.assertEqual(thirteen[57], "  kırığın kendisi yeni bir satırdır; bu kırığı (B)'de yalnız `25a` Başarısızlık "
                                       "onarır.")  # 13:58, as it was


class RecordsTest(unittest.TestCase):
    def test_the_register_row(self):  # ao_e753_open ao_106_register_not_narrowed
        row = register_row("E753")
        for words in ("seed-106 (Kurucu raporu)", "Opus ve Sonnet paneli, iki panelin madde satırları birleşik",
                      "operatör kararı, sahibin yetkisiyle: (b)", "`28:62-71`",
                      "`referee/loop/write_cycle.py:82-96`, `referee/loop/integration.py:21` `head_not_named`",
                      "**L-AM1 daraldı** (sıkılaştırma, sahibe bildirilir): `28:54-55`'in devralması yalnız o merge'den "
                      "önceki başarısızlıklar içindir.", "\"bkz. kayıt\" buraya işaret eder", "Gevşetme yok"):
            self.assertIn(words, row, words)
        self.assertEqual(row.count("|"), 7)
        self.assertTrue(row.endswith("| kapandı (tohum dönemi AO; L-AM1 daraldı, sahibe bildirilir) |"))

    def test_this_entry_opens_with_its_first_task(self):  # ao_first_task_not_first ao_changelog_unindexed ao_index_unlisted
        log = changelog()
        entry = flat("\n".join(log).split("\n- 2.2 (2026-11-28, E753", 1)[1])
        self.assertIn("**İlk iş** (`25` 10b). Teslimden itibaren önyükleme hakeminin hiçbir denetimi kırmızı olmaz",
                      entry[:400])
        for words in ("Kurucu'nun bugünkü işi sürer, sırası `CHANGELOG-14`'ünkidir.", "Gevşetme yok; sahip kararı gerekmez."):
            self.assertIn(words, entry, words)
        index = (ROOT / "spec" / "INDEX.md").read_text(encoding="utf-8")
        self.assertIn("| `tohum/CHANGELOG-24.md` | Değişiklik Günlüğü — Tohum, 2.2'nin Yirmi Üçüncü Kayıtları |", index)
        self.assertEqual(log[0], "# Değişiklik Günlüğü — Tohum, 2.2'nin Yirmi Üçüncü Kayıtları")
        top = (TOHUM / "CHANGELOG.md").read_text(encoding="utf-8").splitlines()
        self.assertTrue(top[6].startswith("- 2.2 (2026-11-28, E753; tohum dönemi AO,"))  # the newest entry
        self.assertTrue(top[6].endswith("`CHANGELOG-24.md`; başında **İlk iş**."))
        self.assertLessEqual(len(log), 80)
        self.assertEqual([n for n, line in enumerate(log, 1) if len(line) > 120], [])

    def test_the_oldest_index_entry_moved_unchanged(self):  # ao_archive_entry_dropped
        moved = "- 2.2 (2026-11-16, E600–E605; Kurucu raporları, sahibin onayı): yeni `29z`."
        archive = (TOHUM / "CHANGELOG-arsiv.md").read_text(encoding="utf-8")
        top = (TOHUM / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn(moved, archive)
        self.assertNotIn(moved, top)
        self.assertLess(archive.index(moved), archive.index("- 2.2 (2026-11-14 – 2026-11-15, E585–E599)"))
        self.assertIn("(2.2'nin E600–E605'i ve öncesi, 2.1 ve öncesi): `CHANGELOG-arsiv.md`.", top.splitlines()[-1])
        self.assertIn("Yer için `CHANGELOG.md`'nin en eski dizin girdisi (E600–E605) `CHANGELOG-arsiv.md`'ye taşındı; "
                      "içeriği değişmedi.", flat("\n".join(changelog())))

    def test_every_item_of_both_panels_and_the_decision(self):
        # ao_106_items_dropped ao_106_both_panels_unsaid ao_106_decision_not_b ao_106_sonnet_row_unmarked
        # ao_106_answers_missing
        log = changelog()
        starts = [k for k, line in enumerate(log) if line.strip().startswith(f"`{R106}` →")]
        self.assertEqual(len(starts), 1)
        self.assertTrue(log[starts[0]].endswith("→ `28:62-71`:"))
        items: list[str] = []
        for line in log[starts[0] + 1:]:
            if line.startswith("  - "):
                items.append(line[4:])
            elif line.startswith("    ") and items:
                items[-1] += " " + line.strip()
            else:
                break
        labels = ["ref (", "durum (", "çek (", "ikisi birden tutamaz:", "yapım (", "testler (", "(a) (", "(b) (", "(c) (",
                  "sahip (a) (", "sahip (b) (", "soru (", "evidence_test (", "(bulunan) ", "(bulunan, 2) "]
        self.assertEqual(len(items), len(labels), items)
        for item, label in zip(items, labels):
            self.assertTrue(item.startswith(label), (label, item[:40]))
        rows = dict(zip(labels, items))
        for label in ("ref (", "durum (", "çek (", "ikisi birden tutamaz:", "yapım (", "testler (", "(c) (", "soru (",
                      "(bulunan, 2) "):  # Sonnet's rows for its declined choice
            self.assertIn(DECLINED, rows[label], label)
        self.assertIn("seçildi, kurulduğu gibi benimsendi", rows["(b) ("])
        self.assertIn("karar: (b), operatör kararı; L-AM1 daraldı (E753)", rows["(b) ("])
        self.assertIn("tek onarım yeni genesis, `25a:25-40`", rows["(b) ("])
        self.assertTrue(cited("25a", 25).startswith("**Başarısızlık.**"))
        self.assertTrue(cited("25a", 41).startswith("**Dış kesinti**"))
        self.assertIn("`13:50-52`'nin kurcalama kuralını (E637) gevşetir, sahibin anayasal seçimidir; verilmedi",
                      rows["(a) ("])
        self.assertIn("bir (B) koşusunda hedefe yazdıktan sonra kırmızı biten koşu yeniden tetiklenmez", cited("28", 57, 58))
        text = flat("\n".join(log))
        for words in ("Opus ve Sonnet paneli, iki panelin madde satırları birleşik;",
                      "paneller seçimde ayrıştı: Opus (b), Sonnet (c)'yi kendi biçiminde, sahip kararıyla;",
                      "operatör kararı, sahibin yetkisiyle: (b), kurulduğu gibi"):
            self.assertIn(words, text, words)
        answers = json.loads((BOOT / "reports" / "answers.json").read_text(encoding="utf-8"))["answers"]
        self.assertEqual([(a["id"], a["kind"]) for a in answers if a["changelog"] == "CHANGELOG-24"],
                         [(R106, "answered")])


if __name__ == "__main__":
    unittest.main()
