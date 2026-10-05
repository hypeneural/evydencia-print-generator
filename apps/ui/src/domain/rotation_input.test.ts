import { describe, it, expect } from "vitest";
import {
  normalizeRotationInput,
  parseRotationText,
  ROTATION_MIN,
  ROTATION_MAX_NUMERIC,
} from "./rotation_input";

describe("rotation_input domain", () => {
  it("normalizes finite values within range", () => {
    expect(normalizeRotationInput(0)).toBe(0);
    expect(normalizeRotationInput(45.54)).toBe(45.5);
    expect(normalizeRotationInput(-90)).toBe(-90);
  });

  it("clamps values >= 180 to 179.9 to prevent wrapping to -180", () => {
    expect(normalizeRotationInput(180)).toBe(ROTATION_MAX_NUMERIC);
    expect(normalizeRotationInput(180.5)).toBe(ROTATION_MAX_NUMERIC);
  });

  it("clamps values < -180 to -180", () => {
    expect(normalizeRotationInput(-180.1)).toBe(ROTATION_MIN);
    expect(normalizeRotationInput(-200)).toBe(ROTATION_MIN);
  });

  it("parses valid rotation text", () => {
    expect(parseRotationText("45", 0)).toBe(45);
    expect(parseRotationText("-12.5", 0)).toBe(-12.5);
    expect(parseRotationText("  90.2  ", 0)).toBe(90.2);
  });

  it("returns fallback on empty or invalid text", () => {
    expect(parseRotationText("", 15)).toBe(15);
    expect(parseRotationText("   ", 15)).toBe(15);
    expect(parseRotationText("-", 15)).toBe(15);
    expect(parseRotationText("abc", 15)).toBe(15);
  });

  it("clamps 180 in text input to 179.9", () => {
    expect(parseRotationText("180", 0)).toBe(179.9);
  });
});
