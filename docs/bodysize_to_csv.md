# bodysize_to_csv.py

Converts the features CSV from `features_to_csv.py` into a per-worm body size table (Dr. Jang's output 3): one column per worm, one row per video frame.

## Input / Output
- **In:** CSV produced by `features_to_csv.py`
- **Out:** per-worm CSV with columns `timestamp`, `time_s`, `worm_<id>`, ...

| Column | Meaning |
|---|---|
| `timestamp` | Video frame number |
| `time_s` | Time in seconds (`timestamp / fps`) |
| `worm_<id>` | Body size for that worm at that frame; blank if the worm isn't tracked |

## Usage
Run `features_to_csv.py` first, then (from `src/trace/io`):

```
python bodysize_to_csv.py ../../../data/out.csv ../../../data/bodysize_area_by_worm.csv
python bodysize_to_csv.py ../../../data/out.csv ../../../data/bodysize_length_by_worm.csv --measure length
```

Options:
- `--measure` — `area` (default) or `length`
- `--fps` — video frame rate (default: 15)

## Notes
- **Units:** pixels (`length`) or pixels² (`area`); not yet converted to microns.
- **Blank cells** mean the worm wasn't tracked at that frame.
- **Worm IDs** come from Tierpsy tracking. With the current tracking settings, one worm may appear as several IDs.