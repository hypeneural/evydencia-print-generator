import React, { useEffect, useRef } from "react";
import { Canvas as FabricCanvas, FabricImage, Rect } from "fabric";
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
  scaleViewport: number;
}

export const ProductCanvas: React.FC<ProductCanvasProps> = ({
  template,
  activeSlotId,
  onSelectSlot,
  slotEdits,
  sources,
  onTransformChange,
  scaleViewport,
}) => {
  const canvasElRef = useRef<HTMLCanvasElement | null>(null);
  const fabricRef = useRef<FabricCanvas | null>(null);
  const isDraggingRef = useRef(false);
  const lastPointerRef = useRef<{ x: number; y: number } | null>(null);

  // References for current props in event handlers
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

  const canvasW = template.canvas_px.width;
  const canvasH = template.canvas_px.height;

  // Initialize Fabric Canvas
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

      const curT: SlotTransform = {
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

      onTransformChangeRef.current(currentSlotId, newT, false);
    });

    fabric.on("mouse:up", () => {
      if (isDraggingRef.current) {
        isDraggingRef.current = false;
        lastPointerRef.current = null;
        const currentSlotId = activeSlotIdRef.current;
        const currentEdit = slotEditsRef.current[currentSlotId];
        if (currentEdit) {
          const curT: SlotTransform = {
            pan_x_norm: currentEdit.pan_x_norm,
            pan_y_norm: currentEdit.pan_y_norm,
            scale: currentEdit.scale,
            rotation_deg: currentEdit.rotation_deg,
          };
          onTransformChangeRef.current(currentSlotId, curT, true);
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
      const curT: SlotTransform = {
        pan_x_norm: currentEdit.pan_x_norm,
        pan_y_norm: currentEdit.pan_y_norm,
        scale: currentEdit.scale,
        rotation_deg: currentEdit.rotation_deg,
      };
      const newScale = curT.scale * factor;
      const clamped = clampTransform({ ...curT, scale: newScale });
      onTransformChangeRef.current(currentSlotId, clamped, true);
    };

    const canvasEl = canvasElRef.current;
    canvasEl.addEventListener("wheel", handleWheel, { passive: false });

    return () => {
      canvasEl.removeEventListener("wheel", handleWheel);
      fabric.dispose();
      fabricRef.current = null;
    };
  }, [canvasW, canvasH]);

  // Full re-render when template, slots, edits, or activeSlotId changes
  useEffect(() => {
    const fabric = fabricRef.current;
    if (!fabric) return;

    let isCancelled = false;

    async function renderScene() {
      if (!fabric) return;
      fabric.clear();

      // 1. Base White Canvas
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

      // 2. Render each slot placeholder & photo
      for (const slot of template.slots) {
        const r = slot.rect_px;

        // Slot placeholder background
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

        // Check if slot has photo
        const edit = slotEdits[slot.id];
        if (edit) {
          const asset = sources.find((s) => s.id === edit.source_id);
          const previewUrl = asset?.preview?.url;
          if (previewUrl) {
            try {
              const img = await FabricImage.fromURL(previewUrl, { crossOrigin: "anonymous" });
              if (isCancelled || !fabric) return;

              const previewW = img.width || asset.probe.oriented_width || asset.probe.width;
              const previewH = img.height || asset.probe.oriented_height || asset.probe.height;

              const t: SlotTransform = {
                pan_x_norm: edit.pan_x_norm,
                pan_y_norm: edit.pan_y_norm,
                scale: edit.scale,
                rotation_deg: edit.rotation_deg,
              };

              const placement = resolvePlacement(previewW, previewH, r.width, r.height, t);

              const clip = new Rect({
                left: r.left,
                top: r.top,
                width: r.width,
                height: r.height,
                absolutePositioned: true,
              });

              img.set({
                left: r.left + placement.center_x,
                top: r.top + placement.center_y,
                scaleX: placement.effective_scale,
                scaleY: placement.effective_scale,
                angle: placement.rotation_deg,
                originX: "center",
                originY: "center",
                clipPath: clip,
                selectable: false,
                evented: false,
              });

              fabric.add(img);
            } catch (err) {
              console.warn(`Failed to render photo for slot ${slot.id}:`, err);
            }
          }
        }

        // 3. Slot borders: Highlight active slot vs subtle cut guidelines for others
        const isActive = slot.id === activeSlotId;
        const border = new Rect({
          left: r.left,
          top: r.top,
          width: r.width,
          height: r.height,
          fill: "transparent",
          stroke: isActive ? "#2563eb" : "#cbd5e1",
          strokeWidth: isActive ? 3 : 1,
          strokeDashArray: isActive ? [6, 4] : undefined,
          selectable: false,
          evented: false,
        });
        fabric.add(border);
      }

      // 4. Overlay if template has PNG overlay
      if (template.overlay?.url) {
        try {
          const overlayImg = await FabricImage.fromURL(template.overlay.url, {
            crossOrigin: "anonymous",
          });
          if (isCancelled || !fabric) return;

          overlayImg.set({
            left: 0,
            top: 0,
            scaleX: canvasW / (overlayImg.width || canvasW),
            scaleY: canvasH / (overlayImg.height || canvasH),
            selectable: false,
            evented: false,
          });
          fabric.add(overlayImg);
        } catch (err) {
          console.warn("Failed to load overlay image:", err);
        }
      }

      fabric.requestRenderAll();
    }

    renderScene();

    return () => {
      isCancelled = true;
    };
  }, [template, slotEdits, sources, activeSlotId, canvasW, canvasH]);

  return (
    <div
      style={{
        transform: `scale(${scaleViewport})`,
        transformOrigin: "center center",
        boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
        borderRadius: "4px",
        overflow: "hidden",
        backgroundColor: "#ffffff",
      }}
    >
      <canvas ref={canvasElRef} />
    </div>
  );
};
