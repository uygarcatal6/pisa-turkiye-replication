#!/usr/bin/env python3
"""PISA analiz hattı — tek giriş noktası (Python + R).

Kullanım (proje kökünden):
    python analysis/run_all.py                 # hafif adımlar (ağır mikroveri adımları atlanır, önbellekteki çıktıları kullanılır)
    python analysis/run_all.py --heavy         # ağır mikroveri adımları dahil, bağımlılık sırasıyla tam hat
    python analysis/run_all.py --only 19 34    # yalnızca seçili adımlar (ağır olsa da)
    python analysis/run_all.py --from 31       # 31'den sonuna
    python analysis/run_all.py --skip-r        # R adımlarını atla ("ATLANDI" raporlanır, hat durmaz)
    python analysis/run_all.py --dry-run       # ne çalışacağını göster
    python analysis/run_all.py --no-backup     # data/derived yedeğini alma

Rscript PATH'te olmadığı için otomatik bulunur (C:/Program Files/R/R-*/bin/Rscript.exe)
veya RSCRIPT ortam değişkeniyle verilir. Her adımın çıktısı analysis/logs/<adim>.log
dosyasına yazılır; bir adım hata verirse hat orada durur ve çıkış kodu 1 olur.

2026-09-28 (Opus 5.5, kör denetim C1/C2): 31–54 arasındaki analiz betikleri hatta bağlandı;
adımlar tek listede BAĞIMLILIK sırasıyla duruyor ve ağır olanlar `heavy=True` taşıyor (önceden
ağır adımlar hafiflerden SONRA koşuyordu, bu yüzden 24 bayat 13/15 çıktısını okuyordu).
Makaledeki sonuçları üreten bayraklar adıma yazıldı (43 --bootstrap, 44 --oecd, 49 --microdata,
54 validate). Hatta bilerek girmeyen betikler EXCLUDED'da gerekçesiyle; ikisinde de olmayan
numaralı bir betik başlangıçta uyarı verir. R bu makinede Windows Uygulama Denetimi'yle
engelliyse --skip-r ile Python adımları yine uçtan uca koşar.
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANALYSIS = ROOT / "analysis"
LOGS = ANALYSIS / "logs"

# (kimlik, dil, betik, açıklama, üretilen ana çıktı, ağır mı, ek argümanlar) — BAĞIMLILIK SIRASIYLA
STEPS = [
    ("01", "python", "01_build_panel.py",
     "PISA skorları + yönetişim panelleri", "data/derived/analysis_panel.csv", False, []),
    ("02", "python", "02_institutional_screen.py",
     "Kurumsal tarama (donör havuzu sınıfları)", "data/derived/institutional_screen.csv", False, []),
    ("03", "R", "03_synth.R",
     "Sentetik kontrol + placebo-in-space", "data/derived/synth/synth_summary.csv", False, []),
    ("04", "R", "04_cs_did.R",
     "Callaway–Sant'Anna DiD (bootstrap tohumu 20260928)", "data/derived/did/csdid_summary.json", False, []),
    ("05", "R", "05_mechanisms.R",
     "Mekanizma betimleyicileri", "data/derived/mechanisms/mechanisms_summary.json", False, []),
    ("06", "python", "06_extract_2025_tables.py",
     "2025 dışlama/çaba tabloları (Vol I PDF + annex)", "data/derived/effort_2025.csv", True, []),
    ("07", "python", "07_microdata_effort.py",
     "Çaba göstergeleri 2015–2022 (COG mikroverisi)", "data/derived/effort_microdata.csv", True, []),
    ("08", "python", "08_composition.py",
     "Türkiye okul-türü bileşimi (okul/öğrenci mikroverisi)", "data/derived/turkiye_school_type_composition.csv", True, []),
    ("09", "R", "09_robustness.R",
     "Sağlamlık: leave-one-out, in-time placebo, donör ızgarası", "data/derived/robustness/robustness_summary.json", False, []),
    ("10", "python", "10_placebo_domain.py",
     "Koşullu plasebo-alan testi (CPS ~ çekirdek, 2025)", "data/derived/mechanisms/placebo_conditional_summary.json", False, []),
    ("11", "R", "11_coverage_adjusted.R",
     "Kapsam-düzeltilmiş sentetik kontrol", "data/derived/coverage_adj/coverage_adjusted_summary.json", False, []),
    ("12b", "python", "12b_effort_2025_process.py",
     "Çaba göstergeleri 2025 (12 GB süreç dosyası; önce zip'i %TEMP%/pisa_microdata_work/2025_proc altına aç)",
     "data/derived/effort_2025_process.csv", True, []),
    ("13", "python", "13_creative_thinking_2022.py",
     "Yaratıcı düşünme 2022: yayımlanmış tablo + CRT mikroveri çapraz-kontrolü (TUR/GEO katılmadı)",
     "data/derived/mechanisms/placebo_conditional_2022_summary.json", True, []),
    ("14", "python", "14_meb2025_report_extracts.py",
     "MEB PISA 2025 raporu grafik değerleri (PDF doğrulamalı)", "data/derived/meb2025_report_extracts.csv", False, []),
    ("15", "python", "15_cps2015_placebo.py",
     "İşbirlikli problem çözme 2015: mikroveriden ülke ortalamaları + koşullu plasebo testi",
     "data/derived/mechanisms/placebo_conditional_2015cps_summary.json", True, []),
    ("16", "python", "16_synthetic_did.py",
     "Sentetik DiD (Arkhangelsky vd. 2021; Python uygulaması, plasebo SE)", "data/derived/sdid/sdid_results.csv", False, []),
    ("16b", "R", "16b_synthdid_crosscheck.R",
     "Python SDiD vs referans synthdid (GitHub) çapraz doğrulaması", "data/derived/sdid/r_synthdid_crosscheck.csv", False, []),
    ("17", "python", "17_matrix_completion_conformal.py",
     "Matris tamamlama (MC-NNM) + konformal çıkarım + Python/R SC çapraz doğrulaması",
     "data/derived/mc_conformal/conformal_results.csv", False, []),
    ("18", "R", "18_macro_partition.R",
     "Makro-bölümleme sağlamlığı: MOB/CTree (partykit) + makro-uzay kNN", "data/derived/macro_partition/results.json", False, []),
    ("19", "python", "19_exclusion_frame_2025.py",
     "Çerçeve/dışlama serisi 2015–2025 + ülkeler arası korelasyon (TUR hariç ve Theil–Sen varyantlarıyla) + mekanik sınır",
     "data/derived/exclusion_frame/summary.json", False, []),
    ("20", "python", "20_mode_transition_2015.py",
     "2015 mod-geçişi kümesinde 2012->2015 çukuru, G4 dışlama-istikrar sıralaması, v4 Şekil 1–2",
     "data/derived/mode_transition_2015/summary.json", False, []),
    ("21", "python", "21_breakyear_sensitivity.py",
     "Kırılma-yılı duyarlılığı: SC, trend-düzeltmeli SC, SDiD, 2012-tabanlı DiD; Şekil 3", "data/derived/breakyear/summary.json", False, []),
    ("22", "python", "22_ict_mode_familiarity.py",
     "2015 çukuru bilgisayar aşinalığıyla açıklanıyor mu? (2015/2018 STU_QQQ SPSS)",
     "data/derived/mode_transition_2015/ict_summary.json", True, []),
    ("23", "python", "23_donor_ablation.py",
     "Donör kriteri ablasyon merdiveni (16 hücre) + C2 kademeleri + düzey eşiği bandı + mod-düzeltilmiş havuz; Şekil 4",
     "data/derived/donor_ablation/summary.json", False, []),
    ("25", "python", "25_problem_solving_2012.py",
     "Kırılma öncesi plasebo noktası: PISA 2012 yaratıcı problem çözme (Volume V Table V.A) ~ çekirdek 2012",
     "data/derived/mechanisms/placebo_conditional_2012ps_summary.json", False, []),
    ("24", "python", "24_placebo_backbone.py",
     "Plasebo-alan omurgası 2012–2025 (25/10/13/15 çıktıları) + CPS 2015 çapraz-kontrolü; Şekil 5",
     "data/derived/placebo_backbone/summary.json", False, []),
    ("31", "python", "31_ps2003_puf.py",
     "Kırılma öncesi plasebo 2003 problem çözme (PUF; BRR+Rubin; korelasyonlu bootstrap, tohum 20260922)",
     "data/derived/mechanisms/placebo_conditional_2003ps_puf_summary.json", True, []),
    ("32", "python", "32_ontrend_2003_2012.py",
     "Ön dönem 2003–2012: Türkiye ve donör havuzu düzeyleri, kapsam sınırı, ESCS düzeltmesi (PUF)",
     "data/derived/ontrend/coverage_bound.csv", True, []),
    ("33", "python", "33_ps2012_puf.py",
     "PISA 2012 problem çözme PUF yeniden hesap + mod kontrolü (tohum 20260922)",
     "data/derived/mechanisms/placebo_conditional_2012ps_puf_summary.json", True, []),
    ("34", "python", "34_a1_residual_change.py",
     "A1: artığın döngüler arası değişiminin dağılımı (31/33/15/10 çıktıları)", "data/derived/placebo_backbone/residual_change.csv", False, []),
    ("35", "python", "35_a3_ict_covariate_2025.py",
     "A3: müfredat özgüllüğü — programlama ve BİT kovaryatları 2025 (PUF)", "data/derived/mechanisms/ict_covariate_2025_summary.json", True, []),
    ("36", "python", "36_a9_three_regressor.py",
     "A9: skaler çekirdek yerine üç ayrı regresör", "data/derived/mechanisms/three_regressor.csv", True, []),
    ("37", "python", "37_a10_oecd_relative_ps2012.py",
     "A10: 2012 artıkları ↔ OECD 'actual minus expected' (Table V.2.6)", "data/derived/mechanisms/a10_oecd_relative_2012_summary.json", False, []),
    ("38", "python", "38_cohort_band.py",
     "Sabit kohort sınırı → bant (makale §5.3, Şekil 5 verisi)", "data/derived/ontrend/cohort_band_summary.json", True, []),
    ("42", "python", "42_makale_sekil_seyir.py",
     "Makale Şekil 1: Türkiye'nin PISA kaydı 2003–2025", "data/derived/placebo_backbone/makale_sekil0_veri.csv", False, []),
    ("39", "python", "39_backbone_figure.py",
     "Makale Şekil 2: plasebo-alan omurgası 2003–2025", "data/derived/placebo_backbone/makale_sekil1_veri.csv", False, []),
    ("43", "python", "43_e1_conditional_change.py",
     "E1: 2015→2025 artık derinleşmesi koşullu olarak uçta mı? (korelasyonlu bootstrap)",
     "data/derived/empirical_fixes/e1_summary.json", True, ["--bootstrap"]),
    ("44", "python", "44_e5_coverage_matched_2003.py",
     "E5: 2003 yanlışlaması kapsam farkından mı? (öğrenci düzeyi; OECD havuzlu ikincil model dahil)",
     "data/derived/empirical_fixes/e5_summary.json", True, ["--oecd"]),
    ("54", "python", "54_diag_2003_science.py",
     "E5'in 2003 fen PV'lerinin dış doğrulaması (NCES B.1.32; 'extract' tek seferlik, burada yalnız 'validate')",
     "data/derived/empirical_fixes/e5_science_2003_validation.json", True, ["validate"]),
    ("45", "python", "45_e2_within_country_ict.py",
     "E2: BİT/programlama açıklaması ülke içinde de taşınıyor mu?", "data/derived/empirical_fixes/e2_summary.json", True, []),
    ("53", "python", "53_e2_denominator_sensitivity.py",
     "E2 paydası: aynı sistem kümesiyle duyarlılık", "data/derived/empirical_fixes/e2_denominator_sensitivity.json", False, []),
    ("47", "python", "47_e7_sc_inference_table.py",
     "E7: SC ailesi p-değerleri havuz büyüklüğüyle (taban 1/(J+1))", "data/derived/empirical_fixes/e7_summary.json", False, []),
    ("48", "python", "48_e6_trough_composition.py",
     "E6: 2015 çukuru okul türü bileşiminden mi? (DiNardo–Fortin–Lemieux)", "data/derived/empirical_fixes/e6_summary.json", True, []),
    ("49", "python", "49_e8_frame_bounds.py",
     "E8: çerçeve kanalının ön dönemi + okul içi dışlama sınırı (σ PUF'tan)", "data/derived/empirical_fixes/e8_summary.json", True, ["--microdata"]),
    ("50", "python", "50_e9_distribution_of_gains.py",
     "E9: kazanımın dağılımı (üst dilim alternatifi)", "data/derived/empirical_fixes/e9_summary.json", True, []),
    ("52", "python", "52_e9b_escs_benchmark.py",
     "E9b: üst ESCS kötüleşmesinin ülkeler arası kıyası", "data/derived/empirical_fixes/e9b_summary.json", False, []),
    ("56", "python", "56_exclusion_placebo_association.py",
     "Bulgu 1: plasebo artığı 2025 dışlamasını izliyor mu? (84 sistem; ön-kayıtsız, 10 ve 19'dan sonra)",
     "data/derived/exclusion_frame/placebo_association_2025.json", False, []),
]

# Numaralı ama hatta BİLEREK olmayan betikler (gerekçe). Başlangıçtaki kayma denetimi bunları sessizce geçer.
EXCLUDED = {
    "12a_inspect_2025_process.py": "keşif: yalnız metaveri ve küçük örnek, çıktı yok",
    "26_download_prior_art_playwright.py": "ağdan PDF indirme (dışa dönük; literatür hattı)",
    "27_manifest_repair_2026-09-21.py": "tek seferlik manifest onarımı (21 Eyl)",
    "28_verify_pdf_titles.py": "literatür hattı: PDF başlık denetimi (argüman ister)",
    "29_merge_ekF1_duplicates.py": "tek seferlik kaynakça birleştirme (21 Eyl)",
    "30_update_ledger_row.py": "claim_check/CLAIM_LEDGER.csv'ye yazar; otomatik koşulmaz (protokol §1)",
    "46_e4_human_audit_harness.py": "insan kodlama düzeneği (argüman ister; insan girdisi)",
    "51_diag_bel_2025_gate.py": "tek seferlik teşhis (Belçika 2025 kapısı)",
}


def find_rscript() -> str | None:
    env = os.environ.get("RSCRIPT")
    if env and Path(env).is_file():
        return env
    which = shutil.which("Rscript")
    if which:
        return which
    cands = sorted(glob.glob("C:/Program Files/R/R-*/bin/Rscript.exe")) + \
        sorted(glob.glob("C:/Program Files/R/R-*/bin/x64/Rscript.exe"))
    return cands[-1] if cands else None


def unwired_scripts() -> list[str]:
    """Hatta da EXCLUDED'da da olmayan numaralı betikler (bağsız betik birikmesini önler)."""
    wired = {s[2] for s in STEPS} | set(EXCLUDED)
    found = [p.name for p in ANALYSIS.iterdir() if re.match(r"^\d+[a-z]?_.+\.(py|R)$", p.name)]
    return sorted(set(found) - wired)


def backup_derived() -> Path | None:
    src = ROOT / "data" / "derived"
    if not src.is_dir():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = ROOT / "data" / f"_derived_backup_{stamp}"
    shutil.copytree(src, dst)
    # en fazla 3 yedek tut
    olds = sorted((ROOT / "data").glob("_derived_backup_*"))
    for old in olds[:-3]:
        shutil.rmtree(old, ignore_errors=True)
    return dst


def run_step(step, rscript: str | None, dry: bool) -> tuple[bool, float, str]:
    sid, lang, script, desc, output, _heavy, extra = step
    path = ANALYSIS / script
    if not path.is_file():
        return False, 0.0, f"betik yok: {path}"
    if lang == "R":
        if not rscript:
            return False, 0.0, "Rscript bulunamadı (RSCRIPT ortam değişkenini ayarla ya da --skip-r)"
        cmd = [rscript, str(path), *extra]
    else:
        cmd = [sys.executable, str(path), *extra]
    if dry:
        print(f"  [{sid}] {desc}\n        -> {' '.join(cmd)}")
        return True, 0.0, "dry-run"
    LOGS.mkdir(parents=True, exist_ok=True)
    logfile = LOGS / f"{sid}_{Path(script).stem}.log"
    t0 = time.time()
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    with open(logfile, "w", encoding="utf-8", errors="replace") as fh:
        proc = subprocess.run(cmd, cwd=str(ROOT), stdout=fh,
                              stderr=subprocess.STDOUT, env=env)
    dt = time.time() - t0
    if proc.returncode != 0:
        tail = "\n".join(logfile.read_text(encoding="utf-8", errors="replace")
                         .splitlines()[-15:])
        return False, dt, f"çıkış kodu {proc.returncode}; log: {logfile}\n{tail}"
    out_path = ROOT / output
    if not out_path.exists():
        return False, dt, f"beklenen çıktı üretilmedi: {output} (log: {logfile})"
    return True, dt, str(out_path.relative_to(ROOT))


def main() -> int:
    ap = argparse.ArgumentParser(description="PISA analiz hattını çalıştır")
    ap.add_argument("--only", nargs="+", metavar="ID", help="yalnızca bu adımlar (ör. 19 34 41; ağır olsa da koşar)")
    ap.add_argument("--from", dest="start", metavar="ID", help="bu adımdan sonuna")
    ap.add_argument("--dry-run", action="store_true", help="çalıştırma, planı yaz")
    ap.add_argument("--no-backup", action="store_true", help="data/derived yedeği alma")
    ap.add_argument("--heavy", action="store_true", help="ağır mikroveri adımlarını da (heavy=True) yerlerinde çalıştır")
    ap.add_argument("--skip-r", action="store_true", help="R adımlarını atla (ATLANDI raporlanır, hat durmaz)")
    args = ap.parse_args()

    stray = unwired_scripts()
    if stray:
        print(f"UYARI: hatta ve EXCLUDED'da olmayan numaralı betik(ler): {', '.join(stray)}", file=sys.stderr)

    if args.only:
        steps = [s for s in STEPS if s[0] in set(args.only)]
    else:
        steps = [s for s in STEPS if args.heavy or not s[5]]
        if args.start:
            ids = [s[0] for s in steps]
            if args.start not in ids:
                print(f"bilinmeyen ya da atlanan (ağır?) adım: {args.start}", file=sys.stderr)
                return 2
            steps = steps[ids.index(args.start):]
    if not steps:
        print("çalıştırılacak adım yok", file=sys.stderr)
        return 2
    skipped_heavy = [s[0] for s in STEPS if s[5] and s not in steps and not args.only]

    rscript = None if args.skip_r else find_rscript()
    print(f"Kök      : {ROOT}")
    print(f"Python   : {sys.version.split()[0]}")
    print(f"Rscript  : {'ATLANIYOR (--skip-r)' if args.skip_r else (rscript or 'BULUNAMADI')}")
    if skipped_heavy:
        print(f"Ağır     : atlandı ({', '.join(skipped_heavy)}); bağımlılar önbellekteki çıktılarını kullanır (--heavy ile tazele)")
    if not args.dry_run and not args.no_backup:
        bk = backup_derived()
        if bk:
            print(f"Yedek    : {bk.relative_to(ROOT)}")
    print(f"Adımlar  : {', '.join(s[0] for s in steps)}\n")

    results, failed = [], False
    for step in steps:
        sid, lang, script, desc = step[:4]
        if lang == "R" and args.skip_r:
            results.append((sid, desc, "ATLANDI", 0.0, "R atlandı (--skip-r)"))
            if args.dry_run:
                print(f"  [{sid}] {desc}\n        -> ATLANDI (--skip-r; R adımı)")
            else:
                print(f"[{sid}] {desc} ({lang}: {script}) ... ATLANDI (--skip-r)\n", flush=True)
            continue
        if not args.dry_run:
            print(f"[{sid}] {desc} ({lang}: {script}) ...", flush=True)
        ok, dt, info = run_step(step, rscript, args.dry_run)
        results.append((sid, desc, "OK  " if ok else "HATA", dt, info))
        if not args.dry_run:
            print(f"     {'OK ' if ok else 'HATA'} {dt:6.1f}s  {info}\n", flush=True)
        if not ok:
            failed = True
            break

    if args.dry_run:
        return 0
    print("=" * 72)
    for sid, desc, status, dt, info in results:
        print(f"{sid} {status} {dt:7.1f}s  {desc}")
    total = sum(r[3] for r in results)
    print(f"Toplam süre: {total:.1f}s")
    if failed:
        print("\nHat DURDU. Yukarıdaki log dosyasına bak.")
        return 1
    if any(r[2] == "ATLANDI" for r in results):
        print("\nNOT: R adımları atlandı; data/derived içindeki R çıktıları önceki koşudan kalma.")
    print("\nHat tamam. Rapor: analysis/RESULTS*.md (sayılar değiştiyse güncellenmeli).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
