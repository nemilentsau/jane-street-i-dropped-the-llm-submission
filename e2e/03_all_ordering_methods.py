"""End-to-End 3: All Ordering Methods Comparison

Uses GT pairing to isolate the ordering question.
Runs all ordering methods and compares raw and polished results.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

import numpy as np
import torch
from scipy.optimize import linear_sum_assignment

from shared import (
    GT_PAIRING_CANONICAL,
    Timer, load_all_pieces, load_data, score_ordering, eval_solution,
)
from fusion_utils import (
    delta_greedy_ordering, pairwise_margin_data, insertion_ordering,
    refine_pairwise, pairwise_objective, mse_polish,
)

print("=" * 60)
print("ALL ORDERING METHODS COMPARISON")
print("  (Using GT pairing to isolate ordering)")
print("=" * 60)

with Timer("Total") as t_total:
    print("\nLoading data and pieces...")
    X, y_pred, _ = load_data()
    pieces = load_all_pieces()
    pairing = list(GT_PAIRING_CANONICAL)
    N_BLOCKS = len(pairing)

    results = []

    # --- Method 1: Delta-Greedy ---
    print("\n[1/5] Delta-Greedy...")
    with Timer("  Delta-greedy"):
        dg_ord = delta_greedy_ordering(pairing, X, pieces)
    dg_mse = eval_solution(pairing, dg_ord, X, y_pred, pieces)
    dg_pos, _ = score_ordering(dg_ord, pairing)
    results.append({"name": "Delta-Greedy", "raw_pos": dg_pos, "raw_mse": dg_mse, "ordering": dg_ord})

    # --- Shared: Pairwise margins (used by methods 2-4) ---
    print("\n[Shared] Computing pairwise margins...")
    X_sub, y_sub = X[:2000], y_pred[:2000]
    with Timer("  Pairwise margins"):
        margin = pairwise_margin_data(pairing, X_sub, y_sub, pieces)
    seed_nodes = np.argsort(-margin.sum(axis=1)).tolist()

    # --- Method 2: Pairwise Tournament ---
    print("\n[2/5] Pairwise Tournament (insertion + refinement)...")
    with Timer("  Tournament"):
        ins_ord = insertion_ordering(seed_nodes, margin)
        ref_ord, _ = refine_pairwise(ins_ord, margin, verbose=False)
    ref_mse = eval_solution(pairing, ref_ord, X, y_pred, pieces)
    ref_pos, _ = score_ordering(ref_ord, pairing)
    results.append({"name": "Pairwise Tournament", "raw_pos": ref_pos, "raw_mse": ref_mse, "ordering": ref_ord})

    # --- Method 3: Sinkhorn Ranking ---
    print("\n[3/5] Sinkhorn Ranking (3 restarts)...")
    margin_t = torch.tensor(margin, dtype=torch.float32)

    def sinkhorn(log_alpha, n_iters=30):
        for _ in range(n_iters):
            log_alpha = log_alpha - torch.logsumexp(log_alpha, dim=1, keepdim=True)
            log_alpha = log_alpha - torch.logsumexp(log_alpha, dim=0, keepdim=True)
        return torch.exp(log_alpha)

    def expected_pairwise_score(Q, m):
        suffix = torch.cumsum(Q.flip(0), dim=0).flip(0) - Q
        score = torch.tensor(0.0, dtype=Q.dtype)
        for pos in range(Q.shape[0] - 1):
            score = score + Q[pos] @ m @ suffix[pos]
        return score

    best_sk_mse, best_sk_ord = float("inf"), None
    with Timer("  Sinkhorn"):
        for seed in range(3):
            torch.manual_seed(seed)
            log_order = torch.nn.Parameter(torch.randn(48, 48) * 0.1)
            opt = torch.optim.Adam([log_order], lr=0.3)
            best_score, best_soft = -float("inf"), None
            for epoch in range(200):
                tau = max(0.03, 1.0 * (0.985 ** epoch))
                Q = sinkhorn(log_order / tau)
                s = expected_pairwise_score(Q, margin_t)
                (-s).backward()
                opt.step()
                opt.zero_grad()
                if s.item() > best_score:
                    best_score = s.item()
                    best_soft = Q.detach().clone()
            assert best_soft is not None
            ri, ci = linear_sum_assignment(-best_soft.numpy())
            sk_ord = ci.tolist()
            sk_mse = eval_solution(pairing, sk_ord, X, y_pred, pieces)
            if sk_mse < best_sk_mse:
                best_sk_mse = sk_mse
                best_sk_ord = sk_ord
    sk_pos, _ = score_ordering(best_sk_ord, pairing)
    results.append({"name": "Sinkhorn Ranking", "raw_pos": sk_pos, "raw_mse": best_sk_mse, "ordering": best_sk_ord})

    # --- Method 4: Insertion Beam Search ---
    print("\n[4/5] Insertion Beam Search (width=5)...")
    with Timer("  Beam search"):
        beams = [([], 0.0)]
        for step, node in enumerate(seed_nodes):
            candidates = []
            for ordering, _ in beams:
                for pos in range(len(ordering) + 1):
                    c = list(ordering)
                    c.insert(pos, node)
                    candidates.append((c, pairwise_objective(c, margin)))
            candidates.sort(key=lambda x: x[1], reverse=True)
            beams = candidates[:5]
        beam_ord = beams[0][0]
    beam_mse = eval_solution(pairing, beam_ord, X, y_pred, pieces)
    beam_pos, _ = score_ordering(beam_ord, pairing)
    results.append({"name": "Beam Search (w=5)", "raw_pos": beam_pos, "raw_mse": beam_mse, "ordering": beam_ord})

    # --- Method 5: Spectral Flow ---
    print("\n[5/5] Spectral Flow...")
    with Timer("  Spectral flow"):
        jacobians = []
        for inp_idx, out_idx in pairing:
            w_inp = pieces[inp_idx]["weight"]
            b_inp = pieces[inp_idx]["bias"]
            w_out = pieces[out_idx]["weight"]
            with torch.no_grad():
                pre = X @ w_inp.T + b_inp
                gate = (pre > 0).float().mean(dim=0)
                A = w_out @ torch.diag(gate) @ w_inp
            jacobians.append(A.numpy())

        d = jacobians[0].shape[0]
        eye = np.eye(d)
        J = eye.copy()
        remaining = set(range(N_BLOCKS))
        sf_ord = []
        prev_eig = np.sort(np.abs(np.linalg.eigvals(J)))
        for step in range(N_BLOCKS):
            best_idx, best_jitter, best_J, best_eig = -1, float("inf"), None, None
            for idx in remaining:
                Jc = (eye + jacobians[idx]) @ J
                ev = np.sort(np.abs(np.linalg.eigvals(Jc)))
                jit = float(np.sum((ev - prev_eig) ** 2))
                if jit < best_jitter:
                    best_jitter, best_idx, best_J, best_eig = jit, idx, Jc, ev
            sf_ord.append(best_idx)
            remaining.remove(best_idx)
            J, prev_eig = best_J, best_eig
    sf_mse = eval_solution(pairing, sf_ord, X, y_pred, pieces)
    sf_pos, _ = score_ordering(sf_ord, pairing)
    results.append({"name": "Spectral Flow", "raw_pos": sf_pos, "raw_mse": sf_mse, "ordering": sf_ord})

    # --- Polish all ---
    print("\n--- Polishing all methods ---")
    print(f"\n{'Method':<25} {'Raw pos':>8} {'Raw MSE':>12} {'Polish pos':>11} {'Polish MSE':>14}")
    print(f"{'-'*72}")
    for r in results:
        with Timer(f"  Polish {r['name']}"):
            polished, polished_mse = mse_polish(
                pairing, r["ordering"], X, y_pred, pieces, verbose=False,
            )
        polished_pos, _ = score_ordering(polished, pairing)
        r["polished_pos"] = polished_pos
        r["polished_mse"] = polished_mse
        print(f"{r['name']:<25} {r['raw_pos']:>5}/97 {r['raw_mse']:>12.6e} "
              f"{polished_pos:>8}/97 {polished_mse:>14.6e}")

print(f"\nTotal wall time: {t_total.elapsed:.2f}s")
