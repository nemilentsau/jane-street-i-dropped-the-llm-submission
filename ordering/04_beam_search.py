"""Ordering Method 4: Insertion Beam Search

Extends greedy insertion (Method 2's inner step) with beam search: at each step,
keep the top-k partial orderings instead of just one. Uses the same pairwise
margin matrix as Methods 2 and 3.

Width 5 achieves the best raw MSE (0.089). All widths polish to exact.
"""
from __future__ import annotations

import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

import numpy as np
from shared import (
    GT_PAIRING_CANONICAL, Timer, load_all_pieces, load_data,
    score_ordering, eval_solution,
)
from fusion_utils import pairwise_margin_data, insertion_beam

DASH_DIR = os.path.join(os.path.dirname(__file__), '..', 'dashboard', 'static', 'data')

print("=" * 60)
print("ORDERING METHOD 4: Insertion Beam Search")
print("=" * 60)

BEAM_WIDTHS = [1, 5, 20]

with Timer("Total") as t:
    print("\nLoading data and pieces...")
    X, y_pred, _ = load_data()
    pieces = load_all_pieces()
    pairing = list(GT_PAIRING_CANONICAL)
    n = len(pairing)
    X_sub = X[:2000]
    y_sub = y_pred[:2000]

    # ── Stage 1: Compute pairwise margin matrix ────────────────
    print("Computing pairwise margin matrix (2000 rows)...")
    with Timer("  Pairwise margins"):
        margin = pairwise_margin_data(pairing, X_sub, y_sub, pieces)

    seed_nodes = np.argsort(-margin.sum(axis=1)).tolist()

    # ── Stage 2: Beam search at multiple widths ────────────────
    beam_results: list[dict] = []
    best_width_idx = 0
    best_raw_mse = float("inf")

    for wi, width in enumerate(BEAM_WIDTHS):
        print(f"\nBeam width={width}...")
        with Timer(f"  Beam w={width}"):
            ordering, pw_score = insertion_beam(seed_nodes, margin, width)

        raw_mse = eval_solution(pairing, ordering, X, y_pred, pieces)
        raw_pos, _ = score_ordering(ordering, pairing)

        beam_results.append({
            "width": width,
            "pairwise_score": round(pw_score, 4),
            "raw_mse": raw_mse,
            "raw_positions": raw_pos,
            "total_positions": 97,
        })
        print(f"  width={width}: raw_mse={raw_mse:.6e}, pos={raw_pos}/97,"
              f" pw_score={pw_score:.3f}")

        if raw_mse < best_raw_mse:
            best_raw_mse = raw_mse
            best_width_idx = wi

    best_width = BEAM_WIDTHS[best_width_idx]
    print(f"\n  Best width: {best_width} (raw MSE={best_raw_mse:.6e})")

    # ── Stage 3: Polish best width with trace ──────────────────
    print(f"\nMSE polish (width={best_width})...")
    # Re-run beam to get the ordering
    best_ordering, _ = insertion_beam(seed_nodes, margin, best_width,
                                      progress_every=None)
    polish_trace: list[dict] = [{"iteration": 0, "mse": best_raw_mse}]
    best = list(best_ordering)
    best_mse = best_raw_mse
    print(f"    MSE polish start: {best_mse:.6e}")

    improved = True
    iteration = 0
    while improved:
        improved = False
        iteration += 1
        for i in range(len(best)):
            for j in range(i + 1, len(best)):
                candidate = list(best)
                candidate[i], candidate[j] = candidate[j], candidate[i]
                mse = eval_solution(pairing, candidate, X, y_pred, pieces)
                if mse < best_mse - 1e-10:
                    best = candidate
                    best_mse = mse
                    improved = True
        polish_trace.append({"iteration": iteration, "mse": best_mse})
        print(f"    MSE polish iter {iteration}: mse={best_mse:.6e},"
              f" improved={improved}")

    polished_pos, _ = score_ordering(best, pairing)

    print("\n  Final results:")
    print(f"    Correct positions: {polished_pos}/97")
    print(f"    MSE: {best_mse:.6e}")

    # ── Random ordering baseline (same polish budget) ─────────
    import random as _rng
    _rng.seed(0)
    rand_order = list(range(n))
    _rng.shuffle(rand_order)
    rand_mse = eval_solution(pairing, rand_order, X, y_pred, pieces)
    random_polish: list[dict] = [{"iteration": 0, "mse": rand_mse}]
    print(f"\nRandom baseline (seed=0, {len(polish_trace)-1} iters)...")
    print(f"    start: {rand_mse:.6e}")

    rand_best = list(rand_order)
    n_rand_iters = len(polish_trace) - 1
    for rit in range(1, n_rand_iters + 1):
        improved_r = False
        for i in range(n):
            for j in range(i + 1, n):
                candidate = list(rand_best)
                candidate[i], candidate[j] = candidate[j], candidate[i]
                mse = eval_solution(pairing, candidate, X, y_pred, pieces)
                if mse < rand_mse - 1e-10:
                    rand_best = candidate
                    rand_mse = mse
                    improved_r = True
        random_polish.append({"iteration": rit, "mse": rand_mse})
        print(f"    iter {rit}: {rand_mse:.6e}")
        if not improved_r:
            for pad in range(rit + 1, n_rand_iters + 1):
                random_polish.append({"iteration": pad, "mse": rand_mse})
            break

# ── Write dashboard JSON ──────────────────────────────────────
result = {
    "beam_widths": BEAM_WIDTHS,
    "beam_results": beam_results,
    "best_width_idx": best_width_idx,
    "methods": {
        "best_raw": {
            "correct_positions": beam_results[best_width_idx]["raw_positions"],
            "total_positions": 97,
            "mse": beam_results[best_width_idx]["raw_mse"],
            "pairwise_score": beam_results[best_width_idx]["pairwise_score"],
        },
        "polished": {
            "correct_positions": polished_pos,
            "total_positions": 97,
            "mse": best_mse,
        },
    },
    "polish_trace": polish_trace,
    "random_polish_trace": random_polish,
    "elapsed_s": t.elapsed,
}

os.makedirs(DASH_DIR, exist_ok=True)
out_path = os.path.join(DASH_DIR, "ordering_04_beam_search.json")
with open(out_path, "w") as f:
    json.dump(result, f, indent=1)
print(f"\nDashboard data -> {out_path}")
print(f"Done in {t.elapsed:.2f}s")
