import { describe, expect, it } from "vitest";
import {
  isKeychainGroupDoubleClick,
  selectKeychainSlot,
} from "./keychain_selection";

describe("Chaveiro operator selection", () => {
  it("keeps all three selected while the first mousedown focuses any member", () => {
    const group = ["slot_01", "slot_02", "slot_03"];
    const firstDown = selectKeychainSlot(group, "slot_02");
    const secondDown = selectKeychainSlot(firstDown.selectedSlotIds, "slot_02");
    expect(firstDown).toEqual({ activeSlotId: "slot_02", selectedSlotIds: group });
    expect(secondDown.selectedSlotIds).toEqual(group);
    expect(isKeychainGroupDoubleClick("chaveiro-3x4", group, "slot_02", {
      slot_01: true, slot_02: true, slot_03: true,
    })).toBe(true);
  });

  it("click outside selected group starts one new selection", () => {
    expect(selectKeychainSlot(["slot_01", "slot_02"], "slot_05"))
      .toEqual({ activeSlotId: "slot_05", selectedSlotIds: ["slot_05"] });
  });

  it("Shift+click adds a member then Shift+click removes it", () => {
    const added = selectKeychainSlot(["slot_01"], "slot_03", true);
    expect(added).toEqual({
      activeSlotId: "slot_03",
      selectedSlotIds: ["slot_01", "slot_03"],
    });
    const removed = selectKeychainSlot(added.selectedSlotIds, "slot_03", true);
    expect(removed).toEqual({
      activeSlotId: "slot_01",
      selectedSlotIds: ["slot_01"],
    });
  });

  it("does not produce an empty selection when toggling the last member", () => {
    expect(selectKeychainSlot(["slot_01"], "slot_01", true))
      .toEqual({ activeSlotId: "slot_01", selectedSlotIds: ["slot_01"] });
  });

  it("never activates batch dblclick for non-Chaveiro or unselected/empty clicks", () => {
    const group = ["slot_01", "slot_02", "slot_03"];
    const filled = { slot_01: true, slot_02: true, slot_03: true };
    expect(isKeychainGroupDoubleClick("globo-neve", group, "slot_02", filled)).toBe(false);
    expect(isKeychainGroupDoubleClick("chaveiro-3x4", group, "slot_07", filled)).toBe(false);
    expect(isKeychainGroupDoubleClick("chaveiro-3x4", group, "slot_02", {})).toBe(false);
    expect(isKeychainGroupDoubleClick("chaveiro-3x4", ["slot_02"], "slot_02", filled))
      .toBe(false);
  });
});
