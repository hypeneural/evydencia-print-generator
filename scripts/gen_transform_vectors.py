#!/usr/bin/env python3
"""Regenerate tests/fixtures/transform_vectors.json from domain/transform.py.

Only run this after an intentional ADR-011 change. The JSON is the Python<->TypeScript
parity contract; tests fail if the implementation drifts from the committed vectors.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "desktop" / "src"))

from evydencia_print_generator.domain.transform import (  # noqa: E402
    SlotTransform,
    clamp_transform,
    cover_scale,
    pan_by_slot_delta,
    resolve_placement,
    slot_to_source_affine,
)

OUT = ROOT / "tests" / "fixtures" / "transform_vectors.json"

CASES: list[dict] = [
    {"name": "landscape_in_square_identity", "src": [4000, 3000], "slot": [1000, 1000],
     "t": [0, 0, 1, 0]},
    {"name": "landscape_in_square_pan_right_edge", "src": [4000, 3000], "slot": [1000, 1000],
     "t": [1, 0, 1, 0]},
    {"name": "landscape_in_square_pan_y_no_range", "src": [4000, 3000], "slot": [1000, 1000],
     "t": [0, 1, 1, 0]},
    {"name": "portrait_slot_zoom2_pan", "src": [6000, 4000], "slot": [800, 1200],
     "t": [-0.5, 0.25, 2, 0]},
    {"name": "rot90_wide_slot", "src": [4000, 3000], "slot": [1000, 500],
     "t": [0, 0, 1, 90]},
    {"name": "rot90_pan", "src": [4000, 3000], "slot": [1000, 500],
     "t": [0.5, -0.5, 1.5, 90]},
    {"name": "rot180", "src": [3000, 3000], "slot": [900, 600],
     "t": [0.3, 0.3, 1.2, 180]},
    {"name": "rot_minus90", "src": [3000, 4000], "slot": [700, 900],
     "t": [-1, 1, 1.1, -90]},
    {"name": "rot45_square", "src": [3000, 3000], "slot": [1000, 1000],
     "t": [0, 0, 1, 45]},
    {"name": "rot_minus12_5_pan_zoom", "src": [5472, 3648], "slot": [1181, 1654],
     "t": [0.4, -0.7, 1.75, -12.5]},
    {"name": "rot270_normalizes", "src": [4000, 3000], "slot": [1000, 500],
     "t": [0, 0, 1, 270]},
    {"name": "clamps_out_of_range", "src": [4000, 3000], "slot": [1000, 1000],
     "t": [3, -3, 20, 540]},
    {"name": "clamps_scale_below_one", "src": [4000, 3000], "slot": [1000, 1000],
     "t": [0, 0, 0.25, 0]},
]

DRAG_CASES: list[dict] = [
    {"name": "drag_right_rot0", "src": [4000, 3000], "slot": [1000, 1000],
     "t": [0, 0, 1.5, 0], "delta": [100, 0]},
    {"name": "drag_right_rot90", "src": [4000, 3000], "slot": [1000, 500],
     "t": [0, 0, 1.5, 90], "delta": [100, 0]},
    {"name": "drag_diag_rot30_clamps", "src": [4000, 3000], "slot": [1000, 800],
     "t": [0.9, 0.9, 2, 30], "delta": [5000, 5000]},
]


def _t(values: list[float]) -> SlotTransform:
    return SlotTransform(*map(float, values))


def _tdict(t: SlotTransform) -> dict:
    return {"pan_x_norm": t.pan_x_norm, "pan_y_norm": t.pan_y_norm, "scale": t.scale,
            "rotation_deg": t.rotation_deg}


def build() -> dict:
    cases = []
    for case in CASES:
        (sw, sh), (w, h), t = case["src"], case["slot"], _t(case["t"])
        clamped = clamp_transform(t)
        p = resolve_placement(sw, sh, w, h, t)
        cases.append({
            "name": case["name"],
            "src": case["src"],
            "slot": case["slot"],
            "transform": _tdict(t),
            "expected": {
                "clamped": _tdict(clamped),
                "cover_scale": cover_scale(sw, sh, w, h, clamped.rotation_deg),
                "effective_scale": p.effective_scale,
                "center": [p.center_x, p.center_y],
                "max_pan": [p.max_dx, p.max_dy],
                "affine": list(slot_to_source_affine(sw, sh, p)),
            },
        })
    drags = []
    for case in DRAG_CASES:
        (sw, sh), (w, h), t = case["src"], case["slot"], _t(case["t"])
        dx, dy = case["delta"]
        drags.append({
            "name": case["name"],
            "src": case["src"],
            "slot": case["slot"],
            "transform": _tdict(t),
            "delta": case["delta"],
            "expected": _tdict(pan_by_slot_delta(sw, sh, w, h, t, dx, dy)),
        })
    return {
        "adr": "ADR-011",
        "tolerance": 1e-9,
        "placement_cases": cases,
        "drag_cases": drags,
    }


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
