"""Distillation 2: Shock Response Analysis

Injects calibrated shocks along different input directions and tracks
how the network responds through all 48 blocks:
- Top-PC (high-variance) shocks: amplified and carried through depth
- Bottom-PC (low-variance) shocks: damped immediately
- Prediction-shift gap: ~22x (top vs bottom)

The network selectively preserves factor-like directions and suppresses
nuisance directions, consistently across the input distribution.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

import numpy as np
import torch

from shared import Block, GT_ORDERING, GT_PAIRING_CANONICAL, LAST_PIECE, Timer, load_all_pieces, load_data
from dynamics_utils import (
    build_direction_library, build_regime_splits,
    run_order_capture, predict_from_state, shock_response_atlas, summarize_shock_groups,
)

print("=" * 60)
print("DISTILLATION 2: Shock Response Analysis")
print("=" * 60)

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

    print("Capturing base trajectory...")
    with Timer("  Trajectory capture"):
        base_states = run_order_capture(blocks, ordering, X)

    print("Building shock direction library...")
    directions = build_direction_library(X, y_pred, top_feature_count=8, n_pca=3, n_noise=3)
    print(f"  {len(directions)} directions: {sum(1 for d in directions if d['kind']=='feature')} features, "
          f"{sum(1 for d in directions if d['kind']=='pca_top')} top-PC, "
          f"{sum(1 for d in directions if d['kind']=='pca_bottom')} bottom-PC")

    print("\nRunning shock response atlas (all rows)...")
    with Timer("  Shock atlas"):
        results = shock_response_atlas(
            blocks, ordering, X, base_states, directions, W_last, b_last,
        )

    summary = summarize_shock_groups(results)
    print(f"\n--- Shock Response Summary ---")
    print(f"  {'Kind':<12} {'Count':>5} {'Damping':>10} {'Pred shift':>12} {'Peak step':>10}")
    for kind, s in sorted(summary.items()):
        print(f"  {kind:<12} {s['count']:>5d} {s['mean_damping_ratio']:>10.4f} "
              f"{s['mean_abs_pred_shift']:>12.6f} {s['mean_peak_step']:>10.1f}")

    top_shift = summary.get("pca_top", {}).get("mean_abs_pred_shift", 0)
    bot_shift = summary.get("pca_bottom", {}).get("mean_abs_pred_shift", 1e-12)
    print(f"\n  Prediction-shift gap (top/bottom): {top_shift/bot_shift:.1f}x")
    print(f"  Top-PC damping ratio: {summary.get('pca_top', {}).get('mean_damping_ratio', 0):.4f} (>1 = amplifying)")
    print(f"  Bottom-PC damping ratio: {summary.get('pca_bottom', {}).get('mean_damping_ratio', 0):.4f} (<1 = damping)")

    # Regime stability check
    print("\n--- Regime Stability ---")
    regime_data = build_regime_splits(X, y_pred)
    regimes = regime_data["regimes"]
    for regime_name, row_idx in sorted(regimes.items()):
        if regime_name == "all_rows":
            continue
        sub_results = shock_response_atlas(
            blocks, ordering, X, base_states, directions, W_last, b_last,
            subset_idx=row_idx,
        )
        sub_summary = summarize_shock_groups(sub_results)
        t_shift = sub_summary.get("pca_top", {}).get("mean_abs_pred_shift", 0)
        b_shift = sub_summary.get("pca_bottom", {}).get("mean_abs_pred_shift", 1e-12)
        t_damp = sub_summary.get("pca_top", {}).get("mean_damping_ratio", 0)
        b_damp = sub_summary.get("pca_bottom", {}).get("mean_damping_ratio", 0)
        print(f"  {regime_name:<20s}: top/bottom shift ratio={t_shift/b_shift:.1f}x, "
              f"top_damp={t_damp:.2f}, bot_damp={b_damp:.2f}")

print(f"\nDone in {t.elapsed:.2f}s")
