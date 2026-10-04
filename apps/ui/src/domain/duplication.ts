import type { SlotEditState } from "./types";

export interface DuplicationResult {
  targetSlotId: string;
  nextSlotEdits: Record<string, SlotEditState>;
}

/**
 * Pure domain logic for slot duplication (M4-D, M4-E).
 *
 * Rules:
 * - Chaveiro: double-clicking a filled slot clones full SlotEditState to the next slot (slot_N -> slot_N+1).
 *   Does nothing if already at the last slot.
 * - Globo: double-clicking foto_1 clones to foto_2, and vice-versa.
 * - Calendario: single slot, duplication is a no-op.
 * - Empty source slot: duplication is a no-op.
 */
export function duplicateSlot(
  templateId: string,
  slotIds: string[],
  sourceSlotId: string,
  slotEdits: Record<string, SlotEditState>
): DuplicationResult | null {
  const sourceEdit = slotEdits[sourceSlotId];
  if (!sourceEdit) return null;

  let targetSlotId: string | null = null;

  if (templateId === "chaveiro-3x4") {
    const currentIdx = slotIds.indexOf(sourceSlotId);
    if (currentIdx !== -1 && currentIdx < slotIds.length - 1) {
      targetSlotId = slotIds[currentIdx + 1];
    }
  } else if (templateId === "globo-neve") {
    targetSlotId = sourceSlotId === "foto_1" ? "foto_2" : "foto_1";
  }

  if (!targetSlotId) return null;

  return {
    targetSlotId,
    nextSlotEdits: {
      ...slotEdits,
      [targetSlotId]: { ...sourceEdit },
    },
  };
}
