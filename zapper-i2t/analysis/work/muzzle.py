import cv2, numpy as np
im=cv2.imread('ref/gun_pose3.png'); hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV).astype(int)
fg=np.load('analysis/work/p3_fg.npy').astype(bool)
V=hsv[...,2]; H=hsv[...,0]; S=hsv[...,1]
print('V map, x=160..185, y=40..86  (digit = V//10, . = bg)')
print('      '+''.join('%d'%(x//10%10) for x in range(160,186)))
print('      '+''.join('%d'%(x%10) for x in range(160,186)))
for y in range(40,87):
    row=''
    for x in range(160,186):
        row += ('%X'%min(15,V[y,x]//10)) if fg[y,x] else '.'
    print('y=%3d %s'%(y,row))
