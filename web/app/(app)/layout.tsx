"use client";

import { Authenticated } from "@refinedev/core";

import { TopBar } from "@/components/app-shell/top-bar";
import { ContextSwitcherProvider } from "@/lib/context-switcher-state";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <Authenticated key="app-shell" redirectOnFail="/login">
      <ContextSwitcherProvider>
        <TopBar />
        <div className="flex-1">{children}</div>
      </ContextSwitcherProvider>
    </Authenticated>
  );
}
