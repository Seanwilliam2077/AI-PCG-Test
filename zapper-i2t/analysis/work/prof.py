import cv2, numpy as np
fg = np.load('analysis/work/p3_fg.npy')
h,w = fg.shape
print('x  top bot  height  ncomp_in_col')
for x in range(0,190,2):
    col = fg[:,x]
    idx = np.flatnonzero(col)
    if len(idx)==0: print(x,'-'); continue
    # runs
    runs=[]; s=idx[0]; p=idx[0]
    for i in idx[1:]:
        if i>p+1: runs.append((s,p)); s=i
        p=i
    runs.append((s,p))
    print('%3d top=%3d bot=%3d h=%3d runs=%s'%(x,idx[0],idx[-1],idx[-1]-idx[0]+1, runs))
