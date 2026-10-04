import type {
  EditStateModel,
  RenderResultModel,
  SourceAssetModel,
  TemplateModel,
} from "../domain/types";

declare global {
  interface Window {
    pywebview?: {
      api: {
        get_templates: () => Promise<TemplateModel[]>;
        get_sources: () => Promise<SourceAssetModel[]>;
        open_file_dialog: () => Promise<SourceAssetModel[]>;
        ingest_paths: (paths: string[]) => Promise<SourceAssetModel[]>;
        render_job: (edit_state: EditStateModel) => Promise<RenderResultModel>;
        open_output_folder: (file_path: string) => Promise<boolean>;
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
    overlay: null,
  },
  {
    id: "globo-neve",
    template_version: "1.0.0",
    name: "Globo de Neve",
    status: "production",
    canvas: { width_mm: 152, height_mm: 102, dpi: 300 },
    canvas_px: { width: 1795, height: 1205 },
    slots: [
      {
        id: "foto_1",
        x_mm: 22.5,
        y_mm: 11.0,
        width_mm: 50.0,
        height_mm: 80.0,
        rect_px: { left: 266, top: 130, width: 590, height: 945 },
        fit: "cover",
        allow_pan: true,
        allow_zoom: true,
        allow_rotate: true,
      },
      {
        id: "foto_2",
        x_mm: 79.5,
        y_mm: 11.0,
        width_mm: 50.0,
        height_mm: 80.0,
        rect_px: { left: 939, top: 130, width: 590, height: 945 },
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
    canvas: { width_mm: 216, height_mm: 152, dpi: 300 },
    canvas_px: { width: 2551, height: 1795 },
    slots: Array.from({ length: 18 }, (_, i) => {
      const col = i % 6;
      const row = Math.floor(i / 6);
      const x_mm = 6 + col * 34;
      const y_mm = 10 + row * 44;
      return {
        id: `slot_${String(i + 1).padStart(2, "0")}`,
        x_mm,
        y_mm,
        width_mm: 34,
        height_mm: 44,
        rect_px: {
          left: Math.round((x_mm / 25.4) * 300),
          top: Math.round((y_mm / 25.4) * 300),
          width: Math.round((34 / 25.4) * 300),
          height: Math.round((44 / 25.4) * 300),
        },
        fit: "cover",
        allow_pan: true,
        allow_zoom: true,
        allow_rotate: true,
      };
    }),
    overlay: null,
  },
];

let mockSources: SourceAssetModel[] = [];

export const bridge = {
  isPyWebView(): boolean {
    return typeof window !== "undefined" && !!window.pywebview?.api;
  },

  async getTemplates(): Promise<TemplateModel[]> {
    if (window.pywebview?.api) {
      return window.pywebview.api.get_templates();
    }
    return mockTemplates;
  },

  async getSources(): Promise<SourceAssetModel[]> {
    if (window.pywebview?.api) {
      return window.pywebview.api.get_sources();
    }
    return mockSources;
  },

  async openFileDialog(): Promise<SourceAssetModel[]> {
    if (window.pywebview?.api) {
      return window.pywebview.api.open_file_dialog();
    }
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
    return [mockAsset];
  },

  async ingestPaths(paths: string[]): Promise<SourceAssetModel[]> {
    if (window.pywebview?.api) {
      return window.pywebview.api.ingest_paths(paths);
    }
    return mockSources;
  },

  async renderJob(editState: EditStateModel): Promise<RenderResultModel> {
    if (window.pywebview?.api) {
      return window.pywebview.api.render_job(editState);
    }
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
    if (window.pywebview?.api) {
      return window.pywebview.api.open_output_folder(filePath);
    }
    console.log("Mock open folder:", filePath);
    return true;
  },
};
