"use client";

import { Refine } from "@refinedev/core";
import routerProvider from "@refinedev/nextjs-router/app";

import { authProvider } from "@/lib/auth-provider";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <Refine
      authProvider={authProvider}
      routerProvider={routerProvider}
      options={{ disableTelemetry: true }}
    >
      {children}
    </Refine>
  );
}
