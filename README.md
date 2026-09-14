# Olfactory Pipeline — FlyWire Connectome-Based Chemical Classification

**🔗 [Try the live 3D brain viewer →](https://raomuhammadumar.github.io/flywire-odor-classifier/viz/)**

[![3D brain viewer demo](docs/images/demo.gif)](https://raomuhammadumar.github.io/flywire-odor-classifier/viz/)

*Click the animation to open the live demo. Real FlyWire neuron positions, real connectome weights, live predictions from 4 trained classifiers.*

---

## 🧠 Live 3D brain viewer

An interactive visualization of a fruit fly's olfactory circuit, running entirely in the browser. Every neuron is plotted at its **actual 3D position** from the FlyWire FAFB reconstruction (139,255 neurons total). Circuit weights come from the **real connectome** — synapse counts from electron microscopy.

**What you can do:**

- **Real odorant mode** — pick any of the 71 chemicals from the de Bruyne 2014 electrophysiology dataset and watch the circuit respond
- **Gradient slider** — smoothly interpolate between a wine prototype and an industrial prototype, watching the brain morph
- **Hazard mode** — select from explosives, drug precursors, toxic industrial chemicals, and radioactive compounds. Each fires a distinct ORN→PN→KC pattern through the real circuit
- **Auto-play** — press the play button (or spacebar) to cycle through all samples
- **Four analysis tabs** — Brain (live predictions), Perception (what the fly smells), State (neural state classifier), Analytics (model performance)

**The 3D scene:**

| Element | Description |
|---|---|
| **Cyan points** | 915 olfactory receptor neurons (ORNs), clustered in the antennal lobe |
| **Blue points** | 685 projection neurons (PNs), relaying to the mushroom body |
| **Amber points** | 5,177 Kenyon cells (KCs), the mushroom body's sparse coding layer |
| **Bright lines** | Actual synaptic connections from the connectome, colored by signal strength |

---

## What this project does

1. Extracts the olfactory circuit (ORN → PN → Kenyon Cell) from the real FlyWire connectome.
2. Loads real measured ORN responses (71 odorants × 20 sensilla) from the de Bruyne 2014 dataset.
3. Pushes ORN responses through the connectome to produce Kenyon Cell representations.
4. Trains 4 classifiers on both raw ORN features and connectome-derived KC features.
5. Reports honest cross-validated accuracy with shuffled-label controls.
6. Visualizes the entire pipeline in an interactive 3D viewer.

---

## Headline result

We ran two evaluations. Both point the same direction.

### 1. Connectome comparison (5-fold CV on all 71 samples)

| Feature set | Best model | Accuracy |
|---|---|---|
| Raw ORN (20-D) | SVM | **83.0%** |
| Connectome-derived KC (5,177-D) | RF | 81.9% |
| Shuffled-label control | — | ~50% (chance) |

The connectome did **not** improve classification. The signal is already present at the receptor level, and the mushroom body's sparse expansion coding did not amplify it on this dataset. **An honest negative result.**

### 2. Held-out test (single 80/20 split, 15 samples never seen in training)

| Model | Accuracy |
|---|---|
| LogReg | 93.3% (14/15) |
| SVM | 93.3% (14/15) |
| RF | 86.7% (13/15) |
| MLP | 60.0% (9/15) |

See **DATA.md** for what every dataset, column, and number means.

---

## Results figures

### Model accuracy on the held-out test set

![Model accuracy](docs/images/01-accuracy-bar.png)

### Behavior along the wine → industrial gradient

![P(industrial) per model](docs/images/02-p-industrial-curves.png)

### Confusion matrices (held-out test set)

| Random Forest | SVM | MLP | LogReg |
|---|---|---|---|
| ![RF](docs/images/06-confusion-rf.png) | ![SVM](docs/images/07-confusion-svm.png) | ![MLP](docs/images/05-confusion-mlp.png) | ![LogReg](docs/images/04-confusion-logreg.png) |

---

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

Data (must be downloaded separately)
Raw datasets are not committed (too large). Download into data/ before running the pipeline.

Dataset	Source	Target folder
FlyWire FAFB v783	https://codex.flywire.ai/api/download?dataset=fafb	data/flywire_raw/
Nowotny/de Bruyne 2014	https://data.csiro.au/collection/csiro:10689	data/nowotny/
DoOR 2.0	http://neuro.uni-konstanz.de/DoOR/content/DoOR.php	data/door_raw/
Required FlyWire files: connections_princeton.csv, classification.csv, consolidated_cell_types.csv, coordinates.csv.

Data (must be downloaded separately)
Raw datasets are not committed (too large). Download into data/ before running the pipeline.

Dataset	Source	Target folder
FlyWire FAFB v783	https://codex.flywire.ai/api/download?dataset=fafb	data/flywire_raw/
Nowotny/de Bruyne 2014	https://data.csiro.au/collection/csiro:10689	data/nowotny/
DoOR 2.0	http://neuro.uni-konstanz.de/DoOR/content/DoOR.php	data/door_raw/
Required FlyWire files: connections_princeton.csv, classification.csv, consolidated_cell_types.csv, coordinates.csv.
