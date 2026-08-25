import cv2, numpy as np
for p,rows,xr in [('ref/gun_pose3.png',range(56,66),range(138,186)),
                  ('ref/gun_pose1.png',range(80,90),range(36,90))]:
    im=cv2.imread(p); V=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)[...,2].astype(float)
    prof=V[list(rows),:][:,list(xr)].mean(0)
    print('\n%s  mean V over rows %d-%d, x=%d..%d'%(p,rows[0],rows[-1],xr[0],xr[-1]))
    for i,x in enumerate(xr):
        b=int(round(prof[i]/6))
        print('  x=%3d V=%5.1f %s'%(x,prof[i],'#'*b))
