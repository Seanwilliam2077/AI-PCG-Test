import cv2, numpy as np, sys, json

def load(p):
    im = cv2.imread(p, cv2.IMREAD_UNCHANGED)
    m = im[:,:,3] > 127
    g = cv2.cvtColor(im[:,:,:3], cv2.COLOR_BGR2GRAY).astype(np.float32)
    return m, g

def texenergy(m, g, s1=1.0, s2=3.0):
    gb = cv2.GaussianBlur(g,(0,0),s1)
    lap = cv2.Laplacian(gb, cv2.CV_32F, ksize=5)
    e = cv2.GaussianBlur(np.abs(lap),(0,0),s2)
    e[~m]=0
    return e

if __name__=='__main__':
    p=sys.argv[1]; out=sys.argv[2]
    m,g=load(p); e=texenergy(m,g)
    thr=np.percentile(e[m], float(sys.argv[3]) if len(sys.argv)>3 else 88)
    B=(e>thr)&m
    B=cv2.morphologyEx(B.astype(np.uint8),cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(9,15)))
    vis=np.dstack([m.astype(np.uint8)*80]*3)
    vis[B>0]=[0,0,255]
    cv2.imwrite(out,vis)
    print('thr',thr)
