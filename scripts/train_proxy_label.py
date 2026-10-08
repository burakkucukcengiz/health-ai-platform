import json
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, train_test_split, cross_val_score
from sklearn.metrics import (roc_auc_score, average_precision_score,
                             confusion_matrix, classification_report)

df = pd.read_csv('data/processed/nafld_multicycle_final.csv')

# Vekil NAFLD etiketi (FIB-4'ten bagimsiz):
# ALT yuksek (erkek >30, kadin >19) VE en az bir metabolik kriter
# (bel yuksek: erkek >=102, kadin >=88 | TG >=150 | HDL dusuk: erkek <40, kadin <50)
male = df['RIAGENDR'] == 1
alt_high = ((male & (df['ALT'] > 30)) | (~male & (df['ALT'] > 19)))
waist_high = ((male & (df['Waist_cm'] >= 102)) | (~male & (df['Waist_cm'] >= 88)))
tg_high = df['Triglyceride'] >= 150
hdl_low = ((male & (df['HDL'] < 40)) | (~male & (df['HDL'] < 50)))
metabolic = waist_high | tg_high | hdl_low
df['target'] = (alt_high & metabolic).astype(int)

# Etiket kaynaklarini ve FIB-4 bilesenlerini ozellikten cikar
drop_cols = ['SEQN', 'CYCLE', 'NAFLD_Risk', 'target', 'FIB4', 'APRI',
             'TG_HDL', 'LBDHDD.1', 'ALT', 'AST', 'Platelet_K', 'Age']
X = df.drop(columns=[c for c in drop_cols if c in df.columns])
X = X.select_dtypes(include=[np.number])
X = X.fillna(X.median(numeric_only=True))
y = df['target']

print("Ozellikler:", list(X.columns))
print("Sinif dagilimi:\n", y.value_counts(normalize=True))

X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2,
                                          stratify=y, random_state=42)

model = RandomForestClassifier(n_estimators=300, class_weight='balanced',
                               random_state=42, n_jobs=-1)

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_auc = cross_val_score(model, X_tr, y_tr, cv=cv, scoring='roc_auc')
print(f"\n5-fold CV AUC: {cv_auc.mean():.4f} +/- {cv_auc.std():.4f}")

model.fit(X_tr, y_tr)
proba = model.predict_proba(X_te)[:, 1]
pred = (proba >= 0.5).astype(int)

metrics = {
    'label': 'proxy_metabolic_nafld (ALT + metabolic criteria)',
    'cv_auc_mean': float(cv_auc.mean()),
    'cv_auc_std': float(cv_auc.std()),
    'test_auc': float(roc_auc_score(y_te, proba)),
    'test_pr_auc': float(average_precision_score(y_te, proba)),
    'positive_rate': float(y.mean()),
    'features': list(X.columns),
}
print(json.dumps(metrics, indent=2))
print("\nConfusion matrix:\n", confusion_matrix(y_te, pred))
print("\n", classification_report(y_te, pred))

with open('models/metrics_proxy.json', 'w') as f:
    json.dump(metrics, f, indent=2)

joblib.dump(model, 'models/nafld_model_proxy.pkl')
joblib.dump(list(X.columns), 'models/feature_names_proxy.pkl')
print("\nKaydedildi: models/nafld_model_proxy.pkl, models/metrics_proxy.json")
