"use client";
// The evidence drawer (spec section 3, UI-09): where a shown value came from. A column beside
// the work on wide screens, an overlay panel on tablets, a bottom sheet on phones. It is
// non-modal, so the work stays usable beside it; Escape or Close dismisses it and focus goes
// back to the control that opened it (UI-06).
//
// Phone sheet (carried from the Task 2 review): it opens at a peek (`--sheet-peek`) so the
// task above stays in view. "More" raises it to the full height below the top bar and
// becomes "Less"; dragging the handle up or down does the same, and dragging down from the
// peek closes it. The button is the keyboard and screen-reader path; the handle is a
// pointer convenience that adds nothing the button cannot do.
import * as Dialog from "@radix-ui/react-dialog";
import {
  createContext,
  type PointerEvent,
  type ReactNode,
  useCallback,
  useContext,
  useId,
  useMemo,
  useRef,
  useState,
} from "react";
import { Glyph } from "./Glyph";

export type Evidence = { title: string; body: ReactNode };

type DrawerContextValue = {
  evidence: Evidence | null;
  open(evidence: Evidence): void;
  close(): void;
};

const DrawerContext = createContext<DrawerContextValue | null>(null);

export function EvidenceProvider({ children }: { children: ReactNode }) {
  const [evidence, setEvidence] = useState<Evidence | null>(null);
  const returnTo = useRef<HTMLElement | null>(null);
  const open = useCallback((next: Evidence) => {
    if (document.activeElement instanceof HTMLElement) returnTo.current = document.activeElement;
    setEvidence(next);
  }, []);
  const close = useCallback(() => setEvidence(null), []);
  const value = useMemo(() => ({ evidence, open, close }), [evidence, open, close]);
  return (
    <DrawerContext.Provider value={value}>
      <ReturnFocus.Provider value={returnTo}>{children}</ReturnFocus.Provider>
    </DrawerContext.Provider>
  );
}

const ReturnFocus = createContext<{ current: HTMLElement | null }>({ current: null });

export function useEvidence(): DrawerContextValue {
  const value = useContext(DrawerContext);
  if (value === null) throw new Error("useEvidence outside EvidenceProvider");
  return value;
}

const DRAG_THRESHOLD_PX = 40;

export function EvidenceDrawer() {
  const { evidence, close } = useEvidence();
  const returnTo = useContext(ReturnFocus);
  const [expanded, setExpanded] = useState(false);
  const title = useRef<HTMLHeadingElement>(null);
  const dragFrom = useRef<number | null>(null);
  const bodyId = useId();

  const onOpenChange = (open: boolean) => {
    if (!open) {
      setExpanded(false);
      close();
    }
  };

  const onHandleDown = (event: PointerEvent<HTMLDivElement>) => {
    dragFrom.current = event.clientY;
    event.currentTarget.setPointerCapture(event.pointerId);
  };

  const onHandleUp = (event: PointerEvent<HTMLDivElement>) => {
    if (dragFrom.current === null) return;
    const moved = event.clientY - dragFrom.current;
    dragFrom.current = null;
    if (moved <= -DRAG_THRESHOLD_PX) setExpanded(true);
    else if (moved >= DRAG_THRESHOLD_PX) {
      if (expanded) setExpanded(false);
      else onOpenChange(false);
    }
  };

  return (
    <Dialog.Root open={evidence !== null} onOpenChange={onOpenChange} modal={false}>
      {evidence !== null && (
        <Dialog.Content
          className="drawer on-reading"
          data-expanded={expanded}
          aria-describedby={undefined}
          onOpenAutoFocus={(event) => {
            event.preventDefault();
            title.current?.focus();
          }}
          onCloseAutoFocus={(event) => {
            event.preventDefault();
            returnTo.current?.focus();
          }}
          onInteractOutside={(event) => event.preventDefault()}
        >
          <div
            className="sheet-handle"
            aria-hidden="true"
            onPointerDown={onHandleDown}
            onPointerUp={onHandleUp}
            onPointerCancel={() => {
              dragFrom.current = null;
            }}
          />
          <div className="drawer-head">
            <Dialog.Title asChild>
              <h2 ref={title} tabIndex={-1} className="drawer-title">
                {evidence.title}
              </h2>
            </Dialog.Title>
            <button
              type="button"
              className="btn btn-secondary sheet-toggle"
              aria-expanded={expanded}
              aria-controls={bodyId}
              onClick={() => setExpanded((value) => !value)}
            >
              <Glyph name={expanded ? "collapse" : "expand"} />
              {expanded ? "Less" : "More"}
            </button>
            <Dialog.Close className="btn btn-icon" aria-label="Close where this came from">
              <Glyph name="close" />
            </Dialog.Close>
          </div>
          <div id={bodyId} className="grid gap-16">
            {evidence.body}
          </div>
        </Dialog.Content>
      )}
    </Dialog.Root>
  );
}
