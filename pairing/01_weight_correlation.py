"""Pairing Method 1: Weight Correlation (Frobenius Inner Product)

The simplest pairing method. Computes score(inp_i, out_j) = |tr(W_out_j @ W_inp_i)|
for every candidate pair, then solves the optimal assignment via the Hungarian algorithm.
Requires no data -- only the weight matrices. Recovers all 48/48 pairs.
"""
import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

import numpy as np
from shared import (
    Timer, load_all_pieces, load_data, score_pairing,
    GT_ORDERING, GT_PAIR_MAP, INP_PIECES, OUT_PIECES, eval_solution,
)
from fusion_utils import compute_weight_correlation_matrix, pairing_from_cost

DASHBOARD_DATA = os.path.join(
    os.path.dirname(__file__), '..', 'dashboard', 'static', 'data',
)

print("=" * 60)
print("PAIRING METHOD 1: Weight Correlation")
print("=" * 60)

with Timer("Total") as t:
    print("\nLoading pieces...")
    pieces = load_all_pieces()

    print("Computing weight correlation matrix...")
    corr_matrix = compute_weight_correlation_matrix(pieces)
    abs_corr = np.abs(corr_matrix)

    # Hungarian assignment (minimizes cost, so negate)
    pairing, row_ind, col_ind = pairing_from_cost(-abs_corr)

    n_correct = score_pairing(pairing)
    print(f"\nPairing accuracy: {n_correct}/48")

    # ── Separation analysis ──────────────────────────────────────
    correct_scores = []
    incorrect_scores = []
    for i, inp_idx in enumerate(INP_PIECES):
        for j, out_idx in enumerate(OUT_PIECES):
            score = float(abs_corr[i, j])
            if GT_PAIR_MAP.get(inp_idx) == out_idx:
                correct_scores.append(score)
            else:
                incorrect_scores.append(score)

    correct_mean = float(np.mean(correct_scores))
    correct_min = float(np.min(correct_scores))
    incorrect_mean = float(np.mean(incorrect_scores))
    incorrect_max = float(np.max(incorrect_scores))
    ratio = correct_mean / incorrect_mean

    print("\nScore separation:")
    print(f"  Correct pairs:   mean={correct_mean:.4f}, min={correct_min:.4f}")
    print(f"  Incorrect pairs: mean={incorrect_mean:.4f}, max={incorrect_max:.4f}")
    print(f"  Ratio (correct/incorrect mean): {ratio:.2f}x")
    print(f"  Clean separation: {correct_min > incorrect_max}")

    # ── Per-row margins ──────────────────────────────────────────
    # For each inp, how much does its correct partner beat the best incorrect?
    margins = []
    for i, inp_idx in enumerate(INP_PIECES):
        gt_out = GT_PAIR_MAP[inp_idx]
        gt_j = OUT_PIECES.index(gt_out)
        correct_val = float(abs_corr[i, gt_j])
        best_incorrect = max(
            float(abs_corr[i, j]) for j in range(48) if j != gt_j
        )
        margins.append(correct_val - best_incorrect)

    margins_sorted = sorted(margins)
    print(f"\n  Min margin: {min(margins):.4f}")
    print(f"  Median margin: {float(np.median(margins)):.4f}")

    # ── Verification ─────────────────────────────────────────────
    X, y_pred, _ = load_data()
    mse = eval_solution(pairing, GT_ORDERING, X, y_pred, pieces)
    print(f"\n  Verification MSE (GT ordering): {mse:.6e}")

elapsed = t.elapsed
print(f"\nDone in {elapsed:.2f}s")

# ── Emit dashboard JSON ──────────────────────────────────────────
os.makedirs(DASHBOARD_DATA, exist_ok=True)

artifact = {
    "method": "Weight Correlation",
    "script": "pairing/01_weight_correlation.py",
    "accuracy": n_correct,
    "cost_matrix": abs_corr.tolist(),
    "correct_scores": sorted(correct_scores),
    "incorrect_scores": sorted(incorrect_scores),
    "margins": margins_sorted,
    "separation": {
        "correct_mean": correct_mean,
        "correct_min": correct_min,
        "incorrect_mean": incorrect_mean,
        "incorrect_max": incorrect_max,
        "ratio": round(ratio, 2),
        "clean": correct_min > incorrect_max,
    },
    "assignment": [
        [int(INP_PIECES[i]), int(OUT_PIECES[j])]
        for i, j in zip(row_ind, col_ind)
    ],
    "mse": mse,
    "elapsed_s": round(elapsed, 2),
}

out_path = os.path.join(DASHBOARD_DATA, "pairing_01_weight_correlation.json")
with open(out_path, "w") as f:
    json.dump(artifact, f, separators=(",", ":"))

print(f"Dashboard artifact: {out_path} ({os.path.getsize(out_path) // 1024}KB)")
