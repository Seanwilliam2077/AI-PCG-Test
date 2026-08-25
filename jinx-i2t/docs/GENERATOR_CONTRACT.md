# What the generator actually reads

Five bugs stood between a validated spec and a correct blockout. Every one
passed strict validation, and every one was found by *rendering*. They are all
the same mistake: I filled spec fields to satisfy the **validator** without
knowing how the **generator** consumes them.

Writing them down because none is discoverable from the schema.

## 1. Position comes from `attachment.localStart`, not `transform.position`

For a component with an attachment, the generator emits

```js
node.position.copy(endpoint.start)   // endpoint built from attachment.localStart
```

The strict gate demands `localStart`/`localEnd` exist. I gave them
`[0,0,0]` and `[0, height, 0]` as placeholders to clear the gate — and every
component collapsed onto its parent's origin. The whole character rendered as a
single vertical pole.

**Placeholders that satisfy a gate are not neutral.** If a field is required, it
is required because something reads it.

## 2. Geometry comes from `attachment.baseRadius` / `endRadius`

An attached component is not emitted as its `primitive`. It is emitted as a
tapered cylinder swept between `localStart` and `localEnd`:

```js
new THREE.CylinderGeometry(endpoint.endRadius, endpoint.baseRadius, endpoint.length, …)
```

With no radii given, everything defaulted to the same cone. `primitive: capsule`
was simply not consulted. The model is *limb-shaped*: a component is a tapered
solid between two joints — which suits a character skeleton very well once you
know it.

## 3. `transform.scale` silently overrides `dimensions`

```py
def scale_vector(component, transform):
    if "scale" in transform:
        return vector(transform.get("scale"), [1, 1, 1])   # wins outright
    dimensions = component.get("dimensions")               # only reached otherwise
```

Normalising the template by writing `scale: [1,1,1]` onto all 101 components
discarded every measured dimension and left each primitive at unit size. That is
what made the first blockouts a totem of metre-scale cones, and what kept the
root as a 1 m box across the lower frame.

## 4. `transform.position` is parent-local, and it accumulates

The measured skeleton is in absolute metres above the floor. Written straight
into a hierarchy, each position adds to its parent's: head 1.59 + hair 1.64 +
cap 1.63 + crest 1.70 put the crest at **y 8.6** on a 1.72 m figure. Rebasing
every position to `world - parentWorld` fixed it in one pass.

The tell was in the numbers, not the picture: a bounding box topping out at 8.638.

## 5. A wrap garment cannot be one component

Because of (2), one component is one tapered cylinder. Trousers authored as a
single component spanning both legs became one tube swallowing both legs and the
gap between them. Wrap garments have to be **per limb**.

The corollary is the useful part: components split into two kinds.

| kind | examples | authoring |
|---|---|---|
| **limb-like** | arms, legs, fingers, neck, braids, belts, boots, gloves | give it an attachment with real `localStart`/`localEnd` and `baseRadius`/`endRadius`; it becomes a tapered solid between two joints |
| **blob-like** | head, ribcage, pelvis, eyes, crest, top, sash, pouch | give it **no** attachment; it falls back to `primitive` + `dimensions`, which is the only path that produces an ellipsoid or a box |

## How to catch this class of bug faster

The per-mesh extent probe in `src/main.ts` — reporting the lowest and tallest
meshes *by name* with their world Y — named bug 4 in one run after two rounds of
guessing from the spec. Any harness driving a generator you did not write should
print named per-object extents from the first render, not the scene bounding box
alone.
