import pandas as pd
import requests
from io import BytesIO
import time
import os

BASE_URL = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/{year}/DataFiles/{fname}.XPT"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}

FILES = {
    "DEMO": "DEMO",
    "BMX": "BMX",
    "BPX": "BPX",
    "BIOPRO": "LAB18",
    "CBC": "LAB25",
    "TRIGLY": "LAB13AM",
    "TCHOL_HDL": "LAB13",
}

def download_xpt(year, fname):
    url = BASE_URL.format(year=year, fname=fname)
    print(f"  -> indiriliyor: {fname}")
    try:
        r = requests.get(url, timeout=60, headers=HEADERS)
        if r.status_code != 200:
            print(f"     [ATLANDI] {fname} bulunamadi ({r.status_code})")
            return None
        if len(r.content) < 1000:
            print(f"     [ATLANDI] {fname} cok kucuk dosya")
            return None
        df = pd.read_sas(BytesIO(r.content), format="xport")
        return df
    except Exception as e:
        print(f"     [HATA] {fname}: {e}")
        return None

print("\n=== 1999-2000 (yil 1999) ===")
tables = {}
for key, fname in FILES.items():
    df = download_xpt(1999, fname)
    if df is not None:
        tables[key] = df
    time.sleep(0.3)

if "DEMO" not in tables:
    print("[HATA] demografik dosya indirilemedi, durduruluyor.")
else:
    merged = tables["DEMO"][["SEQN", "RIDAGEYR", "RIAGENDR"]].copy()

    if "BMX" in tables:
        cols = [c for c in ["SEQN","BMXBMI","BMXWT","BMXHT","BMXWAIST"] if c in tables["BMX"].columns]
        merged = merged.merge(tables["BMX"][cols], on="SEQN", how="left")

    if "BPX" in tables:
        cols = [c for c in ["SEQN","BPXSY1","BPXDI1"] if c in tables["BPX"].columns]
        merged = merged.merge(tables["BPX"][cols], on="SEQN", how="left")

    if "BIOPRO" in tables:
        cols = [c for c in ["SEQN","LBXSASSI","LBXSATSI"] if c in tables["BIOPRO"].columns]
        merged = merged.merge(tables["BIOPRO"][cols], on="SEQN", how="left")

    if "CBC" in tables:
        cols = [c for c in ["SEQN","LBXPLTSI"] if c in tables["CBC"].columns]
        merged = merged.merge(tables["CBC"][cols], on="SEQN", how="left")

    if "TRIGLY" in tables:
        cols = [c for c in ["SEQN","LBXTR","LBDLDL"] if c in tables["TRIGLY"].columns]
        merged = merged.merge(tables["TRIGLY"][cols], on="SEQN", how="left")

    if "TCHOL_HDL" in tables:
        t = tables["TCHOL_HDL"]
        tc_col = [c for c in t.columns if c == "LBXTC"]
        hdl_candidates = [c for c in t.columns if ("HDL" in c.upper() or "HDD" in c.upper()) and not c.upper().endswith("SI")]
        hdl_col = hdl_candidates[:1]
        cols = ["SEQN"] + tc_col + hdl_col
        merged = merged.merge(t[cols], on="SEQN", how="left")
        for c in hdl_col:
            if c != "LBDHDD":
                merged = merged.rename(columns={c: "LBDHDD"})

    merged = merged.loc[:, ~merged.columns.duplicated()]
    merged["CYCLE"] = "1999-2000"

    print(f"  >> 1999-2000: {len(merged)} kisi eklendi")

    existing = pd.read_csv("data/raw/nhanes_multicycle_raw.csv")
    combined = pd.concat([existing, merged], ignore_index=True)
    print(f"\n=== GENEL TOPLAM (10 cycle): {len(combined)} kisi ===")

    combined.to_csv("data/raw/nhanes_multicycle_raw.csv", index=False)
    print("Guncellendi: data/raw/nhanes_multicycle_raw.csv")
