"""Shared utilities for all scripts."""
import os
import time

import pandas as pd
import torch
import torch.nn as nn

# Ensure we can find the data directory regardless of where the script is run from.
# Convention: model/ lives at the project root (next to lib/, pairing/, etc.)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(_PROJECT_ROOT, "model"))

INP_PIECES = [0,1,2,3,4,5,10,13,14,15,16,18,23,27,28,31,35,37,39,41,42,43,44,45,48,49,50,56,58,59,60,61,62,64,65,68,69,73,74,77,81,84,86,87,88,91,94,95]
OUT_PIECES = [6,7,8,9,11,12,17,19,20,21,22,24,25,26,29,30,32,33,34,36,38,40,46,47,51,52,53,54,55,57,63,66,67,70,71,72,75,76,78,79,80,82,83,89,90,92,93,96]
LAST_PIECE = 85

# Ground truth
GT_PERMUTATION = [43,34,65,22,69,89,28,12,27,76,81,8,5,21,62,79,64,70,94,96,4,17,48,9,23,46,14,33,95,26,50,66,1,40,15,67,41,92,16,83,77,32,10,20,3,53,45,19,87,71,88,54,39,38,18,25,56,30,91,29,44,82,35,24,61,80,86,57,31,36,13,7,59,52,68,47,84,63,74,90,0,75,73,11,37,6,58,78,42,55,49,72,2,51,60,93,85]
GT_PAIR_MAP = {
    0: 75, 1: 40, 2: 51, 3: 53, 4: 17, 5: 21, 10: 20, 13: 7, 14: 33, 15: 67, 16: 83, 18: 25,
    23: 46, 27: 76, 28: 12, 31: 36, 35: 24, 37: 6, 39: 38, 41: 92, 42: 55, 43: 34, 44: 82, 45: 19,
    48: 9, 49: 72, 50: 66, 56: 30, 58: 78, 59: 52, 60: 93, 61: 80, 62: 79, 64: 70, 65: 22, 68: 47,
    69: 89, 73: 11, 74: 90, 77: 32, 81: 8, 84: 63, 86: 57, 87: 71, 88: 54, 91: 29, 94: 96, 95: 26,
}
GT_PAIRING = set(GT_PAIR_MAP.items())
GT_PAIRING_CANONICAL = [(inp, GT_PAIR_MAP[inp]) for inp in INP_PIECES]
GT_ORDERING = [21,34,36,14,13,40,5,32,33,46,4,24,12,8,47,26,1,9,19,10,39,6,3,23,43,44,18,11,27,45,22,16,31,42,15,7,29,35,41,38,0,37,17,28,20,25,2,30]

def load_piece(idx):
    return torch.load(os.path.join(DATA_DIR, 'pieces', f'piece_{idx}.pth'),
                      map_location='cpu', weights_only=True)

def load_all_pieces():
    """Returns dict of {idx: {'weight': tensor, 'bias': tensor}}."""
    pieces = {}
    for i in range(97):
        pieces[i] = load_piece(i)
    return pieces

def load_data():
    df = pd.read_csv(os.path.join(DATA_DIR, 'historical_data.csv'))
    X = torch.tensor(df.iloc[:, :48].values, dtype=torch.float32)
    y_pred = torch.tensor(df['pred'].values, dtype=torch.float32)
    y_true = torch.tensor(df['true'].values, dtype=torch.float32)
    return X, y_pred, y_true

def canonical_gt_pairing():
    """Ground-truth blocks in the canonical block index used by GT_ORDERING."""
    return list(GT_PAIRING_CANONICAL)

class Block(nn.Module):
    def __init__(self, inp_idx, out_idx, pieces=None):
        super().__init__()
        self.inp_idx = inp_idx
        self.out_idx = out_idx
        self.inp = nn.Linear(48, 96)
        self.activation = nn.ReLU()
        self.out = nn.Linear(96, 48)
        if pieces:
            inp_data, out_data = pieces[inp_idx], pieces[out_idx]
        else:
            inp_data, out_data = load_piece(inp_idx), load_piece(out_idx)
        self.inp.weight.data = inp_data['weight']
        self.inp.bias.data = inp_data['bias']
        self.out.weight.data = out_data['weight']
        self.out.bias.data = out_data['bias']
    def forward(self, x):
        return x + self.out(self.activation(self.inp(x)))

def eval_solution(pairing, ordering, X, y_pred, pieces=None):
    """Evaluate a (pairing, ordering) solution. Returns MSE vs pred."""
    blocks = [Block(inp, out, pieces) for inp, out in pairing]
    last_data = pieces[LAST_PIECE] if pieces else load_piece(LAST_PIECE)
    W_last, b_last = last_data['weight'], last_data['bias']
    with torch.no_grad():
        z = X.clone()
        for idx in ordering:
            z = blocks[idx](z)
        pred = (z @ W_last.T + b_last).squeeze()
    return ((pred - y_pred) ** 2).mean().item()

def score_pairing(candidate_pairing):
    """How many pairs match the ground truth?"""
    return len(set(candidate_pairing) & GT_PAIRING)

def score_ordering(candidate_ordering, candidate_pairing):
    """Build full permutation and compare to ground truth."""
    perm = [0] * 97
    for pos, block_idx in enumerate(candidate_ordering):
        inp_idx, out_idx = candidate_pairing[block_idx]
        perm[2 * pos] = inp_idx
        perm[2 * pos + 1] = out_idx
    perm[96] = LAST_PIECE
    correct = sum(1 for a, b in zip(perm, GT_PERMUTATION) if a == b)
    return correct, perm

class Timer:
    def __init__(self, name):
        self.name = name
    def __enter__(self):
        self.start = time.time()
        return self
    def __exit__(self, *args):
        self.elapsed = time.time() - self.start
        print(f"[{self.name}] {self.elapsed:.2f}s")

def print_report(name, pairing, ordering, elapsed, X, y_pred, pieces=None):
    """Standard report for any method."""
    n_correct_pairs = score_pairing(pairing)
    n_correct_positions, perm = score_ordering(ordering, pairing)
    mse = eval_solution(pairing, ordering, X, y_pred, pieces)

    print(f"\n{'='*60}")
    print(f"REPORT: {name}")
    print(f"{'='*60}")
    print(f"  Correct pairs:     {n_correct_pairs}/48")
    print(f"  Correct positions: {n_correct_positions}/97")
    print(f"  MSE vs pred:       {mse:.6e}")
    print(f"  Wall time:         {elapsed:.2f}s")
    print(f"{'='*60}")
    return {
        'name': name,
        'correct_pairs': n_correct_pairs,
        'correct_positions': n_correct_positions,
        'mse': mse,
        'wall_time': elapsed,
        'pairing': pairing,
        'ordering': ordering,
    }
