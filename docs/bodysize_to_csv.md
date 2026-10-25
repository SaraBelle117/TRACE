# bodysize_to_csv.py

Converts the features CSV from `features_to_csv.py` into a per-worm body size table (Dr. Jang's output 3): one column per worm, one row per video frame.

## Input / Output
- **In:** CSV produced by `features_to_csv.py` (already in real units)
- **Out:** per-worm CSV with columns `timestamp`, `time_s`, `worm_<id>`, ...

| Column | Meaning | Unit |
|---|---|---|
| `timestamp` | Video frame number | frames |
| `time_s` | Time in seconds (`timestamp / fps`) | s |
| `worm_<id>` | Body size for that worm at that frame; blank if the worm isn't tracked | µm (`length`) or mm² (`area`) |

## Usage
Run `features_to_csv.py` first, then (from `tierpsy_tools`):

    python bodysize_to_csv.py ../output/features.csv ../output/bodysize_area_by_worm.csv
    python bodysize_to_csv.py ../output/features.csv ../output/bodysize_length_by_worm.csv --measure length

### Options
- `--measure`: `area` (default) or `length`
- `--fps`: video frame rate (default: 15)

## Notes
- **Units:** converted by `features_to_csv.py` using µm/px = 15,600 µm / well diameter in px (default 1032 px → ≈ 15.1 µm/px). Length is µm, area is mm². To change the calibration, rerun `features_to_csv.py` with `--well-px`.
- **Blank cells** mean the worm wasn't tracked at that frame.
- **Worm IDs** come from Tierpsy tracking. With the current tracking settings, one worm may appear as several IDs.