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

export interface DuplicateSelectedSlotsInput {
  slotIds: readonly string[];
  selectedSlotIds: readonly string[];
  slotEdits: Readonly<Record<string, SlotEditState>>;
}

export interface DuplicateSelectedSlotsResult {
  nextSlotEdits: Record<string, SlotEditState>;
  duplicatedCount: number;
  unassignedCount: number;
  targetSlotIds: string[];
  changed: boolean;
}

/**
 * Pure domain logic for batch duplication of multiple selected slots (Chaveiro).
 *
 * Rules:
 * - Considers only selected slots that have a photo.
 * - Preserves physical order of template.slots.
 * - Never overwrites occupied slots or source slots.
 * - Seeks empty slots starting after the highest selected index, with wrap-around.
 * - Stops when no empty slots remain.
 * - Clones full SlotEditState (source_id, pan_x_norm, pan_y_norm, scale, rotation_deg).
 */
export function duplicateSelectedSlots(
  input: DuplicateSelectedSlotsInput
): DuplicateSelectedSlotsResult {
  const { slotIds, selectedSlotIds, slotEdits } = input;
  const slotSet = new Set(slotIds);

  // 1. Filter selected slots to valid filled slots and preserve template order
  const validSelectedSet = new Set(
    selectedSlotIds.filter((id) => slotSet.has(id) && !!slotEdits[id])
  );

  const sourcesInOrder = slotIds.filter((id) => validSelectedSet.has(id));
  if (sourcesInOrder.length === 0) {
    return {
      nextSlotEdits: { ...slotEdits },
      duplicatedCount: 0,
      unassignedCount: 0,
      targetSlotIds: [],
      changed: false,
    };
  }

  // 2. Determine search order starting after max selected index with wrap-around
  const selectedIndices = sourcesInOrder.map((id) => slotIds.indexOf(id));
  const maxSelectedIdx = Math.max(...selectedIndices);

  const searchQueue: string[] = [];
  for (let i = maxSelectedIdx + 1; i < slotIds.length; i++) {
    searchQueue.push(slotIds[i]);
  }
  for (let i = 0; i <= maxSelectedIdx; i++) {
    searchQueue.push(slotIds[i]);
  }

  // Find empty candidate slots (not currently occupied and not in selected sources)
  const emptyCandidates = searchQueue.filter(
    (id) => !slotEdits[id] && !validSelectedSet.has(id)
  );

  const nextSlotEdits: Record<string, SlotEditState> = { ...slotEdits };
  const targetSlotIds: string[] = [];
  let duplicatedCount = 0;
  let unassignedCount = 0;

  for (let i = 0; i < sourcesInOrder.length; i++) {
    const srcId = sourcesInOrder[i];
    const srcEdit = slotEdits[srcId];
    if (i < emptyCandidates.length) {
      const tgtId = emptyCandidates[i];
      nextSlotEdits[tgtId] = { ...srcEdit };
      targetSlotIds.push(tgtId);
      duplicatedCount++;
    } else {
      unassignedCount++;
    }
  }

  return {
    nextSlotEdits,
    duplicatedCount,
    unassignedCount,
    targetSlotIds,
    changed: duplicatedCount > 0,
  };
}

