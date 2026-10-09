import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, train_test_split, cross_val_predict

df = pd.read_csv('data/processed/homa_merged.csv')
FEATURES = ['RIAGENDR', 'BMI', 'BMXWT', 'BMXHT', 'Waist_cm', 'SBP', 'DBP',
            'Triglyceride', 'LDL', 'Total_Cholesterol', 'HDL']
X = df[FEATURES].fillna(df[FEATURES].median())
y = df['homa_ir_positive']

X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

rf = RandomForestClassifier(n_estimators=300, class_weight='balanced', random_state=42, n_jobs=-1)
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
oof_proba = cross_val_predict(rf, X_tr, y_tr, cv=cv, method='predict_proba')[:, 1]

print("Esik | Precision | Recall | Pozitif tahmin orani")
for t in [0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65]:
    pred = (oof_proba >= t).astype(int)
    tp = ((pred == 1) & (y_tr == 1)).sum()
    prec = tp / max(pred.sum(), 1)
    rec = tp / max(y_tr.sum(), 1)
    print(t, "prec", round(prec, 3), "recall", round(rec, 3), "pos_rate", round(pred.mean(), 3))
