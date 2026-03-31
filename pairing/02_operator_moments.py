"""Pairing Method 2: Operator Moments

Computes spectral invariants (trace, symmetry ratio, singular value concentration)
of the composed product W_out @ W_inp for every candidate pair. Uses a grid search
over weighted recipes to find optimal combinations. Over 9,000 recipes recover all
48 pairs exactly.
"""
import itertools
import json
import os
import sys
from collections import Counter
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

import numpy as np
from shared import INP_PIECES, OUT_PIECES, Timer, load_all_pieces, load_data
from fusion_utils import robust_normalize
from alt_philosophy_utils import operator_moment_features, end_to_end_from_pairing, search_weighted_recipes

print("=" * 60)
print("PAIRING METHOD 2: Operator Moments")
print("=" * 60)

FEATURE_NAMES = [
    "trace_abs", "tr2_abs", "tr3_abs", "sym_ratio",
    "effective_rank", "stable_rank",
    "neg_top1_share", "neg_top4_share", "kl_to_exp",
]

with Timer("Total") as t:
    print("\nLoading data and pieces...")
    X, y_pred, _ = load_data()
    pieces = load_all_pieces()

    print("Computing operator-moment feature bank...")
    costs = {name: np.zeros((48, 48), dtype=np.float64) for name in FEATURE_NAMES}
    for i, inp_idx in enumerate(INP_PIECES):
        w_inp = pieces[inp_idx]["weight"].numpy()
        for j, out_idx in enumerate(OUT_PIECES):
            w_out = pieces[out_idx]["weight"].numpy()
            feature_vals = operator_moment_features(w_out @ w_inp)
            for name in FEATURE_NAMES:
                costs[name][i, j] = feature_vals[name]
        if (i + 1) % 12 == 0:
            print(f"  operator rows: {i + 1}/48")
    costs = {name: robust_normalize(cost) for name, cost in costs.items()}

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

    print("\n  Top 5 recipes:")
    for i, item in enumerate(results[:5]):
        print(f"    {i+1}. {item['recipe']} -> {item['correct_pairs']}/48")

    print("\nEnd-to-end verification (delta-greedy + polish)...")
    e2e = end_to_end_from_pairing(best["pairing"], X, y_pred, pieces)
    print(f"  Raw delta-greedy MSE: {e2e['mse_delta']:.6e}")
    print(f"  After polish MSE:     {e2e['polished_mse']:.6e}")

elapsed = t.elapsed
print(f"\nDone in {elapsed:.2f}s")

# ── Emit dashboard JSON ──────────────────────────────────────────────
DASHBOARD_DATA = os.path.join(
    os.path.dirname(__file__), "..", "dashboard", "static", "data"
)
os.makedirs(DASHBOARD_DATA, exist_ok=True)

accuracy_dist = Counter(item["correct_pairs"] for item in results)

single_perf = []
for name in FEATURE_NAMES:
    for item in results:
        if item["names"] == (name,) and item["weights"] == (1.0,):
            single_perf.append({"name": name, "accuracy": item["correct_pairs"]})
            break

artifact = {
    "method": "Operator Moments",
    "script": "pairing/02_operator_moments.py",
    "total_recipes": len(results),
    "exact_count": exact_count,
    "accuracy_distribution": {int(k): v for k, v in sorted(accuracy_dist.items())},
    "single_features": sorted(single_perf, key=lambda x: -x["accuracy"]),
    "top_recipes": [
        {"recipe": item["recipe"], "accuracy": item["correct_pairs"]}
        for item in results[:10]
    ],
    "best": {"recipe": best["recipe"], "accuracy": best["correct_pairs"]},
    "e2e": {
        "mse_delta": e2e["mse_delta"],
        "polished_mse": e2e["polished_mse"],
    },
    "elapsed_s": round(elapsed, 2),
}

out_path = os.path.join(DASHBOARD_DATA, "pairing_02_operator_moments.json")
with open(out_path, "w") as f:
    json.dump(artifact, f, separators=(",", ":"))

print(f"Dashboard artifact: {out_path} ({os.path.getsize(out_path) // 1024}KB)")
