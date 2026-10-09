import os
import requests
import pandas as pd

BASE = 'https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public'
OUT = 'data/raw/glucose'
os.makedirs(OUT, exist_ok=True)

# Döngü -> (klasör yılı, glikoz dosya adayları, demo dosya adayları)
CYCLES = {
    '2005-2006': ('2005', ['GLU_D'], ['DEMO_D']),
    '2007-2008': ('2007', ['GLU_E'], ['DEMO_E']),
    '2009-2010': ('2009', ['GLU_F'], ['DEMO_F']),
    '2011-2012': ('2011', ['GLU_G'], ['DEMO_G']),
    '2013-2014': ('2013', ['GLU_H'], ['DEMO_H']),
    '2015-2016': ('2015', ['GLU_I'], ['DEMO_I']),
    '2017-2018': ('2017', ['GLU_J'], ['DEMO_J']),
}


def fetch_xpt(year, names):
    for name in names:
        url = f"{BASE}/{year}/DataFiles/{name}.XPT"
        r = requests.get(url, timeout=60)
        if r.status_code == 200:
            path = os.path.join(OUT, f"{name}.XPT")
            with open(path, 'wb') as f:
                f.write(r.content)
            return path
    return None


def find_col(col, *frames):
    """Kolonu verilen tablolarda ara, bulunduğu tabloyu döndür."""
    for name, df in frames:
        if col in df.columns:
            return df[['SEQN', col]], name
    return None, None


summary = []
for cycle, (year, glu_names, demo_names) in CYCLES.items():
    glu_path = fetch_xpt(year, glu_names)
    demo_path = fetch_xpt(year, demo_names)
    if not (glu_path and demo_path):
        summary.append((cycle, 'indirilemedi', '-', '-', '-'))
        continue

    glu = pd.read_sas(glu_path, format='xport')
    demo = pd.read_sas(demo_path, format='xport')

    # Teşhis: ilk döngüde kolonları göster
    if cycle == '2005-2006':
        print("GLU kolonları:", list(glu.columns))
        print("DEMO kolonları:", list(demo.columns))

    glu_n = int(glu['LBXGLU'].notna().sum()) if 'LBXGLU' in glu else 0

    wt, wt_src = find_col('WTSAF2YR', ('GLU', glu), ('DEMO', demo))
    if wt is None:
        summary.append((cycle, 'WTSAF2YR yok', glu_n, '-', '-'))
        continue

    merged = demo[['SEQN', 'RIDAGEYR', 'RIAGENDR']].merge(
        glu[['SEQN', 'LBXGLU']], on='SEQN', how='left')
    merged = merged.merge(wt, on='SEQN', how='left')
    merged['CYCLE'] = cycle
    merged.to_csv(os.path.join(OUT, f"glucose_{cycle}.csv"), index=False)

    fast_n = int(merged['WTSAF2YR'].notna().sum())
    summary.append((cycle, 'ok', glu_n, fast_n, wt_src))

print(f"{'Döngü':12s}{'Durum':16s}{'LBXGLU':>10s}{'WTSAF2YR':>12s}{'Kaynak':>8s}")
for cycle, status, glu_n, fast_n, src in summary:
    print(f"{cycle:12s}{status:16s}{str(glu_n):>10s}{str(fast_n):>12s}{str(src):>8s}")
