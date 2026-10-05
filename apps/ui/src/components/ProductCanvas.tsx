import React, { useEffect, useRef, useCallback, useState } from "react";
import { Canvas as FabricCanvas, FabricImage, Rect } from "fabric";
import type { PreviewLayout } from "../domain/layout";
import type { SlotTransform } from "../domain/transform";
import {
  panBySlotDelta,
  resolvePlacement,
  clampTransform,
} from "../domain/transform";
import type {
  PixelRect,
  SlotEditState,
  SourceAssetModel,
  TemplateModel,
} from "../domain/types";
import type { DraftSlot, TemplateDraft } from "../domain/draft";
import { pxToMm } from "../domain/draft";
import { findSlotAtClientPoint } from "../domain/hittest";

interface ProductCanvasProps {
  template: TemplateModel;
  activeSlotId: string;
  onSelectSlot: (slotId: string) => void;
  slotEdits: Record<string, SlotEditState>;
  sources: SourceAssetModel[];
  onTransformChange: (
    slotId: string,
    transform: SlotTransform,
    commitToHistory: boolean
  ) => void;
  layout: PreviewLayout;
  onDoubleClickSlot?: (slotId: string) => void;
  mode?: "operator" | "manager";
  draft?: TemplateDraft | null;
  onDraftSlotChange?: (slotId: string, updated: DraftSlot) => void;
  onDropPhoto?: (slotId: string, sourceId: string) => void;
  geometryLocked?: boolean;
}

type ManagerDragState =
  | { kind: "none" }
  | {
      kind: "move";
      slotId: string;
      startPointer: { x: number; y: number };
      startRect: PixelRect;
      currentRect?: PixelRect;
    }
  | {
      kind: "resize";
      corner: "nw" | "ne" | "se" | "sw";
      slotId: string;
      startPointer: { x: number; y: number };
      startRect: PixelRect;
      currentRect?: PixelRect;
    };

export const ProductCanvas: React.FC<ProductCanvasProps> = ({
  template,
  activeSlotId,
  onSelectSlot,
  slotEdits,
  sources,
  onTransformChange,
  layout,
  onDoubleClickSlot,
  mode = "operator",
  draft,
  onDraftSlotChange,
  onDropPhoto,
  geometryLocked = false,
}) => {
  const canvasElRef = useRef<HTMLCanvasElement | null>(null);
  const fabricRef = useRef<FabricCanvas | null>(null);

  // Persistent scene objects (Gate 5)
  const slotPlaceholdersRef = useRef<Map<string, Rect>>(new Map());
  const slotBordersRef = useRef<Map<string, Rect>>(new Map());
  const slotImagesRef = useRef<Map<string, FabricImage>>(new Map());
  const loadedSourceIdsRef = useRef<Map<string, string>>(new Map());
  const overlayImgRef = useRef<FabricImage | null>(null);
  const activeBorderRef = useRef<Rect | null>(null);

  // Corner resize handles for manager mode
  const handleNWRef = useRef<Rect | null>(null);
  const handleNERef = useRef<Rect | null>(null);
  const handleSERef = useRef<Rect | null>(null);
  const handleSWRef = useRef<Rect | null>(null);

  // Interaction refs (Operator mode)
  const isDraggingRef = useRef(false);
  const lastPointerRef = useRef<{ x: number; y: number } | null>(null);
  const transientTransformRef = useRef<Map<string, SlotTransform>>(new Map());
  const wheelCommitTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const rafPendingRef = useRef(false);

  // Interaction refs (Manager mode)
  const managerDragRef = useRef<ManagerDragState>({ kind: "none" });

  // Synchronized prop refs
  const modeRef = useRef(mode);
  modeRef.current = mode;

  const geometryLockedRef = useRef(geometryLocked);
  geometryLockedRef.current = geometryLocked;

  const draftRef = useRef(draft);
  draftRef.current = draft;

  const onDraftSlotChangeRef = useRef(onDraftSlotChange);
  onDraftSlotChangeRef.current = onDraftSlotChange;

  const activeSlotIdRef = useRef(activeSlotId);
  activeSlotIdRef.current = activeSlotId;

  const slotEditsRef = useRef(slotEdits);
  slotEditsRef.current = slotEdits;

  const sourcesRef = useRef(sources);
  sourcesRef.current = sources;

  const templateRef = useRef(template);
  templateRef.current = template;

  const onTransformChangeRef = useRef(onTransformChange);
  onTransformChangeRef.current = onTransformChange;

  const onSelectSlotRef = useRef(onSelectSlot);
  onSelectSlotRef.current = onSelectSlot;

  const onDoubleClickSlotRef = useRef(onDoubleClickSlot);
  onDoubleClickSlotRef.current = onDoubleClickSlot;

  const canvasW = template.canvas_px.width;
  const canvasH = template.canvas_px.height;

  // Coalesced render scheduler via requestAnimationFrame (Gate 5)
  const scheduleRender = useCallback(() => {
    if (!rafPendingRef.current) {
      rafPendingRef.current = true;
      requestAnimationFrame(() => {
        rafPendingRef.current = false;
        fabricRef.current?.requestRenderAll();
      });
    }
  }, []);

  // Update object transform properties without reloading images (Gate 5 hot path)
  const applyImageTransform = useCallback(
    (slotId: string, transform: SlotTransform) => {
      const img = slotImagesRef.current.get(slotId);
      if (!img) return;

      const currentSlots =
        modeRef.current === "manager" && draftRef.current
          ? draftRef.current.slots
          : templateRef.current.slots;
      const slot = currentSlots.find((s) => s.id === slotId);
      if (!slot) return;

      const edit = slotEditsRef.current[slotId];
      if (!edit) return;

      const asset = sourcesRef.current.find((s) => s.id === edit.source_id);
      if (!asset) return;

      const previewW = img.width || asset.probe.oriented_width || asset.probe.width;
      const previewH = img.height || asset.probe.oriented_height || asset.probe.height;

      const placement = resolvePlacement(
        previewW,
        previewH,
        slot.rect_px.width,
        slot.rect_px.height,
        transform
      );

      img.set({
        left: slot.rect_px.left + placement.center_x,
        top: slot.rect_px.top + placement.center_y,
        scaleX: placement.effective_scale,
        scaleY: placement.effective_scale,
        angle: placement.rotation_deg,
      });

      scheduleRender();
    },
    [scheduleRender]
  );

  // Update slot visual elements in real-time (placeholder, border, activeBorder, handles, clipPath)
  const updateSlotVisual = useCallback(
    (slotId: string, rect: PixelRect) => {
      const placeholder = slotPlaceholdersRef.current.get(slotId);
      if (placeholder) {
        placeholder.set({
          left: rect.left,
          top: rect.top,
          width: rect.width,
          height: rect.height,
        });
      }

      const border = slotBordersRef.current.get(slotId);
      if (border) {
        border.set({
          left: rect.left,
          top: rect.top,
          width: rect.width,
          height: rect.height,
        });
      }

      if (slotId === activeSlotIdRef.current && activeBorderRef.current) {
        activeBorderRef.current.set({
          left: rect.left,
          top: rect.top,
          width: rect.width,
          height: rect.height,
        });

        // Update manager resize handles
        if (modeRef.current === "manager") {
          handleNWRef.current?.set({ left: rect.left, top: rect.top });
          handleNERef.current?.set({ left: rect.left + rect.width, top: rect.top });
          handleSERef.current?.set({
            left: rect.left + rect.width,
            top: rect.top + rect.height,
          });
          handleSWRef.current?.set({ left: rect.left, top: rect.top + rect.height });
        }
      }

      // Update image clip path and placement if photo exists
      const img = slotImagesRef.current.get(slotId);
      if (img) {
        if (img.clipPath) {
          (img.clipPath as Rect).set({
            left: rect.left,
            top: rect.top,
            width: rect.width,
            height: rect.height,
          });
        }

        const edit = slotEditsRef.current[slotId];
        const asset = sourcesRef.current.find((s) => s.id === edit?.source_id);
        if (edit && asset) {
          const previewW = img.width || asset.probe.oriented_width || asset.probe.width;
          const previewH = img.height || asset.probe.oriented_height || asset.probe.height;
          const placement = resolvePlacement(
            previewW,
            previewH,
            rect.width,
            rect.height,
            {
              pan_x_norm: edit.pan_x_norm,
              pan_y_norm: edit.pan_y_norm,
              scale: edit.scale,
              rotation_deg: edit.rotation_deg,
            }
          );
          img.set({
            left: rect.left + placement.center_x,
            top: rect.top + placement.center_y,
            scaleX: placement.effective_scale,
            scaleY: placement.effective_scale,
            angle: placement.rotation_deg,
          });
        }
      }
    },
    []
  );

  // Initialize Fabric Canvas & Interaction Events
  useEffect(() => {
    if (!canvasElRef.current) return;

    const fabric = new FabricCanvas(canvasElRef.current, {
      width: layout.displayWidth,
      height: layout.displayHeight,
      backgroundColor: "#ffffff",
      selection: false,
      renderOnAddRemove: false,
    });
    fabricRef.current = fabric;

    fabric.setViewportTransform([layout.fitScale, 0, 0, layout.fitScale, 0, 0]);

    // 1. Static Base Scene: Background
    const bg = new Rect({
      left: 0,
      top: 0,
      width: canvasW,
      height: canvasH,
      originX: "left",
      originY: "top",
      fill: "#ffffff",
      selectable: false,
      evented: false,
    });
    fabric.add(bg);

    // Slot placeholders and borders
    slotPlaceholdersRef.current.clear();
    slotBordersRef.current.clear();

    const initialSlots = template.slots;
    for (const slot of initialSlots) {
      const r = slot.rect_px;
      const placeholder = new Rect({
        left: r.left,
        top: r.top,
        width: r.width,
        height: r.height,
        originX: "left",
        originY: "top",
        fill: "#f8fafc",
        selectable: false,
        evented: false,
      });
      fabric.add(placeholder);
      slotPlaceholdersRef.current.set(slot.id, placeholder);

      const border = new Rect({
        left: r.left,
        top: r.top,
        width: r.width,
        height: r.height,
        originX: "left",
        originY: "top",
        fill: "transparent",
        stroke: "#cbd5e1",
        strokeWidth: 1,
        selectable: false,
        evented: false,
      });
      fabric.add(border);
      slotBordersRef.current.set(slot.id, border);
    }

    // 2. Active slot indicator (created once, updated dynamically)
    const initialActiveSlot = initialSlots.find((s) => s.id === activeSlotIdRef.current);
    const activeBorder = new Rect({
      left: initialActiveSlot?.rect_px.left || 0,
      top: initialActiveSlot?.rect_px.top || 0,
      width: initialActiveSlot?.rect_px.width || 0,
      height: initialActiveSlot?.rect_px.height || 0,
      originX: "left",
      originY: "top",
      fill: "transparent",
      stroke: "#2563eb",
      strokeWidth: 3,
      strokeDashArray: [6, 4],
      selectable: false,
      evented: false,
      visible: !!initialActiveSlot,
    });
    fabric.add(activeBorder);
    activeBorderRef.current = activeBorder;

    // 3. Manager Corner Handles
    const createCornerHandle = () =>
      new Rect({
        width: 14,
        height: 14,
        fill: "#ffffff",
        stroke: "#2563eb",
        strokeWidth: 2,
        originX: "center",
        originY: "center",
        selectable: false,
        evented: false,
        visible: false,
      });

    const hNW = createCornerHandle();
    const hNE = createCornerHandle();
    const hSE = createCornerHandle();
    const hSW = createCornerHandle();

    fabric.add(hNW, hNE, hSE, hSW);
    handleNWRef.current = hNW;
    handleNERef.current = hNE;
    handleSERef.current = hSE;
    handleSWRef.current = hSW;

    // 4. Load static decorative overlay if template has one
    let isCancelled = false;
    if (template.overlay?.url) {
      FabricImage.fromURL(template.overlay.url, { crossOrigin: "anonymous" })
        .then((overlayImg) => {
          if (isCancelled || !fabricRef.current) return;
          const naturalW = overlayImg.width || canvasW;
          const naturalH = overlayImg.height || canvasH;
          const overlayAspect = naturalW / naturalH;
          const canvasAspect = canvasW / canvasH;
          const aspectDrift = Math.abs(overlayAspect - canvasAspect) / canvasAspect;

          if (aspectDrift > 0.001) {
            console.error(
              `OVERLAY_GEOMETRY_MISMATCH: overlay aspect ${overlayAspect.toFixed(4)} differs from canvas aspect ${canvasAspect.toFixed(4)} by ${(aspectDrift * 100).toFixed(2)}%`
            );
            return;
          }

          const uniformScale = canvasW / naturalW;
          overlayImg.set({
            left: 0,
            top: 0,
            originX: "left",
            originY: "top",
            scaleX: uniformScale,
            scaleY: uniformScale,
            selectable: false,
            evented: false,
            lockMovementX: true,
            lockMovementY: true,
            hoverCursor: "default",
          });
          fabric.add(overlayImg);
          overlayImgRef.current = overlayImg;
          fabric.bringObjectToFront(overlayImg);
          fabric.bringObjectToFront(activeBorder);
          fabric.bringObjectToFront(hNW);
          fabric.bringObjectToFront(hNE);
          fabric.bringObjectToFront(hSE);
          fabric.bringObjectToFront(hSW);
          scheduleRender();
        })
        .catch((err) => {
          console.warn("Failed to load overlay image:", err);
        });
    }

    scheduleRender();

    // Mouse handlers
    fabric.on("mouse:down", (opt) => {
      if (!opt.scenePoint) return;
      const { x, y } = opt.scenePoint;

      // MANAGER MODE INTERACTION
      if (modeRef.current === "manager") {
        const currentDraft = draftRef.current;
        const slots = currentDraft?.slots || templateRef.current.slots;

        // If geometry is locked, only allow selecting slots without move or resize
        if (geometryLockedRef.current) {
          const clickedSlot = slots.find((s) => {
            const r = s.rect_px;
            return (
              x >= r.left &&
              x <= r.left + r.width &&
              y >= r.top &&
              y <= r.top + r.height
            );
          });
          if (clickedSlot && clickedSlot.id !== activeSlotIdRef.current) {
            onSelectSlotRef.current(clickedSlot.id);
          }
          return;
        }

        const currentSlot = currentDraft?.slots.find(
          (s) => s.id === activeSlotIdRef.current
        );

        // Check if clicked near active slot corner handles
        if (currentSlot) {
          const r = currentSlot.rect_px;
          const hitRadius = 14;
          const corners = [
            { id: "nw" as const, x: r.left, y: r.top },
            { id: "ne" as const, x: r.left + r.width, y: r.top },
            { id: "se" as const, x: r.left + r.width, y: r.top + r.height },
            { id: "sw" as const, x: r.left, y: r.top + r.height },
          ];

          const hitCorner = corners.find(
            (c) => Math.abs(x - c.x) <= hitRadius && Math.abs(y - c.y) <= hitRadius
          );

          if (hitCorner) {
            managerDragRef.current = {
              kind: "resize",
              corner: hitCorner.id,
              slotId: currentSlot.id,
              startPointer: { x, y },
              startRect: { ...r },
            };
            return;
          }
        }

        // Check if clicked inside any slot
        const clickedSlot = slots.find((s) => {
          const r = s.rect_px;
          return (
            x >= r.left &&
            x <= r.left + r.width &&
            y >= r.top &&
            y <= r.top + r.height
          );
        });

        if (clickedSlot) {
          if (clickedSlot.id !== activeSlotIdRef.current) {
            onSelectSlotRef.current(clickedSlot.id);
          }
          managerDragRef.current = {
            kind: "move",
            slotId: clickedSlot.id,
            startPointer: { x, y },
            startRect: { ...clickedSlot.rect_px },
          };
        }
        return;
      }

      // OPERATOR MODE INTERACTION
      const currentTpl = templateRef.current;
      const clickedSlot = currentTpl.slots.find((s) => {
        const r = s.rect_px;
        return (
          x >= r.left &&
          x <= r.left + r.width &&
          y >= r.top &&
          y <= r.top + r.height
        );
      });

      if (clickedSlot) {
        if (clickedSlot.id !== activeSlotIdRef.current) {
          onSelectSlotRef.current(clickedSlot.id);
        }
        isDraggingRef.current = true;
        lastPointerRef.current = { x, y };

        const currentEdit = slotEditsRef.current[clickedSlot.id];
        if (currentEdit) {
          transientTransformRef.current.set(clickedSlot.id, {
            pan_x_norm: currentEdit.pan_x_norm,
            pan_y_norm: currentEdit.pan_y_norm,
            scale: currentEdit.scale,
            rotation_deg: currentEdit.rotation_deg,
          });
        }
      }
    });

    fabric.on("mouse:dblclick", (opt) => {
      if (!opt.scenePoint) return;
      if (modeRef.current === "manager") return;

      const { x, y } = opt.scenePoint;
      const currentTpl = templateRef.current;
      const clickedSlot = currentTpl.slots.find((s) => {
        const r = s.rect_px;
        return (
          x >= r.left &&
          x <= r.left + r.width &&
          y >= r.top &&
          y <= r.top + r.height
        );
      });

      if (clickedSlot && onDoubleClickSlotRef.current) {
        onDoubleClickSlotRef.current(clickedSlot.id);
      }
    });

    fabric.on("mouse:move", (opt) => {
      if (!opt.scenePoint) return;
      const { x, y } = opt.scenePoint;

      // MANAGER MODE MOVE/RESIZE
      if (modeRef.current === "manager") {
        if (geometryLockedRef.current) return;
        const drag = managerDragRef.current;
        if (drag.kind === "move" || drag.kind === "resize") {
          const dx = x - drag.startPointer.x;
          const dy = y - drag.startPointer.y;
          const newRect: PixelRect = { ...drag.startRect };
          const minSize = 20;

          if (drag.kind === "move") {
            newRect.left = Math.max(
              0,
              Math.min(canvasW - drag.startRect.width, drag.startRect.left + dx)
            );
            newRect.top = Math.max(
              0,
              Math.min(canvasH - drag.startRect.height, drag.startRect.top + dy)
            );
          } else if (drag.kind === "resize" && drag.corner) {
            if (drag.corner === "se") {
              newRect.width = Math.max(
                minSize,
                Math.min(canvasW - drag.startRect.left, drag.startRect.width + dx)
              );
              newRect.height = Math.max(
                minSize,
                Math.min(canvasH - drag.startRect.top, drag.startRect.height + dy)
              );
            } else if (drag.corner === "sw") {
              const leftCandidate = Math.max(
                0,
                Math.min(
                  drag.startRect.left + drag.startRect.width - minSize,
                  drag.startRect.left + dx
                )
              );
              newRect.width = drag.startRect.width - (leftCandidate - drag.startRect.left);
              newRect.left = leftCandidate;
              newRect.height = Math.max(
                minSize,
                Math.min(canvasH - drag.startRect.top, drag.startRect.height + dy)
              );
            } else if (drag.corner === "ne") {
              newRect.width = Math.max(
                minSize,
                Math.min(canvasW - drag.startRect.left, drag.startRect.width + dx)
              );
              const topCandidate = Math.max(
                0,
                Math.min(
                  drag.startRect.top + drag.startRect.height - minSize,
                  drag.startRect.top + dy
                )
              );
              newRect.height =
                drag.startRect.height - (topCandidate - drag.startRect.top);
              newRect.top = topCandidate;
            } else if (drag.corner === "nw") {
              const leftCandidate = Math.max(
                0,
                Math.min(
                  drag.startRect.left + drag.startRect.width - minSize,
                  drag.startRect.left + dx
                )
              );
              const topCandidate = Math.max(
                0,
                Math.min(
                  drag.startRect.top + drag.startRect.height - minSize,
                  drag.startRect.top + dy
                )
              );
              newRect.width = drag.startRect.width - (leftCandidate - drag.startRect.left);
              newRect.height =
                drag.startRect.height - (topCandidate - drag.startRect.top);
              newRect.left = leftCandidate;
              newRect.top = topCandidate;
            }
          }

          updateSlotVisual(drag.slotId, newRect);
          drag.currentRect = newRect;
          scheduleRender();
        } else {
          // Hover cursor feedback in manager mode
          const currentDraft = draftRef.current;
          const currentSlot = currentDraft?.slots.find(
            (s) => s.id === activeSlotIdRef.current
          );
          if (currentSlot && fabricRef.current) {
            const r = currentSlot.rect_px;
            const hitRadius = 14;
            const nearNW =
              Math.abs(x - r.left) <= hitRadius && Math.abs(y - r.top) <= hitRadius;
            const nearSE =
              Math.abs(x - (r.left + r.width)) <= hitRadius &&
              Math.abs(y - (r.top + r.height)) <= hitRadius;
            const nearNE =
              Math.abs(x - (r.left + r.width)) <= hitRadius &&
              Math.abs(y - r.top) <= hitRadius;
            const nearSW =
              Math.abs(x - r.left) <= hitRadius &&
              Math.abs(y - (r.top + r.height)) <= hitRadius;

            if (nearNW || nearSE) {
              fabricRef.current.defaultCursor = "nwse-resize";
            } else if (nearNE || nearSW) {
              fabricRef.current.defaultCursor = "nesw-resize";
            } else if (
              x >= r.left &&
              x <= r.left + r.width &&
              y >= r.top &&
              y <= r.top + r.height
            ) {
              fabricRef.current.defaultCursor = "move";
            } else {
              fabricRef.current.defaultCursor = "default";
            }
          }
        }
        return;
      }

      // OPERATOR MODE PAN
      if (!isDraggingRef.current || !lastPointerRef.current) return;
      const currentSlotId = activeSlotIdRef.current;
      const currentTpl = templateRef.current;
      const currentEdit = slotEditsRef.current[currentSlotId];
      if (!currentEdit) return;

      const currentAsset = sourcesRef.current.find((s) => s.id === currentEdit.source_id);
      if (!currentAsset) return;

      const slot = currentTpl.slots.find((s) => s.id === currentSlotId);
      if (!slot) return;

      const dx = x - lastPointerRef.current.x;
      const dy = y - lastPointerRef.current.y;
      lastPointerRef.current = { x, y };

      const curT: SlotTransform = transientTransformRef.current.get(currentSlotId) || {
        pan_x_norm: currentEdit.pan_x_norm,
        pan_y_norm: currentEdit.pan_y_norm,
        scale: currentEdit.scale,
        rotation_deg: currentEdit.rotation_deg,
      };

      const newT = panBySlotDelta(
        currentAsset.probe.oriented_width || currentAsset.probe.width,
        currentAsset.probe.oriented_height || currentAsset.probe.height,
        slot.rect_px.width,
        slot.rect_px.height,
        curT,
        dx,
        dy
      );

      transientTransformRef.current.set(currentSlotId, newT);
      applyImageTransform(currentSlotId, newT);
    });

    fabric.on("mouse:up", () => {
      // MANAGER MODE UP
      if (modeRef.current === "manager") {
        const drag = managerDragRef.current;
        if (
          (drag.kind === "move" || drag.kind === "resize") &&
          drag.currentRect
        ) {
          const dpi =
            draftRef.current?.canvas.dpi || templateRef.current.canvas.dpi;
          const currentSlot = draftRef.current?.slots.find(
            (s) => s.id === drag.slotId
          );
          if (currentSlot && onDraftSlotChangeRef.current) {
            const x_mm = pxToMm(drag.currentRect.left, dpi);
            const y_mm = pxToMm(drag.currentRect.top, dpi);
            const width_mm = pxToMm(drag.currentRect.width, dpi);
            const height_mm = pxToMm(drag.currentRect.height, dpi);

            onDraftSlotChangeRef.current(drag.slotId, {
              ...currentSlot,
              x_mm,
              y_mm,
              width_mm,
              height_mm,
              rect_px: { ...drag.currentRect },
            });
          }
        }
        managerDragRef.current = { kind: "none" };
        return;
      }

      // OPERATOR MODE UP
      if (isDraggingRef.current) {
        isDraggingRef.current = false;
        lastPointerRef.current = null;
        const currentSlotId = activeSlotIdRef.current;
        const finalT = transientTransformRef.current.get(currentSlotId);
        if (finalT) {
          onTransformChangeRef.current(currentSlotId, finalT, true);
        }
      }
    });

    // Mouse wheel for zoom on hovered/active slot (Operator mode only)
    fabric.on("mouse:wheel", (opt) => {
      if (modeRef.current === "manager") return;
      opt.e.preventDefault();
      opt.e.stopPropagation();

      const point = opt.scenePoint;
      if (!point) return;

      const currentSlots = templateRef.current.slots;

      // Check if cursor is over a slot
      const hovered = currentSlots.find((s) => {
        const r = s.rect_px;
        return (
          point.x >= r.left &&
          point.x <= r.left + r.width &&
          point.y >= r.top &&
          point.y <= r.top + r.height
        );
      });

      // Target slot: cursor MUST be directly over a filled slot (Gate 10)
      // Pointer over empty slot or outside canvas is a strict no-op.
      if (!hovered) return;
      const targetSlotId = hovered.id;
      const currentEdit = slotEditsRef.current[targetSlotId];
      if (!currentEdit) return;

      if (targetSlotId !== activeSlotIdRef.current) {
        onSelectSlotRef.current(targetSlotId);
      }

      const factor = opt.e.deltaY < 0 ? 1.05 : 0.95;
      const curT: SlotTransform = transientTransformRef.current.get(targetSlotId) || {
        pan_x_norm: currentEdit.pan_x_norm,
        pan_y_norm: currentEdit.pan_y_norm,
        scale: currentEdit.scale,
        rotation_deg: currentEdit.rotation_deg,
      };
      const newScale = curT.scale * factor;
      const clamped = clampTransform({ ...curT, scale: newScale });

      transientTransformRef.current.set(targetSlotId, clamped);
      applyImageTransform(targetSlotId, clamped);
      // NOTE: ZERO React setState during wheel ticks! (docs/PERFORMANCE_BUDGETS.md)

      // Debounce commit to history and React state at gesture end
      if (wheelCommitTimeoutRef.current) {
        clearTimeout(wheelCommitTimeoutRef.current);
      }
      wheelCommitTimeoutRef.current = setTimeout(() => {
        onTransformChangeRef.current(targetSlotId, clamped, true);
      }, 300);
    });

    return () => {
      isCancelled = true;
      if (wheelCommitTimeoutRef.current) {
        clearTimeout(wheelCommitTimeoutRef.current);
      }
      fabric.dispose();
      fabricRef.current = null;
      slotPlaceholdersRef.current.clear();
      slotBordersRef.current.clear();
      slotImagesRef.current.clear();
      loadedSourceIdsRef.current.clear();
      overlayImgRef.current = null;
      activeBorderRef.current = null;
      handleNWRef.current = null;
      handleNERef.current = null;
      handleSERef.current = null;
      handleSWRef.current = null;
    };
  }, [canvasW, canvasH, template, scheduleRender, applyImageTransform, updateSlotVisual]);

  // Synchronize display dimensions & viewport transform when layout changes
  useEffect(() => {
    const fabric = fabricRef.current;
    if (!fabric) return;
    fabric.setDimensions({
      width: layout.displayWidth,
      height: layout.displayHeight,
    });
    fabric.setViewportTransform([layout.fitScale, 0, 0, layout.fitScale, 0, 0]);
    scheduleRender();
  }, [layout.displayWidth, layout.displayHeight, layout.fitScale, scheduleRender]);

  // Synchronize Active Slot Border and Manager Handles Position & Visibility
  useEffect(() => {
    const border = activeBorderRef.current;
    if (!border) return;

    const currentSlots =
      mode === "manager" && draft ? draft.slots : templateRef.current.slots;
    const slot = currentSlots.find((s) => s.id === activeSlotId);

    const isManager = mode === "manager";

    if (slot) {
      border.set({
        left: slot.rect_px.left,
        top: slot.rect_px.top,
        width: slot.rect_px.width,
        height: slot.rect_px.height,
        stroke: isManager ? "#38bdf8" : "#2563eb",
        strokeDashArray: isManager ? undefined : [6, 4],
        strokeWidth: isManager ? 2 : 3,
        visible: true,
      });

      // Update manager corner handles
      if (handleNWRef.current && handleNERef.current && handleSERef.current && handleSWRef.current) {
        const showHandles = isManager && !geometryLocked;
        handleNWRef.current.set({
          left: slot.rect_px.left,
          top: slot.rect_px.top,
          visible: showHandles,
        });
        handleNERef.current.set({
          left: slot.rect_px.left + slot.rect_px.width,
          top: slot.rect_px.top,
          visible: showHandles,
        });
        handleSERef.current.set({
          left: slot.rect_px.left + slot.rect_px.width,
          top: slot.rect_px.top + slot.rect_px.height,
          visible: showHandles,
        });
        handleSWRef.current.set({
          left: slot.rect_px.left,
          top: slot.rect_px.top + slot.rect_px.height,
          visible: showHandles,
        });
      }

      if (fabricRef.current) {
        fabricRef.current.bringObjectToFront(border);
        if (handleNWRef.current) fabricRef.current.bringObjectToFront(handleNWRef.current);
        if (handleNERef.current) fabricRef.current.bringObjectToFront(handleNERef.current);
        if (handleSERef.current) fabricRef.current.bringObjectToFront(handleSERef.current);
        if (handleSWRef.current) fabricRef.current.bringObjectToFront(handleSWRef.current);
      }
    } else {
      border.set({ visible: false });
      handleNWRef.current?.set({ visible: false });
      handleNERef.current?.set({ visible: false });
      handleSERef.current?.set({ visible: false });
      handleSWRef.current?.set({ visible: false });
    }

    if (!isManager && fabricRef.current) {
      fabricRef.current.defaultCursor = "default";
    }

    scheduleRender();
  }, [activeSlotId, mode, draft, geometryLocked, scheduleRender]);

  // Synchronize slot visual positions when draft updates externally
  useEffect(() => {
    if (mode !== "manager" || !draft) return;
    for (const slot of draft.slots) {
      updateSlotVisual(slot.id, slot.rect_px);
    }
    scheduleRender();
  }, [draft, mode, scheduleRender, updateSlotVisual]);

  // Synchronize Slot Photos & Transforms (Persistent Scene)
  useEffect(() => {
    let isCancelled = false;

    async function syncPhotos() {
      const curFabric = fabricRef.current;
      if (!curFabric) return;

      const currentSlots =
        mode === "manager" && draft ? draft.slots : template.slots;

      for (const slot of currentSlots) {
        const edit = slotEdits[slot.id];
        const loadedSourceId = loadedSourceIdsRef.current.get(slot.id);

        if (!edit) {
          const existingImg = slotImagesRef.current.get(slot.id);
          if (existingImg) {
            curFabric.remove(existingImg);
            slotImagesRef.current.delete(slot.id);
            loadedSourceIdsRef.current.delete(slot.id);
            scheduleRender();
          }
          continue;
        }

        // Case A: Source changed (or first load for this slot)
        if (loadedSourceId !== edit.source_id) {
          const asset = sources.find((s) => s.id === edit.source_id);
          const previewUrl = asset?.preview?.url;
          if (previewUrl) {
            try {
              const img = await FabricImage.fromURL(previewUrl, {
                crossOrigin: "anonymous",
              });
              if (isCancelled || !fabricRef.current) return;

              const oldImg = slotImagesRef.current.get(slot.id);
              if (oldImg) {
                curFabric.remove(oldImg);
              }

              const previewW =
                img.width || asset.probe.oriented_width || asset.probe.width;
              const previewH =
                img.height || asset.probe.oriented_height || asset.probe.height;

              const t: SlotTransform = {
                pan_x_norm: edit.pan_x_norm,
                pan_y_norm: edit.pan_y_norm,
                scale: edit.scale,
                rotation_deg: edit.rotation_deg,
              };

              const placement = resolvePlacement(
                previewW,
                previewH,
                slot.rect_px.width,
                slot.rect_px.height,
                t
              );

              const clip = new Rect({
                left: slot.rect_px.left,
                top: slot.rect_px.top,
                width: slot.rect_px.width,
                height: slot.rect_px.height,
                originX: "left",
                originY: "top",
                absolutePositioned: true,
              });

              img.set({
                left: slot.rect_px.left + placement.center_x,
                top: slot.rect_px.top + placement.center_y,
                scaleX: placement.effective_scale,
                scaleY: placement.effective_scale,
                angle: placement.rotation_deg,
                originX: "center",
                originY: "center",
                clipPath: clip,
                selectable: false,
                evented: false,
              });

              curFabric.add(img);
              slotImagesRef.current.set(slot.id, img);
              loadedSourceIdsRef.current.set(slot.id, edit.source_id);

              // Maintain z-index: overlay, active border, and handles remain on top
              if (overlayImgRef.current) {
                curFabric.bringObjectToFront(overlayImgRef.current);
              }
              if (activeBorderRef.current) {
                curFabric.bringObjectToFront(activeBorderRef.current);
              }
              if (handleNWRef.current) curFabric.bringObjectToFront(handleNWRef.current);
              if (handleNERef.current) curFabric.bringObjectToFront(handleNERef.current);
              if (handleSERef.current) curFabric.bringObjectToFront(handleSERef.current);
              if (handleSWRef.current) curFabric.bringObjectToFront(handleSWRef.current);

              scheduleRender();
            } catch (err) {
              console.warn(`Failed to load photo for slot ${slot.id}:`, err);
            }
          }
        } else {
          // Case B: Same source, transform updated via props
          if (!isDraggingRef.current && managerDragRef.current.kind === "none") {
            applyImageTransform(slot.id, {
              pan_x_norm: edit.pan_x_norm,
              pan_y_norm: edit.pan_y_norm,
              scale: edit.scale,
              rotation_deg: edit.rotation_deg,
            });
          }
        }
      }
    }

    syncPhotos();

    return () => {
      isCancelled = true;
    };
  }, [template, slotEdits, sources, scheduleRender, applyImageTransform, mode, draft]);

  const [dragOverSlotId, setDragOverSlotId] = useState<string | null>(null);
  const dragOverSlotIdRef = useRef<string | null>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "copy";
    if (mode === "manager") return;
    if (!canvasElRef.current) return;
    const rect = canvasElRef.current.getBoundingClientRect();
    const hit = findSlotAtClientPoint(
      template.slots,
      e.clientX,
      e.clientY,
      rect,
      layout.fitScale
    );
    const nextSlotId = hit?.id || null;
    if (dragOverSlotIdRef.current !== nextSlotId) {
      dragOverSlotIdRef.current = nextSlotId;
      setDragOverSlotId(nextSlotId);
    }
  };

  const handleDragLeave = () => {
    if (dragOverSlotIdRef.current !== null) {
      dragOverSlotIdRef.current = null;
      setDragOverSlotId(null);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    dragOverSlotIdRef.current = null;
    setDragOverSlotId(null);
    if (mode === "manager") return;

    const sourceId =
      e.dataTransfer.getData("application/x-evydencia-source") ||
      e.dataTransfer.getData("text/plain");
    if (!sourceId || !onDropPhoto) return;

    if (!canvasElRef.current) return;
    const rect = canvasElRef.current.getBoundingClientRect();
    const hit = findSlotAtClientPoint(
      template.slots,
      e.clientX,
      e.clientY,
      rect,
      layout.fitScale
    );
    if (hit) {
      onDropPhoto(hit.id, sourceId);
    }
  };

  const currentSlots =
    mode === "manager" && draft ? draft.slots : template.slots;
  const dragOverSlot = currentSlots.find((s) => s.id === dragOverSlotId);

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      style={{
        width: `${layout.displayWidth}px`,
        height: `${layout.displayHeight}px`,
        boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
        borderRadius: "4px",
        overflow: "hidden",
        backgroundColor: "#ffffff",
        position: "relative",
      }}
    >
      <canvas ref={canvasElRef} />
      {dragOverSlot && (
        <div
          style={{
            position: "absolute",
            left: `${dragOverSlot.rect_px.left * layout.fitScale}px`,
            top: `${dragOverSlot.rect_px.top * layout.fitScale}px`,
            width: `${dragOverSlot.rect_px.width * layout.fitScale}px`,
            height: `${dragOverSlot.rect_px.height * layout.fitScale}px`,
            border: "2px solid #22c55e",
            backgroundColor: "rgba(34, 197, 94, 0.15)",
            boxSizing: "border-box",
            borderRadius: "2px",
            pointerEvents: "none",
            zIndex: 50,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#22c55e",
            fontWeight: "700",
            fontSize: "13px",
          }}
        >
          Soltar foto aqui
        </div>
      )}
    </div>
  );
};
