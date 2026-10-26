"""Wide thrashing-frequency table: one column per worm (thrashes/min), one row per frame."""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd

CURVATURE_COLUMN = "curvature_midbody"

def thrash_rate(curv: pd.Series, fps: float, window_s: float) -> pd.Series:
    """Thrashes/min in a centered sliding window. One thrash = 2 sign changes."""
    s = np.sign(curv)
    prev = s.shift()
    cross = (s * prev < 0).astype(float)
    cross[s.isna() | prev.isna()] = np.nan  # gaps don't count either way
    win = max(int(window_s * fps), 2)
    crossings_per_frame = cross.rolling(win, center=True, min_periods=win // 2).mean()
    return crossings_per_frame * fps * 60 / 2

def make_wide(df: pd.DataFrame, fps: float, window_s: float) -> pd.DataFrame:
    curv = df.pivot(index="timestamp", columns="worm_index", values=CURVATURE_COLUMN)
    wide = curv.apply(lambda col: thrash_rate(col, fps, window_s))
    wide.columns = [f"worm_{w}" for w in wide.columns]
    wide.insert(0, "time_s", wide.index / fps)
    return wide.reset_index()

def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", type=Path, help="CSV from features_to_csv.py")
    p.add_argument("output", type=Path, help="wide thrashing CSV to write")
    p.add_argument("--fps", type=float, default=15.0, help="video frame rate (default: 15)")
    p.add_argument("--window", type=float, default=10.0, help="sliding window in seconds (default: 10, provisional)")
    return p.parse_args()


def main():
    args = parse_args()
    df = pd.read_csv(args.input)
    wide = make_wide(df, args.fps, args.window)
    wide.to_csv(args.output, index=False)
    print(f"Wrote {len(wide)} frames x {len(wide.columns) - 2} worms to {args.output}")


if __name__ == "__main__":
    main()