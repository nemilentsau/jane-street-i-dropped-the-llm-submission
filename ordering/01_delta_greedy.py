"""Ordering Method 1: Delta-Greedy (Residual-Flow)

Greedy forward construction: at each step, pick the remaining block that
minimizes ||block(x) - x|| (the perturbation magnitude). Interprets residual
blocks as discrete ODE steps where early blocks make small corrections and
late blocks make larger ones.

The strongest raw extractor: 77/97 correct positions, MSE 0.000288.
Exact after greedy polish.
"""
import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

import torch
from shared import (
    Block, GT_PAIRING_CANONICAL, Timer, load_all_pieces, load_data,
    score_ordering, eval_solution,
)
from fusion_utils import mse_polish

print("=" * 60)
print("ORDERING METHOD 1: Delta-Greedy (Residual-Flow)")
print("=" * 60)

with Timer("Total") as t:
    print("\nLoading data and pieces...")
    X, y_pred, _ = load_data()
    pieces = load_all_pieces()
    pairing = list(GT_PAIRING_CANONICAL)

    print("Running delta-greedy ordering (with per-step margins)...")
    with Timer("  Delta-greedy"):
        # Run greedy manually to capture margin between best and second-best
        blocks = [Block(inp, out, pieces) for inp, out in pairing]
        remaining = set(range(len(blocks)))
        ordering = []
        greedy_steps = []  # {chosen_delta, second_delta, margin, n_remaining}
        current = X.clone()

        while remaining:
            candidates = []
            for idx in remaining:
                with torch.no_grad():
                    z = blocks[idx](current)
                    delta = (z - current).norm(dim=1).mean().item()
                candidates.append((delta, idx))
            candidates.sort()
            best_delta, best_idx = candidates[0]
            second_delta = candidates[1][0] if len(candidates) > 1 else best_delta
            greedy_steps.append({
                "chosen_delta": round(best_delta, 6),
                "second_delta": round(second_delta, 6),
                "margin": round(second_delta - best_delta, 6),
                "n_remaining": len(remaining),
            })
            ordering.append(best_idx)
            remaining.remove(best_idx)
            with torch.no_grad():
                current = blocks[best_idx](current)

    raw_mse = eval_solution(pairing, ordering, X, y_pred, pieces)
    raw_pos, _ = score_ordering(ordering, pairing)
    print("\n  Raw results:")
    print(f"    Correct positions: {raw_pos}/97")
    print(f"    MSE: {raw_mse:.6e}")

    print("\nRunning MSE polish (greedy pairwise swaps)...")
    with Timer("  Polish"):
        polished, polished_mse = mse_polish(pairing, ordering, X, y_pred, pieces, max_iters=5)

    polished_pos, _ = score_ordering(polished, pairing)
    print("\n  After polish:")
    print(f"    Correct positions: {polished_pos}/97")
    print(f"    MSE: {polished_mse:.6e}")

    # ── Per-block perturbation deltas in GT/polished order ──
    print("\nComputing per-block deltas along polished ordering...")
    deltas_polished = []
    current = X.clone()
    for idx in polished:
        with torch.no_grad():
            z = blocks[idx](current)
            d = (z - current).norm(dim=1).mean().item()
        deltas_polished.append(d)
        current = z

    # ── Greedy position vs GT position for each block ──
    gt_pos_of_block = {block_idx: pos for pos, block_idx in enumerate(polished)}
    greedy_vs_gt = [
        {"greedy": g_pos, "gt": gt_pos_of_block[block_idx]}
        for g_pos, block_idx in enumerate(ordering)
    ]

elapsed = t.elapsed
print(f"\nDone in {elapsed:.2f}s")

# ── Emit dashboard JSON ──────────────────────────────────────────────
DASHBOARD_DATA = os.path.join(
    os.path.dirname(__file__), "..", "dashboard", "static", "data"
)
os.makedirs(DASHBOARD_DATA, exist_ok=True)

artifact = {
    "method": "Delta-Greedy (Residual-Flow)",
    "script": "ordering/01_delta_greedy.py",
    "raw": {"correct_positions": raw_pos, "total_positions": 97, "mse": raw_mse},
    "polished": {"correct_positions": polished_pos, "total_positions": 97, "mse": polished_mse},
    "greedy_steps": greedy_steps,
    "deltas_polished": [round(d, 6) for d in deltas_polished],
    "greedy_vs_gt": greedy_vs_gt,
    "elapsed_s": round(elapsed, 2),
}

out_path = os.path.join(DASHBOARD_DATA, "ordering_01_delta_greedy.json")
with open(out_path, "w") as f:
    json.dump(artifact, f, separators=(",", ":"))

print(f"Dashboard artifact: {out_path} ({os.path.getsize(out_path) // 1024}KB)")
