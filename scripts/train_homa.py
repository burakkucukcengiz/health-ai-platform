import json
import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold, train_test_split, cross_validate
from sklearn.metrics import roc_auc_score, average_precision_score

df = pd.read_csv('data/processed/homa_merged.csv')

FEATURES = ['RIAGENDR', 'BMI', 'BMXWT', 'BMXHT', 'Waist_cm', 'SBP', 'DBP',
            'Triglyceride', 'LDL', 'Total_Cholesterol', 'HDL']
X = df[FEATURES].fillna(df[FEATURES].median())
y = df['homa_ir_positive']

print("Pozitif oran:", y.mean())
print("Ornek sayisi:", len(df))
print("Not: glikoz ve insulin bu modelde OZELLIK OLARAK KULLANILMIYOR,")
print("yalnizca hedef (HOMA-IR >= 2.5) hesaplamak icin kullanildi. Bu yuzden")
print("bu model, NAFLD/MetS modellerinden farkli olarak sizintisiz olmali.")

X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

logistic = make_pipeline(StandardScaler(), LogisticRegression(class_weight='balanced', max_iter=1000))
rf = RandomForestClassifier(n_estimators=300, class_weight='balanced', random_state=42, n_jobs=-1)

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

results = {}
for name, model in [('logistic', logistic), ('random_forest', rf)]:
    scores = cross_validate(model, X_tr, y_tr, cv=cv, scoring=['roc_auc', 'average_precision'])
    model.fit(X_tr, y_tr)
    proba = model.predict_proba(X_te)[:, 1]
    auc = roc_auc_score(y_te, proba)
    pr_auc = average_precision_score(y_te, proba)
    cv_auc = scores['test_roc_auc'].mean()
    cv_pr = scores['test_average_precision'].mean()
    results[name] = {'test_auc': float(auc), 'test_pr_auc': float(pr_auc)}
    print(name, "CV AUC", round(cv_auc, 4), "Test AUC", round(auc, 4),
          "CV PR-AUC", round(cv_pr, 4), "Test PR-AUC", round(pr_auc, 4))

rf.fit(X_tr, y_tr)
test_proba = rf.predict_proba(X_te)[:, 1]
test_auc = roc_auc_score(y_te, test_proba)
test_pr = average_precision_score(y_te, test_proba)

metrics = {
    'label': 'homa_ir_insulin_resistance',
    'threshold': 2.5,
    'n_samples': len(df),
    'positive_rate': float(y.mean()),
    'test_auc': float(test_auc),
    'test_pr_auc': float(test_pr),
    'features': FEATURES,
    'note': 'Glikoz ve insulin ozellik olarak kullanilmadi, sadece hedef uretiminde kullanildi. Bu model NAFLD/MetS modellerine kiyasla sizinti icermemelidir.',
}
with open('models/metrics_homa.json', 'w') as f:
    json.dump(metrics, f, indent=2)

joblib.dump(rf, 'models/homa_model.pkl')
joblib.dump(FEATURES, 'models/feature_names_homa.pkl')
print("\nKaydedildi: models/homa_model.pkl, models/metrics_homa.json")
