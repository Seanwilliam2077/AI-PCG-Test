import cv2, numpy as np
im=cv2.imread('ref/views/clay_5.png',cv2.IMREAD_UNCHANGED)
m=im[:,:,3]>127
g=cv2.cvtColor(im[:,:,:3],cv2.COLOR_BGR2GRAY).astype(np.float32)
gb=cv2.GaussianBlur(g,(0,0),1.0)
lap=cv2.Laplacian(gb,cv2.CV_32F,ksize=5)
e=cv2.GaussianBlur(np.abs(lap),(0,0),2.5); e[~m]=0
thr=np.percentile(e[m],85)
B=(e>thr)&m
B=cv2.morphologyEx(B.astype(np.uint8),cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(7,25)))
B=cv2.morphologyEx(B,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,5)))
ys,xs=np.nonzero(m); y0,y1=ys.min(),ys.max(); H=y1-y0
mmpx=1721.0/(H+1)
print('thr',round(thr,1),'H',H+1,'mm/px',round(mmpx,4))
print('  t     Ymm | clusters in x (span, width_mm)')
for i in range(2,40):
    t=i/40.; y=int(round(y1-t*H))
    row=B[y]
    idx=np.nonzero(row)[0]
    cl=[]
    if len(idx):
        s=idx[0];p=idx[0]
        for k in idx[1:]:
            if k-p<=3: p=k; continue
            cl.append((s,p)); s=k;p=k
        cl.append((s,p))
    cl=[c for c in cl if c[1]-c[0]>=8]
    print('  %.3f %6.0f | %s'%(t,t*H*mmpx,'  '.join('%d-%d(%.0fmm)'%(a,b,(b-a+1)*mmpx) for a,b in cl)))
