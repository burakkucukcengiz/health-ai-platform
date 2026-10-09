import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.metrics import brier_score_loss, roc_auc_score

df = pd.read_csv('data/processed/nafld_multicycle_final.csv')

# Etiket: train_proxy_label.py ile birebir aynı
male = df['RIAGENDR'] == 1
alt_high = (male & (df['ALT'] > 30)) | (~male & (df['ALT'] > 19))
waist_high = (male & (df['Waist_cm'] >= 102)) | (~male & (df['Waist_cm'] >= 88))
tg_high = df['Triglyceride'] >= 150
hdl_low = (male & (df['HDL'] < 40)) | (~male & (df['HDL'] < 50))
df['target'] = (alt_high & (waist_high | tg_high | hdl_low)).astype(int)

FEATURES = ['RIAGENDR', 'BMI', 'BMXWT', 'BMXHT', 'Waist_cm', 'SBP', 'DBP',
            'Triglyceride', 'LDL', 'Total_Cholesterol', 'HDL']
X = df[FEATURES].fillna(df[FEATURES].median())
y = df['target']

X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2,
                                         stratify=y, random_state=42)

base = RandomForestClassifier(n_estimators=300, class_weight='balanced',
                              random_state=42, n_jobs=-1)
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

# Ham RF (class_weight nedeniyle kaymış olasılıklar)
base.fit(X_tr, y_tr)
raw = base.predict_proba(X_te)[:, 1]

# Sigmoid kalibrasyon (Platt), 5-katlı CV ile
calib = CalibratedClassifierCV(
    RandomForestClassifier(n_estimators=300, class_weight='balanced',
                           random_state=42, n_jobs=-1),
    method='sigmoid', cv=cv)
calib.fit(X_tr, y_tr)
cal = calib.predict_proba(X_te)[:, 1]

print(f"{'':12s}{'AUC':>8s}{'Brier':>10s}")
print(f"{'Ham RF':12s}{roc_auc_score(y_te, raw):8.4f}{brier_score_loss(y_te, raw):10.4f}")
print(f"{'Kalibre':12s}{roc_auc_score(y_te, cal):8.4f}{brier_score_loss(y_te, cal):10.4f}")

print("\nKalibrasyon (ortalama tahmin vs gerçek oran), 10 kova:")
for name, p in [('Ham RF', raw), ('Kalibre', cal)]:
    frac, mean = calibration_curve(y_te, p, n_bins=10, strategy='quantile')
    print(f"\n{name}:")
    for m, f in zip(mean, frac):
        print(f"  tahmin {m:.3f}  gerçek {f:.3f}")

print(f"\nTest pozitif oranı: {y_te.mean():.3f}")
print(f"Kalibre skorun ortalaması: {cal.mean():.3f}")
