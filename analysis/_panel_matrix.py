#!/usr/bin/env python3
"""Ortak yardımcı: dengeli (eksiksiz) ülke × döngü panel matrisleri.

Sentetik DiD (16), matris tamamlama + konformal çıkarım (17) ve makro-bölümleme (18) aynı
girdiyi kullansın diye tek yerde tanımlanır. Havuz mantığı `_synth_core.R::build_pool` ile aynı:
  pool ∈ {"stable_all_oecd", "stable_plus_ambiguous_oecd", "all_participants"}
  - stable_*: `institutional_screen.csv` sınıfları; OECD üyeleriyle sınırlı
  - drop_paper2015: 2015'te kâğıt tabanlı ülkeler çıkarılır (paper_based_2015.csv)
  - drop_asterisk: ilgili döngülerde OECD uyarı yıldızı taşıyan ülkeler çıkarılır (asterisk_cycles.csv)
  - tam seri şartı: ülke, istenen tüm döngülerde gözlenmeli (dengeli panel)
Fen 2006'dan başlar (2003 fen ölçeği karşılaştırılamaz — 03_synth ile aynı kural).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data" / "derived"

CYCLES = {"math": [2003, 2006, 2009, 2012, 2015, 2018, 2022, 2025],
          "reading": [2003, 2006, 2009, 2012, 2015, 2018, 2022, 2025],
          "science": [2006, 2009, 2012, 2015, 2018, 2022, 2025]}
POST = [2015, 2018, 2022, 2025]
TREATED_DEFAULT = "TUR"


def _load():
    panel = pd.read_csv(D / "analysis_panel.csv")
    screen = pd.read_csv(D / "institutional_screen.csv")
    paper = pd.read_csv(D / "paper_based_2015.csv")
    ast = pd.read_csv(D / "asterisk_cycles.csv")
    panel = panel[panel.iso3.notna() & (panel.iso3.str.len() == 3)]
    panel["oecd"] = pd.to_numeric(panel.oecd_member, errors="coerce").fillna(0) > 0
    return panel, screen, paper, ast


def build_matrix(outcome: str, pool: str = "stable_all_oecd", treated: str = TREATED_DEFAULT,
                 drop_paper2015: bool = True, drop_asterisk: bool = True, cycles: list[int] | None = None):
    """Geniş matris: satır = iso3 (tedavi birimi ilk satır), sütun = döngü; yalnız tam seriler."""
    panel, screen, paper, ast = _load()
    cycles = cycles or CYCLES[outcome]
    col = f"{outcome}_mean"
    wide = panel.pivot_table(index="iso3", columns="cycle", values=col, aggfunc="first")
    wide = wide.reindex(columns=cycles)
    complete = wide.dropna(how="any")

    cls = {"stable_all_oecd": ["stable_clean", "stable_corrupt"],
           "stable_plus_ambiguous_oecd": ["stable_clean", "stable_corrupt", "ambiguous"],
           "all_participants": None}[pool]
    cand = set(complete.index) - {treated}
    if cls is not None:
        cand &= set(screen[screen["class"].isin(cls)].iso3)
        oecd_iso = set(panel[panel.oecd].iso3)
        cand &= oecd_iso
    else:
        # tüm katılımcılar: yine de tedavi/otokratikleşen sınıfları çıkar (kontrol kirlenmesin)
        treated_cls = set(screen[screen["class"].str.startswith("treated")].iso3)
        cand -= treated_cls
    if drop_paper2015:
        cand -= set(paper.iso3)
    if drop_asterisk:
        cand -= set(ast[ast.cycle.isin(cycles)].iso3)
    if treated not in complete.index:
        raise ValueError(f"{treated} için {outcome} tam seri yok")
    donors = sorted(cand)
    mat = complete.loc[[treated] + donors]
    mat.index.name = "iso3"
    return mat


if __name__ == "__main__":
    out = D / "panel_matrices"
    out.mkdir(exist_ok=True)
    for pool in ["stable_all_oecd", "stable_plus_ambiguous_oecd", "all_participants"]:
        for oc in ["math", "reading", "science"]:
            m = build_matrix(oc, pool)
            m.to_csv(out / f"{oc}_{pool}.csv")
            print(f"{oc:8s} {pool:28s} donörler={len(m) - 1:3d} döngüler={list(m.columns)}")
            if len(m) - 1 <= 12:
                print("          ", " ".join(m.index[1:]))
