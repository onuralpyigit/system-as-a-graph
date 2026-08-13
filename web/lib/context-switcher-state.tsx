"use client";

import { createContext, useContext, useState, type ReactNode } from "react";

interface ContextSwitcherState {
  open: boolean;
  setOpen: (open: boolean) => void;
}

const ContextSwitcherContext = createContext<ContextSwitcherState | null>(null);

/** Shared open/closed state for the top-bar project/platform/version switcher,
 * so a page's "select a scope" prompt can open it directly instead of just
 * describing where to find it. */
export function ContextSwitcherProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  return (
    <ContextSwitcherContext.Provider value={{ open, setOpen }}>
      {children}
    </ContextSwitcherContext.Provider>
  );
}

export function useContextSwitcherState(): ContextSwitcherState {
  const context = useContext(ContextSwitcherContext);
  if (!context) {
    throw new Error("useContextSwitcherState must be used within a ContextSwitcherProvider");
  }
  return context;
}
