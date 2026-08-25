import cv2, numpy as np
S = cv2.imread(r"C:/AI Pipeline Test/jinx-i2t/ref/pose_gun_5view.jpg")
d = np.load(r"C:/AI Pipeline Test/zapper-i2t/analysis/_d2.npy")
off = {0:(42,150,225,160),1:(642,192,215,150),2:(1650,203,160,129),3:(2421,214,236,118)}
for i,(x0,y0,w,h) in off.items():
    sub = S[y0:y0+h, x0:x0+w]
    dd  = d[y0:y0+h, x0:x0+w]
    m = (dd>14).astype(np.uint8)
    big = cv2.resize(sub, None, fx=6, fy=6, interpolation=cv2.INTER_NEAREST)
    cv2.imwrite(fr"C:/AI Pipeline Test/zapper-i2t/analysis/_p{i}_big.png", big)
    cv2.imwrite(fr"C:/AI Pipeline Test/zapper-i2t/analysis/_p{i}_mask.png",
                cv2.resize(m*255,None,fx=6,fy=6,interpolation=cv2.INTER_NEAREST))
    print(i, m.sum())
