# TRACE

AI-enabled video analysis of *C. elegans* behavioral and physiological responses to osmotic stress.
Senior design project sdmay27-03 (Iowa State), with Dr. Heeun Jang's lab, College of Veterinary Medicine.

## What's here

| Component | What it does | Docs |
|---|---|---|
| TRACE pipeline (`src/trace/pipeline.py`) | OpenCV pipeline: detects, skeletonizes and tracks worms in a video; writes per-worm CSVs | [docs/custom_pipeline.md](docs/custom_pipeline.md) |
| TRACE GUI (`src/trace/main.py`) | Desktop GUI front end | (none yet) |
| Tierpsy tools (`tierpsy_tools/`) | Standalone scripts that post-process Tierpsy Tracker output. Separate from the pipeline; own setup | [tierpsy_tools/README.md](tierpsy_tools/README.md) |
| `scripts/` | Exploratory helpers (well measurement, worm search, mask viewing, head/tail check) | n/a |

Tierpsy tool docs:
[features_to_csv](docs/features_to_csv.md) ·
[thrashing_to_csv](docs/thrashing_to_csv.md) ·
[bodysize_to_csv](docs/bodysize_to_csv.md) ·
[annotated_mask](docs/annotated_mask.md)

## Setup

Python virtual environment at the repo root.

macOS / Linux:
```
bash setup_venv.sh
source .venv/bin/activate
```

Windows:
```
setup_venv.bat
.venv\Scripts\activate
```

`tierpsy_tools/` has its own `requirements.txt` and setup scripts; see its README.

## Running the pipeline

```
python src/trace/pipeline.py <input_video> <output_dir>
```

Example:
```
python src/trace/pipeline.py data/clip10s_2026-09-22.avi output
```

`output_dir` is created if missing. Per-worm results are written to `output.csv`.

## Running the GUI

```
python src/trace/main.py
```

## Units

| Where | Spatial | Time |
|---|---|---|
| Pipeline output | px (curvature 1/px, area px²) | seconds |
| Client-facing | area mm², length µm, speed mm/s, thrashing bends/min | n/a |

- Video is 15 fps.
- Scale is about 15.1 µm/px (15.6 mm well = 1032 px). Re-measure if camera zoom or lens changes.
- Thrashing: one thrash = 2 sign changes of `curvature_midbody`.

## Repo layout
```
src/trace/      pipeline, GUI entry point, ui/
tierpsy_tools/  Tierpsy post-processing scripts (own README and setup)
scripts/        exploratory helpers and analysis notebook
docs/           documentation for each tool
data/           local videos and CSVs (not committed)
output/         pipeline output (not committed)
```

## Team
- Sara Theriault
- Zevan Gustafson
- Trevor Zimmerman
- Sam McDaniel
