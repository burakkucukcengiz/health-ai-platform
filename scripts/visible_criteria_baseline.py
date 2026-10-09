import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, average_precision_score

df = pd.read_csv('data/processed/mets_merged.csv')

male = df['RIAGENDR'] == 1
waist_crit = (male & (df['Waist_cm'] >= 102)) | (~male & (df['Waist_cm'] >= 88))
tg_crit = df['Triglyceride'] >= 150
hdl_crit = (male & (df['HDL'] < 40)) | (~male & (df['HDL'] < 50))
bp_crit = (df['SBP'] >= 130) | (df['DBP'] >= 85)

visible_score = waist_crit.astype(int) + tg_crit.astype(int) + hdl_crit.astype(int) + bp_crit.astype(int)
y = df['mets']

_, _, _, _, score_train, score_test, y_train, y_test = train_test_split(
    df, df, visible_score, y, test_size=0.2, random_state=42, stratify=y
)

auc_naive = roc_auc_score(y_test, score_test)
pr_auc_naive = average_precision_score(y_test, score_test)

print("=== Sadece gorunur kriter sayisi (0-4), model yok ===")
print(f"Test AUC: {auc_naive:.4f}")
print(f"Test PR-AUC: {pr_auc_naive:.4f}")
print()
print("Esik | Precision | Recall | Pozitif tahmin orani")
for esik in [1, 2, 3]:
    pred = (score_test >= esik).astype(int)
    tp = ((pred == 1) & (y_test == 1)).sum()
    fp = ((pred == 1) & (y_test == 0)).sum()
    fn = ((pred == 0) & (y_test == 1)).sum()
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0
    pos_rate = pred.mean()
    print(f"visible_score>={esik} prec {prec:.3f} recall {rec:.3f} pos_rate {pos_rate:.3f}")

print()
print("Karsilastirma:")
print(f"  Naive (sadece 4 kriter sayisi)  Test AUC = {auc_naive:.4f}")
print(f"  RandomForest (train_mets.py)    Test AUC = 0.9752")
print(f"  Fark (modelin katkisi)          = {0.9752 - auc_naive:.4f}")
