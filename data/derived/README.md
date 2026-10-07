# PISA Annex A2 extract — provenance

`annex_extract.csv` (288 rows, UTF-8 with BOM) holds Annex A2 sampling/coverage/response-rate
figures for the requested economies across seven PISA cycles.

Values are **copied verbatim** from the source workbook cells (full stored precision, `m`/`c`
codes and blanks left as-is). Nothing is computed, rounded, or recoded.

## Columns

| CSV column | Meaning |
|---|---|
| `country` | Economy label exactly as printed in the source coverage table (col 0). `Turkey` in 2006–2015, `Türkiye` in 2022/2025; `Czech Republic` vs `Czechia`; `Slovak Republic`. |
| `cycle` | PISA cycle year (2025, 2022, 2018, 2015, 2012, 2009, 2006). |
| `coverage_index3` | Coverage Index 3 (coverage of the national 15-year-old population). |
| `overall_exclusion_pct` | Overall exclusion rate (%) — total, weighted. |
| `language_exclusion_pct` | **Blank in every cycle — column does not exist.** See "Not located" below. |
| `school_rr_before` | Weighted school participation rate **before** replacement (%). |
| `school_rr_after` | Weighted school participation rate **after** replacement (%). |
| `student_rr` | Weighted student participation rate after replacement (%). |
| `replacement_schools` | **Blank in every cycle — column does not exist.** See "Not located" below. |
| `asterisk_flag` | `*` = caution flag from the source. Populated only for 2025 (see below); blank otherwise. |
| `source_file` | Workbook the row was read from (repo-relative path). |
| `sheet` | Sheet(s) contributing values, `;`-separated. |
| `row` | Source cell provenance as `Sheet!<1-based-worksheet-row>`, `;`-separated (one entry per contributing sheet). |

## Row selection

A cycle's row is emitted when the economy's (normalised) name is in the requested set:
the 38 current OECD members **or** the explicitly named list (Türkiye, Georgia, Hungary,
Serbia, Poland, Greece, Mexico, Brazil, El Salvador, Kazakhstan, Estonia). Selection is by
name (not by the workbook's OECD/Partners block), so current OECD members that participated
as *partners* in an earlier cycle (e.g. Chile, Estonia, Israel, Latvia, Lithuania, Slovenia,
Colombia in 2006) are also included, as are the named partner economies. Row counts per
cycle: 2025=43, 2022=42, 2018=42, 2015=41, 2012=41, 2009=40, 2006=39 (an economy is present
only if it participated that cycle).

## Exact file / sheet / column map per cycle

Column indices below are **0-based positions in the data row** (col 0 = country label).
They were fixed against the `(1)…(15)` column-number header row and independently
verified: Australia's Coverage Index 3 in every cycle matches the cross-cycle CI3 series
printed in the 2025 workbook `Table I.A2.1`.

### 2025 — `data/pisa/2025/annex_tables/pe3lsg.xlsx`
- `coverage_index3` ← sheet **`Table I.A2.1`** (a cross-cycle enrolment/coverage table),
  **col 4** = "Coverage Index 3" under the "PISA 2025" block. Data rows are a single
  alphabetical list (no OECD/Partners split); header block at rows 6–8, data from row 9.
- `overall_exclusion_pct`, `school_rr_*`, `student_rr`: **not present** — the 2025 Annex A2
  StatLink workbook contains only `Table I.A2.1` (enrolment change / cross-cycle coverage),
  `I.A2.2` (modal ISCED level) and `I.A2.3` (grade distribution). It publishes **no**
  exclusion or response-rate tables. Those figures for 2025 exist only in the full
  Volume I PDF (`data/pisa/2025/73451bc5-en.pdf`), not as an Excel StatLink.
- `asterisk_flag`: `*` set for **Canada, Netherlands, New Zealand, Norway, United States**
  (of the selected economies). Source: the caution list printed on the workbook's `TOC`
  sheet ("Caution is required … one or more PISA sampling standards were not met":
  Albania*, Canada*, Netherlands*, New Zealand*, Norway*, United States*). Albania is on
  that list but is not in the requested set, so it is not in the output.

### 2022 — `data/pisa/2022/hpg9nd.xlsx`
- `coverage_index3` ← **`Table I.A2.1`** col 15; `overall_exclusion_pct` ← **`Table I.A2.1`** col 12.
  (NB: the descriptive header text in row 9 is shifted one column left of the data; the
  `(1)…(15)` number row and the data columns are the authority — CI3 is `(15)`, overall
  exclusion is `(12)`.)
- `school_rr_before` ← **`Table I.A2.6`** col 1; `school_rr_after` ← col 6; `student_rr` ← col 11.

### 2018 — `data/pisa/2018/EDU-2019-4228-EN-T010.XLSX`
- `coverage_index3` ← **`Table I.A2.1`** col 15; `overall_exclusion_pct` ← col 12.
- `school_rr_before` ← **`Table I.A2.6`** col 1; `school_rr_after` ← col 6; `student_rr` ← col 11.

### 2015 — `data/pisa/2015/982016061P1G117.XLSX`
- `coverage_index3` ← **`Table A2.1`** col 15; `overall_exclusion_pct` ← col 12.
- `school_rr_before` ← **`Table A2.3`** col 1; `school_rr_after` ← col 6; `student_rr` ← col 11.

### 2012 — `data/pisa/2012/982013041P1T011.xls`
- `coverage_index3` ← **`Table A2.1`** col 15; `overall_exclusion_pct` ← col 12.
- `school_rr_before` ← **`Table A2.3`** col 1; `school_rr_after` ← col 6; `student_rr` ← col 11.

### 2009 — `data/pisa/2009/982010071P1G005.XLS`
- `coverage_index3` ← **`TAB A2.1`** col 15; `overall_exclusion_pct` ← col 12.
- `school_rr_before` ← **`TAB A2.3`** col 1; `school_rr_after` ← col 6; `student_rr` ← col 11.

### 2006 — `data/pisa/2006/982007011P1G006.XLS`
- `coverage_index3` ← **`TA2.1`** col 15; `overall_exclusion_pct` ← col 12.
- `school_rr_before` ← **`TA2.3`** col 1; `school_rr_after` ← col 6; `student_rr` ← col 11.

## Columns / cycles that could NOT be located

- **`language_exclusion_pct` — not found in any cycle.** No PISA Annex A2 table publishes a
  language-based exclusion *percentage*. The exclusions tables (`I.A2.4` in 2018/2022,
  `A2.2`/`TA2.2` in 2006–2015) give exclusion **counts** by reason, including
  "excluded because of language" (Code 3, unweighted and weighted counts). Since the target
  column is a percentage and the task forbids computing, this column is left blank
  throughout. The counts remain available in those sheets if needed later.
- **`replacement_schools` — not found in any cycle.** The A2 response-rate tables
  (`I.A2.6` / `A2.3` / `TA2.3`) report, before and after replacement, the weighted rates and
  the number of *responding* and *responding+non-responding* schools, but no column labelled
  "replacement schools" (a replacement count would have to be derived, which is not
  permitted). Left blank throughout.
- **2025 exclusion & response-rate columns** (`overall_exclusion_pct`, `school_rr_before`,
  `school_rr_after`, `student_rr`): not in the 2025 Annex A2 StatLink workbook (see 2025
  section). Blank for all 2025 rows.
- **`asterisk_flag` for 2022, 2018, 2015, 2012, 2009, 2006:** blank. Those workbooks carry no
  caution list on their TOC and no `*` on any country label in the A2 sheets. Where a cycle
  used caution annotations (2022), they appear only in the full Volume I PDF Reader's Guide,
  not in this Annex A2 workbook.
- **Adjudicated-region rows** (`*_Regions`/`_regions` sheets, and `I.A2.3/5/7` regional
  tables) were intentionally not used — country/economy-level rows only.
- Pre-StatLink cycles (**PISA 2003 and earlier**) publish no Annex A2 Excel workbook; only the
  printed PDF tables exist, so they are not in this extract.

The extraction helper that produced this file is not part of this repository.
