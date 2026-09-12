# Workflow — one-shot commands

Copy-paste block for running the full pipeline from a fresh terminal.

See README.md for context; see DATA.md for what the data means.

---

# ============================================================
# 0. Enter project + set up venv
# ============================================================
cd ~/Desktop/olfactory_pipeline
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# ============================================================
# 1. Clean up any leftover artifacts
# ============================================================
rm -f dummy.py plot_results.py predictions/test_predictions.csv
rmdir data/dummy 2>/dev/null

# ============================================================
# 2. Train (writes models/*.joblib, data/train.csv, data/test_holdout.csv)
# ============================================================
python train.py

# ============================================================
# 3. Predict on held-out test set (20% never seen during training)
# ============================================================
python predict.py data/test_holdout.csv

# ============================================================
# 4. Plot held-out test results (close each window to advance)
# ============================================================
python plot.py predictions/test_holdout_predictions.csv

# ============================================================
# 5. Generate dummy samples along wine → industrial gradient
# ============================================================
python generate_dummy.py --out dummy.csv

# ============================================================
# 6. Predict on dummy data (models have never seen it)
# ============================================================
python predict.py dummy.csv

# ============================================================
# 7. Plot dummy results (close each window to advance)
# ============================================================
python plot.py predictions/dummy_predictions.csv
