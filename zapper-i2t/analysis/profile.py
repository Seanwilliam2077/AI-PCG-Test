import cv2, numpy as np
from scipy import ndimage
d = np.load(r"C:/AI Pipeline Test/zapper-i2t/analysis/_d2.npy")
m = (d>9).astype(np.uint8)
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5,5),np.uint8))
m = ndimage.binary_fill_holes(m).astype(np.uint8)
def prof(x0,x1,ylo,yhi,label):
    print("==",label)
    for x in range(x0,x1+1,2):
        col=m[ylo:yhi,x]; ys=np.where(col>0)[0]
        if len(ys)==0: print(x,"-"); continue
        print(f"  x={x} top={ylo+ys.min()} bot={ylo+ys.max()} h={ys.max()-ys.min()+1}")
prof(2480,2610,235,300,"pose3 barrel")
