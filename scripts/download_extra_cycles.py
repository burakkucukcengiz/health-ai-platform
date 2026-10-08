import pandas as pd
import requests
from io import BytesIO
import time
import os

BASE_URL = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/{year}/DataFiles/{fname}.XPT"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}

# Bu iki cycle'da dosya isimleri farkli (eski format)
CYCLES = {
    "2001-2002": {
        "year": 2001,
        "DEMO": "DEMO_B",
        "BMX": "BMX_B",
        "BPX": "BPX_B",
        "BIOPRO": "L40_B",      # icinde LBXSASSI, LBXSATSI var
        "CBC": "L25_B",         # icinde LBXPLTSI var
        "TRIGLY": "L13AM_B",    # icinde LBXTR, LBDLDL var (fasting subsample)
        "TCHOL_HDL": "L13_B",   # icinde total kolesterol + HDL var
    },
    "2003-2004": {
        "year": 2003,
        "DEMO": "DEMO_C",
        "BMX": "BMX_C",
        "BPX": "BPX_C",
        "BIOPRO": "L40_C",
        "CBC": "L25_C",
        "TRIGLY": "L13AM_C",
        "TCHOL_HDL": "L13_C",
    },
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

all_cycles = []

for cycle, info in CYCLES.items():
    year = info["year"]
    print(f"\n=== {cycle} (yil {year}) ===")
    tables = {}
    for key in ["DEMO", "BMX", "BPX", "BIOPRO", "CBC", "TRIGLY", "TCHOL_HDL"]:
        df = download_xpt(year, info[key])
        if df is not None:
            tables[key] = df
        time.sleep(0.3)

    if "DEMO" not in tables:
        print(f"  [CYCLE ATLANDI] demografik dosya yok: {cycle}")
        continue

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
        # SI birimli (SI ile biten) kolonlari haric tut, sadece mg/dL kolonunu al
        hdl_candidates = [c for c in t.columns if ("HDL" in c.upper() or "HDD" in c.upper()) and not c.upper().endswith("SI")]
        hdl_col = hdl_candidates[:1]  # sadece ilkini al, tekrar olmasin
        cols = ["SEQN"] + tc_col + hdl_col
        merged = merged.merge(t[cols], on="SEQN", how="left")
        for c in hdl_col:
            if c != "LBDHDD":
                merged = merged.rename(columns={c: "LBDHDD"})

    # Guvenlik: olasi duplicate kolonlari temizle
    merged = merged.loc[:, ~merged.columns.duplicated()]
    merged["CYCLE"] = cycle
    all_cycles.append(merged)
    print(f"  >> {cycle}: {len(merged)} kisi eklendi")

if not all_cycles:
    print("\n[HATA] Hic cycle indirilemedi.")
else:
    new_data = pd.concat(all_cycles, ignore_index=True)
    print(f"\n=== YENI CYCLE'LARDAN TOPLAM: {len(new_data)} kisi ===")

    # Mevcut veriyle birlestir
    existing = pd.read_csv("data/raw/nhanes_multicycle_raw.csv")
    combined = pd.concat([existing, new_data], ignore_index=True)
    print(f"=== GENEL TOPLAM (9 cycle): {len(combined)} kisi ===")

    combined.to_csv("data/raw/nhanes_multicycle_raw.csv", index=False)
    print("Guncellendi: data/raw/nhanes_multicycle_raw.csv")
