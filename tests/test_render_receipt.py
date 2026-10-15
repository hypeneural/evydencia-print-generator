"""Safety contract for print-generator JPEG/session snapshot handoff."""
from __future__ import annotations

from pathlib import Path

import pytest
from evydencia_print_generator.domain.job import EditState, JobSnapshot, SlotEdit, SlotTransform
from evydencia_print_generator.soclick.render_receipt import RenderReceipt, RenderReceiptError


def _state(scale: float = 1.0) -> EditState:
    return EditState(
        template_id="chaveiro-3x4",
        template_version="1.0.0",
        slot_edits={
            "slot_01": SlotEdit(
                source_id="source-1",
                transform=SlotTransform(
                    pan_x_norm=0, pan_y_norm=0, scale=scale, rotation_deg=0
                ),
            )
        },
    )


def _receipt(tmp_path: Path) -> tuple[RenderReceipt, Path]:
    image = tmp_path / "render.jpg"
    image.write_bytes(b"jpeg-rendered-version-1")
    state = _state()
    snapshot = JobSnapshot(
        template_id=state.template_id,
        template_version=state.template_version,
        sources={},
        slot_edits=state.slot_edits.copy(),
    )
    return RenderReceipt.capture(image, state, snapshot), image


def test_receipt_accepts_exact_render_file_and_edits(tmp_path: Path) -> None:
    receipt, image = _receipt(tmp_path)
    assert receipt.verify(str(image), _state()) is receipt.snapshot


def test_receipt_rejects_editor_changes_after_render(tmp_path: Path) -> None:
    receipt, image = _receipt(tmp_path)
    with pytest.raises(RenderReceiptError, match="enquadramento"):
        receipt.verify(str(image), _state(scale=1.1))


def test_receipt_rejects_changed_output_contents(tmp_path: Path) -> None:
    receipt, image = _receipt(tmp_path)
    image.write_bytes(b"jpeg-rendered-version-2")
    with pytest.raises(RenderReceiptError, match="JPEG foi modificado"):
        receipt.verify(str(image), _state())


def test_receipt_rejects_different_output_path(tmp_path: Path) -> None:
    receipt, _ = _receipt(tmp_path)
    other = tmp_path / "other.jpg"
    other.write_bytes(b"jpeg-rendered-version-1")
    with pytest.raises(RenderReceiptError, match="última geração"):
        receipt.verify(str(other), _state())


def test_receipt_rejects_deleted_output(tmp_path: Path) -> None:
    receipt, image = _receipt(tmp_path)
    image.unlink()
    with pytest.raises(RenderReceiptError, match="removido"):
        receipt.verify(str(image), _state())
