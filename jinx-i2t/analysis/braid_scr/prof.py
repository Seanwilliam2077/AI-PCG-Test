import cv2,numpy as np,sys
p=sys.argv[1]
im=cv2.imread(p,cv2.IMREAD_UNCHANGED)
a=im[:,:,3]; m=a>127
g=cv2.cvtColor(im[:,:,:3],cv2.COLOR_BGR2GRAY).astype(np.float32)
g[~m]=np.nan
ys,xs=np.nonzero(m); y0,y1=ys.min(),ys.max(); H=y1-y0+1
rows=[float(x) for x in sys.argv[2].split(',')]
x0,x1=int(sys.argv[3]),int(sys.argv[4])
for t in rows:
    y=int(round(y1-t*(H-1)))
    line=g[y,x0:x1]
    s=''.join('.' if np.isnan(v) else '0123456789ABCDEF'[min(15,int(v)//16)] for v in line)
    print('t=%.2f y=%4d x[%d..%d] %s'%(t,y,x0,x1,s))
