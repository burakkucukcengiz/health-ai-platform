import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import precision_recall_curve, roc_auc_score

df = pd.read_csv('data/processed/nafld_multicycle_final.csv')

# Etiket: train_proxy_label.py ile birebir aynı olmalı
male = df['RIAGENDR'] == 1
alt_high = (male & (df['ALT'] > 30)) | (~male & (df['ALT'] > 19))
waist_high = (male & (df['Waist_cm'] >= 102)) | (~male & (df['Waist_cm'] >= 88))
tg_high = df['Triglyceride'] >= 150
hdl_low = (male & (df['HDL'] < 40)) | (~male & (df['HDL'] < 50))
df['target'] = (alt_high & (waist_high | tg_high | hdl_low)).astype(int)

drop_cols = ['SEQN', 'CYCLE', 'NAFLD_Risk', 'target', 'FIB4', 'APRI',
             'TG_HDL', 'LBDHDD.1', 'ALT', 'AST', 'Platelet_K', 'Age']
X = df.drop(columns=[c for c in drop_cols if c in df.columns])
X = X.select_dtypes(include=[np.number])
X = X.fillna(X.median(numeric_only=True))
y = df['target']

model = RandomForestClassifier(n_estimators=300, class_weight='balanced',
                               random_state=42, n_jobs=-1)
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
proba = cross_val_predict(model, X, y, cv=cv, method='predict_proba')[:, 1]

print(f"OOF AUC: {roc_auc_score(y, proba):.4f}\n")

print("Eşik | Precision | Recall | Pozitif tahmin oranı")
for t in [0.2, 0.3, 0.4, 0.5, 0.6, 0.7]:
    pred = (proba >= t).astype(int)
    tp = ((pred == 1) & (y == 1)).sum()
    prec = tp / max(pred.sum(), 1)
    rec = tp / max(y.sum(), 1)
    print(f"{t:.1f}  |  {prec:.3f}   |  {rec:.3f}  |  {pred.mean():.3f}")

print("\nHedef dağılım (popülasyon yüzdesi) için eşik önerileri:")
for pct in [0.50, 0.75, 0.90, 0.95]:
    t = np.quantile(proba, pct)
    print(f"Üst %{int((1-pct)*100)} = eşik {t:.3f}")
