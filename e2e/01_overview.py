"""End-to-End Overview: Aggregated Pipeline View

Pulls precomputed results from the individual pairing and ordering scripts
to build a unified E2E view. No algorithms are re-run here — all timings
come from the original script executions.

Caveat: timings were collected across separate runs on a laptop, potentially
under different processor loads and power states. No statistical testing or
repeated trials were done. These are ballpark single-run wall-clock numbers.
"""
from __future__ import annotations

import json
import os

DASH_DIR = os.path.join(os.path.dirname(__file__), '..', 'dashboard', 'static', 'data')

print("=" * 60)
print("END-TO-END OVERVIEW (aggregated from precomputed results)")
print("=" * 60)

# ── Load individual script results ──────────────────────────────

PAIRING_FILES = {
    "01": ("pairing_01_weight_correlation.json", "Weight Correlation", False),
    "02": ("pairing_02_operator_moments.json", "Operator Moments", False),
    "03": ("pairing_03_svd_cross_alignment.json", "SVD Alignment", False),
    "04": ("pairing_04_affine_linearization.json", "Affine Linearization", True),
    "05": ("pairing_05_multiview_fusion.json", "Multi-View Fusion", True),
}

ORDERING_FILES = {
    "01": ("ordering_01_delta_greedy.json", "Delta Greedy", "01_delta_greedy"),
    "02": ("ordering_02_pairwise_tournament.json", "Pairwise Tournament", "02_pairwise"),
    "03": ("ordering_03_sinkhorn_ranking.json", "Sinkhorn Ranking", "03_sinkhorn"),
    "04": ("ordering_04_beam_search.json", "Beam Search", "04_beam"),
    "05": ("ordering_05_spectral_flow.json", "Spectral Flow", "05_spectral"),
}


def load_json(filename: str) -> dict:
    path = os.path.join(DASH_DIR, filename)
    with open(path) as f:
        return json.load(f)


# ── Pairing results ─────────────────────────────────────────────
print("\nPairing methods (from individual scripts):")
pairing_results: list[dict] = []

for pid, (fname, name, needs_data) in PAIRING_FILES.items():
    d = load_json(fname)
    # Different scripts store accuracy under different keys
    accuracy = d.get("accuracy") or d.get("best", {}).get("accuracy") or d.get("fused_accuracy", 0)
    elapsed = d["elapsed_s"]
    pairing_results.append({
        "id": pid,
        "name": name,
        "accuracy": accuracy,
        "elapsed_s": round(elapsed, 2),
        "needs_data": needs_data,
    })
    print(f"  {pid} {name}: {accuracy}/48, script time {elapsed:.1f}s")

all_canonical = all(p["accuracy"] == 48 for p in pairing_results)
print(f"\n  All produce canonical pairing: {all_canonical}")

# ── Ordering results ─────────────────────────────────────────────
print("\nOrdering methods (from individual scripts):")

overview = load_json("ordering_00_overview.json")
raw_stats = overview["raw_stats"]

ordering_results: list[dict] = []

for oid, (fname, name, stats_key) in ORDERING_FILES.items():
    d = load_json(fname)
    elapsed = d["elapsed_s"]
    stats = raw_stats.get(stats_key, {})
    raw_mse = stats.get("mse", 0.0)
    raw_pos = stats.get("correct_positions", 0)
    ordering_results.append({
        "id": oid,
        "name": name,
        "raw_positions": raw_pos,
        "raw_mse": raw_mse,
        "elapsed_s": round(elapsed, 2),
    })
    print(f"  {oid} {name}: {raw_pos}/97, raw MSE={raw_mse:.4f}, script time {elapsed:.1f}s")

# ── Fastest pipeline ─────────────────────────────────────────────
# Weight Correlation (fastest pairing) + Delta Greedy (fastest ordering)
# These were measured in the same script run so the timing is self-consistent.
p_fastest = pairing_results[0]  # Weight Correlation
o_fastest = ordering_results[0]  # Delta Greedy
total_fastest = p_fastest["elapsed_s"] + o_fastest["elapsed_s"]

print(f"\nFastest pipeline: {p_fastest['name']} ({p_fastest['elapsed_s']:.1f}s)"
      f" + {o_fastest['name']} ({o_fastest['elapsed_s']:.1f}s)"
      f" = ~{total_fastest:.0f}s")

fastest_pipeline = {
    "pairing_method": p_fastest["name"],
    "ordering_method": o_fastest["name"],
    "pairing_elapsed": p_fastest["elapsed_s"],
    "ordering_elapsed": o_fastest["elapsed_s"],
    "total_time": round(total_fastest, 0),
}

# ── 5x5 grid (estimated from individual script times) ────────────
print("\n5x5 Timing Grid (ballpark estimates):")
print("  Note: sums of independently measured script times.")
print("  Actual end-to-end would share data loading overhead.\n")

grid_rows: list[dict] = []
for o in ordering_results:
    for p in pairing_results:
        total = p["elapsed_s"] + o["elapsed_s"]
        grid_rows.append({
            "pairing_id": p["id"],
            "pairing_name": p["name"],
            "ordering_id": o["id"],
            "ordering_name": o["name"],
            "pairing_elapsed": p["elapsed_s"],
            "ordering_elapsed": o["elapsed_s"],
            "total_time": round(total, 0),
        })

# Print summary table
p_names = [p["name"][:12] for p in pairing_results]
print(f"  {'':>20s}  {'  '.join(f'{n:>12s}' for n in p_names)}")
for o in ordering_results:
    times = []
    for p in pairing_results:
        total = p["elapsed_s"] + o["elapsed_s"]
        m, s = divmod(int(total), 60)
        times.append(f"  {m:>3d}m{s:02d}s" if m > 0 else f"     {s:>2d}s")
    print(f"  {o['name']:>20s}  {'  '.join(f'{t:>12s}' for t in times)}")

# ── Write dashboard JSON ─────────────────────────────────────────
result = {
    "pairing_results": pairing_results,
    "ordering_results": ordering_results,
    "all_canonical": all_canonical,
    "fastest_pipeline": fastest_pipeline,
    "grid": grid_rows,
    "caveat": (
        "Timings are ballpark estimates from single-run wall-clock measurements "
        "of individual scripts, collected at different times on a laptop under "
        "varying processor load and power state. No statistical testing with "
        "repeated trials was performed. Summed pipeline times double-count "
        "shared overhead like data loading."
    ),
}

os.makedirs(DASH_DIR, exist_ok=True)
out_path = os.path.join(DASH_DIR, "e2e_overview.json")
with open(out_path, "w") as f:
    json.dump(result, f, indent=1)
print(f"\nDashboard data -> {out_path}")
print("Done.")
