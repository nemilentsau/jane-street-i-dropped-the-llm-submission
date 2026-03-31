"""Ordering Method 3: Sinkhorn Ranking

Optimizes a soft doubly-stochastic permutation matrix via Sinkhorn iterations
to maximize expected pairwise score under soft permutation. Uses temperature
annealing from multiple random restarts.

Best restart: raw MSE ~0.123, 9/97 positions. Exact after polish.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

import numpy as np
import torch
from scipy.optimize import linear_sum_assignment

from shared import (
    GT_PAIRING_CANONICAL, Timer, load_all_pieces, load_data,
    score_ordering, eval_solution,
)
from fusion_utils import pairwise_margin_data, mse_polish

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
    restart_results = []
    best_ordering = None
    best_mse = float("inf")

    for seed in range(5):
        torch.manual_seed(seed)
        log_order = torch.nn.Parameter(torch.randn(48, 48) * 0.1)
        optimizer = torch.optim.Adam([log_order], lr=0.3)

        best_score = -float("inf")
        best_soft = None

        for epoch in range(200):
            tau = max(0.03, 1.0 * (0.985 ** epoch))
            Q = sinkhorn(log_order / tau)
            score = expected_pairwise_score(Q, margin)
            loss = -score

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            if score.item() > best_score:
                best_score = score.item()
                best_soft = Q.detach().clone()

        soft_np = best_soft.numpy()
        row_ind, col_ind = linear_sum_assignment(-soft_np)
        ordering = col_ind.tolist()
        mse = eval_solution(pairing, ordering, X, y_pred, pieces)
        correct_pos, _ = score_ordering(ordering, pairing)
        restart_results.append({
            "seed": seed, "mse": mse,
            "correct_positions": correct_pos, "ordering": ordering,
        })
        print(f"  seed={seed}: raw_mse={mse:.6e}, pos={correct_pos}/97")

        if mse < best_mse:
            best_mse = mse
            best_ordering = ordering

    print(f"\n  Best restart MSE: {best_mse:.6e}")

    print("\nMSE polish...")
    with Timer("  Polish"):
        polished, polished_mse = mse_polish(pairing, best_ordering, X, y_pred, pieces)
    polished_pos, _ = score_ordering(polished, pairing)

    print(f"\n  Final results:")
    print(f"    Correct positions: {polished_pos}/97")
    print(f"    MSE: {polished_mse:.6e}")

print(f"\nDone in {t.elapsed:.2f}s")
