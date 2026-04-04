"""Distillation 1: Network Structure Analysis

Analyzes the recovered network as a discretized ODE and maps to finance concepts:
- Symmetric/antisymmetric decomposition (diffusion vs rotation)
- Volume contraction (trace analysis)
- Ornstein-Uhlenbeck test (mean-reverting modes)
- Cumulative drift: spectral radius, condition number, effective rank trajectory
- Factor structure: SVD of the cumulative operator
- Phase structure: early/mid/late dynamics
- Feature sensitivity: per-feature variance by phase
- Trajectory PCA
"""
import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

import numpy as np

from shared import Block, GT_ORDERING, GT_PAIRING_CANONICAL, Timer, load_all_pieces, load_data
from dynamics_utils import compute_static_jacobians, run_order_capture, phase_slices

DASH_DIR = os.path.join(os.path.dirname(__file__), '..', 'dashboard', 'static', 'data')

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
    sym_mean = float(np.mean(sym_ratios))
    print(f"  ||S||/||A|| (diffusion ratio): mean={sym_mean:.4f}")
    print(f"  Interpretation: {sym_mean*100:.0f}% diffusion, {(1-sym_mean)*100:.0f}% rotation")

    # 2. Trace analysis (volume contraction)
    print("\n--- Volume Contraction (Trace Analysis) ---")
    traces = [float(np.trace(A)) for A in jacobians]
    all_negative = all(tr < 0 for tr in traces)
    print(f"  All 48 blocks have negative trace: {all_negative}")
    print(f"  Trace range: [{min(traces):.2f}, {max(traces):.2f}]")

    # 3. Ornstein-Uhlenbeck test
    print("\n--- Mean-Reverting Modes ---")
    frac_neg_all = []
    for A in jacobians:
        S = (A + A.T) / 2
        eigs_S = np.linalg.eigvalsh(S)
        frac_neg_all.append(np.mean(eigs_S < 0))
    frac_neg_mean = float(np.mean(frac_neg_all))
    print(f"  Fraction of negative eigenvalues of S_k: mean={frac_neg_mean:.4f}")
    print(f"  ~{frac_neg_mean*100:.0f}% of modes are mean-reverting")

    # 4. Cumulative drift analysis
    print("\n--- Cumulative Drift ---")
    eye = np.eye(48)
    P = eye.copy()
    cum_sr: list[float] = []
    cum_eff_rank: list[float] = []
    cum_condition: list[float] = []
    for step, block_idx in enumerate(ordering):
        P = (eye + jacobians[block_idx]) @ P
        eigs = np.abs(np.linalg.eigvals(P))
        cum_sr.append(float(np.max(eigs)))
        sv = np.linalg.svd(P, compute_uv=False)
        cum_condition.append(float(sv[0] / (sv[-1] + 1e-12)))
        probs = sv / sv.sum()
        probs = probs[probs > 1e-10]
        cum_eff_rank.append(float(np.exp(-np.sum(probs * np.log(probs)))))

    print("  Spectral radius trajectory:")
    for step in [0, 11, 23, 35, 47]:
        print(f"    step {step:2d}: rho={cum_sr[step]:.4f},"
              f" cond={cum_condition[step]:.2f},"
              f" eff_rank={cum_eff_rank[step]:.2f}")
    print(f"  Net contractive: final rho={cum_sr[-1]:.4f}"
          f" {'(< 1.0)' if cum_sr[-1] < 1 else '(>= 1.0)'}")

    # 5. Factor structure
    print("\n--- Factor Structure (Final Cumulative Operator) ---")
    sv_final = np.linalg.svd(P, compute_uv=False)
    total_var = np.sum(sv_final ** 2)
    explained = np.cumsum(sv_final ** 2) / total_var
    print(f"  Effective rank: {cum_eff_rank[-1]:.2f}")
    factor_explained: dict[str, float] = {}
    for k in [1, 2, 3, 5, 10]:
        pct = float(explained[k - 1] * 100)
        factor_explained[f"top_{k}"] = pct
        print(f"    Top-{k} factors explain: {pct:.1f}% variance")

    # 6. Phase structure from trajectory
    print("\n--- Phase Structure ---")
    states = run_order_capture(blocks, ordering, X)
    deltas: list[float] = []
    for step in range(N_BLOCKS):
        d = (states[step + 1] - states[step]).detach()
        deltas.append(d.norm(dim=1).mean().item())

    phases = phase_slices(N_BLOCKS)
    phase_means: dict[str, float] = {}
    for phase_name, phase_range in phases.items():
        phase_deltas = [deltas[i] for i in phase_range]
        mean_d = float(np.mean(phase_deltas))
        phase_means[phase_name] = mean_d
        print(f"  {phase_name:5s} (pos {phase_range.start:2d}-{phase_range.stop-1:2d}): "
              f"mean delta={mean_d:.4f}")
    late_early_ratio = phase_means["late"] / phase_means["early"]
    print(f"  Late/early ratio: {late_early_ratio:.2f}x")
    max_delta_pos = int(np.argmax(deltas))
    print(f"  Largest single perturbation: {max(deltas):.4f} at position {max_delta_pos}")

    # 7. Feature sensitivity by phase
    print("\n--- Feature Sensitivity by Phase ---")
    phase_feature_var: dict[str, dict] = {}
    for phase_name, phase_range in phases.items():
        all_deltas_np = []
        for step in phase_range:
            delta = (states[step + 1] - states[step]).detach().numpy()
            all_deltas_np.append(delta)
        all_deltas_np = np.concatenate(all_deltas_np, axis=0)  # type: ignore[arg-type]
        feature_var = np.var(all_deltas_np, axis=0)
        top5 = np.argsort(feature_var)[-5:][::-1].tolist()
        phase_feature_var[phase_name] = {
            "mean_var": float(feature_var.mean()),
            "top5_features": top5,
            "feature_variance": feature_var.tolist(),
        }
        print(f"  {phase_name:5s}: mean feature variance={feature_var.mean():.6f}, "
              f"top 5 features={top5}")

    late_mid_ratio = phase_feature_var["late"]["mean_var"] / phase_feature_var["mid"]["mean_var"]
    print(f"  Late/mid feature variance ratio: {late_mid_ratio:.1f}x")

    # Feature disjointness
    early_top = set(phase_feature_var["early"]["top5_features"])
    late_top = set(phase_feature_var["late"]["top5_features"])
    overlap = early_top & late_top
    print(f"  Early top-5 features: {phase_feature_var['early']['top5_features']}")
    print(f"  Late  top-5 features: {phase_feature_var['late']['top5_features']}")
    print(f"  Overlap: {len(overlap)} features ({overlap if overlap else 'disjoint'})")

    # 8. PCA of mean trajectory
    print("\n--- Trajectory PCA (mean hidden state per step) ---")
    mean_states = np.stack([s.detach().cpu().numpy().mean(axis=0) for s in states])
    mean_traj = mean_states.mean(axis=0)
    centered_traj = mean_states - mean_traj
    cov_traj = centered_traj.T @ centered_traj / max(len(centered_traj) - 1, 1)
    evals_traj = np.linalg.eigvalsh(cov_traj)[::-1]
    explained_traj = np.cumsum(evals_traj) / evals_traj.sum()
    traj_pca = {
        "pc1": float(explained_traj[0] * 100),
        "pc1_2": float(explained_traj[1] * 100),
        "pc1_3": float(explained_traj[2] * 100),
    }
    print(f"  PC1: {traj_pca['pc1']:.1f}% variance")
    print(f"  PC1-2: {traj_pca['pc1_2']:.1f}% variance")
    print(f"  PC1-3: {traj_pca['pc1_3']:.1f}% variance")

# ── Write dashboard JSON ──────────────────────────────────────
result = {
    "sym_antisym": {
        "sym_ratios": sym_ratios,
        "diffusion_pct": round(sym_mean * 100, 1),
    },
    "traces": {
        "values": traces,
        "all_negative": all_negative,
        "range": [min(traces), max(traces)],
    },
    "mean_reverting": {
        "frac_negative_per_block": frac_neg_all,
        "mean_frac_negative": frac_neg_mean,
    },
    "cumulative_drift": {
        "spectral_radius": cum_sr,
        "effective_rank": cum_eff_rank,
        "condition_number": cum_condition,
    },
    "factor_structure": {
        "effective_rank": cum_eff_rank[-1],
        "explained": factor_explained,
        "singular_values": sv_final.tolist(),
    },
    "phase_structure": {
        "deltas": deltas,
        "phase_means": phase_means,
        "late_early_ratio": late_early_ratio,
        "max_delta_position": max_delta_pos,
    },
    "feature_sensitivity": {
        phase: {
            "mean_var": info["mean_var"],
            "top5_features": info["top5_features"],
        }
        for phase, info in phase_feature_var.items()
    },
    "feature_sensitivity_ratio": late_mid_ratio,
    "feature_overlap": len(overlap),
    "trajectory_pca": traj_pca,
    "elapsed_s": t.elapsed,
}

class NumpyEncoder(json.JSONEncoder):
    def default(self, o: object) -> object:
        if isinstance(o, (np.floating, np.integer)):
            return float(o)
        return super().default(o)

os.makedirs(DASH_DIR, exist_ok=True)
out_path = os.path.join(DASH_DIR, "distillation_01_network_structure.json")
with open(out_path, "w") as f:
    json.dump(result, f, indent=1, cls=NumpyEncoder)
print(f"\nDashboard data -> {out_path}")
print(f"Done in {t.elapsed:.2f}s")
