import cv2, numpy as np, sys, json
sys.path.insert(0,'analysis'); from sample import load, stats
def hue_in(H,lo,hi): return (H>=lo)&(H<=hi) if lo<=hi else ((H>=lo)|(H<=hi))
res={}
for pose in ['gun_pose3','gun_pose1','gun_pose0','gun_pose2']:
    im,L,a,b,m = load(pose)
    C=np.hypot(a,b); H=(np.degrees(np.arctan2(b,a))+360)%360
    teal = m & hue_in(H,150,215) & (C>=16) & (L>35)
    mag  = m & hue_in(H,300,15)  & (C>=24)
    res[pose]={}
    for tag,sel in (('teal',teal),('magenta',mag)):
        n,lab,st,cen = cv2.connectedComponentsWithStats(sel.astype(np.uint8),8)
        marks=[]
        for k in range(1,n):
            A=int(st[k,cv2.CC_STAT_AREA])
            if A<2: continue
            marks.append(dict(area=A,x=int(st[k,cv2.CC_STAT_LEFT]),y=int(st[k,cv2.CC_STAT_TOP]),
                w=int(st[k,cv2.CC_STAT_WIDTH]),h=int(st[k,cv2.CC_STAT_HEIGHT]),
                cx=round(float(cen[k][0]),1),cy=round(float(cen[k][1]),1)))
        marks.sort(key=lambda d:-d['area'])
        s = stats(im,L,a,b,sel)
        res[pose][tag]=dict(total_px=int(sel.sum()), n_marks=len(marks), marks=marks, colour=s)
        print('%s %-8s px=%4d marks>=2px=%2d areas=%s'%(pose,tag,sel.sum(),len(marks),[d['area'] for d in marks]))
        if s: print('    colour BGR=(%d,%d,%d) Lab=(%.1f,%.1f,%.1f) C=%.1f H=%.1f Lspan=%.1f'%(
            s['bgr'][0],s['bgr'][1],s['bgr'][2],s['L'],s['a'],s['b'],s['C'],s['H'],s['span']))
json.dump(res,open('analysis/_graffiti.json','w'),indent=1)
