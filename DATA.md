# DATA.md — What the data actually is

This document explains every dataset, every column, and every number that
flows through the pipeline. If you understand this, you understand the project.

---

## 1. Three datasets, three roles

| Dataset | Physical meaning | Role in pipeline |
|---|---|---|
| **FlyWire FAFB v783** | A wiring diagram of one fruit fly's brain | Provides the circuit structure (who connects to whom) |
| **Nowotny / de Bruyne 2014** | Measured neural responses of fly nose cells to real chemicals | Provides the input signal (what the fly smells) |
| **DoOR 2.0** | A lookup table bridging receptors to brain regions | Provides the mapping between the two above |

Think of it as: FlyWire gives the wires, Nowotny gives the signal, DoOR tells us which wire plugs into which signal.

---

## 2. FlyWire FAFB — the connectome

**FAFB** = Female Adult Fly Brain. **v783** = snapshot number. This is a
complete electron-microscopy reconstruction of an adult female
*Drosophila melanogaster* brain. Published in *Nature* (Dorkenwald et al., 2024).

### Facts about the raw data

- **139,255 cells** (individual neurons)
- **50,666,648 synapses** (physical connection sites between neurons)
- **1,168,054 annotations** (labels added by human + machine proofreading)
- Reconstruction method: serial-section electron microscopy, then automated segmentation, then human proofreading

### The three files we use

**`consolidated_cell_types.csv`** (901 KB, 138,327 rows) — maps each neuron ID to its biological cell type.

| Column | Meaning | Example |
|---|---|---|
| `root_id` | Unique 64-bit ID for that neuron | `720575940599457990` |
| `primary_type` | Best-guess cell type label | `ORN_DM4`, `KCg-m`, `L1` |
| `additional_type(s)` | Extra labels (usually empty) | `ORN_DM4_ChAT` |

**`classification.csv`** (9.6 MB, 139,255 rows) — hierarchical taxonomy, same neurons organized into a tree.

| Column | Meaning | Example |
|---|---|---|
| `root_id` | Same ID as above | `720575940599457990` |
| `flow` | Signal direction | `afferent`, `efferent`, `intrinsic` |
| `super_class` | Broadest category | `optic`, `central`, `sensory` |
| `class` | Mid-level category | `olfactory`, `ALPN`, `Kenyon_Cell` |
| `sub_class` | Finest category | `uniglomerular`, `KCg`, `pheromone` |
| `hemilineage` | Developmental lineage | mostly empty |
| `side` | Left / right hemisphere | `left`, `right` |
| `nerve` | Which nerve the axon runs in | `AN` (antennal nerve), `MxLbN` |

**`connections_princeton.csv`** (261 MB, 5,342,446 rows) — the actual wiring.

| Column | Meaning | Example |
|---|---|---|
| `pre_root_id` | The neuron sending the signal | `720575940625363947` |
| `post_root_id` | The neuron receiving the signal | `720575940623224444` |
| `neuropil` | Brain region where the synapse is | `AL` (antennal lobe), `MB_CA` (mushroom body calyx) |
| `syn_count` | Number of synapses at this connection | `12` |
| `nt_type` | Predicted neurotransmitter | `ACH`, `GABA`, `GLUT` |

**Important:** connections with fewer than 5 synapses total are already removed (this is the "filtered" version). Autapses are excluded. One neuron pair can appear on multiple rows if they synapse in multiple brain regions — we sum across rows.

---

## 3. Nowotny / de Bruyne 2014 — the odor responses

Published by Marien de Bruyne and colleagues, hosted on CSIRO. This is
**measured electrophysiology**: a glass electrode inserted into a single
sensillum on a live fly's antenna, exposed to a chemical, and the spike rate
of the neurons inside recorded.

### What's a "sensillum"?

A sensillum is a tiny hair-like structure on the fly's antenna. Inside each
sensillum are 1-4 olfactory receptor neurons (ORNs). Each ORN expresses a
specific odorant receptor gene. So "the `ab2A` neuron" means "the neuron
housed in the `ab2` type sensillum, position A".

The 20 sensilla in the Nowotny dataset:

| Sensillum | Receptor gene | Glomerulus (brain target) |
|---|---|---|
| ab1A | Or42b | DM1 |
| ab1B | Or92a | VA2 |
| ab1C | Gr21a/Gr63a | V |
| ab1D | Or10a | DL1 |
| ab2A | Or59b | DM4 |
| ab2B | Or85a + Or33b | DM5 |
| ab3A | Or22a | DM2 |
| ab3B | Or85b | VM5d |
| ab4A | Or7a | DL5 |
| ab4B | Or56a + Or33a | DA2 |
| ab5A | Or82a | VA6 |
| ab5B | Or47a + Or33b | DM3 |
| ab7A | Or98a | VM5v |
| ab7B | Or67c | VC4 |
| ab8A | Or43b | VM2 |
| ab8B | Or9a | VM3 |
| pb1A | Or42a | VM7d |
| pb1B | Or71a | VC2 |
| pb3A | Or59c | VM7v |
| pb3B | Or85d | VA4 |

**Glomerulus** = the ball of neuropil in the antennal lobe where all ORNs
expressing the same receptor converge. Each ORN type projects to exactly one
glomerulus. In FlyWire, these are labeled `ORN_DM4`, `ORN_VA2`, etc.

### The CSV format

Both `deBruyne_industrialset_*.csv` and `deBruyne_wineset_*.csv` are in
**long format** — one row per (odorant, neuron) pair.

| Column | Meaning | Example |
|---|---|---|
| `odorant` | Chemical abbreviation or name | `NH3`, `2Ac`, `i5Ac` |
| `neuron` | Sensillum code | `pb1A`, `ab2B` |
| `n` | Number of flies tested | `6`, `12` |
| `mean` | Average spike-rate change (Hz) | `-2.0`, `163.08` |
| `std` | Standard deviation across flies | `6.45`, `31.36` |

**Reading `mean`:**
- Positive = the chemical **excited** this neuron (fired more than baseline)
- Negative = the chemical **inhibited** this neuron (fired less than baseline)
- Zero = no response
- Units are Hz (spikes per second)

### What the two files contain

- **Wine set:** 36 wine-related aroma compounds
- **Industrial set:** 35 industrial/hazardous volatiles
- **Total:** 71 unique odorants x 20 sensilla = 1,420 measured values

**This is where "71 x 20" comes from.** 71 chemicals, 20 ORN types.

### Class labels

We treat this as a **binary classification**:
- Class 0 = wine aroma (neutral / food-relevant)
- Class 1 = industrial volatile (hazardous)

**We are NOT classifying drugs.** The chemicals are industrial solvents and
volatile indicators — not illicit substances. The "hazard" class is a proxy
for "could this chemical be detected by a fly's olfactory system?"


---

## 4. DoOR 2.0 — the bridge

**DoOR** = Database of Odorant Responses. Published by Münch & Galizia (2016).
It's a **meta-database**: researchers compiled every published measurement of
*Drosophila* olfactory receptor responses into one giant consensus matrix.

### Why we need it

The Nowotny data uses sensillum codes (`ab2A`). FlyWire uses glomerulus names
(`ORN_DM4`). These are different naming systems. DoOR gives us the
**translation table**.

### The file we use: `DoOR.mappings.RData`

| Column | Meaning | Example |
|---|---|---|
| `receptor` | Receptor gene name | `Or59b` |
| `sensillum` | Sensillum type | `ab2` |
| `OSN` | Specific olfactory sensory neuron | `ab2A` |
| `glomerulus` | Brain target region | `DM4` |
| `code` | Glomerulus shorthand | `DM4` |
| `code.OSN` | Sensillum code (matches Nowotny) | `ab2A` |
| `VFB_id` | Virtual Fly Brain ontology ID | `FBbt_00067046` |

**This single table is what makes the entire project possible.** It lets us
take the 20 Nowotny sensilla, look up their glomeruli, and find the matching
`ORN_DM4`, `ORN_VA2`, etc. neurons in FlyWire.

### The full response matrix

DoOR also ships `response.matrix_non.normalized.RData` — a 693 x 78 matrix of
receptor responses to odorants. **We loaded it but did not end up using it**
because the Nowotny data is more directly relevant (real measured Hz values
for our specific 20 sensilla). DoOR's matrix is a fallback if you ever want
to expand to more chemicals.

---

## 5. The olfactory circuit — ORN -> PN -> KC

This is the biological pathway that the project is testing.

    Fly antenna
         |
    [ 20 ORN types ]           <- 20 features (Nowotny input)
         |  synapses in antennal lobe
         v
    [ ~685 projection neurons ] <- intermediate layer
         |  synapses in mushroom body
         v
    [ ~5,177 Kenyon cells ]     <- sparse, high-dim representation
         |
         v
    downstream learning

- **ORNs** = olfactory receptor neurons. Each sensillum contains 1-4. They
  respond to chemicals. This is where our input lives.
- **PNs** = projection neurons. They relay the ORN signal from the antennal
  lobe to the mushroom body. Some are uniglomerular (connect to one
  glomerulus), others are multiglomerular (connect to several).
- **KCs** = Kenyon cells. The mushroom body's principal neurons. There are
  ~5,177 in the FlyWire dataset. Each KC receives input from only ~4-6 PNs.
  This "sparse expansion coding" is thought to make different odors more
  distinguishable downstream.

### What the pipeline does

1. Extract the ORN->PN and PN->KC weight matrices from FlyWire.
2. Multiply the Nowotny ORN responses by the ORN->PN matrix -> PN activity.
3. Multiply the PN activity by the PN->KC matrix -> KC activity.
4. The KC activity is our connectome-derived feature set.
5. Train classifiers on it and compare to raw ORN features.

**The question we ask:** does passing signals through the mushroom body
circuit actually make chemicals easier to tell apart than they already were
at the ORN level?


---

## 6. Why only 71 samples?

We use every chemical in the Nowotny dataset. There are 71 of them. That's
the entire published measurement set. We cannot manufacture more — the data
is what it is.

**Implications for machine learning:**
- 71 samples is **tiny**. Deep learning would just memorize.
- We use **cross-validation** (5-fold) instead of a single train/test split for the headline result.
- We use **regularized, low-capacity models** (LogReg, SVM with RBF kernel).
- We report **mean +/- std across folds**, not a single accuracy number.
- We run a **shuffled-label control** to prove the model isn't cheating.
- We save a **20% held-out set** and never touch it during training.

**This is honest ML on small data.** It's also why we get ~83% accuracy
rather than 99% — the models are constrained by the actual signal-to-noise
in the measurements.

---

## 7. Known caveats

Stated plainly, for the report:

1. **Sex mismatch:** FlyWire FAFB is from a female fly. The Nowotny recordings
   are from male flies. We assume the olfactory circuit is broadly similar,
   but this is an approximation.
2. **Species-level anatomy vs. individual physiology:** The connectome is one
   specific fly. The odor responses are averages across multiple flies.
   Combining them is a modeling choice, not a direct measurement.
3. **Synapse counts != functional strength.** We use raw synapse counts as
   edge weights. Real synaptic efficacy depends on receptor density, release
   probability, etc. This is a simplification.
4. **No inhibition in the circuit.** We use ReLU (rectification), which models
   only excitatory transmission. Real antennal lobe circuits have strong
   lateral inhibition via local interneurons, which we excluded.
5. **Chemicals are proxies.** The "industrial" class is a category from the
   original paper, not a curated list of drugs or explosives.
6. **Small n.** 71 samples is not enough to make strong generalization claims.
   All results are exploratory.
7. **The connectome does not improve classification here.** Our honest result:
   raw ORN features (83%) match or beat connectome-derived features (best
   82%). This is a negative finding and that's fine — negative findings are
   findings.

---

## 8. Summary table

| Question | Answer |
|---|---|
| What is the connectome? | Physical wiring diagram of a fly brain |
| What is a sensillum? | Hair-like structure housing 1-4 odor neurons |
| What is a glomerulus? | Ball of neuropil where same-receptor ORNs converge |
| What are the 20 features? | Sensillum types (`ab1A` ... `pb3B`) |
| What are the 71 samples? | Chemicals from Nowotny dataset |
| What are the labels? | Wine vs. industrial (from source paper) |
| Why 5,177 KCs? | FlyWire has ~5,177 annotated Kenyon cells |
| Why is accuracy ~83%? | Real noisy data, small n, honest CV |
| Does the connectome help? | No, on this data — and we show why |

---

## 9. Further reading

- Dorkenwald et al. (2024). *Neuronal wiring diagram of an adult brain.* Nature. — FlyWire paper
- Schlegel et al. (2024). *Whole-brain annotation and multi-connectome cell typing.* Nature. — cell types
- de Bruyne, M., et al. (2014). CSIRO Data Access Portal, csiro:10689. — odor responses
- Münch & Galizia (2016). *DoOR 2.0.* Scientific Reports. — receptor response database
- Couto, A., et al. (2005). *Molecular, anatomical, and functional organization of the Drosophila olfactory system.* Current Biology. — sensillum-to-receptor mapping
