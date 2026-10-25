import argparse
import os
from collections import Counter
from pathlib import Path
import cv2
import h5py
import numpy as np

def get_video_output_path(dir_path):
    extensions = ['.mpeg4', '.avi']
    
    # Ensure extensions are properly formatted with leading dots
    ext_set = {ext if ext.startswith('.') else f'.{ext}' for ext in extensions}
    
    # Find the first matching file, or return None if no match is found
    return next((f for f in dir_path.iterdir() if f.is_file() and f.suffix in ext_set), None)

def get_all_output_paths(dir_path):
    files = [item for item in dir_path.rglob("*.hdf5") if item.is_file()]    
    prefix = os.path.commonprefix([p.stem for p in files])
    files_by_suffix = { p.stem.removeprefix(prefix).removeprefix("_"): p for p in files}
    if "" in files_by_suffix:
        files_by_suffix["masks"] = files_by_suffix.pop("")

    files_by_suffix["video"] = get_video_output_path(dir_path)
    return files_by_suffix


def estimate_worm_count(hdf5_path, window_size=100):
    """
    Estimate the number of worms from Tierpsy tracking data.

    Returns
    -------
    tuple
        (estimated_count, frame_counts, total_frames)

        estimated_count: int or None
        frame_counts: dict mapping frame numbers to worm counts
        total_frames: number of unique frames in the original data
    """
    if window_size < 1:
        raise ValueError("window_size must be at least 1.")

    with h5py.File(hdf5_path, "r") as f:
        data = f["/trajectories_data"][:]

    frames = data["frame_number"]
    labels = data["worm_index_joined"]

    total_frames = len(np.unique(frames))

    # Exclude invalid worm IDs.
    valid = labels > 0

    # Exclude poor skeletons when these fields are available.
    if "has_skeleton" in data.dtype.names:
        valid &= data["has_skeleton"] == 1

    if "is_good_skel" in data.dtype.names:
        valid &= data["is_good_skel"] == 1

    frames = frames[valid]
    labels = labels[valid]

    # Return a consistent three-value tuple.
    if len(frames) == 0:
        return None, {}, total_frames

    # Count distinct valid worm IDs in each observed frame.
    frame_counts = {}

    for frame in np.unique(frames):
        frame_labels = labels[frames == frame]
        frame_counts[int(frame)] = len(np.unique(frame_labels))

    # Sort frames chronologically.
    ordered_frames = np.array(sorted(frame_counts))
    counts = np.array([frame_counts[f] for f in ordered_frames])

    # If there are too few observed frames for a full window,
    # use the maximum observed count.
    if len(counts) < window_size:
        return int(np.max(counts)), frame_counts, total_frames

    # Calculate rolling averages.
    rolling_means = np.convolve(
        counts,
        np.ones(window_size) / window_size,
        mode="valid",
    )

    best_window = int(np.argmax(rolling_means))

    window_counts = counts[
        best_window:best_window + window_size
    ]

    # Select the most frequent count in the best window.
    estimated_count = Counter(window_counts).most_common(1)[0][0]

    return int(estimated_count), frame_counts, total_frames


def find_first_fully_labeled_frame(hdf5_path, expected_worms):
    """
    Find the first frame with the expected number of distinct,
    positively labeled worms and no invalid worm IDs.

    Returns
    -------
    int or None
        Frame number, or None if no matching frame exists.
    """
    if expected_worms is None or expected_worms < 1:
        return None

    with h5py.File(hdf5_path, "r") as f:
        trajectories = f["/trajectories_data"][:]

    frames = trajectories["frame_number"]
    labels = trajectories["worm_index_joined"]

    for frame in np.unique(frames):
        frame_labels = labels[frames == frame]

        # Every record must have a valid ID.
        if np.any(frame_labels <= 0):
            continue

        # The frame must contain the expected number of distinct IDs.
        if len(np.unique(frame_labels)) == expected_worms:
            return int(frame)

    return None


def fetch_frame(hdf5_path, ind):
    """
    Retrieve a mask using its zero-based index in the /mask dataset.

    The supplied index must correspond to the desired mask frame.
    """
    with h5py.File(hdf5_path, "r") as f:
        masks = f["/mask"]

        if ind < 0 or ind >= masks.shape[0]:
            raise IndexError(
                f"Frame index {ind} is outside the mask dataset "
                f"(valid indices: 0 to {masks.shape[0] - 1})."
            )

        return masks[ind, :, :]


def fetch_worm_data(skeletons_path, frame_index):
    """
    Retrieve worm centroids and axis-aligned bounding boxes.

    Returns
    -------
    dict
        {
            worm_id: {
                "centroid": (x, y),
                "bounding_box": (x, y, width, height)
            }
        }

    Assumption
    ----------
    Rows in blob_features correspond to rows in trajectories_data
    in the same order.
    """
    results = {}

    with h5py.File(skeletons_path, "r") as f:
        trajectories = f["/trajectories_data"][:]
        blobs = f["/blob_features"][:]

    # Indices into the original trajectory array are needed to
    # retrieve the corresponding blob rows.
    trajectory_indices = np.flatnonzero(
        trajectories["frame_number"] == frame_index
    )

    for trajectory_index in trajectory_indices:
        trajectory = trajectories[trajectory_index]

        worm_id = int(trajectory["worm_index_joined"])

        # Use the same positive-ID convention as the other functions.
        if worm_id <= 0:
            continue

        # Verify that a corresponding blob row exists.
        if trajectory_index >= len(blobs):
            continue

        centroid = (
            float(trajectory["coord_x"]),
            float(trajectory["coord_y"]),
        )

        blob = blobs[trajectory_index]

        cx = float(blob["coord_x"])
        cy = float(blob["coord_y"])
        length = float(blob["box_length"])
        width = float(blob["box_width"])
        angle = float(blob["box_orientation"])

        # Convert the rotated rectangle to an axis-aligned box.
        # This assumes angle is expressed in radians.
        cos_a = abs(np.cos(angle))
        sin_a = abs(np.sin(angle))

        bbox_width = length * cos_a + width * sin_a
        bbox_height = length * sin_a + width * cos_a

        x = int(round(cx - bbox_width / 2))
        y = int(round(cy - bbox_height / 2))

        results[worm_id] = {
            "centroid": centroid,
            "bounding_box": (
                x,
                y,
                int(round(bbox_width)),
                int(round(bbox_height)),
            ),
        }

    return results


def save_masked_image(mask: np.ndarray, output_path: str) -> None:
    """
    Save an image and create its parent directory if necessary.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if mask.dtype != np.uint8:
        mask = mask.astype(np.uint8)

    if not cv2.imwrite(str(output_path), mask):
        raise IOError(f"Failed to save image to {output_path}")


def annotate_worms(
    frame: np.ndarray,
    worm_data: dict,
    box_color=(0, 255, 0),
    centroid_color=(0, 0, 255),
    text_color=(255, 255, 0),
) -> np.ndarray:
    """
    Annotate a frame with worm IDs, centroids, and bounding boxes.

    Returns a new BGR image without modifying the input frame.
    """
    if frame.ndim == 2:
        annotated = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
    elif frame.ndim == 3 and frame.shape[2] == 3:
        annotated = frame.copy()
    else:
        raise ValueError(
            "frame must be a grayscale image or a three-channel color image."
        )

    for worm_id, data in worm_data.items():
        cx, cy = map(
            lambda v: int(round(v)),
            data["centroid"],
        )

        x, y, width, height = data["bounding_box"]

        # Draw bounding box.
        cv2.rectangle(
            annotated,
            (int(x), int(y)),
            (int(x + width), int(y + height)),
            box_color,
            1,
        )

        # Draw centroid.
        cv2.circle(
            annotated,
            (cx, cy),
            radius=3,
            color=centroid_color,
            thickness=-1,
        )

        # Draw worm ID.
        cv2.putText(
            annotated,
            str(worm_id),
            (int(x), max(15, int(y) - 5)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            text_color,
            1,
            cv2.LINE_AA,
        )

    return annotated


def produce_output(data_dir, output_dir="."):
    """
    Process a video's Tierpsy outputs and save annotated mask images.

    Parameters
    ----------
    data_dir : str or Path
        Directory containing the video processing outputs.
    output_dir : str or Path
        Destination directory for generated images.
    """
    data_dir = Path(data_dir)
    output_dir = Path(output_dir)

    if not data_dir.is_dir():
        raise NotADirectoryError(
            f"Video directory does not exist: {data_dir}"
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    # Locate the relevant HDF5 files.
    hdf5_outputs = get_all_output_paths(data_dir)

    if "skeletons" not in hdf5_outputs or "masks" not in hdf5_outputs:
        raise KeyError(
            "get_all_output_paths() must return 'skeletons' and 'masks'."
        )

    skeletons_path = hdf5_outputs["skeletons"]
    masks_path = hdf5_outputs["masks"]

    if not Path(skeletons_path).is_file():
        raise FileNotFoundError(
            f"Skeleton HDF5 file not found: {skeletons_path}"
        )

    if not Path(masks_path).is_file():
        raise FileNotFoundError(
            f"Mask HDF5 file not found: {masks_path}"
        )

    print("HDF5 outputs:", hdf5_outputs)

    # Estimate the expected worm population.
    expected_worms, frame_counts, total_frames = estimate_worm_count(
        skeletons_path
    )

    print("Total frames:", total_frames)
    print("Estimated worm count:", expected_worms)

    if expected_worms is None:
        raise RuntimeError(
            "Could not estimate the worm count: no valid tracking records."
        )

    # Find a frame where all expected worms are labeled.
    frame_ind = find_first_fully_labeled_frame(
        skeletons_path,
        expected_worms,
    )

    if frame_ind is None:
        raise RuntimeError(
            "No fully labeled frame was found for "
            f"{expected_worms} expected worms."
        )

    print("Selected frame number:", frame_ind)

    # IMPORTANT:
    # This assumes frame_ind is also the zero-based index in /mask.
    mask = fetch_frame(masks_path, frame_ind)

    # Extract worm data and annotate the selected frame.
    worm_data = fetch_worm_data(skeletons_path, frame_ind)
    annotated = annotate_worms(mask, worm_data)

    # Save outputs.
    save_masked_image(mask, output_dir / "raw_mask.png")
    save_masked_image(annotated, output_dir / "annotated_mask.png")

    print("Raw mask:", output_dir / "raw_mask.png")
    print("Annotated mask:", output_dir / "annotated_mask.png")
    print("Worm data:", worm_data)

    return {
        "estimated_worms": expected_worms,
        "frame_counts": frame_counts,
        "total_frames": total_frames,
        "frame_index": frame_ind,
        "worm_data": worm_data,
        "raw_mask_path": output_dir / "raw_mask.png",
        "annotated_mask_path": output_dir / "annotated_mask.png",
    }


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Analyze Tierpsy worm tracking outputs and generate "
            "an annotated mask image."
        )
    )

    parser.add_argument(
        "video_dir",
        type=Path,
        help="Directory containing the video's Tierpsy output files.",
    )

    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("."),
        help="Directory for output images (default: current directory).",
    )

    args = parser.parse_args()

    produce_output(args.video_dir, args.output_dir)


if __name__ == "__main__":
    main()
