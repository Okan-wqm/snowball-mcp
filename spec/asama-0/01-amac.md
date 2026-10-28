# Aşama 0 §0.1 — Amaç

Tarih: 2026-10-28 · Sürüm: 2.0 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: beklemede: aşama 0 çıkış raporu

---

Asgari bir harness kurmak; fazlasını değil. Harness, sınıf merdiveni (`tohum/03`) ilerledikçe her
yeni sınıfla birlikte büyür. İlk sınıf K0'dır: profildeki lint aracının kural ihlalleri.

Harness, herhangi bir avcının çıktısını cevabı bilinen gerçek hatalara karşı **LLM'siz ve
deterministik** biçimde puanlar; isabetle birlikte maliyeti de ölçer. Verdict üç değerlidir:
`PASS`, `FAIL`, `UNMEASURABLE` (`tohum/19`).

Bu aşamada sistemin içinde LLM avcı yoktur. İnşa zamanında Kurucu (Opus) ve rakibi (Sonnet)
vardır; bu inşa-zamanı bütçesidir, sistemin çalışma-zamanı LLM maliyeti sıfırdır.
