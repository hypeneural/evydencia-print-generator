import { describe, expect, it } from "vitest";
import type { TemplateDraft } from "./draft";
import {
  cleanDraftForPublish,
  computeNextVersion,
  suggestBumpType,
} from "./publish";
import type { TemplateModel } from "./types";

describe("publish domain", () => {
  it("computes next semver versions correctly", () => {
    expect(computeNextVersion("1.0.0", "patch")).toBe("1.0.1");
    expect(computeNextVersion("1.0.0", "minor")).toBe("1.1.0");
    expect(computeNextVersion("1.0.0", "major")).toBe("2.0.0");
    expect(computeNextVersion("1.2.9", "patch")).toBe("1.2.10");
    expect(computeNextVersion("1.2.9", "minor")).toBe("1.3.0");
    expect(computeNextVersion("1.2.9", "major")).toBe("2.0.0");
    expect(computeNextVersion("invalid", "minor")).toBe("1.1.0");
  });

  const baseTemplate: TemplateModel = {
    id: "sample-tpl",
    template_version: "1.0.0",
    name: "Sample Template",
    status: "production",
    canvas: { width_mm: 100, height_mm: 150, dpi: 300 },
    canvas_px: { width: 1181, height: 1772 },
    slots: [
      {
        id: "s1",
        x_mm: 10,
        y_mm: 10,
        width_mm: 80,
        height_mm: 130,
        rect_px: { left: 118, top: 118, width: 945, height: 1535 },
        fit: "cover",
        allow_pan: true,
        allow_zoom: true,
        allow_rotate: false,
      },
    ],
    overlay: null,
  };

  const baseDraft: TemplateDraft = {
    id: "sample-tpl",
    template_version: "1.0.0",
    name: "Sample Template",
    status: "production",
    canvas: { width_mm: 100, height_mm: 150, dpi: 300 },
    canvas_px: { width: 1181, height: 1772 },
    slots: [
      {
        id: "s1",
        x_mm: 15, // moved slightly
        y_mm: 10,
        width_mm: 80,
        height_mm: 130,
        rect_px: { left: 177, top: 118, width: 945, height: 1535 },
        fit: "cover",
        allow_pan: true,
        allow_zoom: true,
        allow_rotate: false,
      },
    ],
    overlay: null,
    dirty: true,
  };

  it("suggests patch for positional tweaks without slot structure change", () => {
    expect(suggestBumpType(baseTemplate, baseDraft)).toBe("patch");
  });

  it("suggests minor when slots are added or removed", () => {
    const draftWithExtraSlot: TemplateDraft = {
      ...baseDraft,
      slots: [
        ...baseDraft.slots,
        {
          id: "s2",
          x_mm: 20,
          y_mm: 20,
          width_mm: 40,
          height_mm: 40,
          rect_px: { left: 236, top: 236, width: 472, height: 472 },
          fit: "cover",
          allow_pan: true,
          allow_zoom: true,
          allow_rotate: false,
        },
      ],
    };
    expect(suggestBumpType(baseTemplate, draftWithExtraSlot)).toBe("minor");
  });

  it("suggests minor when canvas dimensions change", () => {
    const draftCanvasChanged: TemplateDraft = {
      ...baseDraft,
      canvas: { ...baseDraft.canvas, width_mm: 120 },
    };
    expect(suggestBumpType(baseTemplate, draftCanvasChanged)).toBe("minor");
  });

  it("cleans draft removing UI-only fields", () => {
    const payload = cleanDraftForPublish(baseDraft);
    expect(payload.id).toBe("sample-tpl");
    expect(payload).not.toHaveProperty("canvas_px");
    expect(payload).not.toHaveProperty("dirty");

    const slots = payload.slots as Array<Record<string, unknown>>;
    expect(slots[0]).not.toHaveProperty("rect_px");
    expect(slots[0].x_mm).toBe(15);
    expect(slots[0].id).toBe("s1");
  });
});
