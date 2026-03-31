"""End-to-End 4: Full Grid (All Pairing x All Ordering)

Tests every combination of pairing method x ordering method.
Shows that multiple independent paths reach the exact answer.
"""
import itertools
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

import numpy as np
import torch
from scipy.optimize import linear_sum_assignment

from shared import (
    INP_PIECES, OUT_PIECES, LAST_PIECE, Block,
    Timer, load_all_pieces, load_data, score_pairing, score_ordering, eval_solution,
)
from fusion_utils import (
    compute_weight_correlation_matrix, compute_effective_rank_matrix,
    compute_geodesic_matrix, compute_single_block_mse_matrix,
    pairing_from_cost, robust_normalize,
    delta_greedy_ordering, pairwise_margin_data, insertion_ordering,
    refine_pairwise, mse_polish,
)
from alt_philosophy_utils import operator_moment_features

print("=" * 60)
print("FULL GRID: All Pairing x Ordering Combinations")
print("=" * 60)


def run_ordering_delta(pairing, X, y_pred, pieces):
    ordering = delta_greedy_ordering(pairing, X, pieces)
    polished, mse = mse_polish(pairing, ordering, X, y_pred, pieces, verbose=False)
    return polished, mse


def run_ordering_tournament(pairing, X, y_pred, pieces, margin=None):
    if margin is None:
        margin = pairwise_margin_data(pairing, X[:2000], y_pred[:2000], pieces, progress_every=None)
    seed_nodes = np.argsort(-margin.sum(axis=1)).tolist()
    ins = insertion_ordering(seed_nodes, margin)
    ref, _ = refine_pairwise(ins, margin, verbose=False)
    polished, mse = mse_polish(pairing, ref, X, y_pred, pieces, verbose=False)
    return polished, mse


with Timer("Total") as t_total:
    print("\nLoading data and pieces...")
    X, y_pred, _ = load_data()
    pieces = load_all_pieces()

    # --- Compute all pairings ---
    print("\nComputing pairings...")
    pairings = {}

    with Timer("  Weight Correlation"):
        corr = compute_weight_correlation_matrix(pieces)
        pairings["WeightCorr"], _, _ = pairing_from_cost(-np.abs(corr))

    with Timer("  Operator Moments"):
        FEATURES = ["trace_abs", "effective_rank"]
        om_costs = {n: np.zeros((48, 48), dtype=np.float64) for n in FEATURES}
        for i, inp_idx in enumerate(INP_PIECES):
            w_inp = pieces[inp_idx]["weight"].numpy()
            for j, out_idx in enumerate(OUT_PIECES):
                w_out = pieces[out_idx]["weight"].numpy()
                fv = operator_moment_features(w_out @ w_inp)
                for n in FEATURES:
                    om_costs[n][i, j] = fv[n]
        fused_om = sum(robust_normalize(om_costs[n]) for n in FEATURES)
        pairings["OpMoments"], _, _ = pairing_from_cost(fused_om)

    with Timer("  Multi-View Fusion"):
        eff_rank = compute_effective_rank_matrix(pieces)
        geodesic = compute_geodesic_matrix(pieces)
        sb_mse = compute_single_block_mse_matrix(X, y_pred, pieces)
        fused = robust_normalize(eff_rank) + robust_normalize(geodesic) + robust_normalize(sb_mse)
        pairings["Fusion"], _, _ = pairing_from_cost(fused)

    print(f"\n  Pairing accuracy:")
    for name, pairing in pairings.items():
        print(f"    {name}: {score_pairing(pairing)}/48")

    # --- Run grid ---
    ordering_methods = ["Delta-Greedy", "Tournament"]
    print(f"\n{'='*70}")
    print(f"{'Pairing':<15} {'Ordering':<15} {'Pairs':>6} {'Polish pos':>11} {'Polish MSE':>14}")
    print(f"{'-'*70}")

    for pair_name, pairing in pairings.items():
        n_pairs = score_pairing(pairing)

        # Delta-greedy
        with Timer(f"  {pair_name} x Delta-Greedy"):
            polished, mse = run_ordering_delta(pairing, X, y_pred, pieces)
        pos, _ = score_ordering(polished, pairing)
        print(f"{pair_name:<15} {'Delta-Greedy':<15} {n_pairs:>3}/48 {pos:>8}/97 {mse:>14.6e}")

        # Tournament
        with Timer(f"  {pair_name} x Tournament"):
            polished, mse = run_ordering_tournament(pairing, X, y_pred, pieces)
        pos, _ = score_ordering(polished, pairing)
        print(f"{pair_name:<15} {'Tournament':<15} {n_pairs:>3}/48 {pos:>8}/97 {mse:>14.6e}")

    print(f"{'='*70}")

print(f"\nTotal wall time: {t_total.elapsed:.2f}s")
