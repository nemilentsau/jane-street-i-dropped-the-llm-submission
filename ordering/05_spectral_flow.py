"""Ordering Method 5: Spectral Flow

Order blocks to produce the smoothest evolution of the cumulative Jacobian's
eigenvalue spectrum. Linearize each block as A_k = W_out diag(g) W_inp with
globally averaged ReLU gates, then greedily pick the block minimizing spectral
jitter at each step.

Raw ordering: 9/97 positions, MSE ~0.66. Polishes to exact.
"""
from __future__ import annotations

import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

import numpy as np
import torch

from shared import (
    GT_ORDERING, GT_PAIRING_CANONICAL, Timer, load_all_pieces, load_data,
    score_ordering, eval_solution,
)

DASH_DIR = os.path.join(os.path.dirname(__file__), '..', 'dashboard', 'static', 'data')

print("=" * 60)
print("ORDERING METHOD 5: Spectral Flow")
print("=" * 60)

N_BLOCKS = 48


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
    """Eigenvalue magnitudes of the running Jacobian product."""
    d = jacobians[0].shape[0]
    eye = np.eye(d)
    J = eye.copy()
    eig_trajectories = np.zeros((len(ordering), d))
    for step, block_idx in enumerate(ordering):
        J = (eye + jacobians[block_idx]) @ J
        eigvals = np.abs(np.linalg.eigvals(J))
        eigvals.sort()
        eig_trajectories[step] = eigvals
    return eig_trajectories


def spectral_smoothness(eig_trajectories):
    """Total squared jitter between consecutive steps."""
    diffs = np.diff(eig_trajectories, axis=0)
    return float(np.sum(diffs ** 2))


def spectral_flow_greedy(jacobians):
    """Greedy ordering: pick the block producing smoothest spectral transition."""
    d = jacobians[0].shape[0]
    eye = np.eye(d)
    J = eye.copy()
    remaining = set(range(N_BLOCKS))
    ordering: list[int] = []
    prev_eigvals = np.sort(np.abs(np.linalg.eigvals(J)))
    greedy_steps: list[dict] = []

    for step in range(N_BLOCKS):
        best_idx = -1
        best_jitter = float("inf")
        best_J: np.ndarray | None = None
        best_eigvals: np.ndarray | None = None

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
        assert best_J is not None and best_eigvals is not None
        J = best_J
        prev_eigvals = best_eigvals

        greedy_steps.append({
            "step": step,
            "block_idx": best_idx,
            "jitter": round(best_jitter, 6),
        })

        if (step + 1) % 12 == 0 or step == N_BLOCKS - 1:
            print(f"    step {step + 1}/{N_BLOCKS},"
                  f" jitter={best_jitter:.6f}")

    return ordering, greedy_steps


with Timer("Total") as t:
    print("\nLoading data and pieces...")
    X, y_pred, _ = load_data()
    pieces = load_all_pieces()
    pairing = list(GT_PAIRING_CANONICAL)
    n = len(pairing)

    # ── Stage 1: Compute linearized Jacobians ──────────────────
    print("Computing linearized Jacobians...")
    with Timer("  Jacobians"):
        jacobians = compute_linearized_jacobians(pairing, X, pieces)

    # ── Stage 2: Smoothness baselines ──────────────────────────
    print("\nSmoothing baselines...")
    gt_eigs = running_eigenvalues(GT_ORDERING, jacobians)
    gt_smoothness = spectral_smoothness(gt_eigs)
    print(f"  GT spectral smoothness: {gt_smoothness:.4f}")

    rng = np.random.default_rng(42)
    random_smoothnesses: list[float] = []
    for _ in range(20):
        rand_order = rng.permutation(N_BLOCKS).tolist()
        rand_eigs = running_eigenvalues(rand_order, jacobians)
        random_smoothnesses.append(spectral_smoothness(rand_eigs))
    print(f"  Random smoothness: mean={np.mean(random_smoothnesses):.4f},"
          f" std={np.std(random_smoothnesses):.4f}")

    # ── Stage 3: Spectral flow greedy ──────────────────────────
    print("\nSpectral flow greedy ordering...")
    with Timer("  Spectral flow"):
        sf_ordering, greedy_steps = spectral_flow_greedy(jacobians)

    sf_eigs = running_eigenvalues(sf_ordering, jacobians)
    sf_smoothness = spectral_smoothness(sf_eigs)

    raw_mse = eval_solution(pairing, sf_ordering, X, y_pred, pieces)
    raw_pos, _ = score_ordering(sf_ordering, pairing)
    print(f"\n  Spectral flow: smoothness={sf_smoothness:.4f},"
          f" raw_mse={raw_mse:.6e}, pos={raw_pos}/97")

    # ── Stage 4: MSE polish with trace ─────────────────────────
    print("\nMSE polish...")
    polish_trace: list[dict] = [{"iteration": 0, "mse": raw_mse}]
    best = list(sf_ordering)
    best_mse = raw_mse
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

    # ── Eigenvalue trajectories for dashboard ──────────────────
    eig_indices = [0, 6, 12, 18, 24, 30, 36, 47]
    gt_eig_traces = gt_eigs[:, eig_indices].tolist()
    sf_eig_traces = sf_eigs[:, eig_indices].tolist()

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
    "smoothness": {
        "gt": round(gt_smoothness, 4),
        "spectral_flow": round(sf_smoothness, 4),
        "random_mean": round(float(np.mean(random_smoothnesses)), 4),
        "random_std": round(float(np.std(random_smoothnesses)), 4),
    },
    "greedy_steps": greedy_steps,
    "eig_indices": eig_indices,
    "gt_eig_traces": [[round(v, 6) for v in row] for row in gt_eig_traces],
    "sf_eig_traces": [[round(v, 6) for v in row] for row in sf_eig_traces],
    "methods": {
        "raw": {
            "correct_positions": raw_pos,
            "total_positions": 97,
            "mse": raw_mse,
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
out_path = os.path.join(DASH_DIR, "ordering_05_spectral_flow.json")
with open(out_path, "w") as f:
    json.dump(result, f, indent=1)
print(f"\nDashboard data -> {out_path}")
print(f"Done in {t.elapsed:.2f}s")
