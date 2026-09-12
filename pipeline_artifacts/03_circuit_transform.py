import pandas as pd
import numpy as np

W_ORN_PN = np.load("outputs/W_ORN_PN.npy")
W_PN_KC   = np.load("outputs/W_PN_KC.npy")
sensilla  = pd.read_csv("outputs/sensilla_order.csv")["sensillum"].tolist()
print(f"Circuit: W_ORN_PN {W_ORN_PN.shape}, W_PN_KC {W_PN_KC.shape}")
print(f"Sensilla order: {sensilla}")

ind  = pd.read_csv("data/nowotny/deBruyne_industrialset_OlfCode_Drosophila_2014.csv")
wine = pd.read_csv("data/nowotny/deBruyne_wineset_OlfCode_Drosophila_2014.csv", encoding="latin-1")
print(f"\nIndustrial rows: {len(ind)}, Wine rows: {len(wine)}")

X_ind  = ind.pivot(index="odorant",  columns="neuron", values="mean")
X_wine = wine.pivot(index="odorant", columns="neuron", values="mean")
print(f"Pivoted: industrial {X_ind.shape}, wine {X_wine.shape}")

X_ind  = X_ind[sensilla]
X_wine = X_wine[sensilla]

print(f"NaN counts: industrial={X_ind.isna().sum().sum()}, wine={X_wine.isna().sum().sum()}")

X_orn = np.vstack([X_wine.values, X_ind.values]).astype(np.float32)
y     = np.array([0]*len(X_wine) + [1]*len(X_ind))
print(f"\nX_orn: {X_orn.shape}, y: {y.shape}")
print(f"Class balance: neutral={sum(y==0)}, hazardous={sum(y==1)}")
print(f"X_orn range: min={X_orn.min():.1f}, max={X_orn.max():.1f}")

print("\nApplying connectome transform...")
pn_activity = np.maximum(X_orn @ W_ORN_PN, 0)
print(f"PN activity: {pn_activity.shape}, nonzero={int((pn_activity>0).sum())}")

kc_raw = pn_activity @ W_PN_KC
print(f"KC raw: {kc_raw.shape}, nonzero={int((kc_raw>0).sum())}")

threshold = np.percentile(kc_raw, 95, axis=1, keepdims=True)
X_kc_sparse = np.where(kc_raw >= threshold, kc_raw, 0)
print(f"KC sparse: {(X_kc_sparse==0).mean()*100:.1f}% zeros")
print(f"Active KCs per sample: {(X_kc_sparse>0).sum(axis=1).mean():.0f} of {X_kc_sparse.shape[1]}")

np.save("outputs/X_orn.npy", X_orn)
np.save("outputs/X_kc_sparse.npy", X_kc_sparse)
np.save("outputs/X_kc_raw.npy", kc_raw)
np.save("outputs/y.npy", y)
print("\nSaved: X_orn.npy, X_kc_sparse.npy, X_kc_raw.npy, y.npy")
