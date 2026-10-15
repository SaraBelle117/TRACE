import cv2
import matplotlib.pyplot as plt

V22 = "data/cf_2026-09-22_FMO4KO_~D1-IMAGE-15_38_49_221.avi"
V18 = "data/2026-09-18_FMO4KO_D1_oldlens_polarized-IMAGE-14_11_03_267.avi"

checks = [
    ("9/22 worm_10", V22, 0, 213, 1040),
    ("9/18 track 4707", V18, 27437, 857, 1124),
    ("c02 track 281", V22, 2820, 270, 1160),
    ("c02 track 1965", V22, 19880, 341, 1200),
    ("c02 track 3141", V22, 35380, 1213, 1166),
]

for name, video, frame_no, x, y in checks:
    cap = cv2.VideoCapture(video)
    print(name, "opened:", cap.isOpened(), "frames:", int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
    ok, frame = cap.read()
    if not ok:
        print("  could not read frame", frame_no, "- skipping")
        continue
    plt.imshow(frame, cmap="gray")
    plt.plot(x, y, "r+", markersize=20)
    plt.title(f"{name} (frame {frame_no})")
    plt.show()