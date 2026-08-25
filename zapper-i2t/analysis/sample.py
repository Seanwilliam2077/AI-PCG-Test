import cv2, numpy as np, json, sys
def load(pose):
    im = cv2.imread('ref/%s.png'%pose)
    lab = cv2.cvtColor(im, cv2.COLOR_BGR2LAB).astype(np.float64)
    L = lab[:,:,0]*100/255.0; a = lab[:,:,1]-128.0; b = lab[:,:,2]-128.0
    m = np.load('analysis/_gun_%s.npy'%pose).astype(bool)
    return im, L, a, b, m
def stats(im,L,a,b,sel):
    n = int(sel.sum())
    if n==0: return None
    bgr = im[sel].reshape(-1,3)
    Ls,as_,bs = L[sel],a[sel],b[sel]
    C = np.hypot(as_,bs); H=(np.degrees(np.arctan2(bs,as_))+360)%360
    p5,p95 = np.percentile(Ls,5), np.percentile(Ls,95)
    return dict(n=n, bgr=[int(v) for v in np.median(bgr,0)],
        L=round(float(np.median(Ls)),1), a=round(float(np.median(as_)),1), b=round(float(np.median(bs)),1),
        C=round(float(np.median(C)),1), H=round(float(np.median(H)),1),
        Hp5=round(float(np.percentile(H,5)),1), Hp95=round(float(np.percentile(H,95)),1),
        Lp5=round(float(p5),1), Lp95=round(float(p95),1), span=round(float(p95-p5),1))
def best_patch(L, region, band=14.0, minn=12):
    """largest 4-connected component of `region` whose pixels lie in an L window of width `band`"""
    best=None
    lo_grid = np.arange(0,100,1.0)
    for lo in lo_grid:
        sel = region & (L>=lo) & (L<lo+band)
        if sel.sum()<minn: continue
        n,labm,st,_ = cv2.connectedComponentsWithStats(sel.astype(np.uint8),4)
        if n<2: continue
        k = 1+int(np.argmax(st[1:,cv2.CC_STAT_AREA])); area=int(st[k,cv2.CC_STAT_AREA])
        if area<minn: continue
        if best is None or area>best[0]: best=(area,(labm==k))
    return None if best is None else best[1]
def poly_mask(shape, pts):
    mm = np.zeros(shape[:2], np.uint8); cv2.fillPoly(mm, [np.array(pts,np.int32)],1); return mm.astype(bool)
