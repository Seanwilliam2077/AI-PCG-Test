import cv2, numpy as np, sys
im = cv2.imread('ref/gun_pose3.png'); hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV).astype(int)
fg = np.load('analysis/work/p3_fg.npy')
def cls(h,s,v,f):
    if not f: return '.'
    if v<45: return '#'                     # near black (hole/bore)
    if h<60 and s>70: return 'W' if v>=120 else 'w'   # warm brass bright/dark
    if 80<=h<=130: return 'C' if v>=110 else 'c'      # cool steel bright/dark
    return '?'
for x in [int(a) for a in sys.argv[1:]]:
    line=''
    for y in range(18,92):
        h,s,v = hsv[y,x]; line += cls(h,s,v,fg[y,x])
    print('x=%3d %s'%(x,line))
print('      '+''.join(str((18+i)//10%10) for i in range(74)))
print('      '+''.join(str((18+i)%10) for i in range(74)))
