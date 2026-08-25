"""Re-assert the two material facts that pixel extraction cannot establish.

`extract_pbr_evidence.py` writes `roughness`, `metalness` and the map set from
the crop, which is right for everything the crop can actually show. Two things it
cannot show, and overwrites every time it runs:

  * The tank is glass. A 4 px patch on a 377 px panel carries no gloss
    information, so the extractor returns a fabric-like roughness; the pipeline's
    own material registry and `bind_detail_properties` both say glass, and the
    detail inventory's gloss entry fails strict validation without it. It also has
    to be `physical`, not `standard` -- MeshStandardMaterial has no transmission
    channel, so the transmission value the spec already carried was inert.
  * Metalness is binary in metallic-roughness PBR. brass 0.85 and steel 0.9 are
    neither metal nor dielectric; the registry says 1.0 for both.

Run after analysis/extract_pbr2.py, every time.
"""
import json

SPEC = 'object-sculpt-spec.json'
d = json.load(open(SPEC, encoding='utf-8'))
for m in d['materials']:
    if m['id'] == 'glassTank':
        m['type'] = 'physical'
        m['shaderModel'] = 'MeshPhysicalMaterial / PBR with transmission'
        m['roughness']['base'] = 0.10
        m['roughness']['variation'] = 0.04
        m['metalness'] = 0.0
        m.update(transmission=0.6, ior=1.6, thickness=0.5)
        print(f"  glassTank -> physical, roughness 0.10, transmission 0.6")
    if m['id'] in ('brass', 'steel'):
        was = m.get('metalness')
        m['metalness'] = 1.0
        print(f"  {m['id']:9s} -> metalness 1.0 (was {was})")
json.dump(d, open(SPEC, 'w', encoding='utf-8'), indent=1)
