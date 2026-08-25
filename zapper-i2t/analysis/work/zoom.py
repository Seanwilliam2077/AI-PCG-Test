import cv2, numpy as np, sys
src, x0,x1,y0,y1, k, out = sys.argv[1], *map(int,sys.argv[2:7]), sys.argv[7]
im = cv2.imread(src)[y0:y1, x0:x1]
big = cv2.resize(im, None, fx=k, fy=k, interpolation=cv2.INTER_NEAREST)
H,W = big.shape[:2]
ov = big.copy()
for xx in range(x0, x1+1):
    if xx % 10: continue
    X = (xx-x0)*k
    if X>=W: continue
    c = (0,140,255) if xx%50 else (0,0,255)
    cv2.line(ov,(X,0),(X,H),c,1)
    cv2.putText(ov,str(xx),(X+2,12),cv2.FONT_HERSHEY_PLAIN,0.8,c,1)
for yy in range(y0, y1+1):
    if yy % 10: continue
    Y = (yy-y0)*k
    if Y>=H: continue
    c = (0,140,255) if yy%50 else (0,0,255)
    cv2.line(ov,(0,Y),(W,Y),c,1)
    cv2.putText(ov,str(yy),(2,Y-2),cv2.FONT_HERSHEY_PLAIN,0.8,c,1)
big = cv2.addWeighted(big,0.62,ov,0.38,0)
cv2.imwrite(out,big); print(out, big.shape)
