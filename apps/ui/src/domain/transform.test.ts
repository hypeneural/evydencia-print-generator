import { describe, it, expect } from "vitest";
import transformVectors from "../../../../tests/fixtures/transform_vectors.json";
import {
  clampTransform,
  coverScale,
  resolvePlacement,
  slotToSourceAffine,
  panBySlotDelta,
  type SlotTransform,
} from "./transform";

describe("ADR-011 TypeScript Parity with Python vectors", () => {
  for (const tc of transformVectors.placement_cases) {
    it(`Placement case: ${tc.name}`, () => {
      const [srcW, srcH] = tc.src;
      const [slotW, slotH] = tc.slot;
      const t = tc.transform as SlotTransform;
      const exp = tc.expected;

      const clamped = clampTransform(t);
      expect(clamped.pan_x_norm).toBeCloseTo(exp.clamped.pan_x_norm, 8);
      expect(clamped.pan_y_norm).toBeCloseTo(exp.clamped.pan_y_norm, 8);
      expect(clamped.scale).toBeCloseTo(exp.clamped.scale, 8);
      expect(clamped.rotation_deg).toBeCloseTo(exp.clamped.rotation_deg, 8);

      const cov = coverScale(srcW, srcH, slotW, slotH, clamped.rotation_deg);
      expect(cov).toBeCloseTo(exp.cover_scale, 8);

      const p = resolvePlacement(srcW, srcH, slotW, slotH, t);
      expect(p.effective_scale).toBeCloseTo(exp.effective_scale, 8);
      expect(p.center_x).toBeCloseTo(exp.center[0], 8);
      expect(p.center_y).toBeCloseTo(exp.center[1], 8);
      expect(p.max_dx).toBeCloseTo(exp.max_pan[0], 8);
      expect(p.max_dy).toBeCloseTo(exp.max_pan[1], 8);

      const affine = slotToSourceAffine(srcW, srcH, p);
      for (let i = 0; i < 6; i++) {
        expect(affine[i]).toBeCloseTo(exp.affine[i], 7);
      }
    });
  }

  for (const dc of transformVectors.drag_cases) {
    it(`Drag case: ${dc.name}`, () => {
      const [srcW, srcH] = dc.src;
      const [slotW, slotH] = dc.slot;
      const t = dc.transform as SlotTransform;
      const [dx, dy] = dc.delta;
      const exp = dc.expected;

      const res = panBySlotDelta(srcW, srcH, slotW, slotH, t, dx, dy);
      expect(res.pan_x_norm).toBeCloseTo(exp.pan_x_norm, 8);
      expect(res.pan_y_norm).toBeCloseTo(exp.pan_y_norm, 8);
      expect(res.scale).toBeCloseTo(exp.scale, 8);
      expect(res.rotation_deg).toBeCloseTo(exp.rotation_deg, 8);
    });
  }
});
