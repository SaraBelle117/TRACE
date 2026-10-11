import cv2
import matplotlib.pyplot as plt

cap = cv2.VideoCapture("data/cf_2026-09-22_FMO4KO_~D1-IMAGE-15_38_49_221.avi")
ok, frame = cap.read()
plt.imshow(frame, cmap="gray")
plt.show()