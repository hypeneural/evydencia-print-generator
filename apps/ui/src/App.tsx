import React, { useEffect, useState, useMemo, useRef, useCallback } from "react";
import { bridge } from "./bridge/api";
import { ProductCanvas } from "./components/ProductCanvas";
import { ManagerInspector } from "./components/ManagerInspector";
import { createHistoryManager } from "./domain/history";
import { duplicateSlot, duplicateSelectedSlots } from "./domain/duplication";
import { checkRenderEligibility } from "./domain/render_policy";
import type { PreviewLayout } from "./domain/layout";
import { computePreviewLayout } from "./domain/layout";
import type { SlotTransform } from "./domain/transform";
import { clampTransform } from "./domain/transform";
import type {
  EditStateModel,
  RenderResultModel,
  SlotEditState,
  SourceAssetModel,
  TemplateModel,
} from "./domain/types";
import type { DraftSlot, TemplateDraft } from "./domain/draft";
import { createDraftFromTemplate, updateSlotMm } from "./domain/draft";
import { classifyDropPoint } from "./domain/hittest";
import {
  assignSourcesToSlots,
  countEmptySlots,
  fillEmptySlots,
  removeSlotPhoto,
} from "./domain/slot_assignment";
import {
  shouldHandleDeletePhoto,
  isTextEditingTarget,
  type KeyTargetLike,
} from "./domain/keyboard";

declare global {
  interface Window {
    __onNativeFileDrop?: (payload: {
      sources: SourceAssetModel[];
      accepted_ids: string[];
      clientX: number;
      clientY: number;
    }) => void;
  }
}

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
  const [selectedSlotIds, setSelectedSlotIds] = useState<string[]>([]);
  const [editState, setEditState] = useState<EditStateModel | null>(null);
  const [rendering, setRendering] = useState(false);
  const [renderResult, setRenderResult] = useState<RenderResultModel | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [trayNotice, setTrayNotice] = useState<string | null>(null);
  const [isManagerGeometryUnlocked, setIsManagerGeometryUnlocked] = useState(false);
  const isGeometryLocked =
    template?.status === "production" && !isManagerGeometryUnlocked;
  const canvasContainerRef = useRef<HTMLDivElement | null>(null);
  const [previewLayout, setPreviewLayout] = useState<PreviewLayout>({
    fitScale: 1.0,
    displayWidth: 1067,
    displayHeight: 1474,
  });

  // History manager ref
  const historyRef = useRef<ReturnType<typeof createHistoryManager> | null>(null);

  // Stable refs for event listeners and non-stale callbacks
  const editStateRef = useRef<EditStateModel | null>(null);
  const activeSlotIdRef = useRef<string>("");
  const modeRef = useRef<"operator" | "manager">(mode);
  const templateRef = useRef<TemplateModel | null>(null);
  const layoutRef = useRef<PreviewLayout>(previewLayout);
  const startupBatchIdsRef = useRef<string[]>([]);

  useEffect(() => {
    editStateRef.current = editState;
  }, [editState]);
  useEffect(() => {
    activeSlotIdRef.current = activeSlotId;
  }, [activeSlotId]);
  useEffect(() => {
    modeRef.current = mode;
  }, [mode]);
  useEffect(() => {
    templateRef.current = template;
  }, [template]);
  useEffect(() => {
    layoutRef.current = previewLayout;
  }, [previewLayout]);

  // Single authoritative commit helper: updates ref, updates React state, pushes exactly 1 history entry
  const commitEditState = useCallback((next: EditStateModel) => {
    editStateRef.current = next;
    setEditState(next);
    if (historyRef.current) {
      historyRef.current.push(next);
    }
  }, []);

  // Load templates & initial sources
  useEffect(() => {
    async function init() {
      try {
        const [availableTemplates, initialSources, startupBatch] = await Promise.all([
          bridge.getTemplates(),
          bridge.getSources(),
          bridge.getStartupBatch(),
        ]);
        setTemplates(availableTemplates);
        setSources(initialSources);
        startupBatchIdsRef.current = startupBatch.accepted_ids;

        if (availableTemplates.length > 0) {
          const tpl = availableTemplates[0];
          setTemplate(tpl);
          setDraft(createDraftFromTemplate(tpl));
          const firstSlotId = tpl.slots[0]?.id || "";
          setActiveSlotId(firstSlotId);
          setSelectedSlotIds(firstSlotId ? [firstSlotId] : []);

          let initialEdits: Record<string, SlotEditState> = {};
          if (startupBatch.accepted_ids.length > 0) {
            const res = assignSourcesToSlots({
              slotIds: tpl.slots.map((s) => s.id),
              slotEdits: {},
              sourceIds: startupBatch.accepted_ids,
            });
            initialEdits = res.nextSlotEdits;
          } else if (initialSources.length > 0 && firstSlotId) {
            initialEdits[firstSlotId] = {
              source_id: initialSources[0].id,
              pan_x_norm: 0.0,
              pan_y_norm: 0.0,
              scale: 1.0,
              rotation_deg: 0.0,
            };
          }

          const initialEdit: EditStateModel = {
            template_id: tpl.id,
            template_version: tpl.template_version,
            slot_edits: initialEdits,
          };

          setEditState(initialEdit);
          editStateRef.current = initialEdit;
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
      } catch (e) {
        console.warn("Failed to poll sources:", e);
      }
    }, 250);

    return () => clearInterval(interval);
  }, [sources]);

  // Switch template
  const handleSwitchTemplate = (tpl: TemplateModel) => {
    if (tpl.id === template?.id) return;
    setTemplate(tpl);
    setDraft(createDraftFromTemplate(tpl));
    setIsManagerGeometryUnlocked(false);
    const firstSlot = tpl.slots[0]?.id || "";
    setActiveSlotId(firstSlot);
    setSelectedSlotIds(firstSlot ? [firstSlot] : []);

    // Compute preview layout synchronously to eliminate 1-frame orientation flash
    if (canvasContainerRef.current) {
      const { clientWidth, clientHeight } = canvasContainerRef.current;
      if (clientWidth > 0 && clientHeight > 0) {
        const padding = mode === "manager" ? 24 : 16;
        const l = computePreviewLayout(
          tpl.canvas_px.width,
          tpl.canvas_px.height,
          clientWidth,
          clientHeight,
          padding
        );
        setPreviewLayout(l);
      }
    }

    let initialEdits: Record<string, SlotEditState> = {};
    if (startupBatchIdsRef.current.length > 0) {
      const res = assignSourcesToSlots({
        slotIds: tpl.slots.map((s) => s.id),
        slotEdits: {},
        sourceIds: startupBatchIdsRef.current,
      });
      initialEdits = res.nextSlotEdits;
    } else if (sources.length > 0 && firstSlot) {
      initialEdits[firstSlot] = {
        source_id: sources[0].id,
        pan_x_norm: 0.0,
        pan_y_norm: 0.0,
        scale: 1.0,
        rotation_deg: 0.0,
      };
    }

    const newEditState: EditStateModel = {
      template_id: tpl.id,
      template_version: tpl.template_version,
      slot_edits: initialEdits,
    };

    setEditState(newEditState);
    editStateRef.current = newEditState;
    historyRef.current = createHistoryManager(newEditState);
    setRenderResult(null);
    setErrorMessage(null);
    setTrayNotice(null);
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
      const padding = mode === "manager" ? 24 : 16;
      const l = computePreviewLayout(
        wPx,
        hPx,
        clientWidth,
        clientHeight,
        padding
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

  // Remove photo from active slot (Delete key or "Remover foto" button)
  const removeActiveSlotPhoto = useCallback((): boolean => {
    const prev = editStateRef.current;
    const slotId = activeSlotIdRef.current;
    if (!prev || !slotId) return false;
    const nextEdits = removeSlotPhoto(prev.slot_edits, slotId);
    if (!nextEdits) return false;
    commitEditState({
      ...prev,
      slot_edits: nextEdits,
    });
    return true;
  }, [commitEditState]);

  // Keyboard shortcuts (Ctrl+Z, Ctrl+Y, Delete)
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      const target = e.target as KeyTargetLike;
      if (isTextEditingTarget(target)) return;

      if ((e.ctrlKey || e.metaKey) && !e.shiftKey && e.key.toLowerCase() === "z") {
        e.preventDefault();
        handleUndo();
      } else if (
        (e.ctrlKey || e.metaKey) &&
        (e.key.toLowerCase() === "y" || (e.shiftKey && e.key.toLowerCase() === "z"))
      ) {
        e.preventDefault();
        handleRedo();
      } else if (
        shouldHandleDeletePhoto({
          key: e.key,
          ctrlKey: e.ctrlKey,
          altKey: e.altKey,
          metaKey: e.metaKey,
          shiftKey: e.shiftKey,
          target,
          mode: modeRef.current,
          templateId: templateRef.current?.id,
          activeSlotId: activeSlotIdRef.current,
          hasPhotoInActiveSlot: !!(
            activeSlotIdRef.current &&
            editStateRef.current?.slot_edits[activeSlotIdRef.current]
          ),
        })
      ) {
        e.preventDefault();
        removeActiveSlotPhoto();
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleUndo, handleRedo, removeActiveSlotPhoto]);

  // Set photo to active slot
  const handleSelectSource = (asset: SourceAssetModel) => {
    const prev = editStateRef.current;
    const slotId = activeSlotIdRef.current;
    if (!prev || !slotId) return;

    commitEditState({
      ...prev,
      slot_edits: {
        ...prev.slot_edits,
        [slotId]: {
          source_id: asset.id,
          pan_x_norm: 0.0,
          pan_y_norm: 0.0,
          scale: 1.0,
          rotation_deg: 0.0,
        },
      },
    });
  };

  // Handle dropping an asset directly onto a specific slot from the internal photo tray (1-to-1)
  const handleDropAssetOnSlot = useCallback(
    (slotId: string, sourceId: string) => {
      const prev = editStateRef.current;
      if (!prev) return;
      commitEditState({
        ...prev,
        slot_edits: {
          ...prev.slot_edits,
          [slotId]: {
            source_id: sourceId,
            pan_x_norm: 0.0,
            pan_y_norm: 0.0,
            scale: 1.0,
            rotation_deg: 0.0,
          },
        },
      });
      setActiveSlotId(slotId);
    },
    [commitEditState]
  );

  // Unified batch assignment helper for multi-drop, dialog and startup batch
  const applySourceBatch = useCallback(
    (sourceIds: string[], anchorSlotId?: string | null) => {
      const prev = editStateRef.current;
      const tpl = templateRef.current;
      if (!prev || !tpl || modeRef.current !== "operator" || sourceIds.length === 0) {
        return null;
      }
      const slotIds = tpl.slots.map((s) => s.id);
      const res = assignSourcesToSlots({
        slotIds,
        slotEdits: prev.slot_edits,
        sourceIds,
        anchorSlotId,
      });

      if (res.changed) {
        commitEditState({
          ...prev,
          slot_edits: res.nextSlotEdits,
        });
        if (res.firstAssignedSlotId) {
          setActiveSlotId(res.firstAssignedSlotId);
        }
      }
      if (res.unassignedSourceIds.length > 0) {
        setTrayNotice(
          `${res.unassignedSourceIds.length} foto(s) ficaram na bandeja (sem campos vazios).`
        );
      } else {
        setTrayNotice(null);
      }
      return res;
    },
    [commitEditState]
  );

  // Native Explorer drag & drop event listener dispatched from Python DesktopBridge
  useEffect(() => {
    window.__onNativeFileDrop = (payload) => {
      setSources(payload.sources);

      // Photo drop to slots is Operator-only
      if (modeRef.current !== "operator" || payload.accepted_ids.length === 0) return;
      if (!canvasContainerRef.current || !templateRef.current) return;

      const canvasEl = canvasContainerRef.current.querySelector("canvas");
      if (!canvasEl) return;
      const rect = canvasEl.getBoundingClientRect();
      const tpl = templateRef.current;

      const dropTarget = classifyDropPoint(
        tpl.slots,
        payload.clientX,
        payload.clientY,
        rect,
        layoutRef.current.fitScale
      );

      if (dropTarget.kind === "outside") {
        // CASO 7: drop outside canvas -> sources go to tray, zero slot mutation
        return;
      }

      // CASOS 1..6: drop on specific slot (anchor) or canvas gap/margin (general batch)
      const anchor = dropTarget.kind === "slot" ? dropTarget.slotId : null;
      applySourceBatch(payload.accepted_ids, anchor);
    };

    return () => {
      delete window.__onNativeFileDrop;
    };
  }, [applySourceBatch]);

  // Batch action: Duplicate photo across slots in Globo
  const handleDuplicateGloboSlot = () => {
    const prev = editStateRef.current;
    const tpl = templateRef.current;
    if (!prev || !tpl || tpl.slots.length < 2) return;
    const slot1Edit = prev.slot_edits["foto_1"];
    const slot2Edit = prev.slot_edits["foto_2"];

    const sourceEdit =
      activeSlotIdRef.current === "foto_2"
        ? slot2Edit || slot1Edit
        : slot1Edit || slot2Edit;
    if (!sourceEdit) return;

    commitEditState({
      ...prev,
      slot_edits: {
        ...prev.slot_edits,
        foto_1: { ...sourceEdit },
        foto_2: { ...sourceEdit },
      },
    });
  };

  // Double-click handler per product (M4-D, M4-E)
  const handleDoubleClickSlot = useCallback(
    (slotId: string) => {
      const prev = editStateRef.current;
      const tpl = templateRef.current;
      if (!prev || !tpl) return;

      const slotIds = tpl.slots.map((s) => s.id);
      const res = duplicateSlot(tpl.id, slotIds, slotId, prev.slot_edits);
      if (res) {
        commitEditState({
          ...prev,
          slot_edits: res.nextSlotEdits,
        });
        setActiveSlotId(res.targetSlotId);
      } else {
        // Calendário or generic: focus slot
        setActiveSlotId(slotId);
      }
    },
    [commitEditState]
  );

  // Slot selection with Shift multi-select support for Chaveiro
  const handleSelectSlot = useCallback(
    (slotId: string, options?: { shiftKey?: boolean }) => {
      if (
        modeRef.current === "operator" &&
        templateRef.current?.id === "chaveiro-3x4" &&
        options?.shiftKey
      ) {
        setSelectedSlotIds((prev) => {
          if (prev.includes(slotId)) {
            const next = prev.filter((id) => id !== slotId);
            return next.length > 0 ? next : [slotId];
          }
          return [...prev, slotId];
        });
        setActiveSlotId(slotId);
      } else {
        setSelectedSlotIds([slotId]);
        setActiveSlotId(slotId);
      }
    },
    []
  );

  // Batch action: Duplicate active slot to next slot in Chaveiro
  const handleDuplicateToNextSlot = useCallback(() => {
    if (!activeSlotId) return;
    handleDoubleClickSlot(activeSlotId);
  }, [activeSlotId, handleDoubleClickSlot]);

  // Batch action: Duplicate multiple selected slots in Chaveiro
  const handleDuplicateSelected = useCallback(() => {
    const prev = editStateRef.current;
    const tpl = templateRef.current;
    if (!prev || !tpl) return;

    const slotIds = tpl.slots.map((s) => s.id);
    const res = duplicateSelectedSlots({
      slotIds,
      selectedSlotIds,
      slotEdits: prev.slot_edits,
    });

    if (res.changed) {
      commitEditState({
        ...prev,
        slot_edits: res.nextSlotEdits,
      });
      if (res.targetSlotIds.length > 0) {
        setActiveSlotId(res.targetSlotIds[0]);
        setSelectedSlotIds(res.targetSlotIds);
      }
    }
    if (res.unassignedCount > 0) {
      setTrayNotice(
        `${res.unassignedCount} foto(s) não puderam ser duplicadas por falta de campos vazios.`
      );
    }
  }, [selectedSlotIds, commitEditState]);

  // Batch action: Fill remaining empty slots in Chaveiro
  const emptySlotsCount = useMemo(() => {
    if (!template || !editState) return 0;
    return countEmptySlots(
      template.slots.map((s) => s.id),
      editState.slot_edits
    );
  }, [template, editState]);

  const handleFillRemainingSlots = () => {
    const prev = editStateRef.current;
    const tpl = templateRef.current;
    const activeSlot = activeSlotIdRef.current;
    if (!prev || !tpl || !activeSlot) return;

    const res = fillEmptySlots({
      slotIds: tpl.slots.map((s) => s.id),
      slotEdits: prev.slot_edits,
      baseSlotId: activeSlot,
    });
    if (!res) return;

    commitEditState({
      ...prev,
      slot_edits: res.nextSlotEdits,
    });
  };

  // Clear active slot
  const handleClearSlot = () => {
    removeActiveSlotPhoto();
  };

  // Add photos button
  const handleAddPhotos = async () => {
    try {
      setErrorMessage(null);
      const batch = await bridge.openFileDialog();
      if (batch.sources.length > 0) {
        setSources(batch.sources);
        const active = activeSlotIdRef.current;
        const anchor =
          active && !editStateRef.current?.slot_edits[active] ? active : null;
        applySourceBatch(batch.accepted_ids, anchor);
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

  // Direct rotation angle (slider or number input)
  const handleRotateDirect = (targetDeg: number, commitToHistory: boolean) => {
    if (!activeSlotId) return;
    const clamped = clampTransform({
      ...currentTransform,
      rotation_deg: targetDeg,
    });
    handleTransformChange(activeSlotId, clamped, commitToHistory);
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

  const filledSlotsCount = useMemo(() => {
    if (!editState) return 0;
    return Object.keys(editState.slot_edits).length;
  }, [editState]);

  const renderEligibility = useMemo(() => {
    if (!template || !editState) {
      return {
        canRender: false,
        filledCount: 0,
        minimumRequired: 1,
        totalSlots: 0,
        missingForRequirement: 1,
        requireAll: true,
        statusMessage: "Nenhum template selecionado",
      };
    }
    return checkRenderEligibility(
      template.id,
      template.slots.map((s) => s.id),
      Object.keys(editState.slot_edits)
    );
  }, [template, editState]);

  // Render Job
  const handleRender = async () => {
    if (!editState || !template) return;

    if (!renderEligibility.canRender) {
      setErrorMessage(renderEligibility.statusMessage);
      return;
    }

    try {
      setRendering(true);
      setErrorMessage(null);
      setRenderResult(null);

      const res = await bridge.renderJob(editState);
      setRenderResult(res);

      // Best-effort auto-reveal in Windows Explorer
      try {
        await bridge.openOutputFolder(res.output_path);
      } catch {
        // Auto-reveal failure does not invalidate successful render
      }
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
                const isSelectedSecondary = selectedSlotIds.includes(s.id) && !isActive;
                const hasPhoto = !!editState?.slot_edits[s.id];
                return (
                  <button
                    key={s.id}
                    onClick={(e) => handleSelectSlot(s.id, { shiftKey: e.shiftKey })}
                    style={{
                      padding: "4px 10px",
                      borderRadius: "4px",
                      border: isActive
                        ? mode === "manager"
                          ? "2px solid #38bdf8"
                          : "2px solid #3b82f6"
                        : isSelectedSecondary
                        ? "2px solid #06b6d4"
                        : "1px solid #334155",
                      backgroundColor: isActive
                        ? mode === "manager"
                          ? "#0369a1"
                          : "#1e3a8a"
                        : isSelectedSecondary
                        ? "#164e63"
                        : hasPhoto
                        ? "#1e293b"
                        : "#0f172a",
                      color: isActive
                        ? "#ffffff"
                        : isSelectedSecondary
                        ? "#a5f3fc"
                        : hasPhoto
                        ? "#e2e8f0"
                        : "#64748b",
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
                  {selectedSlotIds.length > 1 ? (
                    <button
                      className="btn-secondary"
                      onClick={handleDuplicateSelected}
                      style={{
                        fontSize: "12px",
                        padding: "5px 12px",
                        backgroundColor: "#0e7490",
                        color: "#ecfeff",
                        border: "1px solid #06b6d4",
                      }}
                      title={`Duplicar os ${selectedSlotIds.length} slots selecionados para os próximos campos vazios`}
                    >
                      ⧉ Duplicar selecionados ({selectedSlotIds.length})
                    </button>
                  ) : (
                    <button
                      className="btn-secondary"
                      onClick={handleDuplicateToNextSlot}
                      disabled={!currentSlotEdit}
                      style={{ fontSize: "12px", padding: "5px 12px", backgroundColor: "#1e293b" }}
                      title="Duplicar enquadramento para o próximo slot (ou dê duplo clique no slot)"
                    >
                      ⏩ Duplicar para próximo
                    </button>
                  )}
                  <button
                    className="btn-secondary"
                    onClick={handleFillRemainingSlots}
                    disabled={!currentSlotEdit || emptySlotsCount === 0}
                    style={{ fontSize: "12px", padding: "5px 12px", backgroundColor: "#1e293b" }}
                    title={
                      currentSlotEdit
                        ? `Preencher ${emptySlotsCount} campo(s) vazio(s) com a foto selecionada`
                        : "Selecione um slot com foto para preencher os campos vazios"
                    }
                  >
                    ⚡ Preencher restantes ({emptySlotsCount})
                  </button>
                </>
              )}

              {currentSlotEdit && (
                <button
                  className="btn-secondary"
                  onClick={handleClearSlot}
                  style={{ fontSize: "12px", padding: "5px 10px", color: "#f87171" }}
                  title="Remover foto do slot selecionado (Delete)"
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
              selectedSlotIds={selectedSlotIds}
              onSelectSlot={handleSelectSlot}
              slotEdits={editState?.slot_edits || {}}
              sources={sources}
              onTransformChange={handleTransformChange}
              layout={previewLayout}
              onDoubleClickSlot={handleDoubleClickSlot}
              mode={mode}
              draft={draft}
              onDraftSlotChange={handleDraftSlotChange}
              onDropPhoto={handleDropAssetOnSlot}
              geometryLocked={isGeometryLocked}
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
            isGeometryLocked={isGeometryLocked}
            onUnlockGeometry={() => setIsManagerGeometryUnlocked(true)}
            onLockGeometry={() => setIsManagerGeometryUnlocked(false)}
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
                <span style={{ color: "#94a3b8" }}>{currentTransform.rotation_deg.toFixed(1)}°</span>
              </div>
              <div style={{ display: "flex", gap: "8px", alignItems: "center", marginBottom: "8px" }}>
                <input
                  type="range"
                  min="-180"
                  max="179"
                  step="1"
                  value={Math.round(currentTransform.rotation_deg)}
                  onChange={(e) => handleRotateDirect(parseFloat(e.target.value), false)}
                  onPointerUp={() => handleRotateDirect(currentTransform.rotation_deg, true)}
                  onKeyUp={() => handleRotateDirect(currentTransform.rotation_deg, true)}
                  disabled={!activeAsset}
                  style={{ flex: 1, accentColor: "#3b82f6" }}
                  title="Ajuste fino de rotação (-180° a +179°)"
                />
                <input
                  type="number"
                  min="-180"
                  max="180"
                  step="0.1"
                  value={Number(currentTransform.rotation_deg.toFixed(1))}
                  onChange={(e) => {
                    const val = parseFloat(e.target.value);
                    if (!Number.isNaN(val)) {
                      handleRotateDirect(val, false);
                    }
                  }}
                  onBlur={() => handleRotateDirect(currentTransform.rotation_deg, true)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      handleRotateDirect(currentTransform.rotation_deg, true);
                    }
                  }}
                  disabled={!activeAsset}
                  style={{
                    width: "60px",
                    padding: "4px 6px",
                    backgroundColor: "#0f172a",
                    border: "1px solid #334155",
                    borderRadius: "4px",
                    color: "#f8fafc",
                    fontSize: "12px",
                    textAlign: "right",
                  }}
                  title="Ângulo exato em graus (-180° a +180°)"
                />
                <span style={{ fontSize: "12px", color: "#94a3b8" }}>°</span>
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

            {trayNotice && (
              <div
                style={{
                  padding: "8px 12px",
                  marginBottom: "12px",
                  borderRadius: "6px",
                  backgroundColor: "#0f172a",
                  border: "1px solid #38bdf8",
                  color: "#38bdf8",
                  fontSize: "12px",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <span>ℹ️ {trayNotice}</span>
                <button
                  onClick={() => setTrayNotice(null)}
                  style={{
                    background: "transparent",
                    border: "none",
                    color: "#94a3b8",
                    cursor: "pointer",
                    fontSize: "12px",
                    padding: "0 4px",
                  }}
                  title="Fechar aviso"
                >
                  ✕
                </button>
              </div>
            )}

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
                    draggable={true}
                    onDragStart={(e) => {
                      e.dataTransfer.setData("application/x-evydencia-source", s.id);
                      e.dataTransfer.setData("text/plain", s.id);
                      e.dataTransfer.effectAllowed = "copy";
                    }}
                    onClick={() => handleSelectSource(s)}
                    title="Clique para atribuir ao slot ativo ou arraste para um slot no produto"
                    style={{
                      cursor: "grab",
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
            disabled={rendering || !renderEligibility.canRender}
            title={!renderEligibility.canRender ? renderEligibility.statusMessage : "Gerar impressão final"}
          >
            {rendering ? "GERANDO ARQUIVO ORIGINAL..." : "GERAR ARQUIVO DE PRODUÇÃO"}
          </button>
        </footer>
      )}
    </div>
  );
};
