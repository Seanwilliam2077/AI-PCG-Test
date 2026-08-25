"""Re-cut the PBR evidence crops: search inside an anatomical band, not by guess.

The stage1 sweep found 15 of 20 crops sampling the wrong pixels -- all five head
materials landed on bare cheek, `nailTeal` sat 30.4 percent inside the silhouette,
and `eye.png` and `sclera.png` were byte-identical. The rects had been hand-placed
as fractions of the panel, which is a guess dressed up as a measurement, and a
wrong guess is silent: the extractor reports 0.75 confidence on a crop of backdrop
just as happily as on a crop of skin.

Searching by colour alone does not fix it either -- the first attempt matched
`hair` to a patch of cheek at dLab 0.0, because the target colour it was given had
itself come from a contaminated component recipe.

So each material declares BOTH:
  * an anatomical band, read off a gridded contact sheet of the reference panels
    (where on the figure this material is, as a fraction of the panel), and
  * a target albedo read off the same sheet.
The search then finds the rect inside that band whose median is closest to the
target in CIE Lab, requiring 95 percent alpha coverage and rejecting rects that
are more than 5 percent matting holes. A material whose best candidate is still
far from its target is REPORTED as weak rather than silently written.
"""
import json

import cv2
import numpy as np

# material -> (panel, x0, x1, y0, y1, target BGR)   bands are panel fractions
BANDS = {
    'skin':        ('head_1', 0.64, 0.82, 0.34, 0.43, (182, 191, 208)),
    'skinShade':   ('body_2', 0.29, 0.38, 0.22, 0.30, (150, 158, 178)),
    'hair':        ('body_2', 0.40, 0.62, 0.01, 0.07, (158, 107, 46)),
    'hairDark':    ('body_5', 0.42, 0.58, 0.34, 0.56, (99, 63, 27)),
    'cloth':       ('body_2', 0.40, 0.58, 0.19, 0.27, (52, 46, 48)),
    'clothWorn':   ('body_2', 0.10, 0.19, 0.425, 0.475, (55, 50, 52)),
    'pants':       ('body_2', 0.38, 0.52, 0.48, 0.62, (75, 50, 84)),
    # the pinstripe is PALE GOLD, lighter than the purple base -- the spec had it
    # as "the darker pinstripe", which is backwards and cost the trousers their
    # contrast entirely
    # measured, not guessed: over the trouser band the base median is BGR
    # (71,47,82) and the brightest 3 percent is (106,105,122). The stripe is
    # LIGHTER than the base -- the spec called it "the darker pinstripe", which is
    # backwards, and is why the trousers rendered with no stripe contrast at all.
    'pantsDark':   ('body_2', 0.38, 0.60, 0.46, 0.62, (106, 105, 122)),
    'leather':     ('body_2', 0.58, 0.72, 0.38, 0.48, (40, 41, 49)),
    'canvas':      ('body_2', 0.48, 0.64, 0.38, 0.46, (96, 132, 138)),
    'brass':       ('body_2', 0.715, 0.80, 0.525, 0.615, (73, 139, 180)),
    'steel':       ('body_0', 0.30, 0.70, 0.40, 0.60, (128, 126, 124)),
    'tattoo':      ('body_5', 0.52, 0.74, 0.18, 0.32, (208, 196, 168)),
    'laceMagenta': ('body_2', 0.49, 0.63, 0.815, 0.925, (120, 60, 165)),
    'nailTeal':    ('body_2', 0.055, 0.125, 0.487, 0.522, (170, 190, 95)),
    'glassTank':   ('body_2', 0.725, 0.80, 0.543, 0.590, (186, 180, 168)),
    'eye':         ('head_1', 0.58, 0.86, 0.27, 0.34, (150, 96, 74)),
    'sclera':      ('head_1', 0.58, 0.86, 0.27, 0.34, (231, 209, 193)),
    'pupil':       ('head_1', 0.58, 0.86, 0.27, 0.34, (30, 28, 26)),
    'lip':         ('head_1', 0.66, 0.82, 0.43, 0.51, (120, 108, 150)),
    'brow':        ('head_1', 0.58, 0.86, 0.23, 0.28, (110, 70, 52)),
}
# small features need small windows; broad garments can afford big ones
SMALL = {'eye', 'sclera', 'pupil', 'brow', 'clothWorn'}
# thin features -- a pinstripe is 2-3 px on a 377 px panel, a bootlace less. An
# 8 px window centred on one is mostly its neighbour, so these get smaller ones.
TINY = {'pantsDark', 'laceMagenta', 'nailTeal', 'brass', 'glassTank'}

panels = {n: cv2.imread(f'ref/views/{n}.png', cv2.IMREAD_UNCHANGED)
          for n in ('body_0', 'body_2', 'body_5', 'head_1')}


def lab(bgr):
    return cv2.cvtColor(np.uint8([[bgr]]), cv2.COLOR_BGR2LAB)[0, 0].astype(float)


def search(mat, panel, x0, x1, y0, y1, target):
    im = panels[panel]
    H, W = im.shape[:2]
    alpha = im[:, :, 3] > 128
    # matting left pure-white holes in the hair; they are not evidence
    holes = im[:, :, :3].min(axis=2) > 248
    X0, X1, Y0, Y1 = int(W * x0), int(W * x1), int(H * y0), int(H * y1)
    tl = lab(target)
    sizes = (4, 5, 6) if mat in TINY else (8, 12, 18) if mat in SMALL else (24, 40, 64)
    best = None
    for side in sizes:
        if X1 - X0 < side or Y1 - Y0 < side:
            continue
        step = max(1, side // 3)
        for y in range(Y0, Y1 - side, step):
            for x in range(X0, X1 - side, step):
                if alpha[y:y + side, x:x + side].mean() < 0.95:
                    continue
                if holes[y:y + side, x:x + side].mean() > 0.05:
                    continue
                sub = im[y:y + side, x:x + side, :3]
                med = np.median(sub.reshape(-1, 3), axis=0)
                dist = float(np.linalg.norm(lab(med) - tl))
                if best is None or dist < best['dist']:
                    best = dict(panel=panel, x=x, y=y, w=side, h=side, dist=round(dist, 1),
                                median=[int(v) for v in med], target=list(target))
    return best


def main() -> int:
    out, weak = {}, []
    print(f'{"material":13s} {"panel":7s} {"rect":20s} {"dLab":>6s}   median vs target')
    for mat, (panel, x0, x1, y0, y1, target) in BANDS.items():
        hit = search(mat, panel, x0, x1, y0, y1, target)
        if hit is None:
            print(f'{mat:13s} -- no rect met the coverage and hole tests')
            weak.append(mat)
            continue
        flag = '  <-- WEAK' if hit['dist'] > 26 else ''
        if flag:
            weak.append(mat)
        out[mat] = hit
        print(f'{mat:13s} {panel:7s} {str((hit["x"], hit["y"], hit["w"], hit["h"])):20s} '
              f'{hit["dist"]:6.1f}   {hit["median"]} vs {list(target)}{flag}')

    json.dump(out, open('analysis/pbr_rects.json', 'w'), indent=1)
    print(f'\n{len(out)}/{len(BANDS)} located, {len(weak)} weak: {weak}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
