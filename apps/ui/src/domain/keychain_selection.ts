/**
 * Operator-only Chaveiro selection semantics.
 *
 * A mouse double click emits down/up twice before dblclick: clicking a member
 * of an existing multi-selection MUST NOT collapse it on the first mouse down.
 * Shift+click remains the explicit way to add/remove members.
 *
 * UI-only: no template geometry, slot edits, or production data is changed.
 */
export interface KeychainSelection {
  activeSlotId: string;
  selectedSlotIds: string[];
}

export function selectKeychainSlot(
  selectedSlotIds: readonly string[],
  slotId: string,
  shiftKey = false
): KeychainSelection {
  const uniqueSelected = [...new Set(selectedSlotIds)];
  if (!shiftKey) {
    return {
      activeSlotId: slotId,
      selectedSlotIds:
        uniqueSelected.length > 1 && uniqueSelected.includes(slotId)
          ? uniqueSelected
          : [slotId],
    };
  }

  if (!uniqueSelected.includes(slotId)) {
    return {
      activeSlotId: slotId,
      selectedSlotIds: [...uniqueSelected, slotId],
    };
  }

  // Never leave zero selected slots or focus a slot just deselected.
  const remaining = uniqueSelected.filter((id) => id !== slotId);
  return {
    activeSlotId: remaining.length ? remaining[remaining.length - 1] : slotId,
    selectedSlotIds: remaining.length ? remaining : [slotId],
  };
}

/** A group dblclick applies only when the clicked photo belongs to that group. */
export function isKeychainGroupDoubleClick(
  templateId: string,
  selectedSlotIds: readonly string[],
  clickedSlotId: string,
  filledSlotIds: Readonly<Record<string, unknown>>
): boolean {
  return (
    templateId === "chaveiro-3x4" &&
    selectedSlotIds.length > 1 &&
    selectedSlotIds.includes(clickedSlotId) &&
    !!filledSlotIds[clickedSlotId]
  );
}
