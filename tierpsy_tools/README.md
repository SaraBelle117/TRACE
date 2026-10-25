# TRACE – Tierpsy Tracker output tools

Four Python scripts that turn Tierpsy Tracker results into CSV files and an ID image.

| # | Script | Input | Output |
|---|---|---|---|
| 1 | `features_to_csv.py` | `VIDEO_featuresN.hdf5` | Per-worm, per-frame features CSV |
| 2 | `thrashing_to_csv.py` | CSV from script 1 | Thrashing frequency per worm (bends/min) |
| 3 | `bodysize_to_csv.py` | CSV from script 1 | Body size per worm (area or length) |
| 4 | `annotate_first_frame.py` | One video's Tierpsy output folder | Image of one frame with worm IDs |

Run script 1 first. Scripts 2 and 3 use its CSV.

*Tested with Spyder 6 (Windows). Menu names may differ in other versions; the console method in section 2 works in Spyder 5 and 6.*

---

## 1. One-time setup

### 1.1 Install Spyder
Download and install Spyder from spyder-ide.org (the standalone installer).

### 1.2 Install the required packages
Spyder comes with its own Python, which does not include everything these scripts need.

1. Open Spyder.
2. In the **IPython Console** (bottom-right panel), type the line below and press Enter. Replace the path with where you saved this folder:
   ```
   %pip install -r "C:\path\to\this\folder\requirements.txt"
   ```
3. When it finishes, restart the console: **Consoles → Restart kernel**.

You only need to do this once per computer.

---

## 2. How to run a script in Spyder

Every script needs **input and output paths**. Spyder does not ask for them, so you give them when you run the script.

### Main method: the IPython Console
Type one line in the IPython Console (bottom-right panel) and press Enter. The general form is:
```
runfile(r"SCRIPT PATH", args=r'"INPUT PATH" "OUTPUT PATH"', wdir=r"FOLDER WITH THE SCRIPTS")
```
- `r"..."`: keep the `r` in front of each path. It stops Windows backslashes (`\`) from being misread.
- `args=r'...'`: the whole argument list goes inside **single** quotes, and each path inside it goes in **double** quotes.
- Full paths are safest.

Section 3 has a ready-to-edit line for each script.

Messages and errors appear in the console. A successful run ends with a line starting with `Wrote …`.

### Alternative: Spyder menus
1. **File → Open**, and open the script.
2. **Run → Configuration per file…** (Ctrl+F6).
3. Under **Working directory**, select **"The directory of the file being executed"**.
4. Check **"Command line options"**, and type the arguments, e.g. `"C:\path\to\input" "C:\path\to\output"`.
5. Click **Run**, or press the green **Run file** button.

If you see `the following arguments are required: input, output`, the paths were not given. Check the `args` part (console) or the command line options (menus).

---

## 3. The scripts

Replace `C:\TRACE` with the folder where you saved these scripts, and replace the input and output paths with your own.

### Script 1 – `features_to_csv.py`
```
runfile(r"C:\TRACE\features_to_csv.py", args=r'"C:\data\VIDEO_featuresN.hdf5" "C:\data\features.csv"', wdir=r"C:\TRACE")
```
Optional, added inside `args`:
- `--well-px 1032`: well inner diameter in pixels (see section 4). Default 1032.
- `--fps 15`: video frame rate. Default 15.

Example with options: `args=r'"C:\data\VIDEO_featuresN.hdf5" "C:\data\features.csv" --well-px 1032 --fps 15'`

**Output columns and units:**

| Column | Unit |
|---|---|
| `worm_index` | Tierpsy worm ID |
| `timestamp` | frame number |
| `length` | µm |
| `area` | mm² |
| `speed`, `speed_midbody` | mm/s |
| `width_head_base`, `width_midbody`, `width_tail_base` | pixels (unconverted) |
| `curvature_head`, `curvature_midbody`, `curvature_tail`, `d_curvature_midbody` | Tierpsy units, per pixel (unconverted) |
| `angular_velocity`, `motion_mode` | Tierpsy units (unconverted) |
| `coord_x_body`, `coord_y_body` | pixels |

### Script 2 – `thrashing_to_csv.py`
```
runfile(r"C:\TRACE\thrashing_to_csv.py", args=r'"C:\data\features.csv" "C:\data\thrashing.csv"', wdir=r"C:\TRACE")
```
Optional, added inside `args`:
- `--fps 15`: video frame rate. Default 15.
- `--window 10`: averaging window in seconds. Default 10.

**Output:** one row per frame. Columns are `timestamp`, `time_s`, then one column per worm (`worm_ID`) with **thrashes per minute**. One thrash is one completed body bend ("<" → ">" → back to "<"). Empty cells mean the worm wasn't tracked in that frame.

### Script 3 – `bodysize_to_csv.py`
```
runfile(r"C:\TRACE\bodysize_to_csv.py", args=r'"C:\data\features.csv" "C:\data\bodysize.csv"', wdir=r"C:\TRACE")
```
Optional, added inside `args`:
- `--measure area` (default) or `--measure length`
- `--fps 15`: video frame rate. Default 15.

**Output:** one row per frame. Columns are `timestamp`, `time_s`, then one column per worm (`worm_ID`). Area is in **mm²**; length is in **µm**.

### Script 4 – `annotate_first_frame.py`
```
runfile(r"C:\TRACE\annotate_first_frame.py", args=r'"C:\data\VIDEO Tierpsy output folder" -o "C:\data\output folder"', wdir=r"C:\TRACE")
```
The input folder must contain the Tierpsy files for **one video only**: `VIDEO.hdf5` (masks), `VIDEO_skeletons.hdf5`, and `VIDEO_featuresN.hdf5`. Subfolders such as `MaskedVideos` and `Results` are fine.

**Output** (in the `-o` folder):
- `raw_mask.png`: the selected frame's mask
- `annotated_mask.png`: the same frame with each worm's ID, center point, and box

The script picks the first frame where all worms are detected.

---

## 4. Units and calibration

Tierpsy was run without a pixel size, so its raw output is in pixels. Script 1 converts to real units using the well:
- Well inner diameter: **15.6 mm** (dark edge to dark edge)
- Default well diameter in the video: **1032 pixels** (camera setup used for the 9/22 FMO4KO recording), which gives about 15.1 µm per pixel

**If the camera zoom or lens has changed:** measure the well's inner diameter (dark edge to dark edge) in pixels on one video frame, using any image tool that shows pixel positions (e.g. ImageJ/Fiji), and pass that number as `--well-px`. If you're unsure, contact the TRACE team.

---

## 5. Troubleshooting

| Message | Fix |
|---|---|
| `the following arguments are required: input, output` | The paths were not given. Check the `args` part (section 2). |
| `ModuleNotFoundError: No module named '…'` | Run the `%pip install` step (section 1.2), then restart the kernel. |
| `FileNotFoundError` | Check the path. Use full paths, with the quotes as shown in section 3. |
| `SyntaxError` on the `runfile` line | Check the quotes: single quotes around the whole `args`, double quotes around each path, and `r` before each. |
| Script 4: `must return 'skeletons' and 'masks'` | The input folder must contain one video's Tierpsy files (section 3, script 4). |