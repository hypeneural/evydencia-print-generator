import { describe, expect, it } from "vitest";
import { duplicateSelectedSlots, duplicateSlot } from "./duplication";
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

describe("duplicateSelectedSlots", () => {
  const chaveiroSlotIds = Array.from({ length: 18 }, (_, i) =>
    `slot_${String(i + 1).padStart(2, "0")}`
  );

  const editA: SlotEditState = {
    source_id: "src_A",
    pan_x_norm: 0.1,
    pan_y_norm: 0.2,
    scale: 1.5,
    rotation_deg: 45,
  };

  const editB: SlotEditState = {
    source_id: "src_B",
    pan_x_norm: -0.1,
    pan_y_norm: -0.2,
    scale: 2.0,
    rotation_deg: -30,
  };

  it("duplicates 2 selected slots to contiguous empty slots", () => {
    const edits: Record<string, SlotEditState> = {
      slot_01: editA,
      slot_02: editB,
    };

    const res = duplicateSelectedSlots({
      slotIds: chaveiroSlotIds,
      selectedSlotIds: ["slot_01", "slot_02"],
      slotEdits: edits,
    });

    expect(res.changed).toBe(true);
    expect(res.duplicatedCount).toBe(2);
    expect(res.unassignedCount).toBe(0);
    expect(res.targetSlotIds).toEqual(["slot_03", "slot_04"]);
    expect(res.nextSlotEdits.slot_03).toEqual(editA);
    expect(res.nextSlotEdits.slot_04).toEqual(editB);
    expect(res.nextSlotEdits.slot_01).toEqual(editA);
    expect(res.nextSlotEdits.slot_02).toEqual(editB);
  });

  it("skips occupied slots in search queue", () => {
    const edits: Record<string, SlotEditState> = {
      slot_01: editA,
      slot_02: editB,
      slot_03: { ...editA, source_id: "src_OCCUPIED" },
    };

    const res = duplicateSelectedSlots({
      slotIds: chaveiroSlotIds,
      selectedSlotIds: ["slot_01", "slot_02"],
      slotEdits: edits,
    });

    expect(res.duplicatedCount).toBe(2);
    expect(res.targetSlotIds).toEqual(["slot_04", "slot_05"]);
    expect(res.nextSlotEdits.slot_04).toEqual(editA);
    expect(res.nextSlotEdits.slot_05).toEqual(editB);
    expect(res.nextSlotEdits.slot_03.source_id).toBe("src_OCCUPIED");
  });

  it("performs wrap-around when selected slots are near the end", () => {
    const edits: Record<string, SlotEditState> = {
      slot_17: editA,
      slot_18: editB,
    };

    const res = duplicateSelectedSlots({
      slotIds: chaveiroSlotIds,
      selectedSlotIds: ["slot_17", "slot_18"],
      slotEdits: edits,
    });

    expect(res.changed).toBe(true);
    expect(res.targetSlotIds).toEqual(["slot_01", "slot_02"]);
    expect(res.nextSlotEdits.slot_01).toEqual(editA);
    expect(res.nextSlotEdits.slot_02).toEqual(editB);
  });

  it("handles insufficient empty slots with unassignedCount", () => {
    // Only slot_18 is empty, but we selected 2 slots (slot_01 and slot_02)
    const edits: Record<string, SlotEditState> = {};
    for (let i = 1; i <= 17; i++) {
      edits[`slot_${String(i).padStart(2, "0")}`] = { ...editA, source_id: `src_${i}` };
    }

    const res = duplicateSelectedSlots({
      slotIds: chaveiroSlotIds,
      selectedSlotIds: ["slot_01", "slot_02"],
      slotEdits: edits,
    });

    expect(res.duplicatedCount).toBe(1);
    expect(res.unassignedCount).toBe(1);
    expect(res.targetSlotIds).toEqual(["slot_18"]);
    expect(res.nextSlotEdits.slot_18).toEqual(edits.slot_01);
  });

  it("returns changed=false when no filled slots selected", () => {
    const res = duplicateSelectedSlots({
      slotIds: chaveiroSlotIds,
      selectedSlotIds: ["slot_01", "slot_02"],
      slotEdits: {},
    });

    expect(res.changed).toBe(false);
    expect(res.duplicatedCount).toBe(0);
    expect(res.unassignedCount).toBe(0);
    expect(res.targetSlotIds).toEqual([]);
  });

  it("preserves immutability of inputs", () => {
    const edits: Record<string, SlotEditState> = Object.freeze({
      slot_01: Object.freeze({ ...editA }),
    });

    const res = duplicateSelectedSlots({
      slotIds: Object.freeze([...chaveiroSlotIds]),
      selectedSlotIds: Object.freeze(["slot_01"]),
      slotEdits: edits,
    });

    expect(res.changed).toBe(true);
    expect(edits.slot_02).toBeUndefined();
  });
});

