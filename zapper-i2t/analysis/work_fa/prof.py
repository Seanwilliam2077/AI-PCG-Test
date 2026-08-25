import cv2, numpy as np, sys
im = cv2.imread('../jinx-i2t/ref/pose_gun_5view.jpg').astype(np.float32)
x0,y0,x1,y1,bgy0,bgy1 = map(int,sys.argv[1:7])
bg = np.median(im[bgy0:bgy1, x0:x1].reshape(-1,3),axis=0)
sub = im[y0:y1, x0:x1]
d = np.linalg.norm(sub-bg,axis=2)
m = (d>16).astype(np.uint8)
m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((2,2),np.uint8)).astype(bool)
for i in range(0,x1-x0):
    col=np.where(m[:,i])[0]
    if len(col)<2: print(x0+i,'-'); continue
    print(x0+i, y0+col.min(), y0+col.max(), col.max()-col.min()+1)
