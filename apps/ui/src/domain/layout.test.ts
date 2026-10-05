import { describe, it, expect } from "vitest";
import { computePreviewLayout } from "./layout";

describe("computePreviewLayout", () => {
  it("throws error if production dimensions are non-positive", () => {
    expect(() => computePreviewLayout(0, 100, 800, 600)).toThrow();
    expect(() => computePreviewLayout(100, -5, 800, 600)).toThrow();
  });

  it("preserves aspect ratio for Calendário (1067x1474 portrait, aspect ~0.72388)", () => {
    const prodW = 1067;
    const prodH = 1474;
    const prodAspect = prodW / prodH;

    const layout = computePreviewLayout(prodW, prodH, 1280, 800, 48);
    const displayAspect = layout.displayWidth / layout.displayHeight;

    expect(Math.abs(displayAspect - prodAspect)).toBeLessThan(0.005);
    expect(layout.displayWidth).toBeLessThanOrEqual(1280 - 96);
    expect(layout.displayHeight).toBeLessThanOrEqual(800 - 96);
    expect(layout.fitScale).toBeLessThanOrEqual(1.0);
  });

  it("preserves aspect ratio for Globo de Neve (1795x1205 landscape, aspect ~1.4896)", () => {
    const prodW = 1795;
    const prodH = 1205;
    const prodAspect = prodW / prodH;

    const layout = computePreviewLayout(prodW, prodH, 1280, 800, 48);
    const displayAspect = layout.displayWidth / layout.displayHeight;

    expect(Math.abs(displayAspect - prodAspect)).toBeLessThan(0.005);
    expect(layout.displayWidth).toBeLessThanOrEqual(1280 - 96);
    expect(layout.displayHeight).toBeLessThanOrEqual(800 - 96);
  });

  it("preserves aspect ratio for Chaveiro 3x4 (2551x1795 landscape, aspect ~1.4211)", () => {
    const prodW = 2551;
    const prodH = 1795;
    const prodAspect = prodW / prodH;

    const layout = computePreviewLayout(prodW, prodH, 1024, 680, 48);
    const displayAspect = layout.displayWidth / layout.displayHeight;

    expect(Math.abs(displayAspect - prodAspect)).toBeLessThan(0.005);
    expect(layout.displayWidth).toBeLessThanOrEqual(1024 - 96);
    expect(layout.displayHeight).toBeLessThanOrEqual(680 - 96);
  });

  it("does not upscale beyond 1.0 when container is huge", () => {
    const prodW = 500;
    const prodH = 500;
    const layout = computePreviewLayout(prodW, prodH, 3000, 2000, 48);

    expect(layout.fitScale).toBe(1.0);
    expect(layout.displayWidth).toBe(500);
    expect(layout.displayHeight).toBe(500);
  });
});
