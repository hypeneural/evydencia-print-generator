import { describe, it, expect } from "vitest";
import {
  PersonRegular,
  SettingsRegular,
  ArrowUndoRegular,
  ArrowRedoRegular,
  ZoomInRegular,
  ZoomOutRegular,
  ArrowResetRegular,
  ArrowRotateClockwiseRegular,
  DeleteRegular,
  CopyRegular,
  FolderRegular,
  ImageRegular,
  CheckmarkCircleRegular,
  WarningRegular,
  InfoRegular,
  DismissRegular,
  LockClosedRegular,
  LockOpenRegular,
  RulerRegular,
  TableRegular,
  ColorRegular,
} from "@fluentui/react-icons";

describe("Fluent UI Icons", () => {
  it("imports all required enterprise icons successfully", () => {
    expect(PersonRegular).toBeDefined();
    expect(SettingsRegular).toBeDefined();
    expect(ArrowUndoRegular).toBeDefined();
    expect(ArrowRedoRegular).toBeDefined();
    expect(ZoomInRegular).toBeDefined();
    expect(ZoomOutRegular).toBeDefined();
    expect(ArrowResetRegular).toBeDefined();
    expect(ArrowRotateClockwiseRegular).toBeDefined();
    expect(DeleteRegular).toBeDefined();
    expect(CopyRegular).toBeDefined();
    expect(FolderRegular).toBeDefined();
    expect(ImageRegular).toBeDefined();
    expect(CheckmarkCircleRegular).toBeDefined();
    expect(WarningRegular).toBeDefined();
    expect(InfoRegular).toBeDefined();
    expect(DismissRegular).toBeDefined();
    expect(LockClosedRegular).toBeDefined();
    expect(LockOpenRegular).toBeDefined();
    expect(RulerRegular).toBeDefined();
    expect(TableRegular).toBeDefined();
    expect(ColorRegular).toBeDefined();
  });
});
