import pandas as pd
import numpy as np

print("="*60)
print("MULTI-CYCLE NHANES VERI TEMIZLEME")
print("="*60)

df = pd.read_csv("data/raw/nhanes_multicycle_raw.csv")
print(f"\nBaslangic (ham veri): {len(df)} kisi")

# AST/ALT eksik olanlari cikar
df = df.dropna(subset=["LBXSASSI", "LBXSATSI"])
print(f"AST/ALT eksik cikarildi: {len(df)} kisi")

# BMI/Weight/Height eksik olanlari cikar
df = df.dropna(subset=["BMXBMI", "BMXWT", "BMXHT"])
print(f"BMI/Weight/Height eksik cikarildi: {len(df)} kisi")

# 18 yas alti filtrele
df = df[df["RIDAGEYR"] >= 18]
print(f"18 yas alti filtrelendi: {len(df)} kisi")

# Eksik degerleri median ile doldur
numeric_cols = ["BMXWAIST", "BPXSY1", "BPXDI1", "LBXPLTSI",
                 "LBXTR", "LBXTC", "LBDLDL", "LBDHDD"]
for col in numeric_cols:
    if col in df.columns:
        median_val = df[col].median()
        df[col] = df[col].fillna(median_val)

print(f"\n=== SONUC: {len(df)} temiz yetiskin ===")

df.to_csv("data/processed/nafld_multicycle_clean.csv", index=False)
print("Kaydedildi: data/processed/nafld_multicycle_clean.csv")

print("\nCycle dagilimi:")
print(df["CYCLE"].value_counts().sort_index())
