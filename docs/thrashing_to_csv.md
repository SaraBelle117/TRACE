# thrashing_to_csv.py

Converts the features CSV from `features_to_csv.py` into a per-worm thrashing table (Dr. Jang's output 2): one column per worm, one row per video frame.

## Input / Output
- **In:** CSV produced by `features_to_csv.py`
- **Out:** per-worm CSV with columns `timestamp`, `time_s`, `worm_<id>`, ...

| Column | Meaning | Unit |
|---|---|---|
| `timestamp` | Video frame number | frames |
| `time_s` | Time in seconds (`timestamp / fps`) | s |
| `worm_<id>` | Thrashing value for that worm at that frame; blank if the worm isn't tracked | rad/px per frame |

## Usage

### From the repo
Run `features_to_csv.py` first, then (from `src/trace/io`):

```
python thrashing_to_csv.py ../../../data/out.csv ../../../data/thrashing_by_worm.csv
```

### Standalone
Requires Python 3. Put `thrashing_to_csv.py` in the same folder as your features CSV, open a terminal in that folder, and run:

```
python thrashing_to_csv.py features.csv thrashing_by_worm.csv
```

Replace `features.csv` with the name of your features file. On Mac, use `python3` instead of `python`.

### Options
- `--fps`: video frame rate (default: 15)

## Notes
- **Thrashing measure:** currently `d_curvature_midbody` (rate of change of midbody bending), a stand-in until the thrashing frequency calculation is ready.
- **Blank cells** mean the worm wasn't tracked at that frame. Each worm's last tracked frame is also blank, since a rate of change needs a following frame.
- **Units:** Tierpsy's raw units (rad/px per frame); not yet calibrated. Since curvature is per pixel, converting to rad/µm means dividing by µm/px (≈ 21.9 for the client lab's setup); to per second, multiply by fps (15).
- **Worm IDs** come from Tierpsy tracking. With the current tracking settings, one worm may appear as several IDs.