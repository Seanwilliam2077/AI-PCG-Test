import numpy as np
from itertools import product
ys=np.array([32.7,40.2,49.8,60.0,69.2,76.1,82.2])
k=np.arange(len(ys))
best=None
for N in range(8,33):
    d=2*np.pi/N
    for yc in np.arange(50,62,0.1):
        for R in np.arange(18,40,0.1):
            for t0 in np.arange(0,np.pi,np.radians(1)):
                pred=yc-R*np.cos(t0+k*d)
                e=((pred-ys)**2).mean()
                if best is None or e<best[0]: best=(e,N,yc,R,np.degrees(t0))
    # per-N best
    bn=None
    for yc in np.arange(50,62,0.1):
        for R in np.arange(18,40,0.1):
            for t0 in np.arange(0,np.pi,np.radians(1)):
                pred=yc-R*np.cos(t0+k*d); e=((pred-ys)**2).mean()
                if bn is None or e<bn[0]: bn=(e,yc,R,np.degrees(t0))
    print('N=%2d  rms=%.3f px  yc=%.1f R=%.1f OD=%.1f theta0=%.0fdeg  arc=%.0fdeg'%(
        N,np.sqrt(bn[0]),bn[1],bn[2],2*bn[2],bn[3],360.0/N*(len(ys)-1)))
print('\nBEST overall: rms=%.3f N=%d yc=%.1f R=%.1f theta0=%.0f'%(np.sqrt(best[0]),best[1],best[2],best[3],best[4]))
