"""Pairing Method 3: SVD Cross-Alignment in Hidden Space

Aligns the write/read directions in the shared 96-D hidden space.
For each inp, its left-singular vectors are the directions it writes into hidden space;
for each out, its right-singular vectors are the directions it reads from.
Correctly paired layers have aligned principal modes at this hidden-space interface.

Key insight: E23 originally aligned the wrong spaces (outer 48-D) and failed (16/48).
E28 repaired this by aligning the correct hidden-space interface and succeeded (48/48).
"""
import itertools
import json
import os
import sys
from collections import Counter
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

import numpy as np
import torch
from scipy.optimize import linear_sum_assignment

from shared import INP_PIECES, OUT_PIECES, Timer, load_all_pieces, load_data
from fusion_utils import robust_normalize
from alt_philosophy_utils import end_to_end_from_pairing, search_weighted_recipes

print("=" * 60)
print("PAIRING METHOD 3: SVD Cross-Alignment (Hidden Space)")
print("=" * 60)

FEATURE_NAMES = ["hidden_diag", "hidden_top8", "hidden_match", "hidden_frob"]


def compute_hidden_alignment_costs(pieces):
    """Align inp left-singular vectors (hidden write) with out right-singular vectors (hidden read)."""
    inp_modes = {}
    for inp_idx in INP_PIECES:
        u, s, _ = torch.linalg.svd(pieces[inp_idx]["weight"], full_matrices=False)
        inp_modes[inp_idx] = {"u_hidden": u.numpy(), "s": (s / s.sum()).numpy()}

    out_modes = {}
    for out_idx in OUT_PIECES:
        _, s, vh = torch.linalg.svd(pieces[out_idx]["weight"], full_matrices=False)
        out_modes[out_idx] = {"v_hidden": vh.T.numpy(), "s": (s / s.sum()).numpy()}

    costs = {name: np.zeros((48, 48), dtype=np.float64) for name in FEATURE_NAMES}
    for i, inp_idx in enumerate(INP_PIECES):
        u_hidden = inp_modes[inp_idx]["u_hidden"]
        s_inp = inp_modes[inp_idx]["s"]
        for j, out_idx in enumerate(OUT_PIECES):
            v_hidden = out_modes[out_idx]["v_hidden"]
            s_out = out_modes[out_idx]["s"]
            align = np.abs(u_hidden.T @ v_hidden)
            weight_matrix = np.outer(s_inp, s_out) * align

            costs["hidden_diag"][i, j] = -np.sum(np.diag(weight_matrix))
            costs["hidden_top8"][i, j] = -np.sum(np.diag(weight_matrix[:8, :8]))

            row_ind, col_ind = linear_sum_assignment(-weight_matrix)
            costs["hidden_match"][i, j] = -weight_matrix[row_ind, col_ind].sum()
            costs["hidden_frob"][i, j] = -np.linalg.norm(weight_matrix, ord="fro")
        if (i + 1) % 12 == 0:
            print(f"  hidden alignment rows: {i + 1}/48")
    return {name: robust_normalize(cost) for name, cost in costs.items()}


with Timer("Total") as t:
    print("\nLoading data and pieces...")
    X, y_pred, _ = load_data()
    pieces = load_all_pieces()

    print("Computing hidden-space alignment costs...")
    costs = compute_hidden_alignment_costs(pieces)

    print("\nSearching weighted recipes...")
    recipes = []
    for r in [1, 2, 3]:
        recipes.extend(tuple(combo) for combo in itertools.combinations(FEATURE_NAMES, r))
    results = search_weighted_recipes(costs, recipes, X, y_pred, pieces)
    best = results[0]
    exact_count = sum(item["correct_pairs"] == 48 for item in results)

    print(f"\n  Best recipe: {best['recipe']}")
    print(f"  Pairing accuracy: {best['correct_pairs']}/48")
    print(f"  Exact recipes found: {exact_count}")

    print("\nEnd-to-end verification (delta-greedy + polish)...")
    e2e = end_to_end_from_pairing(best["pairing"], X, y_pred, pieces)
    print(f"  Raw delta-greedy MSE: {e2e['mse_delta']:.6e}")
    print(f"  After polish MSE:     {e2e['polished_mse']:.6e}")

    # ── Single feature performance ──
    single_perf = []
    for name in FEATURE_NAMES:
        for item in results:
            if item["names"] == (name,) and item["weights"] == (1.0,):
                single_perf.append({"name": name, "accuracy": item["correct_pairs"]})
                break

elapsed = t.elapsed
print(f"\nDone in {elapsed:.2f}s")

# ── Emit dashboard JSON ──────────────────────────────────────────────
DASHBOARD_DATA = os.path.join(
    os.path.dirname(__file__), "..", "dashboard", "static", "data"
)
os.makedirs(DASHBOARD_DATA, exist_ok=True)

accuracy_dist = Counter(item["correct_pairs"] for item in results)

artifact = {
    "method": "SVD Cross-Alignment (Hidden Space)",
    "script": "pairing/03_svd_cross_alignment.py",
    "total_recipes": len(results),
    "exact_count": exact_count,
    "accuracy_distribution": {int(k): v for k, v in sorted(accuracy_dist.items())},
    "single_features": sorted(single_perf, key=lambda x: -x["accuracy"]),
    "best": {"recipe": best["recipe"], "accuracy": best["correct_pairs"]},
    "e2e": {
        "mse_delta": e2e["mse_delta"],
        "polished_mse": e2e["polished_mse"],
    },
    "elapsed_s": round(elapsed, 2),
}

out_path = os.path.join(DASHBOARD_DATA, "pairing_03_svd_cross_alignment.json")
with open(out_path, "w") as f:
    json.dump(artifact, f, separators=(",", ":"))

print(f"Dashboard artifact: {out_path} ({os.path.getsize(out_path) // 1024}KB)")
