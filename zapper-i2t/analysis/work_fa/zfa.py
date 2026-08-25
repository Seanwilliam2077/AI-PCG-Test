import cv2, numpy as np, sys
def zoom(src, x0,y0,x1,y1, s, out, step=5, interp='lanczos'):
    im = cv2.imread(src)
    if im is None: raise SystemExit('cannot read '+src)
    c = im[y0:y1, x0:x1]
    f = cv2.INTER_LANCZOS4 if interp=='lanczos' else cv2.INTER_NEAREST
    z = cv2.resize(c, ((x1-x0)*s, (y1-y0)*s), interpolation=f)
    for gx in range(x0, x1+1):
        if (gx-x0)%step==0:
            X=(gx-x0)*s
            cv2.line(z,(X,0),(X,z.shape[0]),(0,255,255),1)
            cv2.putText(z,str(gx),(X+1,10),cv2.FONT_HERSHEY_PLAIN,0.6,(0,255,255),1)
    for gy in range(y0, y1+1):
        if (gy-y0)%step==0:
            Y=(gy-y0)*s
            cv2.line(z,(0,Y),(z.shape[1],Y),(0,255,255),1)
            cv2.putText(z,str(gy),(1,Y-1),cv2.FONT_HERSHEY_PLAIN,0.6,(0,255,255),1)
    cv2.imwrite(out, z); print(out, z.shape)
a=sys.argv
zoom(a[1], int(a[2]),int(a[3]),int(a[4]),int(a[5]), int(a[6]), a[7], int(a[8]) if len(a)>8 else 5, a[9] if len(a)>9 else 'lanczos')
