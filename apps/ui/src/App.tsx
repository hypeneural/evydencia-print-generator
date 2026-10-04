import React, { useEffect, useState, useMemo, useRef, useCallback } from "react";
import { bridge } from "./bridge/api";
import { ProductCanvas } from "./components/ProductCanvas";
import { ManagerInspector } from "./components/ManagerInspector";
import { createHistoryManager } from "./domain/history";
import { duplicateSlot } from "./domain/duplication";
import type { PreviewLayout } from "./domain/layout";
import { computePreviewLayout } from "./domain/layout";
import type { SlotTransform } from "./domain/transform";
import { clampTransform } from "./domain/transform";
import type {
  EditStateModel,
  RenderResultModel,
  SourceAssetModel,
  TemplateModel,
} from "./domain/types";
import type { DraftSlot, TemplateDraft } from "./domain/draft";
import { createDraftFromTemplate, updateSlotMm } from "./domain/draft";

const DEFAULT_TRANSFORM: SlotTransform = {
  pan_x_norm: 0.0,
  pan_y_norm: 0.0,
  scale: 1.0,
  rotation_deg: 0.0,
};

export const App: React.FC = () => {
  const [mode, setMode] = useState<"operator" | "manager">("operator");
  const [templates, setTemplates] = useState<TemplateModel[]>([]);
  const [template, setTemplate] = useState<TemplateModel | null>(null);
  const [draft, setDraft] = useState<TemplateDraft | null>(null);
  const [sources, setSources] = useState<SourceAssetModel[]>([]);
  const [activeSlotId, setActiveSlotId] = useState<string>("");
  const [editState, setEditState] = useState<EditStateModel | null>(null);
  const [rendering, setRendering] = useState(false);
  const [renderResult, setRenderResult] = useState<RenderResultModel | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const canvasContainerRef = useRef<HTMLDivElement | null>(null);
  const [previewLayout, setPreviewLayout] = useState<PreviewLayout>({
    fitScale: 1.0,
    displayWidth: 1067,
    displayHeight: 1474,
  });

  // History manager ref
  const historyRef = useRef<ReturnType<typeof createHistoryManager> | null>(null);

  // Load templates & initial sources
  useEffect(() => {
    async function init() {
      try {
        const [availableTemplates, initialSources] = await Promise.all([
          bridge.getTemplates(),
          bridge.getSources(),
        ]);
        setTemplates(availableTemplates);
        setSources(initialSources);

        if (availableTemplates.length > 0) {
          const tpl = availableTemplates[0];
          setTemplate(tpl);
          setDraft(createDraftFromTemplate(tpl));
          const firstSlotId = tpl.slots[0]?.id || "";
          setActiveSlotId(firstSlotId);

          const initialEdit: EditStateModel = {
            template_id: tpl.id,
            template_version: tpl.template_version,
            slot_edits: {},
          };

          if (initialSources.length > 0 && firstSlotId) {
            initialEdit.slot_edits[firstSlotId] = {
              source_id: initialSources[0].id,
              pan_x_norm: 0.0,
              pan_y_norm: 0.0,
              scale: 1.0,
              rotation_deg: 0.0,
            };
          }

          setEditState(initialEdit);
          historyRef.current = createHistoryManager(initialEdit);
        }
      } catch (err: unknown) {
        setErrorMessage(err instanceof Error ? err.message : String(err));
      }
    }
    init();
  }, []);

  // Poll bridge for preview readiness if any asset is pending (Gate 1 & 4)
  useEffect(() => {
    const hasPending = sources.some(
      (s) => (s.preview.status !== "ready" && s.preview.status !== "error") || !s.preview.url
    );
    if (!hasPending) return;

    const interval = setInterval(async () => {
      try {
        const updated = await bridge.getSources();
        setSources(updated);

        // Auto-assign first source to active slot if empty
        setEditState((prevEdit) => {
          if (!prevEdit || Object.keys(prevEdit.slot_edits).length > 0) return prevEdit;
          if (updated.length > 0 && activeSlotId) {
            const nextEdit: EditStateModel = {
              ...prevEdit,
              slot_edits: {
                [activeSlotId]: {
                  source_id: updated[0].id,
                  pan_x_norm: 0.0,
                  pan_y_norm: 0.0,
                  scale: 1.0,
                  rotation_deg: 0.0,
                },
              },
            };
            if (historyRef.current) {
              historyRef.current = createHistoryManager(nextEdit);
            }
            return nextEdit;
          }
          return prevEdit;
        });
      } catch (e) {
        console.warn("Failed to poll sources:", e);
      }
    }, 250);

    return () => clearInterval(interval);
  }, [sources, activeSlotId]);

  // Switch template
  const handleSwitchTemplate = (tpl: TemplateModel) => {
    if (tpl.id === template?.id) return;
    setTemplate(tpl);
    setDraft(createDraftFromTemplate(tpl));
    const firstSlot = tpl.slots[0]?.id || "";
    setActiveSlotId(firstSlot);

    // If existing edit has current slot photo, we can carry over if applicable, or start fresh
    const newEditState: EditStateModel = {
      template_id: tpl.id,
      template_version: tpl.template_version,
      slot_edits: {},
    };

    // Auto-assign first source to first slot if available
    if (sources.length > 0 && firstSlot) {
      newEditState.slot_edits[firstSlot] = {
        source_id: sources[0].id,
        pan_x_norm: 0.0,
        pan_y_norm: 0.0,
        scale: 1.0,
        rotation_deg: 0.0,
      };
    }

    setEditState(newEditState);
    historyRef.current = createHistoryManager(newEditState);
    setRenderResult(null);
    setErrorMessage(null);
  };

  // Draft slot change handler (Manager mode)
  const handleDraftSlotChange = useCallback(
    (slotId: string, updatedSlot: DraftSlot) => {
      setDraft((prevDraft) => {
        if (!prevDraft) return prevDraft;
        return updateSlotMm(prevDraft, slotId, {
          x_mm: updatedSlot.x_mm,
          y_mm: updatedSlot.y_mm,
          width_mm: updatedSlot.width_mm,
          height_mm: updatedSlot.height_mm,
        });
      });
    },
    []
  );

  // Compute fitted display dimensions preserving physical aspect ratio
  useEffect(() => {
    function updateLayout() {
      if (!canvasContainerRef.current || !template) return;
      const { clientWidth, clientHeight } = canvasContainerRef.current;
      if (clientWidth <= 0 || clientHeight <= 0) return;
      const wPx =
        mode === "manager" && draft
          ? draft.canvas_px.width
          : template.canvas_px.width;
      const hPx =
        mode === "manager" && draft
          ? draft.canvas_px.height
          : template.canvas_px.height;
      const l = computePreviewLayout(
        wPx,
        hPx,
        clientWidth,
        clientHeight,
        48
      );
      setPreviewLayout(l);
    }
    updateLayout();
    window.addEventListener("resize", updateLayout);
    let observer: ResizeObserver | null = null;
    if (canvasContainerRef.current) {
      observer = new ResizeObserver(updateLayout);
      observer.observe(canvasContainerRef.current);
    }
    return () => {
      window.removeEventListener("resize", updateLayout);
      if (observer) observer.disconnect();
    };
  }, [template, draft, mode]);

  // Current active slot & transform
  const activeSlot = useMemo(() => {
    if (mode === "manager" && draft) {
      return draft.slots.find((s) => s.id === activeSlotId) || draft.slots[0] || null;
    }
    if (!template) return null;
    return template.slots.find((s) => s.id === activeSlotId) || template.slots[0] || null;
  }, [template, activeSlotId, mode, draft]);

  const currentSlotEdit = useMemo(() => {
    if (!editState || !activeSlotId) return null;
    return editState.slot_edits[activeSlotId] || null;
  }, [editState, activeSlotId]);

  const activeAsset = useMemo(() => {
    if (!currentSlotEdit) return null;
    return sources.find((s) => s.id === currentSlotEdit.source_id) || null;
  }, [sources, currentSlotEdit]);

  const currentTransform: SlotTransform = useMemo(() => {
    if (!currentSlotEdit) return DEFAULT_TRANSFORM;
    return {
      pan_x_norm: currentSlotEdit.pan_x_norm,
      pan_y_norm: currentSlotEdit.pan_y_norm,
      scale: currentSlotEdit.scale,
      rotation_deg: currentSlotEdit.rotation_deg,
    };
  }, [currentSlotEdit]);

  // Handle Transform change (from drag, wheel, or buttons)
  const handleTransformChange = useCallback(
    (slotId: string, nextTransform: SlotTransform, commitToHistory: boolean) => {
      if (!editState) return;
      const existing = editState.slot_edits[slotId];
      if (!existing) return;

      const updatedEditState: EditStateModel = {
        ...editState,
        slot_edits: {
          ...editState.slot_edits,
          [slotId]: {
            ...existing,
            pan_x_norm: nextTransform.pan_x_norm,
            pan_y_norm: nextTransform.pan_y_norm,
            scale: nextTransform.scale,
            rotation_deg: nextTransform.rotation_deg,
          },
        },
      };

      setEditState(updatedEditState);
      if (commitToHistory && historyRef.current) {
        historyRef.current.push(updatedEditState);
      }
    },
    [editState]
  );

  // Undo / Redo
  const handleUndo = useCallback(() => {
    if (!historyRef.current || !historyRef.current.canUndo) return;
    const previous = historyRef.current.undo();
    if (previous) {
      setEditState(previous);
    }
  }, []);

  const handleRedo = useCallback(() => {
    if (!historyRef.current || !historyRef.current.canRedo) return;
    const next = historyRef.current.redo();
    if (next) {
      setEditState(next);
    }
  }, []);

  // Keyboard shortcuts (Ctrl+Z, Ctrl+Y)
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && !e.shiftKey && e.key.toLowerCase() === "z") {
        e.preventDefault();
        handleUndo();
      } else if (
        (e.ctrlKey || e.metaKey) &&
        (e.key.toLowerCase() === "y" || (e.shiftKey && e.key.toLowerCase() === "z"))
      ) {
        e.preventDefault();
        handleRedo();
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleUndo, handleRedo]);

  // Set photo to active slot
  const handleSelectSource = (asset: SourceAssetModel) => {
    if (!editState || !activeSlotId) return;

    const nextState: EditStateModel = {
      ...editState,
      slot_edits: {
        ...editState.slot_edits,
        [activeSlotId]: {
          source_id: asset.id,
          pan_x_norm: 0.0,
          pan_y_norm: 0.0,
          scale: 1.0,
          rotation_deg: 0.0,
        },
      },
    };
    setEditState(nextState);
    if (historyRef.current) {
      historyRef.current.push(nextState);
    }
  };

  // Batch action: Duplicate photo across slots in Globo
  const handleDuplicateGloboSlot = () => {
    if (!editState || !template || template.slots.length < 2) return;
    const slot1Edit = editState.slot_edits["foto_1"];
    const slot2Edit = editState.slot_edits["foto_2"];

    const sourceEdit = activeSlotId === "foto_2" ? (slot2Edit || slot1Edit) : (slot1Edit || slot2Edit);
    if (!sourceEdit) return;

    const nextState: EditStateModel = {
      ...editState,
      slot_edits: {
        ...editState.slot_edits,
        foto_1: { ...sourceEdit },
        foto_2: { ...sourceEdit },
      },
    };
    setEditState(nextState);
    if (historyRef.current) {
      historyRef.current.push(nextState);
    }
  };

  // Double-click handler per product (M4-D, M4-E)
  const handleDoubleClickSlot = useCallback(
    (slotId: string) => {
      if (!editState || !template) return;

      const slotIds = template.slots.map((s) => s.id);
      const res = duplicateSlot(template.id, slotIds, slotId, editState.slot_edits);
      if (res) {
        const nextState: EditStateModel = {
          ...editState,
          slot_edits: res.nextSlotEdits,
        };
        setEditState(nextState);
        setActiveSlotId(res.targetSlotId);
        if (historyRef.current) {
          historyRef.current.push(nextState);
        }
      } else {
        // Calendário or generic: focus slot
        setActiveSlotId(slotId);
      }
    },
    [editState, template]
  );

  // Batch action: Duplicate active slot to next slot in Chaveiro
  const handleDuplicateToNextSlot = useCallback(() => {
    if (!activeSlotId) return;
    handleDoubleClickSlot(activeSlotId);
  }, [activeSlotId, handleDoubleClickSlot]);

  // Batch action: Fill all slots in Chaveiro
  const handleFillAllSlots = () => {
    if (!editState || !template) return;
    const baseEdit = currentSlotEdit || Object.values(editState.slot_edits)[0];
    if (!baseEdit) {
      setErrorMessage("Selecione uma foto para o slot ativo antes de preencher todos.");
      return;
    }

    const newEdits = { ...editState.slot_edits };
    for (const s of template.slots) {
      newEdits[s.id] = { ...baseEdit };
    }

    const nextState: EditStateModel = {
      ...editState,
      slot_edits: newEdits,
    };
    setEditState(nextState);
    if (historyRef.current) {
      historyRef.current.push(nextState);
    }
  };

  // Clear active slot
  const handleClearSlot = () => {
    if (!editState || !activeSlotId || !editState.slot_edits[activeSlotId]) return;
    const newEdits = { ...editState.slot_edits };
    delete newEdits[activeSlotId];

    const nextState: EditStateModel = {
      ...editState,
      slot_edits: newEdits,
    };
    setEditState(nextState);
    if (historyRef.current) {
      historyRef.current.push(nextState);
    }
  };

  // Add photos button
  const handleAddPhotos = async () => {
    try {
      setErrorMessage(null);
      const newAssets = await bridge.openFileDialog();
      if (newAssets.length > 0) {
        setSources((prev) => {
          const map = new Map(prev.map((a) => [a.id, a]));
          for (const a of newAssets) {
            map.set(a.id, a);
          }
          return Array.from(map.values());
        });

        // Automatically assign first imported asset to active slot if empty
        if (!currentSlotEdit && activeSlotId) {
          handleSelectSource(newAssets[0]);
        }
      }
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : String(err));
    }
  };

  // Rotation buttons
  const handleRotate = (deltaDeg: number) => {
    if (!activeSlotId) return;
    const nextDeg = currentTransform.rotation_deg + deltaDeg;
    const clamped = clampTransform({
      ...currentTransform,
      rotation_deg: nextDeg,
    });
    handleTransformChange(activeSlotId, clamped, true);
  };

  // Zoom slider / buttons
  const handleZoomChange = (newScale: number, commitToHistory: boolean = true) => {
    if (!activeSlotId) return;
    const clamped = clampTransform({
      ...currentTransform,
      scale: newScale,
    });
    handleTransformChange(activeSlotId, clamped, commitToHistory);
  };

  // Reset button
  const handleResetTransform = () => {
    if (!activeSlotId) return;
    handleTransformChange(activeSlotId, DEFAULT_TRANSFORM, true);
  };

  // Render Job
  const handleRender = async () => {
    if (!editState || !template) return;

    // Check slots
    const filledCount = Object.keys(editState.slot_edits).length;
    const totalSlots = template.slots.length;
    if (filledCount < totalSlots) {
      setErrorMessage(`Preencha todos os slots antes de gerar (${totalSlots - filledCount} restante(s)).`);
      return;
    }

    try {
      setRendering(true);
      setErrorMessage(null);
      setRenderResult(null);

      const res = await bridge.renderJob(editState);
      setRenderResult(res);
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : String(err));
    } finally {
      setRendering(false);
    }
  };

  const filledSlotsCount = useMemo(() => {
    if (!editState) return 0;
    return Object.keys(editState.slot_edits).length;
  }, [editState]);

  const allSlotsFilled = template ? filledSlotsCount === template.slots.length : false;

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh" }}>
      {/* Top Header */}
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "10px 24px",
          backgroundColor: "#1e293b",
          borderBottom: "1px solid #334155",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <h1 style={{ fontSize: "18px", fontWeight: "700", letterSpacing: "0.5px", margin: 0 }}>
            EVYDÊNCIA
          </h1>

          {/* Mode Switcher */}
          <div
            style={{
              display: "flex",
              backgroundColor: "#0f172a",
              borderRadius: "6px",
              padding: "3px",
              gap: "2px",
              border: "1px solid #334155",
            }}
          >
            <button
              onClick={() => setMode("operator")}
              style={{
                backgroundColor: mode === "operator" ? "#2563eb" : "transparent",
                color: mode === "operator" ? "#ffffff" : "#94a3b8",
                border: "none",
                borderRadius: "4px",
                padding: "5px 12px",
                fontSize: "12px",
                fontWeight: mode === "operator" ? "600" : "500",
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
            >
              👤 Operador
            </button>
            <button
              onClick={() => {
                setMode("manager");
                if (!draft && template) {
                  setDraft(createDraftFromTemplate(template));
                }
              }}
              style={{
                backgroundColor: mode === "manager" ? "#0284c7" : "transparent",
                color: mode === "manager" ? "#ffffff" : "#94a3b8",
                border: "none",
                borderRadius: "4px",
                padding: "5px 12px",
                fontSize: "12px",
                fontWeight: mode === "manager" ? "600" : "500",
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
            >
              ⚙️ Gestor
            </button>
          </div>

          {/* Product Switcher Tabs */}
          <div
            style={{
              display: "flex",
              backgroundColor: "#0f172a",
              borderRadius: "6px",
              padding: "3px",
              gap: "2px",
            }}
          >
            {templates.map((t) => {
              const isSelected = t.id === template?.id;
              return (
                <button
                  key={t.id}
                  onClick={() => handleSwitchTemplate(t)}
                  style={{
                    backgroundColor: isSelected ? "#2563eb" : "transparent",
                    color: isSelected ? "#ffffff" : "#94a3b8",
                    border: "none",
                    borderRadius: "4px",
                    padding: "6px 14px",
                    fontSize: "13px",
                    fontWeight: isSelected ? "600" : "500",
                    cursor: "pointer",
                    transition: "all 0.15s ease",
                  }}
                >
                  {t.name}
                </button>
              );
            })}
          </div>
        </div>

        {/* Undo / Redo & Status */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          {mode === "operator" && (
            <>
              <button
                className="btn-secondary"
                onClick={handleUndo}
                disabled={!historyRef.current?.canUndo}
                title="Desfazer (Ctrl+Z)"
                style={{ fontSize: "13px", padding: "6px 12px" }}
              >
                ↶ Desfazer
              </button>
              <button
                className="btn-secondary"
                onClick={handleRedo}
                disabled={!historyRef.current?.canRedo}
                title="Refazer (Ctrl+Y)"
                style={{ fontSize: "13px", padding: "6px 12px" }}
              >
                ↷ Refazer
              </button>
            </>
          )}
        </div>
      </header>

      {/* Product Subheader & Slot Selector */}
      {template && (
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "8px 24px",
            backgroundColor: "#0f172a",
            borderBottom: "1px solid #1e293b",
            fontSize: "13px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px", overflowX: "auto", flex: 1 }}>
            <span style={{ color: mode === "manager" ? "#38bdf8" : "#94a3b8", fontWeight: "600" }}>
              {mode === "manager"
                ? `Slots do Draft (${draft?.slots.length || 0}):`
                : `Slots (${filledSlotsCount}/${template.slots.length}):`}
            </span>
            <div style={{ display: "flex", gap: "6px", flexWrap: "nowrap" }}>
              {(mode === "manager" && draft ? draft.slots : template.slots).map((s) => {
                const isActive = s.id === activeSlotId;
                const hasPhoto = !!editState?.slot_edits[s.id];
                return (
                  <button
                    key={s.id}
                    onClick={() => setActiveSlotId(s.id)}
                    style={{
                      padding: "4px 10px",
                      borderRadius: "4px",
                      border: isActive
                        ? mode === "manager"
                          ? "2px solid #38bdf8"
                          : "2px solid #3b82f6"
                        : "1px solid #334155",
                      backgroundColor: isActive
                        ? mode === "manager"
                          ? "#0369a1"
                          : "#1e3a8a"
                        : hasPhoto
                        ? "#1e293b"
                        : "#0f172a",
                      color: isActive ? "#ffffff" : hasPhoto ? "#e2e8f0" : "#64748b",
                      fontSize: "12px",
                      cursor: "pointer",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {mode !== "manager" && hasPhoto ? "✓ " : ""}
                    {s.id.replace("slot_", "#").replace("foto_", "Foto ")}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Quick Batch Actions (Operator mode only) */}
          {mode === "operator" && (
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginLeft: "16px" }}>
              {template.id === "globo-neve" && (
                <button
                  className="btn-secondary"
                  onClick={handleDuplicateGloboSlot}
                  style={{ fontSize: "12px", padding: "5px 12px", backgroundColor: "#1e293b" }}
                  title="Copiar a mesma foto para ambos os slots"
                >
                  ✨ Usar mesma foto nos dois
                </button>
              )}

              {template.id === "chaveiro-3x4" && (
                <>
                  <button
                    className="btn-secondary"
                    onClick={handleDuplicateToNextSlot}
                    disabled={!currentSlotEdit}
                    style={{ fontSize: "12px", padding: "5px 12px", backgroundColor: "#1e293b" }}
                    title="Duplicar enquadramento para o próximo slot (ou dê duplo clique no slot)"
                  >
                    ⏩ Duplicar para próximo
                  </button>
                  <button
                    className="btn-secondary"
                    onClick={handleFillAllSlots}
                    style={{ fontSize: "12px", padding: "5px 12px", backgroundColor: "#1e293b" }}
                    title="Preencher toda a folha com a foto do slot ativo"
                  >
                    ⚡ Preencher todos os 18 slots
                  </button>
                </>
              )}

              {currentSlotEdit && (
                <button
                  className="btn-secondary"
                  onClick={handleClearSlot}
                  style={{ fontSize: "12px", padding: "5px 10px", color: "#f87171" }}
                  title="Remover foto do slot selecionado"
                >
                  Remover foto
                </button>
              )}
            </div>
          )}
        </div>
      )}

      {/* Main Work Area */}
      <div style={{ display: "flex", flex: 1, minHeight: 0 }}>
        {/* Left / Center: Interactive Canvas */}
        <main
          ref={canvasContainerRef}
          style={{
            flex: 1,
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            backgroundColor: "#0b0f19",
            position: "relative",
            overflow: "hidden",
            padding: "20px",
          }}
        >
          {template ? (
            <ProductCanvas
              key={template.id}
              template={template}
              activeSlotId={activeSlotId}
              onSelectSlot={setActiveSlotId}
              slotEdits={editState?.slot_edits || {}}
              sources={sources}
              onTransformChange={handleTransformChange}
              layout={previewLayout}
              onDoubleClickSlot={handleDoubleClickSlot}
              mode={mode}
              draft={draft}
              onDraftSlotChange={handleDraftSlotChange}
            />
          ) : (
            <div style={{ color: "#64748b" }}>Carregando produto...</div>
          )}
        </main>

        {/* Right Sidebar: Manager Inspector OR Operator Controls */}
        {mode === "manager" && draft ? (
          <ManagerInspector
            draft={draft}
            activeSlotId={activeSlotId}
            onSelectSlot={setActiveSlotId}
            onUpdateDraft={setDraft}
          />
        ) : (
          <aside
            style={{
              width: "360px",
              backgroundColor: "#0f172a",
              borderLeft: "1px solid #334155",
              display: "flex",
              flexDirection: "column",
              overflowY: "auto",
              padding: "20px",
              gap: "24px",
            }}
          >
          {/* Active Slot Header */}
          <div
            style={{
              padding: "12px",
              backgroundColor: "#1e293b",
              borderRadius: "6px",
              border: "1px solid #334155",
            }}
          >
            <div style={{ fontSize: "12px", color: "#94a3b8", textTransform: "uppercase", fontWeight: "600" }}>
              Slot Selecionado
            </div>
            <div style={{ fontSize: "16px", fontWeight: "700", marginTop: "2px", color: "#60a5fa" }}>
              {activeSlot?.id || "Nenhum"}
            </div>
            <div style={{ fontSize: "12px", color: "#cbd5e1", marginTop: "4px" }}>
              {activeAsset ? `Foto: ${activeAsset.display_name}` : "Clique em uma foto abaixo para atribuir"}
            </div>
          </div>

          {/* Photo Adjustment Controls */}
          <div
            style={{
              padding: "16px",
              backgroundColor: "#1e293b",
              borderRadius: "8px",
              border: "1px solid #334155",
            }}
          >
            <h3 style={{ fontSize: "14px", fontWeight: "600", marginBottom: "16px" }}>
              Ajuste de Enquadramento
            </h3>

            {/* Zoom Slider */}
            <div style={{ marginBottom: "20px" }}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  fontSize: "13px",
                  marginBottom: "8px",
                }}
              >
                <span>Zoom</span>
                <span style={{ color: "#94a3b8" }}>{currentTransform.scale.toFixed(2)}x</span>
              </div>
              <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                <button
                  className="btn-secondary"
                  style={{ width: "32px", height: "32px", padding: 0 }}
                  onClick={() => handleZoomChange(Math.max(1.0, currentTransform.scale - 0.25))}
                  disabled={!activeAsset}
                >
                  -
                </button>
                <input
                  type="range"
                  min="1.0"
                  max="8.0"
                  step="0.05"
                  value={currentTransform.scale}
                  onChange={(e) => handleZoomChange(parseFloat(e.target.value), false)}
                  onPointerUp={() => handleZoomChange(currentTransform.scale, true)}
                  onKeyUp={() => handleZoomChange(currentTransform.scale, true)}
                  disabled={!activeAsset}
                  style={{ flex: 1, accentColor: "#3b82f6" }}
                />
                <button
                  className="btn-secondary"
                  style={{ width: "32px", height: "32px", padding: 0 }}
                  onClick={() => handleZoomChange(Math.min(8.0, currentTransform.scale + 0.25))}
                  disabled={!activeAsset}
                >
                  +
                </button>
              </div>
            </div>

            {/* Rotation Control */}
            <div style={{ marginBottom: "20px" }}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  fontSize: "13px",
                  marginBottom: "8px",
                }}
              >
                <span>Rotação</span>
                <span style={{ color: "#94a3b8" }}>{currentTransform.rotation_deg.toFixed(0)}°</span>
              </div>
              <div style={{ display: "flex", gap: "8px" }}>
                <button
                  className="btn-secondary"
                  style={{ flex: 1 }}
                  onClick={() => handleRotate(-90)}
                  disabled={!activeAsset}
                >
                  ↶ -90°
                </button>
                <button
                  className="btn-secondary"
                  style={{ flex: 1 }}
                  onClick={() => handleRotate(90)}
                  disabled={!activeAsset}
                >
                  ↷ +90°
                </button>
              </div>
            </div>

            {/* Reset Button */}
            <button
              className="btn-secondary"
              style={{ width: "100%", marginTop: "4px" }}
              onClick={handleResetTransform}
              disabled={!activeAsset}
            >
              Resetar Enquadramento
            </button>
          </div>

          {/* Source Tray */}
          <div style={{ flex: 1, display: "flex", flexDirection: "column", minHeight: 0 }}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "12px",
              }}
            >
              <h3 style={{ fontSize: "14px", fontWeight: "600", margin: 0 }}>
                Fotos do Cliente ({sources.length})
              </h3>
              <button
                className="btn-primary"
                onClick={handleAddPhotos}
                style={{ fontSize: "12px", padding: "6px 12px" }}
              >
                + Adicionar Fotos
              </button>
            </div>

            <div
              style={{
                flex: 1,
                overflowY: "auto",
                display: "grid",
                gridTemplateColumns: "repeat(2, 1fr)",
                gap: "10px",
                alignContent: "start",
                padding: "4px",
              }}
            >
              {sources.map((s) => {
                const isSelected = activeAsset?.id === s.id;
                return (
                  <div
                    key={s.id}
                    onClick={() => handleSelectSource(s)}
                    style={{
                      cursor: "pointer",
                      border: isSelected ? "2px solid #3b82f6" : "1px solid #334155",
                      borderRadius: "6px",
                      overflow: "hidden",
                      backgroundColor: "#1e293b",
                      position: "relative",
                      transition: "transform 0.1s ease, border-color 0.1s ease",
                    }}
                  >
                    {s.preview.url ? (
                      <img
                        src={s.preview.url}
                        alt={s.display_name}
                        style={{
                          width: "100%",
                          height: "100px",
                          objectFit: "cover",
                          display: "block",
                        }}
                      />
                    ) : (
                      <div
                        style={{
                          width: "100%",
                          height: "100px",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          color: "#64748b",
                          fontSize: "12px",
                        }}
                      >
                        Carregando...
                      </div>
                    )}
                    <div
                      style={{
                        padding: "4px 6px",
                        fontSize: "11px",
                        color: "#cbd5e1",
                        whiteSpace: "nowrap",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        backgroundColor: "#0f172a",
                      }}
                    >
                      {s.display_name}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </aside>
      )}
      </div>

      {/* Bottom Bar: Action & Messages */}
      {mode === "manager" ? (
        <footer
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "14px 24px",
            backgroundColor: "#1e293b",
            borderTop: "1px solid #334155",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "16px",
              fontSize: "13px",
              color: "#94a3b8",
            }}
          >
            <span>
              Modo: <strong style={{ color: "#38bdf8" }}>Gestão de Template</strong>
            </span>
            <span>•</span>
            <span>
              Folha:{" "}
              <strong style={{ color: "#f8fafc" }}>
                {draft?.canvas.width_mm} × {draft?.canvas.height_mm} mm
              </strong>{" "}
              ({draft?.canvas.dpi} DPI)
            </span>
            <span>•</span>
            <span>
              Slots:{" "}
              <strong style={{ color: "#f8fafc" }}>
                {draft?.slots.length}
              </strong>
            </span>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <button
              className="btn-secondary"
              onClick={() => {
                if (template) setDraft(createDraftFromTemplate(template));
              }}
              disabled={!draft?.dirty}
              style={{ fontSize: "13px" }}
              title="Restaurar valores do template oficial em disco"
            >
              Descartar Alterações
            </button>
            <div
              style={{
                fontSize: "12px",
                padding: "6px 14px",
                backgroundColor: "#0369a1",
                color: "#ffffff",
                borderRadius: "6px",
                fontWeight: "600",
              }}
            >
              Publicação em Disco (Marco M5-B)
            </div>
          </div>
        </footer>
      ) : (
        <footer
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "16px 24px",
            backgroundColor: "#1e293b",
            borderTop: "1px solid #334155",
          }}
        >
          <div style={{ flex: 1, minWidth: 0, marginRight: "20px" }}>
            {errorMessage && (
              <div style={{ color: "#f87171", fontSize: "14px", fontWeight: "500" }}>
                ⚠️ {errorMessage}
              </div>
            )}
            {renderResult && (
              <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                <span style={{ color: "#4ade80", fontSize: "14px", fontWeight: "500" }}>
                  ✓ Arquivo gerado em {renderResult.render_time_ms.toFixed(0)} ms!
                </span>
                <button
                  className="btn-secondary"
                  style={{ fontSize: "12px", padding: "4px 10px" }}
                  onClick={() => bridge.openOutputFolder(renderResult.output_path)}
                >
                  Abrir pasta
                </button>
              </div>
            )}
          </div>

          <button
            className="btn-success"
            onClick={handleRender}
            disabled={rendering || !allSlotsFilled}
            title={!allSlotsFilled ? "Preencha todos os slots para gerar" : "Gerar impressão final"}
          >
            {rendering ? "GERANDO ARQUIVO ORIGINAL..." : "GERAR ARQUIVO DE PRODUÇÃO"}
          </button>
        </footer>
      )}
    </div>
  );
};
