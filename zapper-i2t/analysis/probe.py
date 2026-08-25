import cv2, numpy as np, sys, json
def lab(bgr):
    return cv2.cvtColor(np.uint8([[bgr]]), cv2.COLOR_BGR2LAB)[0,0].astype(float)
def report(pose, x0,y0,x1,y1, label=''):
    im = cv2.imread('ref/%s.png'%pose)
    sub = im[y0:y1, x0:x1].reshape(-1,3)
    L = cv2.cvtColor(im, cv2.COLOR_BGR2LAB)[y0:y1,x0:x1].reshape(-1,3).astype(float)
    # OpenCV 8-bit Lab: L*255/100, a,b +128
    Lstar = L[:,0]*100/255.0
    astar = L[:,1]-128.0; bstar = L[:,2]-128.0
    med = np.median(sub,0).astype(int)
    p5,p95 = np.percentile(Lstar,5), np.percentile(Lstar,95)
    print('%-22s %s [%d,%d]-[%d,%d] n=%4d  BGR=(%3d,%3d,%3d)  Lab=(%5.1f,%6.1f,%6.1f)  L p5-p95=%.1f-%.1f span=%.1f %s'%(
        label,pose,x0,y0,x1,y1,len(sub),med[0],med[1],med[2],
        np.median(Lstar),np.median(astar),np.median(bstar), p5,p95,p95-p5,
        'OK' if p95-p5<=14 else 'REJECT'))
if __name__=='__main__':
    for line in sys.stdin:
        line=line.strip()
        if not line or line.startswith('#'): continue
        p = line.split()
        report(p[1], int(p[2]),int(p[3]),int(p[4]),int(p[5]), p[0])
