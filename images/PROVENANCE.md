# What is in here, and what is deliberately not

Every image in this directory is safe to redistribute. That is a decision made per
image, not a blanket one, and the rule differs between the two character builds because
their materials have different origins.

## Published

| file | what it shows | why it is publishable |
|---|---|---|
| `jinx3js_yaw*.png` | the SDF + Surface Nets character, textured | its materials are procedural terms authored in TypeScript. No reference pixel is in them. |
| `jinx-i2t_yaw*.png` | the spec-driven character, **geometry only** | its textured renders bake albedo extracted from the reference, so only the material-stripped pass is published |
| `characters-side-by-side.png` | the two builds at a common figure height | same rule, applied per column |
| `img2threejs-gallery.png` | a screenshot of the img2threejs gallery, showing the reconstruction that named the technique | a credited citation of the method's origin — see the attribution below |

## Not published, anywhere in this repository

- The Jinx turnaround, the head close-ups and the five-pose sheet the pistol was
  measured from. © Riot Games, modelled and textured by **Thibaut Granet**
  (<https://thibaut_granet.artstation.com/projects/X1aWVw>).
- Every PBR map extracted from those pixels — albedo, roughness, normal, height,
  ambient occlusion, twenty materials each — and the served copies of them.
- Any render that displays those maps.

The distinction being drawn: a reference used as a **measurement target** is not
redistributed at full fidelity, and neither is anything derived pixel-wise from it. What
leaves this project from that source is *measurements* — proportions, landmark heights,
colour medians in CIE Lab — which are reported as numbers in the docs.

## Attribution for `img2threejs-gallery.png`

A screenshot of the img2threejs project gallery
(<https://github.com/img2threejs/img2threejs>), showing the entry
**"Dual-Sword Warrior — TypeScript procedural surfaces" by Hoài Nhớ**, tagged
`img2threejs v1.5.1 · procedural TypeScript Surface Nets`.

It is included because it is the origin of the method these projects use, and because
naming a technique without showing where it came from is worse citation than showing it.
The reconstruction is Hoài Nhớ's work and the thumbnail marked SOURCE REFERENCE within
it is a third party's character art; neither is claimed here, and both are reproduced
only at the size and fidelity of the original screenshot, for attribution.

If either author would prefer it removed, it will be.
