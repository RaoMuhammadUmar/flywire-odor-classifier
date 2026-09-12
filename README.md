# Olfactory Pipeline — FlyWire Connectome-Based Chemical Classification

A feasibility study integrating the FlyWire FAFB fruit fly connectome with
real Nowotny/de Bruyne ORN recordings to classify wine vs. industrial
volatile chemicals.

## What this project does

1. Extracts the olfactory circuit (ORN -> PN -> Kenyon Cell) from the real
   FlyWire connectome.
2. Loads real measured ORN responses (71 odorants x 20 sensilla) from the
   de Bruyne 2014 dataset.
3. Pushes the ORN responses through the connectome to produce Kenyon Cell
   representations.
4. Trains 4 classifiers on both raw ORN features and connectome-derived
   KC features.
5. Reports honest cross-validated accuracy with shuffled-label controls.

## Headline result

See predictions/test_holdout_predictions.csv after running the pipeline.
Raw ORN features match or exceed connectome-derived features on this
dataset -- an honest negative result.

## Setup

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

## Data (must be downloaded separately)

Raw datasets are not committed (too large). Download into data/ before
running the pipeline:

| Dataset | Source | Target folder |
|---|---|---|
| FlyWire FAFB v783 | https://codex.flywire.ai/api/download?dataset=fafb | data/flywire_raw/ |
| Nowotny/de Bruyne 2014 | https://data.csiro.au/collection/csiro:10689 | data/nowotny/ |
| DoOR 2.0 | http://neuro.uni-konstanz.de/DoOR/content/DoOR.php | data/door_raw/ |

Required FlyWire files: connections_princeton.csv, classification.csv,
consolidated_cell_types.csv.

## Workflow

    python train.py
    python predict.py data/test_holdout.csv
    python plot.py predictions/test_holdout_predictions.csv

    python generate_dummy.py --out dummy.csv
    python predict.py dummy.csv
    python plot.py predictions/dummy_predictions.csv

## Repository layout

    generate_dummy.py     synthetic ORN samples along wine->industrial gradient
    train.py              train 4 classifiers, save to models/
    predict.py            run inference on any CSV, save to predictions/
    plot.py               visualize any predictions CSV

    data/                 raw data (not committed -- see Data section)
    models/               trained model files (regeneratable)
    predictions/          prediction outputs (regeneratable)
    outputs/              intermediate pipeline artifacts
    pipeline_artifacts/   one-time connectome extraction scripts

## Citation

If you use this code, please cite the underlying datasets:

- Dorkenwald et al. (2024). Neuronal wiring diagram of an adult brain. Nature.
- de Bruyne, M., et al. (2014). CSIRO Data Access Portal, csiro:10689.
- Munch & Galizia (2016). DoOR 2.0, Sci Rep.
