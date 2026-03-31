"""End-to-End 2: All Pairing Methods Comparison

Runs all 5 pairing methods and compares their accuracy.
All should achieve 48/48 correct pairs.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

import numpy as np
import torch
from scipy.optimize import linear_sum_assignment

from shared import (
    INP_PIECES, OUT_PIECES, LAST_PIECE,
    Timer, load_all_pieces, load_data, score_pairing, GT_ORDERING, eval_solution,
)
from fusion_utils import (
    compute_weight_correlation_matrix, compute_effective_rank_matrix,
    compute_geodesic_matrix, compute_single_block_mse_matrix,
    pairing_from_cost, robust_normalize,
)
from alt_philosophy_utils import operator_moment_features, affine_features

print("=" * 60)
print("ALL PAIRING METHODS COMPARISON")
print("=" * 60)

with Timer("Total") as t_total:
    print("\nLoading data and pieces...")
    X, y_pred, _ = load_data()
    pieces = load_all_pieces()

    results = []

    # --- Method 1: Weight Correlation ---
    print("\n[1/5] Weight Correlation...")
    with Timer("  Weight Correlation"):
        corr = compute_weight_correlation_matrix(pieces)
        pairing, _, _ = pairing_from_cost(-np.abs(corr))
    results.append(("Weight Correlation", score_pairing(pairing),
                     eval_solution(pairing, GT_ORDERING, X, y_pred, pieces)))

    # --- Method 2: Operator Moments ---
    print("[2/5] Operator Moments...")
    with Timer("  Operator Moments"):
        FEATURES = ["trace_abs", "tr2_abs", "tr3_abs", "sym_ratio",
                     "effective_rank", "stable_rank", "neg_top1_share", "neg_top4_share", "kl_to_exp"]
        costs = {name: np.zeros((48, 48), dtype=np.float64) for name in FEATURES}
        for i, inp_idx in enumerate(INP_PIECES):
            w_inp = pieces[inp_idx]["weight"].numpy()
            for j, out_idx in enumerate(OUT_PIECES):
                w_out = pieces[out_idx]["weight"].numpy()
                fv = operator_moment_features(w_out @ w_inp)
                for name in FEATURES:
                    costs[name][i, j] = fv[name]
        # Best single feature: trace_abs
        pairing, _, _ = pairing_from_cost(robust_normalize(costs["trace_abs"]))
    results.append(("Operator Moments (trace)", score_pairing(pairing),
                     eval_solution(pairing, GT_ORDERING, X, y_pred, pieces)))

    # --- Method 3: SVD Cross-Alignment (Hidden Space) ---
    print("[3/5] SVD Cross-Alignment (Hidden)...")
    with Timer("  SVD Alignment"):
        inp_modes, out_modes = {}, {}
        for inp_idx in INP_PIECES:
            u, s, _ = torch.linalg.svd(pieces[inp_idx]["weight"], full_matrices=False)
            inp_modes[inp_idx] = {"u": u.numpy(), "s": (s / s.sum()).numpy()}
        for out_idx in OUT_PIECES:
            _, s, vh = torch.linalg.svd(pieces[out_idx]["weight"], full_matrices=False)
            out_modes[out_idx] = {"v": vh.T.numpy(), "s": (s / s.sum()).numpy()}
        svd_costs = {n: np.zeros((48, 48), dtype=np.float64)
                     for n in ["hidden_diag", "hidden_top8", "hidden_match", "hidden_frob"]}
        for i, inp_idx in enumerate(INP_PIECES):
            u_h = inp_modes[inp_idx]["u"]
            s_inp = inp_modes[inp_idx]["s"]
            for j, out_idx in enumerate(OUT_PIECES):
                v_h = out_modes[out_idx]["v"]
                s_out = out_modes[out_idx]["s"]
                align = np.abs(u_h.T @ v_h)
                wm = np.outer(s_inp, s_out) * align
                svd_costs["hidden_diag"][i, j] = -np.sum(np.diag(wm))
                svd_costs["hidden_top8"][i, j] = -np.sum(np.diag(wm[:8, :8]))
                ri, ci = linear_sum_assignment(-wm)
                svd_costs["hidden_match"][i, j] = -wm[ri, ci].sum()
                svd_costs["hidden_frob"][i, j] = -np.linalg.norm(wm, ord="fro")
        # Best recipe from pairing/03: weighted combo
        fused_svd = (0.25 * robust_normalize(svd_costs["hidden_diag"])
                     + 0.25 * robust_normalize(svd_costs["hidden_match"])
                     + 1.0 * robust_normalize(svd_costs["hidden_frob"]))
        pairing, _, _ = pairing_from_cost(fused_svd)
    results.append(("SVD Hidden Alignment", score_pairing(pairing),
                     eval_solution(pairing, GT_ORDERING, X, y_pred, pieces)))

    # --- Method 4: Affine Linearization ---
    print("[4/5] Affine Linearization...")
    with Timer("  Affine"):
        w_last = pieces[LAST_PIECE]["weight"].squeeze(0).numpy()
        gates = {}
        for inp_idx in INP_PIECES:
            with torch.no_grad():
                pre = X @ pieces[inp_idx]["weight"].T + pieces[inp_idx]["bias"]
                gates[inp_idx] = (pre > 0).float().mean(dim=0).numpy()
        AF = ["trace_abs", "effective_rank"]
        af_costs = {name: np.zeros((48, 48), dtype=np.float64) for name in AF}
        for i, inp_idx in enumerate(INP_PIECES):
            w_inp = pieces[inp_idx]["weight"].numpy()
            b_inp = pieces[inp_idx]["bias"].numpy()
            g = gates[inp_idx]
            gi = g[:, None] * w_inp
            gb = g * b_inp
            for j, out_idx in enumerate(OUT_PIECES):
                w_out = pieces[out_idx]["weight"].numpy()
                b_out = pieces[out_idx]["bias"].numpy()
                am = w_out @ gi
                cv = w_out @ gb + b_out
                fv = affine_features(am, cv, w_last)
                for name in AF:
                    af_costs[name][i, j] = fv[name]
        fused_af = sum(robust_normalize(af_costs[n]) for n in AF)
        pairing, _, _ = pairing_from_cost(fused_af)
    results.append(("Affine Linearization", score_pairing(pairing),
                     eval_solution(pairing, GT_ORDERING, X, y_pred, pieces)))

    # --- Method 5: Multi-View Fusion ---
    print("[5/5] Multi-View Fusion...")
    with Timer("  Fusion"):
        eff_rank = compute_effective_rank_matrix(pieces)
        geodesic = compute_geodesic_matrix(pieces)
        sb_mse = compute_single_block_mse_matrix(X, y_pred, pieces)
        fused = robust_normalize(eff_rank) + robust_normalize(geodesic) + robust_normalize(sb_mse)
        pairing, _, _ = pairing_from_cost(fused)
    results.append(("Multi-View Fusion", score_pairing(pairing),
                     eval_solution(pairing, GT_ORDERING, X, y_pred, pieces)))

    # Summary table
    print(f"\n{'='*60}")
    print(f"{'Method':<30} {'Pairs':>8} {'GT-order MSE':>14}")
    print(f"{'-'*60}")
    for name, pairs, mse in results:
        print(f"{name:<30} {pairs:>5}/48 {mse:>14.6e}")
    print(f"{'='*60}")

print(f"\nTotal wall time: {t_total.elapsed:.2f}s")
