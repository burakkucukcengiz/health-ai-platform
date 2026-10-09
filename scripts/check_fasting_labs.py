import requests

BASE = 'https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public'

# Döngü: (yıl klasörü, glikoz dosyası, insülin dosyası, demografi dosyası)
CYCLES = [
    ('1999', 'LAB10AM', None, 'DEMO'),
    ('2001', 'L10AM_B', None, 'DEMO_B'),
    ('2003', 'L10AM_C', None, 'DEMO_C'),
    ('2005', 'GLU_D', 'INS_D', 'DEMO_D'),
    ('2007', 'GLU_E', 'INS_E', 'DEMO_E'),
    ('2009', 'GLU_F', 'INS_F', 'DEMO_F'),
    ('2011', 'GLU_G', 'INS_G', 'DEMO_G'),
    ('2013', 'GLU_H', 'INS_H', 'DEMO_H'),
    ('2015', 'GLU_I', 'INS_I', 'DEMO_I'),
    ('2017', 'GLU_J', 'INS_J', 'DEMO_J'),
]

def exists(url):
    try:
        r = requests.head(url, timeout=15, allow_redirects=True)
        return r.status_code == 200
    except requests.RequestException:
        return False

print(f"{'Yıl':6s}{'Glikoz':10s}{'İnsülin':10s}{'Demo':10s}")
for year, glu, ins, demo in CYCLES:
    row = []
    for code in (glu, ins, demo):
        if code is None:
            row.append('yok')
            continue
        url = f"{BASE}/{year}/DataFiles/{code}.XPT"
        row.append('var' if exists(url) else 'YOK')
    print(f"{year:6s}{row[0]:10s}{row[1]:10s}{row[2]:10s}")

