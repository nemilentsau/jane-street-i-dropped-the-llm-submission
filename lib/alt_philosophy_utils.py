"""Shared helpers for alternative-philosophy experiments."""
import itertools

import numpy as np
import torch

from fusion_utils import assigned_row_top1_count, delta_greedy_ordering, mse_polish, pairing_from_cost
from shared import GT_ORDERING, score_ordering, eval_solution, score_pairing


DEFAULT_WEIGHT_GRID = [0.25, 0.5, 1.0, 2.0, 3.0]


def recipe_name(names, weights):
    return " + ".join(f"{weight:g}*{name}" for name, weight in zip(names, weights))


def evaluate_pairing_cost(cost, X, y_pred, pieces):
    pairing, _, col_ind = pairing_from_cost(cost)
    return {
        "pairing": pairing,
        "correct_pairs": score_pairing(pairing),
        "row_top1": assigned_row_top1_count(cost, col_ind),
        "gt_order_mse": eval_solution(pairing, GT_ORDERING, X, y_pred, pieces),
    }


def search_weighted_recipes(costs, recipes, X, y_pred, pieces, weight_grid=None):
    if weight_grid is None:
        weight_grid = DEFAULT_WEIGHT_GRID

    results = []
    for names in recipes:
        for weights in itertools.product(weight_grid, repeat=len(names)):
            cost = sum(weight * costs[name] for name, weight in zip(names, weights))
            metrics = evaluate_pairing_cost(cost, X, y_pred, pieces)
            metrics.update(
                {
                    "names": names,
                    "weights": tuple(float(w) for w in weights),
                    "recipe": recipe_name(names, weights),
                }
            )
            results.append(metrics)

    results.sort(
        key=lambda item: (
            -item["correct_pairs"],
            item["gt_order_mse"],
            -item["row_top1"],
            item["recipe"],
        )
    )
    return results


def end_to_end_from_pairing(pairing, X, y_pred, pieces, polish_iters=2):
    ordering_delta = delta_greedy_ordering(pairing, X, pieces)
    mse_delta = eval_solution(pairing, ordering_delta, X, y_pred, pieces)
    polished_ordering, polished_mse = mse_polish(
        pairing,
        ordering_delta,
        X,
        y_pred,
        pieces,
        max_iters=polish_iters,
        verbose=False,
    )
    return {
        "ordering_delta": ordering_delta,
        "mse_delta": mse_delta,
        "polished_ordering": polished_ordering,
        "polished_mse": polished_mse,
    }


def singular_value_features(sv, exp_alpha=0.25):
    sv = np.asarray(sv, dtype=np.float64)
    total = sv.sum() + 1e-12
    probs = sv / total
    probs = np.clip(probs, 1e-12, None)
    idx = np.arange(len(sv), dtype=np.float64)
    ref = np.exp(-exp_alpha * idx)
    ref = ref / ref.sum()

    features = {
        "effective_rank": float(np.exp(-np.sum(probs * np.log(probs)))),
        "stable_rank": float((sv**2).sum() / (sv[0] ** 2 + 1e-12)),
        "neg_top1_share": float(-(sv[0] / total)),
        "neg_top4_share": float(-(sv[:4].sum() / total)),
        "kl_to_exp": float(np.sum(probs * (np.log(probs) - np.log(ref)))),
    }
    return features


def operator_moment_features(matrix):
    matrix = np.asarray(matrix, dtype=np.float64)
    sv = np.linalg.svd(matrix, compute_uv=False)
    sym = 0.5 * (matrix + matrix.T)
    skew = 0.5 * (matrix - matrix.T)

    features = singular_value_features(sv)
    features.update(
        {
            "trace_abs": float(-abs(np.trace(matrix))),
            "tr2_abs": float(-abs(np.trace(matrix @ matrix))),
            "tr3_abs": float(-abs(np.trace(matrix @ matrix @ matrix))),
            "sym_ratio": float(
                -np.linalg.norm(sym, ord="fro") / (np.linalg.norm(skew, ord="fro") + 1e-12)
            ),
        }
    )
    return features


def affine_features(matrix, offset, w_last):
    matrix = np.asarray(matrix, dtype=np.float64)
    offset = np.asarray(offset, dtype=np.float64)
    w_last = np.asarray(w_last, dtype=np.float64)

    offset_norm = np.linalg.norm(offset)
    last_proj = float(np.dot(w_last, offset))
    quad = float(offset @ matrix @ offset)

    features = operator_moment_features(matrix)
    features.update(
        {
            "c_norm": float(offset_norm),
            "c_rel_last": float(abs(last_proj) / (np.linalg.norm(w_last) * (offset_norm + 1e-12))),
            "c_quad_abs": float(abs(quad) / (offset_norm**2 + 1e-12)),
        }
    )
    return features


def best_order_from_margin(pairing, margin, X, y_pred, pieces):
    from fusion_utils import insertion_ordering, refine_pairwise

    seed_nodes = np.argsort(-margin.sum(axis=1)).tolist()
    ordering_insert = insertion_ordering(seed_nodes, margin)
    ordering_refined, pairwise_score = refine_pairwise(ordering_insert, margin, verbose=False)
    raw_mse = eval_solution(pairing, ordering_refined, X, y_pred, pieces)
    raw_positions = score_ordering(ordering_refined, pairing)[0]
    return {
        "ordering": ordering_refined,
        "pairwise_score": pairwise_score,
        "raw_mse": raw_mse,
        "raw_positions": raw_positions,
    }
