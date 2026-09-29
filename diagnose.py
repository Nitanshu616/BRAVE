"""Compares fresh NORMAL running data against the saved baseline, feature by feature,
to show WHY the Isolation Forest scores normal data as anomalous.
Run from the same folder as sensor_ai.py, with the belt running normally:
    python diagnose.py --duration 45
"""
import argparse, pickle
import pandas as pd
import sensor_ai as S

ap = argparse.ArgumentParser()
ap.add_argument("--duration", type=int, default=45)
ap.add_argument("--source", choices=["synthetic", "serial"], default="serial")
ap.add_argument("--port", default="COM6")
a = ap.parse_args()

base = pd.read_csv(S.BASELINE_CSV)[S.FEATURE_COLS]
with open(S.MODEL_PATH, "rb") as f:
    model = pickle.load(f)

bs = -model.score_samples(base)
print(f"Baseline rows: {len(base)}")
print(f"Baseline scored by its own model: min={bs.min():.3f} mean={bs.mean():.3f} max={bs.max():.3f}")

print(f"\nCollecting {a.duration}s of NORMAL running data...")
rows = [feats for feats, _ in S.windows_from_stream(S.get_stream(a.source, a.port, a.duration))]
if not rows:
    raise SystemExit("No windows collected - no valid data arrived.")
test = pd.DataFrame(rows)[S.FEATURE_COLS]
ts = -model.score_samples(test)
print(f"Fresh normal data ({len(test)} windows): min={ts.min():.3f} mean={ts.mean():.3f} max={ts.max():.3f}")

lo, hi = base.min(), base.max()
out = pd.DataFrame({
    "base_mean": base.mean(), "base_std": base.std(),
    "base_min": lo, "base_max": hi,
    "test_mean": test.mean(),
    "pct_outside": ((test < lo) | (test > hi)).mean() * 100,
}).round(3)
print("\n", out.to_string())
print("\nRead it: features with high pct_outside, or base_std near 0, are the culprits.")
