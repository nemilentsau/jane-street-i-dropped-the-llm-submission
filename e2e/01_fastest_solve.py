"""End-to-End 1: Fastest Solve

The fastest path to the exact answer:
  Weight correlation (no data needed for pairing) + delta-greedy + MSE polish

Demonstrates the full pipeline from shuffled pieces to verified MSE = 3.16e-14.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

import numpy as np
from shared import Timer, load_all_pieces, load_data, score_pairing, score_ordering, eval_solution, print_report
from fusion_utils import compute_weight_correlation_matrix, pairing_from_cost, delta_greedy_ordering, mse_polish

print("=" * 60)
print("END-TO-END: Fastest Solve")
print("  Weight Correlation + Delta-Greedy + MSE Polish")
print("=" * 60)

with Timer("Total") as t_total:
    # Step 1: Load
    print("\n[Step 1] Loading data and pieces...")
    with Timer("  Load"):
        X, y_pred, _ = load_data()
        pieces = load_all_pieces()

    # Step 2: Pairing via weight correlation
    print("\n[Step 2] Pairing via weight correlation...")
    with Timer("  Pairing"):
        corr_matrix = compute_weight_correlation_matrix(pieces)
        cost = -np.abs(corr_matrix)
        pairing, _, _ = pairing_from_cost(cost)
    n_correct_pairs = score_pairing(pairing)
    print(f"  -> {n_correct_pairs}/48 correct pairs")

    # Step 3: Ordering via delta-greedy
    print("\n[Step 3] Ordering via delta-greedy...")
    with Timer("  Delta-greedy"):
        ordering = delta_greedy_ordering(pairing, X, pieces)
    raw_mse = eval_solution(pairing, ordering, X, y_pred, pieces)
    raw_pos, _ = score_ordering(ordering, pairing)
    print(f"  -> {raw_pos}/97 correct positions, MSE={raw_mse:.6e}")

    # Step 4: MSE polish
    print("\n[Step 4] MSE polish (greedy pairwise swaps)...")
    with Timer("  Polish"):
        polished, polished_mse = mse_polish(pairing, ordering, X, y_pred, pieces, max_iters=5)
    polished_pos, _ = score_ordering(polished, pairing)

print_report(
    "Weight Correlation + Delta-Greedy + Polish",
    pairing, polished, t_total.elapsed, X, y_pred, pieces,
)
