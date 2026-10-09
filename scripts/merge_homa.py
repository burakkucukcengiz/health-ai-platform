import pandas as pd

homa = pd.read_csv('data/processed/homa_ir.csv')
main = pd.read_csv('data/processed/nafld_multicycle_final.csv')

print("HOMA-IR tablosu:", len(homa), "kisi")
print("Ana veri:", len(main), "kisi")

merged = pd.merge(homa[['SEQN', 'HOMA_IR']], main, on='SEQN', how='inner')
merged['homa_ir_positive'] = (merged['HOMA_IR'] >= 2.5).astype(int)

print("Eslesen kisi sayisi:", len(merged))
print("HOMA-IR >= 2.5 pozitif oran:", merged['homa_ir_positive'].mean())

FEATURES = ['RIAGENDR', 'BMI', 'BMXWT', 'BMXHT', 'Waist_cm', 'SBP', 'DBP',
            'Triglyceride', 'LDL', 'Total_Cholesterol', 'HDL']
print("\nOzellik basina eksik sayisi:")
for f in FEATURES:
    if f in merged.columns:
        print(f, "eksik:", merged[f].isna().sum())
    else:
        print(f, "KOLON YOK")

merged.to_csv('data/processed/homa_merged.csv', index=False)
print("\nKaydedildi: data/processed/homa_merged.csv")
