import { afterEach, describe, expect, it, vi } from "vitest";
import { bridge } from "../bridge/api";
import type { SourceAssetModel } from "./types";

const source: SourceAssetModel = {
  id: "src_1",
  display_name: "original.jpg",
  probe: {
    format: "JPEG",
    width: 800,
    height: 600,
    oriented_width: 800,
    oriented_height: 600,
    has_icc: false,
  },
  preview: { status: "queued", url: null },
};

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("pywebview startup API compatibility", () => {
  it("preserves existing photo IDs if a legacy Python bridge lacks get_startup_batch", async () => {
    vi.useFakeTimers();
    const nativeApi = {
      get_templates: vi.fn(async () => []),
      get_sources: vi.fn(async () => [source]),
    };
    vi.stubGlobal("window", {
      pywebview: { api: nativeApi },
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      setInterval: globalThis.setInterval,
      clearInterval: globalThis.clearInterval,
      setTimeout: globalThis.setTimeout,
      clearTimeout: globalThis.clearTimeout,
    });

    const pending = bridge.getStartupBatch([source]);
    await vi.advanceTimersByTimeAsync(600);
    const result = await pending;
    expect(result.accepted_ids).toEqual(["src_1"]);
    expect(result.compatibility_warning).toContain("get_startup_batch");
  });

  it("uses the authoritative startup order when the native API has the method", async () => {
    const startup = vi.fn(async () => ({ accepted_ids: ["src_2", "src_1"] }));
    vi.stubGlobal("window", { pywebview: { api: { get_startup_batch: startup } } });
    const result = await bridge.getStartupBatch([source]);
    expect(result.accepted_ids).toEqual(["src_2", "src_1"]);
    expect(startup).toHaveBeenCalledOnce();
    expect(result.compatibility_warning).toBeUndefined();
  });

  it("calls template API when available instead of browser mock templates", async () => {
    const templates = vi.fn(async () => []);
    vi.stubGlobal("window", { pywebview: { api: { get_templates: templates } } });
    expect(await bridge.getTemplates()).toEqual([]);
    expect(templates).toHaveBeenCalledOnce();
  });
});
