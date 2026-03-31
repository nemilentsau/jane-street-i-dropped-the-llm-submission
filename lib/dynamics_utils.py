"""Shared helpers for trajectory / dynamics / interpretability scripts."""

from __future__ import annotations

import numpy as np
import torch

from shared import Block, GT_ORDERING, GT_PAIRING_CANONICAL, LAST_PIECE, load_all_pieces, load_data


def load_gt_context():
    """Load GT blocks, data, and final readout."""
    X, y_pred, y_true = load_data()
    pieces = load_all_pieces()
    pairing = list(GT_PAIRING_CANONICAL)
    blocks = [Block(inp, out, pieces) for inp, out in pairing]
    last_data = pieces[LAST_PIECE]
    W_last = last_data["weight"]
    b_last = last_data["bias"]
    readout = W_last.squeeze(0).detach().cpu().numpy()
    return {
        "X": X,
        "y_pred": y_pred,
        "y_true": y_true,
        "pieces": pieces,
        "pairing": pairing,
        "ordering": list(GT_ORDERING),
        "blocks": blocks,
        "W_last": W_last,
        "b_last": b_last,
        "readout": readout,
    }


@torch.no_grad()
def run_order_capture(blocks, ordering, X):
    """Capture all states for a given ordering, including the input state."""
    states = []
    z = X.clone()
    states.append(z.clone())
    for idx in ordering:
        z = blocks[idx](z)
        states.append(z.clone())
    return states


@torch.no_grad()
def predict_from_state(state, W_last, b_last):
    return (state @ W_last.T + b_last).squeeze()


def compute_static_jacobians(X, pieces, pairing):
    """Compute average-gate Jacobians A_k = W_out diag(g) W_inp for GT block indices."""
    jacobians = []
    for inp_idx, out_idx in pairing:
        w_inp = pieces[inp_idx]["weight"]
        b_inp = pieces[inp_idx]["bias"]
        w_out = pieces[out_idx]["weight"]
        with torch.no_grad():
            pre = X @ w_inp.T + b_inp
            gate = (pre > 0).float().mean(dim=0)
            A = w_out @ torch.diag(gate) @ w_inp
        jacobians.append(A.detach().cpu().numpy())
    return jacobians


def compute_future_sensitivities(ordering, jacobians, readout):
    """Approximate output sensitivity at each state using static linearized future flow."""
    d = len(readout)
    I = np.eye(d)
    q = [None] * (len(ordering) + 1)
    q[-1] = readout.astype(np.float64).copy()
    for step in range(len(ordering) - 1, -1, -1):
        A = jacobians[ordering[step]]
        q[step] = ((I + A).T @ q[step + 1]).astype(np.float64)
    return q


def normalize(vec):
    vec = np.asarray(vec, dtype=np.float64)
    norm = np.linalg.norm(vec)
    if norm < 1e-12:
        return vec.copy(), norm
    return vec / norm, norm


def phase_slices(n_blocks):
    one_third = n_blocks // 3
    return {
        "early": range(0, one_third),
        "mid": range(one_third, 2 * one_third),
        "late": range(2 * one_third, n_blocks),
    }


def stack_states(states):
    """Stack all states across time and samples into a 2D numpy array."""
    arrays = []
    for state in states:
        arrays.append(state.detach().cpu().numpy())
    return np.concatenate(arrays, axis=0)


def compute_pca_basis(states, rank):
    """Compute a PCA basis from the concatenated state cloud."""
    cloud = stack_states(states).astype(np.float64)
    mean = cloud.mean(axis=0)
    centered = cloud - mean
    cov = centered.T @ centered / max(len(centered) - 1, 1)
    evals, evecs = np.linalg.eigh(cov)
    order = np.argsort(evals)[::-1]
    evals = evals[order]
    basis = evecs[:, order[:rank]]
    return {
        "mean": mean,
        "basis": basis,
        "eigenvalues": evals,
        "explained_ratio": evals / max(evals.sum(), 1e-12),
    }


def project_states(states, mean, basis):
    projected = []
    for state in states:
        arr = state.detach().cpu().numpy().astype(np.float64)
        projected.append((arr - mean) @ basis)
    return projected


def effective_rank_from_samples(samples):
    """Entropy effective rank of a centered sample cloud."""
    centered = samples - samples.mean(axis=0, keepdims=True)
    sv = np.linalg.svd(centered, compute_uv=False)
    if sv.sum() < 1e-12:
        return 0.0
    probs = sv / sv.sum()
    probs = probs[probs > 1e-12]
    return float(np.exp(-np.sum(probs * np.log(probs))))


def feature_target_correlations(X, y):
    X_np = X.detach().cpu().numpy().astype(np.float64)
    y_np = y.detach().cpu().numpy().astype(np.float64)
    X_c = X_np - X_np.mean(axis=0, keepdims=True)
    y_c = y_np - y_np.mean()
    x_std = X_c.std(axis=0) + 1e-12
    y_std = y_c.std() + 1e-12
    corr = (X_c * y_c[:, None]).mean(axis=0) / (x_std * y_std)
    return corr


def build_direction_library(X, y_pred, top_feature_count=8, n_pca=3, n_noise=3):
    """Construct a deterministic library of input-space shock directions."""
    X_np = X.detach().cpu().numpy().astype(np.float64)
    X_c = X_np - X_np.mean(axis=0, keepdims=True)
    cov = X_c.T @ X_c / max(len(X_c) - 1, 1)
    evals, evecs = np.linalg.eigh(cov)
    order = np.argsort(evals)[::-1]
    evals = evals[order]
    evecs = evecs[:, order]

    directions = []

    corrs = feature_target_correlations(X, y_pred)
    top_features = np.argsort(np.abs(corrs))[::-1][:top_feature_count]
    for feat in top_features:
        vec = np.zeros(X_np.shape[1], dtype=np.float64)
        vec[feat] = 1.0
        directions.append(
            {
                "name": f"feature_{feat}",
                "kind": "feature",
                "vector": vec,
                "scale": float(X_c[:, feat].std()),
                "score": float(abs(corrs[feat])),
            }
        )

    for i in range(min(n_pca, X_np.shape[1])):
        vec = evecs[:, i]
        directions.append(
            {
                "name": f"pc_top_{i + 1}",
                "kind": "pca_top",
                "vector": vec,
                "scale": float(np.sqrt(max(evals[i], 1e-12))),
                "score": float(evals[i]),
            }
        )

    for i in range(min(n_noise, X_np.shape[1])):
        vec = evecs[:, -(i + 1)]
        directions.append(
            {
                "name": f"pc_bottom_{i + 1}",
                "kind": "pca_bottom",
                "vector": vec,
                "scale": float(np.sqrt(max(evals[-(i + 1)], 1e-12))),
                "score": float(evals[-(i + 1)]),
            }
        )

    for item in directions:
        item["vector"], _ = normalize(item["vector"])

    return directions


def build_regime_splits(X, y_pred, quantiles=(0.25, 0.75)):
    """Build deterministic easy/hard row subsets used by regime analyses."""
    q_low, q_high = quantiles

    X_np = X.detach().cpu().numpy().astype(np.float64)
    y_np = y_pred.detach().cpu().numpy().astype(np.float64)
    input_norm = np.linalg.norm(X_np, axis=1)

    pca = compute_pca_basis([X], rank=1)
    pc1_scores = (X_np - pca["mean"]) @ pca["basis"]
    pc1_scores = pc1_scores[:, 0]

    q_abs_pred = np.quantile(np.abs(y_np), [q_low, q_high])
    q_input = np.quantile(input_norm, [q_low, q_high])
    q_pc1 = np.quantile(pc1_scores, [q_low, q_high])

    regimes = {
        "all_rows": np.arange(len(X_np)),
        "abs_pred_low": np.where(np.abs(y_np) <= q_abs_pred[0])[0],
        "abs_pred_high": np.where(np.abs(y_np) >= q_abs_pred[1])[0],
        "input_norm_low": np.where(input_norm <= q_input[0])[0],
        "input_norm_high": np.where(input_norm >= q_input[1])[0],
        "pc1_low": np.where(pc1_scores <= q_pc1[0])[0],
        "pc1_high": np.where(pc1_scores >= q_pc1[1])[0],
    }

    return {
        "regimes": regimes,
        "metadata": {
            "quantiles": {"low": float(q_low), "high": float(q_high)},
            "thresholds": {
                "abs_pred": [float(q_abs_pred[0]), float(q_abs_pred[1])],
                "input_norm": [float(q_input[0]), float(q_input[1])],
                "pc1": [float(q_pc1[0]), float(q_pc1[1])],
            },
        },
    }


@torch.no_grad()
def shock_response_atlas(
    blocks,
    ordering,
    X,
    base_states,
    directions,
    W_last,
    b_last,
    subset_idx=None,
    eps_scale=0.25,
):
    """Inject shocks and summarize how the state trajectory responds."""
    if subset_idx is None:
        subset_idx_t = None
    else:
        subset_idx_t = torch.as_tensor(subset_idx, dtype=torch.long)

    base_pred = predict_from_state(base_states[-1], W_last, b_last)
    if subset_idx_t is not None:
        base_pred = base_pred.index_select(0, subset_idx_t)

    def maybe_subset(tensor):
        if subset_idx_t is None:
            return tensor
        return tensor.index_select(0, subset_idx_t)

    results = []
    for item in directions:
        direction = torch.tensor(item["vector"], dtype=X.dtype).unsqueeze(0)
        epsilon = max(item["scale"], 1e-6) * eps_scale
        z = X + epsilon * direction

        response_norms = []
        response = maybe_subset(z - base_states[0])
        response_norms.append(float(response.norm(dim=1).mean().item()))

        for step, block_idx in enumerate(ordering):
            z = blocks[block_idx](z)
            response = maybe_subset(z - base_states[step + 1])
            response_norms.append(float(response.norm(dim=1).mean().item()))

        pred_shift = maybe_subset(predict_from_state(z, W_last, b_last)) - base_pred
        initial_norm = max(response_norms[0], 1e-12)
        final_norm = response_norms[-1]

        results.append(
            {
                "name": item["name"],
                "kind": item["kind"],
                "epsilon": float(epsilon),
                "initial_norm": float(initial_norm),
                "final_norm": float(final_norm),
                "damping_ratio": float(final_norm / initial_norm),
                "max_norm": float(max(response_norms)),
                "peak_step": int(np.argmax(response_norms)),
                "mean_abs_pred_shift": float(pred_shift.abs().mean().item()),
                "signed_pred_shift": float(pred_shift.mean().item()),
                "response_norms": response_norms,
                "phase_means": {
                    "early": float(np.mean(response_norms[:17])),
                    "mid": float(np.mean(response_norms[17:33])),
                    "late": float(np.mean(response_norms[33:])),
                },
            }
        )

    return results


def summarize_shock_groups(results):
    """Aggregate shock metrics by direction family."""
    group_rows = {}
    for row in results:
        group_rows.setdefault(row["kind"], []).append(row)

    summary = {}
    for kind, rows in group_rows.items():
        summary[kind] = {
            "count": int(len(rows)),
            "mean_damping_ratio": float(np.mean([r["damping_ratio"] for r in rows])),
            "mean_abs_pred_shift": float(np.mean([r["mean_abs_pred_shift"] for r in rows])),
            "mean_peak_step": float(np.mean([r["peak_step"] for r in rows])),
        }
    return summary
