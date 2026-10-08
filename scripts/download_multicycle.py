import pandas as pd
import requests
from io import BytesIO
import time
import os

BASE_URL = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/{year}/DataFiles/{fname}.XPT"

# cycle_label: (yil, suffix)
CYCLES = {
    "2005-2006": (2005, "D"),
    "2007-2008": (2007, "E"),
    "2009-2010": (2009, "F"),
    "2011-2012": (2011, "G"),
    "2013-2014": (2013, "H"),
    "2015-2016": (2015, "I"),
    "2017-2018": (2017, "J"),
}

FILES = ["DEMO", "BMX", "BPX", "BIOPRO", "CBC", "TRIGLY", "TCHOL", "HDL"]

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}

def download_xpt(year, fname, suffix):
    full_name = f"{fname}_{suffix}"
    url = BASE_URL.format(year=year, fname=full_name)
    print(f"  -> indiriliyor: {full_name}")
    try:
        r = requests.get(url, timeout=60, headers=HEADERS)
        if r.status_code != 200:
            print(f"     [ATLANDI] {full_name} bulunamadi ({r.status_code})")
            return None
        if len(r.content) < 1000:
            print(f"     [ATLANDI] {full_name} dosya cok kucuk, muhtemelen hata sayfasi")
            return None
        df = pd.read_sas(BytesIO(r.content), format="xport")
        return df
    except Exception as e:
        print(f"     [HATA] {full_name}: {e}")
        return None

all_cycles = []

for cycle, (year, suffix) in CYCLES.items():
    print(f"\n=== {cycle} (yil {year}, suffix {suffix}) ===")
    tables = {}
    for fname in FILES:
        df = download_xpt(year, fname, suffix)
        if df is not None:
            tables[fname] = df
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

    if "TCHOL" in tables:
        cols = [c for c in ["SEQN","LBXTC"] if c in tables["TCHOL"].columns]
        merged = merged.merge(tables["TCHOL"][cols], on="SEQN", how="left")

    if "HDL" in tables:
        hdl_target_cols = [c for c in tables["HDL"].columns if "HDD" in c]
        cols = ["SEQN"] + hdl_target_cols
        merged = merged.merge(tables["HDL"][cols], on="SEQN", how="left")
        for c in hdl_target_cols:
            merged = merged.rename(columns={c: "LBDHDD"})

    merged["CYCLE"] = cycle
    all_cycles.append(merged)
    print(f"  >> {cycle}: {len(merged)} kisi eklendi")

if not all_cycles:
    print("\n[HATA] Hic cycle indirilemedi.")
else:
    combined = pd.concat(all_cycles, ignore_index=True)
    print(f"\n=== TOPLAM HAM VERI: {len(combined)} kisi ===")
    os.makedirs("data/raw", exist_ok=True)
    combined.to_csv("data/raw/nhanes_multicycle_raw.csv", index=False)
    print("Kaydedildi: data/raw/nhanes_multicycle_raw.csv")
