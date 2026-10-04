import React, { useEffect, useRef, useCallback } from "react";
import { Canvas as FabricCanvas, FabricImage, Rect } from "fabric";
import type { PreviewLayout } from "../domain/layout";
import type { SlotTransform } from "../domain/transform";
import {
  panBySlotDelta,
  resolvePlacement,
  clampTransform,
} from "../domain/transform";
import type {
  SlotEditState,
  SourceAssetModel,
  TemplateModel,
} from "../domain/types";

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
}

export const ProductCanvas: React.FC<ProductCanvasProps> = ({
  template,
  activeSlotId,
  onSelectSlot,
  slotEdits,
  sources,
  onTransformChange,
  layout,
  onDoubleClickSlot,
}) => {
  const canvasElRef = useRef<HTMLCanvasElement | null>(null);
  const fabricRef = useRef<FabricCanvas | null>(null);

  // Persistent scene objects (Gate 5)
  const slotImagesRef = useRef<Map<string, FabricImage>>(new Map());
  const loadedSourceIdsRef = useRef<Map<string, string>>(new Map());
  const overlayImgRef = useRef<FabricImage | null>(null);
  const activeBorderRef = useRef<Rect | null>(null);

  // Interaction refs
  const isDraggingRef = useRef(false);
  const lastPointerRef = useRef<{ x: number; y: number } | null>(null);
  const transientTransformRef = useRef<Map<string, SlotTransform>>(new Map());
  const wheelCommitTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const rafPendingRef = useRef(false);

  // Synchronized prop refs
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

      const currentTpl = templateRef.current;
      const slot = currentTpl.slots.find((s) => s.id === slotId);
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

  // Initialize Fabric Canvas & Interaction Events
  useEffect(() => {
    if (!canvasElRef.current) return;

    const fabric = new FabricCanvas(canvasElRef.current, {
      width: canvasW,
      height: canvasH,
      backgroundColor: "#ffffff",
      selection: false,
      renderOnAddRemove: false,
    });
    fabricRef.current = fabric;

    fabric.setDimensions(
      { width: `${layout.displayWidth}px`, height: `${layout.displayHeight}px` },
      { cssOnly: true }
    );

    // 1. Static Base Scene: Background & Placeholders
    const bg = new Rect({
      left: 0,
      top: 0,
      width: canvasW,
      height: canvasH,
      fill: "#ffffff",
      selectable: false,
      evented: false,
    });
    fabric.add(bg);

    for (const slot of template.slots) {
      const r = slot.rect_px;
      const placeholder = new Rect({
        left: r.left,
        top: r.top,
        width: r.width,
        height: r.height,
        fill: "#f8fafc",
        selectable: false,
        evented: false,
      });
      fabric.add(placeholder);

      // Subtle cut guideline for slots
      const border = new Rect({
        left: r.left,
        top: r.top,
        width: r.width,
        height: r.height,
        fill: "transparent",
        stroke: "#cbd5e1",
        strokeWidth: 1,
        selectable: false,
        evented: false,
      });
      fabric.add(border);
    }

    // 2. Active slot indicator (created once, updated dynamically)
    const initialActiveSlot = template.slots.find((s) => s.id === activeSlotIdRef.current);
    const activeBorder = new Rect({
      left: initialActiveSlot?.rect_px.left || 0,
      top: initialActiveSlot?.rect_px.top || 0,
      width: initialActiveSlot?.rect_px.width || 0,
      height: initialActiveSlot?.rect_px.height || 0,
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

    // 3. Load static decorative overlay if template has one
    let isCancelled = false;
    if (template.overlay?.url) {
      FabricImage.fromURL(template.overlay.url, { crossOrigin: "anonymous" })
        .then((overlayImg) => {
          if (isCancelled || !fabricRef.current) return;
          overlayImg.set({
            left: 0,
            top: 0,
            scaleX: canvasW / (overlayImg.width || canvasW),
            scaleY: canvasH / (overlayImg.height || canvasH),
            selectable: false,
            evented: false,
          });
          fabric.add(overlayImg);
          overlayImgRef.current = overlayImg;
          fabric.bringObjectToFront(activeBorder);
          scheduleRender();
        })
        .catch((err) => {
          console.warn("Failed to load overlay image:", err);
        });
    }

    scheduleRender();

    // Mouse handlers for drag
    fabric.on("mouse:down", (opt) => {
      if (!opt.scenePoint) return;
      const { x, y } = opt.scenePoint;

      // Detect which slot was clicked
      const currentTpl = templateRef.current;
      const clickedSlot = currentTpl.slots.find((s) => {
        const r = s.rect_px;
        return x >= r.left && x <= r.left + r.width && y >= r.top && y <= r.top + r.height;
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
      const { x, y } = opt.scenePoint;

      const currentTpl = templateRef.current;
      const clickedSlot = currentTpl.slots.find((s) => {
        const r = s.rect_px;
        return x >= r.left && x <= r.left + r.width && y >= r.top && y <= r.top + r.height;
      });

      if (clickedSlot && onDoubleClickSlotRef.current) {
        onDoubleClickSlotRef.current(clickedSlot.id);
      }
    });

    fabric.on("mouse:move", (opt) => {
      if (!isDraggingRef.current || !lastPointerRef.current || !opt.scenePoint) return;
      const currentSlotId = activeSlotIdRef.current;
      const currentTpl = templateRef.current;
      const currentEdit = slotEditsRef.current[currentSlotId];
      if (!currentEdit) return;

      const currentAsset = sourcesRef.current.find((s) => s.id === currentEdit.source_id);
      if (!currentAsset) return;

      const slot = currentTpl.slots.find((s) => s.id === currentSlotId);
      if (!slot) return;

      const { x, y } = opt.scenePoint;
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

    // Mouse wheel for zoom
    const handleWheel = (e: WheelEvent) => {
      e.preventDefault();
      const currentSlotId = activeSlotIdRef.current;
      const currentEdit = slotEditsRef.current[currentSlotId];
      if (!currentEdit) return;

      const factor = e.deltaY < 0 ? 1.05 : 0.95;
      const curT: SlotTransform = transientTransformRef.current.get(currentSlotId) || {
        pan_x_norm: currentEdit.pan_x_norm,
        pan_y_norm: currentEdit.pan_y_norm,
        scale: currentEdit.scale,
        rotation_deg: currentEdit.rotation_deg,
      };
      const newScale = curT.scale * factor;
      const clamped = clampTransform({ ...curT, scale: newScale });

      transientTransformRef.current.set(currentSlotId, clamped);
      applyImageTransform(currentSlotId, clamped);

      // Debounce commit to history
      if (wheelCommitTimeoutRef.current) {
        clearTimeout(wheelCommitTimeoutRef.current);
      }
      wheelCommitTimeoutRef.current = setTimeout(() => {
        onTransformChangeRef.current(currentSlotId, clamped, true);
      }, 300);
    };

    const canvasEl = canvasElRef.current;
    canvasEl.addEventListener("wheel", handleWheel, { passive: false });

    return () => {
      isCancelled = true;
      if (wheelCommitTimeoutRef.current) {
        clearTimeout(wheelCommitTimeoutRef.current);
      }
      canvasEl.removeEventListener("wheel", handleWheel);
      fabric.dispose();
      fabricRef.current = null;
      slotImagesRef.current.clear();
      loadedSourceIdsRef.current.clear();
      overlayImgRef.current = null;
      activeBorderRef.current = null;
    };
  }, [canvasW, canvasH, template, scheduleRender, applyImageTransform]);

  // Synchronize CSS display dimensions when layout changes
  useEffect(() => {
    const fabric = fabricRef.current;
    if (!fabric) return;
    fabric.setDimensions(
      { width: `${layout.displayWidth}px`, height: `${layout.displayHeight}px` },
      { cssOnly: true }
    );
  }, [layout.displayWidth, layout.displayHeight]);

  // Synchronize Active Slot Border Position
  useEffect(() => {
    const border = activeBorderRef.current;
    if (!border) return;

    const currentTpl = templateRef.current;
    const slot = currentTpl.slots.find((s) => s.id === activeSlotId);
    if (slot) {
      border.set({
        left: slot.rect_px.left,
        top: slot.rect_px.top,
        width: slot.rect_px.width,
        height: slot.rect_px.height,
        visible: true,
      });
      if (fabricRef.current) {
        fabricRef.current.bringObjectToFront(border);
      }
    } else {
      border.set({ visible: false });
    }
    scheduleRender();
  }, [activeSlotId, scheduleRender]);

  // Synchronize Slot Photos & Transforms (Persistent Scene)
  useEffect(() => {
    let isCancelled = false;

    async function syncPhotos() {
      const curFabric = fabricRef.current;
      if (!curFabric) return;

      for (const slot of template.slots) {
        const edit = slotEdits[slot.id];
        const loadedSourceId = loadedSourceIdsRef.current.get(slot.id);

        if (!edit) {
          // Remove photo if slot was cleared
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
              const img = await FabricImage.fromURL(previewUrl, { crossOrigin: "anonymous" });
              if (isCancelled || !fabricRef.current) return;

              // Remove previous image for this slot if any
              const oldImg = slotImagesRef.current.get(slot.id);
              if (oldImg) {
                curFabric.remove(oldImg);
              }

              const previewW = img.width || asset.probe.oriented_width || asset.probe.width;
              const previewH = img.height || asset.probe.oriented_height || asset.probe.height;

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

              // Maintain z-index: overlay and active border remain on top
              if (overlayImgRef.current) {
                curFabric.bringObjectToFront(overlayImgRef.current);
              }
              if (activeBorderRef.current) {
                curFabric.bringObjectToFront(activeBorderRef.current);
              }

              scheduleRender();
            } catch (err) {
              console.warn(`Failed to load photo for slot ${slot.id}:`, err);
            }
          }
        } else {
          // Case B: Same source, transform updated via props (e.g. Undo/Redo or Slider)
          if (!isDraggingRef.current) {
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
  }, [template, slotEdits, sources, scheduleRender, applyImageTransform]);

  return (
    <div
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
      <canvas ref={canvasElRef} width={canvasW} height={canvasH} />
    </div>
  );
};
