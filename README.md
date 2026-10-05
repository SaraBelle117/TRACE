# TRACE

AI-enabled video analysis of *C. elegans* behavioral and physiological responses to osmotic stress.
Senior design project sdmay27-03 (Iowa State), with Dr. Heeun Jang's lab, College of Veterinary Medicine.

## What's here

| Tool | What it does | Docs |
|---|---|---|
| Tierpsy -> CSV export | Converts Tierpsy `_featuresN.hdf5` output to a per-worm, per-frame CSV | [docs/features_to_csv.md](docs/features_to_csv.md) |
| Custom pipeline | Video loading, preprocessing, and frame analysis (PyAV/OpenCV) | [docs/custom_pipeline.md](docs/custom_pipeline.md) |

## Setup (Windows)
```
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Repo layout
```
src/        source code
docs/       documentation for each tool
data/       local data (not committed)
```

## Team
- Sara Theriault
- Zevan Gustafson
- Trevor Zimmerman
- Sam McDaniel