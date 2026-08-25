import cv2, numpy as np
from scipy import ndimage
S = cv2.imread(r"C:/AI Pipeline Test/jinx-i2t/ref/pose_gun_5view.jpg").astype(np.float32)
d = np.load(r"C:/AI Pipeline Test/zapper-i2t/analysis/_d2.npy")
m = (d>9).astype(np.uint8)
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5,5),np.uint8))
m = ndimage.binary_fill_holes(m).astype(np.uint8)

def bottom_edge(x0,x1,ylo,yhi):
    pts=[]
    for x in range(x0,x1+1):
        col=m[ylo:yhi,x]
        ys=np.where(col>0)[0]
        if len(ys): pts.append((x, ylo+ys.max()))
    return np.array(pts,float)

def fitline(pts):
    x=pts[:,0]; y=pts[:,1]
    A=np.polyfit(x,y,1)
    res=y-np.polyval(A,x)
    return A, res.std()

for name,(x0,x1,ylo,yhi) in {
  "p3 tube-bottom":(2500,2580,230,300),
  "p1 tube-bottom":(700,790,240,320),
  "p0 tube-bottom":(80,180,190,280),
}.items():
    pts=bottom_edge(x0,x1,ylo,yhi)
    A,s=fitline(pts)
    ang=np.degrees(np.arctan(A[0]))
    print(f"{name}: slope={A[0]:+.4f} angle={ang:+.2f} deg  rms={s:.2f}px  n={len(pts)}")
