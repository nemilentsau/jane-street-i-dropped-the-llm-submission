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
from fusion_utils import delta_greedy_ordering, mse_polish

print("=" * 60)
print("ORDERING METHOD 1: Delta-Greedy (Residual-Flow)")
print("=" * 60)

with Timer("Total") as t:
    print("\nLoading data and pieces...")
    X, y_pred, _ = load_data()
    pieces = load_all_pieces()
    pairing = list(GT_PAIRING_CANONICAL)

    print("Running delta-greedy ordering...")
    with Timer("  Delta-greedy"):
        ordering = delta_greedy_ordering(pairing, X, pieces)

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

    # ── Per-block perturbation deltas (along greedy order) ──
    print("\nComputing per-block deltas along greedy ordering...")
    blocks = [Block(inp, out, pieces) for inp, out in pairing]
    deltas = []
    current = X.clone()
    for idx in ordering:
        with torch.no_grad():
            z = blocks[idx](current)
            delta = (z - current).norm(dim=1).mean().item()
        deltas.append(delta)
        current = z

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
    "deltas": [round(d, 6) for d in deltas],
    "elapsed_s": round(elapsed, 2),
}

out_path = os.path.join(DASHBOARD_DATA, "ordering_01_delta_greedy.json")
with open(out_path, "w") as f:
    json.dump(artifact, f, separators=(",", ":"))

print(f"Dashboard artifact: {out_path} ({os.path.getsize(out_path) // 1024}KB)")
