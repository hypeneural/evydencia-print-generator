import { describe, it, expect } from "vitest";
import {
  extractClientLabel,
  buildKeychainHeaderText,
  cleanWordName,
} from "./keychain_labels";
import type { TemplateModel, EditStateModel, SourceAssetModel } from "./types";

describe("keychain_labels", () => {
  describe("cleanWordName", () => {
    it("handles accented names like JOÃO, LAÍS", () => {
      expect(cleanWordName("joão")).toBe("JOÃO");
      expect(cleanWordName("Laís")).toBe("LAÍS");
      expect(cleanWordName("Ana Paula")).toBe("ANA PAULA");
      expect(cleanWordName("Maria da Silva")).toBe("MARIA");
    });

    it("strips noise words like pedido, cliente, foto", () => {
      expect(cleanWordName("cliente joao")).toBe("JOAO");
      expect(cleanWordName("pedido 123 maria")).toBe("MARIA");
      expect(cleanWordName("foto teste")).toBe("TESTE");
    });
  });

  describe("extractClientLabel", () => {
    it("matches EvydFlow 4-part folder: Nome - Telefone - Pacote - ID", () => {
      expect(extractClientLabel("João Silva - 11999999999 - Pacote 1 - 1510.jpg")).toBe("JOÃO 1510");
    });

    it("matches ID - Nome pattern", () => {
      expect(extractClientLabel("1510 - João")).toBe("JOÃO 1510");
      expect(extractClientLabel("4545_Maria")).toBe("MARIA 4545");
    });

    it("matches Nome ID pattern", () => {
      expect(extractClientLabel("JOÃO 1510")).toBe("JOÃO 1510");
      expect(extractClientLabel("MARIA 4545.png")).toBe("MARIA 4545");
      expect(extractClientLabel("LAIS 1010")).toBe("LAIS 1010");
    });

    it("matches Pedido #ID - Nome pattern", () => {
      expect(extractClientLabel("Pedido #9999 - Carlos")).toBe("CARLOS 9999");
    });

    it("falls back to uppercase name when no ID", () => {
      expect(extractClientLabel("Mariana.jpg")).toBe("MARIANA");
    });
  });

  describe("buildKeychainHeaderText", () => {
    const mockTemplate: TemplateModel = {
      id: "chaveiro-3x4",
      template_version: "1.0.0",
      name: "Chaveiro 3x4",
      status: "production",
      canvas: { width_mm: 216, height_mm: 152, dpi: 300 },
      canvas_px: { width: 2551, height: 1795 },
      slots: [
        {
          id: "slot_01",
          x_mm: 6,
          y_mm: 10,
          width_mm: 34,
          height_mm: 44,
          rect_px: { left: 71, top: 118, width: 402, height: 520 },
          fit: "cover",
          allow_pan: true,
          allow_zoom: true,
          allow_rotate: true,
        },
        {
          id: "slot_02",
          x_mm: 40,
          y_mm: 10,
          width_mm: 34,
          height_mm: 44,
          rect_px: { left: 472, top: 118, width: 402, height: 520 },
          fit: "cover",
          allow_pan: true,
          allow_zoom: true,
          allow_rotate: true,
        },
        {
          id: "slot_03",
          x_mm: 74,
          y_mm: 10,
          width_mm: 34,
          height_mm: 44,
          rect_px: { left: 874, top: 118, width: 402, height: 520 },
          fit: "cover",
          allow_pan: true,
          allow_zoom: true,
          allow_rotate: true,
        },
      ],
      overlay: null,
    };

    const sources: SourceAssetModel[] = [
      {
        id: "s1",
        display_name: "1510 - João.jpg",
        client_label: "JOÃO 1510",
        probe: { format: "jpeg", width: 1000, height: 1000, oriented_width: 1000, oriented_height: 1000, has_icc: false },
        preview: { status: "ready" },
      },
      {
        id: "s2",
        display_name: "MARIA 4545.jpg",
        client_label: "MARIA 4545",
        probe: { format: "jpeg", width: 1000, height: 1000, oriented_width: 1000, oriented_height: 1000, has_icc: false },
        preview: { status: "ready" },
      },
      {
        id: "s3",
        display_name: "outro_arquivo_joao.jpg",
        client_label: "JOÃO 1510",
        probe: { format: "jpeg", width: 1000, height: 1000, oriented_width: 1000, oriented_height: 1000, has_icc: false },
        preview: { status: "ready" },
      },
    ];

    it("deduplicates client labels preserving slot order", () => {
      const editState: EditStateModel = {
        template_id: "chaveiro-3x4",
        template_version: "1.0.0",
        slot_edits: {
          slot_01: { source_id: "s1", pan_x_norm: 0, pan_y_norm: 0, scale: 1, rotation_deg: 0 },
          slot_02: { source_id: "s2", pan_x_norm: 0, pan_y_norm: 0, scale: 1, rotation_deg: 0 },
          slot_03: { source_id: "s3", pan_x_norm: 0, pan_y_norm: 0, scale: 1, rotation_deg: 0 },
        },
      };

      const header = buildKeychainHeaderText(mockTemplate, editState, sources);
      expect(header).toBe("JOÃO 1510 | MARIA 4545");
    });

    it("returns empty string for non-keychain templates", () => {
      const globoTemplate = { ...mockTemplate, id: "globo-neve" };
      const editState: EditStateModel = {
        template_id: "globo-neve",
        template_version: "1.0.0",
        slot_edits: {
          slot_01: { source_id: "s1", pan_x_norm: 0, pan_y_norm: 0, scale: 1, rotation_deg: 0 },
        },
      };
      expect(buildKeychainHeaderText(globoTemplate, editState, sources)).toBe("");
    });
  });
});
