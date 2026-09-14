"""Build extra scent samples from Marshall et al. 2010 (Chem Senses 35:613).

These are literature-derived ORN activation vectors for compounds associated
with drugs, explosives, and other hazardous agents. Values are approximations
based on published receptor responses (Table 2 of that paper), NOT raw
per-trial spike recordings.

20 sensilla order (must match outputs/sensilla_order.csv):
  ab1A ab1B ab1C ab1D ab2A ab2B ab3A ab3B ab4A ab4B
  ab5A ab5B ab7A ab7B ab8A ab8B pb1A pb1B pb3A pb3B
"""
import json
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "viz" / "extra_scents.json"

# Sensillum index lookup
SENSILLA = ["ab1A","ab1B","ab1C","ab1D","ab2A","ab2B","ab3A","ab3B",
            "ab4A","ab4B","ab5A","ab5B","ab7A","ab7B","ab8A","ab8B",
            "pb1A","pb1B","pb3A","pb3B"]
IDX = {s: i for i, s in enumerate(SENSILLA)}

def vec(**kwargs):
    """Build a 20-dim vector from {sensillum: value} pairs. Values in Hz."""
    v = [0.0] * 20
    for s, val in kwargs.items():
        v[IDX[s]] = float(val)
    return v

# ---------------------------------------------------------------
# Literature-derived vectors (Marshall et al. 2010, Table 2)
# Positive responses were defined as >50 spikes/s.
# Values here are representative magnitudes, not exact measurements.
# ---------------------------------------------------------------
SCENTS = [
    # ---- EXPLOSIVES ----
    {"name": "PETN (explosive)", "category": "explosive",
     "desc": "Pentaerythritol tetranitrate. Or7a / ab4A responds.",
     "vector": vec(ab4A=180)},

    {"name": "2-Ethyl-1-hexanol (explosive marker)", "category": "explosive",
     "desc": "Dominant VOC in polymer-based explosives. Or43b / ab8A responds.",
     "vector": vec(ab8A=210)},

    {"name": "Nitromethane (explosive precursor)", "category": "explosive",
     "desc": "Used in explosive manufacture. Or42a / pb1A responds.",
     "vector": vec(pb1A=160)},

    {"name": "2,4-Dinitrotoluene (TNT marker)", "category": "explosive",
     "desc": "Degradation product of TNT. Detected by dogs. Drosophila receptor not confirmed in Marshall 2010, extrapolated.",
     "vector": vec(ab4A=80, ab8A=110)},

    {"name": "Ammonium nitrate (explosive)", "category": "explosive",
     "desc": "Common industrial explosive. Some response via ammonia-sensitive ac1 neurons, extrapolated to ab1C.",
     "vector": vec(ab1C=140)},

    # ---- DRUG PRECURSORS ----
    {"name": "Benzaldehyde (meth precursor)", "category": "drug",
     "desc": "Part of one methamphetamine synthesis route. Excites 4+ ORN classes.",
     "vector": vec(ab1D=90, ab3A=120, ab4A=150, ab5A=70)},

    {"name": "Phenyl-2-propanone (P2P, meth precursor)", "category": "drug",
     "desc": "Key methamphetamine synthesis precursor. Marshall 2010 tested, moderate response.",
     "vector": vec(ab4A=100, ab8A=80)},

    {"name": "Sassafras oil (MDMA precursor)", "category": "drug",
     "desc": "Natural product. Excites pb2A (Or59c homolog), mapped to pb3A.",
     "vector": vec(pb3A=130)},

    {"name": "Diethyl phosphite (nerve agent precursor)", "category": "drug",
     "desc": "Organophosphate precursor. Or43b / ab8A responds.",
     "vector": vec(ab8A=170)},

    # ---- NERVE / TOXIC AGENTS ----
    {"name": "Acetone (industrial solvent)", "category": "toxic",
     "desc": "Common solvent, also occurs naturally. Detected by multiple ORNs.",
     "vector": vec(ab2A=70, ab3A=90, ab7A=60)},

    {"name": "Methyl ethyl ketone (MEK)", "category": "toxic",
     "desc": "Stimulates 3 ORN classes per Marshall 2010.",
     "vector": vec(ab2A=110, ab3A=130, ab7A=90)},

    {"name": "Diethanolamine (blistering agent precursor)", "category": "toxic",
     "desc": "Nitrogen mustard precursor / hydrolysis product.",
     "vector": vec(ab5A=95, ab7B=75)},

    # ---- RADIOACTIVE (extrapolated) ----
    {"name": "Radon decay VOCs", "category": "radioactive",
     "desc": "Radon is odorless. Flies cannot detect radiation directly. This vector is SPECULATIVE — it represents hypothetical volatile byproducts of radioactive decay. No published ORN data exists.",
     "vector": vec(ab1A=60, ab3A=50)},

    {"name": "Uranium ore outgassing", "category": "radioactive",
     "desc": "Uranium ore releases radon and other gases. SPECULATIVE vector — no Drosophila ORN data. Included for exploratory visualization only.",
     "vector": vec(ab2A=45, ab5A=55, pb1A=40)},

    {"name": "Tritium (H-3) contaminated air", "category": "radioactive",
     "desc": "Tritium emits beta particles. No olfactory signal. This vector is a placeholder — included to demonstrate that flies have no receptor pathway for radiation itself.",
     "vector": vec()},
]

# Save
data = {"scents": SCENTS}
with open(OUT, "w") as f:
    json.dump(data, f, indent=2)
print(f"Wrote {OUT} with {len(SCENTS)} scents")
for s in SCENTS:
    nonzero = sum(1 for x in s["vector"] if x > 0)
    print(f"  [{s['category']:11s}] {s['name'][:40]:40s} ({nonzero} active sensilla)")
