import type {
  EditStateModel,
  IngestBatchModel,
  RenderResultModel,
  SourceAssetModel,
  TemplateModel,
} from "../domain/types";

export interface StartupBatchModel {
  accepted_ids: string[];
  compatibility_warning?: string;
}

export interface SoclicHandoffResponse {
  ok: boolean;
  job_id?: string;
  observation?: string;
  panel_url?: string;
  browser_opened?: boolean;
  is_existing?: boolean;
  total_orders?: number;
  error?: string;
  error_code?: string;
}

declare global {
  interface Window {
    pywebview?: {
      api: {
        get_templates: () => Promise<TemplateModel[]>;
        get_sources: () => Promise<SourceAssetModel[]>;
        get_startup_batch: () => Promise<StartupBatchModel>;
        open_file_dialog: () => Promise<IngestBatchModel>;
        ingest_paths: (paths: string[]) => Promise<SourceAssetModel[]>;
        render_job: (edit_state: EditStateModel) => Promise<RenderResultModel>;
        open_output_folder: (file_path: string) => Promise<boolean>;
        prepare_soclic: (
          render_result: RenderResultModel,
          edit_state: EditStateModel
        ) => Promise<SoclicHandoffResponse>;
      };
    };
  }
}

// Mock implementation for browser-only development (vite dev)
const mockTemplates: TemplateModel[] = [
  {
    id: "calendario-2027",
    template_version: "1.0.0",
    name: "Calendário 2027",
    status: "production",
    canvas: { width_mm: 106.7, height_mm: 147.4, dpi: 254 },
    canvas_px: { width: 1067, height: 1474 },
    slots: [
      {
        id: "foto_principal",
        x_mm: 11.8,
        y_mm: 10.7,
        width_mm: 82.3,
        height_mm: 39.5,
        rect_px: { left: 118, top: 107, width: 823, height: 395 },
        fit: "cover",
        allow_pan: true,
        allow_zoom: true,
        allow_rotate: true,
      },
    ],
    overlay: {
      path: "assets/calendar-2027-overlay.png",
      url: "/api/templates/calendario-2027/assets/calendar-2027-overlay.png",
    },
  },
  {
    id: "globo-neve",
    template_version: "1.1.0",
    name: "Globo de Neve",
    status: "production",
    fixed_production_geometry: true,
    canvas: { width_mm: 152, height_mm: 102, dpi: 300 },
    canvas_px: { width: 1795, height: 1205 },
    slots: [
      {
        id: "foto_1",
        x_mm: 16.7,
        y_mm: 10.2,
        width_mm: 50.0,
        height_mm: 80.0,
        rect_px: { left: 197, top: 120, width: 591, height: 945 },
        fit: "cover",
        allow_pan: true,
        allow_zoom: true,
        allow_rotate: true,
      },
      {
        id: "foto_2",
        x_mm: 73.7,
        y_mm: 10.2,
        width_mm: 50.0,
        height_mm: 80.0,
        rect_px: { left: 870, top: 120, width: 591, height: 945 },
        fit: "cover",
        allow_pan: true,
        allow_zoom: true,
        allow_rotate: true,
      },
    ],
    overlay: null,
  },
  {
    id: "chaveiro-3x4",
    template_version: "1.0.0",
    name: "Chaveiro 3x4 (18 fotos)",
    status: "production",
    fixed_production_geometry: true,
    canvas: { width_mm: 216, height_mm: 152, dpi: 300 },
    canvas_px: { width: 2551, height: 1795 },
    slots: Array.from({ length: 18 }, (_, i) => {
      const col = i % 6;
      const row = Math.floor(i / 6);
      const x_mm = 6 + col * 34;
      const y_mm = 10 + row * 44;
      const left = Math.round((x_mm / 25.4) * 300);
      const right = Math.round(((x_mm + 34) / 25.4) * 300);
      const top = Math.round((y_mm / 25.4) * 300);
      const bottom = Math.round(((y_mm + 44) / 25.4) * 300);
      return {
        id: `slot_${String(i + 1).padStart(2, "0")}`,
        x_mm,
        y_mm,
        width_mm: 34,
        height_mm: 44,
        rect_px: {
          left,
          top,
          width: right - left,
          height: bottom - top,
        },
        fit: "cover",
        allow_pan: true,
        allow_zoom: true,
        allow_rotate: true,
      };
    }),
    overlay: null,
  },
  {
    id: "polaroid-natal",
    template_version: "1.0.0",
    name: "Polaroid Natal",
    status: "draft",
    canvas: { width_mm: 82.97, height_mm: 102.02, dpi: 300 },
    canvas_px: { width: 980, height: 1205 },
    slots: [
      {
        id: "foto_principal",
        x_mm: 5.84,
        y_mm: 5.0,
        width_mm: 71.37,
        height_mm: 72.98,
        rect_px: { left: 69, top: 59, width: 843, height: 862 },
        fit: "cover",
        allow_pan: true,
        allow_zoom: true,
        allow_rotate: true,
      },
    ],
    overlay: {
      path: "assets/polaroid-overlay.png",
      url: "/api/templates/polaroid-natal/assets/polaroid-overlay.png",
    },
  },
];

let mockSources: SourceAssetModel[] = [];

// pywebview exposes the Python methods asynchronously. An existing "api" object does
// not mean each method is registered yet. Wait for the specific callable and honour
// the official "pywebviewready" event. Browser mocks are DEV-ONLY.
type NativeApi = NonNullable<Window["pywebview"]>["api"];

async function nativeMethod<K extends keyof NativeApi>(
  name: K,
  optional = false,
): Promise<NativeApi[K] | null> {
  if (import.meta.env.DEV && (typeof window === "undefined" || !window.pywebview)) return null;

  const method = () => {
    const api = window.pywebview?.api;
    const fn = api?.[name];
    return typeof fn === "function" ? (fn.bind(api) as NativeApi[K]) : null;
  };
  if (method()) return method();

  // pywebviewready can arrive after DOM load (or just before this listener).
  // The short bounded probe also covers API registration after the event.
  await new Promise<void>((resolve) => {
    let settled = false;
    let intervalId: number | undefined;
    let timeoutId: number | undefined;
    const finish = () => {
      if (settled) return;
      settled = true;
      window.removeEventListener("pywebviewready", check);
      if (intervalId !== undefined) window.clearInterval(intervalId);
      if (timeoutId !== undefined) window.clearTimeout(timeoutId);
      resolve();
    };
    const check = () => { if (method()) finish(); };
    window.addEventListener("pywebviewready", check);
    intervalId = window.setInterval(check, 50);
    timeoutId = window.setTimeout(finish, optional ? 500 : 6000);
    check();
  });

  const resolved = method();
  if (!resolved && !optional) {
    throw new Error(
      `A API Python do gerador não disponibilizou ${String(name)}. ` +
      "Feche todas as instâncias, atualize o aplicativo Python e reconstrua a interface (npm run build --prefix apps/ui). " +
      "Verifique se o executável/atalho usa o mesmo checkout atualizado.",
    );
  }
  return resolved;
}

export const bridge = {
  isPyWebView(): boolean {
    return typeof window !== "undefined" && !!window.pywebview?.api;
  },

  async getTemplates(): Promise<TemplateModel[]> {
    const getTemplates = await nativeMethod("get_templates");
    if (getTemplates) return getTemplates();
    return mockTemplates;
  },

  async getSources(): Promise<SourceAssetModel[]> {
    const getSources = await nativeMethod("get_sources");
    if (getSources) return getSources();
    return mockSources;
  },

  async getStartupBatch(initialSources?: SourceAssetModel[]): Promise<StartupBatchModel> {
    const getStartupBatch = await nativeMethod("get_startup_batch", true);
    if (getStartupBatch) return getStartupBatch();
    // Old installed Python bridges do not expose this method. In a fresh
    // desktop window the initial registry contains precisely the CLI batch.
    // Preserve all files, not only the first, and show a diagnostic warning.
    if (import.meta.env.DEV && (typeof window === "undefined" || !window.pywebview)) return { accepted_ids: [] };
    const sources = initialSources ?? await this.getSources();
    return {
      accepted_ids: sources.map((source) => source.id),
      compatibility_warning: "API Python antiga: get_startup_batch indisponível. Fotos recuperadas do registro; atualize o executável/ambiente Python.",
    };
  },

  async openFileDialog(): Promise<IngestBatchModel> {
    const openDialog = await nativeMethod("open_file_dialog");
    if (openDialog) return openDialog();
    // Mock image for browser dev
    const mockAsset: SourceAssetModel = {
      id: "mock_source_" + Date.now(),
      display_name: "foto_demonstracao.jpg",
      probe: {
        format: "JPEG",
        width: 4000,
        height: 3000,
        oriented_width: 4000,
        oriented_height: 3000,
        has_icc: true,
      },
      preview: {
        status: "ready",
        url: "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='800' height='600'><rect width='800' height='600' fill='%2334495e'/><circle cx='400' cy='300' r='180' fill='%23e74c3c'/><text x='400' y='320' font-size='36' font-family='sans-serif' fill='white' text-anchor='middle'>Preview Demonstracao</text></svg>",
      },
    };
    mockSources = [...mockSources, mockAsset];
    return {
      sources: mockSources,
      accepted_ids: [mockAsset.id],
      rejected: [],
    };
  },

  async ingestPaths(paths: string[]): Promise<SourceAssetModel[]> {
    const ingestPaths = await nativeMethod("ingest_paths");
    if (ingestPaths) return ingestPaths(paths);
    return mockSources;
  },

  async renderJob(editState: EditStateModel): Promise<RenderResultModel> {
    const renderJob = await nativeMethod("render_job");
    if (renderJob) return renderJob(editState);
    // Mock render
    await new Promise((r) => setTimeout(r, 600));
    return {
      output_path: "C:\\Users\\Mock\\Calendario_foto_demonstracao.jpg",
      template_id: editState.template_id,
      canvas_size_px: [591, 827],
      dpi: 150,
      render_time_ms: 185.4,
      bytes_written: 124500,
    };
  },

  async openOutputFolder(filePath: string): Promise<boolean> {
    const openOutput = await nativeMethod("open_output_folder");
    if (openOutput) return openOutput(filePath);
    console.log("Mock open folder:", filePath);
    return true;
  },

  async prepareSoclic(
    renderResult: RenderResultModel,
    editState: EditStateModel
  ): Promise<SoclicHandoffResponse> {
    const prepareSoclic = await nativeMethod("prepare_soclic");
    if (prepareSoclic) return prepareSoclic(renderResult, editState);
    console.log("Mock prepareSoclic:", renderResult, editState);
    await new Promise((r) => setTimeout(r, 600));
    return {
      ok: true,
      job_id: "job_print_mock123",
      observation: "Chaveiro | Mock #4101 | 1 folha",
      panel_url: "http://127.0.0.1:8095/panel/soclick?focus=job_print_mock123#review",
      browser_opened: true,
      is_existing: false,
      total_orders: 1,
    };
  },
};

