# PISA trends in Türkiye, 2003–2025: replication code and derived data

This repository holds the analysis code and the **country-level derived data** behind a study of
Türkiye's PISA results between 2003 and 2025: placebo-domain comparisons, synthetic control and
difference-in-differences checks, exclusion and sampling-frame analyses, effort and timing indicators,
and robustness and power analyses.

Raw PISA files are **not** redistributed. They are public and can be downloaded from the OECD.
No student- or school-level records are included. All tables in `data/derived/` are aggregates
(countries, cycles, strata or school types) computed from the OECD public-use files and published OECD tables.

## Contents

| Path | What |
| :--- | :--- |
| `analysis/` | Analysis scripts (Python and R), numbered roughly in the order they were written. `_pisa_puf.py` is the shared reader and BRR/Rubin estimator for PISA public-use files. `run_all.py` runs the pipeline in dependency order. |
| `analysis/RESULTS*.md` | Working notes that document each analysis phase (in Turkish). |
| `data/derived/` | Derived data written by the scripts (CSV/JSON). `data/derived/README.md` and the other `*_README.md` files describe them. |
| `requirements.txt`, `analysis/R_PACKAGES.txt` | Python and R package versions. |

Comments and working notes are mostly in Turkish. Each script's header lists its inputs and outputs.

## Reproducing

1. Python 3.13 and `pip install -r requirements.txt`. The R steps (synthetic control, `did`, `synthdid`) need R 4.x
   and the packages in `analysis/R_PACKAGES.txt`.
2. Download the raw inputs to the paths named in the script headers (relative to the repository root):
   PISA student and school public-use files under `data/pisa_microdata/<year>/`, OECD report tables under
   `data/pisa/<year>/`, and governance indicators (World Bank WGI, Transparency International CPI) under
   `data/governance/`.
3. From the repository root, run `python analysis/run_all.py --dry-run` to see the steps, then
   `python analysis/run_all.py` (light steps; heavy microdata steps reuse cached outputs) or `--heavy` for the full pipeline.
   Heavy steps unpack large `.sav` files into the system temp folder; set `PISA_WORK` (scripts 07, 12a, 12b) or
   `PISA_TMP` (scripts 35, 43–45, 48–51) to use another location. R scripts can be pointed at the repository root
   with `PISA_ROOT`.

Some script headers mention files that are not part of this repository: literature PDFs, manuscripts and
internal verification notes. They are not needed to reproduce the derived data.

For anonymity, comments and notes in this copy were edited: the author's name, local paths, internal file references and
most review notes were removed. Code logic and data values are unchanged, except for the hard-coded root and temp folders,
which now resolve relative to the repository. SHA-256 values quoted in the notes refer to the unedited originals.

## Small cells

Tables that report counts or estimates for school-type strata with fewer than five sampled schools are not
published here: `data/derived/turkiye_school_type_composition.csv`, `data/derived/empirical_fixes/e6_strata_map.csv`
and `data/derived/empirical_fixes/e9_school_type_sector.csv`. Scripts 08, 48 and 50 rebuild them from the OECD
public-use files. Weighted population shares of these strata remain in
`data/derived/turkiye_composition_drift.csv` and `data/derived/empirical_fixes/e6_trough_decomposition.csv` (shares only,
no counts or scores).

## Licence

Code (`*.py`, `*.R`): MIT. Derived data and documentation: CC BY 4.0. See `LICENSE`. The underlying PISA data are
© OECD and remain under the OECD's terms.
