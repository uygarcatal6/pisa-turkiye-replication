#!/usr/bin/env python3
"""56 — Plasebo artığı dışlama kanalını izliyor mu? (PISA 2025, ülkeler arası)

Soru: Makale 1'in "plasebo dışlama kanalına kör" bulgusu yalnız iki olguya (İsveç, Lüksemburg) dayanıyordu. Aynı
öğrenciler çekirdeği ve yenilikçi alanı birlikte aldığı için dışlama iki ortalamayı birlikte kaydırmalı ve artıkta
büyük ölçüde sönmeli. Bu betik bunu tüm dağılımda sınar: 2025 genel dışlama oranı ile 2025 koşullu artık arasında
ilişki var mı, ve %5 dışlama standardını OECD uyarı yıldızı olmadan aşan sistemler artık dağılımının neresinde?

Ön-kayıt durumu: ÖN-KAYITSIZ (post hoc). Makale 1 v3 T1'inin (Cowork, 29 Eyl 2026, bulgu #22) ardından eklendi;
tüm hücreler raporlanır, hiçbir hücre seçilmez.

Tanımlar:
  birincil   : Spearman ρ(genel dışlama %, artık), 4 hücre = {tüm katılımcılar 84, OECD 38} × {doğrusal, ikinci derece}
  ikincil    : Pearson r aynı hücrelerde; okul içi dışlama oranıyla aynı ilişki; %5 üstü ve altı sistemlerin artık
               ortancası ve Mann–Whitney U (iki yönlü); yıldızsız %5 üstü sistemlerin alttan sıraları ve alt ondalık
               dilimde (sıra ≤ ⌊0,10·n⌋) kalanlar
  yıldız     : OECD'nin "one or more PISA sampling standards were not met" uyarı listesi (aşağıdaki PDF'ten okunur);
               veri dosyasındaki ülke adı sonundaki "*" ülke dipnotudur, uyarı değildir

Girdiler (hepsi diskte):
  data/derived/exclusion_frame/rankings_2025.csv     (betik 19; PISA 2025 Teknik Rapor TASLAK T14.A.1, 14 Eyl 2026)
  data/derived/mechanisms/placebo_conditional_2025.csv (betik 10; yayımlanmış ortalamalar, OECD 2026a)
  03_dogrulama/DOGRULANMIS_PAKET/KAYNAK_DOKUMANLAR/oecd_ve_veri/OECD_PISA2025_asterisk-caution-notu.pdf
Çıktılar:
  data/derived/exclusion_frame/placebo_association_2025.csv   (sistem düzeyi birleşik tablo)
  data/derived/exclusion_frame/placebo_association_2025.json  (özet)
Yazan: Claude Opus 5.5 (CC yerel), 2026-09-29. Denetim: T1 taze bağlam (29 Eyl): 0 uyuşmazlık; uyarı listesi
ayrıştırması ve yinelenen satır denetimi T1 üzerine sağlamlaştırıldı.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

import pandas as pd
from pypdf import PdfReader
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "derived" / "exclusion_frame"
EXCL = OUT / "rankings_2025.csv"
RESID = ROOT / "data" / "derived" / "mechanisms" / "placebo_conditional_2025.csv"
FLAG_PDF = (ROOT / "03_dogrulama" / "DOGRULANMIS_PAKET" / "KAYNAK_DOKUMANLAR" / "oecd_ve_veri"
            / "OECD_PISA2025_asterisk-caution-notu.pdf")
CAP = 5.0                                   # PISA teknik standardı: genel dışlama ≤ %5
CELLS = [(sc, sp) for sc in ("all", "oecd") for sp in ("linear", "quadratic")]


def caution_flags() -> list[str]:
    """Uyarı listesi: 'Caution is required …' başlığından sonra gelen ardışık '<ad>*' satırları; yıldızsız ilk
    satırda biter (T1, 29 Eyl: önceki sürüm listeyi 'Israel' dizgisinde kesiyordu)."""
    text = "\n".join(p.extract_text() for p in PdfReader(FLAG_PDF).pages)
    lines = text[text.index("Caution is required"):].split("\n")
    start = next(i for i, ln in enumerate(lines) if re.match(r"^\W*[A-Z][^*]*\*\s*$", ln))
    names = []
    for ln in lines[start:]:
        m = re.match(r"^\W*([A-Z][^*]+?)\*\s*$", ln)
        if not m:
            break
        names.append(m.group(1).strip())
    assert len(names) == 6, f"uyarı listesi beklenen 6 değil: {names}"
    return names


def main() -> None:
    flags = caution_flags()
    ex = pd.read_csv(EXCL)
    ex["country_name"] = ex.country.str.rstrip("*").str.strip()
    assert not ex.country_name.duplicated().any(), "dışlama tablosunda yinelenen ülke adı"
    rs = pd.read_csv(RESID, encoding="utf-8-sig")
    miss = sorted(set(flags) - set(ex.country_name))
    assert not miss, f"uyarılı sistem dışlama tablosunda yok: {miss}"

    # --- sistem düzeyi birleşik tablo (artıklar geniş biçimde)
    assert not rs.duplicated(["country_name", "scope", "spec"]).any(), "artık tablosunda yinelenen satır"
    wide = rs.pivot(index=["iso3", "country_name"], columns=["scope", "spec"],
                    values=["residual", "rank_low"]).reset_index()
    wide.columns = ["_".join(c for c in col if c) for col in wide.columns]
    tab = ex.merge(wide, on="country_name", how="left")
    tab["caution_flag"] = tab.country_name.isin(flags)
    tab["over_cap"] = tab.overall > CAP
    no_resid = sorted(tab.loc[tab.residual_all_linear.isna(), "country_name"])
    unmatched = sorted(set(rs.country_name) - set(ex.country_name))
    assert not unmatched, f"artığı olup dışlama verisi olmayan sistem: {unmatched}"

    # --- birincil ve ikincil ilişkiler
    assoc = []
    for sc, sp in CELLS:
        d = rs[(rs.scope == sc) & (rs.spec == sp)].merge(ex, on="country_name")
        n_cell = int((rs.scope.eq(sc) & rs.spec.eq(sp)).sum())
        assert len(d) == n_cell, (sc, sp, len(d), n_cell)
        for col in ("overall", "within_rate"):
            rho, p_rho = stats.spearmanr(d[col], d.residual)
            r, p_r = stats.pearsonr(d[col], d.residual)
            assoc.append(dict(scope=sc, spec=sp, exclusion=col, n=len(d), spearman=round(float(rho), 3),
                              spearman_p=round(float(p_rho), 3), pearson=round(float(r), 3),
                              pearson_p=round(float(p_r), 3)))
    groups = []
    for sc, sp in CELLS:
        d = rs[(rs.scope == sc) & (rs.spec == sp)].merge(ex, on="country_name")
        hi, lo = d[d.overall > CAP], d[d.overall <= CAP]
        groups.append(dict(scope=sc, spec=sp, n_over=len(hi), n_under=len(lo),
                           median_resid_over=round(float(hi.residual.median()), 1),
                           median_resid_under=round(float(lo.residual.median()), 1),
                           mannwhitney_p=round(float(stats.mannwhitneyu(hi.residual, lo.residual,
                                                                        alternative="two-sided").pvalue), 3)))

    # --- %5'i yıldızsız aşanlar: sıralar (tüm katılımcılar, alttan)
    n_all = int((rs.scope.eq("all") & rs.spec.eq("linear")).sum())
    decile = math.floor(0.10 * n_all)
    over = tab[tab.over_cap].sort_values("overall", ascending=False)
    unflag = over[~over.caution_flag]
    rows = [dict(country=r.country_name, overall=round(r.overall, 2),
                 residual=None if pd.isna(r.residual_all_linear) else [round(r.residual_all_linear, 1),
                                                                        round(r.residual_all_quadratic, 1)],
                 rank_low=None if pd.isna(r.rank_low_all_linear) else [int(r.rank_low_all_linear),
                                                                        int(r.rank_low_all_quadratic)])
            for r in unflag.itertuples()]
    in_decile = [x["country"] for x in rows if x["rank_low"] and min(x["rank_low"]) <= decile]
    in_decile_both = [x["country"] for x in rows if x["rank_low"] and max(x["rank_low"]) <= decile]
    tur = tab[tab.country_name == "Türkiye"].iloc[0]

    summary = dict(
        script="analysis/56_exclusion_placebo_association.py", preregistered=False,
        note=("Post hoc: added after the Makale 1 v3 T1 (29 Sep 2026, finding #22) showed the channel-specificity "
              "claim rested on two cases; all cells reported."),
        sources=dict(exclusion=str(EXCL.relative_to(ROOT)), residual=str(RESID.relative_to(ROOT)),
                     caution_flags=str(FLAG_PDF.relative_to(ROOT))),
        cap_percent=CAP, caution_flagged=flags,
        n_exclusion_systems=len(ex), n_residual_systems_all=n_all,
        n_over_cap=int(len(over)), n_over_cap_flagged=int(over.caution_flag.sum()),
        n_over_cap_unflagged=int(len(unflag)),
        n_over_cap_unflagged_with_residual=int(sum(1 for x in rows if x["residual"])),
        over_cap_unflagged=rows, lower_decile_rank_max=decile,
        unflagged_in_lower_decile_any_spec=in_decile, unflagged_in_lower_decile_both_specs=in_decile_both,
        systems_without_residual=no_resid,
        association=assoc, groups=groups,
        turkiye=dict(overall=round(float(tur.overall), 2), over_cap=bool(tur.over_cap),
                     rank_low_all=[int(tur.rank_low_all_linear), int(tur.rank_low_all_quadratic)]),
    )
    cols = ["country_name", "iso3", "overall", "within_rate", "school_rate", "caution_flag", "over_cap"] + \
           [f"{v}_{sc}_{sp}" for v in ("residual", "rank_low") for sc, sp in CELLS]
    tab[cols].sort_values("overall", ascending=False).to_csv(OUT / "placebo_association_2025.csv", index=False,
                                                            encoding="utf-8")
    (OUT / "placebo_association_2025.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1),
                                                       encoding="utf-8")
    print(f"uyarılı: {flags}")
    print(f"%5 üstü {len(over)} (uyarılı {int(over.caution_flag.sum())}, uyarısız {len(unflag)}, "
          f"artığı olan {summary['n_over_cap_unflagged_with_residual']}); alt ondalık (sıra ≤ {decile}/{n_all}): "
          f"herhangi biçim {in_decile}, iki biçim {in_decile_both}")
    for a in assoc:
        print(f"  {a['scope']:4} {a['spec']:9} {a['exclusion']:11} n={a['n']:2} ρ={a['spearman']:+.3f} "
              f"(p={a['spearman_p']:.3f})  r={a['pearson']:+.3f} (p={a['pearson_p']:.3f})")
    for g in groups:
        print(f"  {g['scope']:4} {g['spec']:9} >%5 ortanca {g['median_resid_over']:+.1f} (n={g['n_over']}) · "
              f"≤%5 {g['median_resid_under']:+.1f} (n={g['n_under']}) · MW p={g['mannwhitney_p']:.3f}")


if __name__ == "__main__":
    main()
