"""Shared helpers for pairing cost matrices and ordering methods."""
import numpy as np
import torch
from scipy.optimize import linear_sum_assignment

from shared import (
    Block,
    GT_ORDERING,
    INP_PIECES,
    LAST_PIECE,
    OUT_PIECES,
    eval_solution,
)


def robust_normalize(matrix):
    """Median/MAD normalization to align heterogeneous score matrices."""
    flat = matrix.reshape(-1)
    center = np.median(flat)
    mad = np.median(np.abs(flat - center))
    scale = mad if mad > 1e-12 else flat.std() + 1e-12
    return (matrix - center) / scale


def compute_weight_correlation_matrix(pieces):
    matrix = np.zeros((48, 48), dtype=np.float64)
    for i, inp_idx in enumerate(INP_PIECES):
        w_inp = pieces[inp_idx]["weight"]
        for j, out_idx in enumerate(OUT_PIECES):
            w_out = pieces[out_idx]["weight"]
            matrix[i, j] = (w_out.T * w_inp).sum().item()
    return matrix


def compute_effective_rank_matrix(pieces, progress_every=12):
    matrix = np.zeros((48, 48), dtype=np.float64)
    for i, inp_idx in enumerate(INP_PIECES):
        w_inp = pieces[inp_idx]["weight"].numpy()
        for j, out_idx in enumerate(OUT_PIECES):
            w_out = pieces[out_idx]["weight"].numpy()
            singular_values = np.linalg.svd(w_out @ w_inp, compute_uv=False)
            probs = singular_values / singular_values.sum()
            probs = probs[probs > 1e-10]
            matrix[i, j] = np.exp(-np.sum(probs * np.log(probs)))
        if progress_every and (i + 1) % progress_every == 0:
            print(f"  effective-rank rows: {i + 1}/48")
    return matrix


def compute_geodesic_matrix(pieces, progress_every=12):
    inp_subspaces = []
    for inp_idx in INP_PIECES:
        u, _, _ = torch.linalg.svd(pieces[inp_idx]["weight"], full_matrices=False)
        inp_subspaces.append(u)

    out_subspaces = []
    for out_idx in OUT_PIECES:
        u, _, _ = torch.linalg.svd(pieces[out_idx]["weight"].T, full_matrices=False)
        out_subspaces.append(u)

    matrix = np.zeros((48, 48), dtype=np.float64)
    for i, u_inp in enumerate(inp_subspaces):
        for j, u_out in enumerate(out_subspaces):
            singular_values = torch.linalg.svdvals(u_inp.T @ u_out).clamp(0.0, 1.0)
            matrix[i, j] = torch.acos(singular_values).norm().item()
        if progress_every and (i + 1) % progress_every == 0:
            print(f"  geodesic rows: {i + 1}/48")
    return matrix


def compute_single_block_mse_matrix(X_eval, y_eval, pieces, progress_every=12):
    matrix = np.zeros((48, 48), dtype=np.float64)
    last_data = pieces[LAST_PIECE]
    w_last, b_last = last_data["weight"], last_data["bias"]

    for i, inp_idx in enumerate(INP_PIECES):
        w_inp, b_inp = pieces[inp_idx]["weight"], pieces[inp_idx]["bias"]
        with torch.no_grad():
            hidden = torch.relu(X_eval @ w_inp.T + b_inp)
        for j, out_idx in enumerate(OUT_PIECES):
            w_out, b_out = pieces[out_idx]["weight"], pieces[out_idx]["bias"]
            with torch.no_grad():
                residual = hidden @ w_out.T + b_out
                z = X_eval + residual
                pred = (z @ w_last.T + b_last).squeeze()
            matrix[i, j] = ((pred - y_eval) ** 2).mean().item()
        if progress_every and (i + 1) % progress_every == 0:
            print(f"  single-block MSE rows: {i + 1}/48")
    return matrix


def pairing_from_cost(cost):
    row_ind, col_ind = linear_sum_assignment(cost)
    pairing = [(INP_PIECES[i], OUT_PIECES[j]) for i, j in zip(row_ind, col_ind)]
    return pairing, row_ind, col_ind


def assigned_row_top1_count(cost, col_ind):
    return int(sum(int(col_ind[i] == np.argmin(cost[i])) for i in range(len(col_ind))))


def assignment_row_gaps(cost, col_ind):
    gaps = np.zeros(len(col_ind), dtype=np.float64)
    for i, j in enumerate(col_ind):
        row = cost[i]
        best_other = np.min(np.delete(row, j))
        gaps[i] = best_other - row[j]
    return gaps


def delta_greedy_ordering(pairing, X, pieces):
    blocks = [Block(inp, out, pieces) for inp, out in pairing]
    remaining = set(range(len(blocks)))
    ordering = []
    current = X.clone()

    while remaining:
        best_delta = float("inf")
        best_idx = -1
        for idx in remaining:
            with torch.no_grad():
                z = blocks[idx](current)
                delta = (z - current).norm(dim=1).mean().item()
            if delta < best_delta:
                best_delta = delta
                best_idx = idx
        ordering.append(best_idx)
        remaining.remove(best_idx)
        with torch.no_grad():
            current = blocks[best_idx](current)
    return ordering


def pairwise_margin_data(pairing, X_sub, y_sub, pieces, progress_every=12):
    blocks = [Block(inp, out, pieces) for inp, out in pairing]
    last_data = pieces[LAST_PIECE]
    w_last, b_last = last_data["weight"], last_data["bias"]
    n = len(blocks)
    margin = np.zeros((n, n), dtype=np.float64)

    for i in range(n):
        for j in range(i + 1, n):
            with torch.no_grad():
                z_ab = blocks[j](blocks[i](X_sub))
                pred_ab = (z_ab @ w_last.T + b_last).squeeze()
                mse_ab = ((pred_ab - y_sub) ** 2).mean().item()

                z_ba = blocks[i](blocks[j](X_sub))
                pred_ba = (z_ba @ w_last.T + b_last).squeeze()
                mse_ba = ((pred_ba - y_sub) ** 2).mean().item()

            margin[i, j] = mse_ba - mse_ab
            margin[j, i] = -margin[i, j]
        if progress_every and (i + 1) % progress_every == 0:
            print(f"  pairwise-margin rows: {i + 1}/48")
    return margin


def pairwise_objective(ordering, margin):
    score = 0.0
    for pos_i, a in enumerate(ordering):
        for b in ordering[pos_i + 1:]:
            score += margin[a, b]
    return float(score)


def insertion_ordering(seed_nodes, margin):
    ordering = []
    for node in seed_nodes:
        best_pos = 0
        best_score = -float("inf")
        for pos in range(len(ordering) + 1):
            score = 0.0
            for left in ordering[:pos]:
                score += margin[left, node]
            for right in ordering[pos:]:
                score += margin[node, right]
            if score > best_score:
                best_score = score
                best_pos = pos
        ordering.insert(best_pos, node)
    return ordering


def refine_pairwise(ordering, margin, verbose=True):
    best = list(ordering)
    best_score = pairwise_objective(best, margin)
    improved = True
    iteration = 0

    while improved:
        improved = False
        iteration += 1
        for i in range(len(best)):
            for j in range(i + 1, len(best)):
                candidate = list(best)
                candidate[i], candidate[j] = candidate[j], candidate[i]
                score = pairwise_objective(candidate, margin)
                if score > best_score + 1e-12:
                    best = candidate
                    best_score = score
                    improved = True
        if verbose:
            print(f"    pairwise refine iter {iteration}: score={best_score:.6f}, improved={improved}")
    return best, best_score


def mse_polish(pairing, ordering, X, y_pred, pieces, max_iters=None, verbose=True):
    best = list(ordering)
    best_mse = eval_solution(pairing, best, X, y_pred, pieces)
    if verbose:
        print(f"    MSE polish start: {best_mse:.6e}")

    improved = True
    iteration = 0
    while improved:
        if max_iters is not None and iteration >= max_iters:
            break
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
        if verbose:
            print(f"    MSE polish iter {iteration}: mse={best_mse:.6e}, improved={improved}")
    return best, best_mse


def pairwise_accuracy(margin):
    pos = np.empty(len(GT_ORDERING), dtype=int)
    pos[GT_ORDERING] = np.arange(len(GT_ORDERING))
    correct = 0
    total = 0
    for i in range(len(GT_ORDERING)):
        for j in range(i + 1, len(GT_ORDERING)):
            truth = pos[i] < pos[j]
            pred = margin[i, j] > 0
            correct += int(pred == truth)
            total += 1
    return correct / total
