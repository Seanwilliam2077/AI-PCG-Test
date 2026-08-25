import cv2, numpy as np, sys
src,x0,y0,x1,y1 = sys.argv[1],*map(int,sys.argv[2:6])
im = cv2.imread(src).astype(np.float32)
reg = im[y0:y1, x0:x1]
bgs = np.median(im[max(0,y0-45):max(1,y0-15), x0:x1].reshape(-1,3),axis=0)
d = np.linalg.norm(reg-bgs, axis=2)
lv = ' .:-=+*#%@'
print('bg BGR',bgs)
print('     '+''.join([str((x)//10%10) for x in range(x0,x1)]))
print('     '+''.join([str(x%10) for x in range(x0,x1)]))
for j in range(y1-y0):
    row=''
    for i in range(x1-x0):
        k=int(min(9, d[j,i]/8))
        row+=lv[k]
    print('%4d '%(y0+j)+row)
