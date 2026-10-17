"""Head/tail consistency check on the longest track of a pipeline output.csv.

Counts midbody curvature sign changes and how many coincide with an
approximate head/tail flip (head end narrower than tail end).

Usage:
    python scripts/headtail_check.py output/py/output.csv
"""

import argparse

import numpy as np
import pandas as pd

parser = argparse.ArgumentParser(description="Head/tail consistency check on the longest track.")
parser.add_argument("csv", nargs="?", default="output/output.csv", help="path to the pipeline's output.csv")
args = parser.parse_args()

df = pd.read_csv(args.csv).dropna(subset=["track_id"])
tid = df["track_id"].value_counts().idxmax()    # longest track
w = df[df["track_id"] == tid].sort_values("timestamp").reset_index(drop=True)

head_wider = w["width_head_base"] > w["width_tail_base"]
flip = (head_wider != head_wider.shift()).iloc[1:]
sign_change = (np.sign(w["curvature_midbody"]) != np.sign(w["curvature_midbody"].shift())).iloc[1:]
duration = w["timestamp"].iloc[-1] - w["timestamp"].iloc[0]

print(f"track {tid}: {len(w)} frames, {duration:.1f} s")
print("midbody sign changes:", sign_change.sum(), f"({sign_change.sum() / duration:.1f} per s)")
print("head/tail flips (approx.):", flip.sum())
print("sign changes coinciding with a flip:", (flip & sign_change).sum())
print("timestamps to check in video:", w["timestamp"].iloc[1:][flip & sign_change].round(2).tolist()[:10])