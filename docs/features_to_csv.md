# Tierpsy -> CSV Export

Converts Tierpsy `_featuresN.hdf5` files into a CSV you can open in Excel.

## What you get
One row per worm per frame, sorted by worm, then frame.

| Column | Meaning |
|---|---|
| `worm_index` | Tierpsy's ID for the worm |
| `timestamp` | Frame number |
| `length` | Body length (pixels) |
| `area` | Body area (pixels²) |
| `width_head_base`, `width_midbody`, `width_tail_base` | Body width at three points (pixels) |
| `speed`, `speed_midbody` | Movement speed, whole body and midbody |
| `angular_velocity` | How fast the worm is turning |
| `motion_mode` | 1 = forward, -1 = backward, 0 = paused |
| `curvature_head`, `curvature_midbody`, `curvature_tail` | How bent the body is at three points |
| `d_curvature_midbody` | Rate of change of midbody bending; closest Tierpsy feature to thrashing speed |
| `coord_x_body`, `coord_y_body` | Worm position in the frame (pixels) |

## One-time setup (Windows)
1. Install Python 3.12 from python.org (check "Add to PATH")
2. Download this repo (Code -> Download ZIP), unzip
3. Open **Command Prompt** in that folder and run:
```
   py -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
```

## Running it
From the unzipped folder, in Command Prompt:
```
   .venv\Scripts\activate
   python src\trace\io\features_to_csv.py INPUT_FILE OUTPUT_FILE
```
Example:
```
src\trace\io\features_to_csv.py data\2026-09-18_FMO4KO_D1_oldlens_polarized-IMAGE-14_11_03_267_featuresN.hdf5 data\out.csv
```
When it finishes, it prints how many rows and columns were written.

## Notes / limitations
- Units are frames and pixels (no calibration applied yet).
- Blank cells = frames where Tierpsy found the worm but couldn't measure it.
- Only worms and frames that Tierpsy tracked appear. Coverage depends on Tierpsy's tracking settings.
- Only `_featuresN.hdf5` files work. The skeletons and masked video files will not.

## Troubleshooting
- **"... does not exist"**: check the file path. Run from the unzipped folder, and don't start the path with `\`.
- **`KeyError: '<column name>'`**: this file is missing one of the expected columns (Tierpsy versions differ). Contact the team.