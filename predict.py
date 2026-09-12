"""Load every model in models/, predict on the given CSV, write predictions.

Input CSV must contain the 20 sensilla columns (names in outputs/sensilla_order.csv).
Optional columns:
  - 'label'  : if present, accuracy is reported and stored
  - 'alpha'  : if present, copied through so plot.py can use it

Output: predictions/<input_stem>_predictions.csv
"""
import argparse
import numpy as np
import pandas as pd
import joblib
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("input", help="CSV with sensilla columns")
p.add_argument("--models-dir", default="models")
p.add_argument("--out-dir", default="predictions")
args = p.parse_args()

input_path = Path(args.input)
if not input_path.exists():
    raise SystemExit(f"ERROR: {input_path} not found")

models_dir = Path(args.models_dir)
model_files = sorted(models_dir.glob("*.joblib"))
if not model_files:
    raise SystemExit(f"ERROR: no .joblib files in {models_dir}/. Run train.py first.")

sensilla = pd.read_csv("outputs/sensilla_order.csv")["sensillum"].tolist()

print(f"Reading {input_path}")
df = pd.read_csv(input_path)
missing = [s for s in sensilla if s not in df.columns]
if missing:
    raise SystemExit(f"ERROR: missing sensilla columns: {missing}")

X = df[sensilla].values.astype(np.float32)
print(f"  {X.shape[0]} samples x {X.shape[1]} sensilla")
print(f"  Loading {len(model_files)} models: {[m.stem for m in model_files]}")

# Build output frame; carry through any passthrough columns
out = pd.DataFrame({"sample_id": np.arange(len(df))})
for passthrough in ("alpha", "label"):
    if passthrough in df.columns:
        out[passthrough] = df[passthrough].values

has_labels = "label" in df.columns
y_true = df["label"].values if has_labels else None

print("\n" + "=" * 60)
print("PREDICTIONS")
print("=" * 60)

for mf in model_files:
    name = mf.stem
    pipe = joblib.load(mf)
    preds = pipe.predict(X)
    proba = pipe.predict_proba(X)[:, 1]
    out[f"{name}_pred"]  = preds
    out[f"{name}_proba"] = proba
    if has_labels:
        acc = (preds == y_true).mean() * 100
        out[f"{name}_correct"] = (preds == y_true).astype(int)
        print(f"  {name:8s}: {acc:5.1f}%  ({int(acc*len(y_true)/100)}/{len(y_true)} correct)")
    else:
        n_ind = int((preds == 1).sum())
        print(f"  {name:8s}: {n_ind:2d}/{len(preds)} predicted industrial")

out_dir = Path(args.out_dir); out_dir.mkdir(exist_ok=True)
out_path = out_dir / f"{input_path.stem}_predictions.csv"
out.to_csv(out_path, index=False)
print(f"\nSaved -> {out_path}")
print(f"Next: python plot.py {out_path}")
