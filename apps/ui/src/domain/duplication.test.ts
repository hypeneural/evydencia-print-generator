import { describe, expect, it } from "vitest";
import { duplicateSlot } from "./duplication";
import type { SlotEditState } from "./types";

describe("duplicateSlot", () => {
  const sampleEdit: SlotEditState = {
    source_id: "asset_abc",
    pan_x_norm: 0.15,
    pan_y_norm: -0.2,
    scale: 1.35,
    rotation_deg: 90,
  };

  const chaveiroSlotIds = Array.from({ length: 18 }, (_, i) =>
    `slot_${String(i + 1).padStart(2, "0")}`
  );

  it("clones complete SlotEditState to next slot in Chaveiro", () => {
    const edits: Record<string, SlotEditState> = {
      slot_01: sampleEdit,
    };

    const res = duplicateSlot("chaveiro-3x4", chaveiroSlotIds, "slot_01", edits);
    expect(res).not.toBeNull();
    expect(res?.targetSlotId).toBe("slot_02");
    expect(res?.nextSlotEdits.slot_02).toEqual(sampleEdit);
    // Preserves original
    expect(res?.nextSlotEdits.slot_01).toEqual(sampleEdit);
  });

  it("cascades sequentially from slot_02 to slot_03 in Chaveiro", () => {
    const edits: Record<string, SlotEditState> = {
      slot_01: sampleEdit,
      slot_02: { ...sampleEdit, scale: 2.0 },
    };

    const res = duplicateSlot("chaveiro-3x4", chaveiroSlotIds, "slot_02", edits);
    expect(res).not.toBeNull();
    expect(res?.targetSlotId).toBe("slot_03");
    expect(res?.nextSlotEdits.slot_03.scale).toBe(2.0);
  });

  it("returns null when duplicating the last slot of Chaveiro", () => {
    const edits: Record<string, SlotEditState> = {
      slot_18: sampleEdit,
    };

    const res = duplicateSlot("chaveiro-3x4", chaveiroSlotIds, "slot_18", edits);
    expect(res).toBeNull();
  });

  it("clones between foto_1 and foto_2 in Globo de Neve", () => {
    const globoSlotIds = ["foto_1", "foto_2"];
    const edits: Record<string, SlotEditState> = {
      foto_1: sampleEdit,
    };

    const res1 = duplicateSlot("globo-neve", globoSlotIds, "foto_1", edits);
    expect(res1).not.toBeNull();
    expect(res1?.targetSlotId).toBe("foto_2");
    expect(res1?.nextSlotEdits.foto_2).toEqual(sampleEdit);

    const editsWithBoth: Record<string, SlotEditState> = {
      foto_1: sampleEdit,
      foto_2: { ...sampleEdit, rotation_deg: 180 },
    };
    const res2 = duplicateSlot("globo-neve", globoSlotIds, "foto_2", editsWithBoth);
    expect(res2?.targetSlotId).toBe("foto_1");
    expect(res2?.nextSlotEdits.foto_1.rotation_deg).toBe(180);
  });

  it("returns null if source slot has no photo", () => {
    const res = duplicateSlot("chaveiro-3x4", chaveiroSlotIds, "slot_05", {});
    expect(res).toBeNull();
  });

  it("returns null for single-slot Calendario", () => {
    const edits: Record<string, SlotEditState> = {
      foto_principal: sampleEdit,
    };
    const res = duplicateSlot("calendario-2027", ["foto_principal"], "foto_principal", edits);
    expect(res).toBeNull();
  });
});
