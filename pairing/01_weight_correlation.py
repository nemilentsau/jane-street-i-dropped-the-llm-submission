"""Pairing Method 1: Weight Correlation (Frobenius Inner Product)

The simplest pairing method. Computes score(inp_i, out_j) = |tr(W_out_j @ W_inp_i)|
for every candidate pair, then solves the optimal assignment via the Hungarian algorithm.
Requires no data -- only the weight matrices. Recovers all 48/48 pairs.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

import numpy as np
from shared import Timer, load_all_pieces, load_data, score_pairing, GT_ORDERING, eval_solution
from fusion_utils import compute_weight_correlation_matrix, pairing_from_cost

print("=" * 60)
print("PAIRING METHOD 1: Weight Correlation")
print("=" * 60)

with Timer("Total") as t:
    print("\nLoading pieces...")
    pieces = load_all_pieces()

    print("Computing weight correlation matrix...")
    corr_matrix = compute_weight_correlation_matrix(pieces)

    # Use negative absolute value as cost (Hungarian minimizes)
    cost = -np.abs(corr_matrix)
    pairing, row_ind, col_ind = pairing_from_cost(cost)

    n_correct = score_pairing(pairing)
    print(f"\nPairing accuracy: {n_correct}/48")

    # Show separation between correct and incorrect pairs
    correct_scores = []
    incorrect_scores = []
    from shared import GT_PAIR_MAP, INP_PIECES, OUT_PIECES
    for i, inp_idx in enumerate(INP_PIECES):
        for j, out_idx in enumerate(OUT_PIECES):
            score = abs(corr_matrix[i, j])
            if GT_PAIR_MAP.get(inp_idx) == out_idx:
                correct_scores.append(score)
            else:
                incorrect_scores.append(score)

    print("\nScore separation:")
    print(f"  Correct pairs:   mean={np.mean(correct_scores):.4f}, min={np.min(correct_scores):.4f}")
    print(f"  Incorrect pairs: mean={np.mean(incorrect_scores):.4f}, max={np.max(incorrect_scores):.4f}")
    print(f"  Ratio (correct/incorrect mean): {np.mean(correct_scores)/np.mean(incorrect_scores):.2f}x")
    print(f"  Clean separation: {np.min(correct_scores) > np.max(incorrect_scores)}")

    # Verify with GT ordering
    X, y_pred, _ = load_data()
    mse = eval_solution(pairing, GT_ORDERING, X, y_pred, pieces)
    print(f"\n  Verification MSE (GT ordering): {mse:.6e}")

print(f"\nDone in {t.elapsed:.2f}s")
