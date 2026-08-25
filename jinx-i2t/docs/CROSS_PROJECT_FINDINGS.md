# Found while measuring something else

## The hand is small, and it was the pistol build that noticed

Establishing a metric scale for `../zapper-i2t` meant anchoring on this character's
hand, because the pistol's reference carries no dimension anywhere and a hand wrapped
around a grip is the only object in frame whose size is known. Six agents measured it.
Three independently reported the same contradiction, and it is about this build, not
theirs:

* `hand-l.width` was 0.044 m, but that field is the **palm block**. At the time the
  four fingers were separate components at 0.016 m each, so the hand's own four-finger
  span was 0.064 m. A palm narrower than the fingers growing out of it is not a shape.
* Four-finger breadth over stature: this spec asserted 0.044 / 1.715 = **0.0257**. The
  reference sheet itself shows 43 px / 1225 px = **0.0351**. Human anthropometry gives
  0.078 / 1.72 = **0.0453**.

The hand's *proportions* were fine — length over breadth 2.09 against a real 2.26 — so
this was a scale error in one part, not a malformed hand.

**Partly fixed already, by accident.** `analysis/patch_extremities.py` had since
replaced the palm and its thirty finger phalanges with a single implicit mitten form,
on the grounds that a phalanx covers about a pixel at this framing. That took the built
hand from a 44 mm palm to a 51 mm mesh, against the sheet's 61 mm target: 84 % rather
than 69 %.

**Not chased further, deliberately.** Closing the remaining 20 % now means rescaling an
SDF descriptor's bounds and its normalisation together, on a part covering roughly
30 x 40 px in a 500 x 900 render. The measurement is recorded here so the next person
does not rediscover it; the effort was spent elsewhere.

**The transferable part** is that the error was invisible from inside this project. It
took a different object, needing this one as a ruler, to expose it. A number that is
only ever consumed by the model that declares it is never tested.

## The pistol's scale chain, for the record

The brief handed to the pistol's measurement agents asserted 0.838 mm/px on the source
sheet, derived from that same 0.044 m. Four of six reports independently corrected it —
to 1.60x, 1.66x, 1.67x and 1.70x — and the frozen contract adopted **1.400 mm/px**.

Every absolute length in that brief was too small by 1.67x. The pixel half of the chain
was fine; the metre half was the axiom, and the axiom was wrong.
