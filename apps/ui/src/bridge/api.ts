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
    id: "calendar-synthetic",
    template_version: "0.0.1",
    name: "Calendário 2027 (Demonstração)",
    status: "draft",
    canvas: { width_mm: 100, height_mm: 140, dpi: 150 },
    canvas_px: { width: 591, height: 827 },
    slots: [
      {
        id: "foto_principal",
        x_mm: 10,
        y_mm: 10,
        width_mm: 80,
        height_mm: 40,
        rect_px: { left: 59, top: 59, width: 472, height: 236 },
        fit: "cover",
        allow_pan: true,
        allow_zoom: true,
        allow_rotate: true,
      },
    ],
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
