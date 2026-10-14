"""Unit tests for the visual customer annotations layer (keychain header)."""
from __future__ import annotations

from pathlib import Path

from evydencia_print_generator.domain.job import (
    JobSnapshot,
    JobSource,
    SlotEdit,
    SlotTransform,
)
from evydencia_print_generator.domain.template import load_template
from evydencia_print_generator.paths import templates_dir
from evydencia_print_generator.render.annotations import (
    build_keychain_header_text,
    extract_client_label,
)
from evydencia_print_generator.render.compose import compose_canvas
from PIL import Image


def test_extract_client_label_patterns():
    # 1. EvydFlow 4-part folder
    p1 = Path("C:/Fotos/JOÃO SILVA - 48999999999 - Pacote A - 1510/foto1.jpg")
    assert extract_client_label(p1) == "JOÃO 1510"
    p2 = Path("C:/Fotos/Ana Paula - 48999999999 - Pacote 2 - 4101/foto.jpg")
    assert extract_client_label(p2) == "ANA PAULA 4101"

    # 2. <ID> - <Nome>
    assert extract_client_label(Path("C:/Jobs/1510 - JOÃO/0M4A0001.jpg")) == "JOÃO 1510"
    assert extract_client_label(Path("C:/Jobs/4545 - MARIA/0M4A0002.jpg")) == "MARIA 4545"

    # 3. <Nome> <ID> or <Nome> - <ID>
    assert extract_client_label(Path("C:/Jobs/MARIA 4545/foto.jpg")) == "MARIA 4545"
    assert extract_client_label(Path("C:/Jobs/LAIS 1010/foto.jpg")) == "LAIS 1010"
    assert extract_client_label(Path("C:/Jobs/LAÍS 1010/foto.jpg")) == "LAÍS 1010"

    # 4. Pedido #<ID> - <Nome> or #<ID>
    assert extract_client_label(Path("C:/Jobs/Pedido 4545 - Maria/img.jpg")) == "MARIA 4545"
    assert extract_client_label(Path("C:/Jobs/Carlos #5022/img.jpg")) == "CARLOS 5022"

    # 5. Fallback without ID
    assert extract_client_label(Path("C:/Jobs/JOÃO/img.jpg")) == "JOÃO"
    assert extract_client_label(Path("C:/Jobs/Cléber Antônio/img.jpg")) == "CLÉBER"


def test_build_keychain_header_text_deduplication():
    tpl = load_template(templates_dir() / "chaveiro-3x4" / "template.json")

    # 3 unique clients across 18 slots
    sources = {
        "src_1": JobSource(
            source_id="src_1", path=Path("C:/Jobs/1510 - JOÃO/f1.jpg"), size_bytes=10, mtime_ns=1
        ),
        "src_2": JobSource(
            source_id="src_2", path=Path("C:/Jobs/MARIA 4545/f2.jpg"), size_bytes=10, mtime_ns=1
        ),
        "src_3": JobSource(
            source_id="src_3", path=Path("C:/Jobs/LAIS 1010/f3.jpg"), size_bytes=10, mtime_ns=1
        ),
    }

    edits: dict[str, SlotEdit] = {}
    for i, slot_id in enumerate(tpl.slot_ids):
        if i < 6:
            edits[slot_id] = SlotEdit(source_id="src_1", transform=SlotTransform())
        elif i < 12:
            edits[slot_id] = SlotEdit(source_id="src_2", transform=SlotTransform())
        else:
            edits[slot_id] = SlotEdit(source_id="src_3", transform=SlotTransform())

    snapshot = JobSnapshot(
        template_id=tpl.id,
        template_version=tpl.template_version,
        sources=sources,
        slot_edits=edits,
    )

    header = build_keychain_header_text(tpl, snapshot)
    assert header == "JOÃO 1510 | MARIA 4545 | LAIS 1010"


def test_build_keychain_header_text_single_client():
    tpl = load_template(templates_dir() / "chaveiro-3x4" / "template.json")
    sources = {
        "src_1": JobSource(
            source_id="src_1", path=Path("C:/Jobs/1510 - JOÃO/f1.jpg"), size_bytes=10, mtime_ns=1
        ),
    }
    edits = {s: SlotEdit(source_id="src_1", transform=SlotTransform()) for s in tpl.slot_ids}
    snapshot = JobSnapshot(
        template_id=tpl.id,
        template_version=tpl.template_version,
        sources=sources,
        slot_edits=edits,
    )

    header = build_keychain_header_text(tpl, snapshot)
    assert header == "JOÃO 1510"


def test_build_keychain_header_text_partial_slots():
    tpl = load_template(templates_dir() / "chaveiro-3x4" / "template.json")
    sources = {
        "src_1": JobSource(
            source_id="src_1", path=Path("C:/Jobs/1510 - JOÃO/f1.jpg"), size_bytes=10, mtime_ns=1
        ),
        "src_2": JobSource(
            source_id="src_2", path=Path("C:/Jobs/MARIA 4545/f2.jpg"), size_bytes=10, mtime_ns=1
        ),
    }
    # Only 2 slots filled
    edits = {
        "slot_01": SlotEdit(source_id="src_1", transform=SlotTransform()),
        "slot_02": SlotEdit(source_id="src_2", transform=SlotTransform()),
    }
    snapshot = JobSnapshot(
        template_id=tpl.id,
        template_version=tpl.template_version,
        sources=sources,
        slot_edits=edits,
    )

    header = build_keychain_header_text(tpl, snapshot)
    assert header == "JOÃO 1510 | MARIA 4545"


def test_build_keychain_header_text_ignored_for_other_templates():
    tpl = load_template(templates_dir() / "calendario-2027" / "template.json")
    sources = {
        "src_1": JobSource(
            source_id="src_1", path=Path("C:/Jobs/1510 - JOÃO/f1.jpg"), size_bytes=10, mtime_ns=1
        ),
    }
    edits = {"slot_01": SlotEdit(source_id="src_1", transform=SlotTransform())}
    snapshot = JobSnapshot(
        template_id=tpl.id,
        template_version=tpl.template_version,
        sources=sources,
        slot_edits=edits,
    )

    header = build_keychain_header_text(tpl, snapshot)
    assert header == ""


def test_draw_keychain_header_preserves_canvas_size(tmp_path):
    tpl = load_template(templates_dir() / "chaveiro-3x4" / "template.json")

    # Create dummy images
    img_path1 = tmp_path / "f1.jpg"
    img_path2 = tmp_path / "f2.jpg"
    Image.new("RGB", (200, 200), color="blue").save(img_path1)
    Image.new("RGB", (200, 200), color="green").save(img_path2)

    sources = {
        "src_1": JobSource(source_id="src_1", path=img_path1, size_bytes=100, mtime_ns=1),
        "src_2": JobSource(source_id="src_2", path=img_path2, size_bytes=100, mtime_ns=1),
    }
    edits = {
        "slot_01": SlotEdit(source_id="src_1", transform=SlotTransform()),
        "slot_02": SlotEdit(source_id="src_2", transform=SlotTransform()),
    }
    snapshot = JobSnapshot(
        template_id=tpl.id,
        template_version=tpl.template_version,
        sources=sources,
        slot_edits=edits,
    )

    canvas, icc = compose_canvas(tpl, snapshot)
    assert canvas.size == (2551, 1795)

    # Top strip (y = 106 px) should contain the divider line
    # Checking that divider line was drawn: pixel at (x=100, y=106) should not be pure white
    pixel_divider = canvas.getpixel((100, 106))
    assert pixel_divider != (255, 255, 255)
