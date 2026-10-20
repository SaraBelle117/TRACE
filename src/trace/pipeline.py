"""TRACE OpenCV pipeline.

Ported from the trace notebook in src/trace/io/.
Detects, skeletonizes and tracks worms in a video and writes per-worm CSV outputs.

Usage:
    python src/trace/pipeline.py data/clip10s_2026-09-22.avi output
"""

# %% Imports
import os
from typing import Dict, List, Tuple
import av
import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import argparse
import signal
import threading
import glob
import tempfile
from fractions import Fraction
from scipy import ndimage as ndi
from scipy.ndimage import gaussian_filter1d, map_coordinates
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from skimage.morphology import skeletonize
from scipy.optimize import linear_sum_assignment

# OS-level file locking: each module exists only on its own OS
if os.name == "nt":
    import msvcrt # Windows
else:
    import fcntl # Mac/Linux


# %% Video Handling: VideoLoader
# Load frames one by one in grayscale
class VideoLoader:

    def __init__(self, input_video):
        self.input_video = input_video
        self.container = av.open(input_video)

        stream = self.container.streams.video[0]

        self.fps = max(1, int(round(float(stream.average_rate)))) if stream.average_rate is not None else None
        self.frame_timestep = 1 / self.fps
        self.frame_w = stream.width
        self.frame_h = stream.height
        self.total_frames = stream.frames

        self.frames = self.container.decode(video=0)
        self.frame_ind = 0

        self.duration = (float(self.container.duration) / av.time_base
            if self.container.duration is not None
            else None
        )

    def reset(self):
        self.container.seek(0)
        self.frames = self.container.decode(video=0)
        self.frame_ind = 0

    def get_next_frame(self):
        res = next(self.frames)
        self.frame_ind += 1
        return res.to_ndarray(format='gray8')

    def get_fps(self):
        return self.fps

    def get_frame_timestep(self):
        return self.frame_timestep

    def get_frame_w(self):
        return self.frame_w

    def get_frame_h(self):
        return self.frame_h

    def get_frame_timestamp(self, frame_ind: int):
        return self.frame_timestep * frame_ind

    def get_last_frame_timestamp(self):
        return self.get_frame_timestamp(self.frame_ind-1)

    def get_total_frames(self):
        return self.total_frames

    def get_frame_ind(self):
        return self.frame_ind

    def get_duration(self):
        return self.duration


# %% Video Handling: VideoWriter
class VideoWriter:

    def __init__(self, output_video, fps, width, height):
        self.output_video = output_video
        self.fps = fps
        self.width = width
        self.height = height

        self.container = av.open(output_video, mode='w')
        self.stream = self.container.add_stream('mpeg4', rate=fps)
        self.stream.width = width
        self.stream.height = height
        self.stream.pix_fmt = 'yuv420p' # Alternatively, 'gray' is grayscale, 'monow' is binary white, and 'monob' is binary black.

    def write_frame(self, frame):
        # Create an AVFrame from the RGB frame
        av_frame = av.VideoFrame.from_ndarray(frame, format='rgb24')

        # Encode the frame and write it to the container
        for packet in self.stream.encode(av_frame):
            self.container.mux(packet)

    def close(self):
        # Flush the encoder and write any remaining packets
        for packet in self.stream.encode():
            self.container.mux(packet)

        # Close the container
        self.container.close()


# %% Preprocessing: find_background
def find_background(video, n, k):
    """
    >> CONTAINS GENERATED CODE <<

    Estimate the background of a video using n sampled frames,
    taking every k-th frame.

    Parameters:
        video: VideoLoader
        n: Number of frames to sample
        k: Number of frames to skip between samples

    Returns:
        A grayscale NumPy array representing the estimated background.
    """
    video.reset()
    frames = []
    try:
        for _ in range(n):
            # Get the next frame
            frames.append(video.get_next_frame())
            # Skip k frames
            for _ in range(k):
                video.get_next_frame()
    except StopIteration:
        pass

    if not frames:
        return None

    # Stack frames and calculate median for every pixel
    frames = np.stack(frames, axis=0)

    background = np.median(np.stack(frames, axis=0), axis=0).astype(np.uint8)
    video.reset()
    return background


# %% Preprocessing: preprocess_frame
def preprocess_frame(
    frame: np.ndarray,
    background: np.ndarray,
    threshold_cap: int = 8,
    threshold_offset: int = 2,
    kernel_size: int = 5,
) -> np.ndarray:

    dark_difference = cv2.subtract(background, frame)
    dark_difference = cv2.medianBlur(dark_difference, 3)

    otsu_threshold, _ = cv2.threshold(
        dark_difference,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU,
    )

    threshold = max(
        0,
        min(otsu_threshold, threshold_cap) - threshold_offset,
    )

    _, mask = cv2.threshold(
        dark_difference,
        threshold,
        255,
        cv2.THRESH_BINARY,
    )

    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (kernel_size, kernel_size),
    )

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_CLOSE,
        kernel,
    )

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        mask,
        connectivity=8,
    )

    keep_labels = np.flatnonzero(
        stats[1:, cv2.CC_STAT_AREA] >= 12
    ) + 1

    mask = np.where(
        np.isin(labels, keep_labels),
        255,
        0,
    ).astype(np.uint8)

    return mask


# %% Single Frame Analysis: skeletal_analysis
def skeletal_analysis(
    mask,
    pixel_size=1.0,
    head_xy=None,
    head_frac=0.1,
    mid_frac=0.5,
    tail_frac=0.9,
    window=0.03,
    smooth_sigma=3.0,
    extend_ends=True,
    return_centerline=False,
):
    """
    Measure length, geodesic midpoint, curvature and width of one worm.

    Generated by Claude (Anthropic) -- see the disclaimer at the top of this file.

    Method
    ------
    1. Clean the mask (largest component, holes filled).
    2. Skeletonize it and take the longest geodesic path through the skeleton; this
       is the worm's centerline. Side spurs are ignored automatically.
    3. Extend the centerline to the worm's tips, resample it to ~1 px spacing and
       smooth it.
    4. Read length, midpoint, curvature and width off the smoothed centerline.

    Parameters
    ----------
    mask : 2D array
        Binary mask containing a single worm (non-zero = worm).
    pixel_size : float
        Physical size of one pixel (e.g. um/px). Length and width are multiplied by
        it; curvature (1/length) is divided by it. Use 1.0 to stay in pixels.
    head_xy : (x, y) or None
        Approximate head location in image coordinates. A mask alone contains no
        head/tail information. If None, the end with the wider cross-section is
        assumed to be the head, which is only a guess -- pass this when you can.
    head_frac, mid_frac, tail_frac : float
        Positions along the body (0 = head tip, 1 = tail tip) where curvature and
        width are sampled. Tips are noisy, so head/tail default to 10% and 90%.
    window : float
        Half-width, as a fraction of body length, averaged around each position.
    smooth_sigma : float
        Gaussian smoothing (pixels) applied to the centerline. Larger values give
        smoother but flatter curvature. Keep it consistent across a dataset.
    extend_ends : bool
        Extend the skeleton to the tips (skeletons stop about one radius short).
    return_centerline : bool
        Also return the smoothed centerline as an (N, 2) array of (x, y) pixels,
        handy for overlaying on the image to check the fit.

    Returns
    -------
    dict
        length             : centerline length (pixels * pixel_size)
        geodesic_midpoint  : (x, y) in pixels, halfway along the centerline
        head_point         : (x, y) in pixels, the extreme tip at the head end
        tail_point         : (x, y) in pixels, the extreme tip at the tail end
        curvature          : {"head", "midbody", "tail"}, signed, in 1/length unit
        width              : {"head", "midbody", "tail"}, in length unit
        centerline         : only if return_centerline=True

    Limitations
    -----------
    Assumes one worm that does not cross or touch itself. Loops or junctions in the
    skeleton make the longest-path centerline (and therefore length) unreliable.
    Filling holes also closes real gaps inside tightly coiled worms.
    """

    # ------------------------------------------------------------------
    # 1. Clean the mask: keep the largest component and fill holes
    # ------------------------------------------------------------------
    mask = np.asarray(mask) > 0
    labels, n_components = ndi.label(mask, structure=np.ones((3, 3)))
    if n_components == 0:
        raise ValueError("Mask is empty.")
    if n_components > 1:
        sizes = ndi.sum(mask, labels, range(1, n_components + 1))
        mask = labels == (np.argmax(sizes) + 1)
    mask = ndi.binary_fill_holes(mask)

    # Distance to background, used later to measure width
    dist = ndi.distance_transform_edt(mask)

    # ------------------------------------------------------------------
    # 2. Centerline: longest geodesic path through the skeleton
    # ------------------------------------------------------------------
    skeleton = skeletonize(mask)
    pixels = np.argwhere(skeleton)  # (row, col) of every skeleton pixel
    if len(pixels) < 2:
        raise ValueError("Skeleton has fewer than 2 pixels.")

    # Graph: one node per skeleton pixel, edges between 8-connected neighbours
    # (weight 1 for side-by-side, sqrt(2) for diagonal).
    node_at = -np.ones(skeleton.shape, dtype=np.int64)
    node_at[pixels[:, 0], pixels[:, 1]] = np.arange(len(pixels))

    edge_from, edge_to, edge_weight = [], [], []
    for d_row, d_col in [(0, 1), (1, -1), (1, 0), (1, 1)]:  # forward neighbours only
        nb_row, nb_col = pixels[:, 0] + d_row, pixels[:, 1] + d_col
        inside = ((nb_row >= 0) & (nb_row < skeleton.shape[0]) &
                  (nb_col >= 0) & (nb_col < skeleton.shape[1]))
        src = np.nonzero(inside)[0]
        dst = node_at[nb_row[src], nb_col[src]]
        is_skeleton = dst >= 0
        edge_from.append(src[is_skeleton])
        edge_to.append(dst[is_skeleton])
        edge_weight.append(np.full(is_skeleton.sum(), np.hypot(d_row, d_col)))

    graph = coo_matrix(
        (np.concatenate(edge_weight), (np.concatenate(edge_from), np.concatenate(edge_to))),
        shape=(len(pixels), len(pixels)),
    ).tocsr()

    # Two sweeps find the geodesically farthest pair of pixels: the pixel farthest
    # from an arbitrary start is one end; the pixel farthest from that is the other.
    dist_from_start = dijkstra(graph, directed=False, indices=0)
    dist_from_start[np.isinf(dist_from_start)] = -1  # ignore disconnected fragments
    end_a = int(np.argmax(dist_from_start))

    dist_from_a, predecessors = dijkstra(
        graph, directed=False, indices=end_a, return_predecessors=True
    )
    dist_from_a[np.isinf(dist_from_a)] = -1
    end_b = int(np.argmax(dist_from_a))

    # Walk back from end_b to end_a to recover the ordered path
    node_path = [end_b]
    while node_path[-1] != end_a:
        node_path.append(predecessors[node_path[-1]])
    path = pixels[node_path][:, ::-1].astype(float)  # convert to (x, y)

    # ------------------------------------------------------------------
    # 3. Extend to the tips, resample to ~1 px spacing, smooth
    # ------------------------------------------------------------------
    if extend_ends and len(path) > 3:
        k = min(10, len(path) - 1)  # look k pixels inward to get the end's direction
        tips = []
        for tip, inward in ((path[0], path[k]), (path[-1], path[-1 - k])):
            direction = tip - inward
            direction /= np.hypot(*direction)
            point = tip.copy()
            for _ in range(400):  # walk outward in half-pixel steps until we leave the mask
                candidate = point + 0.5 * direction
                col, row = int(np.floor(candidate[0] + 0.5)), int(np.floor(candidate[1] + 0.5))
                inside = 0 <= row < mask.shape[0] and 0 <= col < mask.shape[1]
                if not inside or not mask[row, col]:
                    break
                point = candidate
            tips.append(point)
        path = np.vstack([tips[0], path, tips[1]])

    # Remember the extreme end points now: smoothing pulls the ends slightly inward.
    # (With extend_ends=True these sit on the mask boundary at the worm's tips.)
    end_point_1, end_point_2 = path[0].copy(), path[-1].copy()

    arc = np.r_[0, np.cumsum(np.hypot(*np.diff(path, axis=0).T))]
    arc_uniform = np.r_[np.arange(0, arc[-1], 1.0), arc[-1]]
    x = gaussian_filter1d(np.interp(arc_uniform, arc, path[:, 0]), smooth_sigma, mode="nearest")
    y = gaussian_filter1d(np.interp(arc_uniform, arc, path[:, 1]), smooth_sigma, mode="nearest")

    arc = np.r_[0, np.cumsum(np.hypot(np.diff(x), np.diff(y)))]  # arc length of smoothed curve
    length = arc[-1]

    # ------------------------------------------------------------------
    # 4. Width along the centerline
    #    Twice the distance to the background; -1 corrects for pixel-centre sampling.
    # ------------------------------------------------------------------
    width = np.clip(2 * map_coordinates(dist, [y, x], order=1) - 1, 1, None)

    # ------------------------------------------------------------------
    # 5. Orient the centerline head -> tail
    # ------------------------------------------------------------------
    if head_xy is not None:
        head_x, head_y = head_xy
        start_is_tail = (np.hypot(x[0] - head_x, y[0] - head_y) >
                         np.hypot(x[-1] - head_x, y[-1] - head_y))
    else:
        n_end = max(int(0.1 * len(arc)), 1)
        start_is_tail = width[:n_end].mean() < width[-n_end:].mean()  # wider end = head
    if start_is_tail:
        x, y, width = x[::-1], y[::-1], width[::-1]
        head_point, tail_point = end_point_2, end_point_1
    else:
        head_point, tail_point = end_point_1, end_point_2

    # ------------------------------------------------------------------
    # 6. Signed curvature with respect to arc length:
    #    kappa = (x'y'' - y'x'') / (x'^2 + y'^2)^(3/2)
    # ------------------------------------------------------------------
    dx, dy = np.gradient(x, arc), np.gradient(y, arc)
    ddx, ddy = np.gradient(dx, arc), np.gradient(dy, arc)
    curvature = (dx * ddy - dy * ddx) / np.power(dx**2 + dy**2, 1.5)

    # ------------------------------------------------------------------
    # 7. Sample at head / midbody / tail and assemble results
    # ------------------------------------------------------------------
    position = arc / length  # 0 = head tip, 1 = tail tip

    def average_near(values, fraction):
        """Mean of `values` within +/- `window` of a normalised body position."""
        near = np.abs(position - fraction) <= window
        if not near.any():
            return float(np.interp(fraction, position, values))
        return float(values[near].mean())

    midpoint = (float(np.interp(0.5, position, x)), float(np.interp(0.5, position, y)))

    results = {
        "length": length * pixel_size,
        "geodesic_midpoint": midpoint,
        "head_point": (float(head_point[0]), float(head_point[1])),
        "tail_point": (float(tail_point[0]), float(tail_point[1])),
        "curvature": {
            "head": average_near(curvature, head_frac) / pixel_size,
            "midbody": average_near(curvature, mid_frac) / pixel_size,
            "tail": average_near(curvature, tail_frac) / pixel_size,
        },
        "width": {
            "head": average_near(width, head_frac) * pixel_size,
            "midbody": average_near(width, mid_frac) * pixel_size,
            "tail": average_near(width, tail_frac) * pixel_size,
        },
    }
    if return_centerline:
        results["centerline"] = np.column_stack([x, y])
    return results

# This would be used for covariance method, if we go that direction
# def center_on_midpoint(mask, size=512):
#     """
#     Place a single-worm mask into a new square frame, with the worm's geodesic
#     midpoint at the frame center.

#     Parameters
#     ----------
#     mask : 2D array, nonzero = worm (one connected component).
#     size : side length (pixels) of the new square frame.

#     Returns
#     -------
#     centered : uint8 array (size, size), values 0/255.
#     info     : dict with
#         midpoint_xy   - original (x, y) midpoint, sub-pixel
#         shift_xy      - integer (dx, dy) applied to the mask
#         clipped       - True if any worm pixels fell outside the new frame
#         pixels_lost   - number of worm pixels cut off (0 if not clipped)
#     """
#     binary = mask > 0
#     height, width = binary.shape

#     # Geodesic midpoint, rounded to a whole pixel so the mask isn't resampled
#     mid_x, mid_y = worm_midbody(binary)["midpoint_xy"]
#     shift_x = size // 2 - int(round(mid_x))
#     shift_y = size // 2 - int(round(mid_y))

#     # Region of the original that lands inside the new frame
#     src_x0, src_x1 = max(0, -shift_x), min(width, size - shift_x)
#     src_y0, src_y1 = max(0, -shift_y), min(height, size - shift_y)

#     centered = np.zeros((size, size), dtype=np.uint8)
#     if src_x1 > src_x0 and src_y1 > src_y0:
#         centered[src_y0 + shift_y:src_y1 + shift_y,
#                  src_x0 + shift_x:src_x1 + shift_x] = \
#             binary[src_y0:src_y1, src_x0:src_x1] * 255

#     lost = int(binary.sum() - (centered > 0).sum())
#     info = dict(midpoint_xy=(mid_x, mid_y), shift_xy=(shift_x, shift_y),
#                 clipped=lost > 0, pixels_lost=lost)
#     return centered, info


# %% Single Frame Analysis: analyze_frame
def analyze_frame(mask: np.ndarray, timestamp: float) -> Tuple[np.ndarray, int, List[Dict]]:
    num_components, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)

    pad = 2 # background border (px) kept around each blob crop
    frame_h, frame_w = mask.shape

    components = []
    bounding_boxes = []
    for i in range(1, num_components):  # Skip the background (label 0)
        # Morphology stats that we care about
        # Bounding box of blob i, expanded by pad on every side and clamped to the frame
        left = stats[i, cv2.CC_STAT_LEFT]
        top = stats[i, cv2.CC_STAT_TOP]
        width = stats[i, cv2.CC_STAT_WIDTH]
        height = stats[i, cv2.CC_STAT_HEIGHT]
        x0 = max(left - pad, 0)
        y0 = max(top - pad, 0)
        x1 = min(left + width + pad, frame_w)
        y1 = min(top + height + pad, frame_h)

        # Blob i only, cropped to its box: 255 where a pixel belongs to blob i, 0 elsewhere
        blob_crop = (labels[y0:y1, x0:x1] == i).astype(np.uint8) * 255

        # component_mask = (labels == i).astype(np.uint8) * 255
        try:
            component_skeletal_metrics = skeletal_analysis(blob_crop)
        except ValueError:
                continue # speck/junk blob with no usable skeleton (skip it)

        contours, _ = cv2.findContours(blob_crop, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        largest_contour = max(contours, key=cv2.contourArea)
        hull = cv2.convexHull(largest_contour)
        perimeter = cv2.arcLength(largest_contour, True)

        components.append({
            "timestamp": timestamp,
            "length": component_skeletal_metrics["length"],
            "area": stats[i, cv2.CC_STAT_AREA],
            "perimeter": perimeter,
            "solidity" : stats[i, cv2.CC_STAT_AREA] / cv2.contourArea(hull),
            "compactness" : (4 * np.pi * stats[i, cv2.CC_STAT_AREA]) / (perimeter ** 2),
            "width_head_base" : component_skeletal_metrics["width"]["head"],
            "width_midbody" : component_skeletal_metrics["width"]["midbody"],
            "width_tail_base" : component_skeletal_metrics["width"]["tail"],
            "speed" : 0,                                # Calculated from displacement later
            "motion_mode" : 0,                          # TODO Not sure how to do this yet
            "curvature_head" : component_skeletal_metrics["curvature"]["head"],
            "curvature_midbody" : component_skeletal_metrics["curvature"]["midbody"],
            "d_curvature_midbody" : 0,                  # Calculated later
            "curvature_tail" : component_skeletal_metrics["curvature"]["tail"],
            "coord_x_body" : centroids[i][0],
            "coord_y_body" : centroids[i][1],
            "head_x" : component_skeletal_metrics["head_point"][0] + x0,   # crop -> frame coords
            "head_y" : component_skeletal_metrics["head_point"][1] + y0,
            "tail_x" : component_skeletal_metrics["tail_point"][0] + x0,
            "tail_y" : component_skeletal_metrics["tail_point"][1] + y0,
        })

        bounding_boxes.append({
            "timestamp": timestamp,
            "x": left,
            "y": top,
            "width": width,
            "height": height,
        })

    return components, bounding_boxes


# %% Inter-frame Analysis: delta_calculation
# FOR NOW: I need to calculate the delta values for: displacement (which gives speed) and midbody curvature
def delta_calculation(worm_count: int, worm_data: Tuple[List[Dict[str, any]]], frame_timestep: int):
    for i in range(0, worm_count):
        current_worm = worm_data[i]

        # Skip delta calculations for the first row: they will be zero by default, since there is no previous frame to compare to.
        for j in range(1, len(current_worm)):
            current_worm_frame_data = current_worm[j]
            previous_worm_frame_data = current_worm[j-1]

            # Calculate delta values
            dx = current_worm_frame_data["midpoint_x"] - previous_worm_frame_data["midpoint_x"]
            dy = current_worm_frame_data["midpoint_y"] - previous_worm_frame_data["midpoint_y"]
            current_worm["speed"] = np.sqrt(dx**2 + dy**2) / frame_timestep
            current_worm["d_midbody_curvature"] = current_worm_frame_data["midbody_curvature"] - previous_worm_frame_data["midbody_curvature"]


# %% Inter-frame Analysis: stubs (TODO)
def thrashing_frequency_from_curvature():
    pass

def thrashing_frequency_from_covariance():
    pass

def state_classification():
    pass

# %% Tracking: WormTracker
# !!!!!!!!!!!!!!! THIS SHIT IS FROM CLAUDE

FEATS = ["length", "area", "width_midbody"]
BIG = 1e6

CFG = dict(
    base_gate=40.0,        # px, min search radius
    max_speed=60.0,        # px/s, upper bound on plausible worm speed (tune!)
    morph_tol=0.25,        # ~25% log-ratio difference = "1 unit" of morph cost
    w_space=1.0, w_morph=1.0,
    ambig_margin=0.3,      # flag if runner-up cost is within this of chosen cost
    merge_area_ratio=1.4,  # blob this much bigger than a track => likely merge
    max_missed=30,         # frames before a track is closed
    ema=0.1,               # feature smoothing
)

class Track:
    def __init__(self, tid, det):
        self.id = tid
        self.pos = np.array([det["coord_x_body"], det["coord_y_body"]], float)
        self.vel = np.zeros(2)
        self.t = det["timestamp"]
        self.feat = {k: float(det[k]) for k in FEATS}
        self.missed = 0
        self.occluded = False
        self.uncertain = False   # identity may have been swapped in a collision

    def predict(self, t):
        return self.pos + self.vel * (t - self.t)

    def gate(self, t):
        dt = max(t - self.t, 1e-6)
        return max(CFG["base_gate"], CFG["max_speed"] * dt)

    def update(self, det):
        t = det["timestamp"]
        new = np.array([det["coord_x_body"], det["coord_y_body"]], float)
        dt = max(t - self.t, 1e-6)
        if not self.occluded:
            self.vel = 0.5 * self.vel + 0.5 * (new - self.pos) / dt
            for k in FEATS:  # don't pollute features with merged-blob data
                self.feat[k] += CFG["ema"] * (det[k] - self.feat[k])
        self.pos, self.t, self.missed = new, t, 0


def morph_cost(track, det):
    d = [abs(np.log(max(det[k], 1e-6) / max(track.feat[k], 1e-6))) for k in FEATS]
    return np.mean(d) / CFG["morph_tol"]


def build_cost(tracks, dets, t):
    C = np.full((len(tracks), len(dets)), BIG)
    for i, tr in enumerate(tracks):
        pred, gate = tr.predict(t), tr.gate(t)
        for j, d in enumerate(dets):
            dist = np.hypot(d["coord_x_body"] - pred[0], d["coord_y_body"] - pred[1])
            if dist <= gate:
                C[i, j] = CFG["w_space"] * dist / gate + CFG["w_morph"] * morph_cost(tr, d)
    return C


class WormTracker:
    def __init__(self):
        self.tracks, self.next_id, self.closed = [], 0, []

    def step(self, dets, n_expected=None):
        """dets: list of per-component dicts for ONE frame.
        Adds 'track_id', 'flags', 'needs_review' to each det and returns dets."""
        if not dets:
            return dets
        t = dets[0]["timestamp"]
        for d in dets:
            d["flags"] = []
            d["track_id"] = None
        frame_flags = []
        if n_expected is not None and len(dets) != n_expected:
            frame_flags.append(f"count_mismatch({len(dets)}!={n_expected})")

        C = build_cost(self.tracks, dets, t) if self.tracks else np.empty((0, len(dets)))
        matches = {}
        if C.size:
            rows, cols = linear_sum_assignment(C)
            matches = {i: j for i, j in zip(rows, cols) if C[i, j] < BIG}

        # ---- ambiguity check on chosen pairs ----
        for i, j in matches.items():
            others = [C[i, jj] for jj in range(C.shape[1]) if jj != j]
            others += [C[ii, j] for ii in range(C.shape[0]) if ii != i]
            alt = min([c for c in others if c < BIG], default=None)
            if alt is not None and alt - C[i, j] < CFG["ambig_margin"]:
                dets[j]["flags"].append("ambiguous_assignment")

        matched_dets = set(matches.values())
        unmatched_tracks = [i for i in range(len(self.tracks)) if i not in matches]
        unmatched_dets = [j for j in range(len(dets)) if j not in matched_dets]

        # ---- merge / collision detection ----
        merged_dets = {}   # det idx -> list of track idx hidden inside it
        for i in unmatched_tracks:
            tr = self.tracks[i]
            pred, gate = tr.predict(t), tr.gate(t)
            for j, d in enumerate(dets):
                dist = np.hypot(d["coord_x_body"] - pred[0], d["coord_y_body"] - pred[1])
                if dist <= gate and d["area"] > CFG["merge_area_ratio"] * tr.feat["area"]:
                    merged_dets.setdefault(j, []).append(i)
                    break

        # also catch the case where one worm matched a blob that contains it
        # plus another worm (blob much bigger than its track)
        for i, j in list(matches.items()):
            if dets[j]["area"] > CFG["merge_area_ratio"] * self.tracks[i]["feat"]["area"] if False else \
               dets[j]["area"] > CFG["merge_area_ratio"] * self.tracks[i].feat["area"]:
                merged_dets.setdefault(j, []).append(i)
                del matches[i]

        for j, idxs in merged_dets.items():
            ids = [self.tracks[i].id for i in idxs]
            dets[j]["flags"].append(f"merged_blob(tracks={ids})")
            dets[j]["track_id"] = None
            dets[j]["merged_track_ids"] = ids
            for i in idxs:
                tr = self.tracks[i]
                tr.occluded, tr.uncertain = True, True
                tr.missed += 1
                tr.pos, tr.t = tr.predict(t), t   # coast on velocity

        # ---- apply matches ----
        for i, j in matches.items():
            tr = self.tracks[i]
            if tr.uncertain:
                dets[j]["flags"].append("post_collision_identity_uncertain")
                tr.uncertain = False
            tr.occluded = False
            tr.update(dets[j])
            dets[j]["track_id"] = tr.id

        # ---- tracks with nothing at all: lost ----
        still_lost = [i for i in unmatched_tracks
                      if not any(i in v for v in merged_dets.values())]
        for i in still_lost:
            self.tracks[i].missed += 1
            frame_flags.append(f"track_{self.tracks[i].id}_missing")
        survivors = []
        for tr in self.tracks:
            if tr.missed > CFG["max_missed"]:
                self.closed.append(tr)
                frame_flags.append(f"track_{tr.id}_closed")
            else:
                survivors.append(tr)
        self.tracks = survivors

        # ---- new tracks ----
        for j in unmatched_dets:
            if j in merged_dets:
                continue
            tr = Track(self.next_id, dets[j]); self.next_id += 1
            self.tracks.append(tr)
            dets[j]["track_id"] = tr.id
            if len(self.closed) or self.next_id > 1 and t != dets[0]["timestamp"]:
                pass
            dets[j]["flags"].append("new_track")

        for d in dets:
            d["frame_flags"] = frame_flags
            d["needs_review"] = bool(d["flags"] or frame_flags)
        return dets


# %% Tracking: orient_tracks
# CLAUDE-GENERATED: Trying to fix the head/tail swapping issue (w/ minor fixes from Sara)
def flip_orientation(det: Dict) -> None:
    """Swap head and tail of one detection, in place.

    Reading the centerline from the other end swaps the head/tail samples
    (taken at 10% / 90%, which mirror each other) and flips the sign of
    signed curvature. Widths are unsigned, so they are only swapped.
    """
    det["head_x"], det["tail_x"] = det["tail_x"], det["head_x"]
    det["head_y"], det["tail_y"] = det["tail_y"], det["head_y"]
    det["width_head_base"], det["width_tail_base"] = det["width_tail_base"], det["width_head_base"]
    det["curvature_head"], det["curvature_tail"] = -det["curvature_tail"], -det["curvature_head"]
    det["curvature_midbody"] = -det["curvature_midbody"]


def orient_tracks(detections: List[Dict]) -> None:
    """Make head/tail orientation consistent within each track, in place.

    skeletal_analysis guesses the head per frame ("wider end"), and near-ties
    make that guess flip between frames, which flips the curvature sign.
    """
    # Group detections by track (merged blobs have no track_id and are skipped)
    tracks = {}
    for det in detections:
        if det["track_id"] is not None:
            tracks.setdefault(det["track_id"], []).append(det)

    for dets in tracks.values():
        dets.sort(key=lambda d: d["timestamp"])

        # Pass 1: keep the head on the end nearest the previous frame's head.
        # prev is already corrected, so the orientation carries through the track.
        for prev, det in zip(dets, dets[1:]):
            same = np.hypot(det["head_x"] - prev["head_x"], det["head_y"] - prev["head_y"]) + \
                   np.hypot(det["tail_x"] - prev["tail_x"], det["tail_y"] - prev["tail_y"])
            swapped = np.hypot(det["head_x"] - prev["tail_x"], det["head_y"] - prev["tail_y"]) + \
                      np.hypot(det["tail_x"] - prev["head_x"], det["tail_y"] - prev["head_y"])
            if swapped < same:
                flip_orientation(det)

        # Pass 2: pick which end is the head for the whole track by majority vote
        # of "wider end = head", instead of trusting the first frame's guess
        head_wider = sum(d["width_head_base"] > d["width_tail_base"] for d in dets)
        if head_wider < len(dets) / 2:
            for det in dets:
                flip_orientation(det)


# %% Outputs: make_track_csv
def make_track_csv(input_csv, column, output_csv=None):
    """
    >> Generated by Claude <<
    Build a wide CSV from `input_csv` where:
      - the first column is 'timestamp'
      - every other column is a unique track_id
      - each cell holds the value of `column` (the label of a column in the
        original CSV) for that track_id at that timestamp (blank if the track
        has no row at that timestamp)

    Rows with a missing track_id are dropped, since they can't be assigned to a
    track column. Returns the resulting DataFrame.
    """
    df = pd.read_csv(input_csv)
    if column not in df.columns:
        raise ValueError(f"'{column}' not found. Available: {list(df.columns)}")

    df = df.dropna(subset=['track_id'])
    df['track_id'] = df['track_id'].astype(int)

    # Fail loudly if a track has two rows at the same timestamp
    if df.duplicated(['timestamp', 'track_id']).any():
        raise ValueError("Duplicate (timestamp, track_id) pairs found.")

    wide = df.pivot(index='timestamp', columns='track_id', values=column)
    wide = wide.sort_index(axis=0).sort_index(axis=1)
    wide.columns.name = None
    wide = wide.reset_index()  # 'timestamp' becomes the first column

    if output_csv is None:
        output_csv = f"{column}_by_track.csv"
    wide.to_csv(output_csv, index=False)
    return wide


# %% Pipeline: TracePipeline
# It is assumed that the first frame of the video contains all worms, and that they are clearly seperated.
class TracePipeline:

    # Temp mask file name parts: <output_dir>/.trace_masks_<random>.mkv
    TEMP_PREFIX = ".trace_masks_"
    TEMP_SUFFIX = ".mkv"
    LOCK_NAME = ".trace.lock" #  # <output_dir>/.trace.lock; one pipeline run per output folder


    @staticmethod
    def _handle_termination(signum, frame):
        """Convert SIGTERM/SIGBREAK into SystemExit so finally blocks (temp-file cleanup) run."""
        # 128 + signal num --> conventional exit code for "terminated by signal"
        raise SystemExit(128 + signum)

    def _acquire_output_lock(self):
        """Take an exclusive OS lock on <output_dir>/.trace.lock so only one run uses this folder.
        The OS releases the lock automatically if the process dies, so no stale-lock cleanup is needed."""
        lock_path = os.path.join(self.output_dir, self.LOCK_NAME)
        lock_file = open(lock_path, "a+b")  # creates the file if missing, never truncates it
        try:
            if os.name == "nt":
                lock_file.seek(0)  # msvcrt.locking locks starting at the current position
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)  # lock 1 byte; fail immediately if held
            else:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)  # exclusive, non-blocking
        except OSError:  # BlockingIOError (Mac/Linux) is a subclass of OSError
            lock_file.close()
            raise RuntimeError(f"Another pipeline run is already using {self.output_dir}")
        self._lock_file = lock_file

    def _release_output_lock(self):
        """Release the output-folder lock. Closing the file also releases it."""
        if self._lock_file is None:  # lock was never acquired
            return
        try:
            if os.name == "nt":
                self._lock_file.seek(0)
                msvcrt.locking(self._lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_UN)
        finally:
            self._lock_file.close()
            self._lock_file = None

    def _open_mask_writer(self):
        """Open the temp file as an FFV1 (lossless) video for pass 1 masks."""
        self._mask_container = av.open(self._temp_path, mode="w")
        self._mask_stream = self._mask_container.add_stream("ffv1", rate=int(self.video_loader.get_fps()))
        self._mask_stream.width = self.video_loader.get_frame_w()
        self._mask_stream.height = self.video_loader.get_frame_h()
        self._mask_stream.pix_fmt = "gray"  # 8-bit single channel; 0/255 masks are stored exactly
        self._mask_index = 0

    def _write_mask(self, mask):
        """Encode one mask with its frame number as the timestamp (explicit index)."""
        av_frame = av.VideoFrame.from_ndarray(mask, format="gray")
        av_frame.pts = self._mask_index  # frame number, in units of 1/fps
        av_frame.time_base = Fraction(1, int(self.video_loader.get_fps()))
        for packet in self._mask_stream.encode(av_frame):
            self._mask_container.mux(packet)
        self._mask_index += 1

    def _close_mask_writer(self):
        """Flush and close the mask writer. Safe to call twice or if it was never opened."""
        if self._mask_container is None:
            return
        try:
            for packet in self._mask_stream.encode():  # flush: encoder may still hold the last frames
                self._mask_container.mux(packet)
        finally:
            self._mask_container.close()
            self._mask_container = None
            self._mask_stream = None

    def _read_masks(self):
        """Yield masks from the temp file in order; stop with an error if a frame number doesn't match."""
        fps = int(self.video_loader.get_fps())
        with av.open(self._temp_path) as container:
            for expected, av_frame in enumerate(container.decode(video=0)):
                # the container may rescale timestamps (Matroska stores ms), so convert via seconds
                index = round(av_frame.time * fps)
                if index != expected:
                    raise RuntimeError(f"Temp mask file out of order: expected frame {expected}, got {index}")
                yield av_frame.to_ndarray(format="gray")

    def __init__(self, input_video, output_dir):
        self.output_dir = output_dir
        self._lock_file = None # open handle while this run holds the output folder lock
        self._temp_path = None
        self.video_loader = VideoLoader(input_video)
        self.video_writer = VideoWriter(f"{output_dir}/annotated_video.avi", int(self.video_loader.get_fps()), self.video_loader.get_frame_w(), self.video_loader.get_frame_h())

        self.background = find_background(self.video_loader, n=100, k=20)

        self.frame_data = []
        self._mask_container = None
        self._mask_stream = None
        self._mask_index = 0
        self.bounding_boxes = []
        self.true_worm_count = 0

        self.tracking_data = []

        # Print a summary of the loaded video details
        print(f"Analyzing {input_video} -> {output_dir}/annotated_video.avi: [ 'frame_c':{self.video_loader.get_total_frames()} , 'fps':{self.video_loader.get_fps()}, 'w':{self.video_loader.get_frame_w()}, 'h':{self.video_loader.get_frame_h()} ] ")

    def analyze_all_frames(self):
        if (self.background is None):
            print("Error: Could not find background.")
            return
        print("Analyzing all frames...")

        # Setup worm identification using the first frame to determine the number of worms and their initial positions
        first_frame = self.video_loader.get_next_frame()
        print(f"\tAnalyzing Frame: {self.video_loader.get_frame_ind()-1} @ {self.video_loader.get_last_frame_timestamp()}")
        preprocessed_first_frame = preprocess_frame(first_frame, self.background)
        worm_dat, bounding_boxes = analyze_frame(preprocessed_first_frame, self.video_loader.get_last_frame_timestamp())

        self.frame_data.append(worm_dat)
        self.true_worm_count = len(worm_dat)
        self._write_mask(preprocessed_first_frame)
        self.bounding_boxes.append(bounding_boxes)

        # Analyze the video frame by frame
        while True:
            try:
                # Get the next frame from the video
                frame = self.video_loader.get_next_frame()

                print(f"\tAnalyzing Frame: {self.video_loader.get_frame_ind()-1} @ {self.video_loader.get_last_frame_timestamp()}")

                # Preprocess the frame
                preprocessed_frame = preprocess_frame(frame, self.background)

                # Analyze a single frame
                worm_dat, bounding_boxes = analyze_frame(preprocessed_frame, self.video_loader.get_last_frame_timestamp())
                self._write_mask(preprocessed_frame)
                self.frame_data.append(worm_dat)
                self.bounding_boxes.append(bounding_boxes)

                # TEMP: So I don't have to wait 20 hours for the test output
                # if (self.video_loader.get_frame_ind() > 20): break

            except StopIteration:
                break
        print("All frames analyzed.")

    def identify_worms(self):
        print(f"Identifying worms...")
        tracker = WormTracker()
        for frame_dat in self.frame_data:
            self.tracking_data.extend(tracker.step(frame_dat, self.true_worm_count))
        orient_tracks(self.tracking_data)
        print("Worms Identified.")

    def save_outputs(self):
        # Create output video with labelled worms and bounding boxes
        print(f"Creating output video...")
        mask_count = 0
        for i, mask in enumerate(self._read_masks()):
            frame = cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB)

            for j in range(len(self.frame_data[i])):
                worm = self.frame_data[i][j]
                bbox = self.bounding_boxes[i][j]
                track_id = worm["track_id"]
                if track_id is not None:
                    centroid_x = int(worm["coord_x_body"])
                    centroid_y = int(worm["coord_y_body"])
                    cv2.putText(frame, f"ID: {track_id}", (centroid_x + 25, centroid_y - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    cv2.circle(frame, (centroid_x, centroid_y), 5, (0, 255, 0), -1)
                    cv2.rectangle(frame, (bbox["x"], bbox["y"]), (bbox["x"] + bbox["width"], bbox["y"] + bbox["height"]), (255, 0, 0), 2)


            self.video_writer.write_frame(frame)
            mask_count = i + 1
        if mask_count != len(self.frame_data):
            raise RuntimeError(f"Temp mask file has {mask_count} frames, expected {len(self.frame_data)}")
        self.video_writer.close()

        print("Saving Results to output.csv...")
        dataframe = pd.DataFrame(self.tracking_data)
        dataframe.to_csv(f"{self.output_dir}/output.csv", index=False)
        make_track_csv(f"{self.output_dir}/output.csv", "length", f"{self.output_dir}/length_by_track.csv")
        make_track_csv(f"{self.output_dir}/output.csv", "area", f"{self.output_dir}/area_by_track.csv")
        make_track_csv(f"{self.output_dir}/output.csv", "d_curvature_midbody", f"{self.output_dir}/d_curvature_midbody_by_track.csv")
        print("All outputs generated.")

    def run(self):
        print("Pipeline Run Started.")

        previous_handlers = {} # signal -> handler active
        if threading.current_thread() is threading.main_thread():
            for sig_name in ("SIGTERM", "SIGBREAK"):
                sig = getattr(signal, sig_name, None)
                if sig is not None:
                    previous_handlers[sig] = signal.signal(sig, self._handle_termination) # returns old handler
        try:
            # one run per output folder
            self._acquire_output_lock()

            # remove temp mask files left by earlier runs that were hard-killed (crash)
            pattern = os.path.join(self.output_dir, self.TEMP_PREFIX + "*" + self.TEMP_SUFFIX)
            for stale in glob.glob(pattern):
                try:
                    os.remove(stale)
                except OSError: # e.g. still open by another process on Windows (skip it)
                    pass
            # create this run's temp mask file
            fd, self._temp_path = tempfile.mkstemp(prefix=self.TEMP_PREFIX, suffix=self.TEMP_SUFFIX, dir=self.output_dir)
            os.close(fd)
            self._open_mask_writer()

            self.analyze_all_frames()
            self._close_mask_writer()
            self.identify_worms()
            self.save_outputs()
        finally:
            self._close_mask_writer() # Windows can't delete an open file
            if self._temp_path is not None: # None if mkstemp never ran
                try:
                    os.remove(self._temp_path)
                except OSError:
                    pass
                self._temp_path = None
            self._release_output_lock()
            # restore whatever handlers were active before run()
            for sig, handler in previous_handlers.items():
                if handler is not None: # none = old handler
                    signal.signal(sig, handler)

        print("Pipeline Run Completed.")


# %% Testing: test_preprocessing
def test_preprocessing(input_video, output_dir):
    video_loader = VideoLoader(input_video)
    background = find_background(video_loader, n=100, k=20)
    video_loader.reset()
    frame = video_loader.get_next_frame()
    preprocessed_frame = preprocess_frame(frame, background)
    cv2.imwrite(f"{output_dir}/raw_frame.png", frame)
    cv2.imwrite(f"{output_dir}/preprocessed_frame.png", preprocessed_frame)


# %% Entry Point
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the TRACE OpenCV pipeline on one video.")
    parser.add_argument("input_video", help="path to the input video")
    parser.add_argument("output_dir", help="folder for the outputs (created if missing)")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    test_preprocessing(args.input_video, args.output_dir)
    pipeline = TracePipeline(args.input_video, args.output_dir)
    pipeline.run()
