import cv2, numpy as np
def loadmask(p):
    im=cv2.imread(p,cv2.IMREAD_UNCHANGED); return (im[:,:,3]>127)
def runs(row):
    idx=np.nonzero(row)[0]
    if len(idx)==0: return []
    out=[];s=idx[0];p=idx[0]
    for i in idx[1:]:
        if i==p+1: p=i;continue
        out.append((s,p));s=i;p=i
    out.append((s,p)); return [r for r in out if r[1]-r[0]>=1]
for p in ['ref/views/clay_5.png','out/final_clay/render_yaw180.png']:
    m=loadmask(p); ys,xs=np.nonzero(m); y0,y1=ys.min(),ys.max(); H=y1-y0
    mm=1721.0/(H+1)
    # midline from torso band t .70-.82
    mids=[]
    for t in np.arange(0.70,0.821,0.005):
        y=int(round(y1-t*H)); rr=runs(m[y])
        if rr: mids.append((rr[0][0]+rr[-1][1])/2)
    mid=float(np.mean(mids))
    print('## %s H=%d mm/px=%.4f midline_x=%.2f'%(p,H+1,mm,mid))
    for i in range(2,40):
        t=i/40.; y=int(round(y1-t*H)); rr=runs(m[y])
        s=' '.join('%d..%d'%(a,b) for a,b in rr)
        print('  t=%.3f Y=%4.0fmm  L=%7.1f R=%7.1f  runs: %s'%(t,t*H*mm,(rr[0][0]-mid)*mm if rr else 0,(rr[-1][1]-mid)*mm if rr else 0,s))
    print()
