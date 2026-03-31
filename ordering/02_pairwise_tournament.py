"""Ordering Method 2: Pairwise Tournament (Insertion + Refinement)

Compares all O(n^2) ordered pairs (A then B vs B then A) to build a signed
margin matrix. Pairwise accuracy is ~77.6% -- better than chance but nontransitive.

Extracts a global ordering via:
  1. Insertion sort seeded by sum-of-margins rank
  2. Greedy pairwise swap refinement to maximize agreement with margins

Raw MSE ~0.111, exact after MSE polish.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

import numpy as np
from shared import (
    GT_PAIRING_CANONICAL, Timer, load_all_pieces, load_data,
    score_ordering, eval_solution,
)
from fusion_utils import (
    pairwise_margin_data, pairwise_accuracy, insertion_ordering,
    refine_pairwise, mse_polish,
)

print("=" * 60)
print("ORDERING METHOD 2: Pairwise Tournament")
print("=" * 60)

with Timer("Total") as t:
    print("\nLoading data and pieces...")
    X, y_pred, _ = load_data()
    pieces = load_all_pieces()
    pairing = list(GT_PAIRING_CANONICAL)
    X_sub = X[:2000]
    y_sub = y_pred[:2000]

    print("Computing pairwise margin matrix (2000 rows)...")
    with Timer("  Pairwise margins"):
        margin = pairwise_margin_data(pairing, X_sub, y_sub, pieces)

    acc = pairwise_accuracy(margin)
    print(f"\n  Pairwise accuracy vs GT: {acc:.4f}")

    print("\nInsertion ordering (seeded by sum-of-margins)...")
    seed_nodes = np.argsort(-margin.sum(axis=1)).tolist()
    with Timer("  Insertion"):
        ordering_insert = insertion_ordering(seed_nodes, margin)
    raw_mse_insert = eval_solution(pairing, ordering_insert, X, y_pred, pieces)
    raw_pos_insert, _ = score_ordering(ordering_insert, pairing)
    print(f"  Insert: pos={raw_pos_insert}/97, MSE={raw_mse_insert:.6e}")

    print("\nPairwise swap refinement...")
    with Timer("  Refinement"):
        ordering_refined, pw_score = refine_pairwise(ordering_insert, margin)
    raw_mse_refined = eval_solution(pairing, ordering_refined, X, y_pred, pieces)
    raw_pos_refined, _ = score_ordering(ordering_refined, pairing)
    print(f"  Refined: pos={raw_pos_refined}/97, MSE={raw_mse_refined:.6e}")

    print("\nMSE polish (full 10,000 rows)...")
    with Timer("  Polish"):
        polished, polished_mse = mse_polish(pairing, ordering_refined, X, y_pred, pieces)
    polished_pos, _ = score_ordering(polished, pairing)

    print(f"\n  Final results:")
    print(f"    Correct positions: {polished_pos}/97")
    print(f"    MSE: {polished_mse:.6e}")

print(f"\nDone in {t.elapsed:.2f}s")
