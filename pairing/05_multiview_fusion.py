"""Pairing Method 5: Multi-View Fusion

Weighted combination of three individually weaker signals:
  1. Effective rank of W_out @ W_inp
  2. Geodesic distance on Grassmannian (principal angles between subspaces)
  3. Single-block MSE evaluated on the data

None of the three is exact on its own, but their errors are complementary.
Under equal-weight fusion with robust normalization, Hungarian assignment
recovers all 48 pairs. Stable across random subsets as small as 500 rows.
"""
import json
import os
import sys
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
    component_perf = []
    for name, key, matrix in [("Effective rank", "effective_rank", effective_rank),
                               ("Geodesic distance", "geodesic", geodesic),
                               ("Single-block MSE", "single_block_mse", single_block_mse)]:
        p, _, _ = pairing_from_cost(robust_normalize(matrix))
        acc = score_pairing(p)
        component_perf.append({"name": key, "label": name, "accuracy": acc})
        print(f"  {name} alone: {acc}/48")

    # Stability test: random subsets
    print("\nStability across data subsets:")
    rng = np.random.default_rng(0)
    stability_results = []
    for size in [500, 1000, 2000]:
        correct_counts = []
        for trial in range(5):
            indices = rng.choice(len(X), size=size, replace=False)
            sb_subset = compute_single_block_mse_matrix(X[indices], y_pred[indices], pieces, progress_every=None)
            fused = robust_normalize(effective_rank) + robust_normalize(geodesic) + robust_normalize(sb_subset)
            p, _, _ = pairing_from_cost(fused)
            correct_counts.append(score_pairing(p))
        stability_results.append({"subset_size": size, "trials": correct_counts})
        print(f"  {size} rows: {correct_counts} (all trials)")

elapsed = t.elapsed
print(f"\nDone in {elapsed:.2f}s")

# ── Emit dashboard JSON ──────────────────────────────────────────────
DASHBOARD_DATA = os.path.join(
    os.path.dirname(__file__), "..", "dashboard", "static", "data"
)
os.makedirs(DASHBOARD_DATA, exist_ok=True)

artifact = {
    "method": "Multi-View Fusion",
    "script": "pairing/05_multiview_fusion.py",
    "fused_accuracy": n_correct,
    "verification_mse": mse,
    "components": sorted(component_perf, key=lambda x: -x["accuracy"]),
    "stability": stability_results,
    "elapsed_s": round(elapsed, 2),
}

out_path = os.path.join(DASHBOARD_DATA, "pairing_05_multiview_fusion.json")
with open(out_path, "w") as f:
    json.dump(artifact, f, separators=(",", ":"))

print(f"Dashboard artifact: {out_path} ({os.path.getsize(out_path) // 1024}KB)")
