#!/bin/bash
# Teacher demo — runs the full pipeline from scratch in ~30 seconds.
set -e
cd "$(dirname "$0")"

echo "=== Activating venv ==="
source .venv/bin/activate

echo
echo "=== 1. TRAIN: 4 classifiers, 5-fold CV on real Nowotny data ==="
python train.py

echo
echo "=== 2. PREDICT: on the 20% held-out test set (never seen) ==="
python predict.py data/test_holdout.csv

echo
echo "=== 3. GENERATE: 30 synthetic samples along wine->industrial gradient ==="
python generate_dummy.py --out dummy.csv

echo
echo "=== 4. PREDICT: on synthetic samples ==="
python predict.py dummy.csv

echo
echo "=== Done. Predictions in predictions/ ==="
echo "To show plots, run:  python plot.py predictions/test_holdout_predictions.csv"
