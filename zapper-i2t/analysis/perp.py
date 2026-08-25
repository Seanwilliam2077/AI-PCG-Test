import cv2, numpy as np
from scipy import ndimage
S=cv2.imread(r"C:/AI Pipeline Test/jinx-i2t/ref/pose_gun_5view.jpg")
d=np.load(r"C:/AI Pipeline Test/zapper-i2t/analysis/_d2.npy")
def mask(T):
    m=(d>T).astype(np.uint8)
    m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
    return ndimage.binary_fill_holes(m).astype(np.uint8)
M={T:mask(T) for T in (14,20,28)}

def width_profile(p0,p1,smin,smax,T=20,half=40):
    """axis from p0->p1 (unit dir u). For s in [smin,smax] measure the run of mask
    along the perpendicular through p0+s*u."""
    p0=np.array(p0,float); p1=np.array(p1,float)
    u=(p1-p0); u/=np.linalg.norm(u); n=np.array([-u[1],u[0]])
    m=M[T]; out=[]
    for s in np.arange(smin,smax+0.001,1.0):
        c=p0+s*u
        vals=[]
        for t in np.arange(-half,half,0.25):
            q=c+t*n
            xi,yi=int(round(q[0])),int(round(q[1]))
            vals.append(m[yi,xi] if 0<=yi<m.shape[0] and 0<=xi<m.shape[1] else 0)
        vals=np.array(vals)
        idx=np.where(vals>0)[0]
        if len(idx)==0: out.append((s,None,None,0.0)); continue
        # longest contiguous run containing the centre
        w=(idx.max()-idx.min()+1)*0.25
        out.append((s,-half+idx.min()*0.25,-half+idx.max()*0.25,w))
    return u,n,out

cases={
 # pose : (axis point A (near muzzle, on axis), axis point B (rearward on axis))
 "p3": ((2594.0,276.5),(2456.0,270.0)),
 "p1": ((692.0,280.0),(816.0,272.0)),
 "p0": ((66.0,224.0),(174.0,222.0)),
}
for k,(A,B) in cases.items():
    u,n,prof=width_profile(A,B,-12,140,T=20)
    ang=np.degrees(np.arctan2(u[1],u[0]))
    print(f"--- {k} axis dir {u.round(3)} ({ang:.1f} deg)")
    for s,a,b,w in prof:
        if int(s)%4==0: print(f"   s={s:6.1f} w={w:5.2f}  ({a} .. {b})")
