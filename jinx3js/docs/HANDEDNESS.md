# Which side is which

Read off `ref/views/body_2.png` (the front view) at 3x, and cross-checked
against the two side panels. **The first version of `PART_CONTRACT.md` had the
tattoos and the pistol on the wrong sides; this file is the corrected record.**

## The frame

Metres, Y up, character faces **+Z**. The default camera sits on +Z and looks
down −Z, so **screen-right is +X**.

Because the camera faces her, **+X is her LEFT** and appears on the **right** of
a front-view image — the same inversion as looking at someone in a mirror. Every
mistake in this project came from skipping that step, so state the side twice:
once as hers, once as the image's.

## Verified assignments

| feature | her side | axis | where it appears in a FRONT view |
|---|---|---|---|
| cloud tattoos (arm, ribs, back) | **right** | **−X** | image-**left** |
| Zapper pistol | **left** | **+X** | image-**right** |
| two black arm bands | **left** | **+X** | image-**right** |
| purple sash, low corner | **right** | **−X** | image-**left** |
| khaki/canvas panel | centre, dipping to her left | | centre, dipping image-right |
| diagonal hip strap, low end | **left** | **+X** | image-**right** |

So the tattooed arm is the **bare** one and the banded arm is the **clean** one.
They are on opposite sides. An earlier brief said the bands were "on the
tattooed arm", which is what put the ink on the wrong side.

## Reference panel to camera yaw

Panels run left to right across the sheet as a turnaround, but it is **not a
uniform rotation** — five views sweep front-ish, then a back view is appended:

| panel | what it is | yaw |
|---|---|---|
| `clay_0` / `body_0` | her **left** side; she faces image-left; pistol visible | **90°** |
| `clay_1` / `body_1` | three-quarter toward her left | **45°** |
| `clay_2` / `body_2` | **front** | **0°** |
| `clay_3` / `body_3` | three-quarter toward her right | **315°** |
| `clay_4` / `body_4` | her **right** side; tattooed arm toward camera | **270°** |
| `clay_5` / `body_5` | **back** | **180°** |

Two independent checks agree with this: the pistol is visible in `body_0` and
not in `body_4`, and the tattoos are visible in `body_4` and not in `body_0`.

**Silhouette IoU cannot resolve this mapping and must not be trusted to.** With
arms at the sides, front and back silhouettes of this figure differ by about
0.01 IoU — measured: yaw 0 scores 0.797 against both the front panel and the
back panel. A scoreboard fit will happily lock onto a rotated assignment. The
mapping above is knowledge, not a fit, and `out/view_map.json` should be pinned
to it rather than refitted.

## Symptom of getting it wrong

If a lateral feature is mirrored, the two side views score very differently
against their panels even though they are mirror images of each other. Measured
on the first integrated build, with the pistol on the wrong side: yaw 90 against
`clay_0` gave IoU 0.732, while yaw 270 against `clay_4` gave 0.537. A gap that
large between two mirrored pairs is the tell.

## The three-quarter panels *are* three-quarter views

Two authors independently concluded that `clay_1` and `clay_3` are not 45°
views — one putting `clay_3` "within ~15 degrees of frontal" — from the boot's
projected width: a boot 0.20 m long and 0.09 m wide cannot project narrower than
about 0.19 m at 45° off its own axis, yet those panels read the boot at
0.10–0.11 m, the same as dead ahead.

It is a good argument and it is wrong, for a reason worth recording: **the feet
are toed out**. In a three-quarter view one boot is seen nearly along its own
axis and is foreshortened to about its width, while the other is seen nearly
across. Measuring the foreshortened one gives exactly the reading above.

Fitted properly, from torso width at two bare-midriff heights — which varies as
`W·cos θ + D·sin θ` and is therefore actually sensitive to θ, unlike the
silhouette as a whole:

| panel | best-fit yaw | residual | pinned |
|---|---|---|---|
| `clay_1` | 35° | 1 mm | 45° (5 mm) |
| `clay_3` | 310–320° | 3 mm | 315° ✓ |
| `clay_2` | 0–10° | 5 mm | 0° ✓ |

So the pin stands. `clay_1` may be nearer 35° than 45°, on 4 mm of evidence,
which is not enough to move it.

**Do not use whole-silhouette IoU to fit a view angle on this figure.** Swept
across yaw it rises monotonically toward the front for *every* panel — it picks
0–25° as the best match for the side panels and for the back — because a
front-ish silhouette is the closest thing to an average of all of them. It is
the same blindness that makes the front and back panels indistinguishable.
