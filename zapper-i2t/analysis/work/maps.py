import cv2, numpy as np
im = cv2.imread('ref/gun_pose3.png'); hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV).astype(int)
fg = np.load('analysis/work/p3_fg.npy').astype(bool)
H,S,V = hsv[...,0],hsv[...,1],hsv[...,2]
warm = fg & (H<62) & (S>65)
cool = fg & (H>=78) & (H<=132)
dark = fg & (V<78)
out = np.zeros(im.shape[:2]+(3,),np.uint8)
out[...,2] = warm*255          # red = warm
out[...,0] = cool*255          # blue = cool
out[dark] = (0,255,0)          # green = dark
cv2.imwrite('analysis/work/p3_warm.png', cv2.resize(out,None,fx=6,fy=6,interpolation=cv2.INTER_NEAREST))
np.save('analysis/work/p3_warm.npy',warm); np.save('analysis/work/p3_cool.npy',cool); np.save('analysis/work/p3_dark.npy',dark)
# warm fraction per column, restricted to the barrel band rows 30..84
print(' x  warmfrac coolfrac  (rows 42..80, below rail)')
for x in range(22,186):
    band = slice(42,81)
    w = warm[band,x].sum(); c = cool[band,x].sum(); f=fg[band,x].sum()
    if f==0: continue
    print('%3d  %4.2f %4.2f  n=%2d %s'%(x,w/f,c/f,f,'#'*int(round(20*w/max(f,1)))))
