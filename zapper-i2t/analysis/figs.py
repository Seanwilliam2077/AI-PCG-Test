import cv2, numpy as np
S = cv2.imread(r"C:/AI Pipeline Test/jinx-i2t/ref/pose_gun_5view.jpg")
h,w = S.shape[:2]
d = np.load(r"C:/AI Pipeline Test/zapper-i2t/analysis/_d2.npy")
m = (d>16).astype(np.uint8)
m[1350:,:] = 0
m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3,3),np.uint8))
n,lab,stats,cent = cv2.connectedComponentsWithStats(m, 8)
order = np.argsort(-stats[1:,4])+1
for k in order[:12]:
    x,y,ww,hh,a = stats[k]
    print(f"comp{k} area={a} bbox x{x}..{x+ww-1} y{y}..{y+hh-1} w={ww} h={hh}")
