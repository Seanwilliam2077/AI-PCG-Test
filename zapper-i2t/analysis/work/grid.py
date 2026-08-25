import cv2, numpy as np, sys
def grid(src, x0,y0,x1,y1, scale, out, step=10):
    im=cv2.imread(src)
    c=im[y0:y1, x0:x1].copy()
    h,w=c.shape[:2]
    c=cv2.resize(c,(w*scale,h*scale),interpolation=cv2.INTER_CUBIC)
    H,W=c.shape[:2]
    for i in range(0, w+1, step):
        X=i*scale
        cv2.line(c,(X,0),(X,H),(0,140,255),1)
        cv2.putText(c,str(x0+i),(X+2,12),cv2.FONT_HERSHEY_PLAIN,0.8,(0,140,255),1)
    for j in range(0, h+1, step):
        Y=j*scale
        cv2.line(c,(0,Y),(W,Y),(0,140,255),1)
        cv2.putText(c,str(y0+j),(2,Y-2),cv2.FONT_HERSHEY_PLAIN,0.8,(0,140,255),1)
    cv2.imwrite(out,c)
    print(out, c.shape)
if __name__=='__main__':
    a=sys.argv
    grid(a[1],int(a[2]),int(a[3]),int(a[4]),int(a[5]),int(a[6]),a[7], int(a[8]) if len(a)>8 else 10)
