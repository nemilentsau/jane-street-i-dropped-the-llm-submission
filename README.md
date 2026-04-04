# I Dropped the LLM -- Submission

Reassembling a shuffled 48-block residual neural network from 97 linear layers.

**Answer:** MSE = 3.16e-14 on all 10,000 rows. See [`submission.md`](submission.md) for the full writeup.

## Setup

```bash
pip install -r requirements.txt
```

Place the puzzle data so the directory structure looks like:

```
model/
  historical_data.csv
  pieces/
    piece_0.pth
    ...
    piece_96.pth
```

All scripts expect `model/` at the project root. Alternatively, set `DATA_DIR` to point elsewhere:

```bash
export DATA_DIR=/path/to/model
```

## Quick Start

```bash
# Print the final 97-element permutation
python answer.py

# Full end-to-end solve in ~60s
python e2e/01_fastest_solve.py
```

## Dashboard

An interactive evidence dashboard visualizes all key results: pairing cost matrices, Jacobian analysis, phase structure, shock response curves, and trajectory PCA.

```bash
# Generate data artifacts (run each script individually)
python pairing/01_weight_correlation.py
python pairing/01b_training_evolution.py

# Run dashboard
cd dashboard && npm install && npm run dev
```

Or build a static site: `npm run build` (output in `dashboard/build/`).

## Scripts

### Pairing (5 methods, all recover 48/48 correct pairs)

| Script | Method | Data needed? |
|--------|--------|-------------|
| `pairing/01_weight_correlation.py` | Frobenius inner product `\|tr(W_out W_inp)\|` | No |
| `pairing/01b_training_evolution.py` | Training emergence + random control | Yes |
| `pairing/02_operator_moments.py` | Spectral invariants of `W_out @ W_inp` | No |
| `pairing/03_svd_cross_alignment.py` | SVD alignment in shared 96-D hidden space | No |
| `pairing/04_affine_linearization.py` | Gated product with ReLU activation stats | Yes |
| `pairing/05_multiview_fusion.py` | Equal-weight fusion of 3 weaker signals | Yes |

### Ordering (5 methods, all exact after greedy polish)

| Script | Method | Raw positions |
|--------|--------|--------------|
| `ordering/01_delta_greedy.py` | Min-perturbation greedy | 77/97 |
| `ordering/02_pairwise_tournament.py` | Insertion + pairwise refinement | 9/97 |
| `ordering/03_sinkhorn_ranking.py` | Soft permutation optimization | 9/97 |
| `ordering/04_insertion_beam_search.py` | Beam search over insertions | 11/97 |
| `ordering/05_spectral_flow.py` | Eigenvalue-jitter minimization | 9/97 |

### Distillation (network interpretability)

| Script | What it shows |
|--------|--------------|
| `distillation/01_network_structure.py` | Jacobian decomposition, phase structure, factor track, PCA |
| `distillation/02_shock_response.py` | Top-PC vs bottom-PC shock handling, 22x prediction gap |
| `distillation/03_latent_observer.py` | Autonomous vs observer surrogate models |

### End-to-End

| Script | What it does |
|--------|-------------|
| `e2e/01_fastest_solve.py` | Weight corr + delta-greedy + polish (fastest path) |
| `e2e/02_all_pairing_methods.py` | Runs all 5 pairings, comparison table |
| `e2e/03_all_ordering_methods.py` | Runs all 5 orderings (GT pairing), comparison table |
| `e2e/04_full_grid.py` | Pairing x ordering grid, shows multiple paths work |

## Project Structure

```
.
├── answer.py                  # The final permutation
├── submission.md              # Full writeup
├── requirements.txt
├── model/                     # Puzzle data (not included)
├── lib/                       # Shared utilities
│   ├── shared.py              # Block class, eval, scoring, data I/O
│   ├── fusion_utils.py        # Cost matrices, Hungarian, ordering primitives
│   ├── alt_philosophy_utils.py # Feature engineering, recipe search
│   └── dynamics_utils.py      # Trajectories, Jacobians, shock analysis
├── pairing/                   # 5 pairing method scripts
├── ordering/                  # 5 ordering method scripts
├── distillation/              # 3 interpretability scripts
├── e2e/                       # 4 end-to-end demonstration scripts
└── dashboard/                 # Svelte 5 evidence dashboard
    ├── static/data/           # Generated JSON artifacts
    └── src/                   # Dashboard source
```

## Key Insight

The puzzle factorizes into two independent inverse problems:

1. **Pairing** (which inp goes with which out): solved by training-induced weight correlation
2. **Ordering** (in what sequence the 48 blocks act): recoverable by multiple methods that land close enough for greedy polish to finish

The recovered network has the structure of a factor-compressing residual forecaster:
stabilize noisy state, compress onto a narrow factor track, apply sharp late corrections,
then a final linear prediction.
