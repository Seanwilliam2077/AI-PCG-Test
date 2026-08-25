import cv2, numpy as np, json, sys
sys.path.insert(0,'analysis')
from sample import load, stats, best_patch

def hue_in(H, lo, hi):
    return (H>=lo)&(H<=hi) if lo<=hi else ((H>=lo)|(H<=hi))

# (name, pose, box(x0,y0,x1,y1), hue-lo, hue-hi or None, Lmin, Lmax, Cmin)
PARTS = [
 ('muzzle.collar.brass',      'gun_pose3',(144,38,178,88), 35,105, 20,100, 7),
 ('muzzle.bore.liner',        'gun_pose3',(160,42,190,84),180,300, 28, 66, 3),
 ('muzzle.bore.interior',     'gun_pose3',(163,44,190,84), None,None, 0, 26, 0),
 ('barrel.tube.paint_blue',   'gun_pose3',(102,42,152,80),190,320,  0,100, 0),
 ('barrel.tube.copper',       'gun_pose3',( 52,40, 92,80), 35,105,  0,100, 5),
 ('barrel.midband.brass',     'gun_pose3',( 92,36,106,84), 35,105,  0,100, 5),
 ('barrel.lattice.brass',     'gun_pose3',( 20,26, 52,88), 35,105, 24,100, 5),
 ('barrel.lattice.hole',      'gun_pose3',( 26,28, 50,84), None,None, 0, 24, 0),
 ('rail.bar.brass',           'gun_pose3',(114,30,172,40), 45,110,  0,100,10),
 ('rail.mount.red',           'gun_pose3',( 86,28,116,38),  5, 40,  0,100,10),
 ('rearsight.hook.brass',     'gun_pose3',( 14,17, 36,31), 35,110,  0,100, 8),
 ('knob.magenta',             'gun_pose3',( 32,78, 44,90),300, 20,  0,100,18),
 ('frame.body.paint_teal',    'gun_pose0',(120,56,162,92),170,265,  0,100, 4),
 ('port.cylinder.tan',        'gun_pose0',(133,48,152,80), 30, 95,  0,100, 5),
 ('barrel.tube.paint_blue@p1','gun_pose1',( 78,66,124,98),190,320,  0,100, 0),
 ('barrel.tube.copper@p1',    'gun_pose1',(128,64,152,96), 35,105,  0,100, 5),
 ('muzzle.collar.brass@p1',   'gun_pose1',( 40,62, 78,106), 35,105, 20,100, 7),
 ('muzzle.bore.interior@p1',  'gun_pose1',( 44,70, 74,100),None,None,0, 26, 0),
 ('muzzle.bore.liner@p1',     'gun_pose1',( 42,66, 78,104),180,300, 28, 66, 3),
]
out={}
cache={}
for (nm,pose,box,h0,h1,Lmin,Lmax,Cmin) in PARTS:
    if pose not in cache: cache[pose]=load(pose)
    im,L,a,b,m = cache[pose]
    C = np.hypot(a,b); H=(np.degrees(np.arctan2(a*0+a,b*0+b))+360)%360
    H = (np.degrees(np.arctan2(b,a))+360)%360
    x0,y0,x1,y1 = box
    box_m = np.zeros(L.shape,bool); box_m[y0:y1, x0:x1]=True
    sel = box_m & m & (L>=Lmin)&(L<=Lmax)&(C>=Cmin)
    if h0 is not None: sel &= hue_in(H,h0,h1)
    if sel.sum()<8:
        print('%-30s EMPTY'%nm); continue
    whole = stats(im,L,a,b,sel)
    bp = best_patch(L, sel, 14.0, 10)
    tight = stats(im,L,a,b,bp) if bp is not None else None
    out[nm]=dict(pose=pose,box=box,hue=(h0,h1),Lrange=(Lmin,Lmax),Cmin=Cmin,whole=whole,tight=tight)
    def f(s): return 'n=%4d BGR=(%3d,%3d,%3d) Lab=(%5.1f,%5.1f,%5.1f) C=%4.1f H=%5.1f Lspan=%4.1f'%(
        s['n'],s['bgr'][0],s['bgr'][1],s['bgr'][2],s['L'],s['a'],s['b'],s['C'],s['H'],s['span'])
    print('%-30s %-10s WHOLE %s'%(nm,pose,f(whole)))
    if tight: print('%-30s %-10s TIGHT %s'%('','',f(tight)))
json.dump(out, open('analysis/_parts.json','w'), indent=1)
