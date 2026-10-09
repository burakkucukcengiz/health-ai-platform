import os
import pandas as pd
import requests
import io

CYCLES = {
    '2013-2014': ('2013', 'INS_H'),
    '2015-2016': ('2015', 'INS_I'),
    '2017-2018': ('2017', 'INS_J'),
}

OUT_DIR = 'data/raw/insulin'
GLUCOSE_DIR = 'data/raw/glucose'
MERGED_OUT = 'data/processed/homa_ir.csv'

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs('data/processed', exist_ok=True)


def fetch_xpt(year, name):
    url = f"https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/{year}/DataFiles/{name}.XPT"
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    return pd.read_sas(io.BytesIO(resp.content), format='xport')


all_merged = []

for cycle, (year, ins_name) in CYCLES.items():
    print(f"--- {cycle} ({ins_name}) ---")

    ins = fetch_xpt(year, ins_name)
    ins_cols = [c for c in ['SEQN', 'LBXIN'] if c in ins.columns]
    missing_ins = set(['SEQN', 'LBXIN']) - set(ins_cols)
    if missing_ins:
        print(f"UYARI, eksik kolonlar (insulin): {missing_ins}")
    ins = ins[ins_cols].copy()

    glu_path = os.path.join(GLUCOSE_DIR, f"glucose_{cycle}.csv")
    if not os.path.exists(glu_path):
        print(f"UYARI: {glu_path} bulunamadi, bu dongu atlaniyor.")
        continue
    glu = pd.read_csv(glu_path)
    if 'LBXGLU' not in glu.columns:
        print(f"UYARI: {glu_path} icinde LBXGLU yok, bu dongu atlaniyor.")
        continue

    merged = pd.merge(glu[['SEQN', 'LBXGLU']], ins, on='SEQN', how='inner')
    merged['CYCLE'] = cycle

    ins_out_path = os.path.join(OUT_DIR, f"insulin_{cycle}.csv")
    merged.to_csv(ins_out_path, index=False)
    print(f"Kaydedildi: {ins_out_path} ({len(merged)} satir)")

    all_merged.append(merged)

if all_merged:
    full = pd.concat(all_merged, ignore_index=True)
    full = full.dropna(subset=['LBXGLU', 'LBXIN'])
    full = full[(full['LBXGLU'] > 0) & (full['LBXIN'] > 0)]
    full['HOMA_IR'] = (full['LBXGLU'] * full['LBXIN']) / 405.0
    full.to_csv(MERGED_OUT, index=False)
    print(f"\nToplam birlesik satir: {len(full)}")
    print(f"Kaydedildi: {MERGED_OUT}")
    print(full['HOMA_IR'].describe())
else:
    print("Hic veri birlesmedi, lutfen glucose dosyalarini kontrol edin.")
