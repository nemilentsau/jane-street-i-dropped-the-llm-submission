"""Ordering Method 2: Pairwise Tournament (Insertion + Refinement)

Compares all O(n^2) ordered pairs (A then B vs B then A) to build a signed
margin matrix. Pairwise accuracy is ~77.6% -- better than chance but nontransitive.

Win-count sorting fails (MSE ~0.557) because the preferences are nontransitive.
Smart extraction via insertion + pairwise refinement lands close enough (MSE ~0.111)
for MSE polish to finish the job.
"""
import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

import numpy as np
from shared import (
    GT_ORDERING, GT_PAIRING_CANONICAL, Timer, load_all_pieces, load_data,
    score_ordering, eval_solution,
)
from fusion_utils import (
    pairwise_margin_data, pairwise_accuracy, pairwise_objective,
    insertion_ordering, refine_pairwise,
)

DASH_DIR = os.path.join(os.path.dirname(__file__), '..', 'dashboard', 'static', 'data')

print("=" * 60)
print("ORDERING METHOD 2: Pairwise Tournament")
print("=" * 60)

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

    acc = pairwise_accuracy(margin)
    print(f"\n  Pairwise accuracy vs GT: {acc:.4f}")

    # ── Nontransitivity analysis ───────────────────────────────
    n_intransitive = 0
    n_triples = 0
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                n_triples += 1
                m_ij, m_jk, m_ik = margin[i, j], margin[j, k], margin[i, k]
                if (m_ij > 0 and m_jk > 0 and m_ik < 0) or \
                   (m_ij < 0 and m_jk < 0 and m_ik > 0):
                    n_intransitive += 1
    print(f"  Intransitive triples: {n_intransitive}/{n_triples}"
          f" ({100 * n_intransitive / n_triples:.1f}%)")

    # ── Margin matrix in GT order (for heatmap) ───────────────
    margin_gt = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        for j in range(n):
            margin_gt[i][j] = margin[GT_ORDERING[i], GT_ORDERING[j]]

    # ── Margin statistics ──────────────────────────────────────
    upper_idx = np.triu_indices(n, k=1)
    upper_margins = margin_gt[upper_idx]
    n_concordant = int((upper_margins > 0).sum())
    n_discordant = int((upper_margins < 0).sum())
    total_pairs = len(upper_margins)

    # ── Stage 2a: Naive win-count ordering (baseline) ─────────
    print("\nWin-count ordering (naive baseline)...")
    wins = (margin > 0).sum(axis=1).astype(int)
    ordering_wins = np.argsort(-wins).tolist()
    mse_wins = eval_solution(pairing, ordering_wins, X, y_pred, pieces)
    pos_wins, _ = score_ordering(ordering_wins, pairing)
    pw_wins = pairwise_objective(ordering_wins, margin)
    print(f"  Win-count: pos={pos_wins}/97, MSE={mse_wins:.6e}")

    # ── Stage 2b: Insertion ordering ──────────────────────────
    print("\nInsertion ordering (seeded by sum-of-margins)...")
    seed_nodes = np.argsort(-margin.sum(axis=1)).tolist()
    with Timer("  Insertion"):
        ordering_insert = insertion_ordering(seed_nodes, margin)
    mse_insert = eval_solution(pairing, ordering_insert, X, y_pred, pieces)
    pos_insert, _ = score_ordering(ordering_insert, pairing)
    pw_insert = pairwise_objective(ordering_insert, margin)
    print(f"  Insert: pos={pos_insert}/97, MSE={mse_insert:.6e}")

    # ── Stage 2c: Pairwise swap refinement ────────────────────
    print("\nPairwise swap refinement...")
    with Timer("  Refinement"):
        ordering_refined, pw_refined = refine_pairwise(ordering_insert, margin)
    mse_refined = eval_solution(pairing, ordering_refined, X, y_pred, pieces)
    pos_refined, _ = score_ordering(ordering_refined, pairing)
    print(f"  Refined: pos={pos_refined}/97, MSE={mse_refined:.6e}")

    # ── Stage 3: MSE polish with trace ────────────────────────
    print("\nMSE polish (full 10,000 rows)...")
    polish_trace = [{"iteration": 0, "mse": mse_refined}]
    best = list(ordering_refined)
    best_mse = mse_refined
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
    random_polish = [{"iteration": 0, "mse": rand_mse}]
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
    "pairwise_accuracy": acc,
    "margin_matrix_gt_order": margin_gt.tolist(),
    "margin_distribution": upper_margins.tolist(),
    "margin_stats": {
        "mean_abs": float(np.abs(upper_margins).mean()),
        "median_abs": float(np.median(np.abs(upper_margins))),
        "max_abs": float(np.abs(upper_margins).max()),
        "n_concordant": n_concordant,
        "n_discordant": n_discordant,
        "total_pairs": total_pairs,
    },
    "nontransitive": {
        "n_cycles": n_intransitive,
        "n_triples": n_triples,
        "cycle_rate": n_intransitive / n_triples,
    },
    "methods": {
        "win_count": {
            "correct_positions": pos_wins, "total_positions": 97,
            "mse": mse_wins, "pairwise_score": pw_wins,
        },
        "insertion": {
            "correct_positions": pos_insert, "total_positions": 97,
            "mse": mse_insert, "pairwise_score": pw_insert,
        },
        "refined": {
            "correct_positions": pos_refined, "total_positions": 97,
            "mse": mse_refined, "pairwise_score": pw_refined,
        },
        "polished": {
            "correct_positions": polished_pos, "total_positions": 97,
            "mse": best_mse,
        },
    },
    "polish_trace": polish_trace,
    "random_polish_trace": random_polish,
    "elapsed_s": t.elapsed,
}

os.makedirs(DASH_DIR, exist_ok=True)
out_path = os.path.join(DASH_DIR, "ordering_02_pairwise_tournament.json")
with open(out_path, "w") as f:
    json.dump(result, f, indent=1)
print(f"\nDashboard data -> {out_path}")
print(f"Done in {t.elapsed:.2f}s")
