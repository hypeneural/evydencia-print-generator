/**
 * Pure domain logic for keychain (chaveiro-3x4) customer identification header.
 *
 * Requirements:
 * - Top header strip showing deduplicated client labels in slot order.
 * - Format: 'JOÃO 1510 | MARIA 4545 | LAIS 1010'.
 * - Parity between React preview and Python composition.
 */

import type { TemplateModel, EditStateModel, SourceAssetModel } from "./types";

const GENERIC_NAMES = new Set([
  "desktop",
  "downloads",
  "temp",
  "tmp",
  "fotos",
  "foto_teste",
  "artes natal",
  "print",
  "evydencia-print-generator",
  "output",
  "dist",
  "raw",
  "camera",
  "chaveiro",
  "globo",
  "calendario",
]);

export function cleanWordName(raw: string): string {
  let cleaned = raw.replace(/\b(pedido|cliente|foto|fotos|img|dsc|0m4a|canon|nikon)\b/gi, "");
  cleaned = cleaned.replace(/^[\s\-_#]+|[\s\-_#]+$/g, "");
  const words = (cleaned.match(/[\p{L}]+/gu) || []).filter((w) => !/^\d+$/.test(w));
  if (words.length === 0) return "";
  const first = words[0].toUpperCase();
  if (words.length >= 2 && ["DE", "DA", "DO", "DOS", "DAS", "ANA"].includes(first)) {
    return `${first} ${words[1].toUpperCase()}`;
  }
  return first;
}

export function extractClientLabel(displayName: string): string {
  if (!displayName) return "";
  const stem = displayName.replace(/\.[a-zA-Z0-9]+$/, "").trim();
  if (!stem) return "";

  // Pattern 1: EvydFlow standard 4-part (<Nome> - <Telefone> - <Pacote> - <ID>)
  const parts = stem.split(" - ").map((p) => p.trim());
  if (parts.length === 4 && /^\d+$/.test(parts[3])) {
    const cleanName = cleanWordName(parts[0]);
    const orderId = parts[3];
    return cleanName ? `${cleanName} ${orderId}` : orderId;
  }

  // Pattern 2: <ID> - <Nome> or <ID> _ <Nome> (e.g. "1510 - JOÃO")
  const m2 = stem.match(/^(\d{1,18})\s*[-_ ]\s*([^\d\-_].+)$/);
  if (m2) {
    const orderId = m2[1].trim();
    const cleanName = cleanWordName(m2[2]);
    return cleanName ? `${cleanName} ${orderId}` : orderId;
  }

  // Pattern 3: <Nome> - <ID> or <Nome> <ID> (e.g. "JOÃO 1510", "MARIA 4545", "LAIS 1010")
  const m3 = stem.match(/^([^\d#]+?)\s*[-_# ]\s*#?(\d{1,18})$/);
  if (m3) {
    const cleanName = cleanWordName(m3[1]);
    const orderId = m3[2].trim();
    return cleanName ? `${cleanName} ${orderId}` : orderId;
  }

  // Pattern 4: Pedido #<ID> - <Nome> or #<ID> <Nome>
  const m4 = stem.match(/(?:pedido\s*#?|#)(\d{1,18})/i);
  if (m4) {
    const orderId = m4[1].trim();
    const rest = stem.replace(/(?:pedido\s*#?|#)\d{1,18}/gi, "");
    const cleanName = cleanWordName(rest);
    return cleanName ? `${cleanName} ${orderId}` : orderId;
  }

  // Pattern 5: Fallback name without ID
  const cleanOnly = cleanWordName(stem);
  if (cleanOnly && !GENERIC_NAMES.has(cleanOnly.toLowerCase())) {
    return cleanOnly;
  }

  return "";
}

export function buildKeychainHeaderText(
  template: TemplateModel | null | undefined,
  editState: EditStateModel | null | undefined,
  sources: SourceAssetModel[]
): string {
  if (!template || template.id !== "chaveiro-3x4" || !editState) {
    return "";
  }

  const sourcesById = new Map<string, SourceAssetModel>();
  for (const src of sources) {
    sourcesById.set(src.id, src);
  }

  const seen = new Set<string>();
  const labels: string[] = [];

  for (const slot of template.slots) {
    const edit = editState.slot_edits[slot.id];
    if (!edit || !edit.source_id) continue;

    const source = sourcesById.get(edit.source_id);
    if (!source) continue;

    const label = source.client_label || extractClientLabel(source.display_name);
    if (label && !seen.has(label)) {
      seen.add(label);
      labels.push(label);
    }
  }

  return labels.join(" | ");
}
