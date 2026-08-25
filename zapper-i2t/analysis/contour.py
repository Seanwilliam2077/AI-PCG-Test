import cv2, numpy as np, sys
from scipy import ndimage
S=cv2.imread(r"C:/AI Pipeline Test/jinx-i2t/ref/pose_gun_5view.jpg")
d=np.load(r"C:/AI Pipeline Test/zapper-i2t/analysis/_d2.npy")
m=(d>20).astype(np.uint8)
m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
m=ndimage.binary_fill_holes(m).astype(np.uint8)
def go(name,x0,y0,x1,y1,k=10,step=10):
    c=S[y0:y1,x0:x1].copy(); big=cv2.resize(c,None,fx=k,fy=k,interpolation=cv2.INTER_NEAREST)
    sub=m[y0:y1,x0:x1]
    bigm=cv2.resize(sub*255,None,fx=k,fy=k,interpolation=cv2.INTER_NEAREST)
    cont,_=cv2.findContours(bigm,cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)
    cv2.drawContours(big,cont,-1,(0,0,255),2)
    H,W=big.shape[:2]
    for x in range(x0-x0%step+step,x1,step):
        X=(x-x0)*k; cv2.line(big,(X,0),(X,H),(0,255,0),1); cv2.putText(big,str(x),(X+2,12),cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,255,0),1)
    for y in range(y0-y0%step+step,y1,step):
        Y=(y-y0)*k; cv2.line(big,(0,Y),(W,Y),(0,255,255),1); cv2.putText(big,str(y),(2,Y-3),cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,255,255),1)
    cv2.imwrite(fr"C:/AI Pipeline Test/zapper-i2t/analysis/_c_{name}.png",big); print(name,big.shape)
go("p1",670,235,880,320,k=8)
go("p0",50,190,270,290,k=8)
go("p2",1650,205,1810,330,k=9)
