import cv2, numpy as np, sys, json
sys.path.insert(0,'analysis'); from sample import load, stats
def hue_in(H,lo,hi): return (H>=lo)&(H<=hi) if lo<=hi else ((H>=lo)|(H<=hi))
AXIS={'gun_pose3':2.8,'gun_pose1':-8.0,'gun_pose0':-6.0,'gun_pose2':None}
for pose in ['gun_pose3','gun_pose1','gun_pose0']:
    im,L,a,b,m = load(pose)
    C=np.hypot(a,b); H=(np.degrees(np.arctan2(b,a))+360)%360
    print('=== %s  barrel axis %.1f deg ==='%(pose,AXIS[pose]))
    for tag,sel in (('teal', m&hue_in(H,150,215)&(C>=16)&(L>35)),
                    ('magenta', m&hue_in(H,300,15)&(C>=24))):
        n,lb,st,cen = cv2.connectedComponentsWithStats(sel.astype(np.uint8),8)
        core = sel & (C>=np.percentile(C[sel],70))
        s=stats(im,L,a,b,core)
        print(' %s CORE (top-30%% chroma) n=%d BGR=(%d,%d,%d) Lab=(%.1f,%.1f,%.1f) C=%.1f H=%.1f Lspan=%.1f'%(
            tag,s['n'],s['bgr'][0],s['bgr'][1],s['bgr'][2],s['L'],s['a'],s['b'],s['C'],s['H'],s['span']))
        for k in range(1,n):
            A=int(st[k,cv2.CC_STAT_AREA])
            if A<3: continue
            ys,xs=np.where(lb==k)
            P=np.stack([xs-xs.mean(),ys-ys.mean()])
            cov=P@P.T/max(len(xs)-1,1)
            ev,evec=np.linalg.eigh(cov)
            ang=(np.degrees(np.arctan2(evec[1,-1],evec[0,-1])))%180
            ar = float(np.sqrt(max(ev[-1],1e-6)/max(ev[0],1e-6)))
            d = None
            if AXIS[pose] is not None:
                d=abs(((ang-AXIS[pose]+90)%180)-90)
            print('   %-7s A=%3d bbox=(%3d,%3d,%2dx%2d) cen=(%5.1f,%5.1f) ang=%5.1f AR=%4.1f dAxis=%s'%(
              tag,A,st[k,0],st[k,1],st[k,2],st[k,3],cen[k][0],cen[k][1],ang,ar,'%.0f'%d if d is not None else '-'))
