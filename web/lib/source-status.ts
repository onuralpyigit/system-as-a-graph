"use client";

import { useEffect, useState } from "react";

import { setupApi } from "./api-client";
import type { SourceStatusSnapshotResponse } from "./api-types";
import { useSession } from "./use-session";

/**
 * Live source accessibility, pushed over SSE (SRS VAE-01.7). A snapshot
 * arrives on connect and again on every re-probe; nothing here polls.
 */
export function useSourceStatusStream() {
  const { session } = useSession();
  const token = session?.token;
  const [snapshot, setSnapshot] = useState<SourceStatusSnapshotResponse | null>(null);

  useEffect(() => {
    if (!token) return undefined;

    const source = new EventSource(setupApi.sourceStatusStreamUrl(token));
    source.onmessage = (event) => {
      setSnapshot(JSON.parse(event.data) as SourceStatusSnapshotResponse);
    };

    return () => source.close();
  }, [token]);

  return { snapshot };
}
