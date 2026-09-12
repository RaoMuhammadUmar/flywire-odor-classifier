import pandas as pd
import numpy as np
import os

os.makedirs("outputs", exist_ok=True)

# Sensillum -> glomerulus mapping (from DoOR.mappings.RData, verified)
SENSILLUM_TO_GLOM = {
    'ab1A':'DM1','ab1B':'VA2','ab1C':'V','ab1D':'DL1',
    'ab2A':'DM4','ab2B':'DM5','ab3A':'DM2','ab3B':'VM5d',
    'ab4A':'DL5','ab4B':'DA2','ab5A':'VA6','ab5B':'DM3',
    'ab7A':'VM5v','ab7B':'VC4','ab8A':'VM2','ab8B':'VM3',
    'pb1A':'VM7d','pb1B':'VC2','pb3A':'VM7v','pb3B':'VA4',
}
SENSILLA = list(SENSILLUM_TO_GLOM.keys())  # fixed order = 20 features

print("Step 1: Loading cell types...")
ct = pd.read_csv("data/flywire_raw/consolidated_cell_types.csv")

print("Step 2: Getting ORN root_ids per glomerulus...")
glom_to_orns = {}
for sens, glom in SENSILLUM_TO_GLOM.items():
    ids = ct[ct["primary_type"] == f"ORN_{glom}"]["root_id"].tolist()
    glom_to_orns[glom] = ids
    print(f"  {sens} -> {glom}: {len(ids)} ORNs")

print("\nStep 3: Loading classification...")
cl = pd.read_csv("data/flywire_raw/classification.csv")
alpn_ids = cl[cl["class"] == "ALPN"]["root_id"].tolist()
kc_ids   = cl[cl["class"] == "Kenyon_Cell"]["root_id"].tolist()
print(f"  ALPNs: {len(alpn_ids)}")
print(f"  KCs:   {len(kc_ids)}")

print("\nStep 4: Loading connections (261 MB, may take 30s)...")
conn = pd.read_csv("data/flywire_raw/connections_princeton.csv")
print(f"  Total connections: {len(conn):,}")

# Build lookup tables
glom_to_idx = {g: i for i, g in enumerate([SENSILLUM_TO_GLOM[s] for s in SENSILLA])}
alpn_to_idx = {r: i for i, r in enumerate(alpn_ids)}
kc_to_idx   = {r: i for i, r in enumerate(kc_ids)}
orn_id_to_glom = {}
for glom, ids in glom_to_orns.items():
    for rid in ids:
        orn_id_to_glom[rid] = glom

all_orn_ids = set(orn_id_to_glom.keys())
alpn_set = set(alpn_ids)
kc_set = set(kc_ids)

print("\nStep 5: Building W_ORN_PN...")
W_ORN_PN = np.zeros((20, len(alpn_ids)), dtype=np.float32)
count = 0
for _, row in conn.iterrows():
    pre, post = row["pre_root_id"], row["post_root_id"]
    if pre in all_orn_ids and post in alpn_set:
        glom = orn_id_to_glom[pre]
        W_ORN_PN[glom_to_idx[glom], alpn_to_idx[post]] += row["syn_count"]
        count += 1
print(f"  ORN->PN edges: {count:,}")
print(f"  W_ORN_PN shape: {W_ORN_PN.shape}, nonzero: {(W_ORN_PN>0).sum():,}")

print("\nStep 6: Building W_PN_KC...")
W_PN_KC = np.zeros((len(alpn_ids), len(kc_ids)), dtype=np.float32)
count = 0
for _, row in conn.iterrows():
    pre, post = row["pre_root_id"], row["post_root_id"]
    if pre in alpn_set and post in kc_set:
        W_PN_KC[alpn_to_idx[pre], kc_to_idx[post]] += row["syn_count"]
        count += 1
print(f"  PN->KC edges: {count:,}")
print(f"  W_PN_KC shape: {W_PN_KC.shape}, nonzero: {(W_PN_KC>0).sum():,}")

# Save
np.save("outputs/W_ORN_PN.npy", W_ORN_PN)
np.save("outputs/W_PN_KC.npy", W_PN_KC)
pd.Series(SENSILLA).to_csv("outputs/sensilla_order.csv", index=False, header=["sensillum"])
pd.Series([SENSILLUM_TO_GLOM[s] for s in SENSILLA]).to_csv(
    "outputs/glomerulus_order.csv", index=False, header=["glomerulus"])

print("\nSaved to outputs/")
print("  W_ORN_PN.npy, W_PN_KC.npy, sensilla_order.csv, glomerulus_order.csv")

# Sanity check
print("\nSanity check — W_ORN_PN row sums (total synapses per ORN glomerulus):")
for i, s in enumerate(SENSILLA):
    print(f"  {s} ({SENSILLUM_TO_GLOM[s]}): {W_ORN_PN[i].sum():.0f} synapses to {int((W_ORN_PN[i]>0).sum())} PNs")

print("\nSanity check — W_PN_KC row sums (first 5 PNs):")
for i in range(5):
    print(f"  PN {i}: {W_PN_KC[i].sum():.0f} synapses to {int((W_PN_KC[i]>0).sum())} KCs")
