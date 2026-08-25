import cv2, numpy as np, sys, json

def mask(p):
    im = cv2.imread(p, cv2.IMREAD_UNCHANGED)
    a = im[:,:,3]
    return (a>127).astype(np.uint8), im

def runs_row(m, y):
    row = m[y]
    idx = np.nonzero(row)[0]
    if len(idx)==0: return []
    out=[]; s=idx[0]; p=idx[0]
    for i in idx[1:]:
        if i==p+1: p=i; continue
        out.append((s,p)); s=i; p=i
    out.append((s,p))
    return out

def report(path, nrows=40, label=''):
    m,_ = mask(path)
    ys,xs = np.nonzero(m)
    y0,y1 = ys.min(), ys.max()
    H = y1-y0+1
    print('#',label,path,'bbox y',y0,y1,'H',H,'x',xs.min(),xs.max())
    for k in range(nrows+1):
        y = int(round(y0 + (H-1)*k/nrows))
        t = (y1-y)/ (H-1)
        rr = runs_row(m,y)
        rr = [(a,b) for a,b in rr if b-a>=1]
        print(' t=%.3f y=%4d  n=%d  %s' % (t,y,len(rr), ' '.join('[%d-%d w%d]'%(a,b,b-a+1) for a,b in rr)))

report(sys.argv[1], int(sys.argv[2]) if len(sys.argv)>2 else 40)
