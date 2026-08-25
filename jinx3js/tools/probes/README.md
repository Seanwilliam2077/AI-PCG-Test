# Measurement probes

Scratch tooling written by the part authors during the review rounds. Each is
prefixed with the part it was written for. They are kept because
`docs/MEASUREMENTS.md` cites several of them as the derivation of a number, and
because a few are generally useful:

- `*_probe.py` / `*_raw.py` — per-row silhouette run decomposition of a
  reference panel or a `--frame 1.80` preview, **in metres**, which is what most
  of the measurements in the docs are made with.
- `hair_backz.ts` — ray-marches every shell except the braids and reports
  `backZ(x, y)`, the body's rearmost surface. This is what the braid's depth
  column is set from, and it is the fix that stopped the braids hanging in air.
- `*_sweep.py` / `*_fsweep.py` — bake, render and score across one spec key,
  restoring the file on exit.
- `boots_bands.py`, `hair_band.py`, `hair_where.py` — which height bands an
  error actually lives in.

The docs refer to these by their original `out/` paths, which is where they were
written; they are copied here so they survive `out/` being ignored.
