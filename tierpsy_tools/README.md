# TRACE – Tierpsy Tracker output tools

Four Python scripts that turn Tierpsy Tracker results into CSV files and an ID image.

| # | Script | Input | Output |
|---|---|---|---|
| 1 | `features_to_csv.py` | `VIDEO_featuresN.hdf5` | Per-worm, per-frame features CSV |
| 2 | `thrashing_to_csv.py` | CSV from script 1 | Thrashing frequency per worm (bends/min) |
| 3 | `bodysize_to_csv.py` | CSV from script 1 | Body size per worm (area or length) |
| 4 | `annotate_first_frame.py` | One video's Tierpsy output folder | Image of one frame with worm IDs |

Run script 1 (`features_to_csv.py`) first. Scripts 2 (`thrashing_to_csv.py`) and 3 (`bodysize_to_csv.py`) use its CSV.

*Tested with Spyder 6 (Windows). Menu names may differ in other versions.*

---

## 1. One-time setup

### 1.1 Install Spyder and Python
1. Download and install Spyder from spyder-ide.org (the standalone installer).
2. Download and install Python from python.org (use the default options).

### 1.2 Open the `tierpsy_tools` folder in Spyder
The `tierpsy_tools` folder contains the four scripts, `requirements.txt`, and this README. This guide uses `C:\tierpsy_tools` as its location; if you put it somewhere else, use that path instead everywhere below.

1. Open Spyder.
2. **Projects → New Project…**
3. Select **Existing directory**, browse to the `tierpsy_tools` folder, and click **Create**.
4. The scripts appear in the **Projects** pane on the left. If it's hidden: **View → Panes → Projects**.

Next time, open it with **Projects → Recent Projects → tierpsy_tools**.

### 1.3 Install the required packages
Spyder's built-in Python cannot reliably install packages, so the scripts get their own Python environment, and Spyder is set to use it.

**A. Create the environment (in a Windows terminal, not Spyder)**
1. Press **Start**, type `cmd`, and press Enter.
2. Run these three commands, one at a time:
   ```
   cd C:\tierpsy_tools
   ```
   ```
   py -m venv .venv
   ```
   ```
   .venv\Scripts\python.exe -m pip install -r requirements.txt "spyder-kernels==3.1.*"
   ```

**B. Point Spyder to the environment**
1. In Spyder: **Tools → Preferences → IPython interpreter** (called **Python interpreter** in some versions).
2. Select **Use the following Python interpreter**, and browse to `C:\tierpsy_tools\.venv\Scripts\python.exe`.
3. Click **OK**.
4. **Consoles → Restart kernel**. If it is greyed out, use **Consoles → New console (default settings)**.

You only need to do this once per computer.

---

## 2. How to run a script in Spyder

Every script needs **input and output paths**. Spyder does not ask for them, so you give them when you run the script.

**Important: paths must not contain spaces.** Rename folders or files with spaces (e.g. use `_` instead) before running.

### Main method: the IPython Console
Type one line in the IPython Console (bottom-right panel) and press Enter. The general form is:
```
runfile(r"SCRIPT PATH", args=r'INPUT_PATH OUTPUT_PATH', wdir=r"C:\tierpsy_tools")
```
- `r"..."`: keep the `r` in front of each path. It stops Windows backslashes (`\`) from being misread.
- `args=r'...'`: the whole argument list goes inside **single** quotes. Separate the paths with a space. **Do not put quotes around the individual paths.**
- Full paths are safest.

Section 3 has a ready-to-edit line for each script.

Messages and errors appear in the console. A successful run ends with a line starting with `Wrote …` (scripts 1–3) or `Annotated mask: …` (script 4).

### Alternative: Spyder menus
1. Double-click the script in the **Projects** pane to open it.
2. **Run → Configuration per file…** (Ctrl+F6).
3. Under **Working directory**, select **"The directory of the file being executed"**.
4. Check **"Command line options"**, and type the arguments, e.g. `C:\path\to\input C:\path\to\output`.
5. Click **Run**, or press the green **Run file** button.

If you see `the following arguments are required: input, output`, the paths were not given. Check the `args` part (console) or the command line options (menus).

---

## 3. The scripts

Replace the input and output paths (`C:\data\...`) with your own.

### Script 1 – `features_to_csv.py`
```
runfile(r"C:\tierpsy_tools\features_to_csv.py", args=r'C:\data\VIDEO_featuresN.hdf5 C:\data\features.csv', wdir=r"C:\tierpsy_tools")
```
Optional, added inside `args`:
- `--well-px 1032`: well inner diameter in pixels (see section 4). Default 1032.
- `--fps 15`: video frame rate. Default 15.

Example with options: `args=r'C:\data\VIDEO_featuresN.hdf5 C:\data\features.csv --well-px 1032 --fps 15'`

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
runfile(r"C:\tierpsy_tools\thrashing_to_csv.py", args=r'C:\data\features.csv C:\data\thrashing.csv', wdir=r"C:\tierpsy_tools")
```
Optional, added inside `args`:
- `--fps 15`: video frame rate. Default 15.
- `--window 10`: averaging window in seconds. Default 10.

**Output:** one row per frame. Columns are `timestamp`, `time_s`, then one column per worm (`worm_ID`) with **thrashes per minute**. One thrash is one completed body bend ("<" → ">" → back to "<"). Empty cells mean the worm wasn't tracked in that frame.

### Script 3 – `bodysize_to_csv.py`
```
runfile(r"C:\tierpsy_tools\bodysize_to_csv.py", args=r'C:\data\features.csv C:\data\bodysize.csv', wdir=r"C:\tierpsy_tools")
```
Optional, added inside `args`:
- `--measure area` (default) or `--measure length`
- `--fps 15`: video frame rate. Default 15.

**Output:** one row per frame. Columns are `timestamp`, `time_s`, then one column per worm (`worm_ID`). Area is in **mm²**; length is in **µm**.

### Script 4 – `annotate_first_frame.py`
```
runfile(r"C:\tierpsy_tools\annotate_first_frame.py", args=r'C:\data\VIDEO_tierpsy_output -o C:\data\output', wdir=r"C:\tierpsy_tools")
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
| `doesn't have spyder-kernels version >=X,<Y installed` | In cmd, in `C:\tierpsy_tools`, run `.venv\Scripts\python.exe -m pip install "spyder-kernels==X.*"` using the X version from the message, then **Consoles → New console (default settings)**. |
| **Restart kernel** is greyed out | Use **Consoles → New console (default settings)**. |
| `'py' is not recognized` | Python is not installed. Do section 1.1, step 2, then open a new cmd window. |
| `the following arguments are required: input, output` | The paths were not given. Check the `args` part (section 2). |
| `ModuleNotFoundError: No module named '…'` | Spyder is not using the scripts' environment. Redo section 1.3 B. |
| `FileNotFoundError` with `"` in the path | Remove the quotes around the paths inside `args` (section 2). |
| `FileNotFoundError` | Check the path. Use full paths with no spaces. |
| `SyntaxError` on the `runfile` line | Check the quotes: single quotes around the whole `args`, and `r` before each quoted part. |
| Script 4: `must return 'skeletons' and 'masks'` | The input folder must contain one video's Tierpsy files (section 3, script 4). |