"""Ordering Overview: Basin Comparison

Re-derives all 5 raw orderings, then computes:
  - Pairwise Kendall tau distance matrix (methods + GT + random baselines)
  - Per-block displacement from GT position for each method
  - Polish path tracking: ordering at each iteration, distance to GT over time
"""
from __future__ import annotations

import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

import numpy as np
import torch
from scipy.optimize import linear_sum_assignment
from shared import (
    GT_ORDERING, GT_PAIRING_CANONICAL, Timer, load_all_pieces, load_data,
    score_ordering, eval_solution,
)
from fusion_utils import (
    delta_greedy_ordering, pairwise_margin_data, insertion_ordering,
    refine_pairwise, insertion_beam,
)

DASH_DIR = os.path.join(os.path.dirname(__file__), '..', 'dashboard', 'static', 'data')

print("=" * 60)
print("ORDERING OVERVIEW: Basin Comparison")
print("=" * 60)

N_BLOCKS = 48


# ── Spectral flow (inline, same as 05) ───────────────────────
def compute_linearized_jacobians(pairing, X, pieces):
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


def spectral_flow_greedy(jacobians):
    d = jacobians[0].shape[0]
    eye = np.eye(d)
    J = eye.copy()
    remaining = set(range(N_BLOCKS))
    ordering: list[int] = []
    prev_eigvals = np.sort(np.abs(np.linalg.eigvals(J)))
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
    return ordering


# ── Sinkhorn ranking (inline, same as 03) ─────────────────────
def sinkhorn(log_alpha, n_iters=30):
    for _ in range(n_iters):
        log_alpha = log_alpha - torch.logsumexp(log_alpha, dim=1, keepdim=True)
        log_alpha = log_alpha - torch.logsumexp(log_alpha, dim=0, keepdim=True)
    return torch.exp(log_alpha)


def expected_pairwise_score(Q, margin):
    suffix = torch.cumsum(Q.flip(0), dim=0).flip(0) - Q
    score = torch.tensor(0.0, dtype=Q.dtype)
    for pos in range(Q.shape[0] - 1):
        score = score + Q[pos] @ margin @ suffix[pos]
    return score


def sinkhorn_ordering(margin_np):
    margin_t = torch.tensor(margin_np, dtype=torch.float32)
    best_mse_seed = float("inf")
    best_ordering: list[int] = []
    for seed in range(5):
        torch.manual_seed(seed)
        log_order = torch.nn.Parameter(torch.randn(48, 48) * 0.1)
        optimizer = torch.optim.Adam([log_order], lr=0.3)
        best_score = -float("inf")
        best_soft = None
        for epoch in range(200):
            tau = max(0.03, 1.0 * (0.985 ** epoch))
            Q = sinkhorn(log_order / tau)
            score = expected_pairwise_score(Q, margin_t)
            loss = -score
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            if score.item() > best_score:
                best_score = score.item()
                best_soft = Q.detach().clone()
        assert best_soft is not None
        soft_np = best_soft.numpy()
        _, col_ind = linear_sum_assignment(-soft_np)
        ordering = col_ind.tolist()
        # Use pairwise score as proxy (cheaper than eval_solution for seed selection)
        pw = sum(margin_np[ordering[i], ordering[j]]
                 for i in range(len(ordering)) for j in range(i + 1, len(ordering)))
        if seed == 0 or pw > best_mse_seed:
            best_mse_seed = pw
            best_ordering = ordering
        print(f"    sinkhorn seed={seed}, pw_score={pw:.3f}")
    return best_ordering


# ── Distance metrics ─────────��────────────────────────────────
def kendall_tau_distance(a: list[int], b: list[int]) -> int:
    """Number of pairwise inversions between two permutations."""
    n = len(a)
    pos_a = [0] * n
    pos_b = [0] * n
    for i in range(n):
        pos_a[a[i]] = i
        pos_b[b[i]] = i
    count = 0
    for i in range(n):
        for j in range(i + 1, n):
            if (pos_a[i] - pos_a[j]) * (pos_b[i] - pos_b[j]) < 0:
                count += 1
    return count


def cayley_distance(a: list[int], b: list[int]) -> int:
    """Minimum number of transpositions to transform a into b."""
    n = len(a)
    pos_b = [0] * n
    for i in range(n):
        pos_b[b[i]] = i
    # Compose: perm[i] = where a[i] lands in b's ordering
    perm = [pos_b[a[i]] for i in range(n)]
    # Cayley distance = n - number of cycles
    visited = [False] * n
    n_cycles = 0
    for i in range(n):
        if not visited[i]:
            n_cycles += 1
            j = i
            while not visited[j]:
                visited[j] = True
                j = perm[j]
    return n - n_cycles


def block_displacement(ordering: list[int], gt: list[int]) -> list[int]:
    """For each block, |position in ordering - position in GT|."""
    gt_pos = {block: pos for pos, block in enumerate(gt)}
    return [abs(pos - gt_pos[block]) for pos, block in enumerate(ordering)]


# ── Polish with path tracking ─────────────────────────────────
def polish_with_path(pairing, ordering, X, y_pred, pieces, max_iters=10):
    """Polish and record ordering + distance to GT at each step."""
    best = list(ordering)
    best_mse = eval_solution(pairing, best, X, y_pred, pieces)
    kt_dist = kendall_tau_distance(best, GT_ORDERING)
    cy_dist = cayley_distance(best, GT_ORDERING)
    pos, _ = score_ordering(best, pairing)

    path: list[dict] = [{
        "iteration": 0, "mse": best_mse,
        "kendall_tau": kt_dist, "cayley": cy_dist,
        "correct_positions": pos,
        "ordering": list(best),
    }]

    for iteration in range(1, max_iters + 1):
        improved = False
        for i in range(len(best)):
            for j in range(i + 1, len(best)):
                candidate = list(best)
                candidate[i], candidate[j] = candidate[j], candidate[i]
                mse = eval_solution(pairing, candidate, X, y_pred, pieces)
                if mse < best_mse - 1e-10:
                    best = candidate
                    best_mse = mse
                    improved = True

        kt_dist = kendall_tau_distance(best, GT_ORDERING)
        cy_dist = cayley_distance(best, GT_ORDERING)
        pos, _ = score_ordering(best, pairing)
        path.append({
            "iteration": iteration, "mse": best_mse,
            "kendall_tau": kt_dist, "cayley": cy_dist,
            "correct_positions": pos,
            "ordering": list(best),
        })
        print(f"      iter {iteration}: mse={best_mse:.6e},"
              f" kendall={kt_dist}, cayley={cy_dist}, pos={pos}/97")
        if not improved:
            break

    return path


with Timer("Total") as t:
    print("\nLoading data and pieces...")
    X, y_pred, _ = load_data()
    pieces = load_all_pieces()
    pairing = list(GT_PAIRING_CANONICAL)
    X_sub = X[:2000]
    y_sub = y_pred[:2000]

    # ── Re-derive all 5 raw orderings ──────────────────────────
    raw_orderings: dict[str, list[int]] = {}

    print("\n01 Delta Greedy...")
    with Timer("  01"):
        raw_orderings["01_delta_greedy"] = delta_greedy_ordering(pairing, X, pieces)

    print("\n02 Pairwise Tournament...")
    with Timer("  02 margins"):
        margin = pairwise_margin_data(pairing, X_sub, y_sub, pieces)
    seed_nodes = np.argsort(-margin.sum(axis=1)).tolist()
    ordering_insert = insertion_ordering(seed_nodes, margin)
    ordering_refined, _ = refine_pairwise(ordering_insert, margin, verbose=False)
    raw_orderings["02_pairwise"] = ordering_refined

    print("\n03 Sinkhorn Ranking...")
    with Timer("  03"):
        raw_orderings["03_sinkhorn"] = sinkhorn_ordering(margin)

    print("\n04 Beam Search (w=5)...")
    with Timer("  04"):
        beam_ord, _ = insertion_beam(seed_nodes, margin, 5, progress_every=None)
    raw_orderings["04_beam"] = beam_ord

    print("\n05 Spectral Flow...")
    with Timer("  05"):
        jacobians = compute_linearized_jacobians(pairing, X, pieces)
        raw_orderings["05_spectral"] = spectral_flow_greedy(jacobians)

    # ── Random baselines ───────���──────────────────────────────
    import random as _rng
    for seed in range(5):
        _rng.seed(seed)
        rand = list(range(N_BLOCKS))
        _rng.shuffle(rand)
        raw_orderings[f"random_{seed}"] = rand

    method_names = list(raw_orderings.keys())
    all_names = ["gt"] + method_names
    all_orderings = [GT_ORDERING] + [raw_orderings[n] for n in method_names]

    # ── Raw MSE and positions ──────────────────────────────────
    print("\nRaw MSE and positions...")
    raw_stats: dict[str, dict] = {}
    for name, ordering in zip(all_names, all_orderings):
        mse = eval_solution(pairing, ordering, X, y_pred, pieces)
        pos, _ = score_ordering(ordering, pairing)
        raw_stats[name] = {"mse": mse, "correct_positions": pos}
        print(f"  {name}: mse={mse:.6e}, pos={pos}/97")

    # ── Pairwise distance matrix ���─────────────────────────────
    print("\nPairwise distance matrix...")
    n_all = len(all_orderings)
    kendall_matrix = [[0] * n_all for _ in range(n_all)]
    cayley_matrix = [[0] * n_all for _ in range(n_all)]

    for i in range(n_all):
        for j in range(i + 1, n_all):
            kt = kendall_tau_distance(all_orderings[i], all_orderings[j])
            cy = cayley_distance(all_orderings[i], all_orderings[j])
            kendall_matrix[i][j] = kt
            kendall_matrix[j][i] = kt
            cayley_matrix[i][j] = cy
            cayley_matrix[j][i] = cy

    print("  Distances to GT (Kendall / Cayley):")
    for i, name in enumerate(all_names):
        if name == "gt":
            continue
        print(f"    {name}: {kendall_matrix[0][i]} / {cayley_matrix[0][i]}")

    # ── Block displacement from GT ─────────────────────────────
    print("\nBlock displacement from GT...")
    displacement: dict[str, list[int]] = {}
    for name in method_names:
        if name.startswith("random"):
            continue
        disp = block_displacement(raw_orderings[name], GT_ORDERING)
        displacement[name] = disp
        mean_disp = np.mean(disp)
        max_disp = max(disp)
        print(f"  {name}: mean={mean_disp:.1f}, max={max_disp}")

    # ── Polish path tracking (methods only, limited iters) ─────
    print("\nPolish path tracking...")
    method_keys = [n for n in method_names if not n.startswith("random")]
    polish_paths: dict[str, list[dict]] = {}

    for name in method_keys:
        print(f"  {name}:")
        path = polish_with_path(pairing, raw_orderings[name], X, y_pred,
                                pieces, max_iters=10)
        # Strip full ordering from path to keep JSON small
        polish_paths[name] = [{
            "iteration": p["iteration"],
            "mse": p["mse"],
            "kendall_tau": p["kendall_tau"],
            "cayley": p["cayley"],
            "correct_positions": p["correct_positions"],
        } for p in path]

    # ── Random polish path (one seed for comparison) ───────────
    print("\n  random_0:")
    rand_path = polish_with_path(pairing, raw_orderings["random_0"], X, y_pred,
                                 pieces, max_iters=10)
    polish_paths["random_0"] = [{
        "iteration": p["iteration"],
        "mse": p["mse"],
        "kendall_tau": p["kendall_tau"],
        "cayley": p["cayley"],
        "correct_positions": p["correct_positions"],
    } for p in rand_path]

# ── Write dashboard JSON ──────────────────────────────────────
result = {
    "method_names": all_names,
    "raw_stats": raw_stats,
    "kendall_matrix": kendall_matrix,
    "cayley_matrix": cayley_matrix,
    "displacement": displacement,
    "polish_paths": polish_paths,
    "elapsed_s": t.elapsed,
}

os.makedirs(DASH_DIR, exist_ok=True)
out_path = os.path.join(DASH_DIR, "ordering_00_overview.json")
with open(out_path, "w") as f:
    json.dump(result, f, indent=1)
print(f"\nDashboard data -> {out_path}")
print(f"Done in {t.elapsed:.2f}s")
