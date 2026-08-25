import cv2, numpy as np, sys
im=cv2.imread('ref/gun_pose1.png'); hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV).astype(int)
fg=np.load('analysis/work/p1_fg.npy'); H,S,V=hsv[...,0],hsv[...,1],hsv[...,2]
def cls(y,x):
    if not fg[y,x]: return '.'
    h,s,v=H[y,x],S[y,x],V[y,x]
    if h<62 and s>65: return 'W' if v>=120 else 'w'
    if 78<=h<=132: return 'C' if v>=110 else 'c'
    return '?'
y0,y1=40,112
print('      '+''.join(str(y//10%10) for y in range(y0,y1)))
print('      '+''.join(str(y%10) for y in range(y0,y1)))
for x in [int(a) for a in sys.argv[1:]]:
    print('x=%3d %s'%(x,''.join(cls(y,x) for y in range(y0,y1))))
