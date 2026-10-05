import React from "react";
import {
  CheckmarkCircleRegular,
  WarningRegular,
  InfoRegular,
  LockClosedRegular,
  LockOpenRegular,
  RulerRegular,
  TableRegular,
  ColorRegular,
} from "@fluentui/react-icons";
import type { DraftSlot, TemplateDraft } from "../domain/draft";
import {
  updateSlotMm,
  updateCanvasMm,
  validateTemplateDraft,
} from "../domain/draft";

interface ManagerInspectorProps {
  draft: TemplateDraft;
  activeSlotId: string;
  onSelectSlot: (slotId: string) => void;
  onUpdateDraft: (updated: TemplateDraft) => void;
  isGeometryLocked?: boolean;
  onUnlockGeometry?: () => void;
  onLockGeometry?: () => void;
}

export const ManagerInspector: React.FC<ManagerInspectorProps> = ({
  draft,
  activeSlotId,
  onSelectSlot,
  onUpdateDraft,
  isGeometryLocked = false,
  onUnlockGeometry,
  onLockGeometry,
}) => {
  const activeSlot = draft.slots.find((s) => s.id === activeSlotId);
  const validation = validateTemplateDraft(draft);

  const handleCanvasChange = (
    field: "width_mm" | "height_mm" | "dpi",
    value: number
  ) => {
    if (isNaN(value) || value <= 0) return;
    const updated = updateCanvasMm(draft, { [field]: value });
    onUpdateDraft(updated);
  };

  const handleFlipOrientation = () => {
    const updated = updateCanvasMm(draft, {
      width_mm: draft.canvas.height_mm,
      height_mm: draft.canvas.width_mm,
    });
    onUpdateDraft(updated);
  };

  const handleSlotChange = (
    updates: Partial<
      Pick<
        DraftSlot,
        | "x_mm"
        | "y_mm"
        | "width_mm"
        | "height_mm"
        | "fit"
        | "allow_pan"
        | "allow_zoom"
        | "allow_rotate"
      >
    >
  ) => {
    if (!activeSlot) return;
    const updated = updateSlotMm(draft, activeSlot.id, updates);
    onUpdateDraft(updated);
  };

  const handleAddSlot = () => {
    // Generate unique ID
    let counter = draft.slots.length + 1;
    let newId = `slot_${counter}`;
    while (draft.slots.some((s) => s.id === newId)) {
      counter++;
      newId = `slot_${counter}`;
    }

    const defaultWidth = Math.min(40, draft.canvas.width_mm - 10);
    const defaultHeight = Math.min(50, draft.canvas.height_mm - 10);

    const newSlot: DraftSlot = {
      id: newId,
      x_mm: 5.0,
      y_mm: 5.0,
      width_mm: defaultWidth,
      height_mm: defaultHeight,
      rect_px: {
        left: Math.round((5.0 / 25.4) * draft.canvas.dpi),
        top: Math.round((5.0 / 25.4) * draft.canvas.dpi),
        width: Math.round((defaultWidth / 25.4) * draft.canvas.dpi),
        height: Math.round((defaultHeight / 25.4) * draft.canvas.dpi),
      },
      fit: "cover",
      allow_pan: true,
      allow_zoom: true,
      allow_rotate: false,
    };

    const nextDraft: TemplateDraft = {
      ...draft,
      slots: [...draft.slots, newSlot],
      dirty: true,
    };

    onUpdateDraft(nextDraft);
    onSelectSlot(newId);
  };

  const handleDuplicateSlot = () => {
    if (!activeSlot) return;

    let counter = draft.slots.length + 1;
    let newId = `${activeSlot.id}_copy_${counter}`;
    while (draft.slots.some((s) => s.id === newId)) {
      counter++;
      newId = `${activeSlot.id}_copy_${counter}`;
    }

    // Offset slightly so it's visible, constrained to canvas
    const newX = Math.min(
      activeSlot.x_mm + 5.0,
      draft.canvas.width_mm - activeSlot.width_mm
    );
    const newY = Math.min(
      activeSlot.y_mm + 5.0,
      draft.canvas.height_mm - activeSlot.height_mm
    );

    const newSlot: DraftSlot = {
      ...activeSlot,
      id: newId,
      x_mm: Math.max(0, newX),
      y_mm: Math.max(0, newY),
      rect_px: {
        left: Math.round((Math.max(0, newX) / 25.4) * draft.canvas.dpi),
        top: Math.round((Math.max(0, newY) / 25.4) * draft.canvas.dpi),
        width: activeSlot.rect_px.width,
        height: activeSlot.rect_px.height,
      },
    };

    const nextDraft: TemplateDraft = {
      ...draft,
      slots: [...draft.slots, newSlot],
      dirty: true,
    };

    onUpdateDraft(nextDraft);
    onSelectSlot(newId);
  };

  const handleDeleteSlot = () => {
    if (!activeSlot || draft.slots.length <= 1) return;

    const nextSlots = draft.slots.filter((s) => s.id !== activeSlot.id);
    const nextDraft: TemplateDraft = {
      ...draft,
      slots: nextSlots,
      dirty: true,
    };

    onUpdateDraft(nextDraft);
    onSelectSlot(nextSlots[0].id);
  };

  return (
    <aside
      style={{
        width: "380px",
        backgroundColor: "#0f172a",
        borderLeft: "1px solid #334155",
        display: "flex",
        flexDirection: "column",
        overflowY: "auto",
        padding: "20px",
        gap: "20px",
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          paddingBottom: "12px",
          borderBottom: "1px solid #334155",
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
            Modo Gestor • Inspeção de Template
          </div>
          <h2 style={{ fontSize: "16px", fontWeight: "700", marginTop: "2px" }}>
            {draft.name}
          </h2>
        </div>
        <div
          style={{
            fontSize: "11px",
            padding: "3px 8px",
            borderRadius: "4px",
            backgroundColor: draft.dirty ? "#b45309" : "#1e293b",
            color: draft.dirty ? "#fef3c7" : "#94a3b8",
            fontWeight: "600",
          }}
        >
          {draft.dirty ? "Modificado" : "Original"}
        </div>
      </div>

      {/* Real-time Validation Feedback */}
      <div
        style={{
          padding: "12px",
          borderRadius: "6px",
          backgroundColor: validation.valid ? "#064e3b" : "#7f1d1d",
          border: `1px solid ${validation.valid ? "#059669" : "#dc2626"}`,
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            fontWeight: "600",
            fontSize: "13px",
            color: validation.valid ? "#6ee7b7" : "#fca5a5",
          }}
        >
          {validation.valid ? (
            <CheckmarkCircleRegular style={{ fontSize: "16px" }} />
          ) : (
            <WarningRegular style={{ fontSize: "16px" }} />
          )}
          <span>
            {validation.valid
              ? "Template Válido para Produção"
              : `Erros de Validação (${validation.errors.length})`}
          </span>
        </div>
        {!validation.valid && (
          <ul
            style={{
              marginTop: "8px",
              paddingLeft: "20px",
              fontSize: "12px",
              color: "#fecaca",
            }}
          >
            {validation.errors.map((err, idx) => (
              <li key={idx} style={{ marginTop: "2px" }}>
                {err.message}
              </li>
            ))}
          </ul>
        )}
        {validation.warnings.length > 0 && (
          <div
            style={{
              marginTop: "8px",
              padding: "6px 8px",
              borderRadius: "4px",
              backgroundColor: "rgba(245, 158, 11, 0.15)",
              color: "#fcd34d",
              fontSize: "11px",
            }}
          >
            {validation.warnings.map((w, idx) => (
              <div key={idx} style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <InfoRegular style={{ fontSize: "13px", flexShrink: 0 }} />
                <span>{w}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Production Geometry Protection Banner */}
      {isGeometryLocked ? (
        <div
          style={{
            padding: "12px",
            backgroundColor: "#1e293b",
            border: "1px solid #334155",
            borderRadius: "8px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "10px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <LockClosedRegular style={{ fontSize: "18px", color: "#94a3b8" }} />
            <div>
              <div style={{ fontSize: "12px", fontWeight: "600", color: "#f8fafc" }}>
                Geometria de Produção Fixa
              </div>
              <div style={{ fontSize: "11px", color: "#94a3b8" }}>
                Gabarito físico industrial aprovado. Edição bloqueada por segurança.
              </div>
            </div>
          </div>
          {onUnlockGeometry && (
            <button
              onClick={() => {
                if (
                  window.confirm(
                    "Atenção: alterar a geometria deste gabarito físico pode invalidar facas de corte e impressões industriais aprovadas. Deseja realmente desbloquear a edição avançada?"
                  )
                ) {
                  onUnlockGeometry();
                }
              }}
              style={{
                padding: "5px 10px",
                backgroundColor: "#334155",
                border: "1px solid #475569",
                borderRadius: "4px",
                color: "#e2e8f0",
                fontSize: "11px",
                cursor: "pointer",
                fontWeight: "500",
                whiteSpace: "nowrap",
              }}
            >
              Desbloquear
            </button>
          )}
        </div>
      ) : draft.status === "production" ? (
        <div
          style={{
            padding: "10px 12px",
            backgroundColor: "rgba(245, 158, 11, 0.15)",
            border: "1px solid rgba(245, 158, 11, 0.4)",
            borderRadius: "8px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "10px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <LockOpenRegular style={{ fontSize: "18px", color: "#fcd34d" }} />
            <div>
              <div style={{ fontSize: "12px", fontWeight: "600", color: "#fcd34d" }}>
                Edição Avançada Desbloqueada
              </div>
              <div style={{ fontSize: "11px", color: "#fef3c7" }}>
                Cuidado ao modificar dimensões físicas do gabarito.
              </div>
            </div>
          </div>
          {onLockGeometry && (
            <button
              onClick={onLockGeometry}
              style={{
                padding: "4px 8px",
                backgroundColor: "#78350f",
                border: "1px solid #d97706",
                borderRadius: "4px",
                color: "#fef3c7",
                fontSize: "11px",
                cursor: "pointer",
                fontWeight: "500",
                whiteSpace: "nowrap",
              }}
            >
              Bloquear
            </button>
          )}
        </div>
      ) : null}

      {/* Section 1: Physical Paper / Canvas */}
      <div
        style={{
          padding: "14px",
          backgroundColor: "#1e293b",
          borderRadius: "8px",
          border: "1px solid #334155",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "12px",
          }}
        >
          <h3 style={{ fontSize: "13px", fontWeight: "600", color: "#e2e8f0", display: "flex", alignItems: "center", gap: "6px" }}>
            <RulerRegular style={{ fontSize: "16px" }} />
            <span>Folha Física (Canvas)</span>
          </h3>
          <button
            onClick={handleFlipOrientation}
            disabled={isGeometryLocked}
            title={isGeometryLocked ? "Geometria fixa bloqueada" : "Alternar Orientação (Paisagem / Retrato)"}
            style={{
              fontSize: "11px",
              padding: "4px 8px",
              backgroundColor: isGeometryLocked ? "#1e293b" : "#334155",
              color: isGeometryLocked ? "#64748b" : "#cbd5e1",
              borderRadius: "4px",
              cursor: isGeometryLocked ? "not-allowed" : "pointer",
              border: "1px solid #334155",
            }}
          >
            Girar Orientação
          </button>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
          <div>
            <label style={{ fontSize: "11px", color: "#94a3b8" }}>Largura (mm)</label>
            <input
              type="number"
              step="0.1"
              min="1"
              disabled={isGeometryLocked}
              value={draft.canvas.width_mm}
              onChange={(e) =>
                handleCanvasChange("width_mm", parseFloat(e.target.value))
              }
              style={{
                width: "100%",
                padding: "6px 8px",
                marginTop: "4px",
                backgroundColor: isGeometryLocked ? "#1e293b" : "#0f172a",
                border: "1px solid #334155",
                borderRadius: "4px",
                color: isGeometryLocked ? "#94a3b8" : "#ffffff",
                fontSize: "13px",
                cursor: isGeometryLocked ? "not-allowed" : "text",
              }}
            />
          </div>
          <div>
            <label style={{ fontSize: "11px", color: "#94a3b8" }}>Altura (mm)</label>
            <input
              type="number"
              step="0.1"
              min="1"
              disabled={isGeometryLocked}
              value={draft.canvas.height_mm}
              onChange={(e) =>
                handleCanvasChange("height_mm", parseFloat(e.target.value))
              }
              style={{
                width: "100%",
                padding: "6px 8px",
                marginTop: "4px",
                backgroundColor: isGeometryLocked ? "#1e293b" : "#0f172a",
                border: "1px solid #334155",
                borderRadius: "4px",
                color: isGeometryLocked ? "#94a3b8" : "#ffffff",
                fontSize: "13px",
                cursor: isGeometryLocked ? "not-allowed" : "text",
              }}
            />
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginTop: "10px" }}>
          <div>
            <label style={{ fontSize: "11px", color: "#94a3b8" }}>Resolução (DPI)</label>
            <select
              value={draft.canvas.dpi}
              disabled={isGeometryLocked}
              onChange={(e) =>
                handleCanvasChange("dpi", parseInt(e.target.value, 10))
              }
              style={{
                width: "100%",
                padding: "6px 8px",
                marginTop: "4px",
                backgroundColor: isGeometryLocked ? "#1e293b" : "#0f172a",
                border: "1px solid #334155",
                borderRadius: "4px",
                color: isGeometryLocked ? "#94a3b8" : "#ffffff",
                fontSize: "13px",
                cursor: isGeometryLocked ? "not-allowed" : "pointer",
              }}
            >
              <option value="150">150 DPI (Rascunho)</option>
              <option value="254">254 DPI (10 px/mm - Padrão)</option>
              <option value="300">300 DPI (Offset / Fine Art)</option>
              <option value="600">600 DPI (Alta Densidade)</option>
            </select>
          </div>
          <div>
            <label style={{ fontSize: "11px", color: "#94a3b8" }}>Pixels Derivados</label>
            <div
              style={{
                padding: "7px 8px",
                marginTop: "4px",
                backgroundColor: "#0b0f19",
                borderRadius: "4px",
                color: "#64748b",
                fontSize: "12px",
                fontFamily: "monospace",
              }}
            >
              {draft.canvas_px.width} × {draft.canvas_px.height} px
            </div>
          </div>
        </div>
      </div>

      {/* Section 2: Slots List & Active Slot Inspector */}
      <div
        style={{
          padding: "14px",
          backgroundColor: "#1e293b",
          borderRadius: "8px",
          border: "1px solid #334155",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "10px",
          }}
        >
          <h3 style={{ fontSize: "13px", fontWeight: "600", color: "#e2e8f0", display: "flex", alignItems: "center", gap: "6px" }}>
            <TableRegular style={{ fontSize: "16px" }} />
            <span>Slots ({draft.slots.length})</span>
          </h3>
          <button
            onClick={handleAddSlot}
            disabled={isGeometryLocked}
            style={{
              fontSize: "11px",
              padding: "4px 8px",
              backgroundColor: isGeometryLocked ? "#1e293b" : "#2563eb",
              color: isGeometryLocked ? "#64748b" : "#ffffff",
              borderRadius: "4px",
              cursor: isGeometryLocked ? "not-allowed" : "pointer",
              border: "1px solid #334155",
            }}
          >
            + Adicionar Slot
          </button>
        </div>

        {/* Slot Selection Tabs */}
        <div
          style={{
            display: "flex",
            gap: "4px",
            overflowX: "auto",
            paddingBottom: "8px",
            marginBottom: "12px",
          }}
        >
          {draft.slots.map((s) => {
            const isSelected = s.id === activeSlotId;
            return (
              <button
                key={s.id}
                onClick={() => onSelectSlot(s.id)}
                style={{
                  padding: "4px 8px",
                  borderRadius: "4px",
                  backgroundColor: isSelected ? "#3b82f6" : "#0f172a",
                  color: isSelected ? "#ffffff" : "#94a3b8",
                  fontSize: "11px",
                  border: isSelected ? "1px solid #60a5fa" : "1px solid #334155",
                  whiteSpace: "nowrap",
                }}
              >
                {s.id}
              </button>
            );
          })}
        </div>

        {activeSlot ? (
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            <div style={{ fontSize: "12px", color: "#60a5fa", fontWeight: "600" }}>
              Editando Slot: {activeSlot.id}
            </div>

            {/* Position X, Y (mm) */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
              <div>
                <label style={{ fontSize: "11px", color: "#94a3b8" }}>Posição X (mm)</label>
                <input
                  type="number"
                  step="0.1"
                  disabled={isGeometryLocked}
                  value={activeSlot.x_mm}
                  onChange={(e) =>
                    handleSlotChange({ x_mm: parseFloat(e.target.value) || 0 })
                  }
                  style={{
                    width: "100%",
                    padding: "6px 8px",
                    marginTop: "4px",
                    backgroundColor: isGeometryLocked ? "#1e293b" : "#0f172a",
                    border: "1px solid #334155",
                    borderRadius: "4px",
                    color: isGeometryLocked ? "#94a3b8" : "#ffffff",
                    fontSize: "13px",
                    cursor: isGeometryLocked ? "not-allowed" : "text",
                  }}
                />
              </div>
              <div>
                <label style={{ fontSize: "11px", color: "#94a3b8" }}>Posição Y (mm)</label>
                <input
                  type="number"
                  step="0.1"
                  disabled={isGeometryLocked}
                  value={activeSlot.y_mm}
                  onChange={(e) =>
                    handleSlotChange({ y_mm: parseFloat(e.target.value) || 0 })
                  }
                  style={{
                    width: "100%",
                    padding: "6px 8px",
                    marginTop: "4px",
                    backgroundColor: isGeometryLocked ? "#1e293b" : "#0f172a",
                    border: "1px solid #334155",
                    borderRadius: "4px",
                    color: isGeometryLocked ? "#94a3b8" : "#ffffff",
                    fontSize: "13px",
                    cursor: isGeometryLocked ? "not-allowed" : "text",
                  }}
                />
              </div>
            </div>

            {/* Size Width, Height (mm) */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
              <div>
                <label style={{ fontSize: "11px", color: "#94a3b8" }}>Largura (mm)</label>
                <input
                  type="number"
                  step="0.1"
                  min="1"
                  disabled={isGeometryLocked}
                  value={activeSlot.width_mm}
                  onChange={(e) =>
                    handleSlotChange({ width_mm: parseFloat(e.target.value) || 1 })
                  }
                  style={{
                    width: "100%",
                    padding: "6px 8px",
                    marginTop: "4px",
                    backgroundColor: isGeometryLocked ? "#1e293b" : "#0f172a",
                    border: "1px solid #334155",
                    borderRadius: "4px",
                    color: isGeometryLocked ? "#94a3b8" : "#ffffff",
                    fontSize: "13px",
                    cursor: isGeometryLocked ? "not-allowed" : "text",
                  }}
                />
              </div>
              <div>
                <label style={{ fontSize: "11px", color: "#94a3b8" }}>Altura (mm)</label>
                <input
                  type="number"
                  step="0.1"
                  min="1"
                  disabled={isGeometryLocked}
                  value={activeSlot.height_mm}
                  onChange={(e) =>
                    handleSlotChange({ height_mm: parseFloat(e.target.value) || 1 })
                  }
                  style={{
                    width: "100%",
                    padding: "6px 8px",
                    marginTop: "4px",
                    backgroundColor: isGeometryLocked ? "#1e293b" : "#0f172a",
                    border: "1px solid #334155",
                    borderRadius: "4px",
                    color: isGeometryLocked ? "#94a3b8" : "#ffffff",
                    fontSize: "13px",
                    cursor: isGeometryLocked ? "not-allowed" : "text",
                  }}
                />
              </div>
            </div>

            {/* Fit mode */}
            <div>
              <label style={{ fontSize: "11px", color: "#94a3b8" }}>
                Enquadramento Padrão (Fit)
              </label>
              <select
                value={activeSlot.fit}
                onChange={(e) => handleSlotChange({ fit: e.target.value })}
                style={{
                  width: "100%",
                  padding: "6px 8px",
                  marginTop: "4px",
                  backgroundColor: "#0f172a",
                  border: "1px solid #334155",
                  borderRadius: "4px",
                  color: "#ffffff",
                  fontSize: "13px",
                }}
              >
                <option value="cover">Cover (Preencher cortando excedente)</option>
                <option value="fit">Fit (Conter na área mantendo tudo visível)</option>
              </select>
            </div>

            {/* Operator permissions */}
            <div>
              <label style={{ fontSize: "11px", color: "#94a3b8", display: "block", marginBottom: "6px" }}>
                Permissões do Operador
              </label>
              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                <label style={{ fontSize: "12px", display: "flex", alignItems: "center", gap: "8px", cursor: "pointer" }}>
                  <input
                    type="checkbox"
                    checked={activeSlot.allow_pan}
                    onChange={(e) => handleSlotChange({ allow_pan: e.target.checked })}
                  />
                  Permitir mover foto (Pan)
                </label>
                <label style={{ fontSize: "12px", display: "flex", alignItems: "center", gap: "8px", cursor: "pointer" }}>
                  <input
                    type="checkbox"
                    checked={activeSlot.allow_zoom}
                    onChange={(e) => handleSlotChange({ allow_zoom: e.target.checked })}
                  />
                  Permitir alterar zoom
                </label>
                <label style={{ fontSize: "12px", display: "flex", alignItems: "center", gap: "8px", cursor: "pointer" }}>
                  <input
                    type="checkbox"
                    checked={activeSlot.allow_rotate}
                    onChange={(e) => handleSlotChange({ allow_rotate: e.target.checked })}
                  />
                  Permitir rotação
                </label>
              </div>
            </div>

            {/* Slot Actions */}
            <div style={{ display: "flex", gap: "8px", marginTop: "4px" }}>
              <button
                onClick={handleDuplicateSlot}
                disabled={isGeometryLocked}
                style={{
                  flex: 1,
                  padding: "6px 10px",
                  backgroundColor: isGeometryLocked ? "#1e293b" : "#334155",
                  color: isGeometryLocked ? "#64748b" : "#f8fafc",
                  fontSize: "12px",
                  borderRadius: "4px",
                  cursor: isGeometryLocked ? "not-allowed" : "pointer",
                  border: "1px solid #334155",
                }}
              >
                Duplicar Slot
              </button>
              <button
                onClick={handleDeleteSlot}
                disabled={isGeometryLocked || draft.slots.length <= 1}
                style={{
                  padding: "6px 10px",
                  backgroundColor:
                    isGeometryLocked || draft.slots.length <= 1 ? "#1e293b" : "#7f1d1d",
                  color:
                    isGeometryLocked || draft.slots.length <= 1 ? "#64748b" : "#fca5a5",
                  fontSize: "12px",
                  borderRadius: "4px",
                  cursor: isGeometryLocked || draft.slots.length <= 1 ? "not-allowed" : "pointer",
                  border: "1px solid #334155",
                }}
              >
                Remover
              </button>
            </div>
          </div>
        ) : (
          <div style={{ fontSize: "12px", color: "#64748b" }}>
            Nenhum slot selecionado.
          </div>
        )}
      </div>

      {/* Section 3: Overlay (PNG) */}
      <div
        style={{
          padding: "14px",
          backgroundColor: "#1e293b",
          borderRadius: "8px",
          border: "1px solid #334155",
        }}
      >
        <h3 style={{ fontSize: "13px", fontWeight: "600", color: "#e2e8f0", marginBottom: "8px", display: "flex", alignItems: "center", gap: "6px" }}>
          <ColorRegular style={{ fontSize: "16px" }} />
          <span>Máscara / Overlay</span>
        </h3>
        {draft.overlay ? (
          <div style={{ fontSize: "12px", color: "#94a3b8" }}>
            <div>
              <span style={{ color: "#cbd5e1", fontWeight: "500" }}>Arquivo: </span>
              <code style={{ fontSize: "11px", backgroundColor: "#0f172a", padding: "2px 4px", borderRadius: "3px" }}>
                {draft.overlay.path}
              </code>
            </div>
          </div>
        ) : (
          <div style={{ fontSize: "12px", color: "#64748b" }}>
            Sem máscara configurada para este produto.
          </div>
        )}
      </div>
    </aside>
  );
};
