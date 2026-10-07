# -*- coding: utf-8 -*-
"""
24 — Plasebo-alan omurgası 2015–2025 + CPS 2015 ülke ortalamalarının yayımlanmış değerlerle çapraz-kontrolü.

Neden (ek koşul, 20 Eyl 2026): v4 §5.1'de sentetik kontrol ailesi "duyarlılık ailesi"ne inince tanımlamanın omurgası
plasebo-alan testi olur. Omurga olacak bir ayak üç şeyi karşılamalı:
  (1) Mikroveriden hesaplanan 2015 CPS ülke ortalamaları yayımlanmış tabloyla çapraz-kontrol edilmeli (15'in JSON notu: "yapılmadı").
      İki kaynak: (a) BİRİNCİL — OECD (2017) PISA 2015 Results Volume V, Figure V.1.1 "Snapshot of performance in collaborative
      problem solving" (s. 43–44), data/pisa/2015/9789264285521-en.pdf (oecd.org HTML sayfası 403; content/dam PDF bağlantısı
      tarayıcı bölmesinden alınıp curl ile indirildi, 20 Eyl 2026; logs/manifest.csv); (b) İKİNCİL — OECD ülke ortalamalarını
      yeniden basan UK DfE ulusal raporu (Tablo 3–5, s. 12–13), docs/secondary_reports/UK_DfE_PISA_2015_CPS_National_Report.pdf.
      Betik her ikisini (tam sayı) bizim ağırlıklı ortalamalarımızla ülke ülke karşılaştırır; OECD-2015 üyeleri ortalamasının
      ölçek kurgusu gereği 500'e yakın olup olmadığını da yazar. Volume V tablosu PDF'ten çalışma anında ayrıştırılır (pdfplumber;
      yedek: pdftotext), elle yazılmaz.
  (2) Türkiye–Macaristan ayrımı spesifikasyona bağlıysa (2015'te doğrusal: ayırt edilemez; OECD-karesel: ayrışır) bu
      açıkça raporlanmalı — her spesifikasyon için ikisinin artığı ve farkı yan yana.
  (3) 2015 ayağı 2018–2025 iddiasını taşımaz; omurga dört döngüyü kapsamalı: 2015 işbirlikli PS (TUR var), 2018 küresel
      yetkinlik bilişsel testi (TUR yok), 2022 yaratıcı düşünme (TUR yok), 2025 hesaplamalı PS (TUR var). Delikler
      gizlenmez, çizilir (Şekil 6).

Girdi (hepsi önceki adımların çıktısı; hiçbir sayı bu betikte elle yazılmaz — DfE tablosu hariç, o kaynağıyla gömülüdür):
  data/derived/cps2015_country_means.csv                       (15)
  data/derived/mechanisms/placebo_conditional_2015cps.csv      (15)   + *_summary.json
  data/derived/mechanisms/placebo_conditional_2022.csv         (13)   + *_summary.json
  data/derived/mechanisms/placebo_conditional_2025.csv         (10)   + placebo_conditional_summary.json
  data/derived/mechanisms/placebo_conditional_2012ps.csv       (25; kırılma ÖNCESİ nokta, yayımlanmış Table V.A) + *_summary.json — varsa
  data/derived/cache/innovative_domain_participation.csv       (13; 2015 Option_CPS, 2018 PV1GLCM)
Çıktı:
  data/derived/placebo_backbone/{cps2015_crosscheck_oecd_volv.csv, cps2015_crosscheck_dfe.csv, backbone_residuals.csv,
                                 tur_hun_separation.csv, summary.json, backbone_table.md}; analysis/figures/v4_sekil5_plasebo_omurgasi.png
  (20 Eyl gece: şekil numarası 6 → 5 — v4'te Şekil 4 yoktu; ablasyon eğrisi 5 → 4.)
Yazan: Claude Fable 5.1 (kod), 2026-09-20. Denetim: 2015–2025 ayakları Opus 4.8 denetimli (claim_check/PROPOSAL_V4_AUDIT_E23_E24.md);
2012 ayağı bekliyor. Etiket [E24] (2012 ayağı [E25]).
"""
from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data" / "derived"
MECH = D / "mechanisms"
OUT = D / "placebo_backbone"
OUT.mkdir(parents=True, exist_ok=True)
FIG = ROOT / "analysis" / "figures"
INK, BODY, HAIR, ACCENT, BLUE = "#1A1A1A", "#6E6C67", "#D7D5CF", "#8A3324", "#2F5D8A"
GREEN = "#2E7D5B"  # İsveç (Şekil 5 üçüncü seri; ACCENT kırmızı-kahve ve BLUE lacivertle ayrışır)
FOCUS = ["TUR", "HUN", "GEO", "SWE"]  # 21 Eyl 2026 (K8): İsveç dördüncü odak ülke — yalnız SEÇİM için; regresyonlar tüm ülkeler üzerinden (10/13/15/25)
FOCUS_TR = {"TUR": "Türkiye", "HUN": "Macaristan", "GEO": "Gürcistan", "SWE": "İsveç"}

# ---------------------------------------------------------------- (1) DfE tablosu — kaynağıyla gömülü
# UK Department for Education, "Achievement of 15-Year-Olds in England: PISA 2015 Collaborative Problem Solving National Report"
# (Kasım 2017), Tablo 3 (s. 12: İngiltere'nin anlamlı üstündekiler), Tablo 4 (s. 12: farksızlar), Tablo 5 (s. 13: altındakiler).
# Rapor OECD ülke ortalamalarını tam sayıya yuvarlayarak basar; OECD ortalaması ölçek kurgusuyla 500'dür (s. 10, 13).
DFE_SOURCE = "docs/secondary_reports/UK_DfE_PISA_2015_CPS_National_Report.pdf (DfE, Nov 2017), Tables 3–5, pp. 12–13"
DFE = {  # iso3: (yayımlanmış ortalama, tablo)
    "SGP": (561, 3), "JPN": (552, 3), "HKG": (541, 3), "KOR": (538, 3), "CAN": (535, 3), "EST": (535, 3), "FIN": (534, 3),
    "MAC": (534, 3), "NZL": (533, 3), "AUS": (531, 3),
    "TWN": (527, 4), "DEU": (525, 4), "USA": (520, 4), "DNK": (520, 4), "NLD": (518, 4),
    "SWE": (510, 5), "AUT": (509, 5), "NOR": (502, 5), "SVN": (502, 5), "BEL": (501, 5), "ISL": (499, 5), "CZE": (499, 5),
    "PRT": (498, 5), "ESP": (496, 5), "CHN": (496, 5), "FRA": (494, 5), "LUX": (491, 5), "LVA": (485, 5), "ITA": (478, 5),
    "RUS": (473, 5), "HRV": (473, 5), "HUN": (472, 5), "ISR": (469, 5), "LTU": (467, 5), "SVK": (463, 5), "GRC": (459, 5),
    "CHL": (457, 5), "CYP": (444, 5), "BGR": (444, 5), "URY": (443, 5), "CRI": (441, 5), "THA": (436, 5), "ARE": (435, 5),
    "MEX": (433, 5), "COL": (429, 5), "TUR": (422, 5), "PER": (418, 5), "MNE": (416, 5), "BRA": (412, 5), "TUN": (382, 5),
}
DFE_NON_ISO = {"England": 521, "Northern Ireland": 514, "Scotland": 513, "Wales": 496, "OECD average": 500}
# PISA 2015 raporlarındaki 35 OECD üyesi (Letonya dâhil); CPS'e katılmayan üyeler IRL POL CHE → OECD ortalaması 32 ülke üzerinden
OECD35_2015 = {"AUS", "AUT", "BEL", "CAN", "CHL", "CZE", "DNK", "EST", "FIN", "FRA", "DEU", "GRC", "HUN", "ISL", "IRL", "ISR", "ITA",
               "JPN", "KOR", "LVA", "LUX", "MEX", "NLD", "NZL", "NOR", "POL", "PRT", "SVK", "SVN", "ESP", "SWE", "CHE", "TUR", "GBR", "USA"}

means = pd.read_csv(D / "cps2015_country_means.csv")
means["ours"] = means.cps2015_mean_weighted
cc = means[["cnt_microdata", "iso3", "country_name", "ours", "cps2015_mean_unweighted", "n_students"]].copy()
cc["dfe_published"] = cc.iso3.map(lambda i: DFE.get(i, (np.nan, np.nan))[0])
cc["dfe_table"] = cc.iso3.map(lambda i: DFE.get(i, (np.nan, np.nan))[1])
cc["ours_rounded"] = cc.ours.round(0)
cc["diff_ours_minus_dfe"] = (cc.ours - cc.dfe_published).round(2)
cc["match_after_rounding"] = cc.ours_rounded == cc.dfe_published
cc["note"] = ""
cc.loc[cc.iso3 == "GBR", "note"] = "DfE yalnız İngiltere/İskoçya/Galler/K.İrlanda basar; Birleşik Krallık toplamı raporda yok"
cc = cc.sort_values("iso3")
cc.to_csv(OUT / "cps2015_crosscheck_dfe.csv", index=False, encoding="utf-8-sig")
matched = cc[cc.dfe_published.notna()]
unmatched_ours = sorted(cc[cc.dfe_published.isna()].iso3)
unmatched_dfe = sorted(set(DFE) - set(cc.iso3))
oecd32 = means[means.iso3.isin(OECD35_2015)]
crosscheck = dict(source=DFE_SOURCE, n_ours=int(len(cc)), n_dfe_national=len(DFE), n_matched=int(len(matched)),
                  n_match_after_rounding=int(matched.match_after_rounding.sum()),
                  max_abs_diff=float(matched.diff_ours_minus_dfe.abs().max()), mean_diff=float(matched.diff_ours_minus_dfe.mean()),
                  mismatches_after_rounding=[dict(iso3=r.iso3, ours=round(float(r.ours), 2), dfe=int(r.dfe_published)) for r in matched[~matched.match_after_rounding].itertuples()],
                  ours_not_in_dfe=unmatched_ours, dfe_not_in_ours=unmatched_dfe,
                  dfe_not_in_ours_reason="CYP: OECD PUF'unda Kıbrıs yok (CNT listesi 50 sistem); DfE Tablo 5 Kıbrıs 444",
                  TUR=dict(ours=round(float(cc.loc[cc.iso3 == "TUR", "ours"].iloc[0]), 2), dfe=422),
                  HUN=dict(ours=round(float(cc.loc[cc.iso3 == "HUN", "ours"].iloc[0]), 2), dfe=472),
                  oecd_2015_members_in_cps=sorted(oecd32.iso3), n_oecd_2015_members_in_cps=int(len(oecd32)),
                  oecd_2015_mean_of_country_means=round(float(oecd32.ours.mean()), 2),
                  oecd_2015_note="OECD ortalaması ölçek kurgusuyla 500 (DfE s. 10); bizim 2015-üyelik ortalamamız bunun kaç puan yakınında olduğunu gösterir "
                                 "(OECD'nin ortalaması ülke ortalamalarının basit ortalamasıdır)")
print(f"[çapraz-kontrol] eşleşen {crosscheck['n_matched']}/{len(DFE)}; yuvarlama sonrası birebir {crosscheck['n_match_after_rounding']}; "
      f"maks |fark| {crosscheck['max_abs_diff']:.2f}; ort fark {crosscheck['mean_diff']:+.2f}; TUR {crosscheck['TUR']} HUN {crosscheck['HUN']}; "
      f"OECD-2015 ({crosscheck['n_oecd_2015_members_in_cps']} üye) ort {crosscheck['oecd_2015_mean_of_country_means']}")
if crosscheck["mismatches_after_rounding"]:
    print("  yuvarlama sonrası uyuşmayan:", crosscheck["mismatches_after_rounding"])

# ---------------------------------------------------------------- (1b) OECD Volume V (birincil): Figure V.1.1 Snapshot, s. 43–44, PDF'ten ayrıştırma
VOLV_PDF = ROOT / "data" / "pisa" / "2015" / "9789264285521-en.pdf"
VOLV_SOURCE = ("OECD (2017), PISA 2015 Results (Volume V): Collaborative Problem Solving, Figure V.1.1 'Snapshot of performance in "
               "collaborative problem solving', pp. 43–44; data/pisa/2015/9789264285521-en.pdf (content/dam, 21 Nov 2017; indirildi 2026-09-20)")
VOLV_NAME2ISO = {"Singapore": "SGP", "Japan": "JPN", "Hong Kong (China)": "HKG", "Korea": "KOR", "Canada": "CAN", "Estonia": "EST", "Finland": "FIN",
                 "Macao (China)": "MAC", "New Zealand": "NZL", "Australia": "AUS", "Chinese Taipei": "TWN", "Germany": "DEU", "United States": "USA",
                 "Denmark": "DNK", "United Kingdom": "GBR", "Netherlands": "NLD", "Sweden": "SWE", "Austria": "AUT", "Norway": "NOR", "Slovenia": "SVN",
                 "Belgium": "BEL", "Iceland": "ISL", "Czech Republic": "CZE", "Portugal": "PRT", "Spain": "ESP", "B-S-J-G (China)": "CHN", "France": "FRA",
                 "Luxembourg": "LUX", "Latvia": "LVA", "Italy": "ITA", "Russia": "RUS", "Croatia": "HRV", "Hungary": "HUN", "Israel": "ISR",
                 "Lithuania": "LTU", "Slovak Republic": "SVK", "Greece": "GRC", "Chile": "CHL", "Cyprus": "CYP", "Bulgaria": "BGR", "Uruguay": "URY",
                 "Costa Rica": "CRI", "Thailand": "THA", "United Arab Emirates": "ARE", "Mexico": "MEX", "Colombia": "COL", "Turkey": "TUR", "Peru": "PER",
                 "Montenegro": "MNE", "Brazil": "BRA", "Tunisia": "TUN"}


def parse_volv_snapshot(pdf: Path) -> tuple[pd.DataFrame, int | None, str]:
    """Figure V.1.1 satırları: 'Ülke  <ort>  <göreli>  <erkek>  <kız>  <fark> ...'. Sayfa 43–45 taranır; ad → tek satır."""
    import re
    rx = re.compile(r"^\s*([A-Za-z][A-Za-z .()\-]*?[A-Za-z)])[0-9,]*\s{2,}(\d{3})\s+(-?\d+)\s+(\d{3})\s+(\d{3})\s+(-?\d+)")  # ad sonundaki dipnot rakamı (Cyprus1,2) atılır
    rx_oecd = re.compile(r"^\s*(\d{3})\s+Score dif\.\s+(\d{3})\s+(\d{3})")  # 'OECD average-32' başlığının altındaki satır: 500  Score dif.  486  515

    def harvest(text_by_page: list[tuple[int, str]]) -> tuple[dict, int | None]:
        rows, oecd = {}, None
        for pno, txt in text_by_page:
            for line in txt.splitlines():
                m = rx.match(line)
                if m and m.group(1).strip() not in rows:
                    rows[m.group(1).strip()] = dict(name=m.group(1).strip(), mean=int(m.group(2)), relative_perf=int(m.group(3)), boys=int(m.group(4)),
                                                    girls=int(m.group(5)), gender_diff=int(m.group(6)), page=pno)
                mo = rx_oecd.match(line)
                if mo and oecd is None:
                    oecd = int(mo.group(1))
        return rows, oecd

    pages = [43, 44, 45]
    rows, oecd, how = {}, None, ""
    try:
        import pdfplumber
        with pdfplumber.open(str(pdf)) as doc:
            rows, oecd = harvest([(p, doc.pages[p - 1].extract_text(layout=True) or "") for p in pages if p <= len(doc.pages)])
        how = "pdfplumber(layout=True)"
    except Exception as exc:  # pragma: no cover
        how = f"pdfplumber başarısız: {exc}"
    if len(rows) < 45:
        import shutil, subprocess
        if shutil.which("pdftotext"):
            texts = []
            for p in pages:
                out = subprocess.run(["pdftotext", "-layout", "-f", str(p), "-l", str(p), str(pdf), "-"], capture_output=True)
                texts.append((p, out.stdout.decode("utf-8", errors="replace")))
            rows, oecd = harvest(texts)
            how += " → pdftotext -layout"
    df = pd.DataFrame(rows.values())
    return df, oecd, how


volv_ok = VOLV_PDF.exists()
if volv_ok:
    vv, volv_oecd_avg, volv_how = parse_volv_snapshot(VOLV_PDF)
    vv["iso3"] = vv.name.map(VOLV_NAME2ISO)
    unmapped = sorted(vv[vv.iso3.isna()].name)
    vv = vv[vv.iso3.notna()].copy()
    vc = cc[["cnt_microdata", "iso3", "country_name", "ours", "ours_rounded", "n_students"]].merge(
        vv[["iso3", "name", "mean", "relative_perf", "boys", "girls", "gender_diff", "page"]].rename(columns={"mean": "volv_published", "name": "volv_name"}),
        on="iso3", how="outer", indicator=True)
    vc["diff_ours_minus_volv"] = (vc.ours - vc.volv_published).round(2)
    vc["match_after_rounding"] = vc.ours_rounded == vc.volv_published
    vc["dfe_published"] = vc.iso3.map(lambda i: DFE.get(i, (np.nan, np.nan))[0])
    vc["volv_equals_dfe"] = vc.volv_published == vc.dfe_published
    vc = vc.sort_values("iso3")
    vc.to_csv(OUT / "cps2015_crosscheck_oecd_volv.csv", index=False, encoding="utf-8-sig")
    both = vc[vc["_merge"] == "both"]
    crosscheck_volv = dict(source=VOLV_SOURCE, parser=volv_how, n_parsed=int(len(vv)), unmapped_names=unmapped,
                           oecd_average_32_published=volv_oecd_avg, n_matched=int(len(both)),
                           n_match_after_rounding=int(both.match_after_rounding.sum()),
                           max_abs_diff=float(both.diff_ours_minus_volv.abs().max()), mean_diff=float(both.diff_ours_minus_volv.mean()),
                           mismatches_after_rounding=[dict(iso3=r.iso3, ours=round(float(r.ours), 2), volv=int(r.volv_published)) for r in both[~both.match_after_rounding].itertuples()],
                           ours_not_in_volv=sorted(vc[vc["_merge"] == "left_only"].iso3), volv_not_in_ours=sorted(vc[vc["_merge"] == "right_only"].iso3),
                           volv_vs_dfe_disagreements=[dict(iso3=r.iso3, volv=int(r.volv_published), dfe=int(r.dfe_published))
                                                      for r in vc[vc.dfe_published.notna() & vc.volv_published.notna() & ~vc.volv_equals_dfe].itertuples()],
                           TUR=dict(ours=round(float(cc.loc[cc.iso3 == "TUR", "ours"].iloc[0]), 2), volv=int(vv.loc[vv.iso3 == "TUR", "mean"].iloc[0])),
                           HUN=dict(ours=round(float(cc.loc[cc.iso3 == "HUN", "ours"].iloc[0]), 2), volv=int(vv.loc[vv.iso3 == "HUN", "mean"].iloc[0])),
                           GBR=dict(ours=round(float(cc.loc[cc.iso3 == "GBR", "ours"].iloc[0]), 2), volv=int(vv.loc[vv.iso3 == "GBR", "mean"].iloc[0]) if (vv.iso3 == "GBR").any() else None))
    print(f"[Volume V] {volv_how}; ayrıştırılan {len(vv)} ülke (eşlenemeyen ad: {unmapped}); OECD ort-32 {volv_oecd_avg}; eşleşen {crosscheck_volv['n_matched']}; "
          f"yuvarlama sonrası birebir {crosscheck_volv['n_match_after_rounding']}; maks |fark| {crosscheck_volv['max_abs_diff']:.2f}; "
          f"TUR {crosscheck_volv['TUR']} HUN {crosscheck_volv['HUN']} GBR {crosscheck_volv['GBR']}; VolV≠DfE: {crosscheck_volv['volv_vs_dfe_disagreements']}")
else:
    crosscheck_volv = dict(source=VOLV_SOURCE, note="PDF klasörde yok — birincil çapraz-kontrol atlandı")
    print("[Volume V] PDF yok, atlandı")

# ---------------------------------------------------------------- (2)+(3) omurga: dört döngü, odak ülkeler, her spesifikasyon
part = pd.read_csv(D / "cache" / "innovative_domain_participation.csv")
p15 = pd.read_csv(MECH / "placebo_conditional_2015cps.csv")
p22 = pd.read_csv(MECH / "placebo_conditional_2022.csv")
p25 = pd.read_csv(MECH / "placebo_conditional_2025.csv")
s15 = json.loads((MECH / "placebo_conditional_2015cps_summary.json").read_text(encoding="utf-8"))
s22 = json.loads((MECH / "placebo_conditional_2022_summary.json").read_text(encoding="utf-8"))
s25 = json.loads((MECH / "placebo_conditional_summary.json").read_text(encoding="utf-8"))
P12 = MECH / "placebo_conditional_2012ps.csv"
have12 = P12.exists()
if have12:  # kırılma öncesi nokta (25): yayımlanmış ortalamalar, RMSE daha büyük; mod uyarısı summary'de
    p12 = pd.read_csv(P12)
    s12 = json.loads((MECH / "placebo_conditional_2012ps_summary.json").read_text(encoding="utf-8"))
DOM12 = "yaratıcı problem çözme (PS 2012, yayımlanmış)"


def rows_from(df: pd.DataFrame, cycle: int, domain: str, ycol: str, summary: dict) -> list[dict]:
    out = []
    for (scope, spec), g in df.groupby(["scope", "spec"]):
        key = f"{scope}_{spec}"
        n = int(len(g))
        for iso in FOCUS:
            r = g[g.iso3 == iso]
            if r.empty:
                continue
            r = r.iloc[0]
            loo = summary.get(key, {}).get(iso, {}).get("residual_leave_one_out", np.nan)
            out.append(dict(cycle=cycle, domain=domain, iso3=iso, scope=scope, spec=spec, n=n, core=round(float(r.core), 1),
                            domain_score=round(float(r[ycol]), 2), predicted=round(float(r[[c for c in g.columns if c.endswith("_pred")][0]]), 2),
                            residual=float(r.residual), resid_sd=float(r.resid_sd), residual_loo=loo,  # ham; yuvarlama yalnız gösterimde (tek kez)
                            rank_low=int(r.rank_low), rank=f"{int(r.rank_low)}/{n}", pctile=round(float(r.pctile), 1), status="participated"))
    return out


rows = []
if have12:
    rows += rows_from(p12, 2012, DOM12, "ps2012_mean_published", s12)
    for iso in FOCUS:
        if s12["focus_status"].get(iso) == "not in PISA 2012":
            rows.append(dict(cycle=2012, domain=DOM12, iso3=iso, status="not in PISA 2012"))
rows += rows_from(p15, 2015, "işbirlikli problem çözme (CPS 2015)", "cps2015_mean_weighted", s15)
rows += rows_from(p22, 2022, "yaratıcı düşünme (0–60 ölçeği)", "ct_mean", s22)
rows += rows_from(p25, 2025, "hesaplamalı problem çözme (CPS 2025)", "cps2025_mean", s25)
# katılmama satırları (yerel mikroveriden: 13'ün katılım taraması)
for iso in FOCUS:
    r15 = part[(part.cycle == 2015) & (part.indicator == "Option_CPS") & (part.cnt == iso)]
    r18 = part[(part.cycle == 2018) & (part.indicator == "PV1GLCM") & (part.cnt == iso)]
    if len(r15) and not bool(r15.participated.iloc[0]):
        rows.append(dict(cycle=2015, domain="işbirlikli problem çözme (CPS 2015)", iso3=iso, status="did_not_participate (Option_CPS=0)"))
    if len(r18) and not bool(r18.participated.iloc[0]):
        rows.append(dict(cycle=2018, domain="küresel yetkinlik bilişsel testi", iso3=iso, status="no cognitive test (PV1GLCM all missing)"))
    st22 = s22["focus_status"].get(iso)
    if st22 == "did_not_participate":
        rows.append(dict(cycle=2022, domain="yaratıcı düşünme (0–60 ölçeği)", iso3=iso, status="did_not_participate (Table III.B1.2.1 'm'; not in CRT microdata)"))
    elif st22 == "not_in_table":  # İsveç: Table III.B1.2.1'de satırı yok, CRT mikroverisinde de yok → gözlem yok, açıkça yazılır
        rows.append(dict(cycle=2022, domain="yaratıcı düşünme (0–60 ölçeği)", iso3=iso, status="not_in_table (no row in Table III.B1.2.1; not in CRT microdata)"))
    elif st22 and st22 != "participated":
        rows.append(dict(cycle=2022, domain="yaratıcı düşünme (0–60 ölçeği)", iso3=iso, status=st22))
bb = pd.DataFrame(rows).sort_values(["cycle", "iso3", "scope", "spec"], na_position="first")
bb.to_csv(OUT / "backbone_residuals.csv", index=False, encoding="utf-8-sig")

# Türkiye–Macaristan ayrımı: aynı döngü, aynı spesifikasyon
sep_rows = []
for (cyc, scope, spec), g in bb[bb.status == "participated"].groupby(["cycle", "scope", "spec"]):
    t, h = g[g.iso3 == "TUR"], g[g.iso3 == "HUN"]
    if t.empty or h.empty:
        continue
    t, h = t.iloc[0], h.iloc[0]
    sep_rows.append(dict(cycle=int(cyc), scope=scope, spec=spec, n=int(t.n), tur_residual=t.residual, hun_residual=h.residual,
                         diff_tur_minus_hun=round(float(t.residual - h.residual), 2), tur_sd=t.resid_sd, hun_sd=h.resid_sd,
                         diff_sd=round(float(t.resid_sd - h.resid_sd), 2), tur_rank=t["rank"], hun_rank=h["rank"],
                         separated_by_1sd=bool(abs(t.resid_sd - h.resid_sd) >= 1.0)))
sep = pd.DataFrame(sep_rows)
sep.to_csv(OUT / "tur_hun_separation.csv", index=False, encoding="utf-8-sig")

tur = bb[(bb.iso3 == "TUR") & (bb.status == "participated")]
hun = bb[(bb.iso3 == "HUN") & (bb.status == "participated")]
swe = bb[(bb.iso3 == "SWE") & (bb.status == "participated")]
swe_status = {int(r.cycle): r.status for r in bb[(bb.iso3 == "SWE") & (bb.status != "participated")].itertuples()}


def rng(df: pd.DataFrame, cyc: int, col: str) -> dict | None:
    g = df[df.cycle == cyc]
    if g.empty:
        return None
    return dict(min=round(float(g[col].min()), 2), max=round(float(g[col].max()), 2), n_specs=int(len(g)),
                by_spec={f"{r.scope}_{r.spec}": round(float(getattr(r, col)), 2) for r in g.itertuples()})


summary = dict(
    crosscheck_oecd_volv=crosscheck_volv,
    crosscheck_dfe=crosscheck,
    backbone={
        **({"2012": dict(domain="yaratıcı problem çözme (yayımlanmış Table V.A; bilgisayarda, çekirdek kâğıtta)", TUR=s12["focus_status"]["TUR"], HUN=s12["focus_status"]["HUN"],
                         GEO=s12["focus_status"]["GEO"], SWE=s12["focus_status"].get("SWE"), swe_residual=rng(swe, 2012, "residual"), swe_resid_sd=rng(swe, 2012, "resid_sd"),
                         swe_rank={f"{r.scope}_{r.spec}": r.rank for r in swe[swe.cycle == 2012].itertuples()}, swe_residual_loo=rng(swe, 2012, "residual_loo"),
                         tur_residual=rng(tur, 2012, "residual"), tur_resid_sd=rng(tur, 2012, "resid_sd"),
                         tur_rank={f"{r.scope}_{r.spec}": r.rank for r in tur[tur.cycle == 2012].itertuples()}, tur_residual_loo=rng(tur, 2012, "residual_loo"),
                         hun_residual=rng(hun, 2012, "residual"), hun_resid_sd=rng(hun, 2012, "resid_sd"),
                         hun_rank={f"{r.scope}_{r.spec}": r.rank for r in hun[hun.cycle == 2012].itertuples()},
                         n_specs=s12["n_in_regression"], mode_caveat=s12["mode_caveat"], source=s12["source"])} if have12 else {}),
        "2015": dict(domain="işbirlikli problem çözme", TUR="participated", HUN="participated", GEO="did_not_participate",
                     SWE=s15["focus_status"].get("SWE"), swe_residual=rng(swe, 2015, "residual"), swe_resid_sd=rng(swe, 2015, "resid_sd"),
                     swe_rank={f"{r.scope}_{r.spec}": r.rank for r in swe[swe.cycle == 2015].itertuples()}, swe_residual_loo=rng(swe, 2015, "residual_loo"),
                     tur_residual=rng(tur, 2015, "residual"), tur_resid_sd=rng(tur, 2015, "resid_sd"), tur_rank={f"{r.scope}_{r.spec}": r.rank for r in tur[tur.cycle == 2015].itertuples()},
                     hun_residual=rng(hun, 2015, "residual"), hun_resid_sd=rng(hun, 2015, "resid_sd")),
        "2018": dict(domain="küresel yetkinlik bilişsel testi", TUR="no cognitive test", HUN="no cognitive test", GEO="no cognitive test",
                     SWE=swe_status.get(2018),
                     note="PV1GLCM üç ülkede tümüyle boş (13'ün taraması); 29/80 sistem bilişsel testi aldı"),
        "2022": dict(domain="yaratıcı düşünme", TUR="did_not_participate", GEO="did_not_participate", HUN="participated",
                     SWE=s22["focus_status"].get("SWE"), swe_status_row=swe_status.get(2022),
                     hun_residual=rng(hun, 2022, "residual"), hun_resid_sd=rng(hun, 2022, "resid_sd"),
                     note="Türkiye için gözlem yok; Macaristan artığı RMSE'nin −0,4…−1,3 katı, 0–60 ölçeğinde puan olarak karşılaştırılamaz"),
        "2025": dict(domain="hesaplamalı problem çözme", TUR="participated", HUN="participated", GEO="participated",
                     SWE=("participated" if not swe[swe.cycle == 2025].empty else swe_status.get(2025)), swe_residual=rng(swe, 2025, "residual"), swe_resid_sd=rng(swe, 2025, "resid_sd"),
                     swe_rank={f"{r.scope}_{r.spec}": r.rank for r in swe[swe.cycle == 2025].itertuples()}, swe_residual_loo=rng(swe, 2025, "residual_loo"),
                     tur_residual=rng(tur, 2025, "residual"), tur_resid_sd=rng(tur, 2025, "resid_sd"), tur_rank={f"{r.scope}_{r.spec}": r.rank for r in tur[tur.cycle == 2025].itertuples()},
                     tur_residual_loo=rng(tur, 2025, "residual_loo"), hun_residual=rng(hun, 2025, "residual"), hun_resid_sd=rng(hun, 2025, "resid_sd")),
    },
    tur_hun_separation=sep.to_dict("records"),
    verdict=dict(
        cycles_with_tur_observation=([2012] if have12 else []) + [2015, 2025], cycles_without=[2018, 2022],
        **({"spec_dependence_2012": "2012 (kırılma öncesi): " + "; ".join(
            f"{r.scope}/{r.spec}: {r.diff_tur_minus_hun:+.1f} puan ({r.diff_sd:+.2f} SD)" for r in sep[sep.cycle == 2012].itertuples())} if have12 else {}),
        spec_dependence_2015="Türkiye–Macaristan farkı 2015'te spesifikasyona bağlı: " + "; ".join(
            f"{r.scope}/{r.spec}: {r.diff_tur_minus_hun:+.1f} puan ({r.diff_sd:+.2f} SD)" for r in sep[sep.cycle == 2015].itertuples()),
        spec_dependence_2025="2025'te her spesifikasyonda ayrışır: " + "; ".join(
            f"{r.scope}/{r.spec}: {r.diff_tur_minus_hun:+.1f} puan ({r.diff_sd:+.2f} SD)" for r in sep[sep.cycle == 2025].itertuples()),
        caution="Alanlar (2012 yaratıcı, 2015 işbirlikli, 2025 hesaplamalı problem çözme) farklı yapılardır; puanlar değil yalnız SD/sıra karşılaştırılır. "
                + ("2012 ayağı yayımlanmış tam-sayı ortalamalardan (mikroveri yok; RMSE 15–17) ve problem çözme bilgisayarda, çekirdek kâğıtta uygulandığı için "
                   "mod farkını da içerir (25'in notu)." if have12 else "2012 yaratıcı problem çözme (kırılma öncesi nokta) yok — açık kalem.")),
    notes=["Hiçbir artık bu betikte yeniden tahmin edilmedi; 10/13/15 çıktıları okunup yan yana kondu.",
           "FOCUS yalnız raporlanacak ülkeleri SEÇER; regresyonlar 10/13/15/25'te tüm ülkeler üzerinden uydurulur. İsveç'in eklenmesi (21 Eyl 2026) TUR/HUN/GEO artıklarını değiştirmez.",
           "Yayımlanmış ortalamalar tam sayıdır (Volume V Figure V.1.1 ve DfE Tablo 3–5); karşılaştırma yuvarlama sonrası birebirlik ve |fark| ≤ 0,5 ölçütüyle yapılır.",
           "Volume V birincil kaynaktır; DfE onu yeniden basan ikincil kaynaktır (Birleşik Krallık toplamı yalnız Volume V'te)."])
with open(OUT / "summary.json", "w", encoding="utf-8") as fh:
    json.dump(summary, fh, ensure_ascii=False, indent=1, default=float)

# ---------------------------------------------------------------- tablo (md)
lines = ["| Döngü | Alan | " + " | ".join(FOCUS_TR.get(iso, iso) for iso in FOCUS) + " |", "|---|---|" + "---|" * len(FOCUS)]  # başlık FOCUS'tan: sütun sayısı hücre sayısına eşit


def cell(df: pd.DataFrame, cyc: int) -> str:
    g = df[df.cycle == cyc]
    if g.empty:
        return "—"
    return (f"artık {g.residual.min():+.1f}…{g.residual.max():+.1f} ({g.resid_sd.min():+.2f}…{g.resid_sd.max():+.2f} SD); "
            f"sıra {', '.join(sorted(set(g['rank'])))}")


status = {(r.cycle, r.iso3): r.status for r in bb[bb.status != "participated"].itertuples()}
for cyc, dom in ([(2012, "yaratıcı PS (yayımlanmış)")] if have12 else []) + [(2015, "işbirlikli PS"), (2018, "küresel yetkinlik"), (2022, "yaratıcı düşünme"), (2025, "hesaplamalı PS")]:
    cells = []
    for iso in FOCUS:
        st = status.get((cyc, iso))
        if st:
            cells.append(f"*{st}*")
        else:
            cells.append(cell(bb[(bb.iso3 == iso) & (bb.status == "participated")], cyc))
    lines.append(f"| {cyc} | {dom} | " + " | ".join(cells) + " |")
lines += ["", "Türkiye − Macaristan (aynı spesifikasyon):", "", "| Döngü | Kapsam / spek | n | TUR artık (SD) | HUN artık (SD) | Fark puan (SD) | ≥ 1 SD ayrışma |", "|---|---|---|---|---|---|---|"]
for r in sep.itertuples():
    lines.append(f"| {r.cycle} | {r.scope} / {r.spec} | {r.n} | {r.tur_residual:+.1f} ({r.tur_sd:+.2f}) | {r.hun_residual:+.1f} ({r.hun_sd:+.2f}) | {r.diff_tur_minus_hun:+.1f} ({r.diff_sd:+.2f}) | {'evet' if r.separated_by_1sd else 'hayır'} |")
lines += ["", f"Çapraz-kontrol (ikincil, DfE Tablo 3–5): eşleşen {crosscheck['n_matched']}/{len(DFE)} ülke; yuvarlama sonrası birebir {crosscheck['n_match_after_rounding']}; "
          f"maks |fark| {crosscheck['max_abs_diff']:.2f} puan; Türkiye {crosscheck['TUR']['ours']} vs 422; Macaristan {crosscheck['HUN']['ours']} vs 472; "
          f"OECD-2015 üyeleri ({crosscheck['n_oecd_2015_members_in_cps']}) ortalaması {crosscheck['oecd_2015_mean_of_country_means']} (ölçek kurgusu 500)."]
if volv_ok:
    lines += ["", f"Çapraz-kontrol (birincil, OECD Volume V Figure V.1.1): ayrıştırılan {crosscheck_volv['n_parsed']} ülke; eşleşen {crosscheck_volv['n_matched']}; "
              f"yuvarlama sonrası birebir {crosscheck_volv['n_match_after_rounding']}; maks |fark| {crosscheck_volv['max_abs_diff']:.2f} puan; "
              f"Türkiye {crosscheck_volv['TUR']['ours']} vs {crosscheck_volv['TUR']['volv']}; Macaristan {crosscheck_volv['HUN']['ours']} vs {crosscheck_volv['HUN']['volv']}; "
              f"Birleşik Krallık {crosscheck_volv['GBR']['ours']} vs {crosscheck_volv['GBR']['volv']}; OECD ortalaması-32 yayımlanan {crosscheck_volv['oecd_average_32_published']}; "
              f"Volume V ≠ DfE: {crosscheck_volv['volv_vs_dfe_disagreements'] or 'yok'}."]
(OUT / "backbone_table.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

# ---------------------------------------------------------------- Şekil 5 (20 Eyl gece: 6 → 5)
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Liberation Sans", "Arial", "DejaVu Sans"], "font.size": 10})
fig, ax = plt.subplots(figsize=(12, 6))
CYCLES = ([2012] if have12 else []) + [2015, 2018, 2022, 2025]
cyc_x = {c: i for i, c in enumerate(CYCLES)}
ax.axhline(0, color=INK, lw=1.1)
if have12:
    ax.axvline(0.5, color=HAIR, lw=1, ls="--")
    ax.text(0.5, 0.78, "2013 kırılması", ha="center", va="bottom", fontsize=8, color=BODY)
SERIES = [("TUR", ACCENT, -0.13, "below", 0.22), ("HUN", BLUE, 0.0, "above", -0.22), ("SWE", GREEN, 0.13, "right", 0.50)]  # (iso, renk, x kayması, artık-etiket konumu, "gözlem yok" etiketi y)
for iso, col, dx, lab_pos, nolab_y in SERIES:  # GEO bilerek çizilmez
    g = bb[(bb.iso3 == iso) & (bb.status == "participated")]
    for cyc in [c for c in CYCLES if c != 2018]:
        s = g[g.cycle == cyc]
        if s.empty:
            continue
        x = cyc_x[cyc] + dx
        ax.vlines(x, s.resid_sd.min(), s.resid_sd.max(), color=col, lw=2.2, alpha=0.9)
        ax.scatter([x] * len(s), s.resid_sd, s=42, color=col, zorder=3, edgecolor="white", lw=0.5)
        lab_txt = f"{s.resid_sd.min():+.2f}…{s.resid_sd.max():+.2f}"
        if lab_pos == "below":     # Türkiye: aralığın altına, ortalanmış
            ax.text(x, s.resid_sd.min() - 0.1, lab_txt, ha="center", va="top", fontsize=8, color=col)
        elif lab_pos == "above":   # Macaristan: aralığın üstüne, ortalanmış
            ax.text(x, s.resid_sd.max() + 0.1, lab_txt, ha="center", va="bottom", fontsize=8, color=col)
        else:                      # İsveç: aralığın sağ-altına (orta nokta sıfır çizgisine düşebilir; 2025 öyle)
            ax.text(x + 0.05, s.resid_sd.min() - 0.05, lab_txt, ha="left", va="top", fontsize=8, color=col)
    for cyc in [2018, 2022]:
        st = status.get((cyc, iso))
        if st:
            x = cyc_x[cyc] + dx
            ax.scatter([x], [0], s=70, facecolors="white", edgecolors=col, lw=1.4, zorder=3)
            ax.text(x, nolab_y, "gözlem yok" if "not" in st or "no " in st else st, ha="center", va="bottom" if nolab_y > 0 else "top", fontsize=7.5, color=col, rotation=0)
ax.set_xticks(list(cyc_x.values()))
XLAB = {2012: "2012\nyaratıcı problem çözme\n(yayımlanmış; kırılma öncesi)", 2015: "2015\nişbirlikli problem çözme", 2018: "2018\nküresel yetkinlik",
        2022: "2022\nyaratıcı düşünme", 2025: "2025\nhesaplamalı problem çözme"}
ax.set_xticklabels([XLAB[c] for c in CYCLES], color=BODY)
ax.set_ylabel("koşullu artık (alan ~ çekirdek), RMSE birimi", color=BODY)
_plotted = bb[bb.iso3.isin([s[0] for s in SERIES]) & (bb.status == "participated")].resid_sd
ax.set_ylim(min(-3.6, float(_plotted.min()) - 0.4), max(1.2, float(_plotted.max()) + 0.4))  # üçüncü seri aralık dışına düşerse kırpılmaz
ax.set_xlim(-0.45, len(CYCLES) - 0.2)  # sağda pay: İsveç etiketi (sağa yazılır) eksen dışına taşmasın
ax.spines[["top", "right"]].set_visible(False); ax.spines[["left", "bottom"]].set_color(HAIR); ax.tick_params(colors=BODY)
ax.grid(axis="y", color=HAIR, lw=0.6)
ax.scatter([], [], color=ACCENT, label="Türkiye"); ax.scatter([], [], color=BLUE, label="Macaristan"); ax.scatter([], [], color=GREEN, label="İsveç (karşı-örnek)")
ax.scatter([], [], facecolors="white", edgecolors=BODY, label="katılmadı / bilişsel test yok")
ax.legend(frameon=False, loc="lower left", fontsize=9)
fig.suptitle(f"Şekil 5 · Plasebo-alan omurgası {CYCLES[0]}–2025: hazırlık yapılamayan alanda koşullu artık", x=0.01, ha="left", fontsize=13.5, color=INK, family="DejaVu Serif")
# Hangi odak ülkenin hangi döngüde gözlemi olduğu VERİDEN türetilir, elle yazılmaz.
# (21 Eyl düzeltmesi: eski metin "2018 ve 2022'de Türkiye ve İsveç için gözlem yoktur;
#  Macaristan 2022'de var" diyordu — bu, 2018'de Macaristan'ın gözlemi varmış izlenimi
#  veriyordu. Oysa 2018'de dört odak ülkenin HİÇBİRİNDE gözlem yok: küresel yetkinlik
#  bilişsel testinde PV1GLCM tümüyle eksik.)
def _obs(cyc: int) -> list[str]:
    return [i for i in FOCUS if not bb[(bb.iso3 == i) & (bb.cycle == cyc) & (bb.status == "participated")].empty]


def _tr(isos: list[str]) -> str:
    return ", ".join(FOCUS_TR.get(i, i) for i in isos)


_o18, _o22 = _obs(2018), _obs(2022)
GAP_TXT = (("2018'de odak ülkelerin hiçbirinde gözlem yoktur (küresel yetkinlik bilişsel testi)"
            if not _o18 else f"2018'de yalnız {_tr(_o18)} için gözlem vardır")
           + ("; 2022'de de yoktur. " if not _o22 else f"; 2022'de yalnız {_tr(_o22)} için vardır. "))
CAPTION = ("Dikey çizgi = dört spesifikasyon (tüm/OECD × doğrusal/karesel) aralığı. " + GAP_TXT
           + "İsveç (yeşil) karşı-örnektir: dışlama kanalı 2018'de işledi; plasebo alanda ayrışması hipotez gereği beklenmez — sayı ne derse o. "
           + ("2012: yayımlanmış ortalamalar, problem çözme bilgisayarda / çekirdek kâğıtta. " if have12 else "")
           + "Alanlar farklı yapılar: yalnız RMSE birimi ve sıra karşılaştırılır. Gürcistan çizilmez (tabloda). Kaynak: 10/13/15" + ("/25" if have12 else "") + " çıktıları; betik analysis/24_placebo_backbone.py [E24]" + ("[E25]" if have12 else "") + ".")
# Altbilgi TEK SATIR bırakılırsa `bbox_inches="tight"` tuvali yatayda metne kadar
# genişletir: 21 Eyl'de İsveç cümleleri eklenince şekil 2364→3691 px'e çıktı (en/boy
# 3,0 → 4,7) ve PDF'te sayfa genişliğine ölçeklenince çizim ezilip yazı okunmaz hâle
# geliyordu. Bu yüzden satır ~200 karakterde sarılır ve tuval 12 inçte kalır.
CAP_LINES = textwrap.wrap(CAPTION, width=200, break_long_words=False)
fig.text(0.01, 0.005, "\n".join(CAP_LINES), fontsize=8, color=BODY, va="bottom")
fig.tight_layout(rect=(0, 0.015 * len(CAP_LINES) + 0.02, 1, 0.95))
fig.savefig(FIG / "v4_sekil5_plasebo_omurgasi.png", dpi=130, bbox_inches="tight")
plt.close(fig)
print((OUT / "backbone_table.md").read_text(encoding="utf-8"))
print("DONE placebo backbone")
