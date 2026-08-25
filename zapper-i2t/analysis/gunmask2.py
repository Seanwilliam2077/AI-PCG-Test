import cv2, numpy as np
from scipy import ndimage
S = cv2.imread(r"C:/AI Pipeline Test/jinx-i2t/ref/pose_gun_5view.jpg")
d = np.load(r"C:/AI Pipeline Test/zapper-i2t/analysis/_d2.npy")
off = {0:(42,150,225,160),1:(642,192,215,150),2:(1650,203,160,129),3:(2421,214,236,118)}
for i,(x0,y0,w,h) in off.items():
    dd  = d[y0:y0+h, x0:x0+w]
    m = (dd>9).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5,5),np.uint8))
    m = ndimage.binary_fill_holes(m).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3,3),np.uint8))
    n,lab,st,ce = cv2.connectedComponentsWithStats(m,8)
    if n>1:
        k=1+np.argmax(st[1:,4]); m=(lab==k).astype(np.uint8)
    np.save(fr"C:/AI Pipeline Test/zapper-i2t/analysis/_p{i}_fg.npy", m)
    cv2.imwrite(fr"C:/AI Pipeline Test/zapper-i2t/analysis/_p{i}_mask2.png",
                cv2.resize(m*255,None,fx=6,fy=6,interpolation=cv2.INTER_NEAREST))
    ys,xs=np.where(m>0); print(i,"bbox x",xs.min(),xs.max(),"y",ys.min(),ys.max(),"area",m.sum())
