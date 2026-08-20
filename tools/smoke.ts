import { sphere, smoothUnion, capsule, ellipsoid } from '../src/sdf/ops.js';
import { surfaceNets, compact } from '../src/mesh/surfacenets.js';
import { encodeMesh } from '../src/mesh/encode.js';

const f = smoothUnion(0.05,
  ellipsoid([0, 1.0, 0], [0.12, 0.20, 0.11]),
  capsule([0, 0.2, 0], [0, 0.85, 0], 0.09, 0.13),
  sphere([0.2, 0.6, 0], 0.07),
);

for (const voxel of [0.012, 0.006, 0.003]) {
  const m = compact(surfaceNets(f, { voxel, material: (x) => (x > 0.1 ? 1 : 0) }));
  const s = m.stats;
  const skipPct = (100 * s.blocksSkipped / (s.blocksSkipped + s.blocksSampled)).toFixed(1);
  console.log(
    `voxel ${(voxel * 1000).toFixed(0)}mm  dims ${s.dims.join('x')}  grid ${(s.samples / 1e6).toFixed(2)}M  ` +
    `evaluated ${(s.evaluated / 1e6).toFixed(2)}M (${(100 * s.evaluated / s.samples).toFixed(1)}%)  ` +
    `blocks skipped ${skipPct}%  verts ${s.vertices}  tris ${s.triangles}  ${s.ms}ms`,
  );
  const enc = encodeMesh('smoke', m, ['a', 'b']);
  console.log(`   encoded ${(enc.position.length + enc.normal.length + enc.index.length) / 1024 | 0}kB  groups ${enc.groups.map((g) => g.material + ':' + g.count).join(' ')}`);
}
