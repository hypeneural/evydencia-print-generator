import React, { useState, useEffect } from "react";
import type { TemplateDraft } from "../domain/draft";
import { validateTemplateDraft } from "../domain/draft";
import {
  computeNextVersion,
  suggestBumpType,
  type BumpType,
} from "../domain/publish";
import type { TemplateModel } from "../domain/types";
import { bridge } from "../bridge/api";

interface PublishTemplateModalProps {
  isOpen: boolean;
  onClose: () => void;
  draft: TemplateDraft;
  originalTemplate: TemplateModel | null;
  onPublishSuccess: (
    updatedTemplate: TemplateModel,
    updatedTemplates: TemplateModel[]
  ) => void;
}

export const PublishTemplateModal: React.FC<PublishTemplateModalProps> = ({
  isOpen,
  onClose,
  draft,
  originalTemplate,
  onPublishSuccess,
}) => {
  const [bumpType, setBumpType] = useState<BumpType>("minor");
  const [notes, setNotes] = useState<string>("");
  const [publishing, setPublishing] = useState<boolean>(false);
  const [publishError, setPublishError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      setBumpType(suggestBumpType(originalTemplate, draft));
      setNotes("");
      setPublishError(null);
      setPublishing(false);
    }
  }, [isOpen, originalTemplate, draft]);

  if (!isOpen) return null;

  const validation = validateTemplateDraft(draft);
  const currentVersion = draft.template_version || "1.0.0";
  const nextVersion = computeNextVersion(currentVersion, bumpType);

  const handlePublish = async () => {
    if (!validation.valid || publishing) return;

    setPublishing(true);
    setPublishError(null);

    try {
      const res = await bridge.publishTemplate(draft, bumpType, notes);
      if (res.success && res.template && res.templates) {
        onPublishSuccess(res.template, res.templates);
        onClose();
      } else {
        const errorDetail =
          res.issues && res.issues.length > 0
            ? `${res.error}: ${res.issues.join("; ")}`
            : res.error || "Erro desconhecido ao publicar template.";
        setPublishError(errorDetail);
      }
    } catch (err: unknown) {
      setPublishError(err instanceof Error ? err.message : String(err));
    } finally {
      setPublishing(false);
    }
  };

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(0, 0, 0, 0.75)",
        backdropFilter: "blur(4px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 9999,
        padding: "20px",
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget && !publishing) onClose();
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "520px",
          backgroundColor: "#0f172a",
          border: "1px solid #334155",
          borderRadius: "12px",
          boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.5)",
          overflow: "hidden",
          display: "flex",
          flexDirection: "column",
        }}
      >
        {/* Modal Header */}
        <div
          style={{
            padding: "18px 24px",
            borderBottom: "1px solid #334155",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            backgroundColor: "#1e293b",
          }}
        >
          <div>
            <div
              style={{
                fontSize: "11px",
                color: "#38bdf8",
                textTransform: "uppercase",
                fontWeight: "700",
                letterSpacing: "0.5px",
              }}
            >
              Governança de Templates • Marco M5-B
            </div>
            <h3
              style={{
                fontSize: "17px",
                fontWeight: "700",
                color: "#f8fafc",
                marginTop: "2px",
              }}
            >
              Publicar Nova Versão em Disco
            </h3>
          </div>
          <button
            onClick={onClose}
            disabled={publishing}
            style={{
              background: "none",
              border: "none",
              color: "#94a3b8",
              fontSize: "20px",
              cursor: publishing ? "not-allowed" : "pointer",
              padding: "4px 8px",
              borderRadius: "4px",
            }}
          >
            ✕
          </button>
        </div>

        {/* Modal Content */}
        <div
          style={{
            padding: "20px 24px",
            display: "flex",
            flexDirection: "column",
            gap: "16px",
          }}
        >
          {/* Target Product Badge */}
          <div
            style={{
              padding: "10px 14px",
              backgroundColor: "#1e293b",
              borderRadius: "8px",
              border: "1px solid #334155",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <div>
              <div
                style={{
                  fontSize: "13px",
                  fontWeight: "600",
                  color: "#f8fafc",
                }}
              >
                {draft.name}
              </div>
              <div style={{ fontSize: "11px", color: "#64748b" }}>
                ID: <code>{draft.id}</code>
              </div>
            </div>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                fontSize: "12px",
              }}
            >
              <span
                style={{
                  color: "#94a3b8",
                  backgroundColor: "#0f172a",
                  padding: "3px 8px",
                  borderRadius: "4px",
                }}
              >
                v{currentVersion}
              </span>
              <span style={{ color: "#38bdf8", fontWeight: "bold" }}>➔</span>
              <span
                style={{
                  color: "#38bdf8",
                  backgroundColor: "#0c4a6e",
                  padding: "3px 8px",
                  borderRadius: "4px",
                  fontWeight: "700",
                }}
              >
                v{nextVersion}
              </span>
            </div>
          </div>

          {/* Semver Bump Choice */}
          <div>
            <label
              style={{
                fontSize: "12px",
                fontWeight: "600",
                color: "#cbd5e1",
                display: "block",
                marginBottom: "8px",
              }}
            >
              Tipo de Incremento Semântico:
            </label>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "8px" }}>
              {(
                [
                  { type: "patch", label: "Patch", desc: "Ajuste fino / slots" },
                  { type: "minor", label: "Minor", desc: "Slots ou tamanho" },
                  { type: "major", label: "Major", desc: "Redesenho total" },
                ] as const
              ).map(({ type, label, desc }) => {
                const isSelected = bumpType === type;
                return (
                  <button
                    key={type}
                    type="button"
                    onClick={() => setBumpType(type)}
                    style={{
                      padding: "8px 10px",
                      borderRadius: "6px",
                      border: `1px solid ${isSelected ? "#38bdf8" : "#334155"}`,
                      backgroundColor: isSelected ? "#0c4a6e" : "#1e293b",
                      color: isSelected ? "#ffffff" : "#94a3b8",
                      cursor: "pointer",
                      textAlign: "left",
                    }}
                  >
                    <div style={{ fontSize: "13px", fontWeight: "700" }}>{label}</div>
                    <div style={{ fontSize: "10px", opacity: 0.85, marginTop: "2px" }}>
                      {desc}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Change Summary */}
          <div
            style={{
              padding: "12px 14px",
              backgroundColor: "#1e293b",
              borderRadius: "8px",
              border: "1px solid #334155",
              fontSize: "12px",
              display: "flex",
              flexDirection: "column",
              gap: "6px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "#94a3b8" }}>Folha Física:</span>
              <strong style={{ color: "#f8fafc" }}>
                {draft.canvas.width_mm} × {draft.canvas.height_mm} mm ({draft.canvas.dpi} DPI)
              </strong>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "#94a3b8" }}>Slots de Foto:</span>
              <strong style={{ color: "#f8fafc" }}>
                {draft.slots.length} slot(s)
              </strong>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "#94a3b8" }}>Máscara / Overlay:</span>
              <span style={{ color: draft.overlay ? "#38bdf8" : "#64748b" }}>
                {draft.overlay ? draft.overlay.path : "Nenhuma"}
              </span>
            </div>
          </div>

          {/* Physical Validation Status */}
          <div
            style={{
              padding: "10px 14px",
              borderRadius: "6px",
              backgroundColor: validation.valid ? "#064e3b" : "#7f1d1d",
              border: `1px solid ${validation.valid ? "#059669" : "#dc2626"}`,
              fontSize: "12px",
              color: validation.valid ? "#6ee7b7" : "#fca5a5",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <span>{validation.valid ? "✓" : "⚠️"}</span>
            <span>
              {validation.valid
                ? "Geometria e regras físicas 100% validadas para produção."
                : `Existem ${validation.errors.length} erro(s) de validação impedindo a publicação.`}
            </span>
          </div>

          {/* Notes Input */}
          <div>
            <label
              style={{
                fontSize: "12px",
                color: "#cbd5e1",
                display: "block",
                marginBottom: "6px",
              }}
            >
              Notas de Auditoria (opcional):
            </label>
            <input
              type="text"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Ex: Ajuste fino do slot principal para centralização"
              style={{
                width: "100%",
                padding: "8px 12px",
                borderRadius: "6px",
                backgroundColor: "#1e293b",
                border: "1px solid #334155",
                color: "#f8fafc",
                fontSize: "13px",
              }}
            />
          </div>

          {/* Error Message if API fails */}
          {publishError && (
            <div
              style={{
                padding: "10px 12px",
                borderRadius: "6px",
                backgroundColor: "#7f1d1d",
                border: "1px solid #dc2626",
                color: "#fecaca",
                fontSize: "12px",
              }}
            >
              ⚠️ {publishError}
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div
          style={{
            padding: "16px 24px",
            borderTop: "1px solid #334155",
            display: "flex",
            justifyContent: "flex-end",
            gap: "12px",
            backgroundColor: "#1e293b",
          }}
        >
          <button
            type="button"
            className="btn-secondary"
            onClick={onClose}
            disabled={publishing}
            style={{ fontSize: "13px" }}
          >
            Cancelar
          </button>
          <button
            type="button"
            className="btn-success"
            onClick={handlePublish}
            disabled={publishing || !validation.valid}
            style={{
              fontSize: "13px",
              padding: "8px 20px",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            {publishing ? (
              <>Gravando em Disco...</>
            ) : (
              <>🚀 Publicar Versão v{nextVersion}</>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
