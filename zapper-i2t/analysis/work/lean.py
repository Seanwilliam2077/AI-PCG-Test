import cv2, numpy as np
fg=np.load('analysis/work/p3_fg.npy').astype(bool)
warm=np.load('analysis/work/p3_warm.npy'); cool=np.load('analysis/work/p3_cool.npy')
print('A) steel-tube -> muzzle-collar boundary: first warm x in [138,160] per row')
xs=[]
for y in range(43,80):
    idx=[x for x in range(138,162) if warm[y,x] and warm[y,x+1]]
    if idx: xs.append((y,idx[0])); print('   y=%2d  x=%3d'%(y,idx[0]))
ys=np.array([a for a,b in xs]); vx=np.array([b for a,b in xs])
print('   -> lean: min x=%d at y=%d ; max x=%d at y=%d ; span=%d'%(vx.min(),ys[vx.argmin()],vx.max(),ys[vx.argmax()],vx.max()-vx.min()))
print()
print('B) copper->midband: last warm-run boundary; and midband bright strip centre per row')
im=cv2.imread('ref/gun_pose3.png'); hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV).astype(int)
V=hsv[...,2]
for y in range(42,80):
    seg=V[y,84:100].astype(float)
    if not fg[y,88]: print('   y=%2d  --'%y); continue
    k=int(np.argmax(seg)); print('   y=%2d  brightest x=%3d  V=%3d   row=%s'%(y,84+k,seg[k],' '.join('%3d'%v for v in seg)))
