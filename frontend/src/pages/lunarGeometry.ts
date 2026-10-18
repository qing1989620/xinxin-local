export type Point3 = { x: number; y: number; z: number };
export type Camera = { yaw: number; pitch: number; zoom: number };
export const INITIAL_CAMERA: Camera = { yaw: 0.42, pitch: -0.12, zoom: 1 };
export const clamp = (value: number, low: number, high: number) =>
  Math.max(low, Math.min(high, value));
export function position(index: number, count: number): Point3 {
  const y = 1 - (2 * (index + 0.5)) / count;
  const radius = Math.sqrt(Math.max(0, 1 - y * y));
  const theta = index * Math.PI * (3 - Math.sqrt(5));
  return { x: Math.cos(theta) * radius, y, z: Math.sin(theta) * radius };
}
export function rotate(point: Point3, camera: Camera): Point3 {
  const x = point.x * Math.cos(camera.yaw) + point.z * Math.sin(camera.yaw);
  const z = point.z * Math.cos(camera.yaw) - point.x * Math.sin(camera.yaw);
  return {
    x,
    y: point.y * Math.cos(camera.pitch) - z * Math.sin(camera.pitch),
    z: point.y * Math.sin(camera.pitch) + z * Math.cos(camera.pitch),
  };
}
export function project(point: Point3, camera: Camera) {
  const p = rotate(point, camera);
  return {
    x: 300 + p.x * 170 * camera.zoom,
    y: 250 + p.y * 170 * camera.zoom,
    z: p.z,
  };
}
export function focusCamera(point: Point3, current: Camera): Camera {
  const targetYaw = Math.atan2(-point.x, point.z);
  const shortestTurn = Math.atan2(
    Math.sin(targetYaw - current.yaw),
    Math.cos(targetYaw - current.yaw),
  );
  return {
    yaw: current.yaw + shortestTurn,
    pitch: Math.atan2(point.y, Math.hypot(point.x, point.z)),
    zoom: current.zoom,
  };
}
export function arc(a: Point3, b: Point3, steps = 40): Point3[] {
  const theta = Math.acos(clamp(a.x * b.x + a.y * b.y + a.z * b.z, -1, 1));
  const sine = Math.sin(theta);
  return Array.from({ length: steps + 1 }, (_, i) => {
    if (Math.abs(sine) < 1e-6) return a;
    const t = i / steps,
      left = Math.sin((1 - t) * theta) / sine,
      right = Math.sin(t * theta) / sine;
    return {
      x: a.x * left + b.x * right,
      y: a.y * left + b.y * right,
      z: a.z * left + b.z * right,
    };
  });
}
export function visibleArc(points: Point3[], camera: Camera): string {
  let drawing = false;
  return points
    .map((point) => {
      const p = project(point, camera);
      if (p.z < 0.02) {
        drawing = false;
        return "";
      }
      const command = drawing ? "L" : "M";
      drawing = true;
      return `${command}${p.x.toFixed(2)},${p.y.toFixed(2)}`;
    })
    .join(" ");
}
