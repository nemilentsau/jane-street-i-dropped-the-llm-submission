"""Ordering Method 3: Sinkhorn Ranking

Optimizes a soft doubly-stochastic permutation matrix via Sinkhorn iterations
to maximize expected pairwise score under soft permutation. Uses temperature
annealing from multiple random restarts.

Best restart: raw MSE ~0.123, 9/97 positions. Exact after polish.
"""
from __future__ import annotations

import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

import numpy as np
import torch
from scipy.optimize import linear_sum_assignment

from shared import (
    GT_PAIRING_CANONICAL, Timer, load_all_pieces, load_data,
    score_ordering, eval_solution,
)
from fusion_utils import pairwise_margin_data

DASH_DIR = os.path.join(os.path.dirname(__file__), '..', 'dashboard', 'static', 'data')

print("=" * 60)
print("ORDERING METHOD 3: Sinkhorn Ranking")
print("=" * 60)


def sinkhorn(log_alpha, n_iters=30):
    for _ in range(n_iters):
        log_alpha = log_alpha - torch.logsumexp(log_alpha, dim=1, keepdim=True)
        log_alpha = log_alpha - torch.logsumexp(log_alpha, dim=0, keepdim=True)
    return torch.exp(log_alpha)


def expected_pairwise_score(Q, margin):
    suffix = torch.cumsum(Q.flip(0), dim=0).flip(0) - Q
    score = torch.tensor(0.0, dtype=Q.dtype)
    for pos in range(Q.shape[0] - 1):
        score = score + Q[pos] @ margin @ suffix[pos]
    return score


with Timer("Total") as t:
    print("\nLoading data and pieces...")
    X, y_pred, _ = load_data()
    pieces = load_all_pieces()
    pairing = list(GT_PAIRING_CANONICAL)
    X_sub = X[:2000]
    y_sub = y_pred[:2000]

    print("Computing pairwise margin matrix...")
    with Timer("  Pairwise margins"):
        margin_np = pairwise_margin_data(pairing, X_sub, y_sub, pieces)
    margin = torch.tensor(margin_np, dtype=torch.float32)

    print("\nSinkhorn ranking with 5 restarts...")
    restarts = []
    best_restart_idx = 0
    best_mse = float("inf")
    best_soft_np: np.ndarray | None = None
    best_ordering: list[int] = []

    for seed in range(5):
        torch.manual_seed(seed)
        log_order = torch.nn.Parameter(torch.randn(48, 48) * 0.1)
        optimizer = torch.optim.Adam([log_order], lr=0.3)

        best_score = -float("inf")
        best_soft = None
        training_curve: list[dict] = []

        for epoch in range(200):
            tau = max(0.03, 1.0 * (0.985 ** epoch))
            Q = sinkhorn(log_order / tau)
            score = expected_pairwise_score(Q, margin)
            loss = -score

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            training_curve.append({
                "epoch": epoch,
                "score": round(score.item(), 4),
                "tau": round(tau, 4),
            })

            if score.item() > best_score:
                best_score = score.item()
                best_soft = Q.detach().clone()

        assert best_soft is not None
        soft_np = best_soft.numpy()
        _, col_ind = linear_sum_assignment(-soft_np)
        ordering = col_ind.tolist()
        mse = eval_solution(pairing, ordering, X, y_pred, pieces)
        correct_pos, _ = score_ordering(ordering, pairing)

        restarts.append({
            "seed": seed,
            "mse": mse,
            "correct_positions": correct_pos,
            "total_positions": 97,
            "best_score": round(best_score, 4),
            "training_curve": training_curve,
        })
        print(f"  seed={seed}: raw_mse={mse:.6e}, pos={correct_pos}/97,"
              f" score={best_score:.3f}")

        if mse < best_mse:
            best_mse = mse
            best_restart_idx = seed
            best_soft_np = soft_np
            best_ordering = ordering

    print(f"\n  Best restart: seed={best_restart_idx}, MSE={best_mse:.6e}")

    # ── Position confidence from best soft matrix ─────────────
    assert best_soft_np is not None
    position_confidence = best_soft_np.max(axis=1).tolist()

    # ── Reordered soft matrix (rows=positions, cols reordered) ─
    soft_reordered = best_soft_np[:, best_ordering]

    # ── MSE polish with trace ─────────────────────────────────
    print("\nMSE polish...")
    polish_trace = [{"iteration": 0, "mse": best_mse}]
    best = list(best_ordering)
    best_polish_mse = best_mse
    print(f"    MSE polish start: {best_polish_mse:.6e}")

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
                if mse < best_polish_mse - 1e-10:
                    best = candidate
                    best_polish_mse = mse
                    improved = True
        polish_trace.append({"iteration": iteration, "mse": best_polish_mse})
        print(f"    MSE polish iter {iteration}: mse={best_polish_mse:.6e},"
              f" improved={improved}")

    polished_pos, _ = score_ordering(best, pairing)

    print("\n  Final results:")
    print(f"    Correct positions: {polished_pos}/97")
    print(f"    MSE: {best_polish_mse:.6e}")

# ── Write dashboard JSON ──────────────────────────────────────
result = {
    "restarts": restarts,
    "best_restart_idx": best_restart_idx,
    "soft_matrix_reordered": np.round(soft_reordered, 4).tolist(),
    "position_confidence": [round(c, 4) for c in position_confidence],
    "methods": {
        "best_raw": {
            "correct_positions": restarts[best_restart_idx]["correct_positions"],
            "total_positions": 97,
            "mse": restarts[best_restart_idx]["mse"],
        },
        "polished": {
            "correct_positions": polished_pos,
            "total_positions": 97,
            "mse": best_polish_mse,
        },
    },
    "polish_trace": polish_trace,
    "elapsed_s": t.elapsed,
}

os.makedirs(DASH_DIR, exist_ok=True)
out_path = os.path.join(DASH_DIR, "ordering_03_sinkhorn_ranking.json")
with open(out_path, "w") as f:
    json.dump(result, f, indent=1)
print(f"\nDashboard data -> {out_path}")
print(f"Done in {t.elapsed:.2f}s")
