import cv2, numpy as np
im=cv2.imread('ref/gun_pose2.png').astype(np.float32)
g=cv2.GaussianBlur(cv2.cvtColor(im.astype(np.uint8),cv2.COLOR_BGR2GRAY).astype(np.float32),(0,0),0.8)
fg=np.load('analysis/work/p2_fg.npy')
cy,cx=89.2,104.2
def val(a,r,arr):
    y=cy+r*np.sin(a); x=cx+r*np.cos(a)
    if 0<=y<arr.shape[0]-1 and 0<=x<arr.shape[1]-1:
        return cv2.getRectSubPix(arr,(1,1),(float(x),float(y)))[0,0]
    return None
print('collar outer edge radius (last fg->bg transition, subpixel by residual)')
rs=[]
for deg in list(range(-70,101,10))+list(range(250,340,10)):
    a=np.radians(deg); last=None
    for r in np.arange(8,34,0.25):
        f=val(a,r,fg.astype(np.float32))
        if f is not None and f>0.5: last=r
    if last: rs.append((deg%360,last)); print('  %4d deg  r=%5.2f'%(deg,last))
v=np.array([r for _,r in rs]); ang=np.radians(np.array([d for d,_ in rs]))
# fit r = R + dx*cos + dy*sin  (small offset of true centre from bore centre)
A=np.stack([np.ones_like(ang),np.cos(ang),np.sin(ang)],1)
co,*_=np.linalg.lstsq(A,v,rcond=None)
print('\n fit: R=%.2f  offset=(%.2f, %.2f) px  |offset|=%.2f  -> %.1f%% of collar radius'%(
    co[0],co[1],co[2],np.hypot(co[1],co[2]),100*np.hypot(co[1],co[2])/co[0]))
res=v-A@co; print(' residual rms=%.2f px  (n=%d)'%(np.sqrt((res**2).mean()),len(v)))
