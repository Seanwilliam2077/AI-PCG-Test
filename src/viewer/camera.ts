/**
 * Deterministic framing.
 *
 * Everything the review loop measures depends on two renders of the same figure
 * being comparable pixel for pixel, so the camera is *derived*, never nudged:
 *
 *   - It is **orthographic**.  A perspective camera changes the foreshortening
 *     of the legs as the yaw changes, which makes a turnaround impossible to
 *     read panel to panel and poisons any silhouette IoU.
 *   - It sits on a circle about the Y axis through the model's bounding-box
 *     centre, looking at that centre.  Yaw 0 puts it on +Z, which the part
 *     contract defines as the character's front.
 *   - The vertical frustum is exactly `bbox height * FRAME_PAD`.  Because the
 *     box is measured from whatever was actually baked, a body-only bake and a
 *     fully dressed one both fill the same fraction of the frame, and the
 *     figure never drifts when a part lands.
 *
 * The horizontal frustum follows from the viewport aspect, so an image is only
 * ever cropped or letterboxed horizontally -- vertical scale is invariant.
 */
import { Box3, MathUtils, Object3D, OrthographicCamera, Vector3 } from 'three';

/** Headroom above and below the figure, as a multiple of its height. */
export const FRAME_PAD = 1.06;

/** The six turnaround yaws the viewport buttons offer, in degrees. */
export const CANONICAL_YAWS = [0, 45, 90, 135, 180, 270] as const;

/**
 * The superset `tools/render.mjs` shoots by default.  The reference sheet's
 * per-panel yaw is fitted by `tools/compare.py`, so render every 45 degrees and
 * let the fit choose.
 */
export const RENDER_YAWS = [0, 45, 90, 135, 180, 225, 270, 315] as const;

export interface Framing {
  /** World-space centre of the model's bounding box; the camera always aims here. */
  center: Vector3;
  size: Vector3;
  /** Bounding-box height in metres, before `FRAME_PAD`. */
  height: number;
  /** Bounding-sphere radius, used only to park the camera outside the model. */
  radius: number;
}

/** Measure the world bounding box of whatever has been loaded. */
export function computeFraming(target: Object3D): Framing {
  const box = new Box3().setFromObject(target);
  if (box.isEmpty()) {
    // Nothing baked yet: fall back to a nominal 1.72 m figure so the viewer
    // still shows a sane frame instead of a NaN projection matrix.
    box.setFromCenterAndSize(new Vector3(0, 0.86, 0), new Vector3(0.7, 1.72, 0.5));
  }
  const center = box.getCenter(new Vector3());
  const size = box.getSize(new Vector3());
  return {
    center,
    size,
    height: Math.max(size.y, 1e-3),
    radius: Math.max(size.length() * 0.5, 1e-3),
  };
}

/** Unit vector from the model centre to the camera for a given yaw. Yaw 0 = +Z. */
export function yawDirection(yawDeg: number): Vector3 {
  const y = MathUtils.degToRad(yawDeg);
  return new Vector3(Math.sin(y), 0, Math.cos(y));
}

/** Vertical extent of the orthographic frustum, in metres. */
export function frustumHeight(f: Framing): number {
  return f.height * FRAME_PAD;
}

/**
 * Re-derive the frustum for a viewport aspect (width / height).  Called on every
 * resize; leaves position, target and `zoom` alone so user orbiting survives.
 */
export function applyAspect(cam: OrthographicCamera, f: Framing, aspect: number): void {
  const h = frustumHeight(f);
  const w = h * (Number.isFinite(aspect) && aspect > 0 ? aspect : 1);
  cam.top = h * 0.5;
  cam.bottom = -h * 0.5;
  cam.left = -w * 0.5;
  cam.right = w * 0.5;
  cam.updateProjectionMatrix();
}

/**
 * Place the camera for a canonical view and reset the frustum. Returns the point
 * it looks at, which is also what OrbitControls should use as its target.
 */
export function applyCanonicalView(
  cam: OrthographicCamera,
  f: Framing,
  yawDeg: number,
  aspect: number,
): Vector3 {
  // Orthographic: distance does not affect scale, it only has to clear the model.
  const dist = f.radius * 3 + 1;
  cam.position.copy(f.center).addScaledVector(yawDirection(yawDeg), dist);
  cam.up.set(0, 1, 0);
  cam.lookAt(f.center);
  cam.zoom = 1;
  cam.near = 0.01;
  cam.far = dist + f.radius * 2 + 1;
  applyAspect(cam, f, aspect);
  cam.updateMatrixWorld();
  return f.center.clone();
}

/** Current yaw of a camera about the framing centre, in degrees, 0..360. */
export function yawOf(cam: OrthographicCamera, f: Framing): number {
  const d = cam.position.clone().sub(f.center);
  const deg = MathUtils.radToDeg(Math.atan2(d.x, d.z));
  return ((deg % 360) + 360) % 360;
}
