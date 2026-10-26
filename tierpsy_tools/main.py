import bodysize_to_csv
import features_to_csv
import thrashing_to_csv
import annotate_first_frame
import argparse
from pathlib import Path

import pandas as pd
import cv2

# ----------------------------------------------------------------- #

# vv DEFINE INPUT AND OUTPUT PATHS HERE vv

data_path = "../data/box_folder/2026-10-13_PolarizerA"
DEFAULT_OUTPUT_DIR = "output"

# -------------------------------------- #

THRASH_FREQ_SLIDING_WINDOW_IN_S = 10
USE_CMD_ARGS = False

# ----------------------------------------------------------------- #

def get_video_fps(video_path: str) -> float:
    """
    Opens a video file and returns its frame rate (FPS).
    Returns 0.0 if the file cannot be opened or if the FPS metadata is missing.
    """
    # Create a VideoCapture object for the file
    video = cv2.VideoCapture(video_path)
    
    # Check if the video opened successfully
    if not video.isOpened():
        print(f"Error: Could not open video file {video_path}")
        return 0.0
        
    # Retrieve the container frame rate metadata
    fps = video.get(cv2.CAP_PROP_FPS)
    
    # Release the video file resource immediately
    video.release()
    
    return float(fps)

def write_csv(df: pd.DataFrame, out_path: Path) -> None:
    """Sort and write to CSV."""
    df = df.sort_values(["worm_index", "timestamp"])
    df.to_csv(out_path, index=False)

if USE_CMD_ARGS:
    parser = argparse.ArgumentParser(prog='Tierpsy Output Analysis Script', usage= "python main.py data_directory [-o/--out_dir out_dir]", description='Produce requested outputs from a directory containing both the original video and the tierpsy hdf5 outputs.', epilog='See the read me for usage details.')
    parser.add_argument('data_dir')
    parser.add_argument('-o', '--out_dir')      # option that takes a value
    
    args = parser.parse_args()
    data_dir = args.data_dir
    out_dir = args.out_dir if args.out_dir is not None else DEFAULT_OUTPUT_DIR
else:
    data_dir = data_path
    out_dir = DEFAULT_OUTPUT_DIR

data_path = Path(data_dir)
out_path = Path(out_dir)
# Check if the directory exists
if not data_path.is_dir():
    print("The provided data directory does not exist.")
    exit()
# Get the relevant output paths
all_outputs = annotate_first_frame.get_all_output_paths(data_path)
out_path.mkdir(parents=True, exist_ok=True)


vid_fps = get_video_fps(all_outputs["video"])

df = features_to_csv.read_timeseries(all_outputs["featuresN"])
df = features_to_csv.select_columns(df)
write_csv(df, out_path / "features.csv")

# Use a new copy of the data frame for each modifictation
df1 = df.copy()
df2 = df.copy()

bodysize_to_csv.make_wide(df, "area", vid_fps)
bodysize_to_csv.make_wide(df1, "length", vid_fps)
thrashing_to_csv.make_wide(df2, vid_fps, THRASH_FREQ_SLIDING_WINDOW_IN_S)

write_csv(df, out_path / "body_area.csv")
write_csv(df1, out_path / "body_length.csv")
write_csv(df2, out_path / "thrashing_frequency.csv")

annotate_first_frame.produce_output(data_path, out_path)




