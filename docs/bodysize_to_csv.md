# bodysize_to_csv.py

Converts the features CSV from `features_to_csv.py` into a per-worm body size table (Dr. Jang's output 3): one column per worm, one row per video frame.

## Input / Output
- **In:** CSV produced by `features_to_csv.py`
- **Out:** per-worm CSV with columns `timestamp`, `time_s`, `worm_<id>`, ...

| Column | Meaning | Unit |
|---|---|---|
| `timestamp` | Video frame number | frames |
| `time_s` | Time in seconds (`timestamp / fps`) | s |
| `worm_<id>` | Body size for that worm at that frame; blank if the worm isn't tracked | px (`length`) or px² (`area`) |

## Usage

### From the repo
Run `features_to_csv.py` first, then (from `src/trace/io`):

    python bodysize_to_csv.py ../../../data/out.csv ../../../data/bodysize_area_by_worm.csv
    python bodysize_to_csv.py ../../../data/out.csv ../../../data/bodysize_length_by_worm.csv --measure length

### Standalone
Requires Python 3. Put `bodysize_to_csv.py` in the same folder as your features CSV, open a terminal in that folder, and run:

    python bodysize_to_csv.py features.csv bodysize_area_by_worm.csv
    python bodysize_to_csv.py features.csv bodysize_length_by_worm.csv --measure length

Replace `features.csv` with the name of your features file. On Mac, use `python3` instead of `python`.

### Options
- `--measure`: `area` (default) or `length`
- `--fps`: video frame rate (default: 15)

## Notes
- **Units:** pixels, not yet converted to microns. For the client lab's setup, µm/px ≈ 21.9 (measured from the well's inner diameter, 22,600 µm = 1032 px). To convert: length (µm) = px × 21.9; area (µm²) = px² × 21.9² (≈ 480).
- **Blank cells** mean the worm wasn't tracked at that frame.
- **Worm IDs** come from Tierpsy tracking. With the current tracking settings, one worm may appear as several IDs.