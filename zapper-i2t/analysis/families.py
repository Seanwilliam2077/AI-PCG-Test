import cv2, numpy as np, sys
sys.path.insert(0,'analysis'); from sample import load
def hin(H,lo,hi): return (H>=lo)&(H<=hi) if lo<=hi else ((H>=lo)|(H<=hi))
print('--- hue-family area fractions (gun mask) ---')
for pose in ['gun_pose3','gun_pose1','gun_pose0','gun_pose2']:
    im,L,a,b,m = load(pose)
    C=np.hypot(a,b); H=(np.degrees(np.arctan2(b,a))+360)%360
    fam = {
     'warm metal  (H 30-110, C>=10)': m&hin(H,30,110)&(C>=10),
     'cool paint  (H 190-300, C 3-16)': m&hin(H,190,300)&(C>=3)&(C<16),
     'teal mark   (H 150-215, C>=16)': m&hin(H,150,215)&(C>=16)&(L>35),
     'magenta mark(H 300-15,  C>=24)': m&hin(H,300,15)&(C>=24),
     'red/orange  (H 5-40,    C>=12)': m&hin(H,5,40)&(C>=12),
     'near-neutral(C<3)':              m&(C<3),
    }
    tot=int(m.sum()); acc=np.zeros(L.shape,bool)
    print(' %s  gunpx=%d'%(pose,tot))
    for k,v in fam.items():
        v = v & ~acc if 'warm' not in k else v
        print('   %-32s %5d  %5.2f%%'%(k,int(v.sum()),100*v.sum()/tot))
    other = m & ~(fam['warm metal  (H 30-110, C>=10)']|fam['cool paint  (H 190-300, C 3-16)']|
                  fam['teal mark   (H 150-215, C>=16)']|fam['magenta mark(H 300-15,  C>=24)']|
                  fam['red/orange  (H 5-40,    C>=12)']|fam['near-neutral(C<3)'])
    print('   %-32s %5d  %5.2f%%'%('unclassified',int(other.sum()),100*other.sum()/tot))
print()
print('--- texture roughness: residual after removing smooth cross-axis shading ---')
im,L,a,b,m = load('gun_pose3')
for nm,(x0,y0,x1,y1) in [('tube.copper',(58,44,86,78)),('tube.paint_blue',(104,46,150,78)),
                          ('lattice.collar',(24,34,48,78)),('muzzle.collar',(150,46,168,80))]:
    P = L[y0:y1,x0:x1]
    prof = np.median(P,axis=1,keepdims=True)     # smooth shading model = per-row median (rows ~ along axis)
    R = P - prof
    print(' %-16s box=(%d,%d)-(%d,%d) n=%4d  rowprofile L range=%.1f  residual sd=%.2f  |R| p95=%.2f'%(
        nm,x0,y0,x1,y1,P.size, prof.max()-prof.min(), R.std(), np.percentile(np.abs(R),95)))
