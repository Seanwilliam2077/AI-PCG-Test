"""Add the costume components and the measured material palette to the spec.

The character template ships a bare rigged humanoid. Everything that makes the
subject recognisable -- hair, top, trousers, sash, belts, boots, pistol, ink --
is added here, each entry carrying the note that says how it was got wrong
before, so the build passes have the failure mode in front of them.
"""
import json

M = json.load(open('analysis/measured_skeleton.json', encoding='utf-8'))
sk = M['skeleton']
SPEC = 'object-sculpt-spec.json'
d = json.load(open(SPEC, encoding='utf-8'))
tmpl = d['componentTree'][1]


def comp(cid, name, level, parent, pos, dims, mat, importance, conf, note,
         role="accessory", repetition=None):
    c = json.loads(json.dumps(tmpl))
    c.update({
        "id": cid, "name": name, "level": level, "role": role,
        "importance": importance, "confidence": conf, "parent": parent,
        "transform": {"position": [round(v, 4) for v in pos], "rotation": [0, 0, 0], "scale": [1, 1, 1]},
        "dimensions": {"width": dims[0], "height": dims[1], "depth": dims[2],
                       "units": "metres", "confidence": conf},
        "materialRef": mat, "notes": note,
        "attachment": {"parentSocket": parent, "contactType": "overlap", "embedDepth": 0.004},
    })
    if repetition:
        c["repetitionRef"] = repetition
    return c


NEW = [
    comp("hair-cap", "Scalp cap", "meso", "hair", [0, 1.630, -0.012], (0.150, 0.140, 0.170), "hair", 0.7, 0.85,
         "Follows the skull; the centre part is an 8 mm groove that vanishes below a ~10 mm voxel.", "hair"),
    comp("hair-crest", "Upswept crest", "meso", "hair", [-0.012, 1.700, -0.030], (0.120, 0.110, 0.190), "hair", 0.95, 0.85,
         "ONE breaking wave from her left-back to her right-front, overhanging the brow to z +0.058. NOT a fan of "
         "spikes: crown width 0.161 m at yaw 45 against 0.067 m at yaw 315, a 2.4x directional fin.", "hair"),
    comp("hair-fringe", "Centre-parted fringe", "meso", "hair", [0, 1.632, 0.052], (0.130, 0.080, 0.060), "hair", 0.7, 0.8,
         "Five locks unioned AFTER the hairline cut so they lie over the forehead instead of being sliced off by it.", "hair"),
    comp("hair-sidelock-l", "Side lock (her left)", "meso", "hair", [0.058, 1.500, 0.030], (0.030, 0.170, 0.040), "hair", 0.6, 0.8,
         "Face-framing lock in front of the ear.", "hair"),
    comp("hair-sidelock-r", "Side lock (her right)", "meso", "hair", [-0.058, 1.500, 0.030], (0.030, 0.170, 0.040), "hair", 0.6, 0.8,
         "Mirror of the left lock.", "hair"),
    comp("braid-l", "Braid (her left)", "macro", "hair", [0.030, 0.900, -0.100], (0.055, 1.610, 0.055), "hair", 1.0, 0.9,
         "Plaited rope from the crown to y=0.082. RESTS ON the back: its depth column is set from the assembled body's "
         "rearmost surface, not hung in space. Envelope radius 0.0195 at the root, 0.027 at the gather, 0.0158 at the tie.",
         "hair", repetition="braid-plait"),
    comp("braid-r", "Braid (her right)", "macro", "hair", [-0.030, 0.900, -0.100], (0.055, 1.610, 0.055), "hair", 1.0, 0.9,
         "Mirror path, but NOT a mirror drape: clay_4 shows this braid mass 0.19 m behind the leg's back edge at y=0.70 "
         "against clay_0's 0.07 m. No single static rope satisfies both panels; the drape follows clay_0 and clay_4 is "
         "recorded as an unreachable projection.", "hair", repetition="braid-plait"),
    comp("braid-ties", "Braid ties", "micro", "hair", [0, 0.700, -0.110], (0.040, 0.900, 0.040), "leather", 0.5, 0.85,
         "Three bands along each braid.", "hair"),
    comp("braid-tassel", "Frayed tips", "micro", "hair", [0, 0.100, -0.090], (0.060, 0.060, 0.060), "hair", 0.5, 0.8,
         "The reference puts 0.0137 of the side-view silhouette below y=0.20; a braid that stops dead at the tie puts 0.0035.", "hair"),

    comp("top", "Halter crop top", "macro", "chest", [0, 1.300, 0.012], (0.215, 0.150, 0.230), "cloth", 0.95, 0.9,
         "Front panel rising into a strap round the neck. The BACK IS OPEN -- bare skin and the tattoo show there.", "garment"),
    comp("top-strap", "Halter neck strap", "meso", "top", [0, 1.410, 0.010], (0.090, 0.070, 0.090), "cloth", 0.6, 0.85,
         "Climbs to the throat; the neckline is a high narrow V, not a straight bandeau edge.", "garment"),
    comp("top-band", "Under-bust band", "meso", "top", [0, 1.243, 0.014], (0.210, 0.026, 0.220), "cloth", 0.6, 0.85,
         "Carries a centre buckle.", "garment"),
    comp("x-lacing", "Brass X lacing", "meso", "top", [0, 1.318, 0.098], (0.080, 0.080, 0.018), "brass", 0.9, 0.9,
         "Two crossed straps through FOUR ring eyelets. Degrades to four dots below a ~4 mm voxel, which is why it is a "
         "featureReviewTarget.", "garment"),
    comp("choker", "Choker", "meso", "neck", [0, 1.452, 0.004], (0.100, 0.032, 0.104), "cloth", 0.8, 0.9,
         "Sits proud of the neck. In an earlier build the neck loft capped off with a 137 mm ball at the throat and "
         "swallowed this whole.", "garment"),
    comp("choker-straps", "Choker wraps", "micro", "choker", [0, 1.440, 0.040], (0.090, 0.060, 0.060), "leather", 0.5, 0.8,
         "Three straps, one crossing the throat diagonally.", "garment"),

    comp("pants", "Pinstripe capris", "macro", "pelvis", [0, 0.760, 0.004], (0.290, 0.640, 0.230), "pants", 0.95, 0.9,
         "Low-rise at y=1.078, ending BELOW the knee at y=0.438-0.49. Baggy at the hip, tapering hard below the sash.",
         "garment", repetition="trouser-pinstripe"),
    comp("pants-hem", "Tattered hem", "meso", "pants", [0, 0.450, 0.004], (0.280, 0.080, 0.220), "pants", 0.8, 0.9,
         "Saw-tooth, ~8 teeth per leg; the reference's teeth vary in WIDTH and LEAN as well as depth.", "garment"),
    comp("sash", "Hip sash", "macro", "pelvis", [-0.010, 0.960, 0.010], (0.300, 0.290, 0.250), "pants", 0.9, 0.85,
         "A WRAP, not a barrel: it must not close across the midline or it fills the negative space between the thighs "
         "and destroys the open-legged read. Low corner on her RIGHT (-X).", "garment"),
    comp("canvas-panel", "Canvas panel", "meso", "sash", [0.010, 1.040, 0.100], (0.150, 0.090, 0.060), "canvas", 0.7, 0.85,
         "Front waist, dipping toward her left.", "garment"),
    comp("pouch", "Hip pouch", "meso", "sash", [0.100, 0.960, 0.050], (0.062, 0.078, 0.034), "leather", 0.6, 0.8,
         "Lapped box on the wrap.", "garment"),

    comp("hip-belt", "Hip belt", "meso", "pelvis", [0, 1.062, 0.010], (0.300, 0.026, 0.230), "leather", 0.8, 0.9,
         "Centre buckle at the front.", "garment", repetition="belt-hardware"),
    comp("diagonal-strap", "Diagonal hip strap", "meso", "pelvis", [0.020, 1.010, 0.030], (0.280, 0.120, 0.220), "leather", 0.7, 0.85,
         "Low end on her LEFT.", "garment"),
    comp("thigh-strap", "Thigh strap", "meso", "thigh-l", [0.070, 0.855, 0.020], (0.150, 0.030, 0.150), "leather", 0.7, 0.85,
         "Carries the holster.", "garment"),
    comp("arm-band-upper", "Arm band (upper)", "meso", "upper-arm-l", [0.118, 1.268, 0.062], (0.080, 0.030, 0.078), "cloth", 0.7, 0.9,
         "On her LEFT arm -- the BARE, untattooed one. Describing this as 'the tattooed arm' is what put the ink on the "
         "wrong side in an earlier build.", "garment"),
    comp("arm-band-lower", "Arm band (lower)", "meso", "upper-arm-l", [0.126, 1.196, 0.068], (0.078, 0.030, 0.076), "cloth", 0.7, 0.9,
         "Second band, same arm.", "garment"),
    comp("glove-l", "Glove (her left)", "macro", "forearm-l", [0.160, 1.010, 0.080], (0.070, 0.230, 0.062), "cloth", 0.8, 0.9,
         "Fingerless, covering most of the forearm; the fingers are cut at the knuckle.", "garment"),
    comp("glove-r", "Glove (her right)", "macro", "forearm-r", [-0.160, 1.010, 0.080], (0.070, 0.230, 0.062), "cloth", 0.8, 0.9,
         "Mirror.", "garment"),
    comp("nails", "Teal fingernails", "micro", "glove-l", [0.200, 0.870, 0.086], (0.040, 0.020, 0.020), "nailTeal", 0.3, 0.85,
         "The only saturated cool accent below the waist. Found by cropping; missed entirely in the previous reconstruction.",
         "garment"),

    comp("boot-l", "Boot (her left)", "macro", "foot-l", [0.049, 0.150, 0.020], (0.108, 0.300, 0.200), "leather", 0.9, 0.9,
         "Hangs off the ANKLE JOINT in Y as well as X/Z. Translating Y by a literal 0 is what left the contrapposto "
         "stranded at the shells in an earlier build: a 47 mm lift came out as 0.", "garment"),
    comp("boot-r", "Boot (her right)", "macro", "foot-r", [-0.055, 0.103, -0.008], (0.108, 0.300, 0.200), "leather", 0.9, 0.9,
         "Planted; this is the weight-bearing foot.", "garment"),
    comp("boot-sole", "Sole slab", "meso", "boot-l", [0.049, 0.020, 0.020], (0.096, 0.036, 0.200), "leather", 0.6, 0.9,
         "36 mm slab overhanging the upper by 14 mm.", "garment"),
    comp("boot-cuff", "Folded cuff", "meso", "boot-l", [0.049, 0.305, 0.010], (0.180, 0.070, 0.190), "leather", 0.8, 0.85,
         "A deep floppy ROLL that flares outward, not a smooth cone. The hem tucks IN across the boot and flares OUT "
         "fore-and-aft -- that lateral relation is signed and was inverted twice.", "garment"),
    comp("boot-toecap", "Brass toe cap", "meso", "boot-l", [0.049, 0.045, 0.120], (0.080, 0.045, 0.060), "brass", 0.7, 0.9,
         "", "garment"),
    comp("boot-lace", "Cross lacing", "micro", "boot-l", [0.049, 0.180, 0.075], (0.050, 0.180, 0.030), "laceMagenta", 0.6, 0.9,
         "Six rows.", "garment", repetition="boot-lacing"),

    comp("zapper", "Zapper pistol", "macro", "thigh-l", [0.118, 0.885, 0.055], (0.070, 0.300, 0.090), "steel", 0.85, 0.85,
         "On her LEFT thigh (+X). Visible in body_0 and absent from body_4 -- that pair is the evidence for the side.", "prop"),
    comp("zapper-tank", "Glass tank", "meso", "zapper", [0.118, 0.850, 0.055], (0.052, 0.110, 0.052), "glassTank", 0.6, 0.8,
         "TRANSPARENT cylinder with visible teal and pink contents and brass end caps. The only translucent material in "
         "the subject -- transmission is justified here and nowhere else.", "prop"),
    comp("zapper-barrel", "Barrel", "meso", "zapper", [0.118, 0.760, 0.062], (0.038, 0.150, 0.038), "steel", 0.6, 0.85, "", "prop"),
    comp("zapper-grip", "Grip", "meso", "zapper", [0.118, 0.960, 0.040], (0.032, 0.078, 0.044), "leather", 0.5, 0.8, "", "prop"),

    comp("tattoo-region", "Cloud tattoos", "meso", "chest", [-0.070, 1.240, 0.020], (0.120, 0.420, 0.160), "tattoo", 0.85, 0.9,
         "Her RIGHT arm, shoulder and ribs (-X). INK, not geometry -- a painted region on the skin shell. Within ~0.06 "
         "of skin colour; the previous build made it bright cyan and spread it across the chest.", "skin"),
    comp("shin-patch", "Taped shin patch", "micro", "shin-l", [0.046, 0.400, 0.055], (0.040, 0.055, 0.014), "canvas", 0.3, 0.75,
         "On her LEFT shin above the boot cuff. Found by cropping.", "skin"),
]

d['componentTree'].extend(NEW)

MATS = [
    ("skin", "Skin", "#D4BDB4", 0.0, 0.62, "warm base; rim/backlight approximation, no true SSS"),
    ("skinShade", "Skin (shadow tint)", "#BCA298", 0.0, 0.64, "slightly desaturated shadow tint"),
    ("hair", "Hair", "#274E69", 0.0, 0.42, "vivid blue, mid value; anisotropic sheen along the strand"),
    ("hairDark", "Hair (roots/underside)", "#1D3A50", 0.0, 0.46, ""),
    ("cloth", "Black cloth", "#343749", 0.0, 0.86,
     "visible weave with a blue cast; NEVER reads as dead black -- measured albedo L 18.7, not 5"),
    ("pants", "Trousers", "#54324B", 0.0, 0.80, "desaturated magenta"),
    ("pantsDark", "Trouser stripe", "#402439", 0.0, 0.82, "the darker pinstripe"),
    ("leather", "Leather", "#312928", 0.0, 0.66, "grain, edge wear"),
    ("canvas", "Canvas", "#7A7353", 0.0, 0.90, "woven khaki"),
    ("brass", "Brass", "#B48B49", 0.85, 0.38, "satin, warm; garment furniture"),
    ("steel", "Steel", "#797D82", 0.90, 0.35,
     "brushed, neutral; pistol only -- reading brass and steel as one metal is a common error"),
    ("tattoo", "Tattoo ink", "#BEC7CB", 0.0, 0.62, "pale grey-blue, within ~0.06 of skin"),
    ("laceMagenta", "Boot lace", "#8E3A5C", 0.0, 0.85, ""),
    ("nailTeal", "Nail polish", "#3FB8B0", 0.0, 0.35, ""),
    ("glassTank", "Tank glass", "#9FB6BE", 0.0, 0.12,
     "the ONLY translucent material in the subject; transmission is justified here and nowhere else"),
    ("eye", "Iris", "#5A8296", 0.0, 0.20, ""),
    ("sclera", "Sclera", "#ECE8E4", 0.0, 0.22, ""),
    ("pupil", "Pupil", "#1B1A20", 0.0, 0.18, ""),
    ("lip", "Lip", "#A96766", 0.0, 0.50, ""),
    ("brow", "Brow", "#3A2C28", 0.0, 0.70, ""),
]

base = d['materials'][0]
mats = []
for mid, name, hexc, metal, rough, note in MATS:
    m = json.loads(json.dumps(base))
    m.update({
        "id": mid, "name": name, "baseColor": hexc, "color": hexc,
        "metalness": metal, "roughness": rough, "notes": note,
        "albedo": {
            "dominant": hexc, "secondary": [],
            "samplingNotes": (
                "Median sampled off body_2.png and DE-LIT. The raw sample carries the sheet's own "
                "lighting; using it directly put the hair +14.65 L too bright once the global exposure "
                "offset was removed."),
        },
    })
    if mid == "glassTank":
        m["transmission"] = 0.85
    mats.append(m)
d['materials'] = mats

json.dump(d, open(SPEC, 'w', encoding='utf-8'), indent=1)

from collections import Counter
print('components:', len(d['componentTree']), dict(Counter(c['level'] for c in d['componentTree'])))
print('materials:', len(d['materials']))
print('contract minimums:', d['qualityContract']['minimumSpecDepth'])
