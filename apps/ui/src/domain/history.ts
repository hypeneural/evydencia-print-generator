import type { EditStateModel } from "./types";

export interface HistoryManager<T> {
  canUndo: boolean;
  canRedo: boolean;
  present: T;
  push: (next: T) => void;
  undo: () => T | null;
  redo: () => T | null;
  reset: (initial: T) => void;
}

export function createHistoryManager(
  initialState: EditStateModel,
  maxDepth = 50,
): HistoryManager<EditStateModel> {
  let past: EditStateModel[] = [];
  let present: EditStateModel = structuredClone(initialState);
  let future: EditStateModel[] = [];

  return {
    get canUndo() {
      return past.length > 0;
    },
    get canRedo() {
      return future.length > 0;
    },
    get present() {
      return present;
    },
    push(next: EditStateModel) {
      // Don't push if identical
      if (JSON.stringify(present) === JSON.stringify(next)) {
        return;
      }
      past.push(present);
      if (past.length > maxDepth) {
        past.shift();
      }
      present = structuredClone(next);
      future = []; // Clear redo stack on new action
    },
    undo() {
      if (past.length === 0) {
        return null;
      }
      const previous = past.pop()!;
      future.unshift(present);
      present = previous;
      return present;
    },
    redo() {
      if (future.length === 0) {
        return null;
      }
      const next = future.shift()!;
      past.push(present);
      present = next;
      return present;
    },
    reset(initial: EditStateModel) {
      past = [];
      present = structuredClone(initial);
      future = [];
    },
  };
}
