"""Show diagnostic plots for any predictions CSV produced by predict.py.

Auto-detects what's available:
  - 'label' column   -> accuracy bar chart + confusion matrices
  - 'alpha' column   -> P(class=1) vs alpha curve
  - always           -> prediction heatmap (samples x models)

No files are saved. Close each window to see the next.
"""
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("predictions", help="CSV from predict.py")
args = p.parse_args()

path = Path(args.predictions)
if not path.exists():
    raise SystemExit(f"ERROR: {path} not found")

df = pd.read_csv(path)
model_names = sorted({c[:-5] for c in df.columns if c.endswith("_pred")})
if not model_names:
    raise SystemExit("ERROR: no <model>_pred columns found")

has_labels = "label" in df.columns
has_alpha  = "alpha" in df.columns
x_axis = df["alpha"].values if has_alpha else np.arange(len(df))
x_label = "alpha (0 = wine prototype, 1 = industrial)" if has_alpha else "sample index"

print(f"{path.name}: {len(df)} samples, models = {model_names}")
print(f"  has label: {has_labels}   has alpha: {has_alpha}")
print("Close each plot window to continue.\n")

# --- Plot 1: P(industrial) per model across samples / alpha ---
fig, ax = plt.subplots(figsize=(9, 5.5))
for name in model_names:
    ax.plot(x_axis, df[f"{name}_proba"], marker="o", label=name,
            linewidth=2, markersize=4)
ax.axhline(0.5, color="k", linestyle="--", alpha=0.4, label="decision boundary")
ax.set_xlabel(x_label)
ax.set_ylabel("P(industrial) predicted")
ax.set_title(f"Model behavior — {path.name}")
ax.set_ylim(-0.05, 1.05)
ax.legend(); ax.grid(alpha=0.3)
plt.tight_layout(); plt.show()

# --- Plot 2: prediction heatmap (samples x models) ---
fig, ax = plt.subplots(figsize=(6, max(5, len(df) * 0.25)))
pred_matrix = np.column_stack([df[f"{name}_pred"].values for name in model_names])
ax.imshow(pred_matrix, aspect="auto", cmap="coolwarm", vmin=0, vmax=1)
ax.set_xticks(range(len(model_names))); ax.set_xticklabels(model_names)
ax.set_yticks(range(len(df)))
if has_alpha:
    ax.set_yticklabels([f"{a:.2f}" for a in df["alpha"].values], fontsize=7)
ax.set_xlabel("model"); ax.set_ylabel("alpha" if has_alpha else "sample")
ax.set_title(f"Predicted class per sample per model\n(blue = wine, red = industrial)")
for i in range(len(df)):
    for j, name in enumerate(model_names):
        v = pred_matrix[i, j]
        ax.text(j, i, "W" if v == 0 else "I", ha="center", va="center",
                fontsize=8, color="white" if v == 1 else "black")
plt.tight_layout(); plt.show()

# --- Plot 3 (only if labels present): accuracy + confusion matrices ---
if has_labels:
    y_true = df["label"].values
    accs = [(name, (df[f"{name}_pred"] == y_true).mean() * 100) for name in model_names]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar([a[0] for a in accs], [a[1] for a in accs],
                  color="steelblue", edgecolor="black")
    ax.axhline(50, color="red", linestyle="--", alpha=0.5, label="chance")
    ax.set_ylabel("Accuracy (%)"); ax.set_ylim(0, 105)
    ax.set_title(f"Accuracy — {path.name}")
    for b, (_, v) in zip(bars, accs):
        ax.text(b.get_x() + b.get_width()/2, v + 1.5, f"{v:.1f}%",
                ha="center", fontsize=11)
    ax.legend(); ax.grid(axis="y", alpha=0.3)
    plt.tight_layout(); plt.show()

    for name in model_names:
        cm = confusion_matrix(y_true, df[f"{name}_pred"].values, labels=[0, 1])
        fig, ax = plt.subplots(figsize=(5, 4.5))
        ConfusionMatrixDisplay(cm, display_labels=["wine", "industrial"]).plot(
            ax=ax, cmap="Blues", colorbar=False)
        acc = (df[f"{name}_pred"] == y_true).mean() * 100
        ax.set_title(f"{name} — confusion (acc {acc:.1f}%)")
        plt.tight_layout(); plt.show()

print("All plots shown. No files were saved.")
