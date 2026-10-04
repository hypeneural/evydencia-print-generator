/**
 * Pure preview-layout calculation defined by Gate 3 / PR UI-B.
 * Computes the fitted display dimensions preserving physical aspect ratio.
 */

export interface PreviewLayout {
  fitScale: number;
  displayWidth: number;
  displayHeight: number;
}

export function computePreviewLayout(
  productionWidth: number,
  productionHeight: number,
  containerWidth: number,
  containerHeight: number,
  padding: number = 48
): PreviewLayout {
  if (productionWidth <= 0 || productionHeight <= 0) {
    throw new Error("Production dimensions must be strictly positive");
  }

  const availW = Math.max(1, containerWidth - padding * 2);
  const availH = Math.max(1, containerHeight - padding * 2);

  const scaleX = availW / productionWidth;
  const scaleY = availH / productionHeight;
  const fitScale = Math.min(scaleX, scaleY, 1.0);

  const displayWidth = Math.round(productionWidth * fitScale);
  const displayHeight = Math.round(productionHeight * fitScale);

  return {
    fitScale,
    displayWidth,
    displayHeight,
  };
}
