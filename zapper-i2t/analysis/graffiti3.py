import cv2, numpy as np, sys
sys.path.insert(0,'analysis'); from sample import load
def hin(H,lo,hi): return (H>=lo)&(H<=hi) if lo<=hi else ((H>=lo)|(H<=hi))
lab3 = np.load('analysis/_labmap_p3.npy')
NAMES=['(none)','muzzle.bore','rail.mount.red','rearsight.hook','rail.bar','lattice.collar',
       'tube.copper','tube.midband','tube.paint_blue','muzzle.collar']
SUB={'muzzle.bore':'bore','rail.mount.red':'red','rearsight.hook':'brass','rail.bar':'brass',
     'lattice.collar':'brass','tube.copper':'copper','tube.midband':'brass',
     'tube.paint_blue':'paint','muzzle.collar':'brass','(none)':'?'}
im,L,a,b,m = load('gun_pose3')
C=np.hypot(a,b); H=(np.degrees(np.arctan2(b,a))+360)%360
marks = m&((hin(H,150,215)&(C>=16)&(L>35)) | (hin(H,300,15)&(C>=24)))
print('pose3: substrate under / around each graffiti mark (labmap parts)')
for tag,sel in (('teal',m&hin(H,150,215)&(C>=16)&(L>35)),('magenta',m&hin(H,300,15)&(C>=24))):
    n,lb,st,cen = cv2.connectedComponentsWithStats(sel.astype(np.uint8),8)
    for k in range(1,n):
        A=int(st[k,cv2.CC_STAT_AREA])
        if A<3: continue
        comp=(lb==k)
        ring = cv2.dilate(comp.astype(np.uint8),np.ones((5,5),np.uint8)).astype(bool)&~marks&m
        parts={}
        for pid in np.unique(lab3[ring]):
            parts[SUB[NAMES[pid]]]=parts.get(SUB[NAMES[pid]],0)+int((lab3[ring]==pid).sum())
        under={}
        for pid in np.unique(lab3[comp]):
            under[SUB[NAMES[pid]]]=under.get(SUB[NAMES[pid]],0)+int((lab3[comp]==pid).sum())
        print('  %-7s A=%3d cen=(%5.1f,%5.1f) under=%s ring=%s'%(tag,A,cen[k][0],cen[k][1],under,parts))
# area-share expectation
tot=int((lab3>0).sum())
share={}
for pid in range(1,10): share[SUB[NAMES[pid]]]=share.get(SUB[NAMES[pid]],0)+int((lab3==pid).sum())
print('part-area shares:', {k:round(100*v/tot,1) for k,v in share.items()})
print('graffiti px by substrate:')
gp={}
for pid in np.unique(lab3[marks]):
    gp[SUB[NAMES[pid]]]=gp.get(SUB[NAMES[pid]],0)+int((lab3[marks]==pid).sum())
print(' ',gp, 'total',int(marks.sum()))
