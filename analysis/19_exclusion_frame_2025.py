# -*- coding: utf-8 -*-
"""
19 — Çerçeve / dışlama serisi 2015–2025 ve ülkeler arası korelasyon.

Kaynaklar (hepsi diskte; hiçbir sayı ezberden değil):
  2015: data/pisa/2015/982016061P1G117.XLSX            Table A2.1   (OECD PISA 2015 Vol I annex)
  2018: data/pisa/2018/EDU-2019-4228-EN-T010.XLSX      Table I.A2.1 (OECD PISA 2018 Vol I annex)
  2022: data/pisa/2022/hpg9nd.xlsx                     Table I.A2.1 (OECD PISA 2022 Vol I annex)
  2025: PISA 2025 Technical Report/Excel Files/14-...AnnexTables_14092026.xlsx  T14.A.1, T14.A.20
        (OECD PISA 2025 Technical Report, TASLAK, 14 Eyl 2026 sürümü)
  2025 enrolled series: data/pisa/2025/annex_tables/pe3lsg.xlsx  Table I.A2.1 (Vol I, 8 döngü)
  Puanlar: data/derived/pisa_scores_wide.csv (kökeni: data/pisa/2025/annex_tables/mrq53f.xlsx)
  Standart sapmalar: 2018 TR Ch.11 Tables 11.11–11.13 (xlsx), Turkey satırı
Çıktılar: data/derived/exclusion_frame/{turkiye_exclusion_series.csv, crosscountry_exclusion_deltas.csv,
          crosscountry_correlations.csv, rankings_2025.csv, summary.json}
Yazan: Claude Fable 5.1 (kod), 2026-09-19. Denetim: bekliyor (Opus 4.8).
Güncelleme 2026-09-28 (Opus 5.5, kör denetim L13): Türkiye'nin kendi Δdışlamasına "eğimin atfettiği puan",
Türkiye'yi de içeren bir eğimle hesaplanıyordu; Türkiye'nin noktası uyumu belirlediği için (2015–2018'de
Cook's D 1,31–1,46, diğer sistemlerde en çok 0,82; Δdışlamada 3. sırada, artığı büyük) sınır döngüseldi. Mevcut sütunlar DEĞİŞMEDİ; yanlarına döngüsel olmayan iki varyant
eklendi: Türkiye hariç OLS (…_ex_tur) ve Türkiye dahil Theil–Sen (…_theilsen), ayrıca Türkiye'nin kaldıraç ve
Cook's D değeri.
"""
import json
import numpy as np
import pandas as pd
import openpyxl
from scipy import stats

import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace("\\", "/")
OUT = f"{ROOT}/data/derived/exclusion_frame"
_TR25_NAME = "14-PISA-2025-Technical Report-AnnexTables_14092026.xlsx"
_TR25_CANDIDATES = [f"{ROOT}/PISA 2025 Technical Report/Excel Files/{_TR25_NAME}",                         # özgün konum
                    f"{ROOT}/docs/oecd_technical_reports/2025_alternatif_indirme/Excel Files/{_TR25_NAME}"]  # taşındığı yer (28 Eyl'de bulundu)
TR25 = next((p for p in _TR25_CANDIDATES if __import__("os").path.exists(p)), None)
if TR25 is None:
    raise FileNotFoundError("2025 Technical Report annex workbook not found in: " + " | ".join(_TR25_CANDIDATES))
REPL = "\ufffd"  # pdf/xlsx'lerde bozuk 'ü'


def norm(s):
    return str(s).replace(REPL, "ü").replace("Turkey", "Türkiye").strip()


def sheet_rows(fn, sheet):
    wb = openpyxl.load_workbook(fn, read_only=True, data_only=True)
    return list(wb[sheet].iter_rows(values_only=True))


def find_row(rows, name_pats):
    for i, r in enumerate(rows):
        if isinstance(r[0], str) and any(p in r[0] for p in name_pats):
            return i, r
    raise KeyError(name_pats)


# ---------- 1. Türkiye serisi ----------
series = []
# Vol I annex A2.1 sütunları: name, pop, enrolled, target, sch_excl, target_minus, sch_rate, n_part, w_part,
#                             n_excl, w_excl, within_rate, overall, ci1, ci2, ci3
fn = f"{ROOT}/data/pisa/2015/982016061P1G117.XLSX"
i, r = find_row(sheet_rows(fn, "Table A2.1"), ["Turkey"])
series.append(dict(cycle=2015, pop=r[1], enrolled=r[2], school_excl=r[4], school_rate=r[6], n_part=r[7], w_part=r[8],
                   n_within=r[9], w_within=r[10], within_rate=r[11], overall=r[12], ci3=r[15],
                   source=f"{fn}#Table A2.1 row{i + 1}"))
fn = f"{ROOT}/data/pisa/2018/EDU-2019-4228-EN-T010.XLSX"
i, r = find_row(sheet_rows(fn, "Table I.A2.1"), ["Turkey"])
series.append(dict(cycle=2018, pop=r[1], enrolled=r[2], school_excl=r[4], school_rate=r[6], n_part=r[7], w_part=r[8],
                   n_within=r[9], w_within=r[10], within_rate=r[11], overall=r[12], ci3=r[15],
                   source=f"{fn}#Table I.A2.1 row{i + 1}"))
fn = f"{ROOT}/data/pisa/2022/hpg9nd.xlsx"
i, r = find_row(sheet_rows(fn, "Table I.A2.1"), ["rkiye", "Turkey"])
series.append(dict(cycle=2022, pop=r[1], enrolled=r[2], school_excl=r[4], school_rate=r[6], n_part=r[7], w_part=r[8],
                   n_within=r[9], w_within=r[10], within_rate=r[11], overall=r[12], ci3=r[15],
                   source=f"{fn}#Table I.A2.1 row{i + 1}"))
# 2025 TR T14.A.1 sütunları: name, pop, enrolled, target, sch_excl, target_minus, sch_rate, frame_est, n_part, w_part,
#                            n_excl, w_excl, n_inelig, w_inelig, within_rate, overall, pct_inelig, ci1, ci2, ci3, ci4, ci5
rows25 = sheet_rows(TR25, "T14.A.1")
i, r = find_row(rows25, ["rkiye", "Turkey"])
series.append(dict(cycle=2025, pop=r[1], enrolled=r[2], school_excl=r[4], school_rate=r[6], n_part=r[8], w_part=r[9],
                   n_within=r[10], w_within=r[11], within_rate=r[14], overall=r[15], ci3=r[19],
                   source=f"{TR25}#T14.A.1 row{i + 1}"))
ser = pd.DataFrame(series)
ser["enrolled_over_pop"] = ser["enrolled"] / ser["pop"]
sc = pd.read_csv(f"{ROOT}/data/derived/pisa_scores_wide.csv")
sc["country"] = sc.country_name.map(norm)
tur = sc[sc.country == "Türkiye"].set_index("cycle")
for d in ["math", "reading", "science"]:
    ser[d] = ser.cycle.map(tur[f"{d}_mean"])
ser.to_csv(f"{OUT}/turkiye_exclusion_series.csv", index=False)

# 2025 öğrenci dışlamaları gerekçe koduna göre (T14.A.20)
rows = sheet_rows(TR25, "T14.A.20")
i, r = find_row(rows, ["Turkey", "rkiye"])
keys = ["c1_functional", "c2_intellectual", "c3_language", "c4_no_materials", "c5_other", "total"]
code5 = dict(unweighted=dict(zip(keys, r[1:7])), weighted=dict(zip(keys, r[7:13])),
             source=f"{TR25}#T14.A.20 row{i + 1}", share_c5_weighted=r[11] / r[12])
c5 = []
for rr in rows[6:]:
    if isinstance(rr[0], str) and isinstance(rr[1], (int, float)) and rr[12]:
        c5.append((norm(rr[0]), rr[6], rr[12], rr[5], rr[11], rr[11] / rr[12]))
c5 = sorted(c5, key=lambda x: x[5], reverse=True)
code5["rank_share_c5"] = [k for k, x in enumerate(c5) if x[0] == "Türkiye"][0] + 1
code5["n_countries"] = len(c5)
code5["n_using_code5"] = sum(1 for x in c5 if x[4] > 0)
code5["top5"] = [(x[0], round(x[5], 3)) for x in c5[:5]]

# ---------- 2. 2025 sıralamalar (T14.A.1) ----------
recs = []
for rr in rows25[5:]:
    if isinstance(rr[0], str) and isinstance(rr[1], (int, float)):
        recs.append(dict(country=norm(rr[0]), pop=rr[1], enrolled=rr[2], school_rate=rr[6], within_rate=rr[14],
                         overall=rr[15], ci3=rr[19], enrolled_over_pop=rr[2] / rr[1] if rr[1] else np.nan))
r25 = pd.DataFrame(recs)
rank = {}
for col, asc in [("school_rate", False), ("within_rate", False), ("overall", False),
                 ("enrolled_over_pop", True), ("ci3", True)]:
    s = r25.dropna(subset=[col]).sort_values(col, ascending=asc).reset_index(drop=True)
    rank[col] = dict(tur_value=float(s.loc[s.country == "Türkiye", col].iloc[0]),
                     tur_rank=int(s.index[s.country == "Türkiye"][0]) + 1, n=len(s),
                     median=float(s[col].median()), order="desc" if not asc else "asc")
r25.to_csv(f"{OUT}/rankings_2025.csv", index=False)

# ---------- 3. 2022→2025 değişimleri ----------
rows = sheet_rows(f"{ROOT}/data/pisa/2025/annex_tables/pe3lsg.xlsx", "Table I.A2.1")
enr = {}
for rr in rows[7:]:
    if isinstance(rr[0], str) and all(isinstance(rr[j], (int, float)) for j in (1, 2, 5, 6)):
        enr[norm(rr[0])] = dict(pop25=rr[1], enr25=rr[2], pop22=rr[5], enr22=rr[6])
d_enr = pd.DataFrame([(k, v["enr22"] / v["pop22"], v["enr25"] / v["pop25"]) for k, v in enr.items() if all(v.values())],
                     columns=["country", "ratio22", "ratio25"])
d_enr["d_ratio_pp"] = (d_enr.ratio25 - d_enr.ratio22) * 100
d_enr = d_enr.sort_values("d_ratio_pp").reset_index(drop=True)
rank["d_enrolled_ratio_22_25"] = dict(tur_value=float(d_enr.loc[d_enr.country == "Türkiye", "d_ratio_pp"].iloc[0]),
                                      tur_rank=int(d_enr.index[d_enr.country == "Türkiye"][0]) + 1, n=len(d_enr),
                                      median=float(d_enr.d_ratio_pp.median()), order="asc (en büyük düşüş = 1)")
rows22 = sheet_rows(f"{ROOT}/data/pisa/2022/hpg9nd.xlsx", "Table I.A2.1")
sx22 = {norm(rr[0]): dict(sch=rr[6], overall=rr[12]) for rr in rows22
        if isinstance(rr[0], str) and isinstance(rr[1], (int, float)) and isinstance(rr[6], (int, float))}
sx25 = r25.set_index("country")
dd = pd.DataFrame([(k, sx22[k]["sch"], sx25.loc[k, "school_rate"], sx22[k]["overall"], sx25.loc[k, "overall"])
                   for k in sx25.index if k in sx22], columns=["country", "sch22", "sch25", "ov22", "ov25"])
dd["d_sch"] = dd.sch25 - dd.sch22
dd["d_ov"] = dd.ov25 - dd.ov22
for col in ["d_sch", "d_ov"]:
    s = dd.sort_values(col).reset_index(drop=True)
    rank[f"{col}_22_25"] = dict(tur_value=float(s.loc[s.country == "Türkiye", col].iloc[0]),
                                tur_rank=int(s.index[s.country == "Türkiye"][0]) + 1, n=len(s),
                                order="asc (en büyük düşüş = 1)")
dd.to_csv(f"{OUT}/exclusion_change_2022_2025.csv", index=False)

# ---------- 4. Ülkeler arası Δdışlama × Δpuan korelasyonu ----------
ax = pd.read_csv(f"{ROOT}/data/derived/annex_extract.csv")
ax["country"] = ax.country.map(norm)
ex = ax[["country", "cycle", "overall_exclusion_pct"]].dropna()
ex = pd.concat([ex, r25[["country", "overall"]].assign(cycle=2025).rename(columns={"overall": "overall_exclusion_pct"})],
               ignore_index=True).drop_duplicates(["country", "cycle"])
df = sc.drop(columns=["overall_exclusion_pct"], errors="ignore").merge(ex, on=["country", "cycle"], how="left")
corr_rows, delta_rows = [], []
for a, b in [(2015, 2018), (2018, 2022), (2022, 2025)]:
    A = df[df.cycle == a].set_index("country")
    B = df[df.cycle == b].set_index("country")
    c = A.index.intersection(B.index)
    d = pd.DataFrame({"d_excl": B.loc[c, "overall_exclusion_pct"] - A.loc[c, "overall_exclusion_pct"],
                      "d_math": B.loc[c, "math_mean"] - A.loc[c, "math_mean"],
                      "d_read": B.loc[c, "reading_mean"] - A.loc[c, "reading_mean"],
                      "d_sci": B.loc[c, "science_mean"] - A.loc[c, "science_mean"]}).dropna()
    d.insert(0, "window", f"{a}-{b}")
    delta_rows.append(d.reset_index())
    t = d.loc["Türkiye"]
    dx = d.drop(index="Türkiye")                                   # döngüsel olmayan varyant için
    X = np.column_stack([np.ones(len(d)), d.d_excl.values])
    lev = np.diag(X @ np.linalg.inv(X.T @ X) @ X.T)                # kaldıraç (şapka matrisi köşegeni)
    i_tur = list(d.index).index("Türkiye")
    for dom in ["d_math", "d_read", "d_sci"]:
        slope, icpt = np.polyfit(d.d_excl.values, d[dom].values, 1)
        slope_x, _ = np.polyfit(dx.d_excl.values, dx[dom].values, 1)
        ts_slope = stats.theilslopes(d[dom].values, d.d_excl.values)[0]
        e = d[dom].values - (icpt + slope * d.d_excl.values)
        s2 = float(e @ e) / (len(d) - 2)
        cook_tur = float(e[i_tur] ** 2 / (2 * s2) * lev[i_tur] / (1 - lev[i_tur]) ** 2)
        corr_rows.append(dict(window=f"{a}-{b}", domain=dom, n=len(d), pearson=d.d_excl.corr(d[dom]),
                              spearman=d.d_excl.corr(d[dom], method="spearman"), slope_pts_per_pp=slope,
                              tur_d_excl=t.d_excl, tur_d_score=t[dom], tur_predicted_by_slope=slope * t.d_excl,
                              tur_rank_d_excl_desc=int((d.d_excl > t.d_excl).sum()) + 1,
                              n_ex_tur=len(dx), pearson_ex_tur=dx.d_excl.corr(dx[dom]),
                              spearman_ex_tur=dx.d_excl.corr(dx[dom], method="spearman"),
                              slope_ex_tur=slope_x, tur_predicted_ex_tur=slope_x * t.d_excl,
                              slope_theilsen=ts_slope, tur_predicted_theilsen=ts_slope * t.d_excl,
                              tur_leverage=float(lev[i_tur]), tur_cooks_d=cook_tur))
pd.concat(delta_rows).to_csv(f"{OUT}/crosscountry_exclusion_deltas.csv", index=False)
corr = pd.DataFrame(corr_rows)
corr.to_csv(f"{OUT}/crosscountry_correlations.csv", index=False)

# ---------- 5. Mekanik sınır hesabı (varsayımlar açık) ----------
sd18 = {"math": 88.155859749, "reading": 87.662532209, "science": 83.526792788}  # 2018 TR Tables 11.12/11.11/11.13
s15, s18 = ser[ser.cycle == 2015].iloc[0], ser[ser.cycle == 2018].iloc[0]
q_sch = (s18.school_excl - s15.school_excl) / s18.enrolled
q_ov = (s18.overall - s15.overall) / 100
bound = {"q_added_school_excl_share_2018": float(q_sch), "q_overall_excl_change_2015_2018": float(q_ov),
         "formula": "ortalama kayması = q × d ; d = tutulan ortalama − dışlanan ortalama (özdeşlik, yaklaşıklık değil)",
         "shift_points_using_q_overall": {dom: {f"gap_{m}SD": float(q_ov * m * s) for m in (1.0, 1.5, 2.0)}
                                          for dom, s in sd18.items()}}
# 2022→2025 CI3 düşüşünün mekanik sınırı (test edilen nüfus payı olarak; 2025 SD'leri 2025 TR T14.A.13/12/11)
s25, s22 = ser[ser.cycle == 2025].iloc[0], ser[ser.cycle == 2022].iloc[0]
sd25 = {"math": 97.09195763184528, "reading": 90.70774985512995, "science": 94.48274990493287}
q_ci3 = (s22.ci3 - s25.ci3) / s25.ci3
bound["ci3_drop_2022_2025"] = {"ci3_2022": float(s22.ci3), "ci3_2025": float(s25.ci3),
                               "q_share_of_tested_pop": float(q_ci3),
                               "shift_points": {dom: {f"gap_{m}SD": float(q_ci3 * m * s) for m in (1.0, 2.0)}
                                                for dom, s in sd25.items()}}
# 2025'in 2022-karşılaştırmalı dışlama oranı, iki varsayım altında
within25 = s25.w_within / (s25.w_part + s25.w_within) * 100  # = raporlanan 2,115
comp = {}
for label, X in [("X_eq_2022_excluded_school_students", float(s22.school_excl)),
                 ("X_eq_full_enrolled_drop_2022_2025", float(s22.enrolled - s25.enrolled))]:
    enr_c = s25.enrolled + X
    sch_c = (s25.school_excl + X) / enr_c * 100
    comp[label] = dict(X=X, comparable_enrolled=float(enr_c), school_rate=float(sch_c), within_rate=float(within25),
                       overall=float(sch_c + (1 - sch_c / 100) * within25))
summary = dict(series=ser.to_dict("records"), code5_2025=code5, rankings=rank, mechanical_bound=bound,
               comparable_2025=comp,
               notes=["2025 sayıları OECD PISA 2025 Technical Report TASLAK (14 Eyl 2026) sürümünden; nihai rapor 2027.",
                      "2025 raporlanan dışlama oranı 2018/2022 ile KARŞILAŞTIRILAMAZ (OECD Böl. 18, Türkiye notu).",
                      "Korelasyonlar tanımlayıcıdır; nedensellik iddiası yoktur."])
with open(f"{OUT}/summary.json", "w", encoding="utf-8") as fh:
    json.dump(summary, fh, ensure_ascii=False, indent=2, default=float)

pd.set_option("display.width", 220)
cols = ["cycle", "pop", "enrolled", "enrolled_over_pop", "school_excl", "school_rate", "n_within", "w_within",
        "within_rate", "overall", "ci3", "math", "reading", "science"]
print(ser[cols].round(4).to_string(index=False))
print("\nCode-5 2025:", json.dumps({k: v for k, v in code5.items() if k != "source"}, ensure_ascii=False, default=float))
print("\nRankings:", json.dumps(rank, indent=1, ensure_ascii=False))
print("\nCorrelations:\n", corr.round(3).to_string(index=False))
print("\nBound:", json.dumps(bound, indent=1, ensure_ascii=False))
print("\nComparable 2025:", json.dumps(comp, indent=1))
