"""
Step 1 — Extract real W_ORN_PN and W_PN_KC from the FlyWire FAFB connectome.

Inputs (place these first, see README):
    data/flywire/connections_filtered.csv
    data/flywire/cell_types.csv
    data/flywire/classification.csv

Outputs:
    outputs/W_ORN_PN.npy   shape (n_orn_types, n_PNs)
    outputs/W_PN_KC.npy    shape (n_PNs, n_KCs)
    outputs/orn_type_order.json   -- which of the 20 ORN types map to which column
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path

DATA = Path("data/flywire")
OUT = Path("outputs")
OUT.mkdir(exist_ok=True)

# The 20 ORN types must match the columns in the Nowotny dataset (data/nowotny/orn_responses.csv).
# Fill this in after inspecting that file's header row.
TARGET_ORN_TYPES = [
    # e.g. "Or42b", "Or47a", "Or59b", ...  -- EDIT to match your Nowotny column names
]


def load_connectome():
    conns = pd.read_csv(DATA / "connections_filtered.csv")
    cell_types = pd.read_csv(DATA / "cell_types.csv")
    classification = pd.read_csv(DATA / "classification.csv")
    return conns, cell_types, classification


def build_orn_pn_matrix(conns, cell_types, classification, orn_types):
    """
    Aggregate synapse counts from ORN cell-type -> PN cell-type into a
    weight matrix, restricted to the given ORN types (matching the
    Nowotny 20-receptor panel).
    """
    # Merge classification onto both pre and post synaptic partners
    cls_map = classification.set_index("root_id")["cell_class"].to_dict() \
        if "root_id" in classification.columns else {}

    orn_ids = cell_types[cell_types["cell_type"].isin(orn_types)]
    pn_ids = cell_types[cell_types["cell_class"].str.contains("PN", case=False, na=False)] \
        if "cell_class" in cell_types.columns else cell_types[cell_types["cell_type"].str.contains("PN")]

    orn_id_to_type = orn_ids.set_index("root_id")["cell_type"].to_dict()
    pn_id_to_type = pn_ids.set_index("root_id")["cell_type"].to_dict()

    sub = conns[
        conns["pre_root_id"].isin(orn_id_to_type) & conns["post_root_id"].isin(pn_id_to_type)
    ].copy()
    sub["orn_type"] = sub["pre_root_id"].map(orn_id_to_type)
    sub["pn_type"] = sub["post_root_id"].map(pn_id_to_type)

    weight_col = "syn_count" if "syn_count" in sub.columns else "weight"
    pivot = sub.pivot_table(
        index="orn_type", columns="pn_type", values=weight_col, aggfunc="sum", fill_value=0
    )
    pivot = pivot.reindex(orn_types).fillna(0)  # enforce fixed row order matching Nowotny columns
    return pivot


def build_pn_kc_matrix(conns, cell_types, classification, pn_types):
    kc_ids = cell_types[cell_types["cell_type"].str.contains("KC", case=False, na=False)]
    pn_ids = cell_types[cell_types["cell_type"].isin(pn_types)]

    kc_id_to_type = kc_ids.set_index("root_id")["cell_type"].to_dict()
    pn_id_to_type = pn_ids.set_index("root_id")["cell_type"].to_dict()

    sub = conns[
        conns["pre_root_id"].isin(pn_id_to_type) & conns["post_root_id"].isin(kc_id_to_type)
    ].copy()
    sub["pn_type"] = sub["pre_root_id"].map(pn_id_to_type)
    sub["kc_id"] = sub["post_root_id"]  # keep individual KCs, not aggregated by type

    weight_col = "syn_count" if "syn_count" in sub.columns else "weight"
    pivot = sub.pivot_table(
        index="pn_type", columns="kc_id", values=weight_col, aggfunc="sum", fill_value=0
    )
    return pivot


if __name__ == "__main__":
    if not TARGET_ORN_TYPES:
        raise SystemExit(
            "Edit TARGET_ORN_TYPES at the top of this file to match the 20 ORN "
            "column names in data/nowotny/orn_responses.csv before running."
        )

    conns, cell_types, classification = load_connectome()

    W_ORN_PN = build_orn_pn_matrix(conns, cell_types, classification, TARGET_ORN_TYPES)
    W_PN_KC = build_pn_kc_matrix(conns, cell_types, classification, list(W_ORN_PN.columns))

    np.save(OUT / "W_ORN_PN.npy", W_ORN_PN.values)
    np.save(OUT / "W_PN_KC.npy", W_PN_KC.values)
    with open(OUT / "orn_type_order.json", "w") as f:
        json.dump(list(W_ORN_PN.index), f)

    print(f"W_ORN_PN: {W_ORN_PN.shape}")
    print(f"W_PN_KC:  {W_PN_KC.shape}")
