# -*- coding: utf-8 -*-
"""
55 — İkinci makalenin revizyonu için hesaplar ve şekiller.
Yazarın revizyon notları (28 Eyl 2026) üzerine. Yazan: Claude (Opus 5.5, Cowork), 2026-09-29.

 A. Türkiye'nin öğrenci SD'leri 2012–2025 (yayımlanmış OECD Cilt I tabloları) ve ardışık değişimler:
    puan, SD birimi (iki döngünün SD ortalaması), ilk döngünün ortalamasına göre yüzde.
 B. Ortak tanımla (normalize) çerçeve ve dışlama kaydı 2015–2025. Tanım A: açık öğretim ve Mesleki Eğitim Merkezleri
    (MESEM) her döngüde çerçeve dışı — 2015 ve 2025'teki uygulama. 2018 ve 2022'de bu kurumlar listelenip okul düzeyinde
    dışlandı (TR18 Böl. 14; TR25 Böl. 18); öğrenci sayıları (X) yayımlanmadı. X aralığı = raporlanan okul düzeyi dışlama −
    [diğer okul düzeyi dışlamalar]; "diğer" için 2015 (5.746) ve 2025 (6.796) düzeyleri alt/üst sınır (varsayım, raporlanır).
    Nüfus payları (paydası tüm 15 yaşlılar; Coverage Index 3 ile aynı payda) tanımdan bağımsızdır.
 C. Mekanik sınır: μ_tutulan − μ_tüm = q × (μ_tutulan − μ_dışlanan); fark k·σ (k = 1, 2); σ her döngünün kendi öğrenci SD'si
    (betik 49 / E8 kuralı). Geçiş katkısı = q_t2·k·σ_t2 − q_t1·k·σ_t1.
 D. Mod geçişi 2012–2015–2018: 2015'te bilgisayarla test eden sistemler (kâğıtta kalanlar: data/derived/paper_based_2015.csv,
    Jerrim vd. 2018); 2018'de kâğıtla test eden dokuz ülke OECD (2019) Cilt I'den (aşağıda PAPER_2018). Değişimlerde Türkiye'nin
    sırası ve z'si; sabit kümede düzey z'si; OECD ortalaması-35'e göre fark. 2012→2015 betik 20 (E20) ile birebir karşılaştırılır.
 E. 2025 cinsiyet bileşimi aritmetiği: temsil edilen nüfustaki kız payı (E41) nüfus kaydı payına çekilirse ortalama değişimi
    = (s_kayıt − s_PISA) × (kız − erkek); kız ve erkek ortalamaları sabit tutulur (yalnız bileşim etkisi).

Kaynaklar yalnız diskte (ezberden sayı yok). Çıktılar: data/derived/paper2_revizyon/ ; şekiller analysis/figures/paper2/
Gereksinim: pandas, numpy, openpyxl, xlrd (2012 .xls), matplotlib.  Çalıştırma: python analysis/55_paper2_revizyon.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "derived" / "paper2_revizyon"
FIG = ROOT / "analysis" / "figures" / "paper2"
FIG.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)

DOMAINS = ["math", "reading", "science"]
DLAB = {"math": "Mathematics", "reading": "Reading", "science": "Science"}

# ---------- kaynak tablolar (dosya, sayfa) ----------
SD_SOURCES = {
    2012: {"math": ("data/pisa/2012/982013041P1T001.XLS", "Table I.2.3a"),
           "reading": ("data/pisa/2012/982013041P1T003.XLS", "Table I.4.3a"),
           "science": ("data/pisa/2012/982013041P1T004.XLS", "Table I.5.3a")},
    2015: {"science": ("data/pisa/2015/982016061P1T004.XLSX", "Table I.2.3"),
           "reading": ("data/pisa/2015/982016061P1T006.XLSX", "Table I.4.3"),
           "math": ("data/pisa/2015/982016061P1T007.XLSX", "Table I.5.3")},
    2018: {"reading": ("data/pisa/2018/EDU-2019-4228-EN-T014.XLSX", "Table I.B1.4"),
           "math": ("data/pisa/2018/EDU-2019-4228-EN-T014.XLSX", "Table I.B1.5"),
           "science": ("data/pisa/2018/EDU-2019-4228-EN-T014.XLSX", "Table I.B1.6")},
    2022: {"math": ("data/pisa/2022/xmrlsh.xlsx", "Table I.B1.2.1"),
           "reading": ("data/pisa/2022/xmrlsh.xlsx", "Table I.B1.2.2"),
           "science": ("data/pisa/2022/xmrlsh.xlsx", "Table I.B1.2.3")},
    2025: {"science": ("data/pisa/2025/annex_tables/mrq53f.xlsx", "Table I.B1.2a.1"),
           "reading": ("data/pisa/2025/annex_tables/mrq53f.xlsx", "Table I.B1.2a.2"),
           "math": ("data/pisa/2025/annex_tables/mrq53f.xlsx", "Table I.B1.2a.3")},
}
GENDER_2025 = {"science": ("data/pisa/2025/annex_tables/68stqn.xlsx", "Table I.B1.2c.1"),
               "reading": ("data/pisa/2025/annex_tables/68stqn.xlsx", "Table I.B1.2c.2"),
               "math": ("data/pisa/2025/annex_tables/68stqn.xlsx", "Table I.B1.2c.3")}
# OECD (2019), PISA 2018 Results Vol. I, basılı s. 30 not 1 ve liste s. 33 (data/pisa/2018/5f07c754-en.pdf, "nine countries"; T1 29 Eyl):
PAPER_2018 = ["ARG", "JOR", "LBN", "MDA", "MKD", "ROU", "SAU", "UKR", "VNM"]
TUR_LABELS = {"Turkey", "Türkiye"}


def row_of(df, labels):
    col0 = df.iloc[:, 0].astype(str).str.strip()
    hit = df[col0.isin(labels)]
    if len(hit) != 1:
        raise RuntimeError(f"{labels}: {len(hit)} satır")
    return hit.index[0], hit.iloc[0]


def oecd_avg_row(df):
    col0 = df.iloc[:, 0].astype(str).str.strip()
    hit = df[col0.str.lower().str.startswith("oecd average")]
    return hit.index[0], hit.iloc[0]


# ================= A. SD serisi ve ardışık değişimler =================
wide = pd.read_csv(ROOT / "data/derived/pisa_scores_wide.csv")
tur_w = wide[wide.iso3 == "TUR"].set_index("cycle")
sd_rows = []
for cyc, dd in SD_SOURCES.items():
    for dom, (f, sh) in dd.items():
        df = pd.read_excel(ROOT / f, sheet_name=sh, header=None)
        i, r = row_of(df, TUR_LABELS)
        j, o = oecd_avg_row(df)
        mean, sd = float(r.iloc[1]), float(r.iloc[3])
        ref = float(tur_w.loc[cyc, f"{dom}_mean"])
        if abs(mean - ref) > 0.01:
            raise RuntimeError(f"{cyc} {dom}: tablo {mean} ≠ pisa_scores_wide {ref}")
        sd_rows.append(dict(cycle=cyc, domain=dom, mean=mean, se=float(r.iloc[2]), sd=sd, sd_se=float(r.iloc[4]),
                            oecd_avg_mean=float(o.iloc[1]), oecd_avg_sd=float(o.iloc[3]),
                            source=f"{f}#{sh} satır {i + 1} (Türkiye), {j + 1} ({str(o.iloc[0]).strip()})"))
sds = pd.DataFrame(sd_rows).sort_values(["domain", "cycle"])
sds.to_csv(OUT / "sd_series.csv", index=False)
SD = {(r.cycle, r.domain): r.sd for r in sds.itertuples()}
MEAN = {(r.cycle, r.domain): r["mean"] for _, r in sds.iterrows()}

TRANS = [(2012, 2015), (2015, 2018), (2018, 2022), (2022, 2025), (2015, 2025), (2012, 2018), (2012, 2025)]
ch_rows = []
for a, b in TRANS:
    for dom in DOMAINS:
        d = MEAN[(b, dom)] - MEAN[(a, dom)]
        psd = (SD[(a, dom)] + SD[(b, dom)]) / 2
        ch_rows.append(dict(t1=a, t2=b, domain=dom, mean_t1=MEAN[(a, dom)], mean_t2=MEAN[(b, dom)], d_points=d,
                            sd_t1=SD[(a, dom)], sd_t2=SD[(b, dom)], pooled_sd=psd, d_sd=d / psd,
                            d_pct_of_mean=100 * d / MEAN[(a, dom)]))
changes = pd.DataFrame(ch_rows)
changes.to_csv(OUT / "timeline_changes.csv", index=False)

# ================= B. Ortak tanımla çerçeve kaydı (tanım A) =================
ser = pd.read_csv(ROOT / "data/derived/exclusion_frame/turkiye_exclusion_series.csv").set_index("cycle")
LISTED = {2015: False, 2018: True, 2022: True, 2025: False}  # TR18 Böl.14 ("previously not listed ... listed, but excluded, in 2018"); TR25 Böl.18
band_lo, band_hi = float(ser.loc[2015, "school_excl"]), float(ser.loc[2025, "school_excl"])
band_mid = (band_lo + band_hi) / 2
fr_rows = []
for cyc in [2015, 2018, 2022, 2025]:
    s = ser.loc[cyc]
    rec = dict(cycle=cyc, listed_and_excluded=LISTED[cyc], pop=s["pop"], enrolled=s["enrolled"],
               school_excl_reported=s["school_excl"], w_part=s["w_part"], w_within=s["w_within"],
               within_rate=s["within_rate"], overall_reported=s["overall"], ci3=s["ci3"])
    for tag, other in (("lo", band_lo), ("mid", band_mid), ("hi", band_hi)):
        # tag: normalize dışlama oranının alt / orta / üst ucu; normalize okul dışlaması = "diğer" (5.746 → alt, 6.796 → üst)
        X = (s["school_excl"] - other) if LISTED[cyc] else 0.0
        sch = s["school_excl"] - X
        enr = s["enrolled"] - X
        srate = 100 * sch / enr
        overall = srate + s["within_rate"] * (1 - srate / 100)
        rec[f"X_{tag}"] = X
        rec[f"school_excl_A_{tag}"] = sch
        rec[f"school_rate_A_{tag}"] = srate
        rec[f"overall_A_{tag}"] = overall
    # nüfus payları (orta değer)
    rec["share_represented"] = s["w_part"] / s["pop"]
    rec["share_within_excl"] = s["w_within"] / s["pop"]
    rec["share_other_school_excl"] = rec["school_excl_A_mid"] / s["pop"]
    rec["share_open_ed_listed_excluded"] = rec["X_mid"] / s["pop"]
    rec["share_outside_frame_or_not_enrolled"] = 1 - (rec["share_represented"] + rec["share_within_excl"]
                                                      + rec["share_other_school_excl"] + rec["share_open_ed_listed_excluded"])
    if abs(rec["share_represented"] - s["ci3"]) > 1e-6:
        raise RuntimeError(f"{cyc}: w_part/pop ≠ CI3")
    fr_rows.append(rec)
frame = pd.DataFrame(fr_rows)
frame.to_csv(OUT / "frame_normalised.csv", index=False)

# 2025'in 2018–2022 tanımıyla (tanım B) yeniden ifadesi, bu betiğin X aralığıyla (X_2022 = 37.136–38.186).
# E19'un X = 43.932 senaryosu 2025'in 6.796 "diğer" dışlamasını ikinci kez sayar (T1, 29 Eyl); bu sürüm saymaz.
s25 = ser.loc[2025]
restated = []
for tag in ("lo", "hi"):
    X = float(frame.set_index("cycle").loc[2022, f"X_{tag}"])
    srate = 100 * (s25["school_excl"] + X) / (s25["enrolled"] + X)
    restated.append(dict(X=X, school_rate_B=srate, overall_B=srate + s25["within_rate"] * (1 - srate / 100)))
restated_2025_B = pd.DataFrame(restated)
restated_2025_B.to_csv(OUT / "restated_2025_defB.csv", index=False)
fs_ = frame.set_index("cycle")
jumps = dict(reported_2015_2018_pp=float(fs_.loc[2018, "overall_reported"] - fs_.loc[2015, "overall_reported"]),
             normalised_2015_2018_pp=[float(fs_.loc[2018, "overall_A_lo"] - fs_.loc[2015, "overall_A_lo"]),
                                      float(fs_.loc[2018, "overall_A_hi"] - fs_.loc[2015, "overall_A_hi"])],
             within_2015_2018_pp=float(fs_.loc[2018, "within_rate"] - fs_.loc[2015, "within_rate"]),
             normalised_2015_2025_pp=float(fs_.loc[2025, "overall_A_mid"] - fs_.loc[2015, "overall_A_mid"]),
             within_2015_2025_pp=float(fs_.loc[2025, "within_rate"] - fs_.loc[2015, "within_rate"]))

# ================= C. Mekanik sınır, geçiş başına =================
b_rows = []
qA = {r.cycle: {"lo": r.overall_A_lo / 100, "mid": r.overall_A_mid / 100, "hi": r.overall_A_hi / 100} for r in frame.itertuples()}
qR = {r.cycle: r.overall_reported / 100 for r in frame.itertuples()}
for a, b in [(2015, 2018), (2018, 2022), (2022, 2025), (2015, 2025)]:
    for dom in DOMAINS:
        actual = MEAN[(b, dom)] - MEAN[(a, dom)]
        for k in (1.0, 2.0):
            vals = [qA[b][tb] * k * SD[(b, dom)] - qA[a][ta] * k * SD[(a, dom)]
                    for ta in ("lo", "hi") for tb in ("lo", "hi")]
            rep = qR[b] * k * SD[(b, dom)] - qR[a] * k * SD[(a, dom)]
            b_rows.append(dict(t1=a, t2=b, domain=dom, gap_sd=k, actual_change=actual,
                               bound_normalised_min=min(vals), bound_normalised_max=max(vals),
                               bound_as_reported=rep,
                               share_of_change_max=max(vals) / actual if actual else np.nan,
                               # gerçek değişimi tek başına üretmek için gereken fark (SD), ortak tanımla
                               required_gap_sd_min=(k * actual / max(vals)) if max(vals) > 0 else np.nan,
                               required_gap_sd_max=(k * actual / min(vals)) if min(vals) > 0 else np.nan))
bounds = pd.DataFrame(b_rows)
bounds.to_csv(OUT / "bounds_by_transition.csv", index=False)

# ================= D. Mod geçişi 2012–2015–2018 =================
paper15 = set(pd.read_csv(ROOT / "data/derived/paper_based_2015.csv", encoding="utf-8-sig").iso3)
sysw = wide[~wide.iso3.str.startswith("OECD")]


def panel(cycles):
    sub = sysw[sysw.cycle.isin(cycles)]
    ok = sub.groupby("iso3").filter(lambda g: set(g.cycle) >= set(cycles)
                                    and g[[f"{d}_mean" for d in DOMAINS]].notna().all().all())
    excl = set()
    if 2015 in cycles:
        excl |= paper15
    if 2018 in cycles:
        excl |= set(PAPER_2018)
    return ok[~ok.iso3.isin(excl)]


m_rows, lev_rows = [], []
for a, b in [(2012, 2015), (2015, 2018), (2012, 2018)]:
    cyc = [2012, 2015, 2018] if (a, b) == (2012, 2018) else [a, b]
    p = panel(cyc)
    wa = p[p.cycle == a].set_index("iso3")
    wb = p[p.cycle == b].set_index("iso3")
    for dom in DOMAINS:
        d = (wb[f"{dom}_mean"] - wa[f"{dom}_mean"]).dropna()
        t = d["TUR"]
        m_rows.append(dict(t1=a, t2=b, domain=dom, n=len(d), tur=t, median=d.median(), mean=d.mean(), sd=d.std(ddof=1),
                           z_tur=(t - d.mean()) / d.std(ddof=1), rank_most_negative=int((d < t).sum() + 1),
                           rank_most_positive=int((d > t).sum() + 1)))
mode = pd.DataFrame(m_rows)
mode.to_csv(OUT / "mode_transition_changes.csv", index=False)
# E20 kapısı: 2012→2015 betik 20 ile aynı mı
e20 = pd.read_csv(ROOT / "data/derived/mode_transition_2015/cba2015_changes.csv").set_index("iso3").loc["TUR"]
for dom, c in (("math", "d_math"), ("reading", "d_read"), ("science", "d_sci")):
    r = mode[(mode.t1 == 2012) & (mode.t2 == 2015) & (mode.domain == dom)].iloc[0]
    if abs(r.tur - e20[c]) > 1e-9 or r.rank_most_negative != int(e20[f"rank_{c}"]):
        raise RuntimeError(f"E20 kapısı: {dom} {r.tur} vs {e20[c]}")
# sabit kümede düzey z'si ve OECD ortalaması-35 farkı
p3 = panel([2012, 2015, 2018])
oecd35 = wide[wide.iso3 == "OECD_A35"].set_index("cycle")
for cyc in (2012, 2015, 2018):
    w = p3[p3.cycle == cyc].set_index("iso3")
    for dom in DOMAINS:
        x = w[f"{dom}_mean"]
        lev_rows.append(dict(cycle=cyc, domain=dom, n=len(x), tur=x["TUR"], z_tur=(x["TUR"] - x.mean()) / x.std(ddof=1),
                             rank_from_bottom=int((x < x["TUR"]).sum() + 1),
                             oecd35_mean=float(oecd35.loc[cyc, f"{dom}_mean"]),
                             gap_oecd35=float(x["TUR"] - oecd35.loc[cyc, f"{dom}_mean"]),
                             gap_oecd35_in_oecd_sd=float((x["TUR"] - oecd35.loc[cyc, f"{dom}_mean"])
                                                         / sds[(sds.cycle == cyc) & (sds.domain == dom)].oecd_avg_sd.iloc[0])))
levels = pd.DataFrame(lev_rows)
levels.to_csv(OUT / "mode_transition_levels.csv", index=False)
ict = json.load(open(ROOT / "data/derived/mode_transition_2015/ict_summary.json", encoding="utf-8"))
ictfit = pd.read_csv(ROOT / "data/derived/mode_transition_2015/ict_penalty_fit.csv")

# ================= E. 2025 cinsiyet bileşimi =================
e6 = pd.read_csv(ROOT / "outputs/tables/pisa2025/e6_results.csv")
e6 = e6[e6.role == "ana"].iloc[0]
g_rows = []
for dom, (f, sh) in GENDER_2025.items():
    df = pd.read_excel(ROOT / f, sheet_name=sh, header=None)
    if str(df.iloc[8, 31]).strip() != "Score dif." or str(df.iloc[8, 1]).strip() != "Mean score":
        raise RuntimeError(f"{sh}: başlık beklenen gibi değil")
    for lab, getter in (("Türkiye", lambda: row_of(df, TUR_LABELS)), ("OECD average", lambda: oecd_avg_row(df))):
        i, r = getter()
        girls, boys, bg, bg_se = float(r.iloc[1]), float(r.iloc[16]), float(r.iloc[31]), float(r.iloc[32])
        if abs((boys - girls) - bg) > 0.01:
            raise RuntimeError(f"{sh} {lab}: fark tutarsız")
        rec = dict(domain=dom, system=lab, girls_mean=girls, boys_mean=boys, boys_minus_girls=bg, se=bg_se,
                   source=f"{f}#{sh} satır {i + 1}")
        if lab == "Türkiye":
            ds = float(e6.tuik_female_share - e6.pisa_female_share)
            rec.update(pisa_female_share=float(e6.pisa_female_share), register_female_share=float(e6.tuik_female_share),
                       reweight_shift=ds * (girls - boys))
        g_rows.append(rec)
gender = pd.DataFrame(g_rows)
gender.to_csv(OUT / "gender_composition_2025.csv", index=False)

# ================= özet =================
ci3 = pd.read_csv(ROOT / "data/derived/annex_extract.csv")
ci3 = ci3[ci3.country.isin(["Turkey", "Türkiye"])][["cycle", "coverage_index3", "overall_exclusion_pct"]].sort_values("cycle")
summary = dict(
    note="Betik 55 — Makale 2 revizyonu. Kaynaklar dosya ve sayfa düzeyinde CSV'lerin source sütunlarında.",
    sd_series=sds.to_dict("records"),
    timeline_changes=changes.to_dict("records"),
    frame_normalised=frame.to_dict("records"),
    restated_2025_defB=restated_2025_B.to_dict("records"),
    exclusion_jumps_pp=jumps,
    other_school_excl_band=dict(lo_2015=band_lo, hi_2025=band_hi,
                                assumption="2018/2022'de açık öğretim ve MESEM dışındaki okul düzeyi dışlamalar 2015–2025 bandında"),
    bounds_by_transition=bounds.to_dict("records"),
    mode_changes=mode.to_dict("records"),
    mode_levels=levels.to_dict("records"),
    ict_e22=dict(tur_2015_ict_module_administered=ict["tur_2015_ict_module_administered"],
                 tur_2015_ictres_coverage_pct=ict["tur_2015_ictres_coverage_pct"],
                 n_countries_administering_module_2015=ict["n_countries_administering_module_2015"],
                 key_result=ict["key_result"],
                 fit_rows=ictfit[["ict_measure", "domain", "n_countries", "pearson_r", "tur_predicted", "tur_observed"]]
                 .to_dict("records")),
    gender_2025=gender.to_dict("records"),
    ci3_series=ci3.to_dict("records"),
    paper_based_2018=PAPER_2018,
)
json.dump(summary, open(OUT / "summary.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)

# ================= şekiller =================
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5})
STY = {"math": dict(color="black", ls="-", marker="o"), "reading": dict(color="0.35", ls="--", marker="s"),
       "science": dict(color="0.6", ls=":", marker="^")}
CYC = [2012, 2015, 2018, 2022, 2025]

# Şekil 1: zaman çizelgesi (puan, SD birimi, yüzde; olaylar) — döngüler eşit aralıklı
XP = {c: i for i, c in enumerate(CYC)}
fig = plt.figure(figsize=(8.2, 7.0))
gs = fig.add_gridspec(3, 1, height_ratios=[3.0, 0.8, 1.25], hspace=0.04)
ax = fig.add_subplot(gs[0])
OFF = {"math": (0, -13), "reading": (-15, 5), "science": (15, 5)}
for dom in DOMAINS:
    y = [MEAN[(c, dom)] for c in CYC]
    ax.plot([XP[c] for c in CYC], y, lw=1.6, ms=5, label=DLAB[dom], **STY[dom])
    for c, v in zip(CYC, y):
        ax.annotate(f"{v:.0f}", (XP[c], v), textcoords="offset points", xytext=OFF[dom],
                    ha="center", fontsize=7.5, color=STY[dom]["color"])
ax.set_xlim(-0.6, 4.6)
ax.set_ylim(398, 510)
ax.set_xticks(range(len(CYC)))
ax.tick_params(labelbottom=False)
ax.set_ylabel("Mean score (PISA points)")
ax.axvspan(0.12, 0.88, color="0.92", zorder=0)
ax.text(0.5, 507, "paper → computer\n(core domains)", ha="center", va="top", fontsize=7)
ax.legend(loc="lower right", frameon=False, ncol=3)
ax.set_title("Türkiye's PISA record, 2012–2025: scores, changes and measurement events", fontsize=10, loc="left")
ax.grid(axis="y", color="0.9", lw=0.6)
# değişim şeridi
ax2 = fig.add_subplot(gs[1], sharex=ax)
ax2.set_ylim(0, 1)
ax2.axis("off")
for a, b in zip(CYC[:-1], CYC[1:]):
    xm = (XP[a] + XP[b]) / 2
    lines = []
    for dom in DOMAINS:
        r = changes[(changes.t1 == a) & (changes.t2 == b) & (changes.domain == dom)].iloc[0]
        lines.append(f"{DLAB[dom][0]} {r.d_points:+5.1f} ({r.d_sd:+.2f} SD)")
    ax2.text(xm, 0.97, f"{a}→{b}", ha="center", va="top", fontsize=7.3, fontweight="bold")
    ax2.text(xm, 0.72, "\n".join(lines), ha="center", va="top", fontsize=6.3, family="DejaVu Sans Mono",
             linespacing=1.3)
# olay şeridi
ax3 = fig.add_subplot(gs[2], sharex=ax)
ax3.set_ylim(0, 1)
ax3.axis("off")
ax3.hlines(0.86, -0.45, 4.45, color="black", lw=1)
EVENTS = {
    2012: "Paper-based core\nCI3 0.68\nexcl. 1.5%",
    2015: "First computer-based core\nFirst cycle run by\nÖDSGM (est. 2014)\nOpen-ed. & VTCs\nnot listed · excl. 1.1%",
    2018: "Open-ed. & VTCs\nlisted, then excluded\nexcl. 5.7%\nStrata: school type ×\nperformance percentile",
    2022: "Listed and excluded\nexcl. 5.6%\nProgramme-level units\nSubject teachers\nin briefings",
    2025: "Open-ed. & VTCs left\nout of the frame\nexcl. 2.74%*\n601 teachers'\nworkshop",
}
for c, txt in EVENTS.items():
    ax3.plot([XP[c]], [0.86], marker="o", color="black", ms=4)
    ax3.text(XP[c], 0.955, str(c), ha="center", va="bottom", fontsize=8, fontweight="bold")
    ax3.text(XP[c], 0.79, txt, ha="center", va="top", fontsize=6.4, linespacing=1.22)
ax3.text(-0.6, 0.12, "Changes: points and, in brackets, SD units (change ÷ mean of the two cycles' student SDs); per cent changes in Table 2. "
                     "* Draft 2025 rate, not comparable with 2018–2022 (TR25 Ch. 14, 18).",
         fontsize=6.2, va="top", ha="left", color="0.25")
fig.savefig(FIG / "timeline.png", dpi=220, bbox_inches="tight")
plt.close(fig)

# Şekil 2: ortak tanımla çerçeve (nüfus payları + dışlama oranı)
fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.2, 3.9), gridspec_kw=dict(width_ratios=[1.25, 1]))
x = np.arange(4)
cyc4 = [2015, 2018, 2022, 2025]
parts = [("share_represented", "Represented by the weighted sample (CI3)", dict(color="0.35")),
         ("share_within_excl", "Excluded within sampled schools", dict(color="black")),
         ("share_other_school_excl", "Other school-level exclusions", dict(color="0.65")),
         ("share_open_ed_listed_excluded", "Open-ed. & VTCs listed, then excluded", dict(color="white", hatch="////", edgecolor="black")),
         ("share_outside_frame_or_not_enrolled", "Outside the frame, not enrolled, other", dict(color="0.88", edgecolor="0.5"))]
bottom = np.zeros(4)
for col, lab, kw in parts:
    v = 100 * frame.set_index("cycle").loc[cyc4, col].values
    a1.bar(x, v, bottom=bottom, width=0.62, label=lab, lw=0.5, **kw)
    for xi, (vi, bi) in enumerate(zip(v, bottom)):
        if vi > 2.2:
            a1.text(xi, bi + vi / 2, f"{vi:.1f}", ha="center", va="center", fontsize=7,
                    color="white" if col in ("share_represented", "share_within_excl") else "black")
    bottom += v
a1.set_xticks(x, [str(c) for c in cyc4])
a1.set_ylabel("Per cent of all 15-year-olds")
a1.set_ylim(0, 100)
a1.set_title("(a) Where the 15-year-old cohort sits", fontsize=9, loc="left")
a1.legend(fontsize=6.4, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2, frameon=False)
fs = frame.set_index("cycle").loc[cyc4]
a2.plot(x, fs.overall_reported, color="0.55", ls="--", marker="s", label="Overall exclusion as reported")
yerr = np.vstack([fs.overall_A_mid - fs.overall_A_lo, fs.overall_A_hi - fs.overall_A_mid])
a2.errorbar(x, fs.overall_A_mid, yerr=yerr, color="black", marker="o", capsize=3, label="Overall exclusion, common definition")
a2.plot(x, fs.within_rate, color="black", ls=":", marker="^", label="of which within-school")
for xi, c in enumerate(cyc4):
    a2.annotate(f"{fs.overall_A_mid.iloc[xi]:.2f}", (xi, fs.overall_A_mid.iloc[xi]), textcoords="offset points",
                xytext=(9, -3), fontsize=7)
    if abs(fs.overall_reported.iloc[xi] - fs.overall_A_mid.iloc[xi]) > 0.05:
        a2.annotate(f"{fs.overall_reported.iloc[xi]:.2f}", (xi, fs.overall_reported.iloc[xi]), textcoords="offset points",
                    xytext=(-2, 6), fontsize=7, color="0.4", ha="center")
a2.set_xticks(x, [str(c) for c in cyc4])
a2.set_ylabel("Per cent")
a2.set_ylim(0, 6.6)
a2.set_title("(b) Exclusion rate, reported vs common definition", fontsize=9, loc="left")
a2.legend(fontsize=6.4, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=1, frameon=False)
fig.tight_layout()
fig.savefig(FIG / "frame_normalised.png", dpi=220, bbox_inches="tight")
plt.close(fig)

# Şekil 3: mod geçişi 2012–2018
fig, (b1, b2) = plt.subplots(1, 2, figsize=(8.2, 3.7), gridspec_kw=dict(width_ratios=[1, 1.35]))
for dom in DOMAINS:
    lv = levels[levels.domain == dom].sort_values("cycle")
    b1.plot(lv.cycle, lv.gap_oecd35, lw=1.5, ms=5, label=DLAB[dom], **STY[dom])
    off = {"math": (9, -9), "reading": (9, 4), "science": (-24, 3)}[dom]
    for c, g in zip(lv.cycle, lv.gap_oecd35):
        b1.annotate(f"{g:+.0f}", (c, g), textcoords="offset points", xytext=off, fontsize=7, color=STY[dom]["color"])
b1.axhline(0, color="0.6", lw=0.6)
b1.set_xticks([2012, 2015, 2018])
b1.set_xlim(2011, 2019.3)
b1.set_ylabel("Türkiye minus OECD average-35 (points)")
b1.set_title("(a) Distance to the OECD average", fontsize=9, loc="left")
b1.legend(fontsize=7, frameon=False, loc="lower right")
pos = 0
ticks, tlabs, allv = [], [], []
rng = np.random.default_rng(20260929)
for dom in DOMAINS:
    for a, b in [(2012, 2015), (2015, 2018), (2012, 2018)]:
        cyc = [2012, 2015, 2018] if (a, b) == (2012, 2018) else [a, b]
        p = panel(cyc)
        wa = p[p.cycle == a].set_index("iso3")[f"{dom}_mean"]
        wb = p[p.cycle == b].set_index("iso3")[f"{dom}_mean"]
        d = (wb - wa).dropna()
        oth = d.drop("TUR")
        allv.extend(d.tolist())
        b2.scatter(pos + rng.uniform(-0.18, 0.18, len(oth)), oth, s=7, color="0.65", lw=0)
        b2.scatter([pos], [d["TUR"]], s=36, marker="D", color="black", zorder=3)
        r = mode[(mode.t1 == a) & (mode.t2 == b) & (mode.domain == dom)].iloc[0]
        b2.annotate(f"{r.rank_most_negative}/{r.n}" if d["TUR"] < 0 else f"{r.rank_most_positive}/{r.n}↑",
                    (pos, d["TUR"]), textcoords="offset points", xytext=(6, -3), fontsize=6.3)
        ticks.append(pos)
        tlabs.append(f"{str(a)[2:]}→{str(b)[2:]}")
        pos += 1
    pos += 0.6
b2.axhline(0, color="0.6", lw=0.6)
b2.set_xticks(ticks, tlabs, fontsize=6.8)
ylo, yhi = min(allv) - 6, max(allv) + 14
for k, dom in enumerate(DOMAINS):
    b2.text(1 + k * 3.6, yhi - 7, DLAB[dom], ha="center", fontsize=7.5)
b2.set_ylim(ylo, yhi)
b2.set_ylabel("Change in mean score (points)")
b2.set_title("(b) Changes across systems tested on computer", fontsize=9, loc="left")
fig.tight_layout()
fig.savefig(FIG / "mode_transition.png", dpi=220, bbox_inches="tight")
plt.close(fig)

# ---------- konsol özeti ----------
pd.set_option("display.width", 220)
print("SD:\n", sds.pivot(index="cycle", columns="domain", values="sd").round(2))
print("Değişimler:\n", changes[["t1", "t2", "domain", "d_points", "d_sd", "d_pct_of_mean"]].round(3).to_string(index=False))
print("Çerçeve (tanım A):\n", frame[["cycle", "listed_and_excluded", "X_lo", "X_hi", "overall_reported", "overall_A_lo",
                                      "overall_A_mid", "overall_A_hi", "within_rate", "ci3"]].round(3).to_string(index=False))
print("Nüfus payları (%):\n", (100 * frame.set_index("cycle")[[c for c, _, _ in parts]]).round(2).to_string())
print("Sınırlar:\n", bounds.round(2).to_string(index=False))
print("Mod değişimleri:\n", mode.round(3).to_string(index=False))
print("Mod düzeyleri:\n", levels.round(3).to_string(index=False))
print("Cinsiyet:\n", gender.drop(columns=["source"]).round(3).to_string(index=False))
