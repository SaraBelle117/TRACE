# features_to_csv.py

Converts Tierpsy `_featuresN.hdf5` files into a features CSV (Dr. Jang's output 1): one row per worm per frame, sorted by worm, then frame.

## Input / Output
- **In:** Tierpsy `_featuresN.hdf5` file
- **Out:** CSV with the columns below

| Column | Meaning | Unit |
|---|---|---|
| `worm_index` | Tierpsy's ID for the worm | — |
| `timestamp` | Frame number | frames |
| `length` | Body length | µm |
| `area` | Body area | mm² |
| `width_head_base`, `width_midbody`, `width_tail_base` | Body width at three points | px (unconverted) |
| `speed`, `speed_midbody` | Movement speed, whole body and midbody | mm/s |
| `angular_velocity` | How fast the worm is turning | rad/frame (unconverted) |
| `motion_mode` | 1 = forward, -1 = backward, 0 = paused | unitless |
| `curvature_head`, `curvature_midbody`, `curvature_tail` | How bent the body is at three points | rad/px (unconverted) |
| `d_curvature_midbody` | Rate of change of midbody bending; closest Tierpsy feature to thrashing speed | rad/px per frame (unconverted) |
| `coord_x_body`, `coord_y_body` | Worm position in the frame | px |

## Usage
From `tierpsy_tools`:

```
python features_to_csv.py ../data/cf_2026-09-22_FMO4KO_~D1-IMAGE-15_38_49_221_featuresN.hdf5 ../output/features.csv
```

When it finishes, it prints how many rows and columns were written.

### Options
- `--well-px`: well inner diameter in pixels (default: 1032)
- `--fps`: video frame rate (default: 15)

## Notes
- **Units:** `length`, `area`, and `speed` are converted using µm/px = 15,600 µm / `--well-px` (default 1032 px → ≈ 15.1 µm/px). Speed also uses `--fps`, and assumes Tierpsy outputs px/frame (unverified; if wrong, speed is off by a factor of the fps). All other columns stay in Tierpsy's units. Seconds = frames / fps.
- **Blank cells** mean Tierpsy found the worm but couldn't measure it at that frame.
- **Coverage:** only worms and frames that Tierpsy tracked appear, which depends on Tierpsy's tracking settings.
- **Input type:** only `_featuresN.hdf5` files work. The skeletons and masked video files will not.

## Troubleshooting
- **"... does not exist"**: check the file path and run from `tierpsy_tools`.
- **`KeyError: '<column name>'`**: this file is missing one of the expected columns (Tierpsy versions differ). Contact the team.