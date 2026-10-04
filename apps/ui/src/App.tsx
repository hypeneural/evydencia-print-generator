import React, { useEffect, useState, useMemo, useRef, useCallback } from "react";
import { bridge } from "./bridge/api";
import { CalendarCanvas } from "./components/CalendarCanvas";
import { createHistoryManager } from "./domain/history";
import type { SlotTransform } from "./domain/transform";
import { clampTransform } from "./domain/transform";
import type {
  EditStateModel,
  RenderResultModel,
  SourceAssetModel,
  TemplateModel,
} from "./domain/types";

const DEFAULT_TRANSFORM: SlotTransform = {
  pan_x_norm: 0.0,
  pan_y_norm: 0.0,
  scale: 1.0,
  rotation_deg: 0.0,
};

export const App: React.FC = () => {
  const [template, setTemplate] = useState<TemplateModel | null>(null);
  const [sources, setSources] = useState<SourceAssetModel[]>([]);
  const [activeSlotId, setActiveSlotId] = useState<string>("foto_principal");
  const [editState, setEditState] = useState<EditStateModel | null>(null);
  const [rendering, setRendering] = useState(false);
  const [renderResult, setRenderResult] = useState<RenderResultModel | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const canvasContainerRef = useRef<HTMLDivElement | null>(null);
  const [viewportScale, setViewportScale] = useState<number>(0.7);

  // History manager ref
  const historyRef = useRef<ReturnType<typeof createHistoryManager> | null>(null);

  // Load templates & initial sources
  useEffect(() => {
    async function init() {
      try {
        const templates = await bridge.getTemplates();
        if (templates.length > 0) {
          const tpl = templates[0];
          setTemplate(tpl);
          setActiveSlotId(tpl.slots[0]?.id || "foto_principal");

          const initialEdit: EditStateModel = {
            template_id: tpl.id,
            template_version: tpl.template_version,
            slot_edits: {},
          };
          setEditState(initialEdit);
          historyRef.current = createHistoryManager(initialEdit);
        }
        const initialSources = await bridge.getSources();
        setSources(initialSources);
      } catch (err: unknown) {
        setErrorMessage(err instanceof Error ? err.message : String(err));
      }
    }
    init();
  }, []);

  // Compute scale to fit calendar inside center area
  useEffect(() => {
    function updateScale() {
      if (!canvasContainerRef.current || !template) return;
      const { clientWidth, clientHeight } = canvasContainerRef.current;
      const targetW = template.canvas_px.width;
      const targetH = template.canvas_px.height;
      const pad = 40;
      const scaleX = (clientWidth - pad) / targetW;
      const scaleY = (clientHeight - pad) / targetH;
      const s = Math.min(scaleX, scaleY, 1.0);
      setViewportScale(Math.max(0.2, s));
    }
    updateScale();
    window.addEventListener("resize", updateScale);
    return () => window.removeEventListener("resize", updateScale);
  }, [template]);

  // Current active slot & transform
  const activeSlot = useMemo(() => {
    if (!template) return null;
    return template.slots.find((s) => s.id === activeSlotId) || template.slots[0] || null;
  }, [template, activeSlotId]);

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
    (nextTransform: SlotTransform, commitToHistory: boolean) => {
      if (!editState || !activeSlotId || !currentSlotEdit) return;

      const updatedEditState: EditStateModel = {
        ...editState,
        slot_edits: {
          ...editState.slot_edits,
          [activeSlotId]: {
            ...currentSlotEdit,
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
    [editState, activeSlotId, currentSlotEdit]
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

  // Set photo to slot
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
        // Auto-assign to active slot if empty
        if (!currentSlotEdit) {
          handleSelectSource(newAssets[0]);
        }
      }
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : String(err));
    }
  };

  // Rotate button
  const handleRotate = (deltaDeg: number) => {
    const nextDeg = currentTransform.rotation_deg + deltaDeg;
    const clamped = clampTransform({
      ...currentTransform,
      rotation_deg: nextDeg,
    });
    handleTransformChange(clamped, true);
  };

  // Zoom slider / buttons
  const handleZoomChange = (newScale: number) => {
    const clamped = clampTransform({
      ...currentTransform,
      scale: newScale,
    });
    handleTransformChange(clamped, true);
  };

  // Reset button
  const handleResetTransform = () => {
    handleTransformChange(DEFAULT_TRANSFORM, true);
  };

  // Render Job
  const handleRender = async () => {
    if (!editState || !template) return;
    if (Object.keys(editState.slot_edits).length === 0) {
      setErrorMessage("Adicione uma foto ao calendário antes de gerar.");
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

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh" }}>
      {/* Top Header */}
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "12px 24px",
          backgroundColor: "#1e293b",
          borderBottom: "1px solid #334155",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <h1 style={{ fontSize: "18px", fontWeight: "700", letterSpacing: "0.5px" }}>
            EVYDÊNCIA
          </h1>
          <span
            style={{
              fontSize: "12px",
              padding: "2px 8px",
              borderRadius: "4px",
              backgroundColor: "#334155",
              color: "#94a3b8",
            }}
          >
            {template?.name || "Carregando produto..."}
          </span>
        </div>

        {/* Undo / Redo */}
        <div style={{ display: "flex", gap: "8px" }}>
          <button
            className="btn-secondary"
            onClick={handleUndo}
            disabled={!historyRef.current?.canUndo}
            title="Desfazer (Ctrl+Z)"
          >
            ↺ Desfazer
          </button>
          <button
            className="btn-secondary"
            onClick={handleRedo}
            disabled={!historyRef.current?.canRedo}
            title="Refazer (Ctrl+Y)"
          >
            ↻ Refazer
          </button>
        </div>
      </header>

      {/* Main Layout Area */}
      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        {/* Left Sidebar: Source Tray */}
        <aside
          style={{
            width: "280px",
            backgroundColor: "#0f172a",
            borderRight: "1px solid #334155",
            display: "flex",
            flexDirection: "column",
            padding: "16px",
          }}
        >
          <div style={{ marginBottom: "16px" }}>
            <h2 style={{ fontSize: "14px", fontWeight: "600", marginBottom: "8px" }}>FOTOS</h2>
            <button
              className="btn-primary"
              style={{ width: "100%" }}
              onClick={handleAddPhotos}
            >
              + Adicionar fotos
            </button>
          </div>

          <div
            style={{
              flex: 1,
              overflowY: "auto",
              display: "flex",
              flexDirection: "column",
              gap: "10px",
            }}
          >
            {sources.length === 0 ? (
              <div
                style={{
                  padding: "24px 12px",
                  textAlign: "center",
                  color: "#64748b",
                  fontSize: "13px",
                  border: "2px dashed #334155",
                  borderRadius: "8px",
                }}
              >
                Nenhuma foto carregada.
                <br />
                Clique em <strong>+ Adicionar fotos</strong> para começar.
              </div>
            ) : (
              sources.map((src) => {
                const isSelected = currentSlotEdit?.source_id === src.id;
                return (
                  <div
                    key={src.id}
                    onClick={() => handleSelectSource(src)}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "12px",
                      padding: "8px",
                      borderRadius: "6px",
                      cursor: "pointer",
                      backgroundColor: isSelected ? "#1e293b" : "#182234",
                      border: isSelected ? "2px solid #3b82f6" : "1px solid #334155",
                      transition: "border-color 0.15s ease",
                    }}
                  >
                    <div
                      style={{
                        width: "60px",
                        height: "60px",
                        backgroundColor: "#0f172a",
                        borderRadius: "4px",
                        overflow: "hidden",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                      }}
                    >
                      {src.preview.status === "ready" && src.preview.url ? (
                        <img
                          src={src.preview.url}
                          alt={src.display_name}
                          style={{ width: "100%", height: "100%", objectFit: "cover" }}
                        />
                      ) : src.preview.status === "loading" ? (
                        <span style={{ fontSize: "11px", color: "#94a3b8" }}>Carregando...</span>
                      ) : (
                        <span style={{ fontSize: "11px", color: "#ef4444" }}>Erro</span>
                      )}
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div
                        style={{
                          fontSize: "13px",
                          fontWeight: "500",
                          whiteSpace: "nowrap",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                        }}
                      >
                        {src.display_name}
                      </div>
                      <div style={{ fontSize: "11px", color: "#64748b" }}>
                        {src.probe.oriented_width} × {src.probe.oriented_height} px
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </aside>

        {/* Center: Interactive Canvas */}
        <main
          ref={canvasContainerRef}
          style={{
            flex: 1,
            position: "relative",
            backgroundColor: "#1e293b",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
          }}
        >
          {template && activeSlot ? (
            <CalendarCanvas
              template={template}
              slot={activeSlot}
              asset={activeAsset}
              transform={currentTransform}
              onTransformChange={handleTransformChange}
              scaleViewport={viewportScale}
            />
          ) : (
            <div>Carregando editor...</div>
          )}
        </main>

        {/* Right Sidebar: Adjust Controls (Operador) */}
        <aside
          style={{
            width: "280px",
            backgroundColor: "#0f172a",
            borderLeft: "1px solid #334155",
            display: "flex",
            flexDirection: "column",
            padding: "20px",
            gap: "24px",
          }}
        >
          <div>
            <h2 style={{ fontSize: "14px", fontWeight: "600", marginBottom: "16px" }}>
              AJUSTAR FOTO
            </h2>

            {/* Zoom Control */}
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
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
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
                  onChange={(e) => handleZoomChange(parseFloat(e.target.value))}
                  disabled={!activeAsset}
                  style={{ flex: 1, cursor: "pointer" }}
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
              style={{ width: "100%", marginTop: "8px" }}
              onClick={handleResetTransform}
              disabled={!activeAsset}
            >
              Resetar Enquadramento
            </button>
          </div>

          <div
            style={{
              padding: "12px",
              backgroundColor: "#182234",
              borderRadius: "6px",
              fontSize: "12px",
              color: "#94a3b8",
              lineHeight: "1.5",
            }}
          >
            💡 <strong>Dica Operador:</strong>
            <br />
            • Arraste a foto diretamente no calendário para mover o enquadramento.
            <br />• Use a rodinha do mouse sobre a foto para aumentar ou diminuir o zoom.
          </div>
        </aside>
      </div>

      {/* Bottom Bar: Action & Messages */}
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
          disabled={rendering || !activeAsset}
        >
          {rendering ? "GERANDO ARQUIVO ORIGINAL..." : "GERAR ARQUIVO DE PRODUÇÃO"}
        </button>
      </footer>
    </div>
  );
};
