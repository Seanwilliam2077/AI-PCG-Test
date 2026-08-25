import cv2, numpy as np, sys, json
sys.path.insert(0,'analysis'); from sample import load, stats, best_patch
POLY = [
 ('muzzle.bore',         [(166,47),(176,45),(184,53),(185,69),(177,80),(167,77),(163,62)],(255,255,0)),
 ('rail.mount.red',      [(86,29),(115,32),(114,39),(88,38)],                          (60,60,255)),
 ('rearsight.hook',      [(15,18),(25,18),(35,24),(35,30),(26,28),(16,25)],            (200,255,255)),
 ('rail.bar',            [(31,22),(60,22),(63,29),(88,30),(170,34),(172,41),(116,39),(62,37),(57,32),(31,31)],(0,215,255)),
 ('lattice.collar',      [(21,28),(31,24),(46,26),(56,34),(57,62),(52,80),(45,89),(31,89),(22,74),(19,50)],(0,140,255)),
 ('tube.copper',         [(55,40),(89,38),(86,83),(57,83)],                            (40,90,150)),
 ('tube.midband',        [(88,37),(98,39),(95,84),(84,84)],                          (0,255,0)),
 ('tube.paint_blue',     [(97,39),(152,43),(154,81),(94,82)],                        (255,180,80)),
 ('muzzle.collar',       [(150,39),(168,38),(177,46),(179,62),(174,79),(163,86),(151,83),(147,60)],(255,0,255)),
]
im,L,a,b,m = load('gun_pose3')
C=np.hypot(a,b); H=(np.degrees(np.arctan2(b,a))+360)%360
h,w = L.shape
labmap = np.zeros((h,w), np.int32)
ov = im.copy()
for i,(nm,pts,col) in enumerate(POLY,1):
    mm=np.zeros((h,w),np.uint8); cv2.fillPoly(mm,[np.array(pts,np.int32)],1)
    sel = (mm>0)&m&(labmap==0)
    labmap[sel]=i
    ov[sel] = (0.45*np.array(col)+0.55*ov[sel]).astype(np.uint8)
np.save('analysis/_labmap_p3.npy', labmap)
tot = int((m&(labmap>0)).sum()); unass=int((m&(labmap==0)).sum())
print('assigned %d, unassigned-in-mask %d, gunmask %d'%(tot,unass,int(m.sum())))
for i,(nm,pts,col) in enumerate(POLY,1):
    sel=labmap==i; s=stats(im,L,a,b,sel)
    print('%-20s n=%4d  %5.1f%%  BGR=(%3d,%3d,%3d) Lab=(%5.1f,%5.1f,%5.1f) C=%4.1f H=%5.1f Lspan=%4.1f'%(
      nm,s['n'],100*s['n']/tot,s['bgr'][0],s['bgr'][1],s['bgr'][2],s['L'],s['a'],s['b'],s['C'],s['H'],s['span']))
cv2.imwrite(sys.argv[1]+'/p3_regions.png', cv2.resize(ov,None,fx=6,fy=6,interpolation=cv2.INTER_NEAREST))
