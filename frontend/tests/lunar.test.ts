import { describe, expect, it } from "vitest";
import {
  arc,
  focusCamera,
  INITIAL_CAMERA,
  position,
  project,
  rotate,
  visibleArc,
} from "../src/pages/lunarGeometry";

describe("particle globe camera and real dependency paths", () => {
  it("focuses every selectable skill on the front without a full extra spin", () => {
    const camera = { ...INITIAL_CAMERA, yaw: 19.3 };
    for (let i = 0; i < 39; i++) {
      const point = position(i, 39),
        target = focusCamera(point, camera),
        focused = project(point, target);
      expect(Math.abs(target.yaw - camera.yaw)).toBeLessThanOrEqual(Math.PI);
      expect(focused.x).toBeCloseTo(300);
      expect(focused.y).toBeCloseTo(250);
      expect(focused.z).toBeCloseTo(1);
    }
  });
  it("keeps dependency arcs on the surface and hides their far side", () => {
    const start = position(1, 9),
      end = position(3, 9),
      points = arc(start, end);
    expect(points[0]).toEqual(start);
    expect(points.at(-1)!.x).toBeCloseTo(end.x);
    points.forEach((point) =>
      expect(Math.hypot(point.x, point.y, point.z)).toBeCloseTo(1),
    );
    const camera = focusCamera(start, INITIAL_CAMERA),
      path = visibleArc(points, camera);
    expect(path).toContain("M");
    expect(path).not.toContain("NaN");
    const reversed = {
      ...camera,
      yaw: camera.yaw + Math.PI,
      pitch: -camera.pitch,
    };
    expect(rotate(start, reversed).z).toBeLessThan(0);
  });
});
