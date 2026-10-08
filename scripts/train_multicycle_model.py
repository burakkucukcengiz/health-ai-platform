import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report, confusion_matrix
import joblib
import os

print("="*60)
print("MULTI-CYCLE NAFLD MODEL EGITIMI (51K+ VERI)")
print("="*60)

df = pd.read_csv("data/processed/nafld_multicycle_clean.csv")
print(f"\nToplam veri: {len(df)} kisi")

# Kolon isimlerini standart isimlere cevir
df = df.rename(columns={
    "RIDAGEYR": "Age",
    "BMXBMI": "BMI",
    "LBXSASSI": "AST",
    "LBXSATSI": "ALT",
    "LBXPLTSI": "Platelet_K",
    "LBXTR": "Triglyceride",
    "LBXTC": "Total_Cholesterol",
    "LBDLDL": "LDL",
    "LBDHDD": "HDL",
    "BPXSY1": "SBP",
    "BPXDI1": "DBP",
    "BMXWAIST": "Waist_cm",
})

# Eksik HDL/LDL/Trigliserit/Kolesterol icin median doldur (cycle'lar arasi farklar olabilir)
for col in ["Triglyceride", "Total_Cholesterol", "LDL", "HDL", "SBP", "DBP", "Waist_cm"]:
    if col in df.columns:
        df[col] = df[col].fillna(df[col].median())

# HDL hesaplanamayan satirlari Friedewald formulu ile tahmin et (gerekirse)
df["HDL"] = df["HDL"].fillna(df["Total_Cholesterol"] - df["LDL"] - (df["Triglyceride"]/5))

# FIB-4 Index
df["FIB4"] = (df["Age"] * df["AST"]) / (df["Platelet_K"] * np.sqrt(df["ALT"]))

# APRI Score
df["APRI"] = ((df["AST"]/40) / df["Platelet_K"]) * 100

# TG/HDL Ratio
df["TG_HDL"] = df["Triglyceride"] / df["HDL"]

# Risk siniflandirma (FIB-4 bazli)
def classify_risk(fib4):
    if fib4 < 1.3:
        return "Low"
    elif fib4 < 2.67:
        return "Moderate"
    else:
        return "High"

df["NAFLD_Risk"] = df["FIB4"].apply(classify_risk)

print("\nRisk dagilimi:")
print(df["NAFLD_Risk"].value_counts())
print(df["NAFLD_Risk"].value_counts(normalize=True) * 100)

# Model icin feature'lar
X_cols = ["Age", "BMI", "AST", "ALT", "Platelet_K", "Triglyceride",
          "Total_Cholesterol", "LDL", "HDL", "SBP", "DBP", "Waist_cm"]

df = df.dropna(subset=X_cols)
print(f"\nModel icin kullanilabilir veri: {len(df)} kisi")

X = df[X_cols]
y = (df["NAFLD_Risk"] != "Low").astype(int)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"\nTrain: {len(X_train)}, Test: {len(X_test)}")

model = RandomForestClassifier(n_estimators=200, max_depth=15, random_state=42, n_jobs=-1)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
y_proba = model.predict_proba(X_test)[:, 1]

auc = roc_auc_score(y_test, y_proba)
print(f"\n{'='*60}")
print(f"AUC-ROC: {auc:.4f}")
print(f"{'='*60}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred))
print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

print("\nFeature Importance:")
importance = pd.Series(model.feature_importances_, index=X_cols).sort_values(ascending=False)
print(importance)

os.makedirs("models", exist_ok=True)
joblib.dump(model, "models/nafld_model_51k.pkl")
joblib.dump(X_cols, "models/feature_names_51k.pkl")

df.to_csv("data/processed/nafld_multicycle_final.csv", index=False)

print("\n✅ Kaydedildi: models/nafld_model_51k.pkl")
print("✅ Kaydedildi: data/processed/nafld_multicycle_final.csv")
