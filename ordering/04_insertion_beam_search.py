"""Ordering Method 4: Insertion Beam Search

Greedy insertion with branching. At each step, keep the top w best partial
orderings instead of just one. Width 5 performs best (raw MSE 0.089, 11/97
positions). Exact after polish.

Non-monotone in beam width: widths 1, 20 are worse than width 5.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

import numpy as np
from shared import (
    GT_PAIRING_CANONICAL, Timer, load_all_pieces, load_data,
    score_ordering, eval_solution,
)
from fusion_utils import (
    pairwise_margin_data, pairwise_objective, mse_polish,
)

print("=" * 60)
print("ORDERING METHOD 4: Insertion Beam Search")
print("=" * 60)


def insertion_beam(seed_nodes, margin, width):
    beams = [([], 0.0)]
    for step, node in enumerate(seed_nodes):
        candidates = []
        for ordering, _ in beams:
            for pos in range(len(ordering) + 1):
                candidate = list(ordering)
                candidate.insert(pos, node)
                candidates.append((candidate, pairwise_objective(candidate, margin)))
        candidates.sort(key=lambda item: item[1], reverse=True)
        beams = candidates[:width]
        if (step + 1) % 12 == 0:
            print(f"    width={width:2d}, step={step + 1}/48, best_score={beams[0][1]:.6f}")
    return beams[0]


with Timer("Total") as t:
    print("\nLoading data and pieces...")
    X, y_pred, _ = load_data()
    pieces = load_all_pieces()
    pairing = list(GT_PAIRING_CANONICAL)
    X_sub = X[:2000]
    y_sub = y_pred[:2000]

    print("Computing pairwise margin matrix...")
    with Timer("  Pairwise margins"):
        margin = pairwise_margin_data(pairing, X_sub, y_sub, pieces)
    seed_nodes = np.argsort(-margin.sum(axis=1)).tolist()

    print("\nTesting beam widths [1, 5, 20]...")
    beam_results = {}
    for width in [1, 5, 20]:
        print(f"\n  Beam width {width}:")
        with Timer(f"    Beam w={width}"):
            ordering, score = insertion_beam(seed_nodes, margin, width)

        raw_mse = eval_solution(pairing, ordering, X, y_pred, pieces)
        raw_pos, _ = score_ordering(ordering, pairing)

        with Timer(f"    Polish w={width}"):
            polished, polished_mse = mse_polish(
                pairing, ordering, X, y_pred, pieces, verbose=False,
            )
        polished_pos, _ = score_ordering(polished, pairing)

        beam_results[width] = {
            "raw_mse": raw_mse, "raw_pos": raw_pos,
            "polished_mse": polished_mse, "polished_pos": polished_pos,
        }
        print(f"    raw: pos={raw_pos}/97, MSE={raw_mse:.6e}")
        print(f"    polished: pos={polished_pos}/97, MSE={polished_mse:.6e}")

    print("\n  Summary:")
    print(f"  {'Width':>6} {'Raw pos':>8} {'Raw MSE':>12} {'Polish pos':>11} {'Polish MSE':>12}")
    for w, r in beam_results.items():
        print(f"  {w:>6d} {r['raw_pos']:>5d}/97 {r['raw_mse']:>12.6e} {r['polished_pos']:>8d}/97 {r['polished_mse']:>12.6e}")

print(f"\nDone in {t.elapsed:.2f}s")
