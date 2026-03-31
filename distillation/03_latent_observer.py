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
import os, sys
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
    x_next = np.concatenate([states_np[t + 1][train_idx] for t in range(48)], axis=0)
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

    print(f"\nFitting models at ranks {RANKS}...")
    print(f"  {'Rank':>4} {'Model':>12} {'Track MSE':>12} {'Pred MSE':>12} {'Spec Radius':>12}")

    for rank in RANKS:
        mean, basis = fit_pca_basis(states_np, train_idx, rank)
        z_states = project_states_np(states_np, mean, basis)
        models = fit_models(states_np, z_states, mean, basis, train_idx)

        for name, model in models.items():
            tracked = teacher_forced_track(model, states_np, test_idx, mean, basis)
            metrics = summarize_track(tracked, states_np, test_idx, X, y_pred, W_last, b_last)
            print(f"  {rank:>4d} {name:>12s} {metrics['track_state_mse']:>12.6f} "
                  f"{metrics['final_prediction_mse']:>12.6f} {model['spectral_radius']:>12.4f}")

    # Best rank comparison
    print(f"\n--- Best Rank (rank=9) Detail ---")
    mean, basis = fit_pca_basis(states_np, train_idx, 9)
    z_states = project_states_np(states_np, mean, basis)
    models = fit_models(states_np, z_states, mean, basis, train_idx)

    for name, model in models.items():
        tracked = teacher_forced_track(model, states_np, test_idx, mean, basis)
        metrics = summarize_track(tracked, states_np, test_idx, X, y_pred, W_last, b_last)
        print(f"  {name:>12s}: pred_mse={metrics['final_prediction_mse']:.6f}, "
              f"track_mse={metrics['track_state_mse']:.6f}")

    improvement = None
    auto_tracked = teacher_forced_track(models["autonomous"], states_np, test_idx, mean, basis)
    obs_tracked = teacher_forced_track(models["observer"], states_np, test_idx, mean, basis)
    auto_metrics = summarize_track(auto_tracked, states_np, test_idx, X, y_pred, W_last, b_last)
    obs_metrics = summarize_track(obs_tracked, states_np, test_idx, X, y_pred, W_last, b_last)
    print(f"\n  Observer improvement on prediction MSE: "
          f"{auto_metrics['final_prediction_mse']:.4f} -> {obs_metrics['final_prediction_mse']:.4f}")

print(f"\nDone in {t.elapsed:.2f}s")
