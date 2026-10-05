export type PreviewStatus = "queued" | "loading" | "ready" | "error";

export interface PixelRect {
  left: number;
  top: number;
  width: number;
  height: number;
}

export interface SlotSpec {
  id: string;
  x_mm: number;
  y_mm: number;
  width_mm: number;
  height_mm: number;
  rect_px: PixelRect;
  fit: string;
  allow_pan: boolean;
  allow_zoom: boolean;
  allow_rotate: boolean;
}

export interface TemplateModel {
  id: string;
  template_version: string;
  name: string;
  status: string;
  canvas: {
    width_mm: number;
    height_mm: number;
    dpi: number;
  };
  canvas_px: {
    width: number;
    height: number;
  };
  slots: SlotSpec[];
  overlay: {
    path: string;
    url?: string;
  } | null;
  fixed_production_geometry?: boolean;
}

export interface SourceAssetModel {
  id: string;
  display_name: string;
  probe: {
    format: string;
    width: number;
    height: number;
    oriented_width: number;
    oriented_height: number;
    has_icc: boolean;
  };
  preview: {
    status: PreviewStatus;
    url?: string;
    error_code?: string;
  };
}

export interface SlotEditState {
  source_id: string;
  pan_x_norm: number;
  pan_y_norm: number;
  scale: number;
  rotation_deg: number;
}

export interface EditStateModel {
  template_id: string;
  template_version: string;
  slot_edits: Record<string, SlotEditState>;
}

export interface RenderResultModel {
  output_path: string;
  template_id: string;
  canvas_size_px: [number, number];
  dpi: number;
  render_time_ms: number;
  bytes_written: number;
}

/** Result of one ingest batch (file dialog / native drop). */
export interface IngestBatchModel {
  /** Full, updated SourceRegistry list (tray). */
  sources: SourceAssetModel[];
  /** Exactly the sources of this batch, in input order, de-duplicated. */
  accepted_ids: string[];
  rejected: { display_name: string; code: string }[];
}

