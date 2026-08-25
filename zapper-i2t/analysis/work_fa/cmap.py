import cv2, numpy as np, sys
src,x0,y0,x1,y1 = sys.argv[1],*map(int,sys.argv[2:6])
im = cv2.imread(src)
reg = im[y0:y1, x0:x1]
hsv = cv2.cvtColor(reg, cv2.COLOR_BGR2HSV).astype(int)
bgr = reg.astype(int)
bgs = np.median(im[max(0,y0-45):max(1,y0-15), x0:x1].reshape(-1,3),axis=0)
d = np.linalg.norm(bgr-bgs, axis=2)
out=[]
print('     '+''.join([str((x//10)%10) for x in range(x0,x1)]))
print('     '+''.join([str(x%10) for x in range(x0,x1)]))
for j in range(y1-y0):
    row=''
    for i in range(x1-x0):
        h,s,v = hsv[j,i]
        dd = d[j,i]
        if dd < 12: c='.'                      # background
        elif v < 55: c='K'                     # very dark
        elif s < 45: c='w' if v>150 else 'g'   # grey/white
        elif 5 <= h <= 30: c='B' if v>110 else 'b'   # brass/tan (orange-yellow)
        elif 30 < h <= 45: c='Y'               # yellow
        elif 45 < h <= 100: c='T' if v>110 else 't' # teal/green-cyan
        elif 100 < h <= 135: c='U'             # blue
        elif h > 135: c='M'                    # magenta/red
        else: c='R'                            # red-orange
        row+=c
    print('%4d '%(y0+j)+row)
