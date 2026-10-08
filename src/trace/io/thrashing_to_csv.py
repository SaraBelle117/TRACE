"""Pivot the features CSV into a wide thrashing table: one column per worm, one row per frame."""
import argparse
from pathlib import Path
import pandas as pd

# Stand-in for thrashing until the frequency calculation is ready.
THRASHING_COLUMN = "d_curvature_midbody"


def make_wide(df: pd.DataFrame, fps: float) -> pd.DataFrame:
    wide = df.pivot(index="timestamp", columns="worm_index", values=THRASHING_COLUMN)
    wide.columns = [f"worm_{w}" for w in wide.columns]
    wide.insert(0, "time_s", wide.index / fps)
    return wide.reset_index()


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", type=Path, help="CSV from features_to_csv.py")
    p.add_argument("output", type=Path, help="wide thrashing CSV to write")
    p.add_argument("--fps", type=float, default=15.0, help="video frame rate (default: 15)")
    return p.parse_args()


def main():
    args = parse_args()
    df = pd.read_csv(args.input)
    wide = make_wide(df, args.fps)
    wide.to_csv(args.output, index=False)
    print(f"Wrote {len(wide)} frames x {len(wide.columns) - 2} worms to {args.output}")


if __name__ == "__main__":
    main()