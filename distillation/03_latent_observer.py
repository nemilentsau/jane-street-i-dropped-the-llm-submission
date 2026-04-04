"""Distillation 3: Latent Observer Distillation

Fits compact low-rank surrogates to the GT trajectories:
- Autonomous model: z_{t+1} = a + z_t @ F (pure latent dynamics)
- Observer model: z_{t+1} = a + z_t @ F + r_t @ C (with residual correction)

The observer wins on final prediction accuracy and shock-response fidelity:
  rank 9 prediction MSE: 0.8466 -> 0.8015
  shock damping gap: 1.1530 -> 0.6582

The best compact summary is a low-rank stable factor system with observer-like
correction from the current high-dimensional state.
"""
import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

import numpy as np
import torch

from shared import Block, GT_ORDERING, GT_PAIRING_CANONICAL, LAST_PIECE, Timer, load_all_pieces, load_data
from dynamics_utils import (
    build_direction_library, run_order_capture, predict_from_state,
)

print("=" * 60)
print("DISTILLATION 3: Latent Observer Distillation")
print("=" * 60)

RANKS = [5, 7, 9]
MAX_RADIUS = 0.98
SHOCK_ROWS = 512


def fit_pca_basis(states_np, train_idx, rank):
    cloud = np.concatenate([state[train_idx] for state in states_np], axis=0)
    mean = cloud.mean(axis=0)
    centered = cloud - mean
    _, _, vh = np.linalg.svd(centered, full_matrices=False)
    basis = vh[:rank].T
    return mean, basis


def project_states_np(states_np, mean, basis):
    return [(state - mean) @ basis for state in states_np]


def spectral_clip(mat, radius=MAX_RADIUS):
    eigvals = np.linalg.eigvals(mat)
    sr = float(np.max(np.abs(eigvals))) if eigvals.size else 0.0
    if sr > radius and sr > 1e-12:
        mat = mat * (radius / sr)
    return mat, sr


def fit_models(states_np, z_states, mean, basis, train_idx):
    x_t = np.concatenate([states_np[t][train_idx] for t in range(48)], axis=0)
    z_t = np.concatenate([z_states[t][train_idx] for t in range(48)], axis=0)
    z_next = np.concatenate([z_states[t + 1][train_idx] for t in range(48)], axis=0)

    proj_t = mean + z_t @ basis.T
    residual_t = x_t - proj_t

    phi_auto = np.concatenate([np.ones((len(z_t), 1)), z_t], axis=1)
    theta_auto, _, _, _ = np.linalg.lstsq(phi_auto, z_next, rcond=None)
    a_auto = theta_auto[0]
    F_auto = theta_auto[1:]
    F_auto, sr_auto = spectral_clip(F_auto)

    phi_obs = np.concatenate([np.ones((len(z_t), 1)), z_t, residual_t], axis=1)
    theta_obs, _, _, _ = np.linalg.lstsq(phi_obs, z_next, rcond=None)
    a_obs = theta_obs[0]
    F_obs = theta_obs[1:1 + z_t.shape[1]]
    C_obs = theta_obs[1 + z_t.shape[1]:]
    F_obs, sr_obs = spectral_clip(F_obs)

    return {
        "autonomous": {"name": "autonomous", "a": a_auto, "F": F_auto,
                       "C": np.zeros((basis.shape[0], basis.shape[1]), dtype=np.float64),
                       "spectral_radius": sr_auto},
        "observer": {"name": "observer", "a": a_obs, "F": F_obs, "C": C_obs,
                     "spectral_radius": sr_obs},
    }


def teacher_forced_track(model, states_np, subset_idx, mean, basis):
    z = (states_np[0][subset_idx] - mean) @ basis
    decoded = [mean + z @ basis.T]
    for step_t in range(48):
        x_hat = mean + z @ basis.T
        residual = states_np[step_t][subset_idx] - x_hat
        z = model["a"] + z @ model["F"] + residual @ model["C"]
        decoded.append(mean + z @ basis.T)
    return decoded


def summarize_track(decoded_states, states_np, subset_idx, X, y_pred, W_last, b_last):
    gt_states = [states_np[t][subset_idx] for t in range(49)]
    state_mse = float(np.mean([np.mean((decoded_states[t] - gt_states[t]) ** 2) for t in range(49)]))
    x_final = torch.tensor(decoded_states[-1], dtype=X.dtype)
    pred = predict_from_state(x_final, W_last, b_last).detach().cpu().numpy().astype(np.float64)
    pred_mse = float(np.mean((pred - y_pred[subset_idx].detach().cpu().numpy()) ** 2))
    return {"track_state_mse": state_mse, "final_prediction_mse": pred_mse}


@torch.no_grad()
def capture_states_from_input(x0, blocks, ordering):
    z = x0.clone()
    states = [z.clone()]
    for idx in ordering:
        z = blocks[idx](z)
        states.append(z.clone())
    return [s.detach().cpu().numpy().astype(np.float64) for s in states]


def shock_summary_from_states(shocked_states, base_states, subset_idx, X, W_last, b_last):
    response_norms = [
        float(np.linalg.norm(shocked_states[t][subset_idx] - base_states[t][subset_idx], axis=1).mean())
        for t in range(49)
    ]
    base_pred = predict_from_state(
        torch.tensor(base_states[-1][subset_idx], dtype=X.dtype), W_last, b_last
    ).detach().cpu().numpy()
    pred = predict_from_state(
        torch.tensor(shocked_states[-1][subset_idx], dtype=X.dtype), W_last, b_last
    ).detach().cpu().numpy()
    initial = max(response_norms[0], 1e-12)
    return {
        "damping_ratio": float(response_norms[-1] / initial),
        "mean_abs_pred_shift": float(np.mean(np.abs(pred - base_pred))),
        "peak_step": int(np.argmax(response_norms)),
    }


def shock_summary_from_decoded(decoded_states, decoded_base, X, W_last, b_last):
    response_norms = [
        float(np.linalg.norm(decoded_states[t] - decoded_base[t], axis=1).mean())
        for t in range(49)
    ]
    base_pred = predict_from_state(
        torch.tensor(decoded_base[-1], dtype=X.dtype), W_last, b_last
    ).detach().cpu().numpy()
    pred = predict_from_state(
        torch.tensor(decoded_states[-1], dtype=X.dtype), W_last, b_last
    ).detach().cpu().numpy()
    initial = max(response_norms[0], 1e-12)
    return {
        "damping_ratio": float(response_norms[-1] / initial),
        "mean_abs_pred_shift": float(np.mean(np.abs(pred - base_pred))),
        "peak_step": int(np.argmax(response_norms)),
    }


with Timer("Total") as t:
    print("\nLoading GT context...")
    X, y_pred, _ = load_data()
    pieces = load_all_pieces()
    pairing = list(GT_PAIRING_CANONICAL)
    blocks = [Block(inp, out, pieces) for inp, out in pairing]
    ordering = list(GT_ORDERING)
    last_data = pieces[LAST_PIECE]
    W_last = last_data["weight"]
    b_last = last_data["bias"]

    print("Capturing trajectory...")
    states_torch = run_order_capture(blocks, ordering, X)
    states_np = [s.detach().cpu().numpy().astype(np.float64) for s in states_torch]

    rng = np.random.default_rng(42)
    perm = rng.permutation(len(X))
    split = int(0.8 * len(X))
    train_idx = perm[:split]
    test_idx = perm[split:]

    shock_idx = test_idx[:min(SHOCK_ROWS, len(test_idx))]
    directions = build_direction_library(X, y_pred, top_feature_count=0, n_pca=3, n_noise=3)

    print(f"\nFitting models at ranks {RANKS}...")
    print(f"  {'Rank':>4} {'Model':>12} {'Track MSE':>12} {'Pred MSE':>12} {'Spec Radius':>12}")

    all_rank_results: list[dict] = []
    for rank in RANKS:
        mean, basis = fit_pca_basis(states_np, train_idx, rank)
        z_states = project_states_np(states_np, mean, basis)
        models = fit_models(states_np, z_states, mean, basis, train_idx)

        for name, model in models.items():
            tracked = teacher_forced_track(model, states_np, test_idx, mean, basis)
            metrics = summarize_track(tracked, states_np, test_idx, X, y_pred, W_last, b_last)
            all_rank_results.append({
                "rank": rank,
                "model": name,
                "track_state_mse": metrics["track_state_mse"],
                "final_prediction_mse": metrics["final_prediction_mse"],
                "spectral_radius": model["spectral_radius"],
            })
            print(f"  {rank:>4d} {name:>12s} {metrics['track_state_mse']:>12.6f} "
                  f"{metrics['final_prediction_mse']:>12.6f} {model['spectral_radius']:>12.4f}")

    # Best rank shock analysis
    print("\n--- Best Rank (rank=9) Detail ---")
    mean, basis = fit_pca_basis(states_np, train_idx, 9)
    z_states = project_states_np(states_np, mean, basis)
    models = fit_models(states_np, z_states, mean, basis, train_idx)

    auto_tracked = teacher_forced_track(models["autonomous"], states_np, test_idx, mean, basis)
    obs_tracked = teacher_forced_track(models["observer"], states_np, test_idx, mean, basis)
    auto_metrics = summarize_track(auto_tracked, states_np, test_idx, X, y_pred, W_last, b_last)
    obs_metrics = summarize_track(obs_tracked, states_np, test_idx, X, y_pred, W_last, b_last)
    print(f"  autonomous: pred_mse={auto_metrics['final_prediction_mse']:.6f}, "
          f"track_mse={auto_metrics['track_state_mse']:.6f}")
    print(f"  observer:   pred_mse={obs_metrics['final_prediction_mse']:.6f}, "
          f"track_mse={obs_metrics['track_state_mse']:.6f}")
    print(f"\n  Observer improvement on prediction MSE: "
          f"{auto_metrics['final_prediction_mse']:.4f} -> {obs_metrics['final_prediction_mse']:.4f}")

    # Shock fidelity comparison at rank 9
    print("\n--- Shock Fidelity (rank=9) ---")
    base_decoded_auto = teacher_forced_track(models["autonomous"], states_np, shock_idx, mean, basis)
    base_decoded_obs = teacher_forced_track(models["observer"], states_np, shock_idx, mean, basis)
    base_states_sub = [state[shock_idx] for state in states_np]

    shock_rows: list[dict] = []
    for item in directions:
        direction = torch.tensor(item["vector"], dtype=X.dtype).unsqueeze(0)
        epsilon = max(item["scale"], 1e-6) * 0.25
        shocked_input = X.index_select(0, torch.tensor(shock_idx, dtype=torch.long)) + epsilon * direction
        shocked_states = capture_states_from_input(shocked_input, blocks, ordering)
        gt_summary = shock_summary_from_states(
            shocked_states, base_states_sub, np.arange(len(shock_idx)), X, W_last, b_last,
        )
        auto_decoded = teacher_forced_track(models["autonomous"], shocked_states, np.arange(len(shock_idx)), mean, basis)
        obs_decoded = teacher_forced_track(models["observer"], shocked_states, np.arange(len(shock_idx)), mean, basis)
        auto_shock = shock_summary_from_decoded(auto_decoded, base_decoded_auto, X, W_last, b_last)
        obs_shock = shock_summary_from_decoded(obs_decoded, base_decoded_obs, X, W_last, b_last)
        shock_rows.append({
            "name": item["name"],
            "kind": item["kind"],
            "gt_damping": gt_summary["damping_ratio"],
            "gt_pred_shift": gt_summary["mean_abs_pred_shift"],
            "auto_damping_gap": abs(auto_shock["damping_ratio"] - gt_summary["damping_ratio"]),
            "auto_pred_shift_gap": abs(auto_shock["mean_abs_pred_shift"] - gt_summary["mean_abs_pred_shift"]),
            "obs_damping_gap": abs(obs_shock["damping_ratio"] - gt_summary["damping_ratio"]),
            "obs_pred_shift_gap": abs(obs_shock["mean_abs_pred_shift"] - gt_summary["mean_abs_pred_shift"]),
        })

    auto_mean_damp_gap = float(np.mean([r["auto_damping_gap"] for r in shock_rows]))
    auto_mean_pred_gap = float(np.mean([r["auto_pred_shift_gap"] for r in shock_rows]))
    obs_mean_damp_gap = float(np.mean([r["obs_damping_gap"] for r in shock_rows]))
    obs_mean_pred_gap = float(np.mean([r["obs_pred_shift_gap"] for r in shock_rows]))

    print(f"  Damping gap:     autonomous={auto_mean_damp_gap:.4f}  observer={obs_mean_damp_gap:.4f}")
    print(f"  Pred-shift gap:  autonomous={auto_mean_pred_gap:.6f}  observer={obs_mean_pred_gap:.6f}")
    damp_improvement = (1 - obs_mean_damp_gap / max(auto_mean_damp_gap, 1e-12)) * 100
    print(f"  Observer shock damping improvement: {damp_improvement:.1f}%")

# ── Write dashboard JSON ──────────────────────────────────────
DASH_DIR = os.path.join(os.path.dirname(__file__), '..', 'dashboard', 'static', 'data')
os.makedirs(DASH_DIR, exist_ok=True)

result_json = {
    "rank_results": all_rank_results,
    "best_rank": 9,
    "best_auto_pred_mse": auto_metrics["final_prediction_mse"],
    "best_obs_pred_mse": obs_metrics["final_prediction_mse"],
    "best_auto_track_mse": auto_metrics["track_state_mse"],
    "best_obs_track_mse": obs_metrics["track_state_mse"],
    "shock_fidelity": {
        "auto_mean_damping_gap": auto_mean_damp_gap,
        "obs_mean_damping_gap": obs_mean_damp_gap,
        "auto_mean_pred_shift_gap": auto_mean_pred_gap,
        "obs_mean_pred_shift_gap": obs_mean_pred_gap,
        "damping_improvement_pct": round(damp_improvement, 1),
    },
    "shock_rows": shock_rows,
    "elapsed_s": t.elapsed,
}

out_path = os.path.join(DASH_DIR, "distillation_03_latent_observer.json")
with open(out_path, "w") as f:
    json.dump(result_json, f, indent=1)
print(f"\nDashboard data -> {out_path}")
print(f"Done in {t.elapsed:.2f}s")
