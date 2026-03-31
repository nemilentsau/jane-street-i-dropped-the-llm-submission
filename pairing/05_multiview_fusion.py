"""Pairing Method 5: Multi-View Fusion

Weighted combination of three individually weaker signals:
  1. Effective rank of W_out @ W_inp
  2. Geodesic distance on Grassmannian (principal angles between subspaces)
  3. Single-block MSE evaluated on the data

None of the three is exact on its own, but their errors are complementary.
Under equal-weight fusion with robust normalization, Hungarian assignment
recovers all 48 pairs. Stable across random subsets as small as 500 rows.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

import numpy as np

from shared import Timer, load_all_pieces, load_data, score_pairing, GT_ORDERING, eval_solution
from fusion_utils import (
    compute_effective_rank_matrix,
    compute_geodesic_matrix,
    compute_single_block_mse_matrix,
    pairing_from_cost,
    robust_normalize,
)

print("=" * 60)
print("PAIRING METHOD 5: Multi-View Fusion")
print("=" * 60)

with Timer("Total") as t:
    print("\nLoading data and pieces...")
    X, y_pred, _ = load_data()
    pieces = load_all_pieces()

    print("Computing component matrices...")
    with Timer("  Effective rank"):
        effective_rank = compute_effective_rank_matrix(pieces)
    with Timer("  Geodesic distance"):
        geodesic = compute_geodesic_matrix(pieces)
    with Timer("  Single-block MSE"):
        single_block_mse = compute_single_block_mse_matrix(X, y_pred, pieces)

    print("\nFusing with equal weights + robust normalization...")
    fused_cost = robust_normalize(effective_rank) + robust_normalize(geodesic) + robust_normalize(single_block_mse)
    pairing, row_ind, col_ind = pairing_from_cost(fused_cost)
    n_correct = score_pairing(pairing)
    mse = eval_solution(pairing, GT_ORDERING, X, y_pred, pieces)

    print(f"\n  Pairing accuracy: {n_correct}/48")
    print(f"  Verification MSE (GT ordering): {mse:.6e}")

    # Individual component accuracy
    for name, matrix in [("Effective rank", effective_rank),
                         ("Geodesic", geodesic),
                         ("Single-block MSE", single_block_mse)]:
        p, _, _ = pairing_from_cost(robust_normalize(matrix))
        print(f"  {name} alone: {score_pairing(p)}/48")

    # Stability test: random subsets
    print("\nStability across data subsets:")
    rng = np.random.default_rng(0)
    for size in [500, 1000, 2000]:
        correct_counts = []
        for trial in range(5):
            indices = rng.choice(len(X), size=size, replace=False)
            sb_subset = compute_single_block_mse_matrix(X[indices], y_pred[indices], pieces, progress_every=None)
            fused = robust_normalize(effective_rank) + robust_normalize(geodesic) + robust_normalize(sb_subset)
            p, _, _ = pairing_from_cost(fused)
            correct_counts.append(score_pairing(p))
        print(f"  {size} rows: {correct_counts} (all trials)")

print(f"\nDone in {t.elapsed:.2f}s")
