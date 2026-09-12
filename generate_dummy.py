"""Generate synthetic ORN samples along a wine -> industrial gradient.

Writes a CSV with one row per sample: 20 sensilla columns + an 'alpha' column.
The alpha column lets plot.py show the model's behavior along the gradient.
"""
import argparse
import numpy as np
import pandas as pd

p = argparse.ArgumentParser()
p.add_argument("--n", type=int, default=30, help="number of samples")
p.add_argument("--out", default="dummy.csv", help="output CSV path")
p.add_argument("--noise", type=float, default=0.25, help="noise scale")
p.add_argument("--seed", type=int, default=42)
args = p.parse_args()

# Prototypes come from the real data so the dummy lives in the same feature space
X = np.load("outputs/X_orn.npy")
y = np.load("outputs/y.npy")
sensilla = pd.read_csv("outputs/sensilla_order.csv")["sensillum"].tolist()

wine_mean = X[y == 0].mean(axis=0)
ind_mean  = X[y == 1].mean(axis=0)
scale     = X.std(axis=0)

rng = np.random.default_rng(args.seed)
alphas = np.linspace(0.0, 1.0, args.n)
X_dummy = np.zeros((args.n, len(sensilla)), dtype=np.float32)
for i, a in enumerate(alphas):
    base = (1 - a) * wine_mean + a * ind_mean
    X_dummy[i] = base + rng.normal(0, args.noise * scale, size=len(sensilla))

df = pd.DataFrame(X_dummy, columns=sensilla)
df.insert(0, "alpha", alphas)          # alpha at front, sensilla after
df.to_csv(args.out, index=False)

print(f"Wrote {args.out}: {df.shape} ({args.n} samples, {len(sensilla)} sensilla + alpha)")
print(f"  Row 0     = pure wine prototype")
print(f"  Row {args.n//2}    = ambiguous mixture")
print(f"  Row {args.n-1}    = pure industrial prototype")
