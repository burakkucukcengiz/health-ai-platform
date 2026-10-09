import glob
import pandas as pd

glu_files = sorted(glob.glob('data/raw/glucose/glucose_*.csv'))
print("Bulunan glikoz dosyalari:", glu_files)

glu_all = pd.concat([pd.read_csv(f) for f in glu_files], ignore_index=True)
glu_all = glu_all.drop_duplicates(subset='SEQN')
print("Birlesik glikoz tablosu:", len(glu_all), "kisi")

main = pd.read_csv('data/processed/nafld_multicycle_final.csv')
print("Ana veri:", len(main), "kisi")

glu_small = glu_all[['SEQN', 'LBXGLU', 'WTSAF2YR']]
glu_small = glu_small.dropna(subset=['LBXGLU'])
merged = main.merge(glu_small, on='SEQN', how='inner')
print("Eslesen kisi sayisi:", len(merged))

male = merged['RIAGENDR'] == 1
waist_crit = (male & (merged['Waist_cm'] >= 102)) | (~male & (merged['Waist_cm'] >= 88))
tg_crit = merged['Triglyceride'] >= 150
hdl_crit = (male & (merged['HDL'] < 40)) | (~male & (merged['HDL'] < 50))
bp_crit = (merged['SBP'] >= 130) | (merged['DBP'] >= 85)
glu_crit = merged['LBXGLU'] >= 100

c1 = waist_crit.astype(int)
c2 = tg_crit.astype(int)
c3 = hdl_crit.astype(int)
c4 = bp_crit.astype(int)
c5 = glu_crit.astype(int)
crit_count = c1 + c2 + c3 + c4 + c5
merged['mets'] = (crit_count >= 3).astype(int)

print("Kriter basina eksik sayisi:")
print("Waist_cm eksik:", merged['Waist_cm'].isna().sum())
print("Triglyceride eksik:", merged['Triglyceride'].isna().sum())
print("HDL eksik:", merged['HDL'].isna().sum())
print("SBP eksik:", merged['SBP'].isna().sum())
print("DBP eksik:", merged['DBP'].isna().sum())
print("LBXGLU eksik:", merged['LBXGLU'].isna().sum())

print("MetS pozitif orani:", merged['mets'].mean())
print("Kriter dagilimi:")
print(crit_count.value_counts().sort_index())

merged.to_csv('data/processed/mets_merged.csv', index=False)
print("Kaydedildi: data/processed/mets_merged.csv")
