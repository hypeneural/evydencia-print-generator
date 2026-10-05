"""Pure domain logic for print render eligibility per product.

Python mirror of apps/ui/src/domain/render_policy.ts.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class RenderEligibility:
    can_render: bool
    filled_count: int
    minimum_required: int
    total_slots: int
    missing_for_requirement: int
    require_all: bool
    status_message: str


def get_minimum_filled_slots(template_id: str, total_slots: int) -> tuple[int, bool]:
    """Returns (minimum_required, require_all)."""
    if template_id == "chaveiro-3x4":
        return 2, False
    return total_slots, True


def check_render_eligibility(
    template_id: str,
    slot_ids: Sequence[str],
    filled_slot_ids: Sequence[str],
) -> RenderEligibility:
    total = len(slot_ids)
    slot_set = set(slot_ids)
    valid_filled = set(filled_slot_ids) & slot_set
    filled_count = len(valid_filled)
    minimum_required, require_all = get_minimum_filled_slots(template_id, total)

    can_render = filled_count >= minimum_required
    missing = max(0, minimum_required - filled_count)

    if can_render:
        status_message = "Pronto para gerar"
    elif filled_count == 0:
        status_message = (
            f"Adicione pelo menos {minimum_required} fotos"
            if minimum_required > 1
            else "Adicione uma foto"
        )
    else:
        suffix = "s" if missing > 1 else ""
        status_message = f"Adicione mais {missing} foto{suffix} para gerar"

    return RenderEligibility(
        can_render=can_render,
        filled_count=filled_count,
        minimum_required=minimum_required,
        total_slots=total,
        missing_for_requirement=missing,
        require_all=require_all,
        status_message=status_message,
    )
