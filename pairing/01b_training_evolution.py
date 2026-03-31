"""Pairing 01b: Training Evolution

Trains a fresh 48-block residual network from scratch on the historical data
and tracks the emergence of the Frobenius weight-correlation pairing signal
at several checkpoints. Also evaluates 10 random untrained networks as control.

Demonstrates that the pairing fingerprint is created by SGD, not architecture.
"""

import json
import os
import sys

import numpy as np
import torch
import torch.nn as nn
from scipy.optimize import linear_sum_assignment
from torch.utils.data import DataLoader, TensorDataset

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from shared import (
    GT_PAIR_MAP,
    INP_PIECES,
    OUT_PIECES,
    Timer,
    load_all_pieces,
    load_data,
)
from fusion_utils import compute_weight_correlation_matrix, pairing_from_cost

DASHBOARD_DATA = os.path.join(
    os.path.dirname(__file__), "..", "dashboard", "static", "data"
)

CHECKPOINT_EPOCHS = [0, 2, 5, 10, 20, 60]
N_RANDOM = 10
SEED = 42

D_IN, D_HIDDEN, N_BLOCKS = 48, 96, 48
BATCH_SIZE, LR, WEIGHT_DECAY, GRAD_CLIP = 1024, 1e-3, 1e-5, 1.0


# ── Model ────────────────────────────────────────────────────────────


class ResBlock(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.inp = nn.Linear(D_IN, D_HIDDEN)
        self.out = nn.Linear(D_HIDDEN, D_IN)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.out(torch.relu(self.inp(x)))


class ResidualNet(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.blocks = nn.ModuleList([ResBlock() for _ in range(N_BLOCKS)])
        self.readout = nn.Linear(D_IN, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        for block in self.blocks:
            x = block(x)
        return self.readout(x).squeeze(-1)


# ── Evaluation ───────────────────────────────────────────────────────


def frobenius_pairing(model: ResidualNet) -> tuple[int, float]:
    """Frobenius correlation pairing on a model's own blocks.

    Correct means block i's inp is paired with block i's out (diagonal).
    Returns (n_correct, snr).
    """
    n = len(model.blocks)
    inp_w: list[np.ndarray] = []
    out_w: list[np.ndarray] = []
    for k in range(n):
        block = model.blocks[k]
        assert isinstance(block, ResBlock)
        inp_w.append(block.inp.weight.detach().cpu().numpy())
        out_w.append(block.out.weight.detach().cpu().numpy())

    corr = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            corr[i, j] = abs(np.trace(out_w[j] @ inp_w[i]))

    row_ind, col_ind = linear_sum_assignment(-corr)
    n_correct = int(sum(1 for r, c in zip(row_ind, col_ind) if r == c))

    diag = np.array([corr[i, i] for i in range(n)])
    offdiag = np.array(
        [corr[i, j] for i in range(n) for j in range(n) if i != j]
    )
    mean_off = float(np.mean(offdiag))
    snr = round(float(np.mean(diag) / mean_off), 2) if mean_off > 0 else 1.0

    return n_correct, snr


def compute_trained_baseline() -> tuple[int, float]:
    """Pairing stats from the original dropped model's pieces."""
    pieces = load_all_pieces()
    corr = np.abs(compute_weight_correlation_matrix(pieces))
    _, row_ind, col_ind = pairing_from_cost(-corr)

    n_correct = sum(
        1
        for i, j in zip(row_ind, col_ind)
        if GT_PAIR_MAP.get(INP_PIECES[i]) == OUT_PIECES[j]
    )

    correct_scores = []
    incorrect_scores = []
    for i, inp_idx in enumerate(INP_PIECES):
        for j, out_idx in enumerate(OUT_PIECES):
            if GT_PAIR_MAP.get(inp_idx) == out_idx:
                correct_scores.append(float(corr[i, j]))
            else:
                incorrect_scores.append(float(corr[i, j]))

    snr = round(float(np.mean(correct_scores) / np.mean(incorrect_scores)), 2)
    return n_correct, snr


# ── Main ─────────────────────────────────────────────────────────────

print("=" * 60)
print("PAIRING 01b: Training Evolution")
print("=" * 60)

with Timer("Total") as t:
    print("\nLoading data...")
    X, _, y_true = load_data()
    dataset = TensorDataset(X, y_true)
    loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)

    # ── Trained baseline ──
    print("Computing trained baseline (puzzle pieces)...")
    baseline_correct, baseline_snr = compute_trained_baseline()
    print(f"  Original model: {baseline_correct}/48 pairs, {baseline_snr}x SNR")

    # ── Training evolution ──
    max_epoch = max(CHECKPOINT_EPOCHS)
    print(f"\nTraining fresh network for {max_epoch} epochs...")
    torch.manual_seed(SEED)
    model = ResidualNet()
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY
    )
    criterion = nn.MSELoss()

    curve: list[dict[str, object]] = []

    for epoch in range(max_epoch + 1):
        if epoch in CHECKPOINT_EPOCHS:
            with torch.no_grad():
                pred_all = model(X)
                mse_val = float(criterion(pred_all, y_true))
            n_correct, snr = frobenius_pairing(model)
            curve.append(
                {
                    "epoch": epoch,
                    "pairs_correct": n_correct,
                    "snr": snr,
                    "mse": round(mse_val, 4),
                }
            )
            print(
                f"  Epoch {epoch:3d}: {n_correct}/48 pairs, "
                f"SNR {snr}x, MSE {mse_val:.4f}"
            )

        if epoch < max_epoch:
            model.train()
            for xb, yb in loader:
                optimizer.zero_grad()
                loss = criterion(model(xb), yb)
                loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), GRAD_CLIP)
                optimizer.step()

    # ── Random control ──
    print(f"\nEvaluating {N_RANDOM} random untrained networks...")
    random_results: list[dict[str, object]] = []
    for seed in range(N_RANDOM):
        torch.manual_seed(seed * 1000)
        rnd = ResidualNet()
        nc, rsnr = frobenius_pairing(rnd)
        random_results.append({"seed": seed, "pairs_correct": nc, "snr": rsnr})
        print(f"  Random {seed}: {nc}/48 pairs, SNR {rsnr}x")

    mean_correct = round(
        float(np.mean([r["pairs_correct"] for r in random_results])), 1
    )
    mean_snr = round(float(np.mean([r["snr"] for r in random_results])), 2)
    print(f"  Random mean: {mean_correct}/48 pairs, SNR {mean_snr}x")

elapsed = t.elapsed
print(f"\nDone in {elapsed:.1f}s")

# ── Emit dashboard JSON ──────────────────────────────────────────────
os.makedirs(DASHBOARD_DATA, exist_ok=True)

artifact = {
    "script": "pairing/01b_training_evolution.py",
    "training_curve": curve,
    "random_control": {
        "n_networks": N_RANDOM,
        "mean_correct": mean_correct,
        "mean_snr": mean_snr,
        "results": random_results,
    },
    "trained_baseline": {
        "pairs_correct": baseline_correct,
        "snr": baseline_snr,
    },
    "elapsed_s": round(elapsed, 1),
}

out_path = os.path.join(DASHBOARD_DATA, "pairing_01b_training_evolution.json")
with open(out_path, "w") as f:
    json.dump(artifact, f, separators=(",", ":"))

print(f"Dashboard artifact: {out_path} ({os.path.getsize(out_path) // 1024}KB)")
