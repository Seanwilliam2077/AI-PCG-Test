import cv2, numpy as np
im=cv2.imread('ref/gun_pose3.png'); hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV).astype(int)
fg=np.load('analysis/work/p3_fg.npy').astype(bool)
H,S,V=hsv[...,0],hsv[...,1],hsv[...,2]
print('pose3 lattice region V-map  x=22..58  y=17..92')
print('      '+''.join('%d'%(x//10%10) for x in range(22,59)))
print('      '+''.join('%d'%(x%10) for x in range(22,59)))
for y in range(17,93):
    print('y=%3d %s'%(y,''.join(('%X'%min(15,V[y,x]//10)) if fg[y,x] else '.' for x in range(22,59))))
