import cv2, numpy as np, sys
S = cv2.imread(r"C:/AI Pipeline Test/jinx-i2t/ref/pose_gun_5view.jpg")
def ruler(name,x0,y0,x1,y1,k=8,step=10):
    c=S[y0:y1,x0:x1].copy()
    big=cv2.resize(c,None,fx=k,fy=k,interpolation=cv2.INTER_NEAREST)
    H,W=big.shape[:2]
    for x in range(x0 - x0%step + step, x1, step):
        X=(x-x0)*k
        cv2.line(big,(X,0),(X,H),(0,0,255),1)
        cv2.putText(big,str(x),(X+2,14),cv2.FONT_HERSHEY_SIMPLEX,0.42,(0,0,255),1)
    for y in range(y0 - y0%step + step, y1, step):
        Y=(y-y0)*k
        cv2.line(big,(0,Y),(W,Y),(0,255,255),1)
        cv2.putText(big,str(y),(2,Y-3),cv2.FONT_HERSHEY_SIMPLEX,0.42,(0,255,255),1)
    cv2.imwrite(fr"C:/AI Pipeline Test/zapper-i2t/analysis/_ruler_{name}.png",big)
    print(name,big.shape)
ruler("p3",2400,215,2620,320,k=8,step=10)
