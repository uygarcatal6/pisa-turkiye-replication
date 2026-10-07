# -*- coding: utf-8 -*-
"""
02_institutional_screen.py  -- PISA proposal v2, section 4.1-4.2 donor-pool institutional screen.

Builds the institutional screen for every PISA-participating country identifiable from
the ERT / V-Dem ISO3 universe, following proposal rules (pisa_proposal_v2_TR_EN.md, 4.1-4.2):

  STABLE  = (no ERT autocratization OR democratization episode overlapping 2013-2025)
            AND (v2x_libdem change 2013->latest lies within the CI band:
                 latest point inside 2013 [codelow,codehigh] AND 2013 point inside latest band)
  stable_clean   = STABLE and mean CPI 2013-2025 > 50
  stable_corrupt = STABLE and mean CPI 2013-2025 <= 50
  TREATED        = has an episode overlapping the window; record type/start/end.
                   autocratization-then-democratization  -> treated_reversed
  ambiguous      = no episode but libdem moved outside CI, or data missing.

Every value comes from a file; each output row carries provenance columns.
Outputs under data/derived/. Run with the system Python 3.13 (pandas, pyreadr, openpyxl).
"""
import os, re, sys, zipfile, subprocess
import xml.etree.ElementTree as ET
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace("\\", "/")
ERT_CSV   = os.path.join(ROOT, "data/governance/ert/ert.csv")
VDEM_RDATA= os.path.join(ROOT, "data/governance/vdem/vdem.RData")
CPI2025   = os.path.join(ROOT, "data/governance/cpi/CPI2025_Results.xlsx")
CPI2024   = os.path.join(ROOT, "claim_check/evidence/cpi/CPI2024-Results-and-trends.xlsx")
PISA2025_VOL1 = os.path.join(ROOT, "data/pisa/2025/73451bc5-en.pdf")
OUTDIR = os.path.join(ROOT, "data/derived")
os.makedirs(OUTDIR, exist_ok=True)

WIN_START, WIN_END = 2013, 2025
BASE_YEAR   = 2013
# Proposal 4.1 states the CI test as "compare libdem_2024 with the 2013 codelow/codehigh
# band, and vice versa" -> the point-estimate comparison year is 2024. V-Dem v16 also carries
# 2025, but its 2025 codings are the most recent/least settled; using them would flag several
# long-standing democracies (Belgium, Spain, Iceland, Lithuania, New Zealand) as 'ambiguous'.
# We therefore use 2024 as the primary "latest" year (faithful to the rule) and report the
# 2025 result as a sensitivity check.
LATEST_YEAR = 2024
SENS_YEAR   = 2025
CPI_YEARS   = list(range(2013, 2026))   # 2013..2025 inclusive

def log(*a): print(*a, flush=True)

# --------------------------------------------------------------------------------------
# 1. V-Dem liberal-democracy index (point + confidence band), from vdem.RData
# --------------------------------------------------------------------------------------
def load_vdem():
    import pyreadr
    v = pyreadr.read_r(VDEM_RDATA)["vdem"]
    cols = ["country_name","country_text_id","year",
            "v2x_libdem","v2x_libdem_codelow","v2x_libdem_codehigh"]
    v = v[cols].copy()
    v["year"] = v["year"].astype(int)
    v = v[(v["year"]>=2010)&(v["year"]<=2025)]
    return v

# --------------------------------------------------------------------------------------
# 2. ERT episodes overlapping the 2013-2025 window
# --------------------------------------------------------------------------------------
def load_ert_episodes():
    df = pd.read_csv(ERT_CSV)
    def eps(sub, kind):
        col_id, s, e = f"{kind}_ep_id", f"{kind}_ep_start_year", f"{kind}_ep_end_year"
        rows = sub[sub[f"{kind}_ep"]==1][[col_id, s, e]].dropna(subset=[s]).drop_duplicates()
        out=[]
        for _, r in rows.iterrows():
            st=int(r[s]); en=int(r[e]) if pd.notna(r[e]) else st
            if st<=WIN_END and en>=WIN_START:            # overlaps window
                out.append((st, en, str(r[col_id])))
        return sorted(set(out))
    result={}
    for iso, sub in df.groupby("country_text_id"):
        result[iso] = {"aut": eps(sub,"aut"), "dem": eps(sub,"dem")}
    return result, df

# --------------------------------------------------------------------------------------
# 3. CPI time-series (strict-OOXML workbook -> manual XML parse), mean 2013-2025
# --------------------------------------------------------------------------------------
def _read_strict_sheet(path, sheetfile):
    L=lambda t: t.split('}')[-1]
    z=zipfile.ZipFile(path)
    ss=[]
    try:
        for si in ET.fromstring(z.read('xl/sharedStrings.xml')):
            if L(si.tag)=='si':
                ss.append(''.join(t.text or '' for t in si.iter() if L(t.tag)=='t'))
    except KeyError:
        pass
    def col_idx(ref):
        s=''.join(ch for ch in ref if ch.isalpha()); n=0
        for ch in s: n=n*26+(ord(ch)-64)
        return n-1
    root=ET.fromstring(z.read('xl/'+sheetfile))
    rows=[]
    for row in root.iter():
        if L(row.tag)!='row': continue
        cells={}
        for c in row:
            if L(c.tag)!='c': continue
            ref=c.attrib.get('r','A1'); t=c.attrib.get('t'); val=None
            for ch in c:
                if L(ch.tag)=='v': val=ch.text
                elif L(ch.tag)=='is':
                    val=''.join(x.text or '' for x in ch.iter() if L(x.tag)=='t')
            if t=='s' and val is not None: val=ss[int(val)]
            cells[col_idx(ref)]=val
        if cells:
            m=max(cells); rows.append([cells.get(i) for i in range(m+1)])
    return rows

def _cpi_sheet_target(path, want="Timeseries"):
    L=lambda t:t.split('}')[-1]
    z=zipfile.ZipFile(path)
    wb=ET.fromstring(z.read('xl/workbook.xml'))
    rels=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    ridmap={r.attrib['Id']:r.attrib['Target'] for r in rels}
    for sh in wb.iter():
        if L(sh.tag)=='sheet':
            a=sh.attrib
            name=a.get('name','')
            rid=[v for k,v in a.items() if L(k)=='id']
            if want.lower() in name.lower():
                return name, 'worksheets/'+ridmap[rid[0]].split('/')[-1]
    raise RuntimeError("timeseries sheet not found in "+path)

def load_cpi_timeseries():
    """Return dict iso3 -> {year: score} plus provenance (file, sheet)."""
    sheet_name, sheet_file = _cpi_sheet_target(CPI2025, "Timeseries")
    rows = _read_strict_sheet(CPI2025, sheet_file)
    # locate header row containing 'ISO3'
    hdr_i = next(i for i,r in enumerate(rows) if any((str(c or '')).strip()=="ISO3" for c in r))
    hdr = [str(c or '').strip() for c in rows[hdr_i]]
    iso_col = hdr.index("ISO3")
    ctry_col= 0
    year_col={}
    for j,h in enumerate(hdr):
        m=re.match(r"CPI score (\d{4})", h)
        if m: year_col[int(m.group(1))]=j
    data={}
    names={}
    for r in rows[hdr_i+1:]:
        if iso_col>=len(r): continue
        iso=(str(r[iso_col] or '')).strip()
        if not iso or len(iso)!=3: continue
        yd={}
        for y,j in year_col.items():
            if j<len(r) and r[j] not in (None,''):
                try: yd[y]=float(r[j])
                except ValueError: pass
        data[iso]=yd
        names[iso]=str(r[ctry_col] or '').strip()
    return data, names, sheet_name, os.path.basename(CPI2025), sorted(year_col)

# --------------------------------------------------------------------------------------
# 4. OECD membership -- parsed from PISA 2025 Vol I, Table 1 (printed p.47 / PDF p.49)
# --------------------------------------------------------------------------------------
NAME2ISO_ALIAS = {
    "Australia":"AUS","Austria":"AUT","Belgium":"BEL","Canada":"CAN","Chile":"CHL",
    "Colombia":"COL","Costa Rica":"CRI","Czechia":"CZE","Czech Republic":"CZE","Denmark":"DNK",
    "Estonia":"EST","Finland":"FIN","France":"FRA","Germany":"DEU","Greece":"GRC","Hungary":"HUN",
    "Iceland":"ISL","Ireland":"IRL","Israel":"ISR","Italy":"ITA","Japan":"JPN","Korea":"KOR",
    "Latvia":"LVA","Lithuania":"LTU","Luxembourg":"LUX","Mexico":"MEX","Netherlands":"NLD",
    "New Zealand":"NZL","Norway":"NOR","Poland":"POL","Portugal":"PRT","Slovak Republic":"SVK",
    "Slovenia":"SVN","Spain":"ESP","Sweden":"SWE","Switzerland":"CHE","Turkiye":"TUR",
    "Turkey":"TUR","United Kingdom":"GBR","United States":"USA",
}
def parse_oecd_members():
    txt = subprocess.run(["pdftotext","-f","49","-l","49",PISA2025_VOL1,"-"],
                         capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    # block between the two headers
    a = txt.find("OECD Member countries in PISA 2025")
    b = txt.find("Partner countries and economies")
    block = txt[a:b]
    isos=set(); found=[]
    for line in block.splitlines():
        s=re.sub(r"\d","",line).replace("\ufffd","").strip()   # drop footnote digits / bad chars
        s=s.replace("T rkiye","Turkiye").replace("Trkiye","Turkiye")
        if s in NAME2ISO_ALIAS:
            isos.add(NAME2ISO_ALIAS[s]); found.append(s)
    return isos, found, "PISA 2025 Vol I (73451bc5-en.pdf) Table 1, printed p.47 / PDF p.49"

# --------------------------------------------------------------------------------------
# classification
# --------------------------------------------------------------------------------------
def fmt_eps(lst):
    return ";".join(f"{s}-{e}" for s,e,_ in lst) if lst else ""

def classify(aut, dem, change_outside_ci, have_libdem, cpi_mean):
    if aut and dem:
        aut_min=min(s for s,_,_ in aut); dem_min=min(s for s,_,_ in dem)
        if aut_min<=dem_min:
            return "treated_reversed", f"autocratization {aut_min} then democratization {dem_min} (reversal)"
        return "treated_autocratization", f"democratization {dem_min} then autocratization {aut_min}; ends in autocratization"
    if aut:
        return "treated_autocratization", f"ERT autocratization episode(s): {fmt_eps(aut)}"
    if dem:
        return "treated_democratization", f"ERT democratization episode(s): {fmt_eps(dem)}"
    # no episode
    if not have_libdem:
        return "ambiguous", "no ERT episode but V-Dem libdem missing for 2013 or latest"
    if change_outside_ci:
        return "ambiguous", "no ERT episode but libdem 2013->latest change outside the CI band"
    if pd.isna(cpi_mean):
        return "ambiguous", "institutionally stable but no CPI 2013-2025 data to split clean/corrupt"
    if cpi_mean>50:
        return "stable_clean", "no episode; libdem change within CI; mean CPI 2013-2025 > 50"
    return "stable_corrupt", "no episode; libdem change within CI; mean CPI 2013-2025 <= 50"

# --------------------------------------------------------------------------------------
def main():
    log("Loading V-Dem ...")
    v = load_vdem()
    iso2name = dict(zip(v["country_text_id"], v["country_name"]))
    def libdem_at(iso, yr):
        r=v[(v["country_text_id"]==iso)&(v["year"]==yr)]
        if len(r)==0 or pd.isna(r["v2x_libdem"].iloc[0]): return None
        x=r.iloc[0]
        return (float(x["v2x_libdem"]), float(x["v2x_libdem_codelow"]), float(x["v2x_libdem_codehigh"]))

    log("Loading ERT episodes ...")
    ert, ert_df = load_ert_episodes()

    log("Loading CPI time-series ...")
    cpi, cpi_names, cpi_sheet, cpi_file, cpi_years_avail = load_cpi_timeseries()
    cpi_alias={"KSV":"XKX"}   # Kosovo code differs between CPI and V-Dem
    def cpi_mean_for(iso):
        key=iso
        if iso not in cpi:
            for k,val in cpi_alias.items():
                if val==iso and k in cpi: key=k; break
        yd=cpi.get(key,{})
        vals=[yd[y] for y in CPI_YEARS if y in yd]
        return (sum(vals)/len(vals) if vals else float("nan")), len(vals)

    log("Parsing OECD membership ...")
    oecd_iso, oecd_found, oecd_prov = parse_oecd_members()
    log(f"  OECD members parsed: {len(oecd_iso)} ({len(oecd_found)} names)")
    if len(oecd_iso)!=38:
        log("  WARNING: expected 38 OECD members, got", len(oecd_iso), sorted(oecd_iso))

    # universe: every ISO3 with V-Dem libdem data in the window
    universe = sorted(set(v.dropna(subset=["v2x_libdem"])["country_text_id"].unique()))
    rows=[]
    flips=[]   # sensitivity: class differs if latest=2024 instead of 2025
    for iso in universe:
        name = iso2name.get(iso, iso)
        aut = ert.get(iso,{}).get("aut",[])
        dem = ert.get(iso,{}).get("dem",[])
        b   = libdem_at(iso, BASE_YEAR)
        lat = libdem_at(iso, LATEST_YEAR)
        have = (b is not None and lat is not None)
        if have:
            (v13,lo13,hi13)=b; (vl,lol,hil)=lat
            delta=vl-v13
            latest_in_2013 = lo13<=vl<=hi13
            base_in_latest = lol<=v13<=hil
            outside = not (latest_in_2013 and base_in_latest)
        else:
            v13=lo13=hi13=vl=lol=hil=delta=float("nan"); outside=False
        cpi_mean, cpi_n = cpi_mean_for(iso)
        klass, reason = classify(aut, dem, outside, have, cpi_mean)

        # sensitivity check: what if "latest" were SENS_YEAR (2025) instead of 2024
        latS=libdem_at(iso,SENS_YEAR)
        if (not aut and not dem) and b is not None and latS is not None:
            (v13b,lo13b,hi13b)=b;(vS,loS,hiS)=latS
            outS = not ((lo13b<=vS<=hi13b) and (loS<=v13b<=hiS))
            kS,_=classify(aut,dem,outS,True,cpi_mean)
            if kS!=klass: flips.append((iso,name,klass,kS))

        rows.append(dict(
            iso3=iso, country=name,
            oecd_member=int(iso in oecd_iso),
            libdem_2013=round(v13,4) if pd.notna(v13) else "",
            libdem_2013_lo=round(lo13,4) if pd.notna(lo13) else "",
            libdem_2013_hi=round(hi13,4) if pd.notna(hi13) else "",
            libdem_latest=round(vl,4) if pd.notna(vl) else "",
            libdem_latest_lo=round(lol,4) if pd.notna(lol) else "",
            libdem_latest_hi=round(hil,4) if pd.notna(hil) else "",
            delta_libdem=round(delta,4) if pd.notna(delta) else "",
            change_outside_ci=int(outside) if have else "",
            ert_aut_episodes=fmt_eps(aut),
            ert_dem_episodes=fmt_eps(dem),
            cpi_mean_2013_2025=round(cpi_mean,2) if pd.notna(cpi_mean) else "",
            cpi_n_years=cpi_n,
            **{"class":klass},
            reason=reason,
            libdem_latest_year=LATEST_YEAR,
            src_vdem="vdem.RData (V-Dem v16); rows country_text_id=%s year in {%d,%d}; cols v2x_libdem(_codelow/_codehigh)"%(iso,BASE_YEAR,LATEST_YEAR),
            src_ert="ert.csv rows country_text_id=%s; cols aut_ep*/dem_ep_start_year/end_year"%iso,
            src_cpi="%s sheet '%s'; rows ISO3=%s; cols 'CPI score 2013..2025'"%(cpi_file,cpi_sheet,iso),
            src_oecd=oecd_prov,
        ))
    scr=pd.DataFrame(rows)
    scr_path=os.path.join(OUTDIR,"institutional_screen.csv")
    scr.to_csv(scr_path, index=False, encoding="utf-8-sig")
    log("wrote", scr_path, len(scr),"rows")

    # ----- (b) paper-based 2015 -----
    paper=[("ALB","Albania"),("DZA","Algeria"),("ARG","Argentina"),("GEO","Georgia"),
           ("IDN","Indonesia"),("JOR","Jordan"),("KAZ","Kazakhstan"),("XKX","Kosovo"),
           ("LBN","Lebanon"),("MKD","Macedonia (North Macedonia)"),("MLT","Malta"),
           ("MDA","Moldova"),("ROU","Romania"),("TTO","Trinidad and Tobago"),("VNM","Viet Nam")]
    src_j="Jerrim et al. 2018, 'The Impact of Computer-Based Assessment on PISA 2015', footnote 1, p.1 (docs/literature/Jerrim_Revised_Main_Body_27_11_2017_Clean.pdf; also claim_check/evidence/literature/jerrim2018.pdf p.1)"
    pb=pd.DataFrame([dict(iso3=i,country=c,mode_2015="paper",source_file=src_j) for i,c in paper])
    pb_path=os.path.join(OUTDIR,"paper_based_2015.csv"); pb.to_csv(pb_path,index=False,encoding="utf-8-sig")
    log("wrote", pb_path, len(pb),"rows")

    # ----- (c) asterisk / caution cycles -----
    ast=[]
    F25="data/pisa/2025/73451bc5-en.pdf"; F22="data/pisa/2022/53f23881-en.pdf"
    F18="data/pisa/2018/5f07c754-en.pdf"; F15="data/pisa/2015/9789264266490-en.pdf"
    # 2015 -- not fully comparable (Reader's guide / Ch.2 text p.83 & note 2 p.108)
    for iso,c,why in [("ARG","Argentina","sample did not cover full target population (coverage)"),
                      ("MYS","Malaysia","did not meet school response-rate standards"),
                      ("KAZ","Kazakhstan","construct-coverage issue; results not fully comparable [B2-108]")]:
        ast.append(dict(cycle=2015,iso3=iso,country=c,flag="not_fully_comparable / not in most figures",
                        reason=why,source_file=F15,source_page="PDF p.83 (printed 61) and note 2, PDF p.108 (printed 86)"))
    # 2018 -- superscript '1': data did not meet standards but accepted as largely comparable
    for iso,c in [("HKG","Hong Kong (China)"),("NLD","Netherlands"),("PRT","Portugal"),("USA","United States")]:
        ast.append(dict(cycle=2018,iso3=iso,country=c,flag="annotation '1' (did not meet PISA technical standards, accepted as largely comparable)",
                        reason="see Annexes A2 and A4",source_file=F18,
                        source_page="footnote under Table I.4.1, PDF p.60 (printed 58); annotation used on tables PDF p.59-64"))
    # 2022 -- 13 adjudicated entities reported with annotations (Reader's Guide)
    e22=[("CAN","Canada","student resp. 77% (7/10 provinces short)"),
         ("IRL","Ireland","student resp. 77%"),
         ("NZL","New Zealand","excl. 5.8%; student resp. 72%; school resp. short"),
         ("GBR","United Kingdom (excluding Scotland)","student resp. 75%; school resp. short"),
         ("GBR-SCT","Scotland (UK region)","excl. 6.6%; student resp. 79%"),
         ("AUS","Australia","excl. 6.9%; student resp. 76%"),
         ("DNK","Denmark","below sampling standard (Reader's Guide list)"),
         ("HKG","Hong Kong (China)","student resp. 75%; school resp. short"),
         ("JAM","Jamaica","student resp. 68%"),
         ("LVA","Latvia","below sampling standard (Reader's Guide list)"),
         ("NLD","Netherlands","below sampling standard (Reader's Guide list)"),
         ("PAN","Panama","student resp. 77%"),
         ("USA","United States","excl. 6.1%; school/student resp. below standard")]
    for iso,c,why in e22:
        ast.append(dict(cycle=2022,iso3=iso,country=c,flag="reported with annotation (adjudicated entity not meeting >=1 sampling standard)",
                        reason=why,source_file=F22,source_page="Reader's Guide, PDF p.18-22 (printed 16-20)"))
    # 2025 -- Reader's Guide, reporting with annotation (asterisk)
    e25=[("CAN","Canada","full reporting w/ asterisk; school resp. 82% (after repl.), student 77%"),
         ("NLD","Netherlands","full reporting w/ asterisk; excl. 9.3%; school 88%/student 78%"),
         ("NZL","New Zealand","full reporting w/ asterisk; excl. 8.1%; school 52%/student 76%"),
         ("NOR","Norway","full reporting w/ asterisk (Reader's Guide list)"),
         ("ALB","Albania","limited reporting w/ asterisk; school resp. 76%; small schools not contacted; no trend"),
         ("USA","United States","limited reporting w/ asterisk; excl. 6.9%; school 54%/student 76%")]
    for iso,c,why in e25:
        ast.append(dict(cycle=2025,iso3=iso,country=c,flag="reporting with annotation (asterisk)",
                        reason=why,source_file=F25,source_page="Reader's Guide, PDF p.18-20 (printed 16-18)"))
    # 2025 subnational asterisk entities recorded for completeness (not country-level)
    for c in ["Alberta (CAN)","British Columbia (CAN)","Manitoba (CAN)","Newfoundland and Labrador (CAN)",
              "Nova Scotia (CAN)","Ontario (CAN)","Quebec (CAN)","Murcia (Spain)"]:
        ast.append(dict(cycle=2025,iso3="",country=c,flag="reporting with annotation (asterisk) - subnational region",
                        reason="subnational entity (not a country-level PISA unit)",source_file=F25,
                        source_page="Reader's Guide, PDF p.18-20 (printed 16-18)"))
    ac=pd.DataFrame(ast)
    ac_path=os.path.join(OUTDIR,"asterisk_cycles.csv"); ac.to_csv(ac_path,index=False,encoding="utf-8-sig")
    log("wrote", ac_path, len(ac),"rows")

    # ----- (d) ledger cross-checks -----
    log("\n==================== LEDGER CROSS-CHECKS ====================")
    def show(iso):
        r=scr[scr["iso3"]==iso]
        if len(r)==0: log(f"  {iso}: NOT FOUND"); return
        r=r.iloc[0]
        log(f"  {iso} {r['country']:<12} class={r['class']:<24} aut=[{r['ert_aut_episodes']}] dem=[{r['ert_dem_episodes']}] "
            f"cpi_mean={r['cpi_mean_2013_2025']} oecd={r['oecd_member']} | {r['reason']}")
    for iso in ["TUR","GEO","HUN","SRB","POL","EST"]: show(iso)
    log("  Expected: TUR treated_autocratization (ERT episode TUR_2005_2017 -> starts 2005, i.e. <=2013);")
    log("            GEO start 2017; HUN 2006; SRB 2010; POL reversed (aut 2016 -> dem 2023); EST stable_clean.")

    log("\n==================== COUNTS PER CLASS ====================")
    for k,n in scr["class"].value_counts().items(): log(f"  {k:<26} {n}")
    log(f"  TOTAL {len(scr)}")
    log(f"  OECD members in screen: {int(scr['oecd_member'].sum())}")
    if flips:
        log(f"\n  Sensitivity (class would differ if latest={SENS_YEAR} were used instead of {LATEST_YEAR}):")
        for iso,name,kp,ks in flips: log(f"    {iso} {name}: {LATEST_YEAR}->{kp} vs {SENS_YEAR}->{ks}")
    else:
        log(f"\n  Sensitivity: no country's stable/ambiguous class changes between latest={LATEST_YEAR} and {SENS_YEAR}.")
    return scr, flips, oecd_found

if __name__=="__main__":
    main()
