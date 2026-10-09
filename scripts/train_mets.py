import json
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold, train_test_split, cross_validate, cross_val_predict
from sklearn.metrics import roc_auc_score, average_precision_score, confusion_matrix, classification_report

df = pd.read_csv('data/processed/mets_merged.csv')

FEATURES = ['RIAGENDR', 'BMI', 'BMXWT', 'BMXHT', 'Waist_cm', 'SBP', 'DBP',
            'Triglyceride', 'LDL', 'Total_Cholesterol', 'HDL']
X = df[FEATURES].fillna(df[FEATURES].median())
y = df['mets']

print("Pozitif oran:", y.mean())
print("Ornek sayisi:", len(df))

X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

logistic = make_pipeline(StandardScaler(), LogisticRegression(class_weight='balanced', max_iter=1000))
rf = RandomForestClassifier(n_estimators=300, class_weight='balanced', random_state=42, n_jobs=-1)

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

for name, model in [('logistic', logistic), ('random_forest', rf)]:
    scores = cross_validate(model, X_tr, y_tr, cv=cv, scoring=['roc_auc', 'average_precision'])
    model.fit(X_tr, y_tr)
    proba = model.predict_proba(X_te)[:, 1]
    auc = roc_auc_score(y_te, proba)
    pr_auc = average_precision_score(y_te, proba)
    cv_auc = scores['test_roc_auc'].mean()
    cv_auc_std = scores['test_roc_auc'].std()
    cv_pr = scores['test_average_precision'].mean()
    print(name, "CV AUC", round(cv_auc, 4), "+/-", round(cv_auc_std, 4),
          "Test AUC", round(auc, 4), "CV PR-AUC", round(cv_pr, 4), "Test PR-AUC", round(pr_auc, 4))

# Secilen model: Random Forest, esikleri OOF uzerinden sec
oof_proba = cross_val_predict(rf, X_tr, y_tr, cv=cv, method='predict_proba')[:, 1]
print("\nEsik | Precision | Recall | Pozitif tahmin orani")
for t in [0.3, 0.4, 0.5, 0.6, 0.7]:
    pred = (oof_proba >= t).astype(int)
    tp = ((pred == 1) & (y_tr == 1)).sum()
    prec = tp / max(pred.sum(), 1)
    rec = tp / max(y_tr.sum(), 1)
    print(t, "prec", round(prec, 3), "recall", round(rec, 3), "pos_rate", round(pred.mean(), 3))

rf.fit(X_tr, y_tr)
test_proba = rf.predict_proba(X_te)[:, 1]
test_auc = roc_auc_score(y_te, test_proba)
test_pr = average_precision_score(y_te, test_proba)

metrics = {
    'label': 'metabolic_syndrome_ATPIII',
    'n_samples': len(df),
    'positive_rate': float(y.mean()),
    'test_auc': float(test_auc),
    'test_pr_auc': float(test_pr),
    'features': FEATURES,
}
with open('models/metrics_mets.json', 'w') as f:
    json.dump(metrics, f, indent=2)

joblib.dump(rf, 'models/mets_model.pkl')
joblib.dump(FEATURES, 'models/feature_names_mets.pkl')
print("\nKaydedildi: models/mets_model.pkl, models/metrics_mets.json")
