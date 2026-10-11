import cv2
import matplotlib.pyplot as plt

cap = cv2.VideoCapture("data/2026-09-18_FMO4KO_D1_oldlens_polarized-IMAGE-14_11_03_267.avi")
cap.set(cv2.CAP_PROP_POS_FRAMES, 27437)
ok, frame = cap.read()
plt.imshow(frame, cmap="gray")
plt.plot(857, 1124, "r+", markersize=20)
plt.show()