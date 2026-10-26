# thrashing_to_csv.py

Converts the features CSV from `features_to_csv.py` into a per-worm thrashing-frequency table (Dr. Jang's output 2): one column per worm, one row per video frame.

## Input / Output
- **In:** CSV produced by `features_to_csv.py`
- **Out:** per-worm CSV with columns `timestamp`, `time_s`, `worm_<id>`, ...

| Column | Meaning | Unit |
|---|---|---|
| `timestamp` | Video frame number | frames |
| `time_s` | Time in seconds (`timestamp / fps`) | s |
| `worm_<id>` | Thrashing frequency for that worm, centered on that frame; blank if not enough tracked frames | thrashes/min |

## Usage
Run `features_to_csv.py` first, then (from `tierpsy_tools`):

```
python thrashing_to_csv.py ../output/features.csv ../output/thrashing.csv
```

### Options
- `--fps`: video frame rate (default: 15)
- `--window`: sliding window in seconds (default: 10, provisional)

## Notes
- **Thrashing measure:** one thrash = one full body bend = 2 sign changes of `curvature_midbody`. The rate is the sign-change count in a centered sliding window of `--window` seconds, converted to thrashes/min.
- **Blank cells** mean fewer than half the frames in the window were tracked for that worm. Frames where the worm wasn't tracked don't count as crossings.
- **Units:** thrashes/min only depends on the curvature's sign and the fps, so no pixel calibration is needed.
- **Worm IDs** come from Tierpsy tracking. With the current tracking settings, one worm may appear as several IDs.