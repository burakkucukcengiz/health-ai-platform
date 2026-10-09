import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, train_test_split, cross_validate
from sklearn.metrics import roc_auc_score, average_precision_score

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

models = {
    'logistic': make_pipeline(StandardScaler(),
                              LogisticRegression(class_weight='balanced', max_iter=1000)),
    'random_forest': RandomForestClassifier(n_estimators=300, class_weight='balanced',
                                            random_state=42, n_jobs=-1),
}

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
for name, m in models.items():
    scores = cross_validate(m, X_tr, y_tr, cv=cv, scoring=['roc_auc', 'average_precision'])
    m.fit(X_tr, y_tr)
    proba = m.predict_proba(X_te)[:, 1]
    print(f"{name:14s} CV AUC {scores['test_roc_auc'].mean():.4f} "
          f"± {scores['test_roc_auc'].std():.4f} | "
          f"CV PR-AUC {scores['test_average_precision'].mean():.4f} | "
          f"Test AUC {roc_auc_score(y_te, proba):.4f} | "
          f"Test PR-AUC {average_precision_score(y_te, proba):.4f}")
