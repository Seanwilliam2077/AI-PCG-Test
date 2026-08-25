import cv2, numpy as np
im = cv2.imread('../jinx-i2t/ref/pose_gun_5view.jpg').astype(np.float32)
bg = np.median(im[195:220, 2400:2610].reshape(-1,3),axis=0)
sub = im[225:300, 2400:2610]
d = np.linalg.norm(sub-bg,axis=2)
m = d>16
m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2,2),np.uint8)).astype(bool)
tops=[];bots=[];xs=[]
for i in range(m.shape[1]):
    col=np.where(m[:,i])[0]
    if len(col)<3: continue
    xs.append(2400+i); tops.append(225+col.min()); bots.append(225+col.max())
xs=np.array(xs);tops=np.array(tops);bots=np.array(bots)
for x0,x1,lab in [(2490,2570,'tube'),(2500,2560,'tube2')]:
    s=(xs>=x0)&(xs<=x1)
    pt=np.polyfit(xs[s],tops[s],1); pb=np.polyfit(xs[s],bots[s],1)
    mid=(tops[s]+bots[s])/2; pm=np.polyfit(xs[s],mid,1)
    print(lab,'top slope %.4f'%pt[0],'bot slope %.4f'%pb[0],'mid slope %.4f'%pm[0],
          'angle %.2f deg'%np.degrees(np.arctan(pm[0])),
          'mid at x=2500: %.2f'%np.polyval(pm,2500), 'diam mean %.2f'%np.mean(bots[s]-tops[s]))
print()
for x in range(2400,2610,5):
    j=np.where(xs==x)[0]
    if len(j): print(x, tops[j[0]], bots[j[0]], bots[j[0]]-tops[j[0]])
