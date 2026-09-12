import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics import confusion_matrix
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

X_orn       = np.load("outputs/X_orn.npy")
X_kc_sparse = np.load("outputs/X_kc_sparse.npy")
X_kc_raw    = np.load("outputs/X_kc_raw.npy")
y           = np.load("outputs/y.npy")

print(f"X_orn:       {X_orn.shape}")
print(f"X_kc_sparse: {X_kc_sparse.shape}")
print(f"X_kc_raw:    {X_kc_raw.shape}")
print(f"y:           {y.shape}, classes: {np.bincount(y)}")

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

models = {
    "LogReg":  LogisticRegression(C=1.0, max_iter=2000),
    "SVM":     SVC(kernel="rbf", C=10, gamma="scale"),
    "RF":      RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42),
    "MLP":     MLPClassifier(hidden_layer_sizes=(32,), max_iter=1000,
                             early_stopping=True, random_state=42),
}

feature_sets = {
    "Raw ORN (20-D)":        X_orn,
    "KC raw (5177-D)":       X_kc_raw,
    "KC sparse (5177-D)":    X_kc_sparse,
    "KC-SVD (20-D)":         TruncatedSVD(n_components=20, random_state=42).fit_transform(X_kc_sparse),
    "KC-SVD (10-D)":         TruncatedSVD(n_components=10, random_state=42).fit_transform(X_kc_sparse),
}

results = {}
for fs_name, X in feature_sets.items():
    print(f"\n=== {fs_name} ===")
    results[fs_name] = {}
    for model_name, model in models.items():
        pipe = Pipeline([("scale", StandardScaler()), ("clf", model)])
        scores = cross_val_score(pipe, X, y, cv=cv, scoring="accuracy")
        results[fs_name][model_name] = (scores.mean(), scores.std())
        print(f"  {model_name:8s}: {scores.mean()*100:.1f}% +/- {scores.std()*100:.1f}%")

# Build comparison table
print("\n" + "=" * 70)
print("FINAL COMPARISON TABLE")
print("=" * 70)
df = pd.DataFrame({fs: {m: f"{acc*100:.1f} +/- {sd*100:.1f}"
                        for m, (acc, sd) in models_d.items()}
                   for fs, models_d in results.items()})
print(df.to_string())
df.to_csv("outputs/connectome_comparison.csv")

# Shuffled-label negative control
print("\n" + "=" * 70)
print("CONTROL B: SHUFFLED LABELS (should be ~50%)")
print("=" * 70)
rng = np.random.default_rng(42)
y_shuf = rng.permutation(y)
for fs_name, X in feature_sets.items():
    pipe = Pipeline([("scale", StandardScaler()),
                     ("clf", RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42))])
    scores = cross_val_score(pipe, X, y_shuf, cv=cv, scoring="accuracy")
    print(f"  {fs_name:22s}: {scores.mean()*100:.1f}% +/- {scores.std()*100:.1f}%")

# Confusion matrix for best result
print("\n" + "=" * 70)
print("CONFUSION MATRIX — best model on KC sparse")
print("=" * 70)
from sklearn.model_selection import cross_val_predict
best_pipe = Pipeline([("scale", StandardScaler()),
                      ("clf", RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42))])
y_pred = cross_val_predict(best_pipe, X_kc_sparse, y, cv=cv)
cm = confusion_matrix(y, y_pred)
print(f"  Predicted:  0    1")
print(f"  True 0:  {cm[0,0]:3d}  {cm[0,1]:3d}")
print(f"  True 1:  {cm[1,0]:3d}  {cm[1,1]:3d}")

# Save summary plot
fig, ax = plt.subplots(figsize=(10, 6))
fs_names = list(feature_sets.keys())
model_names = list(models.keys())
x = np.arange(len(fs_names))
width = 0.2
for i, m in enumerate(model_names):
    means = [results[fs][m][0]*100 for fs in fs_names]
    stds  = [results[fs][m][1]*100 for fs in fs_names]
    ax.bar(x + i*width, means, width, yerr=stds, label=m, capsize=4)
ax.set_xticks(x + width*1.5)
ax.set_xticklabels(fs_names, rotation=20, ha="right")
ax.set_ylabel("5-fold CV accuracy (%)")
ax.set_title("Raw ORN vs Connectome-derived KC features")
ax.axhline(50, color="k", linestyle="--", alpha=0.3, label="chance")
ax.legend()
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig("outputs/connectome_comparison.png", dpi=150)
print("\nSaved: outputs/connectome_comparison.csv and .png")
