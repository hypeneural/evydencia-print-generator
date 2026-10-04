import React, { useEffect, useRef } from "react";
import { Canvas as FabricCanvas, FabricImage, Rect } from "fabric";
import type { SlotTransform } from "../domain/transform";
import {
  panBySlotDelta,
  resolvePlacement,
  clampTransform,
} from "../domain/transform";
import type { SlotSpec, SourceAssetModel, TemplateModel } from "../domain/types";

interface CalendarCanvasProps {
  template: TemplateModel;
  slot: SlotSpec;
  asset: SourceAssetModel | null;
  transform: SlotTransform;
  onTransformChange: (transform: SlotTransform, commitToHistory: boolean) => void;
  scaleViewport: number;
}

export const CalendarCanvas: React.FC<CalendarCanvasProps> = ({
  template,
  slot,
  asset,
  transform,
  onTransformChange,
  scaleViewport,
}) => {
  const canvasElRef = useRef<HTMLCanvasElement | null>(null);
  const fabricRef = useRef<FabricCanvas | null>(null);
  const photoObjRef = useRef<FabricImage | null>(null);
  const overlayObjRef = useRef<FabricImage | null>(null);
  const isDraggingRef = useRef(false);
  const lastPointerRef = useRef<{ x: number; y: number } | null>(null);
  const transformRef = useRef(transform);
  transformRef.current = transform;

  const canvasW = template.canvas_px.width;
  const canvasH = template.canvas_px.height;

  // Initialize Fabric Canvas once
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

    // Background base
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

    // Slot border / placeholder indicator
    const slotBorder = new Rect({
      left: slot.rect_px.left,
      top: slot.rect_px.top,
      width: slot.rect_px.width,
      height: slot.rect_px.height,
      fill: "#f8f9fa",
      stroke: "#cbd5e1",
      strokeWidth: 2,
      strokeDashArray: [6, 6],
      selectable: false,
      evented: false,
    });
    fabric.add(slotBorder);

    fabric.requestRenderAll();

    // Event handlers for drag & zoom
    fabric.on("mouse:down", (opt) => {
      if (!opt.scenePoint) return;
      const { x, y } = opt.scenePoint;
      // Check if clicked inside slot
      const r = slot.rect_px;
      if (x >= r.left && x <= r.left + r.width && y >= r.top && y <= r.top + r.height) {
        isDraggingRef.current = true;
        lastPointerRef.current = { x, y };
      }
    });

    fabric.on("mouse:move", (opt) => {
      if (!isDraggingRef.current || !lastPointerRef.current || !opt.scenePoint || !asset) return;
      const { x, y } = opt.scenePoint;
      const dx = x - lastPointerRef.current.x;
      const dy = y - lastPointerRef.current.y;
      lastPointerRef.current = { x, y };

      const sw = asset.probe.oriented_width;
      const sh = asset.probe.oriented_height;
      const rw = slot.rect_px.width;
      const rh = slot.rect_px.height;

      const nextTransform = panBySlotDelta(sw, sh, rw, rh, transformRef.current, dx, dy);
      onTransformChange(nextTransform, false);
    });

    fabric.on("mouse:up", () => {
      if (isDraggingRef.current) {
        isDraggingRef.current = false;
        lastPointerRef.current = null;
        // Commit drag action to undo/redo history
        onTransformChange(transformRef.current, true);
      }
    });

    fabric.on("mouse:wheel", (opt) => {
      if (!opt.scenePoint || !asset) return;
      const { x, y } = opt.scenePoint;
      const r = slot.rect_px;
      if (x >= r.left && x <= r.left + r.width && y >= r.top && y <= r.top + r.height) {
        opt.e.preventDefault();
        opt.e.stopPropagation();
        const delta = opt.e.deltaY < 0 ? 0.05 : -0.05;
        const nextScale = Math.min(8.0, Math.max(1.0, transformRef.current.scale + delta));
        const nextTransform = clampTransform({
          ...transformRef.current,
          scale: nextScale,
        });
        onTransformChange(nextTransform, true);
      }
    });

    return () => {
      fabric.dispose();
      fabricRef.current = null;
    };
  }, [canvasW, canvasH, slot]);

  // Load / Update Photo inside Slot
  useEffect(() => {
    const fabric = fabricRef.current;
    if (!fabric) return;

    if (!asset || !asset.preview.url || asset.preview.status !== "ready") {
      if (photoObjRef.current) {
        fabric.remove(photoObjRef.current);
        photoObjRef.current = null;
        fabric.requestRenderAll();
      }
      return;
    }

    const previewUrl = asset.preview.url;
    FabricImage.fromURL(previewUrl, { crossOrigin: "anonymous" }).then((fImg) => {
      if (!fabricRef.current) return;
      if (photoObjRef.current) {
        fabric.remove(photoObjRef.current);
      }

      // Slot clipping mask
      const clipRect = new Rect({
        left: slot.rect_px.left,
        top: slot.rect_px.top,
        width: slot.rect_px.width,
        height: slot.rect_px.height,
        absolutePositioned: true,
      });

      fImg.clipPath = clipRect;
      fImg.selectable = false;
      fImg.evented = false;
      fImg.originX = "center";
      fImg.originY = "center";

      photoObjRef.current = fImg;
      // Insert photo below overlay
      fabric.insertAt(1, fImg);
      updatePhotoPlacement();
      fabric.requestRenderAll();
    });
  }, [asset?.preview.url, asset?.preview.status, slot]);

  // Load locked overlay
  useEffect(() => {
    const fabric = fabricRef.current;
    if (!fabric || !template.overlay?.url) return;

    FabricImage.fromURL(template.overlay.url, { crossOrigin: "anonymous" }).then((overlayImg) => {
      if (!fabricRef.current) return;
      if (overlayObjRef.current) {
        fabric.remove(overlayObjRef.current);
      }
      overlayImg.set({
        left: 0,
        top: 0,
        scaleX: canvasW / overlayImg.width,
        scaleY: canvasH / overlayImg.height,
        selectable: false,
        evented: false, // pointer events pass through to slot
      });
      overlayObjRef.current = overlayImg;
      fabric.add(overlayImg);
      fabric.requestRenderAll();
    });
  }, [template.overlay?.url, canvasW, canvasH]);

  // Update photo transform placement when transform changes
  const updatePhotoPlacement = () => {
    const fImg = photoObjRef.current;
    if (!fImg || !asset) return;

    const sw = asset.probe.oriented_width;
    const sh = asset.probe.oriented_height;
    const rw = slot.rect_px.width;
    const rh = slot.rect_px.height;

    const p = resolvePlacement(sw, sh, rw, rh, transform);

    // Ratio between original image dimensions and loaded preview proxy dimensions
    const previewScaleRatioX = sw / (fImg.width || 1);
    const previewScaleRatioY = sh / (fImg.height || 1);

    fImg.set({
      left: slot.rect_px.left + p.center_x,
      top: slot.rect_px.top + p.center_y,
      scaleX: p.effective_scale * previewScaleRatioX,
      scaleY: p.effective_scale * previewScaleRatioY,
      angle: p.rotation_deg,
    });
  };

  useEffect(() => {
    const fabric = fabricRef.current;
    if (!fabric) return;
    updatePhotoPlacement();
    fabric.requestRenderAll();
  }, [transform, asset]);

  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        width: "100%",
        height: "100%",
        overflow: "hidden",
        backgroundColor: "#1e293b",
      }}
    >
      <div
        style={{
          transform: `scale(${scaleViewport})`,
          transformOrigin: "center center",
          boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.4), 0 8px 10px -6px rgba(0, 0, 0, 0.4)",
          borderRadius: "4px",
          overflow: "hidden",
        }}
      >
        <canvas ref={canvasElRef} />
      </div>
    </div>
  );
};
