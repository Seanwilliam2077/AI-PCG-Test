# Image analysis — Arcane Jinx turnaround

Protocol: `grimoire/intake/image_analysis.md`, all eight layers, generic pass first,
character specialisation layered after.

**Input is unusually strong for this pipeline.** The protocol is written around a single
photograph. Here the reference is a professional *character turnaround sheet*: six
orthographic-ish views of the textured model, the same six as an untextured sculpt, and four
head close-ups. Everything the protocol normally has to mark `hidden` is actually observed.
Provenance and the fetch/matte procedure are in `ref/manifest.json`.

Source: Thibaut Granet, *ARCANE — Jinx*, © Riot Games. Used as a measurement target only.

---

## Layer 1 — Identification & classification

- **Work type:** full-body humanoid game character, stylised realism.
- **Broad classification:** character (biped, clothed, prop-carrying).
- **`primaryDomain`:** `character`. Confidence **0.98** — humanoid silhouette, skin/cloth/hair
  material set, readable pose, no ambiguity.
- **Identity:** Jinx as designed for the *Arcane* series — not the League of Legends base-game
  Jinx, which has a different outfit and a much longer torso-to-leg ratio.
- **Route:** `character-conditional → maximum likeness`. The user's stated goal is "as close as
  possible to the reference", which is the explicit intent the rubric requires before taking the
  projection-first path.

## Layer 2 — Overall form & silhouette

- **Bounding volume:** 1.72 m tall (declared scale; the sheet carries none), 0.30 m across the
  ribcage including both arms, 0.19 m deep at the waist. Footprint ~0.28 × 0.20 m.
- **Symmetry:** **bilateral in construction, asymmetric in pose and kit.** This matters more than
  anything else in this layer:
  - weight on her right leg; her left foot's lowest point sits **47 mm (2.74 % of figure height)
    above** her right's;
  - the Zapper pistol, its holster and the thigh canister are on her **left** (+X);
  - the cloud tattoos are on her **right** (−X);
  - the hip sash hangs low on her **right**;
  - the two braids do not drape symmetrically — at y = 0.70 the braid mass sits 0.07 m behind the
    leg on her left side and 0.19 m behind it on her right.
- **Shape language:** organic through the body and hair, geometric through the boots, belts and
  the pistol. Not reducible to one primitive family — the trunk is a lofted elliptical section,
  the limbs are tapered swept solids, the kit is hard-surface.
- **Proportion:** **8.2 head-units.** Measured, not assumed: hair-crest tip to chin is 0.122 of
  total figure height. That is well above realistic (7.5) and far above anime-adjacent (5–6) —
  the design is deliberately long-legged. Crotch at 0.543 of height against a real figure's
  0.47–0.49; knee at 0.337 against ~0.285.

## Layer 3 — Macro → meso → micro

**Macro** — body, head, hair, top, trousers, sash, belts, gloves, boots, pistol.

**Meso** —
- head: cranium, mandible, zygomatic arch, nose, lips, eyes, ears;
- hair: scalp cap, centre-parted fringe, upswept crest, two face-framing side locks, two ankle-
  length plaited braids, three ties per braid, frayed tassels;
- top: front panel, halter strap round the neck, under-bust band, X lacing;
- trousers: two legs, waistband, tattered hem;
- sash: wrap, canvas panel, pouch;
- belts: hip belt, diagonal strap, thigh strap, two upper-arm bands;
- boots: sole slab, upper, folded cuff, toe cap, cross lacing;
- pistol: barrel, muzzle ring, tank, receiver, grip, trigger guard.

**Micro** — eyelet rings on the X lacing, buckles and rivets along the belt runs, boot tread,
stripe pattern on the trousers, brow and lash linework, freckles.

## Layer 4 — Spatial relationships

- `<halter strap, wraps, neck>` — contact type *overlap*, sits under the choker.
- `<choker, encircles, neck>` at y = 1.452, *overlap*.
- `<X lacing, embedded-in, top front panel>` — *embed*, eyelets pierce the cloth.
- `<arm bands, encircle, left upper arm>` at y = 1.268 and 1.196, *overlap*.
- `<sash, drapes-over, trouser waist>` — *overlap*, low corner on her right.
- `<pouch, attached-to, sash>` — *socket*.
- `<holster, attached-to, thigh strap>`; `<pistol, seated-in, holster>` — *socket*.
- `<boot cuff, folds-over, boot upper>` — *overlap*, flares outward.
- `<braids, lie-on, back>` — **flush-with, not floating.** The reference silhouette is a single
  run from hips to crown on both side views because the rope rests against the back. This is the
  single most commonly mis-built relationship in the subject.

## Layer 5 — Materials & surface (PBR)

One claim per surface, sampled off `body_2.png` as medians and stated as sRGB display values —
**these carry the sheet's own lighting and are not albedo** (see Layer 8).

| region | sampled sRGB | metalness | roughness | relief |
|---|---|---|---|---|
| skin | 0.831, 0.741, 0.706 | 0 | 0.62 | pores below resolution; freckles are texture |
| hair | 0.192, 0.380, 0.514 | 0 | 0.42 | anisotropic sheen along the strand |
| black cloth (top, gloves) | 0.220, 0.227, 0.337 | 0 | 0.86 | visible weave; **never reads as dead black** |
| trousers | 0.330, 0.195, 0.295 | 0 | 0.80 | fine vertical pinstripe, ~21.5 mm pitch |
| leather (belts, boots) | 0.192, 0.161, 0.157 | 0 | 0.66 | grain, edge wear |
| canvas panel | 0.478, 0.451, 0.325 | 0 | 0.90 | woven |
| brass (X lacing, toe cap, buckles) | 0.706, 0.545, 0.286 | 0.85 | 0.38 | polished, worn at edges |
| steel (pistol) | 0.475, 0.490, 0.510 | 0.90 | 0.35 | brushed |
| tattoo ink | 0.769, 0.667, 0.624 | 0 | 0.62 | **within ~0.06 of skin — not cyan** |

Translucency: opaque everywhere. No transmission anywhere in the subject.

## Layer 6 — Colour & finish

- Hair: vivid blue, mid value, high saturation at the crown, desaturating toward the braid tips.
- Trousers: desaturated magenta, low-mid value, with a darker stripe — a two-tone finish, not
  one flat colour.
- Metal splits into two finishes: **brass, satin, warm** on the garment furniture, and **steel,
  brushed, neutral** on the pistol. Reading them as one metal is a common error.
- Boots: near-black leather with a **brass toe cap** and magenta laces.

## Layer 7 — Identity-defining features

Ranked by how much each carries recognition:

1. **Two ankle-length blue plaited braids**, resting on the back, splitting lower down.
2. **The upswept crest** — one breaking wave off the crown, not a fan of spikes.
3. **The gold X lacing** across a black halter crop top.
4. **Purple pinstripe capris with a tattered hem** below the knee.
5. **Cloud tattoos** on her right arm and ribs, pale grey-blue.
6. Chunky black boots with a brass toe cap and magenta cross-lacing.
7. The Zapper pistol on her left thigh.
8. Two black bands on her left upper arm — the *clean* arm; the tattooed arm is bare.

Each becomes a `detailInventory` entry; 1, 2, 3 and 8 also become `featureReviewTargets`
because each was built wrong at least once in the previous reconstruction.

## Layer 8 — Uncertainty & single-image limits

What the reference genuinely does **not** settle:

- **Absolute scale.** No dimension is given anywhere on the sheet. 1.72 m is a declared choice;
  every other length is a measured ratio against it.
- **The two side panels disagree about the braid.** At y = 0.70 the braid mass sits 0.07 m behind
  the leg's back edge in `clay_0` and 0.19 m behind it in `clay_4`. A silhouette is a union of
  projections, so no single static rope satisfies both. Marked *uncertain*; the drape follows
  `clay_0`.
- **Sampled colours are not albedo.** Every value in Layer 5 is a median off a *render*, so it
  carries that render's lighting. Using them directly as base colour and then lighting them again
  double-counts — measured at +15 L on the hair before correction. A de-lighting pass is a hard
  requirement, not an optimisation.
- **Interiors** — inside the boots, under the sash, behind the trouser fold — are *hidden* in all
  ten views. Mark low confidence rather than inventing.
- **Hair microstructure and skin pores** are below the sheet's resolution (the front figure is
  377 px wide at native scale). *Undetermined*; stylised clumps only, per the character track.
- **The intermediate panels' exact yaw.** Fitted from torso width at two bare-midriff heights to
  35° and 315° ± 10°, not assumed to be 45°. Whole-silhouette IoU cannot resolve this — swept
  across yaw it rises monotonically toward the front for *every* panel.

No `request-input` is needed: front, both sides, both three-quarters, back and four head
close-ups are all present. That is the input the rubric tells you to ask for.
