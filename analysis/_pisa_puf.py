# -*- coding: utf-8 -*-
"""
_pisa_puf — PISA 2003–2012 kamuya açık mikroveri (PUF) okuyucu + BRR/Rubin varyans motoru.

Neden: §10(6) ve §10(4) için gereken ağırlıklı ülke ortalamaları ve standart hataları
yayımlanmış tam sayılı tablolardan değil mikroveriden gelmeli. Betik 25 yayımlanmış
Table V.A ortalamalarını kullanıyor (§9'daki RMSE 15–17 sınırı); bu modül onun yerine
GEÇMEZ, yeni betiklerin (31, 32) ortak çekirdeğidir. Betik 25'e dokunulmaz.

Zip'ler AÇILMAZ (protokol §8): zipfile ile akıştan okunur. Sabit genişlik konumları
`PISA<yıl>_SPSS_student.txt` sözdiziminden parse edilir, elle yazılmaz. Dört dosya da
sabit kayıt uzunluklu (reclen + CRLF), bu yüzden numpy adımlamasıyla okunur.

BRR + RUBIN (OECD PISA Data Analysis Manual; Fay k = 0,5, G = 80 replikasyon):
  M = artırılmış değer (PV) sayısı, G = replikasyon ağırlığı sayısı
  1) theta_p    = W_FSTUWT ile ağırlıklı ortalama, her PV p için
  2) theta_p_r  = W_FSTR<r> ile ağırlıklı ortalama, her p ve her r için
  3) V_samp_p   = 1/(G*(1-k)^2) * SUM_r (theta_p_r - theta_p)^2      (k=0,5 -> çarpan 1/20)
  4) theta      = ortalama_p(theta_p)
  5) V_samp     = ortalama_p(V_samp_p)
  6) V_imp      = (1 + 1/M) * (1/(M-1)) * SUM_p (theta_p - theta)^2
  7) V = V_samp + V_imp ;  SE = sqrt(V)

Kabul kapısı: sözdiziminden gelen max(bitiş) veri dosyasının kayıt uzunluğuna eşit olmalı
(2003=1883, 2006=1808, 2009=1825, 2012=2348). Eşit değilse okuma yapılmaz, hata verilir.

Yazan: Claude Opus 5 (ana oturum), 2026-09-22. Yönlendirme kuralı gereği kod Fable 5.1'e
gidecekti; Fable kullanım limiti nedeniyle iki koşum da düştü ve iş ana oturuma alındı
(gerekçe: 06_calisma/PUF_MOTOR_DOGRULAMA_2026-09-22.md). Denetim: Opus 4.8, bekliyor.
"""
from __future__ import annotations

import hashlib
import re
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "derived" / "cache" / "puf"

REGISTRY = {
    2003: dict(zip="data/pisa_microdata/2003/INT_stui_2003_v2.zip", inner="INT_stui_2003_v2.txt",
               syn="data/pisa_microdata/2003/PISA2003_SPSS_student.txt", reclen=1883),
    2006: dict(zip="data/pisa_microdata/2006/INT_Stu06_Dec07.zip", inner="INT_Stu06_Dec07.txt",
               syn="data/pisa_microdata/2006/PISA2006_SPSS_student.txt", reclen=1808),
    2009: dict(zip="data/pisa_microdata/2009/INT_STQ09_DEC11.zip", inner="INT_STQ09_DEC11.txt",
               syn="data/pisa_microdata/2009/PISA2009_SPSS_student.txt", reclen=1825),
    2012: dict(zip="data/pisa_microdata/2012/INT_STU12_DEC03.zip", inner="INT_STU12_DEC03.txt",
               syn="data/pisa_microdata/2012/PISA2012_SPSS_student.txt", reclen=2348),
    # PISA 2012 bilgisayar tabanli degerlendirme (CBA) ogrenci dosyasi — ayri OECD yayini,
    # 22 Eyl 2026'da geldi. Icinde PV*CPRO (problem cozme), PV*CMAT (bilgisayarda matematik),
    # PV*CREA (dijital okuma) ve AYNI ogrencilerin kagit PV*MATH/READ/SCIE'si birlikte var.
    "2012cba": dict(zip="data/pisa_microdata/2012_cba/CBA_STU12_MAR31.zip", inner="CBA_STU12_MAR31.txt",
                    syn="data/pisa_microdata/2012_cba/PISA2012_SPSS_CBA_student.txt", reclen=2170),
}

REPW = [f"W_FSTR{i}" for i in range(1, 81)]
PANEL_FIELD = {"MATH": ("math_mean", "math_se"), "READ": ("reading_mean", "reading_se"),
               "SCIE": ("science_mean", "science_se")}

_VAR = re.compile(r"^\s*/?\s*([A-Za-z][A-Za-z0-9_]*)\s+(\d+)\s*-\s*(\d+)\s*(?:\(\s*([aAfF])[^)]*\))?\s*(\.)?\s*$")


def parse_datalist(syntax_path):
    """SPSS DATA LIST bloğu -> {AD: (başlangıç1, bitiş1, 'A'|'F')}.

    Yorum satırları (* ile başlar) atlanır: 2006/2009'da "DATA LIST" ifadesi bir yorumda
    da geçiyor, gerçek komut sonraki satırda. Blok tek başına '.' satırında ya da sonunda
    '.' bulunan değişken satırında biter (2009: "VER_STU 1813 - 1825 (A).").
    """
    lines = Path(syntax_path).read_text(encoding="latin-1").splitlines()
    start = None
    for i, raw in enumerate(lines):
        if raw.strip().startswith("*"):
            continue
        if re.match(r"^\s*DATA\s+LIST\b", raw, re.I):
            start = i
            break
    if start is None:
        raise ValueError(f"DATA LIST komutu bulunamadi: {syntax_path}")

    out = {}
    for raw in lines[start:]:
        line = raw.replace("\t", " ")
        if line.strip() == ".":
            break
        m = _VAR.match(line)
        if not m:
            continue
        name = m.group(1).upper()
        if name in out:
            raise ValueError(f"{syntax_path}: {name} iki kez tanimli")
        out[name] = (int(m.group(2)), int(m.group(3)), (m.group(4) or "F").upper())
        if m.group(5):
            break
    if not out:
        raise ValueError(f"DATA LIST bos ayristirildi: {syntax_path}")
    return out


def parse_missing(syntax_path):
    """MISSING VALUES bildirimleri -> ({AD: {kodlar}}, ayristirilamayanlar).

    Büyük/küçük harf duyarsız, çok satırlı (2006/2009'da onlarca satırlık bloklar var);
    bildirim '(...)' + '.' ile biter. Formlar: (9,8,7) · ('97','98') · ("999997") ·
    (96 thru 99) · (999). Ayrıştırılamayan bildirim sessizce atlanmaz, döndürülür.
    """
    # Yorum satırları atılır: başlıktaki "…applies … missing values specifications." cümlesi
    # aksi hâlde sahte bir bildirim gibi görünür.
    text = "\n".join(l for l in Path(syntax_path).read_text(encoding="latin-1").splitlines()
                     if not l.strip().startswith("*"))
    out, unparsed = {}, []
    for m in re.finditer(r"missing\s+values\b(.*?)\.\s*(?:\r?\n|$)", text, re.I | re.S):
        stmt = m.group(1)
        if "(" not in stmt:
            unparsed.append(" ".join(stmt.split())[:120])
            continue
        for part in stmt.split("/"):
            grp = re.search(r"\(([^)]*)\)", part)
            if not grp:
                if part.strip():
                    unparsed.append(" ".join(part.split())[:120])
                continue
            names = [w.upper() for w in re.findall(r"[A-Za-z][A-Za-z0-9_]*", part[:grp.start()])]
            body = grp.group(1)
            codes = set()
            thru = re.match(r"\s*(-?\d+(?:\.\d+)?)\s+thru\s+(-?\d+(?:\.\d+)?)\s*$", body, re.I)
            if thru:
                lo, hi = float(thru.group(1)), float(thru.group(2))
                if lo.is_integer() and hi.is_integer() and 0 <= hi - lo <= 1000:
                    codes = {float(v) for v in range(int(lo), int(hi) + 1)}
                else:
                    unparsed.append(("thru: " + body)[:120])
                    continue
            else:
                for tok in re.split(r"[,\s]+", body.strip()):
                    tok = tok.strip("'\"")
                    if not tok:
                        continue
                    try:
                        codes.add(float(tok))
                    except ValueError:
                        unparsed.append(f"kod: {tok}"[:120])
            for n in names:
                out.setdefault(n, set()).update(codes)
    return out, unparsed


def record_layout(cycle):
    """(kayit_uzunlugu_dahil_satir_sonu, satir_sayisi). Sabit kayit degilse hata."""
    cfg = REGISTRY[cycle]
    with zipfile.ZipFile(ROOT / cfg["zip"]) as z:
        size = z.getinfo(cfg["inner"]).file_size
    for eol in (2, 1):
        rec = cfg["reclen"] + eol
        if size % rec == 0:
            return rec, size // rec
    raise ValueError(f"{cycle}: sabit kayit degil (boyut {size}, reclen {cfg['reclen']})")


def pv_cols(spec, root, m=5):
    """PV1<root>…PVm<root>; hepsi sozdiziminde yoksa bos liste."""
    names = [f"PV{i}{root}" for i in range(1, m + 1)]
    return names if all(n in spec for n in names) else []


def read_columns(cycle, wanted, chunk_rows=100_000, use_cache=True):
    """Zip icinden akisla YALNIZCA istenen kolonlari cikarir. Parquet onbellekli."""
    cfg = REGISTRY[cycle]
    wanted = [w.upper() for w in wanted]
    key = hashlib.sha256("|".join(sorted(wanted)).encode()).hexdigest()[:16]
    cache_file = CACHE / f"{cycle}_{key}.parquet"
    if use_cache and cache_file.exists():
        return pd.read_parquet(cache_file)

    spec = parse_datalist(ROOT / cfg["syn"])
    maxpos = max(e for _, e, _ in spec.values())
    if maxpos != cfg["reclen"]:
        raise ValueError(f"{cycle}: KABUL KAPISI dustu — sozdizimi maxpos {maxpos} != reclen {cfg['reclen']}")
    eksik = [w for w in wanted if w not in spec]
    if eksik:
        raise KeyError(f"{cycle}: sozdiziminde yok: {eksik}")
    missing_codes, _ = parse_missing(ROOT / cfg["syn"])

    rec, nrows = record_layout(cycle)
    cols = {w: [] for w in wanted}
    done = 0
    with zipfile.ZipFile(ROOT / cfg["zip"]) as z, z.open(cfg["inner"]) as f:
        while True:
            buf = f.read(rec * chunk_rows)
            if not buf:
                break
            n = len(buf) // rec
            if n == 0:
                break
            arr = np.frombuffer(buf[: n * rec], dtype="S1").reshape(n, rec)
            for w in wanted:
                a, b, kind = spec[w]
                raw = arr[:, a - 1:b].copy().view(f"S{b - a + 1}").ravel().astype("U")
                if kind == "A":
                    cols[w].append(np.char.strip(raw))
                else:
                    s = pd.Series(raw).str.strip()
                    v = pd.to_numeric(s.where(s != ""), errors="coerce").to_numpy(dtype=float)
                    mc = missing_codes.get(w)
                    if mc:
                        v = np.where(np.isin(v, list(mc)), np.nan, v)
                    cols[w].append(v)
            done += n
            print(f"  [{cycle}] {done:,}/{nrows:,}", file=sys.stderr, flush=True)
    df = pd.DataFrame({w: np.concatenate(cols[w]) for w in wanted})
    if len(df) != nrows:
        raise ValueError(f"{cycle}: {len(df)} satir okundu, {nrows} bekleniyordu")
    CACHE.mkdir(parents=True, exist_ok=True)
    df.to_parquet(cache_file, index=False)
    return df


def brr_pv_stat(df, pv_columns, weight_col, repweight_cols, fay=0.5, by="CNT"):
    """Ulke bazinda agirlikli PV ortalamasi + BRR/Rubin standart hatasi (formul: modul docstring)."""
    M, G = len(pv_columns), len(repweight_cols)
    if M < 2:
        raise ValueError("en az 2 PV gerekir (Rubin atama varyansi)")
    mult = 1.0 / (G * (1.0 - fay) ** 2)
    d = df[[by, weight_col, *pv_columns, *repweight_cols]].dropna()
    rows = []
    for cnt, g in d.groupby(by, sort=True):
        X = g[pv_columns].to_numpy(float)
        W = g[weight_col].to_numpy(float)
        R = g[repweight_cols].to_numpy(float)
        if len(g) < 2 or W.sum() <= 0:
            continue
        theta = (W @ X) / W.sum()
        theta_rep = (R.T @ X) / R.sum(axis=0)[:, None]
        v_s = float((mult * ((theta_rep - theta) ** 2).sum(axis=0)).mean())
        v_i = (1.0 + 1.0 / M) * float(((theta - theta.mean()) ** 2).sum()) / (M - 1)
        rows.append(dict(iso3=cnt, mean=float(theta.mean()), se=float(np.sqrt(v_s + v_i)),
                         se_sampling=float(np.sqrt(v_s)), se_imputation=float(np.sqrt(v_i)),
                         n_students=int(len(g)), sum_weight=float(W.sum())))
    return pd.DataFrame(rows)


def brr_pv_corr(df, pv_a, pv_b, weight_col, repweight_cols, fay=0.5, by="CNT"):
    """İki büyüklüğün ülke kestirimleri arasındaki BRR + Rubin KORELASYONU.

    Neden gerekli: iki büyüklük AYNI öğrencilerden geliyorsa (ör. problem çözme ve çekirdek
    alanlar), ülke kestirimleri korelasyonludur. Artığın belirsizliğini bootstrap'la taşırken
    ikisini bağımsız çekmek Var(y − b·x)'i abartır ve aralığı GEREKSİZ genişletir
    (Opus 4.8 denetimi, 22 Eyl, D2a).

    Yöntem: örnekleme korelasyonu 80 replikasyon serisinden, atama korelasyonu 5 PV serisinden
    ayrı ayrı; sonra toplam kovaryans bileşen standart hatalarıyla birleştirilir
        Cov = rho_samp * se_samp_A * se_samp_B + rho_imp * se_imp_A * se_imp_B
        rho = Cov / (se_A * se_B)
    Bileşen SE'leri `brr_pv_stat`'tan gelir; böylece doğrulanmış SE'ler DEĞİŞMEZ, yalnız
    aralarındaki korelasyon eklenir.
    """
    # pv_a / pv_b: ya M kolon (tek alan), ya M grup (çok alanlı çekirdek). Çok alanlı olanda
    # PV İNDEKSİ hizalanır — PISA'da her alanın p'inci PV'si AYNI atama çekilişinden gelir,
    # bu yüzden çekirdeğin p'inci PV'si = o alanların p'inci PV'lerinin ortalamasıdır.
    def norm(pv):
        return [g if isinstance(g, (list, tuple)) else [g] for g in pv]

    ga, gb = norm(pv_a), norm(pv_b)
    flat = [c for g in ga + gb for c in g]
    d = df[[by, weight_col, *flat, *repweight_cols]].dropna()
    rows = []
    for cnt, g in d.groupby(by, sort=True):
        W = g[weight_col].to_numpy(float)
        R = g[repweight_cols].to_numpy(float)
        den = R.sum(axis=0)
        out = {}
        for tag, groups in (("a", ga), ("b", gb)):
            X = np.column_stack([g[list(c)].to_numpy(float).mean(axis=1) for c in groups])  # n x M
            theta_pv = (W @ X) / W.sum()                    # (M,)
            rep = ((R.T @ X) / den[:, None]).mean(axis=1)    # (G,) PV-ortalamalı replikasyon
            out[tag] = (theta_pv, rep)
        (pa, ra), (pb, rb) = out["a"], out["b"]
        rho_s = float(np.corrcoef(ra, rb)[0, 1]) if ra.std() > 0 and rb.std() > 0 else 0.0
        rho_i = float(np.corrcoef(pa, pb)[0, 1]) if pa.std() > 0 and pb.std() > 0 else 0.0
        rows.append(dict(iso3=cnt, rho_sampling=rho_s, rho_imputation=rho_i))
    return pd.DataFrame(rows)


def combine_rho(rho_s, rho_i, se_s_a, se_i_a, se_s_b, se_i_b):
    """Bileşen korelasyonlarını toplam korelasyona çevirir (docstring: brr_pv_corr)."""
    cov = rho_s * se_s_a * se_s_b + rho_i * se_i_a * se_i_b
    se_a = np.sqrt(se_s_a ** 2 + se_i_a ** 2)
    se_b = np.sqrt(se_s_b ** 2 + se_i_b ** 2)
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.where((se_a > 0) & (se_b > 0), cov / (se_a * se_b), 0.0)
    return np.clip(r, -0.999, 0.999)


def _validate():
    panel = pd.read_csv(ROOT / "data" / "derived" / "analysis_panel.csv")
    CACHE.mkdir(parents=True, exist_ok=True)
    out_csv = CACHE / "VALIDATION_2026-09-22.csv"
    if out_csv.exists():
        out_csv.unlink()
    header = True
    for cycle in (2003, 2006, 2009, 2012):
        spec = parse_datalist(ROOT / REGISTRY[cycle]["syn"])
        roots = [r for r in ("MATH", "READ", "SCIE") if pv_cols(spec, r)]
        want = ["CNT", "W_FSTUWT", *REPW] + [c for r in roots for c in pv_cols(spec, r)]
        df = read_columns(cycle, want)
        print(f"[{cycle}] {len(df):,} satir · alanlar {roots} · TUR {int((df.CNT == 'TUR').sum()):,}")
        pub = panel[panel.cycle == cycle]
        for r in roots:
            est = brr_pv_stat(df, pv_cols(spec, r), "W_FSTUWT", REPW)
            mcol, scol = PANEL_FIELD[r]
            j = est.merge(pub[["iso3", mcol, scol]], on="iso3", how="left")
            j.insert(0, "alan", r)
            j.insert(0, "cycle", cycle)
            j = j.rename(columns={"mean": "puf_mean", "se": "puf_se", mcol: "pub_mean", scol: "pub_se"})
            j["fark"] = j.puf_mean - j.pub_mean
            j["se_orani"] = j.puf_se / j.pub_se
            j.to_csv(out_csv, mode="a", header=header, index=False, encoding="utf-8-sig")
            header = False
            ok = j.dropna(subset=["fark"])
            if ok.empty:
                print(f"   {r}: panelde karsilastirilacak deger yok (n_puf={len(j)})")
            else:
                i = ok.fark.abs().idxmax()
                print(f"   {r}: n={len(ok)} · |fark| medyan {ok.fark.abs().median():.3f} · "
                      f"maks {ok.fark.abs().max():.3f} ({ok.loc[i, 'iso3']}) · "
                      f"SE orani medyan {ok.se_orani.median():.3f}")
        del df
    print(f"\nyazildi: {out_csv.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    if "--validate" in sys.argv:
        sys.exit(_validate())
    print("kullanim: python analysis/_pisa_puf.py --validate")
