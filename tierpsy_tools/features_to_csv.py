"""Export Tierpsy featuresN timeseries_data to CSV."""

import argparse          
from pathlib import Path 

import pandas as pd
import tables           

# Columns to export from timeseries_data.
COLUMNS = [
    # ID and time
    "worm_index",
    "timestamp",
    # body size
    "length",
    "area",
    "width_head_base",
    "width_midbody",
    "width_tail_base",
    # movement
    "speed",
    "speed_midbody",
    "angular_velocity",
    "motion_mode",
    # thrashing
    "curvature_head",
    "curvature_midbody",
    # Rate of change of midbody bending; closest Tierpsy feature to thrashing speed.
    "d_curvature_midbody",
    "curvature_tail",
    #position
    "coord_x_body",
    "coord_y_body"
]

WELL_DIAMETER_UM = 15600  # inner well diameter (15.6 mm, dark edge to dark edge), from the client lab


def read_timeseries(h5_path: Path) -> pd.DataFrame:
    """Load timeseries_data from a _featuresN.hdf5 file."""
    with tables.open_file(h5_path, mode="r") as f:
        table = f.root.timeseries_data

        data = table.read()
    return pd.DataFrame(data)


def select_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only the columns in COLUMNS."""
    return df[COLUMNS]


def convert_units(df: pd.DataFrame, well_px: float, fps: float) -> pd.DataFrame:
    """Tierpsy output is in pixels and frames (microns_per_pixel and expected_fps unset).
    Convert to the client's units: length um, area mm^2, speed mm/s. Other columns unchanged."""
    um_per_px = WELL_DIAMETER_UM / well_px
    df = df.copy()
    df["length"] = df["length"] * um_per_px                        # px -> um
    df["area"] = df["area"] * um_per_px**2 * 1e-6                  # px^2 -> mm^2
    for col in ("speed", "speed_midbody"):
        df[col] = df[col] * um_per_px * fps * 1e-3                 # px/frame -> mm/s
    return df


def write_csv(df: pd.DataFrame, out_path: Path) -> None:
    """Sort and write to CSV."""
    df = df.sort_values(["worm_index", "timestamp"])
    df.to_csv(out_path, index=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "input",
        type=Path,
        help="Path to a Tierpsy _featuresN.hdf5 file",
    )

    parser.add_argument(
        "output",
        type=Path,
        help="Where to save the output CSV file",
    )

    parser.add_argument(
        "--well-px",
        type=float,
        default=1032.0,
        help="Well inner diameter in pixels (default: 1032, from the 9/22 recording)",
    )

    parser.add_argument(
        "--fps",
        type=float,
        default=15.0,
        help="Video frame rate (default: 15)",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    df = read_timeseries(args.input)
    df = select_columns(df)
    df = convert_units(df, args.well_px, args.fps)
    write_csv(df, args.output)

    print(f"Wrote {len(df)} rows x {len(df.columns)} columns to {args.output}")


if __name__ == "__main__":
    main()