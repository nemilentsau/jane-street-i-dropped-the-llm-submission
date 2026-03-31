"""Pairing Method 4: Affine Linearization

Uses the full affine block linearization A = W_out @ diag(g) @ W_inp (gated product
with average ReLU gate from data) plus the bias offset c = W_out @ (gate * b_inp) + b_out.
Features from both the operator matrix A and offset c are used. The full affine pair (A, c)
is required -- c-only features fail completely (0/48).
"""
import itertools
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

import numpy as np
import torch

from shared import INP_PIECES, OUT_PIECES, LAST_PIECE, Timer, load_all_pieces, load_data
from fusion_utils import robust_normalize
from alt_philosophy_utils import affine_features, end_to_end_from_pairing, search_weighted_recipes

print("=" * 60)
print("PAIRING METHOD 4: Affine Linearization")
print("=" * 60)

FEATURE_NAMES = [
    "trace_abs", "tr2_abs", "tr3_abs", "sym_ratio",
    "effective_rank", "neg_top4_share",
    "c_norm", "c_rel_last", "c_quad_abs",
]


with Timer("Total") as t:
    print("\nLoading data and pieces...")
    X, y_pred, _ = load_data()
    pieces = load_all_pieces()

    print("Computing average ReLU gates...")
    gates = {}
    for inp_idx in INP_PIECES:
        w_inp = pieces[inp_idx]["weight"]
        b_inp = pieces[inp_idx]["bias"]
        with torch.no_grad():
            pre = X @ w_inp.T + b_inp
            gates[inp_idx] = (pre > 0).float().mean(dim=0).numpy()

    print("Computing affine feature bank...")
    w_last = pieces[LAST_PIECE]["weight"].squeeze(0).numpy()
    costs = {name: np.zeros((48, 48), dtype=np.float64) for name in FEATURE_NAMES}
    for i, inp_idx in enumerate(INP_PIECES):
        w_inp = pieces[inp_idx]["weight"].numpy()
        b_inp = pieces[inp_idx]["bias"].numpy()
        gate = gates[inp_idx]
        gated_inp = gate[:, None] * w_inp
        gated_bias = gate * b_inp
        for j, out_idx in enumerate(OUT_PIECES):
            w_out = pieces[out_idx]["weight"].numpy()
            b_out = pieces[out_idx]["bias"].numpy()
            a_matrix = w_out @ gated_inp
            c_vec = w_out @ gated_bias + b_out
            feature_vals = affine_features(a_matrix, c_vec, w_last)
            for name in FEATURE_NAMES:
                costs[name][i, j] = feature_vals[name]
        if (i + 1) % 12 == 0:
            print(f"  affine rows: {i + 1}/48")
    costs = {name: robust_normalize(cost) for name, cost in costs.items()}

    print("\nSearching weighted recipes...")
    recipes = []
    for r in [1, 2, 3]:
        recipes.extend(tuple(combo) for combo in itertools.combinations(FEATURE_NAMES, r))
    results = search_weighted_recipes(costs, recipes, X, y_pred, pieces)
    best = results[0]
    exact_count = sum(item["correct_pairs"] == 48 for item in results)

    # Also test c-only features (expected to fail)
    C_ONLY = ["c_norm", "c_rel_last", "c_quad_abs"]
    c_recipes = []
    for r in [1, 2, 3]:
        c_recipes.extend(tuple(combo) for combo in itertools.combinations(C_ONLY, r))
    c_results = search_weighted_recipes(costs, c_recipes, X, y_pred, pieces)
    best_c_only = c_results[0]

    print(f"\n  Best affine recipe: {best['recipe']}")
    print(f"  Pairing accuracy: {best['correct_pairs']}/48")
    print(f"  Exact recipes found: {exact_count}")
    print(f"\n  Best c-only recipe: {best_c_only['recipe']}")
    print(f"  c-only accuracy: {best_c_only['correct_pairs']}/48  (expected ~0)")

    print("\nEnd-to-end verification (delta-greedy + polish)...")
    e2e = end_to_end_from_pairing(best["pairing"], X, y_pred, pieces)
    print(f"  Raw delta-greedy MSE: {e2e['mse_delta']:.6e}")
    print(f"  After polish MSE:     {e2e['polished_mse']:.6e}")

print(f"\nDone in {t.elapsed:.2f}s")
