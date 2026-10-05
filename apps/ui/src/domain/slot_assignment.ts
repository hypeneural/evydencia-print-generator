import type { SlotEditState } from "./types";

/**
 * Pure slot assignment policy shared by every multi-source entry point of the
 * Operator: native Explorer multi-drop, "Adicionar fotos" dialog and the
 * context-menu startup batch. Capacity always comes from the template slot list;
 * nothing here knows about a specific product (no 18/2 hard-code).
 *
 * Invariants:
 * - occupied slots are never overwritten, except the explicit drop anchor;
 * - source order is preserved;
 * - sources that do not fit are reported (they stay in the tray), never dropped;
 * - inputs are never mutated.
 */

export const INITIAL_SLOT_TRANSFORM = {
  pan_x_norm: 0,
  pan_y_norm: 0,
  scale: 1,
  rotation_deg: 0,
} as const;

export type SlotEdits = Record<string, SlotEditState>;

export interface AssignSourcesInput {
  /** Template slot ids in template order. This is the real capacity. */
  slotIds: readonly string[];
  slotEdits: Readonly<SlotEdits>;
  /** Accepted source ids in batch (input) order. */
  sourceIds: readonly string[];
  /** Slot explicitly targeted by the user (drop over a slot). */
  anchorSlotId?: string | null;
}

export interface SlotAssignment {
  slotId: string;
  sourceId: string;
}

export interface AssignSourcesResult {
  nextSlotEdits: SlotEdits;
  assignments: SlotAssignment[];
  unassignedSourceIds: string[];
  firstAssignedSlotId: string | null;
  changed: boolean;
}

function dedupePreservingOrder(ids: readonly string[]): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const id of ids) {
    if (!id || seen.has(id)) continue;
    seen.add(id);
    out.push(id);
  }
  return out;
}

function freshSlotEdit(sourceId: string): SlotEditState {
  return { source_id: sourceId, ...INITIAL_SLOT_TRANSFORM };
}

export function assignSourcesToSlots(input: AssignSourcesInput): AssignSourcesResult {
  const { slotIds, slotEdits } = input;
  const ids = dedupePreservingOrder(input.sourceIds);

  if (ids.length === 0 || slotIds.length === 0) {
    return {
      nextSlotEdits: slotEdits as SlotEdits,
      assignments: [],
      unassignedSourceIds: ids,
      firstAssignedSlotId: null,
      changed: false,
    };
  }

  const next: SlotEdits = { ...slotEdits };
  const assignments: SlotAssignment[] = [];
  const taken = new Set<string>();
  let cursor = 0;

  const anchorIdx =
    input.anchorSlotId != null ? slotIds.indexOf(input.anchorSlotId) : -1;

  if (anchorIdx !== -1) {
    // Explicit drop target: the first source replaces it, even if occupied.
    const anchorId = slotIds[anchorIdx];
    next[anchorId] = freshSlotEdit(ids[0]);
    assignments.push({ slotId: anchorId, sourceId: ids[0] });
    taken.add(anchorId);
    cursor = 1;
  }

  // Empty-slot search order: after the anchor to the end, then wrap to the start.
  const start = anchorIdx === -1 ? 0 : anchorIdx + 1;
  const searchOrder: string[] = [];
  for (let k = 0; k < slotIds.length; k++) {
    searchOrder.push(slotIds[(start + k) % slotIds.length]);
  }

  let s = 0;
  while (cursor < ids.length && s < searchOrder.length) {
    const slotId = searchOrder[s++];
    if (taken.has(slotId) || slotEdits[slotId]) continue; // never overwrite occupied
    next[slotId] = freshSlotEdit(ids[cursor]);
    assignments.push({ slotId, sourceId: ids[cursor] });
    taken.add(slotId);
    cursor++;
  }

  const changed = assignments.length > 0;
  return {
    nextSlotEdits: changed ? next : (slotEdits as SlotEdits),
    assignments,
    unassignedSourceIds: ids.slice(cursor),
    firstAssignedSlotId: assignments[0]?.slotId ?? null,
    changed,
  };
}

export function countEmptySlots(
  slotIds: readonly string[],
  slotEdits: Readonly<SlotEdits>
): number {
  let n = 0;
  for (const id of slotIds) if (!slotEdits[id]) n++;
  return n;
}

export interface FillEmptySlotsResult {
  nextSlotEdits: SlotEdits;
  filledSlotIds: string[];
}

/**
 * "Preencher restantes": clone the full SlotEditState of the base (active) slot
 * into every EMPTY slot. Occupied slots are preserved. Returns null (no-op) when
 * the base slot has no photo or there is no empty slot.
 */
export function fillEmptySlots(input: {
  slotIds: readonly string[];
  slotEdits: Readonly<SlotEdits>;
  baseSlotId: string | null | undefined;
}): FillEmptySlotsResult | null {
  const { slotIds, slotEdits, baseSlotId } = input;
  if (!baseSlotId) return null;
  const base = slotEdits[baseSlotId];
  if (!base) return null;

  const next: SlotEdits = { ...slotEdits };
  const filledSlotIds: string[] = [];
  for (const id of slotIds) {
    if (slotEdits[id]) continue;
    next[id] = { ...base };
    filledSlotIds.push(id);
  }
  if (filledSlotIds.length === 0) return null;
  return { nextSlotEdits: next, filledSlotIds };
}

/**
 * Remove only the photo assignment of one slot. The source stays in the
 * SourceRegistry/tray and the original file is never touched.
 * Returns null (no-op) for an empty or unknown slot.
 */
export function removeSlotPhoto(
  slotEdits: Readonly<SlotEdits>,
  slotId: string | null | undefined
): SlotEdits | null {
  if (!slotId || !slotEdits[slotId]) return null;
  const next: SlotEdits = { ...slotEdits };
  delete next[slotId];
  return next;
}
