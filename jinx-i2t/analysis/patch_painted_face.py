"""Paint the face instead of modelling it, the way img2threejs's own character does.

The reference implementation for this pipeline is the showcase's
`createGirlCharacterModel.ts`. Its head is a contoured implicit surface, but its
FACE is not geometry at all: it is a canvas texture of soft-edged ellipse blobs --
face oval, brows, eyes with sclera/iris/pupil/lid layers, a lit nose bridge with
nostrils, split upper and lower lips -- mapped through UVs computed as azimuth and
depth-from-crown.

This build did the opposite and it has cost every pass. The eyes are 36 x 16 mm
spheres, the brows 50 x 8 mm boxes, the mouth a 45 mm ellipsoid, all as separate
meshes. On a 500 x 900 render of a 1.72 m figure the whole head is about 50 px
tall, so an eye is three pixels and a brow is one. `face-landmark-placement` has
scored 0.15 against a 0.80 critical threshold in all eight passes -- the worst
feature in the build -- and a round of geometry work moved it not at all.

The blocker is UVs. `polygonizeSdf` emits position, index and computed normals and
no UVs at all, so a map on an implicit head samples a single texel. The reference
implementation solves this by computing UVs for its contoured head; this generator
offers no such hook. So the head goes back to an ellipsoid primitive, which is
emitted as a scaled SphereGeometry and carries ordinary spherical UVs.

That trade is deliberate and it costs something real: the SDF skull's brow ridge,
cheekbones and jaw line go away. At 50 px they were worth about two pixels of
shading. A painted face at the same size is legible.

Nothing here is invented. Every colour is read out of the spec's own measured
materials -- `skin`, `skinShade`, `eye`, `sclera`, `pupil`, `lip`, `brow` -- so the
face stays inside the same measurement chain as the rest of the build, and the
texture is generated rather than sampled, so unlike the extracted PBR maps it
carries no reference pixels and is safe to publish.

Sphere UV convention, derived rather than guessed: three.js parametrises
x = -r cos(theta) sin(phi), z = r sin(theta) sin(phi) with theta = u * 2pi, so
u = 0.25 faces +Z, which is the front of this character.

**v is polar-angle linear, not height linear** -- `y = Ry * cos(pi * v)`. The first
attempt placed features by treating v as a height fraction and every one of them
landed 0.05 to 0.07 v too high; the mouth went off the visible face entirely. Each
row below is inverted from the landmark's measured height above or below the head's
centre, `v = acos(y / Ry) / pi`, with Ry = 97.8 mm:

    brow  +20.5 mm -> 0.433      nose base  -22.5 mm -> 0.574
    eye    +4.9 mm -> 0.484      mouth      -39.1 mm -> 0.631
                                 chin       -70.4 mm -> 0.756

Feature widths come from the same geometry: the head's equator circumference is
484 mm, so a 28 mm eye spans du = 0.058 and a 26 mm mouth du = 0.054.

Expected measurable effect: the geometry terms should barely move -- five small
meshes are removed and the head's own extent is unchanged, so silhouette IoU should
hold within noise. The change to look for is the scoreboard's region colour term
for `head`, currently the worst region at dE 42.8 against the reference's L 59.4,
and whether the face reads at all in the sheet. If IoU falls more than noise, the
removed features were carrying silhouette and this should be reverted.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SPEC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'object-sculpt-spec.json'
TEX = 1024

# Painted away, because at this framing they are one to three pixels each and the
# texture states them far better than a mesh can.
PAINTED = ('eye-l', 'eye-r', 'brow-l', 'brow-r', 'mouth', 'eye-cavity-l', 'eye-cavity-r',
           'nose')
# The nose is painted too, and it took two attempts to see why it had to be. As
# authored it was 31.7 x 52.8 x 33.0 mm on a head 154 mm deep -- a beak. Resized to
# 22 x 32 x 13 mm it still spanned y 1.529-1.561 in world space while the painted
# mouth sits at 1.5405, so the mesh covered the mouth completely and the render came
# back with no mouth at all. Both attempts are on the record because the second one
# looked like a fix and was not.
#
# The reference implementation paints the nose as a lit bridge plus two nostril
# shadows and models nothing, which is the right call at this framing: a 13 mm
# projection is about two pixels of profile silhouette, against a mouth it hides
# entirely from the front. Five of the six scored views are not the profile.
KEPT = ('ear-l', 'ear-r')


def bgr_of(spec: dict, mat_id: str, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
    """A material's measured base colour, as BGR. Never a colour chosen here."""
    for m in spec['materials']:
        if m['id'] == mat_id:
            hexcol = (m.get('baseColor') or m.get('color') or '').lstrip('#')
            if len(hexcol) == 6:
                r, g, b = (int(hexcol[i:i + 2], 16) for i in (0, 2, 4))
                return (b, g, r)
    return fallback


def blob(img, cx, cy, rx, ry, colour, softness=0.86, alpha=1.0, angle=0.0):
    """A soft-edged ellipse, feathered from `softness` of its radius to the rim.

    The reference implementation's `blob()` builds the same thing from a canvas
    radial gradient. Here it is a distance field over the ellipse, which gives the
    same falloff without a gradient object.
    """
    h, w = img.shape[:2]
    x0, x1 = max(0, int(cx - rx * 1.6)), min(w, int(cx + rx * 1.6) + 1)
    y0, y1 = max(0, int(cy - ry * 1.6)), min(h, int(cy + ry * 1.6) + 1)
    if x1 <= x0 or y1 <= y0:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    dx, dy = xx - cx, yy - cy
    if angle:
        ca, sa = np.cos(-angle), np.sin(-angle)
        dx, dy = dx * ca - dy * sa, dx * sa + dy * ca
    d = np.sqrt((dx / max(rx, 1e-6)) ** 2 + (dy / max(ry, 1e-6)) ** 2)
    a = np.clip((1.0 - d) / max(1e-6, 1.0 - softness), 0.0, 1.0) * alpha
    a = a[..., None]
    img[y0:y1, x0:x1] = (img[y0:y1, x0:x1] * (1 - a) + np.array(colour, np.float32) * a)


def build_face(spec: dict) -> np.ndarray:
    skin = bgr_of(spec, 'skin', (150, 165, 195))
    shade = bgr_of(spec, 'skinShade', (110, 122, 145))
    eye = bgr_of(spec, 'eye', (150, 96, 74))
    sclera = bgr_of(spec, 'sclera', (231, 225, 222))
    pupil = bgr_of(spec, 'pupil', (28, 26, 24))
    lip = bgr_of(spec, 'lip', (120, 108, 150))
    brow = bgr_of(spec, 'brow', (110, 70, 52))

    img = np.zeros((TEX, TEX, 3), np.float32)
    img[:] = skin

    U = lambda u: u * TEX          # noqa: E731 -- azimuth fraction to pixels
    V = lambda v: v * TEX          # noqa: E731 -- crown-to-chin fraction to pixels
    FRONT = 0.25                   # +Z in three.js sphere UVs; derived, not guessed

    # a faint shaded rim so the head does not read as a flat disc under flat light,
    # centred on the face rather than the sphere's equator
    blob(img, U(FRONT), V(0.575), U(0.145), V(0.30), shade, softness=0.10, alpha=0.5)
    blob(img, U(FRONT), V(0.560), U(0.112), V(0.235), skin, softness=0.35, alpha=1.0)
    # jaw and chin shading, so the lower face is not a blank expanse
    blob(img, U(FRONT), V(0.735), U(0.062), V(0.055), shade, softness=0.25, alpha=0.35)
    blob(img, U(FRONT), V(0.700), U(0.048), V(0.040),
         tuple(min(255, c * 1.04) for c in skin), softness=0.4, alpha=0.6)

    eye_v, eye_dx = 0.484, 0.046
    for sign in (-1, +1):
        cx = U(FRONT + sign * eye_dx)
        # socket shading, then the eye itself: sclera, iris, pupil, lash line
        blob(img, cx, V(eye_v + 0.006), U(0.038), V(0.030), shade, softness=0.2, alpha=0.55)
        blob(img, cx, V(eye_v), U(0.029), V(0.018), sclera, softness=0.72)
        blob(img, cx, V(eye_v), U(0.0155), V(0.0155), eye, softness=0.80)
        blob(img, cx, V(eye_v), U(0.0070), V(0.0070), pupil, softness=0.85)
        blob(img, cx - U(0.005), V(eye_v - 0.006), U(0.0045), V(0.0040),
             (250, 250, 250), softness=0.9, alpha=0.85)          # catchlight
        blob(img, cx, V(eye_v - 0.016), U(0.030), V(0.0055), pupil,
             softness=0.55, alpha=0.85)                          # upper lash line
        # brow, angled outward-down the way the reference's are
        blob(img, cx, V(0.433), U(0.0352), V(0.0090), brow, softness=0.45,
             angle=sign * 0.13)

    # nose: a lit bridge and two nostril shadows. The bridge is light on skin, so it
    # reads at figure scale where a 30 mm ellipsoid does not.
    blob(img, U(FRONT), V(0.532), U(0.0105), V(0.052),
         tuple(min(255, c * 1.10) for c in skin), softness=0.25, alpha=0.55)
    for sign in (-1, +1):
        blob(img, U(FRONT + sign * 0.0145), V(0.574), U(0.0065), V(0.0050),
             shade, softness=0.5, alpha=0.8)

    # mouth: upper and lower lip split by a darker seam, as the reference does
    blob(img, U(FRONT), V(0.6255), U(0.0269), V(0.0125), lip, softness=0.55)
    blob(img, U(FRONT), V(0.6335), U(0.0255), V(0.0110),
         tuple(min(255, c * 1.12) for c in lip), softness=0.6)
    blob(img, U(FRONT), V(0.6230), U(0.0250), V(0.0028),
         tuple(c * 0.55 for c in lip), softness=0.5, alpha=0.85)

    # the seam at u=0 and u=1 is the back of the head, under hair in every view, but
    # blurring the wrap keeps a hard line out of any grazing view
    img = cv2.GaussianBlur(img, (0, 0), TEX / 900)
    return np.clip(img, 0, 255).astype(np.uint8)


def main() -> int:
    spec = json.loads(SPEC.read_text(encoding='utf-8'))
    comps = {c['id']: c for c in spec['componentTree']}

    face = build_face(spec)
    (ROOT / 'pbr/face').mkdir(parents=True, exist_ok=True)
    (ROOT / 'public').mkdir(exist_ok=True)
    cv2.imwrite(str(ROOT / 'pbr/face/face_albedo.png'), face)
    (ROOT / 'public/face_albedo.png').write_bytes((ROOT / 'pbr/face/face_albedo.png').read_bytes())

    # a `face` material cloned from measured skin, carrying the painted map
    skin = next(m for m in spec['materials'] if m['id'] == 'skin')
    face_mat = json.loads(json.dumps(skin))
    face_mat['id'] = 'face'
    face_mat['name'] = 'Face (painted)'
    face_mat['notes'] = ('Skin, with the facial features painted into the albedo rather '
                         'than modelled. Colours are read from the measured eye, sclera, '
                         'pupil, lip, brow and skinShade materials; the texture is '
                         'generated, so it carries no reference pixels.')
    for ch in ('albedo',):
        if isinstance(face_mat.get(ch), dict) and isinstance(face_mat[ch].get('map'), dict):
            face_mat[ch]['map'] = {'path': str(ROOT / 'pbr/face/face_albedo.png'),
                                   'url': 'face_albedo.png', 'channel': 'albedo',
                                   'source': 'generated-from-measured-materials'}
    rp = face_mat.get('referencePbr')
    if isinstance(rp, dict) and isinstance(rp.get('maps'), dict):
        rp['maps']['albedo'] = dict(face_mat['albedo']['map'])
    # the face must not tile: it is a single painted layout, not a material sample
    face_mat.setdefault('textureProjection', {})['repeat'] = [1.0, 1.0]
    spec['materials'] = [m for m in spec['materials'] if m['id'] != 'face'] + [face_mat]

    # head back to a primitive so it carries spherical UVs
    head = comps['head']
    was_implicit = head.get('topologyClass') == 'implicit'
    head['topologyClass'] = 'assembled-solid'
    head['primitive'] = 'ellipsoid'
    head['material'] = 'face'
    head['materialLayers'] = ['face']
    gd = head.get('geometryDescriptor') or {}
    gd.pop('sdf', None)
    gd.pop('subdivide', None)
    gd['uvStrategy'] = 'spherical, from the ellipsoid primitive'
    head['geometryDescriptor'] = gd
    head['notes'] = ((head.get('notes') or '') +
                     ' Primitive rather than implicit, because polygonizeSdf emits no UVs '
                     'and the face is painted into the albedo.').strip()

    dropped = [c for c in spec['componentTree'] if c['id'] in PAINTED]
    spec['componentTree'] = [c for c in spec['componentTree'] if c['id'] not in PAINTED]
    gone = {c['id'] for c in dropped}
    for c in spec['componentTree']:
        if c.get('parent') in gone:
            c['parent'] = 'head'
    for bp in spec.get('buildPasses', []):
        if isinstance(bp.get('componentRefs'), list):
            bp['componentRefs'] = [r for r in bp['componentRefs'] if r not in gone]
    rig = spec.get('rig') or {}
    rig['bones'] = [b for b in (rig.get('bones') or []) if b.get('component') not in gone]

    SPEC.write_text(json.dumps(spec, indent=1), encoding='utf-8')

    print(f'face texture {TEX}x{TEX} written from measured materials '
          f'(skin, skinShade, eye, sclera, pupil, lip, brow)')
    print(f'head: {"implicit -> " if was_implicit else ""}ellipsoid primitive, '
          f'material "face", spherical UVs')
    print(f'painted away, no longer meshes: {", ".join(sorted(gone))}')
    print(f'kept as geometry: {", ".join(k for k in KEPT if k in comps)}')
    print(f'components {len(comps)} -> {len(spec["componentTree"])}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
