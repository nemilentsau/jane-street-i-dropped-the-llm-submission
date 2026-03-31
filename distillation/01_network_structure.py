"""Distillation 1: Network Structure Analysis

Analyzes the recovered network as a discretized ODE and maps to finance concepts:
- Symmetric/antisymmetric decomposition (diffusion vs rotation)
- Ornstein-Uhlenbeck test (mean-reverting modes)
- Cumulative drift: spectral radius, condition number, effective rank trajectory
- Factor structure: SVD of the cumulative operator
- Phase structure: early/mid/late dynamics
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

import numpy as np

from shared import Block, GT_ORDERING, GT_PAIRING_CANONICAL, Timer, load_all_pieces, load_data
from dynamics_utils import compute_static_jacobians, run_order_capture, phase_slices

print("=" * 60)
print("DISTILLATION 1: Network Structure Analysis")
print("=" * 60)

with Timer("Total") as t:
    print("\nLoading data and pieces...")
    X, y_pred, _ = load_data()
    pieces = load_all_pieces()
    pairing = list(GT_PAIRING_CANONICAL)
    blocks = [Block(inp, out, pieces) for inp, out in pairing]
    ordering = list(GT_ORDERING)
    N_BLOCKS = len(pairing)

    print("Computing linearized Jacobians...")
    jacobians = compute_static_jacobians(X, pieces, pairing)

    # 1. Symmetric/Antisymmetric decomposition
    print("\n--- Symmetric/Antisymmetric Decomposition ---")
    sym_ratios = []
    for A in jacobians:
        S = (A + A.T) / 2
        A_norm = np.linalg.norm(A, 'fro')
        sym_ratios.append(np.linalg.norm(S, 'fro') / (A_norm + 1e-12))
    print(f"  ||S||/||A|| (diffusion ratio): mean={np.mean(sym_ratios):.4f}")
    print(f"  Interpretation: {np.mean(sym_ratios)*100:.0f}% diffusion, {(1-np.mean(sym_ratios))*100:.0f}% rotation")

    # 2. Trace analysis (volume contraction)
    print("\n--- Volume Contraction (Trace Analysis) ---")
    traces = [float(np.trace(A)) for A in jacobians]
    print(f"  All 48 blocks have negative trace: {all(t < 0 for t in traces)}")
    print(f"  Trace range: [{min(traces):.2f}, {max(traces):.2f}]")

    # 3. Ornstein-Uhlenbeck test
    print("\n--- Mean-Reverting Modes ---")
    frac_neg_all = []
    for A in jacobians:
        S = (A + A.T) / 2
        eigs_S = np.linalg.eigvalsh(S)
        frac_neg_all.append(np.mean(eigs_S < 0))
    print(f"  Fraction of negative eigenvalues of S_k: mean={np.mean(frac_neg_all):.4f}")
    print(f"  ~{np.mean(frac_neg_all)*100:.0f}% of modes are mean-reverting")

    # 4. Cumulative drift analysis
    print("\n--- Cumulative Drift ---")
    eye = np.eye(48)
    P = eye.copy()
    cum_sr = []
    cum_eff_rank = []
    for step, block_idx in enumerate(ordering):
        P = (eye + jacobians[block_idx]) @ P
        eigs = np.abs(np.linalg.eigvals(P))
        cum_sr.append(float(np.max(eigs)))
        sv = np.linalg.svd(P, compute_uv=False)
        probs = sv / sv.sum()
        probs = probs[probs > 1e-10]
        cum_eff_rank.append(float(np.exp(-np.sum(probs * np.log(probs)))))

    print("  Spectral radius trajectory:")
    for step in [0, 11, 23, 35, 47]:
        print(f"    step {step:2d}: rho={cum_sr[step]:.4f}, eff_rank={cum_eff_rank[step]:.2f}")
    print(f"  Net contractive: final rho={cum_sr[-1]:.4f} {'(< 1.0)' if cum_sr[-1] < 1 else '(>= 1.0)'}")

    # 5. Factor structure
    print("\n--- Factor Structure (Final Cumulative Operator) ---")
    sv_final = np.linalg.svd(P, compute_uv=False)
    total_var = np.sum(sv_final ** 2)
    explained = np.cumsum(sv_final ** 2) / total_var
    print(f"  Effective rank: {cum_eff_rank[-1]:.2f}")
    for k in [1, 2, 3, 5, 10]:
        print(f"    Top-{k} factors explain: {explained[k-1]*100:.1f}% variance")

    # 6. Phase structure from trajectory
    print("\n--- Phase Structure ---")
    states = run_order_capture(blocks, ordering, X)
    deltas = []
    for step in range(N_BLOCKS):
        d = (states[step + 1] - states[step]).detach()
        deltas.append(d.norm(dim=1).mean().item())

    phases = phase_slices(N_BLOCKS)
    for phase_name, phase_range in phases.items():
        phase_deltas = [deltas[i] for i in phase_range]
        print(f"  {phase_name:5s} (pos {phase_range.start:2d}-{phase_range.stop-1:2d}): "
              f"mean delta={np.mean(phase_deltas):.4f}")
    print(f"  Late/early ratio: {np.mean([deltas[i] for i in phases['late']]) / np.mean([deltas[i] for i in phases['early']]):.2f}x")
    print(f"  Largest single perturbation: {max(deltas):.4f} at position {np.argmax(deltas)}")

    # 7. PCA of mean trajectory (one mean state per step)
    print("\n--- Trajectory PCA (mean hidden state per step) ---")
    mean_states = np.stack([s.detach().cpu().numpy().mean(axis=0) for s in states])
    mean_traj = mean_states.mean(axis=0)
    centered_traj = mean_states - mean_traj
    cov_traj = centered_traj.T @ centered_traj / max(len(centered_traj) - 1, 1)
    evals_traj = np.linalg.eigvalsh(cov_traj)[::-1]
    explained_traj = np.cumsum(evals_traj) / evals_traj.sum()
    print(f"  PC1: {explained_traj[0]*100:.1f}% variance")
    print(f"  PC1-2: {explained_traj[1]*100:.1f}% variance")
    print(f"  PC1-3: {explained_traj[2]*100:.1f}% variance")

print(f"\nDone in {t.elapsed:.2f}s")
