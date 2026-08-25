import cv2, numpy as np, sys

def loadmask(p):
    im=cv2.imread(p,cv2.IMREAD_UNCHANGED)
    return (im[:,:,3]>127)

def runs(row):
    idx=np.nonzero(row)[0]
    if len(idx)==0: return []
    out=[];s=idx[0];p=idx[0]
    for i in idx[1:]:
        if i==p+1: p=i;continue
        out.append((s,p));s=i;p=i
    out.append((s,p)); return out

def table(path,mmpx,label,ts):
    m=loadmask(path); ys,xs=np.nonzero(m); y0,y1=ys.min(),ys.max(); H=y1-y0
    print('## %s  %s  H=%dpx  mm/px=%.4f'%(label,path,H+1,mmpx))
    print('   t     Ypx   Ymm  |  runs (x0..x1 w) ... | bodyRun  braidRun  gap_mm  braidW_mm')
    for t in ts:
        y=int(round(y1-t*H))
        rr=[r for r in runs(m[y]) if r[1]-r[0]>=1]
        s=' '.join('%d-%d(%d)'%(a,b,b-a+1) for a,b in rr)
        # body = widest run ; braid = the posterior-most run that is not body
        if rr:
            body=max(rr,key=lambda r:r[1]-r[0])
            post=rr[-1]
            if post is body:
                gap=0.0; bw=0.0; braid='-'
            else:
                gap=(post[0]-body[1]-1)*mmpx; bw=(post[1]-post[0]+1)*mmpx
                braid='%d-%d'%(post[0],post[1])
            print('  %.3f %5d %6.1f | %-46s | %d-%d  %-10s %6.1f %8.1f'%(t,y,t*H*mmpx,s,body[0],body[1],braid,gap,bw))
    print()

ts=[i/40 for i in range(1,40)]
table('ref/views/clay_0.png',1721.0/1212,'REF side clay_0',ts)
table('out/final_clay/render_yaw90.png',2.0,'RENDER yaw90',ts)
