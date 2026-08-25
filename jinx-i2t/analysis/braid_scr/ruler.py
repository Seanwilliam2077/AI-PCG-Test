import cv2, numpy as np, sys
# usage: ruler.py img out x0 x1 y0 y1 zoom [grid]
p,out=sys.argv[1],sys.argv[2]
x0,x1,y0,y1,z=[int(v) for v in sys.argv[3:8]]
grid=int(sys.argv[8]) if len(sys.argv)>8 else 10
im=cv2.imread(p,cv2.IMREAD_UNCHANGED)
a=im[:,:,3:4].astype(np.float32)/255.
o=(im[:,:,:3].astype(np.float32)*a+255*(1-a)).astype(np.uint8)
c=o[y0:y1,x0:x1].copy()
c=cv2.resize(c,((x1-x0)*z,(y1-y0)*z),interpolation=cv2.INTER_NEAREST)
for x in range(x0,x1):
    if x%grid==0:
        col=(0,0,255) if x%(grid*5)==0 else (0,200,255)
        cv2.line(c,((x-x0)*z,0),((x-x0)*z,c.shape[0]),col,1)
        if x%(grid*5)==0:
            cv2.putText(c,str(x),((x-x0)*z+2,14),cv2.FONT_HERSHEY_PLAIN,0.9,(0,0,255),1)
for y in range(y0,y1):
    if y%grid==0:
        col=(255,0,0) if y%(grid*5)==0 else (255,200,0)
        cv2.line(c,(0,(y-y0)*z),(c.shape[1],(y-y0)*z),col,1)
        if y%(grid*5)==0:
            cv2.putText(c,str(y),(2,(y-y0)*z-3),cv2.FONT_HERSHEY_PLAIN,0.9,(255,0,0),1)
cv2.imwrite(out,c); print(out,c.shape)
