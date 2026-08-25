import cv2, numpy as np
fg=np.load('analysis/work/p3_fg.npy').astype(bool)
warm=np.load('analysis/work/p3_warm.npy'); cool=np.load('analysis/work/p3_cool.npy')
print('STEEL TUBE section: cool-run extent + fg silhouette')
print('  x  coolTop coolBot  fgTop fgBot   coolH  fgH')
for x in range(96,150):
    idx=np.flatnonzero(cool[20:90,x]); f=np.flatnonzero(fg[20:90,x])
    if len(idx)==0 or len(f)==0: print(x,'-'); continue
    ct,cb=idx[0]+20,idx[-1]+20; ft,fb=f[0]+20,f[-1]+20
    print('%3d   %3d %3d    %3d %3d    %4.0f %4.0f'%(x,ct,cb,ft,fb,cb-ct+1,fb-ft+1))
