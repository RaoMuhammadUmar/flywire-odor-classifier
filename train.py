"""Train 4 classifiers on a CSV of ORN features + labels.

Auto-bootstraps data/train.csv from outputs/X_orn.npy + outputs/y.npy
if that file doesn't exist.

Splits 80/20 stratified, saves:
  models/*.joblib           — trained pipelines
  models/test_indices.npy   — row indices of the held-out test set
  data/test_holdout.csv     — the test CSV, ready for predict.py
"""
import argparse
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier

p = argparse.ArgumentParser()
p.add_argument("--data", default="data/train.csv")
p.add_argument("--test-size", type=float, default=0.2)
p.add_argument("--seed", type=int, default=42)
args = p.parse_args()

MODELS_DIR = Path("models");  MODELS_DIR.mkdir(exist_ok=True)
DATA_DIR   = Path("data");    DATA_DIR.mkdir(exist_ok=True)

# --- Bootstrap the training CSV from the pipeline .npy files if needed ---
data_path = Path(args.data)
if not data_path.exists() and data_path == Path("data/train.csv"):
    print("data/train.csv not found -- bootstrapping from outputs/*.npy")
    X = np.load("outputs/X_orn.npy")
    y = np.load("outputs/y.npy")
    sensilla = pd.read_csv("outputs/sensilla_order.csv")["sensillum"].tolist()
    df = pd.DataFrame(X, columns=sensilla)
    df["label"] = y
    df.to_csv(data_path, index=False)
    print(f"  Wrote {data_path}: {df.shape}")

print(f"Loading {data_path}")
df = pd.read_csv(data_path)

if "label" not in df.columns:
    raise SystemExit(f"ERROR: {data_path} has no 'label' column")

y = df["label"].values
X = df.drop(columns=["label"]).values
print(f"  X: {X.shape}, y: {y.shape}, classes: {np.bincount(y)}")

# --- Stratified 80/20 split ---
idx = np.arange(len(y))
X_tr, X_te, y_tr, y_te, i_tr, i_te = train_test_split(
    X, y, idx, test_size=args.test_size, stratify=y, random_state=args.seed)

np.save(MODELS_DIR / "test_indices.npy", i_te)
np.save(MODELS_DIR / "train_indices.npy", i_tr)

# Save the test set as a CSV so predict.py can consume it directly
test_df = df.iloc[i_te].reset_index(drop=True)
test_df.to_csv(DATA_DIR / "test_holdout.csv", index=False)

print(f"\nTrain: {X_tr.shape}  classes {np.bincount(y_tr)}")
print(f"Test:  {X_te.shape}  classes {np.bincount(y_te)}")
print(f"  -> {DATA_DIR/'test_holdout.csv'}")

# --- Models ---
models = {
    "LogReg": LogisticRegression(C=1.0, max_iter=2000, random_state=args.seed),
    "SVM":    SVC(kernel="rbf", C=10, gamma="scale", probability=True, random_state=args.seed),
    "RF":     RandomForestClassifier(n_estimators=200, max_depth=10, random_state=args.seed),
    "MLP":    MLPClassifier(hidden_layer_sizes=(32,), max_iter=1000,
                            early_stopping=True, random_state=args.seed),
}
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=args.seed)

print("\n" + "=" * 60)
print("5-fold CV on TRAINING set")
print("=" * 60)
for name, model in models.items():
    pipe = Pipeline([("scale", StandardScaler()), ("clf", model)])
    scores = cross_val_score(pipe, X_tr, y_tr, cv=cv, scoring="accuracy")
    print(f"  {name:8s}: {scores.mean()*100:5.1f}% +/- {scores.std()*100:.1f}%")
    pipe.fit(X_tr, y_tr)
    joblib.dump(pipe, MODELS_DIR / f"{name}.joblib")

print(f"\nSaved {len(models)} models -> {MODELS_DIR}/")
print("Next: python predict.py data/test_holdout.csv")
