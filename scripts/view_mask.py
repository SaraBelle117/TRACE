import h5py
import matplotlib.pyplot as plt

FILE = "data/cf_2026-09-22_FMO4KO_~D1-IMAGE-15_38_49_221.hdf5"

with h5py.File(FILE, "r") as f:
    print("datasets:", list(f.keys()))
    mask = f["/mask"]
    print("frames:", mask.shape)
    frame = mask[0]

plt.imshow(frame, cmap="gray")
plt.show()