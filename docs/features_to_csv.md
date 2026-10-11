# features_to_csv.py

Converts Tierpsy `_featuresN.hdf5` files into a features CSV (Dr. Jang's output 1): one row per worm per frame, sorted by worm, then frame.

## Input / Output
- **In:** Tierpsy `_featuresN.hdf5` file
- **Out:** CSV with the columns below

| Column | Meaning | Unit |
|---|---|---|
| `worm_index` | Tierpsy's ID for the worm | — |
| `timestamp` | Frame number | frames |
| `length` | Body length | px |
| `area` | Body area | px² |
| `width_head_base`, `width_midbody`, `width_tail_base` | Body width at three points | px |
| `speed`, `speed_midbody` | Movement speed, whole body and midbody | px/frame (× 15 = px/s) |
| `angular_velocity` | How fast the worm is turning | rad/frame |
| `motion_mode` | 1 = forward, -1 = backward, 0 = paused | unitless |
| `curvature_head`, `curvature_midbody`, `curvature_tail` | How bent the body is at three points | rad/px |
| `d_curvature_midbody` | Rate of change of midbody bending; closest Tierpsy feature to thrashing speed | rad/px per frame |
| `coord_x_body`, `coord_y_body` | Worm position in the frame | px |

## Usage

### From the repo
From `src/trace/io`:

```
python features_to_csv.py ../../../data/2026-09-18_FMO4KO_D1_oldlens_polarized-IMAGE-14_11_03_267_featuresN.hdf5 ../../../data/out.csv
```

### Standalone
Requires Python 3 and h5py (`pip install h5py`). Put `features_to_csv.py` in the same folder as your `_featuresN.hdf5` file, open a terminal in that folder, and run:

```
python features_to_csv.py your_video_featuresN.hdf5 out.csv
```

Replace `your_video_featuresN.hdf5` with your file's name. On Mac, use `python3` instead of `python`.

When it finishes, it prints how many rows and columns were written.

## Notes
- **Units:** frames and pixels, not yet converted to seconds or microns. For the client lab's setup, µm/px ≈ 21.9 (measured from the well's inner diameter, 22,600 µm = 1032 px). To convert: length (µm) = px × 21.9; area (µm²) = px² × 21.9² (≈ 480); seconds = frames / 15.
- **Blank cells** mean Tierpsy found the worm but couldn't measure it at that frame.
- **Coverage:** only worms and frames that Tierpsy tracked appear, which depends on Tierpsy's tracking settings.
- **Input type:** only `_featuresN.hdf5` files work. The skeletons and masked video files will not.

## Troubleshooting
- **"... does not exist"**: check the file path and run from the folder the file is in.
- **`KeyError: '<column name>'`**: this file is missing one of the expected columns (Tierpsy versions differ). Contact the team.