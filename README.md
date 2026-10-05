# Worm Tracking

This project is an in-progress video-processing pipeline for detecting and
analyzing worms in grayscale video. The current implementation is in the
Jupyter notebook [`src/trace.ipynb`](src/trace.ipynb), and the sample video is
[`data/demo.avi`](data/demo.avi).

## Setup

From the repository root, create a virtual environment and install the pinned
dependencies:

```bash
bash setup_venv.sh
```

Activate it in your shell:

```bash
source .venv/bin/activate
```

In VS Code, open `src/trace.ipynb` and select the `.venv` Python interpreter as
the notebook kernel.


## Current pipeline

- `VideoLoader` reads video frames as grayscale and exposes basic video
  metadata.
- `find_background` estimates a background image from sampled frames.
- `preprocess_frame` creates a binary mask of dark foreground regions against
  the estimated background.
- `analyze_frame` finds connected components and reports their area, centroid,
  contour, and bounding box.
- Sequence analysis and export are not implemented yet.

The preprocessing thresholds and connected-component filtering are still being
tuned; inspect the displayed masks and component results when changing them.
