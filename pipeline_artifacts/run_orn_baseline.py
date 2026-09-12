"""
WORKING PROTOTYPE — ORN-level classification of wine vs. industrial/hazardous
volatiles using REAL measured Drosophila ORN spike-rate data (de Bruyne et al.
2014 / Marshall, Warr & de Bruyne 2010).

This is the part of the pipeline that is fully real and validated right now.
The connectome (ORN->PN->KC) expansion is NOT included here -- see README.md
for why, and receptor_map.py for the mapping table that's ready once the
missing FlyWire "Cell Types" file is supplied.

Run:
    python run_orn_baseline.py
Outputs land in outputs/.
"""
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.model_selection import StratifiedKFold, cross_val_score, cross_val_predict
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import confusion_matrix

DATA = Path("data/nowotny")
OUT = Path("outputs")
OUT.mkdir(exist_ok=True)

MODELS = {
    "LogisticRegression": lambda: make_pipeline(StandardScaler(), LogisticRegression(max_iter=5000)),
    "SVM_RBF": lambda: make_pipeline(StandardScaler(), SVC(kernel="rbf")),
    "RandomForest": lambda: RandomForestClassifier(n_estimators=300, random_state=0),
    "MLP": lambda: make_pipeline(
        StandardScaler(), MLPClassifier(hidden_layer_sizes=(32,), alpha=1e-2, max_iter=3000, random_state=0)
    ),
}


def build_X_orn():
    """Real (71, 20) ORN response matrix: 36 wine (label 0) + 35 industrial/hazardous (label 1) odorants."""
    ind = pd.read_csv(DATA / "deBruyne_industrialset_OlfCode_Drosophila_2014.csv", encoding="latin1")
    wine = pd.read_csv(DATA / "deBruyne_wineset_OlfCode_Drosophila_2014.csv", encoding="latin1")
    ind["odorant"] = ind["odorant"].str.strip()
    wine["odorant"] = wine["odorant"].str.strip()
    ind_p = ind.pivot(index="odorant", columns="neuron", values="mean")
    wine_p = wine.pivot(index="odorant", columns="neuron", values="mean")
    combined = pd.concat([wine_p.assign(label=0), ind_p.assign(label=1)])
    return combined


if __name__ == "__main__":
    df = build_X_orn()
    df.to_csv(OUT / "X_orn_real_71x20.csv")

    y = df["label"].values
    X = df.drop(columns="label").values
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)

    # Main models
    rows = []
    for name, make_model in MODELS.items():
        scores = cross_val_score(make_model(), X, y, cv=cv, scoring="accuracy")
        rows.append({"model": name, "mean_acc": scores.mean(), "std_acc": scores.std()})
        print(f"{name}: {scores.mean():.3f} +/- {scores.std():.3f}")
    pd.DataFrame(rows).to_csv(OUT / "results_table_ORN_only.csv", index=False)

    # Control B: shuffled labels -> should collapse to chance (0.5)
    rng = np.random.default_rng(0)
    shuffled_accs = []
    for _ in range(20):
        y_shuffled = rng.permutation(y)
        s = cross_val_score(MODELS["SVM_RBF"](), X, y_shuffled, cv=cv, scoring="accuracy")
        shuffled_accs.append(s.mean())
    pd.DataFrame([{
        "shuffled_mean_acc": np.mean(shuffled_accs),
        "shuffled_std_acc": np.std(shuffled_accs),
        "chance": 0.5,
    }]).to_csv(OUT / "control_b_shuffled.csv", index=False)
    print(f"Control B (shuffled labels): {np.mean(shuffled_accs):.3f} +/- {np.std(shuffled_accs):.3f}")

    # Control C: receptor ablation
    ablation_rows = []
    for k in (5, 10, 15, 20):
        accs_k = []
        for _ in range(10):
            idx = rng.choice(20, size=k, replace=False)
            s = cross_val_score(RandomForestClassifier(n_estimators=300, random_state=0),
                                 X[:, idx], y, cv=cv, scoring="accuracy")
            accs_k.append(s.mean())
        ablation_rows.append({"n_receptors": k, "mean_acc": np.mean(accs_k), "std_acc": np.std(accs_k)})
        print(f"Ablation k={k}: {np.mean(accs_k):.3f}")
    ablation_df = pd.DataFrame(ablation_rows)
    ablation_df.to_csv(OUT / "control_c_ablation.csv", index=False)

    plt.figure(figsize=(6, 4))
    plt.errorbar(ablation_df["n_receptors"], ablation_df["mean_acc"], yerr=ablation_df["std_acc"], marker="o")
    plt.xlabel("Number of ORN types used")
    plt.ylabel("CV accuracy")
    plt.title("Receptor ablation (real data)")
    plt.tight_layout()
    plt.savefig(OUT / "ablation_curve.png", dpi=150)

    preds = cross_val_predict(RandomForestClassifier(n_estimators=300, random_state=0), X, y, cv=cv)
    cm = confusion_matrix(y, preds)
    plt.figure(figsize=(4, 4))
    plt.imshow(cm, cmap="Blues")
    plt.colorbar()
    plt.xticks([0, 1], ["wine(0)", "industrial(1)"])
    plt.yticks([0, 1], ["wine(0)", "industrial(1)"])
    for i in range(2):
        for j in range(2):
            plt.text(j, i, cm[i, j], ha="center", va="center")
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.title("Confusion matrix (RandomForest, CV)")
    plt.tight_layout()
    plt.savefig(OUT / "confusion_matrix.png", dpi=150)

    metadata = {
        "n_samples": int(len(y)),
        "n_wine": int((y == 0).sum()),
        "n_industrial": int((y == 1).sum()),
        "status": (
            "ORN-level baseline (Control A) is fully real and validated. "
            "Connectome KC expansion NOT included -- blocked on missing FlyWire "
            "'Cell Types' file. DoOR expansion NOT included -- .RData format "
            "unreadable without R/pyreadr in this environment."
        ),
        "caveats": [
            "Labels are binary (wine/neutral vs industrial/hazardous) as published, "
            "not the 4-way drug/explosive/toxin split -- that needs the source "
            "paper's Table 2 compound key.",
            "FAFB connectome (once added) is female; this ORN data is from male flies.",
            "n=71 total odorants; all accuracies are 5-fold CV, not a single split.",
        ],
    }
    with open(OUT / "run_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print("\nDone. See outputs/ for results table, controls, plots, and metadata.")
