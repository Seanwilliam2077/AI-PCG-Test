import numpy as np
ys=np.array([32.7,40.2,49.8,60.0,69.2,76.1,82.2]); k=np.arange(len(ys))
yc=np.arange(50,63,0.25); R=np.arange(18,42,0.25); t0=np.radians(np.arange(0,180,1.0))
Yc,Rr,T0=np.meshgrid(yc,R,t0,indexing='ij')
print(' N   rms(px)   yc     R      OD     th0    th_span')
rows=[]
for N in range(8,33):
    d=2*np.pi/N
    e=0
    for i,yv in enumerate(ys):
        e=e+(Yc-Rr*np.cos(T0+i*d)-yv)**2
    e=e/len(ys)
    j=np.unravel_index(np.argmin(e),e.shape)
    rms=np.sqrt(e[j]); a=np.degrees(T0[j])
    rows.append((rms,N,Yc[j],Rr[j],a))
    print('%2d  %7.3f  %5.2f  %5.2f  %6.2f  %5.1f  %5.1f'%(N,rms,Yc[j],Rr[j],2*Rr[j],a,a+360.0/N*6))
rows.sort()
print('\nranked by rms:'); 
for r in rows[:6]: print('  N=%2d rms=%.3f OD=%.1f yc=%.1f'%(r[1],r[0],2*r[3],r[2]))
