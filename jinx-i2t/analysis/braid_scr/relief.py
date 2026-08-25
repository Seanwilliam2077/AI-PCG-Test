import cv2, numpy as np
def load(p):
    im=cv2.imread(p,cv2.IMREAD_UNCHANGED)
    return (im[:,:,3]>127), cv2.cvtColor(im[:,:,:3],cv2.COLOR_BGR2GRAY).astype(np.float32)

def relief(p, xf, y0,y1, halfw, mmpx, label):
    m,g=load(p); prof=[]
    for y in range(y0,y1+1):
        xc=xf(y); xs=np.arange(int(round(xc-halfw)),int(round(xc+halfw))+1)
        vals=g[y,xs][m[y,xs]]
        prof.append(vals.mean() if len(vals) else np.nan)
    p_=np.array(prof); p_=p_[~np.isnan(p_)]
    base=cv2.GaussianBlur(p_.reshape(-1,1),(0,0),12).ravel()
    d=p_-base
    n=len(d); dd=d-d.mean(); ac=np.correlate(dd,dd,'full')[n-1:]; ac/=ac[0]
    z=np.argmax(ac<0); k=z+int(np.argmax(ac[z:min(n,z+70)]))
    print('%-34s len=%dpx  rms_modulation=%.2f gray  p2p=%.1f  1stACpeak=%dpx(%.0fmm) ac=%.2f'%(
        label,n,d.std(),d.max()-d.min(),k,k*mmpx,ac[k]))

# REF back view, braid columns
relief('ref/views/clay_5.png', lambda y:138+(y-420)*(170-138)/260., 420,680, 8, 1721/1203., 'REF back  L-braid y420-680')
relief('ref/views/clay_5.png', lambda y:172+(y-420)*(205-172)/260., 420,680, 8, 1721/1203., 'REF back  R-braid y420-680')
# REF side view, detached braid run t .15-.40  (y 739..1041), x centre from measured runs
relief('ref/views/clay_0.png', lambda y:{ }.get(y, 195+(y-739)*(272-195)/302.), 739,1041, 8, 1721/1212., 'REF side  braid y739-1041')
# RENDER back view: braid axis screen x = 250 - X/0.002 ; use braid-l  (Y .98->1.39 => y 410..205)
relief('out/final_clay/render_yaw180.png', lambda y: 250-(0.021+(0.032-0.021)*((900-y)*0.002-0.9806)/(1.3944-0.9806))/0.002, 220,400, 10, 2.0, 'RND back  L-braid y220-400')
# RENDER side view: braid axis screen x = 250 - Z/0.002 for braid-l-2/-3, y 300..650
relief('out/final_clay/render_yaw90.png', lambda y: 313.0 + (y-300)*(-8.0)/350., 300,650, 8, 2.0, 'RND side  braid y300-650')
