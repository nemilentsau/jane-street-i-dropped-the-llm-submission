"""Ordering Method 1: Delta-Greedy (Residual-Flow)

Greedy forward construction: at each step, pick the remaining block that
minimizes ||block(x) - x|| (the perturbation magnitude). Interprets residual
blocks as discrete ODE steps where early blocks make small corrections and
late blocks make larger ones.

The strongest raw extractor: 77/97 correct positions, MSE 0.000288.
Exact after greedy polish.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

from shared import (
    GT_PAIRING_CANONICAL, Timer, load_all_pieces, load_data,
    score_ordering, eval_solution, print_report,
)
from fusion_utils import delta_greedy_ordering, mse_polish

print("=" * 60)
print("ORDERING METHOD 1: Delta-Greedy (Residual-Flow)")
print("=" * 60)

with Timer("Total") as t:
    print("\nLoading data and pieces...")
    X, y_pred, _ = load_data()
    pieces = load_all_pieces()
    pairing = list(GT_PAIRING_CANONICAL)

    print("Running delta-greedy ordering...")
    with Timer("  Delta-greedy"):
        ordering = delta_greedy_ordering(pairing, X, pieces)

    raw_mse = eval_solution(pairing, ordering, X, y_pred, pieces)
    raw_pos, _ = score_ordering(ordering, pairing)
    print(f"\n  Raw results:")
    print(f"    Correct positions: {raw_pos}/97")
    print(f"    MSE: {raw_mse:.6e}")

    print("\nRunning MSE polish (greedy pairwise swaps)...")
    with Timer("  Polish"):
        polished, polished_mse = mse_polish(pairing, ordering, X, y_pred, pieces, max_iters=5)

    polished_pos, _ = score_ordering(polished, pairing)
    print(f"\n  After polish:")
    print(f"    Correct positions: {polished_pos}/97")
    print(f"    MSE: {polished_mse:.6e}")

print(f"\nDone in {t.elapsed:.2f}s")
