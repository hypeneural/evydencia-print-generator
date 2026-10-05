import { describe, it, expect } from "vitest";
import { getOperatorCapabilities } from "./capabilities";
import type { SlotSpec } from "./types";

describe("getOperatorCapabilities", () => {
  const baseSlot: SlotSpec = {
    id: "slot_01",
    x_mm: 10,
    y_mm: 10,
    width_mm: 50,
    height_mm: 80,
    rect_px: { left: 100, top: 100, width: 500, height: 800 },
    fit: "cover",
    allow_pan: true,
    allow_zoom: true,
    allow_rotate: true,
  };

  it("returns all false for null/undefined slot", () => {
    expect(getOperatorCapabilities(null)).toEqual({
      canPan: false,
      canZoom: false,
      canRotate: false,
    });
    expect(getOperatorCapabilities(undefined)).toEqual({
      canPan: false,
      canZoom: false,
      canRotate: false,
    });
  });

  it("returns all true when all permissions are true", () => {
    expect(getOperatorCapabilities(baseSlot)).toEqual({
      canPan: true,
      canZoom: true,
      canRotate: true,
    });
  });

  it("blocks pan when allow_pan is false", () => {
    const slot = { ...baseSlot, allow_pan: false };
    expect(getOperatorCapabilities(slot)).toEqual({
      canPan: false,
      canZoom: true,
      canRotate: true,
    });
  });

  it("blocks zoom when allow_zoom is false", () => {
    const slot = { ...baseSlot, allow_zoom: false };
    expect(getOperatorCapabilities(slot)).toEqual({
      canPan: true,
      canZoom: false,
      canRotate: true,
    });
  });

  it("blocks rotate when allow_rotate is false", () => {
    const slot = { ...baseSlot, allow_rotate: false };
    expect(getOperatorCapabilities(slot)).toEqual({
      canPan: true,
      canZoom: true,
      canRotate: false,
    });
  });

  it("blocks all when all are false", () => {
    const slot = { ...baseSlot, allow_pan: false, allow_zoom: false, allow_rotate: false };
    expect(getOperatorCapabilities(slot)).toEqual({
      canPan: false,
      canZoom: false,
      canRotate: false,
    });
  });
});
