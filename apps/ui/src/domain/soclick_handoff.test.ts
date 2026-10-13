import { describe, it, expect, vi } from "vitest";
import { bridge, type SoclicHandoffResponse } from "../bridge/api";
import type { EditStateModel, RenderResultModel } from "./types";

describe("SoClic Handoff UI Bridge Contract", () => {
  const dummyRenderResult: RenderResultModel = {
    output_path: "C:\\Mock\\Output\\Chaveiro_20261013.jpg",
    template_id: "chaveiro-3x4",
    canvas_size_px: [2551, 1795],
    dpi: 300,
    render_time_ms: 120,
    bytes_written: 1048576,
  };

  const dummyEditState: EditStateModel = {
    template_id: "chaveiro-3x4",
    template_version: "1.0.0",
    slot_edits: {
      slot_01: {
        source_id: "src_1",
        pan_x_norm: 0,
        pan_y_norm: 0,
        scale: 1,
        rotation_deg: 0,
      },
    },
  };

  it("calls prepareSoclic with render result and edit state", async () => {
    const spy = vi.spyOn(bridge, "prepareSoclic").mockResolvedValueOnce({
      ok: true,
      job_id: "job_print_abc123",
      observation: "Chaveiro | Ana #4101 | 1 folha",
      panel_url: "http://127.0.0.1:8095/panel/soclick?focus=job_print_abc123#review",
      is_existing: false,
      total_orders: 1,
    });

    const res: SoclicHandoffResponse = await bridge.prepareSoclic(dummyRenderResult, dummyEditState);

    expect(spy).toHaveBeenCalledWith(dummyRenderResult, dummyEditState);
    expect(res.ok).toBe(true);
    expect(res.job_id).toBe("job_print_abc123");
    expect(res.observation).toContain("Chaveiro | Ana #4101 | 1 folha");
    expect(res.panel_url).toContain("#review");
    expect(res.is_existing).toBe(false);
  });

  it("handles panel unavailable error cleanly without throwing", async () => {
    vi.spyOn(bridge, "prepareSoclic").mockResolvedValueOnce({
      ok: false,
      error: "Painel EvydFlow não está em execução na porta local. Inicie o EvydFlow para preparar na SóClick.",
    });

    const res = await bridge.prepareSoclic(dummyRenderResult, dummyEditState);

    expect(res.ok).toBe(false);
    expect(res.error).toContain("Painel EvydFlow não está em execução");
  });

  it("returns idempotent flag when job already exists", async () => {
    vi.spyOn(bridge, "prepareSoclic").mockResolvedValueOnce({
      ok: true,
      job_id: "job_print_existing",
      observation: "Chaveiro | #4101 | 1 folha",
      panel_url: "http://127.0.0.1:8095/panel/soclick?focus=job_print_existing#review",
      is_existing: true,
      total_orders: 1,
    });

    const res = await bridge.prepareSoclic(dummyRenderResult, dummyEditState);

    expect(res.ok).toBe(true);
    expect(res.is_existing).toBe(true);
    expect(res.job_id).toBe("job_print_existing");
  });
});
