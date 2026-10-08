# thrashing_to_csv.py

Converts the features CSV from `features_to_csv.py` into a wide thrashing table (Dr. Jang's output 2): one column per worm, one row per video frame.

## Input / Output
- **In:** CSV produced by `features_to_csv.py`
- **Out:** wide CSV with columns `timestamp`, `time_s`, `worm_<id>`, ...

| Column | Meaning |
|---|---|
| `timestamp` | Video frame number |
| `time_s` | Time in seconds (`timestamp / fps`) |
| `worm_<id>` | Thrashing value for that worm at that frame; blank if the worm isn't tracked |

## Usage
Run `features_to_csv.py` first, then (from `src/trace/io`):

```
python thrashing_to_csv.py ../../../data/out.csv ../../../data/thrashing_wide.csv
```

Options:
- `--fps` — video frame rate (default: 15)

## Notes
- **Thrashing measure:** currently `d_curvature_midbody` (rate of change of midbody bending), a stand-in until the thrashing frequency calculation is ready.
- **Blank cells** mean the worm wasn't tracked at that frame. Each worm's last tracked frame is also blank, since a rate of change needs a following frame.
- **Units:** values are in Tierpsy's raw units (per frame, pixels); not yet calibrated.
- **Worm IDs** come from Tierpsy tracking. With the current tracking settings, one worm may appear as several IDs.