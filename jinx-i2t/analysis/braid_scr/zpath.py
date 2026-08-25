import cv2, numpy as np, json
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

mR=loadmask('ref/views/clay_0.png'); ys,xs=np.nonzero(mR); Ry0,Ry1=ys.min(),ys.max(); RH=Ry1-Ry0; Rmm=1721.0/(RH+1)
mQ=loadmask('out/final_clay/render_yaw90.png'); ys,xs=np.nonzero(mQ); Qy0,Qy1=ys.min(),ys.max(); QH=Qy1-Qy0; Qmm=2.0

def post(m,y1,H,t):
    y=int(round(y1-t*H)); rr=runs(m[y]);  return (rr[-1][0],rr[-1][1],len(rr),rr) if rr else None

# anchor: t=0.95 posterior edge = back of skull, pure body in both
tA=0.95
xR_A=post(mR,Ry1,RH,tA)[1]; xQ_A=post(mQ,Qy1,QH,tA)[1]
ZQ_A=-(xQ_A-250)*0.002
print('anchor t=0.95: ref x=%d, render x=%d -> render Z=%.4f m'%(xR_A,xQ_A,ZQ_A))
print()
print('  t    Y(mm) | ref postX  Z_ref(mm)  refBraidFront Z(mm) | rnd postX Z_rnd(mm) rndBraidFront Z(mm) | dZ_back  dZ_front')
for i in range(4,38):
    t=i/40.
    pr=post(mR,Ry1,RH,t); pq=post(mQ,Qy1,QH,t)
    ZrB = ZQ_A - (pr[1]-xR_A)*Rmm/1000.
    ZqB = -(pq[1]-250)*0.002
    ZrF = ZQ_A - (pr[0]-xR_A)*Rmm/1000. if pr[2]>1 else None
    ZqF = -(pq[0]-250)*0.002 if pq[2]>1 else None
    fF=lambda v: ('%8.1f'%(v*1000)) if v is not None else '     -  '
    d=lambda a,b: ('%8.1f'%((b-a)*1000)) if (a is not None and b is not None) else '     -  '
    print('  %.3f %5.0f | %6d %9.1f %s | %6d %9.1f %s | %s %s'%(t,t*RH*Rmm,pr[1],ZrB*1000,fF(ZrF),pq[1],ZqB*1000,fF(ZqF),d(ZrB,ZqB),d(ZrF,ZqF)))
