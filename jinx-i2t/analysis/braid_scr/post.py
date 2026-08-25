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

def prep(p,anchor_lo=0.70,anchor_hi=0.80):
    m=loadmask(p); ys,xs=np.nonzero(m); y0,y1=ys.min(),ys.max(); H=y1-y0
    mm=1721.0/(H+1)
    t=(y1-ys)/H
    sel=(t>=anchor_lo)&(t<=anchor_hi)
    anchor=xs[sel].mean()
    return m,y0,y1,H,mm,anchor

R=prep('ref/views/clay_0.png')
Q=prep('out/final_clay/render_yaw90.png')
print('ref anchor x=%.2f mm/px=%.4f ; render anchor x=%.2f mm/px=%.4f'%(R[5],R[4],Q[5],Q[4]))
print()
print('  t     Ymm  | REF: bodyBack braidF braidB (mm right of anchor) | RND: bodyBack braidF braidB | dBodyBack dBraidF dBraidB')
for i in range(2,40):
    t=i/40.
    row=[]
    for (m,y0,y1,H,mm,anc) in (R,Q):
        y=int(round(y1-t*H)); rr=runs(m[y])
        if not rr: row.append((None,None,None)); continue
        body=max(rr,key=lambda r:r[1]-r[0]); post=rr[-1]
        bb=(body[1]-anc)*mm
        if post is body: bf=None; bk=(post[1]-anc)*mm
        else: bf=(post[0]-anc)*mm; bk=(post[1]-anc)*mm
        row.append((bb,bf,bk))
    (rb,rf,rk),(qb,qf,qk)=row
    f=lambda v: ('%7.1f'%v) if v is not None else '    -  '
    d=lambda a,b: ('%7.1f'%(b-a)) if (a is not None and b is not None) else '    -  '
    print('  %.3f %6.0f | %s %s %s | %s %s %s | %s %s %s'%(t,t*R[3]*R[4],f(rb),f(rf),f(rk),f(qb),f(qf),f(qk),d(rb,qb),d(rf,qf),d(rk,qk)))
