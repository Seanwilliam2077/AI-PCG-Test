import cv2, numpy as np
im=cv2.imread('ref/views/clay_5.png',cv2.IMREAD_UNCHANGED)
g=cv2.cvtColor(im[:,:,:3],cv2.COLOR_BGR2GRAY).astype(np.float32)
H=1203; mm=1721.0/H

def sample(x_at_y, y0,y1, halfw):
    """average intensity across the braid width at each y, then autocorrelate along y"""
    prof=[]
    for y in range(y0,y1+1):
        xc=x_at_y(y)
        xs=np.arange(int(round(xc-halfw)),int(round(xc+halfw))+1)
        prof.append(g[y,xs].mean())
    p=np.array(prof)
    p=p-cv2.GaussianBlur(p.reshape(-1,1),(0,0),12).ravel()   # detrend
    p=p-p.mean()
    n=len(p); ac=np.correlate(p,p,'full')[n-1:]
    ac/=ac[0]
    # first local max after first zero crossing
    z=np.argmax(ac<0)
    k=z+int(np.argmax(ac[z:min(n,z+60)]))
    return p,ac,k

segs=[
 ('L braid y420-680', lambda y: 138+ (y-420)*(170-138)/260., 420,680, 8),
 ('R braid y420-680', lambda y: 172+ (y-420)*(205-172)/260., 420,680, 8),
 ('L braid y200-400', lambda y: 128+ (y-200)*(148-128)/200., 200,400, 8),
 ('R braid y200-400', lambda y: 172+ (y-200)*(185-172)/200., 200,400, 8),
 ('L braid y760-940', lambda y: 158+ (y-760)*(140-158)/180., 760,940, 8),
]
for name,f,y0,y1,hw in segs:
    p,ac,k=sample(f,y0,y1,hw)
    print('%-20s first AC peak at %d px  -> vertical pitch %.1f mm ; ac=%.2f'%(name,k,k*mm,ac[k]))
    print('   ac[1..40]:',' '.join('%.2f'%v for v in ac[1:41]))
