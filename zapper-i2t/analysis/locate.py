import cv2, numpy as np
S = cv2.imread(r"C:/AI Pipeline Test/jinx-i2t/ref/pose_gun_5view.jpg")
for i in range(4):
    T = cv2.imread(fr"C:/AI Pipeline Test/zapper-i2t/ref/gun_pose{i}.png")
    r = cv2.matchTemplate(S, T, cv2.TM_CCOEFF_NORMED)
    mn,mx,mnl,mxl = cv2.minMaxLoc(r)
    print(f"pose{i} size={T.shape[1]}x{T.shape[0]} best={mx:.4f} at sheet x={mxl[0]} y={mxl[1]}  -> x range {mxl[0]}..{mxl[0]+T.shape[1]-1}, y {mxl[1]}..{mxl[1]+T.shape[0]-1}")
