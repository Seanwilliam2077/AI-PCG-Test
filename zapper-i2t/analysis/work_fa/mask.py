import cv2, numpy as np, sys
src,x0,y0,x1,y1 = sys.argv[1],*map(int,sys.argv[2:6])
thr = float(sys.argv[6]) if len(sys.argv)>6 else 20
im = cv2.imread(src).astype(np.float32)
H,W = im.shape[:2]
# background estimate: median of pixels in a ring far from the object, per region
reg = im[y0:y1, x0:x1]
# use column-wise bg from top rows of the wider strip
bgstrip = im[max(0,y0-40):max(1,y0-10), x0:x1]
bg = np.median(bgstrip.reshape(-1,3), axis=0)
print('bg BGR', bg)
d = np.linalg.norm(reg-bg, axis=2)
m = d>thr
hdr='     '+''.join([str((x)//10%10) for x in range(x0,x1)])
print(hdr); print('     '+''.join([str(x%10) for x in range(x0,x1)]))
for j in range(y1-y0):
    print('%4d '%(y0+j) + ''.join('#' if m[j,i] else '.' for i in range(x1-x0)))
