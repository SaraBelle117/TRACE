import h5py
import numpy as np

FILE = "data/R3-cf_2026-09-22_FMO4KO_~D1-IMAGE-15_38_49_221_featuresN.hdf5"
X, Y, RADIUS = 655, 645, 40

with h5py.File(FILE, "r") as f:
    t = f["/trajectories_data"][:]

print("columns:", t.dtype.names)
dist = np.hypot(t["coord_x"] - X, t["coord_y"] - Y)
near = t[dist < RADIUS]
print(len(near), "rows within", RADIUS, "px of", (X, Y))
for row in near[:20]:
    print({k: row[k] for k in ("worm_index_joined", "frame_number", "coord_x", "coord_y", "area")})
    
print("unique IDs:", len(np.unique(t["worm_index_joined"])))
print("area min/median/max:", t["area"].min(), np.median(t["area"]), t["area"].max())
print("threshold values:", np.unique(t["threshold"])[:10])