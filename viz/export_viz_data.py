"""Export 3D brain visualization data.

Reads:
  data/flywire_raw/coordinates.csv            (soma positions)
  data/flywire_raw/consolidated_cell_types.csv
  data/flywire_raw/classification.csv
  outputs/X_orn.npy, X_kc_raw.npy, y.npy, sensilla_order.csv
  outputs/W_ORN_PN.npy                        (for PN activity)
  models/*.joblib                             (for predictions)

Writes:
  viz/brain_data.json
"""
import json
import numpy as np
import pandas as pd
import joblib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "viz"
OUT_DIR.mkdir(exist_ok=True)

SENSILLUM_TO_GLOM = {
    'ab1A':'DM1','ab1B':'VA2','ab1C':'V','ab1D':'DL1',
    'ab2A':'DM4','ab2B':'DM5','ab3A':'DM2','ab3B':'VM5d',
    'ab4A':'DL5','ab4B':'DA2','ab5A':'VA6','ab5B':'DM3',
    'ab7A':'VM5v','ab7B':'VC4','ab8A':'VM2','ab8B':'VM3',
    'pb1A':'VM7d','pb1B':'VC2','pb3A':'VM7v','pb3B':'VA4',
}
sensilla = list(SENSILLUM_TO_GLOM.keys())
glom_to_sens_idx = {SENSILLUM_TO_GLOM[s]: i for i, s in enumerate(sensilla)}

print("[1/6] Loading coordinates...")
coords = pd.read_csv(ROOT / "data/flywire_raw/coordinates.csv")
pos_split = coords["position"].str.strip("[]").str.split(expand=True).astype(np.int64)
coords["x"] = pos_split[0]
coords["y"] = pos_split[1]
coords["z"] = pos_split[2]
coord_map = dict(zip(coords["root_id"], zip(coords["x"], coords["y"], coords["z"])))
print(f"  {len(coord_map)} neurons with coordinates")

print("[2/6] Loading cell types...")
ct = pd.read_csv(ROOT / "data/flywire_raw/consolidated_cell_types.csv")
cl = pd.read_csv(ROOT / "data/flywire_raw/classification.csv")

print("[3/6] Collecting ORN / PN / KC root_ids...")
orn_by_glom = {}
for sens, glom in SENSILLUM_TO_GLOM.items():
    ids = ct[ct["primary_type"] == f"ORN_{glom}"]["root_id"].tolist()
    orn_by_glom[glom] = ids

alpn_ids = cl[cl["class"] == "ALPN"]["root_id"].tolist()
kc_ids = cl[cl["class"] == "Kenyon_Cell"]["root_id"].tolist()

print(f"  ORNs total: {sum(len(v) for v in orn_by_glom.values())}")
print(f"  ALPNs: {len(alpn_ids)}")
print(f"  KCs: {len(kc_ids)}")

orn_root_ids, orn_glom_idx = [], []
for sens, glom in SENSILLUM_TO_GLOM.items():
    idx = glom_to_sens_idx[glom]
    for rid in orn_by_glom[glom]:
        orn_root_ids.append(rid)
        orn_glom_idx.append(idx)

def keep_with_coords(root_ids):
    return [(i, r) for i, r in enumerate(root_ids) if r in coord_map]

orn_kept = keep_with_coords(orn_root_ids)
pn_kept = keep_with_coords(alpn_ids)
kc_kept = keep_with_coords(kc_ids)

print(f"  With coords -- ORNs: {len(orn_kept)}/{len(orn_root_ids)}, "
      f"PNs: {len(pn_kept)}/{len(alpn_ids)}, KCs: {len(kc_kept)}/{len(kc_ids)}")

all_pos = np.array([coord_map[r] for _, r in orn_kept + pn_kept + kc_kept], dtype=np.float64)
center = all_pos.mean(axis=0)
centered = all_pos - center
extent = np.abs(centered).max()
scale = 5.0 / extent

def scaled_pos(rid):
    p = np.array(coord_map[rid], dtype=np.float64)
    return ((p - center) * scale).tolist()

print("[4/6] Loading activity data...")
X_orn = np.load(ROOT / "outputs/X_orn.npy")
X_kc = np.load(ROOT / "outputs/X_kc_raw.npy")
y = np.load(ROOT / "outputs/y.npy")
W_ORN_PN = np.load(ROOT / "outputs/W_ORN_PN.npy")

X_pn = np.maximum(X_orn @ W_ORN_PN, 0)
print(f"  X_orn {X_orn.shape}, X_pn {X_pn.shape}, X_kc {X_kc.shape}")

pn_indices = [i for i, _ in pn_kept]
X_pn = X_pn[:, pn_indices]
kc_indices = [i for i, _ in kc_kept]
X_kc = X_kc[:, kc_indices]

print("[5/6] Running models on all samples...")
model_files = sorted((ROOT / "models").glob("*.joblib"))
predictions = {}
for mf in model_files:
    pipe = joblib.load(mf)
    pred = pipe.predict(X_orn)
    proba = pipe.predict_proba(X_orn)[:, 1]
    predictions[mf.stem] = {"pred": pred.tolist(), "proba": proba.tolist()}

def norm_uint8(arr):
    a = arr.astype(np.float32)
    amax = a.max(axis=1, keepdims=True)
    amax[amax == 0] = 1
    return np.round(a / amax * 255).astype(np.uint8)

X_orn_u8 = norm_uint8(X_orn)
X_pn_u8 = norm_uint8(X_pn)
X_kc_u8 = norm_uint8(X_kc)

print("[6/6] Writing JSON...")
data = {
    "meta": {
        "sensilla": sensilla,
        "glomeruli": [SENSILLUM_TO_GLOM[s] for s in sensilla],
        "n_samples": len(X_orn),
        "orn_total": len(orn_kept),
        "pn_total": len(pn_kept),
        "kc_total": len(kc_kept),
    },
    "neurons": {
        "orn": {
            "root_ids": [str(r) for _, r in orn_kept],
            "positions": [c for _, r in orn_kept for c in scaled_pos(r)],
            "glom_idx": [orn_glom_idx[i] for i, _ in orn_kept],
        },
        "pn": {
            "root_ids": [str(r) for _, r in pn_kept],
            "positions": [c for _, r in pn_kept for c in scaled_pos(r)],
        },
        "kc": {
            "root_ids": [str(r) for _, r in kc_kept],
            "positions": [c for _, r in kc_kept for c in scaled_pos(r)],
        },
    },
    "samples": [
        {
            "id": i,
            "true_label": int(y[i]),
            "orn": X_orn_u8[i].tolist(),
            "pn": X_pn_u8[i].tolist(),
            "kc": X_kc_u8[i].tolist(),
            "predictions": {
                name: {"pred": int(predictions[name]["pred"][i]),
                       "proba": float(predictions[name]["proba"][i])}
                for name in predictions
            },
        }
        for i in range(len(X_orn))
    ],
}

out_path = OUT_DIR / "brain_data.json"
with open(out_path, "w") as f:
    json.dump(data, f, separators=(",", ":"))
size_mb = out_path.stat().st_size / 1e6
print(f"  Wrote {out_path} ({size_mb:.2f} MB)")
print("Done.")
"""Export 3D brain visualization data (with edges)."""
import json
import numpy as np
import pandas as pd
import joblib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "viz"
OUT_DIR.mkdir(exist_ok=True)

SENSILLUM_TO_GLOM = {
    'ab1A':'DM1','ab1B':'VA2','ab1C':'V','ab1D':'DL1',
    'ab2A':'DM4','ab2B':'DM5','ab3A':'DM2','ab3B':'VM5d',
    'ab4A':'DL5','ab4B':'DA2','ab5A':'VA6','ab5B':'DM3',
    'ab7A':'VM5v','ab7B':'VC4','ab8A':'VM2','ab8B':'VM3',
    'pb1A':'VM7d','pb1B':'VC2','pb3A':'VM7v','pb3B':'VA4',
}
sensilla = list(SENSILLUM_TO_GLOM.keys())
glom_to_sens_idx = {SENSILLUM_TO_GLOM[s]: i for i, s in enumerate(sensilla)}

print("[1/7] Loading coordinates...")
coords = pd.read_csv(ROOT / "data/flywire_raw/coordinates.csv")
pos_split = coords["position"].str.strip("[]").str.split(expand=True).astype(np.int64)
coords["x"] = pos_split[0]; coords["y"] = pos_split[1]; coords["z"] = pos_split[2]
coord_map = dict(zip(coords["root_id"], zip(coords["x"], coords["y"], coords["z"])))
print(f"  {len(coord_map)} neurons")

print("[2/7] Loading cell types...")
ct = pd.read_csv(ROOT / "data/flywire_raw/consolidated_cell_types.csv")
cl = pd.read_csv(ROOT / "data/flywire_raw/classification.csv")

print("[3/7] Collecting root_ids...")
orn_by_glom = {g: ct[ct["primary_type"] == f"ORN_{g}"]["root_id"].tolist()
               for g in SENSILLUM_TO_GLOM.values()}
alpn_ids = cl[cl["class"] == "ALPN"]["root_id"].tolist()
kc_ids = cl[cl["class"] == "Kenyon_Cell"]["root_id"].tolist()

orn_root_ids, orn_glom_idx = [], []
for sens, glom in SENSILLUM_TO_GLOM.items():
    idx = glom_to_sens_idx[glom]
    for rid in orn_by_glom[glom]:
        orn_root_ids.append(rid); orn_glom_idx.append(idx)

def keep(root_ids): return [(i, r) for i, r in enumerate(root_ids) if r in coord_map]
orn_kept = keep(orn_root_ids); pn_kept = keep(alpn_ids); kc_kept = keep(kc_ids)
print(f"  ORNs {len(orn_kept)}, PNs {len(pn_kept)}, KCs {len(kc_kept)}")

all_pos = np.array([coord_map[r] for _, r in orn_kept + pn_kept + kc_kept], dtype=np.float64)
center = all_pos.mean(axis=0); extent = np.abs(all_pos - center).max()
scale = 5.0 / extent
def sp(rid):
    p = np.array(coord_map[rid], dtype=np.float64)
    return ((p - center) * scale).tolist()

print("[4/7] Loading activity...")
X_orn = np.load(ROOT / "outputs/X_orn.npy")
X_kc  = np.load(ROOT / "outputs/X_kc_raw.npy")
y     = np.load(ROOT / "outputs/y.npy")
W_ORN_PN = np.load(ROOT / "outputs/W_ORN_PN.npy")
W_PN_KC  = np.load(ROOT / "outputs/W_PN_KC.npy")

X_pn = np.maximum(X_orn @ W_ORN_PN, 0)
pn_indices = [i for i, _ in pn_kept]; kc_indices = [i for i, _ in kc_kept]
X_pn = X_pn[:, pn_indices]; X_kc = X_kc[:, kc_indices]

print("[5/7] Building edge lists...")
# ORN -> PN edges: scatter origins across the actual ORN somas
import random
random.seed(42)
orn_pn_edges = []
max_w = W_ORN_PN.max() if W_ORN_PN.max() > 0 else 1
glom_orn_indices = {}
for i, gi in enumerate(orn_glom_idx):
    glom_orn_indices.setdefault(gi, []).append(i)
for g in range(20):
    orn_list = glom_orn_indices.get(g, [])
    if not orn_list:
        continue
    for p in range(685):
        w = W_ORN_PN[g, p]
        if w > 0:
            orn_idx = random.choice(orn_list)
            orn_pn_edges.extend([orn_idx, p, float(w / max_w)])

# PN -> KC: keep top edges to avoid visual chaos
pn_kc_edges = []
# Only keep edges with weight above threshold (top ~15%)
flat = W_PN_KC[W_PN_KC > 0]
thresh = np.percentile(flat, 85)
max_w2 = W_PN_KC.max()
pn = 0
for p in range(685):
    for k in range(5177):
        w = W_PN_KC[p, k]
        if w > thresh:
            pn_kc_edges.extend([p, k, float(w / max_w2)])
            pn += 1
print(f"  ORN->PN edges: {len(orn_pn_edges)//3}")
print(f"  PN->KC edges (top 15%): {len(pn_kc_edges)//3}")

print("[6/7] Running models...")
predictions = {}
for mf in sorted((ROOT / "models").glob("*.joblib")):
    pipe = joblib.load(mf)
    predictions[mf.stem] = {
        "pred": pipe.predict(X_orn).tolist(),
        "proba": pipe.predict_proba(X_orn)[:, 1].tolist(),
    }

def norm_u8(arr):
    a = arr.astype(np.float32); amax = a.max(axis=1, keepdims=True); amax[amax == 0] = 1
    return np.round(a / amax * 255).astype(np.uint8)

print("[6.5/7] Loading dummy.csv (if present)...")
dummy_section = []
dummy_path = ROOT / "dummy.csv"
if dummy_path.exists():
    dummy_df = pd.read_csv(dummy_path)
    missing = [s for s in sensilla if s not in dummy_df.columns]
    if missing:
        print(f"  WARNING: dummy.csv missing columns: {missing}")
    else:
        alphas = dummy_df["alpha"].values if "alpha" in dummy_df.columns \
                 else np.linspace(0, 1, len(dummy_df))
        X_dummy_orn = dummy_df[sensilla].values.astype(np.float32)
        X_dummy_pn  = np.maximum(X_dummy_orn @ W_ORN_PN, 0)
        X_dummy_kc  = X_dummy_pn @ W_PN_KC
        dummy_preds = {}
        for mf in sorted((ROOT / "models").glob("*.joblib")):
            pipe = joblib.load(mf)
            dummy_preds[mf.stem] = {
                "pred":  pipe.predict(X_dummy_orn).tolist(),
                "proba": pipe.predict_proba(X_dummy_orn)[:, 1].tolist(),
            }
        orn_u8 = norm_u8(X_dummy_orn)
        pn_u8  = norm_u8(X_dummy_pn)
        kc_u8  = norm_u8(X_dummy_kc)
        for i in range(len(dummy_df)):
            dummy_section.append({
                "alpha": float(alphas[i]),
                "orn": orn_u8[i].tolist(),
                "pn":  pn_u8[i].tolist(),
                "kc":  kc_u8[i].tolist(),
                "predictions": {
                    n: {"pred": int(dummy_preds[n]["pred"][i]),
                        "proba": float(dummy_preds[n]["proba"][i])}
                    for n in dummy_preds
                },
            })
        print(f"  {len(dummy_section)} dummy samples added")
else:
    print("  dummy.csv not found — blend slider will be approximate")

print("[6.6/7] Loading extra scent categories...")
extra_scents = []
extra_path = ROOT / "viz" / "extra_scents.json"
if extra_path.exists():
    import json as _json
    with open(extra_path) as f:
        raw = _json.load(f)["scents"]
    for sc in raw:
        orn_vec = np.array(sc["vector"], dtype=np.float32)
        pn_vec = np.maximum(orn_vec @ W_ORN_PN, 0)
        kc_vec = pn_vec @ W_PN_KC
        extra_scents.append({
            "name": sc["name"],
            "category": sc["category"],
            "desc": sc["desc"],
            "orn": norm_u8(np.array([orn_vec]))[0].tolist(),
            "pn":  norm_u8(np.array([pn_vec]))[0].tolist(),
            "kc":  norm_u8(np.array([kc_vec]))[0].tolist(),
        })
    print(f"  {len(extra_scents)} extra scents added")
else:
    print("  extra_scents.json not found — run viz/extra_scents.py first")

print("[7/7] Writing JSON...")
data = {
    "meta": {"sensilla": sensilla,
             "glomeruli": [SENSILLUM_TO_GLOM[s] for s in sensilla],
             "n_samples": len(X_orn),
             "orn_total": len(orn_kept), "pn_total": len(pn_kept), "kc_total": len(kc_kept)},
    "neurons": {
        "orn": {"positions": [c for _, r in orn_kept for c in sp(r)],
                "glom_idx": [orn_glom_idx[i] for i, _ in orn_kept]},
        "pn":  {"positions": [c for _, r in pn_kept for c in sp(r)]},
        "kc":  {"positions": [c for _, r in kc_kept for c in sp(r)]},
    },
        "edges": {"orn_pn": orn_pn_edges, "pn_kc": pn_kc_edges},
        "dummy": dummy_section,
    "extra_scents": extra_scents,

    "samples": [
        {"id": i, "true_label": int(y[i]),
         "orn": norm_u8(X_orn)[i].tolist(),
         "pn":  norm_u8(X_pn)[i].tolist(),
         "kc":  norm_u8(X_kc)[i].tolist(),
         "predictions": {n: {"pred": int(predictions[n]["pred"][i]),
                             "proba": float(predictions[n]["proba"][i])}
                         for n in predictions}}
        for i in range(len(X_orn))
    ],
}
out = OUT_DIR / "brain_data.json"
with open(out, "w") as f: json.dump(data, f, separators=(",", ":"))
print(f"  {out} ({out.stat().st_size/1e6:.2f} MB)")
print("Done.")
