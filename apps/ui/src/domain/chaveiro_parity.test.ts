import { describe, it, expect } from "vitest";
import { Rect } from "fabric";

describe("Chaveiro 3x4 Mathematical & Scene-to-Display Parity", () => {
  const CANVAS_W_MM = 216;
  const CANVAS_H_MM = 152;
  const SLOT_W_MM = 34;
  const SLOT_H_MM = 44;
  const COLS = 6;
  const ROWS = 3;
  const MARGIN_LEFT_MM = 6;
  const MARGIN_TOP_MM = 10;
  const DPI = 300;

  it("proves grid dimensions and exact centered margins in millimeters", () => {
    const gridW_mm = COLS * SLOT_W_MM; // 204 mm
    const gridH_mm = ROWS * SLOT_H_MM; // 132 mm

    expect(gridW_mm).toBe(204);
    expect(gridH_mm).toBe(132);

    const marginLeft = (CANVAS_W_MM - gridW_mm) / 2;
    const marginRight = CANVAS_W_MM - (marginLeft + gridW_mm);
    const marginTop = (CANVAS_H_MM - gridH_mm) / 2;
    const marginBottom = CANVAS_H_MM - (marginTop + gridH_mm);

    expect(marginLeft).toBe(MARGIN_LEFT_MM);
    expect(marginRight).toBe(MARGIN_LEFT_MM);
    expect(marginTop).toBe(MARGIN_TOP_MM);
    expect(marginBottom).toBe(MARGIN_TOP_MM);
  });

  it("verifies edge-based conversion produces contiguous slots without 1px gap or overlap", () => {
    const mmToPx = (mm: number) => Math.round((mm / 25.4) * DPI);

    // Compute pixel edges for all 6 columns
    const xEdgesPx: number[] = [];
    for (let c = 0; c <= COLS; c++) {
      xEdgesPx.push(mmToPx(MARGIN_LEFT_MM + c * SLOT_W_MM));
    }

    // [71, 472, 874, 1276, 1677, 2079, 2480]
    expect(xEdgesPx).toEqual([71, 472, 874, 1276, 1677, 2079, 2480]);

    // Check each column slot width and contiguity
    for (let c = 0; c < COLS; c++) {
      const left = xEdgesPx[c];
      const right = xEdgesPx[c + 1];
      const width = right - left;

      expect(width).toBeGreaterThanOrEqual(401);
      expect(width).toBeLessThanOrEqual(402);
      // Contiguity: slot c right equals slot c+1 left
      if (c < COLS - 1) {
        expect(right).toBe(xEdgesPx[c + 1]);
      }
    }

    // Y edges
    const yEdgesPx: number[] = [];
    for (let r = 0; r <= ROWS; r++) {
      yEdgesPx.push(mmToPx(MARGIN_TOP_MM + r * SLOT_H_MM));
    }

    // [118, 638, 1157, 1677]
    expect(yEdgesPx).toEqual([118, 638, 1157, 1677]);

    for (let r = 0; r < ROWS; r++) {
      const top = yEdgesPx[r];
      const bottom = yEdgesPx[r + 1];
      const height = bottom - top;

      expect(height).toBeGreaterThanOrEqual(519);
      expect(height).toBeLessThanOrEqual(520);
      if (r < ROWS - 1) {
        expect(bottom).toBe(yEdgesPx[r + 1]);
      }
    }

    // Canvas size
    const canvasWPx = mmToPx(CANVAS_W_MM); // 2551
    const canvasHPx = mmToPx(CANVAS_H_MM); // 1795
    expect(canvasWPx).toBe(2551);
    expect(canvasHPx).toBe(1795);

    // Margins in pixels
    const marginLeftPx = xEdgesPx[0];
    const marginRightPx = canvasWPx - xEdgesPx[COLS];
    expect(marginLeftPx).toBe(71);
    expect(marginRightPx).toBe(71);

    const marginTopPx = yEdgesPx[0];
    const marginBottomPx = canvasHPx - yEdgesPx[ROWS];
    expect(marginTopPx).toBe(118);
    expect(marginBottomPx).toBe(118);
  });

  it("verifies display margin ratios match physical mm ratios", () => {
    const displayWidth = 1200;
    const displayHeight = Math.round(displayWidth * (CANVAS_H_MM / CANVAS_W_MM));

    const displayMarginLeft = (displayWidth * MARGIN_LEFT_MM) / CANVAS_W_MM;
    const displayMarginTop = (displayHeight * MARGIN_TOP_MM) / CANVAS_H_MM;

    expect(displayMarginLeft / displayWidth).toBeCloseTo(MARGIN_LEFT_MM / CANVAS_W_MM, 5);
    expect(displayMarginTop / displayHeight).toBeCloseTo(MARGIN_TOP_MM / CANVAS_H_MM, 5);
  });
});

describe("Fabric Rect & ClipPath Origin Forensics", () => {
  it("proves Rect with originX='left', originY='top' has exact top-left bounding box", () => {
    const rect = new Rect({
      left: 118,
      top: 107,
      width: 823,
      height: 395,
      originX: "left",
      originY: "top",
      strokeWidth: 0,
    });

    const bounds = rect.getBoundingRect();
    expect(bounds.left).toBeCloseTo(118, 1);
    expect(bounds.top).toBeCloseTo(107, 1);
    expect(bounds.width).toBeCloseTo(823, 1);
    expect(bounds.height).toBeCloseTo(395, 1);
  });

  it("proves Rect without explicit origin in Fabric 7 shifts by half-width/half-height", () => {
    const rectWithoutOrigin = new Rect({
      left: 118,
      top: 107,
      width: 823,
      height: 395,
      strokeWidth: 0,
    });

    // Default origin in Fabric 7 is center/center
    expect(rectWithoutOrigin.originX).toBe("center");
    expect(rectWithoutOrigin.originY).toBe("center");

    const bounds = rectWithoutOrigin.getBoundingRect();
    // Centered at (118, 107) -> left is 118 - 823/2 = -293.5
    expect(bounds.left).toBeCloseTo(118 - 823 / 2, 1);
    expect(bounds.top).toBeCloseTo(107 - 395 / 2, 1);
  });
});
