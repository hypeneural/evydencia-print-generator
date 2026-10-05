import { describe, expect, it } from "vitest";
import { computePreviewLayout } from "./layout";

describe("Visual Layout & Aspect Ratio Matrix (M4-A / M4-G)", () => {
  // Production geometry definitions
  const PRODUCTS = [
    {
      id: "calendario-2027",
      name: "Calendário 2027",
      productionWidth: 1067,
      productionHeight: 1474,
      expectedAspect: 1067 / 1474, // ~0.72388 (Retrato)
      isPortrait: true,
    },
    {
      id: "globo-neve",
      name: "Globo de Neve",
      productionWidth: 2551,
      productionHeight: 1205,
      expectedAspect: 2551 / 1205, // ~2.1170 (Paisagem)
      isPortrait: false,
    },
    {
      id: "chaveiro-3x4",
      name: "Chaveiro 3x4",
      productionWidth: 2551,
      productionHeight: 1795,
      expectedAspect: 2551 / 1795, // ~1.4212 (Paisagem)
      isPortrait: false,
    },
  ];

  // Target viewport matrix
  const VIEWPORTS = [
    { name: "Min Size (1024x680)", containerW: 1024 - 360, containerH: 680 - 100 },
    { name: "Default (1280x800)", containerW: 1280 - 360, containerH: 800 - 100 },
    { name: "Full HD (1920x1080)", containerW: 1920 - 360, containerH: 1080 - 100 },
  ];

  for (const product of PRODUCTS) {
    describe(`Product: ${product.name}`, () => {
      it(`enforces correct physical orientation (${product.isPortrait ? "Retrato" : "Paisagem"})`, () => {
        if (product.isPortrait) {
          expect(product.productionWidth).toBeLessThan(product.productionHeight);
          expect(product.expectedAspect).toBeLessThan(1.0);
        } else {
          expect(product.productionWidth).toBeGreaterThan(product.productionHeight);
          expect(product.expectedAspect).toBeGreaterThan(1.0);
        }
      });

      for (const vp of VIEWPORTS) {
        it(`preserves exact aspect ratio and fits container in ${vp.name}`, () => {
          const padding = 48;
          const layout = computePreviewLayout(
            product.productionWidth,
            product.productionHeight,
            vp.containerW,
            vp.containerH,
            padding
          );

          // 1. Aspect ratio invariant: displayWidth / displayHeight == productionWidth / productionHeight
          // (Within 2 decimal places due to integer pixel rounding on compact viewports)
          const displayAspect = layout.displayWidth / layout.displayHeight;
          expect(displayAspect).toBeCloseTo(product.expectedAspect, 2);

          // 2. Bounds invariant: displayWidth and displayHeight must not overflow available area
          const availableW = vp.containerW - padding * 2;
          const availableH = vp.containerH - padding * 2;
          expect(layout.displayWidth).toBeLessThanOrEqual(availableW + 1);
          expect(layout.displayHeight).toBeLessThanOrEqual(availableH + 1);

          // 3. Positive dimensions invariant
          expect(layout.displayWidth).toBeGreaterThan(0);
          expect(layout.displayHeight).toBeGreaterThan(0);
          expect(layout.fitScale).toBeGreaterThan(0);
          expect(layout.fitScale).toBeLessThanOrEqual(1.0);
        });
      }
    });
  }

  it("handles zero or degenerate container dimensions gracefully with minimum 1px bounds", () => {
    const layout = computePreviewLayout(2551, 1205, 0, 0, 48);
    expect(layout.displayWidth).toBeGreaterThan(0);
    expect(layout.displayHeight).toBeGreaterThan(0);
    expect(layout.fitScale).toBeGreaterThan(0);
  });
});
