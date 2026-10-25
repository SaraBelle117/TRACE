# Worm Count Estimation and Annotation

This script processes Tierpsy Tracker HDF5 outputs to estimate the number of worms in a video and identify the first frame in which all expected worms are labeled.

The selected frame is annotated with each worm's **ID, centroid, and bounding box**.

## Requirements

Install the required Python packages:

```bash
pip install numpy opencv-python h5py
```

The script also requires `search_data.py`, which provides `get_all_output_paths()` for locating the relevant HDF5 files.

## Usage

Run the script with the **base directory containing both the original video and its Tierpsy output files**:

```bash
python output.py /path/to/video_directory
```

To specify an output directory:

```bash
python output.py /path/to/video_directory --output-dir ./results
```

Use `python output.py --help` to see the available arguments.

## Processing Pipeline

1. **Estimate worm count:** Estimate the expected population from valid worm IDs across frames.
2. **Find the first fully labeled frame:** Identify the first frame containing the expected number of uniquely labeled worms.
3. **Extract worm data:** Retrieve each worm's centroid and bounding box.
4. **Annotate the frame:** Draw each worm's bounding box, centroid, and ID.
5. **Save the results:** Export the original mask and annotated image.

## Output

The script saves two images in the specified output directory:

| File | Description |
|---|---|
| `raw_mask.png` | Original mask of the selected frame. |
| `annotated_mask.png` | Mask annotated with worm IDs, centroids, and bounding boxes. |

The script also prints the estimated worm count, total number of observed frames, selected frame number, and extracted worm data.

## Assumptions

- The estimated worm count is a heuristic and may not equal the true population.
- The selected frame number must correspond to the correct index in the `/mask` dataset.
- Rows in `/blob_features` are assumed to correspond to rows in `/trajectories_data` in the same order.
- Bounding-box orientation is assumed to be measured in radians.