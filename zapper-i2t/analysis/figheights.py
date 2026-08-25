import cv2, numpy as np
d = np.load(r"C:/AI Pipeline Test/zapper-i2t/analysis/_d2.npy")
bands = {0:(0,660),1:(661,1386),2:(1387,1828),3:(1829,2604),4:(2605,2999)}
for T in [16,25,40]:
    m = (d>T).astype(np.uint8); m[1345:,:]=0
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3,3),np.uint8))
    out=[]
    for k,(a,b) in bands.items():
        sub = m[:,a:b+1]
        rows = np.where(sub.sum(axis=1)>0)[0]
        cols = np.where(sub.sum(axis=0)>0)[0]
        out.append((k, rows.min(), rows.max(), rows.max()-rows.min()+1, a+cols.min(), a+cols.max()))
    print("T=",T)
    for o in out: print("   fig%d  top=%d bot=%d H=%d  x %d..%d"%o)
