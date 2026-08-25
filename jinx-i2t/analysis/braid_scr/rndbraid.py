import json, math
s=json.load(open('object-sculpt-spec.json'))
ct={c['id']:c for c in s['componentTree']}
def wpos(cid):
    c=ct[cid]; a=c.get('attachment')
    p=a['localStart'] if a else c['transform']['position']
    par=c.get('parent')
    if par is None: return list(p)
    q=wpos(par); return [q[0]+p[0],q[1]+p[1],q[2]+p[2]]
h=wpos('hair')
def seg(cid):
    a=ct[cid]['attachment']
    S=[h[i]+a['localStart'][i] for i in range(3)]
    E=[h[i]+a['localEnd'][i] for i in range(3)]
    return S,E,a['baseRadius'],a['endRadius']
L=['braid-l','braid-l-2','braid-l-3','braid-l-4','braid-l-5','braid-l-6']
R=['braid-r','braid-r-2','braid-r-3','braid-r-4','braid-r-5','braid-r-6']
def sample(chain,Y):
    for cid in chain:
        S,E,r0,r1=seg(cid)
        if E[1]-1e-9<=Y<=S[1]+1e-9:
            u=(S[1]-Y)/(S[1]-E[1]) if S[1]!=E[1] else 0
            u=max(0,min(1,u))
            X=S[0]+(E[0]-S[0])*u; Z=S[2]+(E[2]-S[2])*u; r=r0+(r1-r0)*u
            return X,Z,r,cid
    return None
print('  Y(mm) | LEFT  X(mm)  Z(mm)  dia(mm) seg     | RIGHT X(mm)  Z(mm)  dia(mm) seg     | sep(mm)')
Ys=[1520,1450,1380,1310,1240,1160,1090,1020,950,880,810,740,660,590,520,450,380,300,250,200,150,100,85]
for Ym in Ys:
    Y=Ym/1000.
    a=sample(L,Y); b=sample(R,Y)
    def f(x): return '  %7.1f %6.1f %7.1f %-8s'%(x[0]*1000,x[1]*1000,2*x[2]*1000,x[3].replace('braid-','')) if x else '     -       -       -    -      '
    sep=('%7.1f'%((a[0]-b[0])*1000)) if (a and b) else '   -'
    print(' %6d |%s |%s | %s'%(Ym,f(a),f(b),sep))
print()
print('segment endpoints (world m):')
for cid in L+R+['braid-ties','braid-tassel','braid-tassel-r']:
    S,E,r0,r1=seg(cid)
    print(' %-14s S=(%7.4f,%7.4f,%7.4f) E=(%7.4f,%7.4f,%7.4f) dia %5.1f->%5.1f mm'%(cid,S[0],S[1],S[2],E[0],E[1],E[2],2000*r0,2000*r1))
