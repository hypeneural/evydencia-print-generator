import { describe, it, expect } from "vitest";
import {
  assignSourcesToSlots,
  countEmptySlots,
  fillEmptySlots,
  removeSlotPhoto,
  INITIAL_SLOT_TRANSFORM,
} from "./slot_assignment";
import type { SlotEditState } from "./types";

const CHAVEIRO_SLOT_IDS = Array.from({ length: 18 }, (_, i) =>
  `slot_${String(i + 1).padStart(2, "0")}`
);
const GLOBO_SLOT_IDS = ["foto_1", "foto_2"];

function makeEdit(sourceId: string, overrides?: Partial<SlotEditState>): SlotEditState {
  return {
    source_id: sourceId,
    pan_x_norm: 0.1,
    pan_y_norm: -0.1,
    scale: 1.25,
    rotation_deg: 90,
    ...overrides,
  };
}

describe("slot_assignment domain", () => {
  it("1. Chaveiro vazio + 4 -> slots 1..4", () => {
    const res = assignSourcesToSlots({
      slotIds: CHAVEIRO_SLOT_IDS,
      slotEdits: {},
      sourceIds: ["src_a", "src_b", "src_c", "src_d"],
    });

    expect(res.changed).toBe(true);
    expect(res.assignments).toEqual([
      { slotId: "slot_01", sourceId: "src_a" },
      { slotId: "slot_02", sourceId: "src_b" },
      { slotId: "slot_03", sourceId: "src_c" },
      { slotId: "slot_04", sourceId: "src_d" },
    ]);
    expect(res.unassignedSourceIds).toEqual([]);
    expect(res.firstAssignedSlotId).toBe("slot_01");

    expect(res.nextSlotEdits["slot_01"]).toEqual({
      source_id: "src_a",
      ...INITIAL_SLOT_TRANSFORM,
    });
    expect(res.nextSlotEdits["slot_04"]).toEqual({
      source_id: "src_d",
      ...INITIAL_SLOT_TRANSFORM,
    });
    expect(res.nextSlotEdits["slot_05"]).toBeUndefined();
  });

  it("2. Chaveiro vazio + 20 -> 18 assigned, 2 unassigned (ordem preservada)", () => {
    const twentySources = Array.from({ length: 20 }, (_, i) => `src_${i + 1}`);
    const res = assignSourcesToSlots({
      slotIds: CHAVEIRO_SLOT_IDS,
      slotEdits: {},
      sourceIds: twentySources,
    });

    expect(res.changed).toBe(true);
    expect(res.assignments.length).toBe(18);
    expect(res.assignments[0]).toEqual({ slotId: "slot_01", sourceId: "src_1" });
    expect(res.assignments[17]).toEqual({ slotId: "slot_18", sourceId: "src_18" });
    expect(res.unassignedSourceIds).toEqual(["src_19", "src_20"]);
  });

  it("3. Chaveiro 15 ocupados + 4 -> 3 assigned, 1 unassigned", () => {
    // 15 occupied (slots 1..15), 3 empty (slots 16, 17, 18)
    const slotEdits: Record<string, SlotEditState> = {};
    for (let i = 0; i < 15; i++) {
      slotEdits[CHAVEIRO_SLOT_IDS[i]] = makeEdit(`existing_${i + 1}`);
    }

    const res = assignSourcesToSlots({
      slotIds: CHAVEIRO_SLOT_IDS,
      slotEdits,
      sourceIds: ["new_1", "new_2", "new_3", "new_4"],
    });

    expect(res.changed).toBe(true);
    expect(res.assignments).toEqual([
      { slotId: "slot_16", sourceId: "new_1" },
      { slotId: "slot_17", sourceId: "new_2" },
      { slotId: "slot_18", sourceId: "new_3" },
    ]);
    expect(res.unassignedSourceIds).toEqual(["new_4"]);
    expect(res.firstAssignedSlotId).toBe("slot_16");
  });

  it("4. Os 15 ocupados permanecem deep-equal e com valores intactos", () => {
    const slotEdits: Record<string, SlotEditState> = {};
    for (let i = 0; i < 15; i++) {
      slotEdits[CHAVEIRO_SLOT_IDS[i]] = makeEdit(`existing_${i + 1}`);
    }

    const res = assignSourcesToSlots({
      slotIds: CHAVEIRO_SLOT_IDS,
      slotEdits,
      sourceIds: ["new_1"],
    });

    for (let i = 0; i < 15; i++) {
      const id = CHAVEIRO_SLOT_IDS[i];
      expect(res.nextSlotEdits[id]).toEqual(slotEdits[id]);
    }
  });

  it("5. Globo vazio + 2 -> foto_1, foto_2", () => {
    const res = assignSourcesToSlots({
      slotIds: GLOBO_SLOT_IDS,
      slotEdits: {},
      sourceIds: ["globo_a", "globo_b"],
    });

    expect(res.changed).toBe(true);
    expect(res.assignments).toEqual([
      { slotId: "foto_1", sourceId: "globo_a" },
      { slotId: "foto_2", sourceId: "globo_b" },
    ]);
    expect(res.unassignedSourceIds).toEqual([]);
    expect(res.firstAssignedSlotId).toBe("foto_1");
  });

  it("6. Globo vazio + 4 -> só 2 assigned, 2 unassigned no tray", () => {
    const res = assignSourcesToSlots({
      slotIds: GLOBO_SLOT_IDS,
      slotEdits: {},
      sourceIds: ["g1", "g2", "g3", "g4"],
    });

    expect(res.changed).toBe(true);
    expect(res.assignments).toEqual([
      { slotId: "foto_1", sourceId: "g1" },
      { slotId: "foto_2", sourceId: "g2" },
    ]);
    expect(res.unassignedSourceIds).toEqual(["g3", "g4"]);
  });

  it("7. Globo foto_1 ocupada + A -> foto_2", () => {
    const slotEdits = {
      foto_1: makeEdit("existing_globo_1"),
    };
    const res = assignSourcesToSlots({
      slotIds: GLOBO_SLOT_IDS,
      slotEdits,
      sourceIds: ["new_a"],
    });

    expect(res.changed).toBe(true);
    expect(res.assignments).toEqual([{ slotId: "foto_2", sourceId: "new_a" }]);
    expect(res.nextSlotEdits.foto_1).toEqual(slotEdits.foto_1);
    expect(res.nextSlotEdits.foto_2.source_id).toBe("new_a");
  });

  it("8. Anchor ocupado é substituído quando target explícito", () => {
    const slotEdits: Record<string, SlotEditState> = {
      slot_10: makeEdit("old_photo_at_10"),
    };

    const res = assignSourcesToSlots({
      slotIds: CHAVEIRO_SLOT_IDS,
      slotEdits,
      sourceIds: ["replacement_a"],
      anchorSlotId: "slot_10",
    });

    expect(res.changed).toBe(true);
    expect(res.assignments).toEqual([{ slotId: "slot_10", sourceId: "replacement_a" }]);
    expect(res.nextSlotEdits["slot_10"].source_id).toBe("replacement_a");
  });

  it("9. Com anchor, outros ocupados não são substituídos e wrap-around busca vazios do início", () => {
    // slot_16 ocupado, slot_17 vazio, slot_18 ocupado, slot_01 vazio
    const slotEdits: Record<string, SlotEditState> = {
      slot_16: makeEdit("at_16"),
      slot_18: makeEdit("at_18"),
    };

    const res = assignSourcesToSlots({
      slotIds: CHAVEIRO_SLOT_IDS,
      slotEdits,
      sourceIds: ["drop_on_16", "seek_next_1", "seek_next_2"],
      anchorSlotId: "slot_16",
    });

    expect(res.changed).toBe(true);
    // drop_on_16 replaces anchor slot_16
    // seek_next_1 finds slot_17 (next empty)
    // slot_18 is occupied -> skipped
    // wraps around: seek_next_2 finds slot_01 (empty)
    expect(res.assignments).toEqual([
      { slotId: "slot_16", sourceId: "drop_on_16" },
      { slotId: "slot_17", sourceId: "seek_next_1" },
      { slotId: "slot_01", sourceId: "seek_next_2" },
    ]);
    expect(res.nextSlotEdits["slot_18"]).toEqual(slotEdits["slot_18"]); // slot_18 untouched
  });

  it("10. Ordem de sourceIds preservada nas assignments", () => {
    const res = assignSourcesToSlots({
      slotIds: CHAVEIRO_SLOT_IDS,
      slotEdits: {},
      sourceIds: ["z_first", "m_second", "a_third"],
    });

    expect(res.assignments.map((a) => a.sourceId)).toEqual(["z_first", "m_second", "a_third"]);
  });

  it("11. Batch vazio -> changed: false, no-op", () => {
    const slotEdits = { slot_01: makeEdit("x") };
    const res = assignSourcesToSlots({
      slotIds: CHAVEIRO_SLOT_IDS,
      slotEdits,
      sourceIds: [],
    });

    expect(res.changed).toBe(false);
    expect(res.assignments).toEqual([]);
    expect(res.unassignedSourceIds).toEqual([]);
    expect(res.firstAssignedSlotId).toBeNull();
    expect(res.nextSlotEdits).toBe(slotEdits);
  });

  it("12. fillEmptySlots copia somente vazios", () => {
    const slotEdits: Record<string, SlotEditState> = {
      slot_01: makeEdit("photo_orig"),
      slot_02: makeEdit("photo_other"),
    };

    const res = fillEmptySlots({
      slotIds: ["slot_01", "slot_02", "slot_03"],
      slotEdits,
      baseSlotId: "slot_01",
    });

    expect(res).not.toBeNull();
    expect(res!.filledSlotIds).toEqual(["slot_03"]);
    expect(res!.nextSlotEdits["slot_01"]).toEqual(slotEdits["slot_01"]);
    expect(res!.nextSlotEdits["slot_02"]).toEqual(slotEdits["slot_02"]);
    expect(res!.nextSlotEdits["slot_03"]).toEqual(slotEdits["slot_01"]);
  });

  it("13. fillEmptySlots copia transform completo", () => {
    const customTransform = makeEdit("photo_orig", {
      pan_x_norm: 0.35,
      pan_y_norm: -0.22,
      scale: 2.1,
      rotation_deg: 270,
    });
    const slotEdits = { slot_01: customTransform };

    const res = fillEmptySlots({
      slotIds: ["slot_01", "slot_02"],
      slotEdits,
      baseSlotId: "slot_01",
    });

    expect(res).not.toBeNull();
    expect(res!.nextSlotEdits["slot_02"]).toEqual(customTransform);
  });

  it("14. fillEmptySlots com slot base vazio -> null (no-op)", () => {
    const slotEdits = {};
    const res = fillEmptySlots({
      slotIds: ["slot_01", "slot_02"],
      slotEdits,
      baseSlotId: "slot_01",
    });
    expect(res).toBeNull();
  });

  it("15. fillEmptySlots com zero vazios -> null (no-op)", () => {
    const slotEdits = {
      slot_01: makeEdit("a"),
      slot_02: makeEdit("b"),
    };
    const res = fillEmptySlots({
      slotIds: ["slot_01", "slot_02"],
      slotEdits,
      baseSlotId: "slot_01",
    });
    expect(res).toBeNull();
  });

  it("16. Inputs não sofrem mutação (Object.freeze + deep compare)", () => {
    const slotEdits = Object.freeze({
      slot_01: Object.freeze(makeEdit("a")),
    });
    const sourceIds = Object.freeze(["b", "c"]);
    const slotIds = Object.freeze(["slot_01", "slot_02", "slot_03"]);

    expect(() => {
      assignSourcesToSlots({
        slotIds,
        slotEdits,
        sourceIds,
      });
    }).not.toThrow();

    expect(slotEdits.slot_01.source_id).toBe("a");
  });

  it("17. Extras: deduplicação de sourceIds, countEmptySlots, removeSlotPhoto", () => {
    // Deduplication of duplicate source IDs in batch
    const res = assignSourcesToSlots({
      slotIds: ["slot_01", "slot_02", "slot_03"],
      slotEdits: {},
      sourceIds: ["dup", "dup", "other"],
    });
    expect(res.assignments).toEqual([
      { slotId: "slot_01", sourceId: "dup" },
      { slotId: "slot_02", sourceId: "other" },
    ]);

    // countEmptySlots
    const emptyCount = countEmptySlots(["slot_01", "slot_02", "slot_03"], {
      slot_01: makeEdit("x"),
    });
    expect(emptyCount).toBe(2);

    // removeSlotPhoto
    const removed = removeSlotPhoto({ slot_01: makeEdit("x"), slot_02: makeEdit("y") }, "slot_01");
    expect(removed).toEqual({ slot_02: makeEdit("y") });

    // removeSlotPhoto on empty or null
    expect(removeSlotPhoto({}, "slot_01")).toBeNull();
    expect(removeSlotPhoto({ slot_01: makeEdit("x") }, null)).toBeNull();
  });
});
