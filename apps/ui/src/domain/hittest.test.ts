import { describe, it, expect } from "vitest";
import {
  pointToScene,
  findSlotAtScenePoint,
  findSlotAtClientPoint,
} from "./hittest";
import type { PixelRect } from "./types";

describe("hittest domain", () => {
  describe("pointToScene", () => {
    it("converts client coordinates to scene space correctly", () => {
      const canvasRect = { left: 100, top: 50 };
      const fitScale = 0.5;
      const res = pointToScene(200, 150, canvasRect, fitScale);
      // (200 - 100) / 0.5 = 200
      // (150 - 50) / 0.5 = 200
      expect(res.x).toBe(200);
      expect(res.y).toBe(200);
    });

    it("throws if fitScale is not positive", () => {
      expect(() => pointToScene(100, 100, { left: 0, top: 0 }, 0)).toThrow();
      expect(() => pointToScene(100, 100, { left: 0, top: 0 }, -1)).toThrow();
    });
  });

  describe("findSlotAtScenePoint", () => {
    const slots = [
      {
        id: "slot_1",
        rect_px: { left: 100, top: 100, width: 200, height: 300 } as PixelRect,
      },
      {
        id: "slot_2",
        rect_px: { left: 350, top: 100, width: 200, height: 300 } as PixelRect,
      },
    ];

    it("identifies target slot when point is inside", () => {
      const hit = findSlotAtScenePoint(slots, 150, 150);
      expect(hit?.id).toBe("slot_1");

      const hit2 = findSlotAtScenePoint(slots, 400, 200);
      expect(hit2?.id).toBe("slot_2");
    });

    it("returns null when point is in gap between slots", () => {
      const hit = findSlotAtScenePoint(slots, 320, 150);
      expect(hit).toBeNull();
    });

    it("handles boundary edges inclusively", () => {
      expect(findSlotAtScenePoint(slots, 100, 100)?.id).toBe("slot_1");
      expect(findSlotAtScenePoint(slots, 300, 400)?.id).toBe("slot_1");
    });
  });

  describe("findSlotAtClientPoint", () => {
    const slots = [
      {
        id: "foto_principal",
        rect_px: { left: 118, top: 107, width: 823, height: 395 } as PixelRect,
      },
    ];
    // Suppose canvas display is at { left: 50, top: 50, width: 533.5, height: 737 }
    // fitScale = 0.5
    const canvasRect = { left: 50, top: 50, width: 534, height: 737 };
    const fitScale = 0.5;

    it("detects slot from client coordinates", () => {
      // Scene point inside slot: left 118 + 100 = 218, top 107 + 100 = 207
      // Client point = 50 + 218 * 0.5 = 159, top = 50 + 207 * 0.5 = 153.5
      const hit = findSlotAtClientPoint(slots, 159, 154, canvasRect, fitScale);
      expect(hit?.id).toBe("foto_principal");
    });

    it("returns null if client point is outside canvas rect", () => {
      const hit = findSlotAtClientPoint(slots, 10, 10, canvasRect, fitScale);
      expect(hit).toBeNull();
    });

    it("returns null if client point is inside canvas but outside slot", () => {
      // Top left of canvas is at scene (0, 0), which is outside the slot (118, 107)
      const hit = findSlotAtClientPoint(slots, 55, 55, canvasRect, fitScale);
      expect(hit).toBeNull();
    });
  });

  describe("Globo de Neve 216x102 2-slot hit-test", () => {
    const globoSlots = [
      {
        id: "foto_1",
        rect_px: { left: 644, top: 130, width: 591, height: 945 } as PixelRect,
      },
      {
        id: "foto_2",
        rect_px: { left: 1317, top: 130, width: 591, height: 945 } as PixelRect,
      },
    ];

    it("correctly differentiates between foto_1, gap, and foto_2", () => {
      // Inside foto_1
      expect(findSlotAtScenePoint(globoSlots, 700, 500)?.id).toBe("foto_1");
      // In the 7mm gap (~82px) between 644+591=1235 and 1317
      expect(findSlotAtScenePoint(globoSlots, 1270, 500)).toBeNull();
      // Inside foto_2
      expect(findSlotAtScenePoint(globoSlots, 1400, 500)?.id).toBe("foto_2");
      // In lateral margin
      expect(findSlotAtScenePoint(globoSlots, 100, 500)).toBeNull();
    });
  });
});
