"""Ordering Method 5: Spectral Flow

The only successful ordering method that does not use prediction MSE or pairwise
comparisons. Works from linearized block Jacobians A_k = W_out diag(g) W_inp and
greedily minimizes eigenvalue jitter in the cumulative Jacobian product.

Raw ordering is weak (9/97 correct, MSE 0.663) but lands in the right basin.
Exact after greedy polish.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

import numpy as np
import torch

from shared import (
    GT_ORDERING, GT_PAIRING_CANONICAL,
    Timer, load_all_pieces, load_data,
    score_ordering, eval_solution,
)
from fusion_utils import delta_greedy_ordering, mse_polish

print("=" * 60)
print("ORDERING METHOD 5: Spectral Flow")
print("=" * 60)


def compute_linearized_jacobians(pairing, X, pieces):
    """Compute A_k = W_out_k @ diag(g_k) @ W_inp_k for each block."""
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
    return jacobians


def running_eigenvalues(ordering, jacobians):
    n = len(ordering)
    d = jacobians[0].shape[0]
    eye = np.eye(d)
    J = eye.copy()
    eig_trajectories = np.zeros((n, d))
    for step, block_idx in enumerate(ordering):
        J = (eye + jacobians[block_idx]) @ J
        eigvals = np.abs(np.linalg.eigvals(J))
        eigvals.sort()
        eig_trajectories[step] = eigvals
    return eig_trajectories


def spectral_smoothness(eig_trajectories):
    diffs = np.diff(eig_trajectories, axis=0)
    return float(np.sum(diffs ** 2))


def spectral_flow_greedy(jacobians, n_blocks):
    d = jacobians[0].shape[0]
    eye = np.eye(d)
    J = eye.copy()
    remaining = set(range(n_blocks))
    ordering = []
    prev_eigvals = np.sort(np.abs(np.linalg.eigvals(J)))

    for step in range(n_blocks):
        best_idx = -1
        best_jitter = float("inf")
        best_J = None
        best_eigvals = None

        for idx in remaining:
            J_candidate = (eye + jacobians[idx]) @ J
            eigvals = np.sort(np.abs(np.linalg.eigvals(J_candidate)))
            jitter = float(np.sum((eigvals - prev_eigvals) ** 2))
            if jitter < best_jitter:
                best_jitter = jitter
                best_idx = idx
                best_J = J_candidate
                best_eigvals = eigvals

        ordering.append(best_idx)
        remaining.remove(best_idx)
        J = best_J
        prev_eigvals = best_eigvals

        if (step + 1) % 12 == 0 or step == n_blocks - 1:
            print(f"    step {step + 1}/{n_blocks}, jitter={best_jitter:.6f}")

    return ordering


with Timer("Total") as t:
    print("\nLoading data and pieces...")
    X, y_pred, _ = load_data()
    pieces = load_all_pieces()
    pairing = list(GT_PAIRING_CANONICAL)
    N_BLOCKS = len(pairing)

    print("Computing linearized Jacobians...")
    with Timer("  Jacobians"):
        jacobians = compute_linearized_jacobians(pairing, X, pieces)

    # Baseline: GT ordering smoothness
    gt_eigs = running_eigenvalues(GT_ORDERING, jacobians)
    gt_smoothness = spectral_smoothness(gt_eigs)
    print(f"\n  GT spectral smoothness: {gt_smoothness:.4f}")

    # Random ordering smoothness
    rng = np.random.default_rng(42)
    random_smoothnesses = [spectral_smoothness(running_eigenvalues(rng.permutation(N_BLOCKS).tolist(), jacobians)) for _ in range(20)]
    print(f"  Random smoothness: mean={np.mean(random_smoothnesses):.4f}")

    print("\nRunning spectral flow greedy...")
    with Timer("  Spectral flow"):
        sf_ordering = spectral_flow_greedy(jacobians, N_BLOCKS)
    sf_eigs = running_eigenvalues(sf_ordering, jacobians)
    sf_smoothness = spectral_smoothness(sf_eigs)
    sf_mse_raw = eval_solution(pairing, sf_ordering, X, y_pred, pieces)
    sf_pos_raw, _ = score_ordering(sf_ordering, pairing)

    print("\n  Spectral flow greedy:")
    print(f"    Smoothness: {sf_smoothness:.4f} (GT: {gt_smoothness:.4f}, random: {np.mean(random_smoothnesses):.4f})")
    print(f"    Raw positions: {sf_pos_raw}/97")
    print(f"    Raw MSE: {sf_mse_raw:.6e}")

    # Delta-greedy for comparison
    print("\nDelta-greedy baseline for comparison...")
    with Timer("  Delta-greedy"):
        dg_ordering = delta_greedy_ordering(pairing, X, pieces)
    dg_mse_raw = eval_solution(pairing, dg_ordering, X, y_pred, pieces)
    dg_pos_raw, _ = score_ordering(dg_ordering, pairing)
    print(f"  Delta-greedy: pos={dg_pos_raw}/97, MSE={dg_mse_raw:.6e}")

    # Polish both
    print("\nPolishing both methods...")
    for name, ordering in [("Spectral flow", sf_ordering), ("Delta-greedy", dg_ordering)]:
        with Timer(f"  Polish {name}"):
            polished, polished_mse = mse_polish(pairing, ordering, X, y_pred, pieces, verbose=False)
        polished_pos, _ = score_ordering(polished, pairing)
        print(f"  {name}: polished pos={polished_pos}/97, MSE={polished_mse:.6e}")

print(f"\nDone in {t.elapsed:.2f}s")
