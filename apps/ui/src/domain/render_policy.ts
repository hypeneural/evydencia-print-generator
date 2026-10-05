/**
 * Pure domain logic for print render eligibility per product.
 * TypeScript mirror of apps/desktop/src/evydencia_print_generator/domain/render_policy.py.
 */

export interface RenderEligibility {
  canRender: boolean;
  filledCount: number;
  minimumRequired: number;
  totalSlots: number;
  missingForRequirement: number;
  requireAll: boolean;
  statusMessage: string;
}

export function getMinimumFilledSlots(
  templateId: string,
  totalSlots: number
): { minimumRequired: number; requireAll: boolean } {
  if (templateId === "chaveiro-3x4") {
    return { minimumRequired: 2, requireAll: false };
  }
  return { minimumRequired: totalSlots, requireAll: true };
}

export function checkRenderEligibility(
  templateId: string,
  slotIds: readonly string[],
  filledSlotIds: readonly string[]
): RenderEligibility {
  const total = slotIds.length;
  const slotSet = new Set(slotIds);
  const validFilled = Array.from(new Set(filledSlotIds.filter((id) => slotSet.has(id))));
  const filledCount = validFilled.length;
  const { minimumRequired, requireAll } = getMinimumFilledSlots(templateId, total);

  const canRender = filledCount >= minimumRequired;
  const missingForRequirement = Math.max(0, minimumRequired - filledCount);

  let statusMessage = "Pronto para gerar";
  if (!canRender) {
    if (filledCount === 0) {
      statusMessage =
        minimumRequired > 1
          ? `Adicione pelo menos ${minimumRequired} fotos`
          : "Adicione uma foto";
    } else {
      statusMessage = `Adicione mais ${missingForRequirement} foto${missingForRequirement > 1 ? "s" : ""} para gerar`;
    }
  }

  return {
    canRender,
    filledCount,
    minimumRequired,
    totalSlots: total,
    missingForRequirement,
    requireAll,
    statusMessage,
  };
}
