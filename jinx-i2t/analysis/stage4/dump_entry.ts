import * as THREE from 'three';
import { createJinxArcaneModel } from '../../src/createJinxModel.js';

declare global { interface Window { __DUMP__?: any; __DUMPERR__?: string; __READY2__?: boolean } }

try {
  const model = createJinxArcaneModel({});
  const parts: any[] = [];
  const meshes: any[] = [];
  model.updateMatrixWorld(true);
  model.traverse((o: any) => {
    if (!o.isMesh || !o.geometry) return;
    const g = o.geometry as THREE.BufferGeometry;
    const pos = g.getAttribute('position');
    const idx = g.getIndex();
    const tris = idx ? idx.count / 3 : (pos ? pos.count / 3 : 0);
    const b = new THREE.Box3().setFromObject(o);
    const c = b.getCenter(new THREE.Vector3());
    const mat: any = o.material;
    parts.push({
      name: o.name || '(unnamed)',
      parent: o.parent ? (o.parent.name || '(unnamed-parent)') : null,
      kind: 'part',
      module: (typeof o.userData?.sculptComponent === 'string' ? o.userData.sculptComponent : (o.userData?.sculptComponent?.id ?? null)),
      componentId: (typeof o.userData?.sculptComponent === 'string' ? o.userData.sculptComponent : (o.userData?.sculptComponent?.id ?? null)),
      sculptComponentRaw: (typeof o.userData?.sculptComponent === 'object' ? Object.keys(o.userData.sculptComponent||{}) : o.userData?.sculptComponent) ?? null,
      materialId: o.userData?.materialId ?? (mat && mat.name) ?? null,
      matColor: mat && mat.color ? '#' + mat.color.getHexString() : null,
      matMap: !!(mat && mat.map),
      matMapSrc: (mat && mat.map && (mat.map.image?.src || mat.map.name || mat.map.userData?.src)) || null,
      matName: (mat && mat.name) || null,
      matRough: mat ? mat.roughness : null,
      matMetal: mat ? mat.metalness : null,
      specMaterial: o.userData?.sculptComponent?.material ?? null,
      specMaterialRef: o.userData?.sculptComponent?.materialRef ?? null,
      triangles: tris,
      hasIndex: !!idx,
      hasNormal: !!g.getAttribute('normal'),
      hasUV: !!g.getAttribute('uv'),
      bounds: [b.min.toArray(), b.max.toArray()],
      centre: c.toArray(),
      userDataKeys: Object.keys(o.userData || {}),
    });
    // world-space vertex + index arrays, rounded
    const m = o.matrixWorld;
    const v = new THREE.Vector3();
    const verts: number[][] = [];
    for (let i = 0; i < pos.count; i++) {
      v.fromBufferAttribute(pos as any, i).applyMatrix4(m);
      verts.push([+v.x.toFixed(5), +v.y.toFixed(5), +v.z.toFixed(5)]);
    }
    let indices: number[] = [];
    if (idx) { for (let i = 0; i < idx.count; i++) indices.push(idx.getX(i)); }
    else { for (let i = 0; i < pos.count; i++) indices.push(i); }
    const nrm = g.getAttribute('normal');
    const normals: number[][] = [];
    if (nrm) {
      const nm = new THREE.Matrix3().getNormalMatrix(m);
      const n = new THREE.Vector3();
      for (let i = 0; i < nrm.count; i++) {
        n.fromBufferAttribute(nrm as any, i).applyMatrix3(nm).normalize();
        normals.push([+n.x.toFixed(4), +n.y.toFixed(4), +n.z.toFixed(4)]);
      }
    }
    meshes.push({ id: o.name || `mesh-${meshes.length}`, triangleCount: tris,
      bounds: { min: b.min.toArray(), max: b.max.toArray() },
      vertices: verts, indices, normals });
  });
  const box = new THREE.Box3().setFromObject(model);
  window.__DUMP__ = { model: 'jinx-arcane', parts, meshes,
    unnamedMeshes: parts.filter((p) => p.name === '(unnamed)').length,
    integralMeshes: parts.length,
    totalTriangles: parts.reduce((s, p) => s + p.triangles, 0),
    bbox: { min: box.min.toArray(), max: box.max.toArray() } };
  window.__READY2__ = true;
} catch (e: any) {
  window.__DUMPERR__ = String(e?.stack || e);
  window.__READY2__ = true;
}
