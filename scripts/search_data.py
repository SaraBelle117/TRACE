from pathlib import Path
import os

VIDEO_DATA_BASE_DIR_STR = "../data/Worm_Movies_Tierpsy_Jang Lab"
VIDEO_DATA_BASE_DIR = Path(VIDEO_DATA_BASE_DIR_STR)
video_directories = [x for x in VIDEO_DATA_BASE_DIR.iterdir() if x.is_dir()]

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
